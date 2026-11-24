from fastapi import APIRouter

from app.api.responses import COMMON_ERROR_RESPONSES
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.services.assistant_service import chat_about_refills

router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
    summary="Ask the refill assistant",
)
async def chat(
    data: AssistantChatRequest,
) -> AssistantChatResponse:
    result = await chat_about_refills(data.message)
    return AssistantChatResponse(**result)
