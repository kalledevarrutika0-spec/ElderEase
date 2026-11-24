from typing import Annotated, Any

from pydantic import StringConstraints

from app.schemas.common import APIRequest, ORMResponse


class AssistantChatRequest(APIRequest):
    message: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
    ]


class AssistantChatResponse(ORMResponse):
    message: str
    tool_name: str
    tool_result: dict[str, Any]
    model: str
