from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Caregiver
from app.services.errors import NotFoundError


def list_caregivers(
    session: Session, offset: int, limit: int
) -> tuple[list[Caregiver], int]:
    items = list(
        session.scalars(
            select(Caregiver).order_by(Caregiver.id).offset(offset).limit(limit)
        )
    )
    total = int(session.scalar(select(func.count()).select_from(Caregiver)))
    return items, total


def get_caregiver(session: Session, caregiver_id: int) -> Caregiver:
    caregiver = session.get(Caregiver, caregiver_id)
    if caregiver is None:
        raise NotFoundError(f"Caregiver {caregiver_id} was not found.")
    return caregiver


def get_optional_caregiver(
    session: Session, caregiver_id: int | None
) -> Caregiver | None:
    if caregiver_id is None:
        return None
    return get_caregiver(session, caregiver_id)
