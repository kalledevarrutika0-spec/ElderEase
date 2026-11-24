from datetime import datetime

from app.models.enums import NotificationStatus
from app.schemas.common import ORMResponse, PageResponse


class NotificationRead(ORMResponse):
    id: int
    recipient_id: int
    message: str
    notification_type: str
    status: NotificationStatus
    created_at: datetime
    acknowledged_at: datetime | None


class NotificationPage(PageResponse[NotificationRead]):
    pass
