from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Caregiver
from app.services.errors import NotFoundError


def list_caregivers(
    session: Session, offset: int, limit: int, family_id: int | None = None
) -> tuple[list[Caregiver], int]:
    statement = select(Caregiver)
    count_statement = select(func.count()).select_from(Caregiver)
    if family_id is not None:
        statement = statement.where(Caregiver.family_id == family_id)
        count_statement = count_statement.where(Caregiver.family_id == family_id)
    items = list(
        session.scalars(
            statement.order_by(Caregiver.id).offset(offset).limit(limit)
        )
    )
    total = int(session.scalar(count_statement))
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
