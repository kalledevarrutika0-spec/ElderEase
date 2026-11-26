from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Caregiver, Notification, NotificationStatus
from app.services.datetime_utils import utc_now
from app.services.errors import ConflictError, NotFoundError


def list_notifications(
    session: Session, offset: int, limit: int, family_id: int | None = None
) -> tuple[list[Notification], int]:
    statement = select(Notification).join(Notification.recipient)
    count_statement = select(func.count()).select_from(Notification).join(
        Notification.recipient
    )
    if family_id is not None:
        from app.models import Caregiver
        statement = statement.where(Caregiver.family_id == family_id)
        count_statement = count_statement.where(Caregiver.family_id == family_id)
    items = list(
        session.scalars(
            statement
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset(offset)
            .limit(limit)
        )
    )
    total = int(session.scalar(count_statement))
    return items, total


def acknowledge_notification(
    session: Session,
    notification_id: int,
    family_id: int | None = None,
) -> Notification:
    with session.begin():
        notification = session.scalar(
            select(Notification)
            .join(Notification.recipient)
            .where(Notification.id == notification_id)
            .where(
                Caregiver.family_id == family_id
                if family_id is not None
                else True
            )
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
