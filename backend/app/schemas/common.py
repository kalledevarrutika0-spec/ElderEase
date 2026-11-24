from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class APIRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="before")
    @classmethod
    def normalize_datetime(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value


class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)


class ValidationIssue(BaseModel):
    location: list[str | int]
    message: str
    type: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ValidationIssue] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
