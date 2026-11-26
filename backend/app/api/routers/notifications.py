from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.responses import COMMON_ERROR_RESPONSES
from app.database import get_db
from app.schemas.notification import NotificationPage, NotificationRead
from app.services.notification_service import (
    acknowledge_notification,
    list_notifications,
)
from app.core.auth import get_family_member
from app.models import FamilyMember

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get("", response_model=NotificationPage, summary="List notifications")
def read_notifications(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db),
    member: FamilyMember = Depends(get_family_member),
) -> NotificationPage:
    items, total = list_notifications(
        session, offset, limit, member.family_id
    )
    return NotificationPage(items=items, total=total, offset=offset, limit=limit)


@router.patch(
    "/{notification_id}/acknowledge",
    response_model=NotificationRead,
    summary="Acknowledge a notification",
)
def acknowledge(
    notification_id: int = Path(gt=0),
    session: Session = Depends(get_db),
    member: FamilyMember = Depends(get_family_member),
) -> NotificationRead:
    return acknowledge_notification(
        session, notification_id, member.family_id
    )
