from datetime import datetime

from pydantic import Field

from app.models.enums import DoseStatus
from app.schemas.common import APIRequest, ORMResponse, PageResponse


class DoseLogRequest(APIRequest):
    status: DoseStatus
    notes: str | None = Field(default=None, max_length=2000)


class DoseRead(ORMResponse):
    id: int
    medicine_id: int
    caregiver_id: int
    scheduled_at: datetime
    status: DoseStatus
    logged_at: datetime | None
    notes: str | None


class DosePage(PageResponse[DoseRead]):
    pass
