from fastapi import APIRouter, Depends

from app.api.responses import COMMON_ERROR_RESPONSES
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.services.assistant_service import chat_about_refills
from app.core.auth import get_family_member
from app.models import FamilyMember

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
    member: FamilyMember = Depends(get_family_member),
) -> AssistantChatResponse:
    result = await chat_about_refills(data.message, member.family_id)
    return AssistantChatResponse(**result)
