from datetime import datetime

from app.schemas.common import ORMResponse, PageResponse


class CaregiverRead(ORMResponse):
    id: int
    name: str
    relationship: str
    email: str | None
    phone: str | None
    telegram_chat_id: str | None
    created_at: datetime


class CaregiverPage(PageResponse[CaregiverRead]):
    pass
