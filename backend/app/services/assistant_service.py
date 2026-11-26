import asyncio
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import APIError, AsyncOpenAI

from app.core.config import settings
from app.services.errors import AssistantConfigurationError, AssistantWorkflowError

logger = logging.getLogger(__name__)
BACKEND_ROOT = Path(__file__).resolve().parents[2]
REFILL_TOOL_NAME = "check_refill_status"
_BEARER_TOKEN_PATTERN = re.compile(r"(?i)\bbearer\s+[^\s,;]+")
_PROVIDER_KEY_PATTERN = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{8,}|gsk_[A-Za-z0-9_-]{8,})\b")
_API_KEY_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)((?:GROQ|OPENAI)_API_KEY\s*[:=]\s*)[^\s,;]+"
)


def _sanitize_log_value(value: object, secret: str, *, limit: int = 300) -> str:
    if not isinstance(value, str) or not value:
        return "unavailable"
    sanitized = value.replace(secret, "[REDACTED]") if secret else value
    sanitized = _BEARER_TOKEN_PATTERN.sub("Bearer [REDACTED]", sanitized)
    sanitized = _PROVIDER_KEY_PATTERN.sub("[REDACTED]", sanitized)
    sanitized = _API_KEY_ASSIGNMENT_PATTERN.sub(
        r"\1[REDACTED]", sanitized
    )
    return " ".join(sanitized.split())[:limit]


def _provider_error_details(
    error: APIError, secret: str
) -> tuple[int | None, str, str, str]:
    status_code = getattr(error, "status_code", None)
    if not isinstance(status_code, int):
        status_code = None

    details = error.body if isinstance(error.body, dict) else {}
    nested_error = details.get("error")
    if isinstance(nested_error, dict):
        details = nested_error

    code = _sanitize_log_value(
        details.get("code") or error.code, secret, limit=120
    )
    error_type = _sanitize_log_value(
        details.get("type") or error.type, secret, limit=120
    )
    message = details.get("message")
    if not isinstance(message, str) or not message:
        message = error.message
    return status_code, code, error_type, _sanitize_log_value(message, secret)


async def chat_about_refills(
    message: str,
    family_id: int | None = None,
) -> dict[str, Any]:
    api_key = settings.groq_api_key
    if (
        api_key is None
        or not api_key.get_secret_value().strip()
        or api_key.get_secret_value().strip().lower().startswith("replace_with_")
    ):
        raise AssistantConfigurationError(
            "Groq is not configured. Set an actual GROQ_API_KEY in backend/.env and restart the API."
        )

    try:
        tool_result = await asyncio.wait_for(
            invoke_refill_status_tool(family_id), timeout=30
        )
    except Exception as exc:
        logger.exception("The refill MCP tool workflow failed.")
        raise AssistantWorkflowError(
            "The refill status MCP tool could not be reached. Please try again."
        ) from exc

    client: AsyncOpenAI | None = None
    try:
        client = AsyncOpenAI(
            api_key=api_key.get_secret_value(),
            base_url=settings.groq_base_url,
        )
        response = await asyncio.wait_for(
            client.responses.create(
                model=settings.groq_model,
                instructions=(
                    "You are Elderease's family care assistant. Answer the user's "
                    "question using only the supplied check_refill_status tool result. "
                    "For each medicine, explain whether the returned seven-day "
                    "forecast covers its scheduled doses and include the actual "
                    "estimated depletion date and urgency when available. If there "
                    "are no forecasts or a forecast is unavailable, state that clearly. "
                    "The tool result does not link medicines to a care recipient; "
                    "if the user asks about a named person, explain that the results "
                    "cover medicines in the shared care plan and do not claim which "
                    "ones belong to that person. Do not invent medicine data, diagnose "
                    "conditions, recommend starting or stopping medicine, or recommend "
                    "changing medication dosage. Do not provide medical advice. "
                    "Keep the answer concise and understandable."
                ),
                input=(
                    "User question:\n"
                    f"{message}\n\n"
                    "Actual result from the check_refill_status MCP tool:\n"
                    f"{json.dumps(tool_result, ensure_ascii=True)}"
                ),
                temperature=0.2,
            ),
            timeout=40,
        )
        answer = response.output_text
        if not answer or not answer.strip():
            raise ValueError("Groq returned an empty answer.")
    except APIError as exc:
        status_code, error_code, error_type, message = _provider_error_details(
            exc, api_key.get_secret_value()
        )
        logger.error(
            "Groq API request failed: http_status=%s error_code=%s "
            "error_type=%s message=%s",
            status_code if status_code is not None else "unavailable",
            error_code,
            error_type,
            message,
        )
        raise AssistantWorkflowError(
            "Groq could not generate an answer from the refill results. Please try again."
        ) from exc
    except Exception as exc:
        logger.warning(
            "Groq failed to generate the refill response (%s).",
            type(exc).__name__,
        )
        raise AssistantWorkflowError(
            "Groq could not generate an answer from the refill results. Please try again."
        ) from exc
    finally:
        if client is not None:
            try:
                await client.close()
            except Exception as exc:
                logger.warning(
                    "Could not close the Groq client cleanly (%s).",
                    type(exc).__name__,
                )

    return {
        "message": answer.strip(),
        "tool_name": REFILL_TOOL_NAME,
        "tool_result": tool_result,
        "model": settings.groq_model,
    }


async def invoke_refill_status_tool(
    family_id: int | None = None,
) -> dict[str, Any]:
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

            result = await session.call_tool(
                REFILL_TOOL_NAME,
                arguments={"family_id": family_id} if family_id is not None else {},
            )
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
