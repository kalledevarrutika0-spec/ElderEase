from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Notification, NotificationStatus
from app.services.datetime_utils import utc_now
from app.services.errors import ConflictError, NotFoundError


def list_notifications(
    session: Session, offset: int, limit: int
) -> tuple[list[Notification], int]:
    items = list(
        session.scalars(
            select(Notification)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset(offset)
            .limit(limit)
        )
    )
    total = int(session.scalar(select(func.count()).select_from(Notification)))
    return items, total


def acknowledge_notification(session: Session, notification_id: int) -> Notification:
    with session.begin():
        notification = session.scalar(
            select(Notification)
            .where(Notification.id == notification_id)
            .with_for_update()
        )
        if notification is None:
            raise NotFoundError(f"Notification {notification_id} was not found.")
        if notification.status == NotificationStatus.FAILED:
            raise ConflictError("A failed notification cannot be acknowledged.")
        if notification.status != NotificationStatus.ACKNOWLEDGED:
            notification.status = NotificationStatus.ACKNOWLEDGED
            notification.acknowledged_at = utc_now()
    return notification
