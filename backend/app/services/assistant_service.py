import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.config import settings
from app.services.errors import AssistantConfigurationError, AssistantWorkflowError

logger = logging.getLogger(__name__)
BACKEND_ROOT = Path(__file__).resolve().parents[2]
REFILL_TOOL_NAME = "check_refill_status"


async def chat_about_refills(message: str) -> dict[str, Any]:
    api_key = settings.gemini_api_key
    if (
        api_key is None
        or not api_key.get_secret_value().strip()
        or api_key.get_secret_value().strip().lower().startswith("replace_with_")
    ):
        raise AssistantConfigurationError(
            "Gemini is not configured. Set an actual GEMINI_API_KEY in backend/.env and restart the API."
        )

    try:
        tool_result = await asyncio.wait_for(
            invoke_refill_status_tool(), timeout=30
        )
    except Exception as exc:
        logger.exception("The refill MCP tool workflow failed.")
        raise AssistantWorkflowError(
            "The refill status MCP tool could not be reached. Please try again."
        ) from exc

    client = None
    try:
        client = genai.Client(api_key=api_key.get_secret_value())
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=(
                    "User question:\n"
                    f"{message}\n\n"
                    "Actual result from the check_refill_status MCP tool:\n"
                    f"{json.dumps(tool_result, ensure_ascii=True)}"
                ),
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are Elderease's family care assistant. Answer the user's "
                        "question using only the supplied check_refill_status tool result. "
                        "For each medicine, explain whether the returned seven-day "
                        "forecast covers its scheduled doses and include the actual "
                        "estimated depletion date and urgency when available. If there "
                        "are no forecasts or a forecast is unavailable, state that clearly. "
                        "The tool result does not link medicines to a care recipient; "
                        "if the user asks about a named person, explain that the results "
                        "cover medicines in the shared care plan and do not claim which "
                        "ones belong to that person. Do not invent medicine data or "
                        "provide medical advice. Keep the answer concise and understandable."
                    ),
                    temperature=0.2,
                ),
            ),
            timeout=40,
        )
        answer = response.text
        if not answer or not answer.strip():
            raise ValueError("Gemini returned an empty answer.")
    except Exception as exc:
        logger.exception("Gemini failed to generate the refill response.")
        raise AssistantWorkflowError(
            "Gemini could not generate an answer from the refill results. Please try again."
        ) from exc
    finally:
        if client is not None:
            try:
                await client.aio.aclose()
            except Exception:
                logger.exception("Could not close the Gemini client cleanly.")

    return {
        "message": answer.strip(),
        "tool_name": REFILL_TOOL_NAME,
        "tool_result": tool_result,
        "model": settings.gemini_model,
    }


async def invoke_refill_status_tool() -> dict[str, Any]:
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp.server"],
        cwd=BACKEND_ROOT,
        env={"DATABASE_URL": settings.database_url},
        encoding="utf-8",
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            discovered_tools = await session.list_tools()
            if not any(
                tool.name == REFILL_TOOL_NAME for tool in discovered_tools.tools
            ):
                raise RuntimeError(
                    "The MCP server does not expose check_refill_status."
                )

            result = await session.call_tool(REFILL_TOOL_NAME, arguments={})
            if result.isError:
                details = "; ".join(
                    content.text
                    for content in result.content
                    if getattr(content, "text", None)
                )
                raise RuntimeError(details or "The refill MCP tool returned an error.")

            structured_content = getattr(result, "structuredContent", None)
            if structured_content is not None:
                return structured_content

            for content in result.content:
                text = getattr(content, "text", None)
                if text:
                    decoded = json.loads(text)
                    if isinstance(decoded, dict):
                        return decoded
            raise RuntimeError("The refill MCP tool returned no structured result.")
