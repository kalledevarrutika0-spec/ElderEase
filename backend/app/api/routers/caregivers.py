from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.responses import COMMON_ERROR_RESPONSES
from app.database import get_db
from app.schemas.caregiver import CaregiverPage, CaregiverRead
from app.services.caregiver_service import get_caregiver, list_caregivers

router = APIRouter(
    prefix="/caregivers",
    tags=["caregivers"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get("", response_model=CaregiverPage, summary="List caregivers")
def read_caregivers(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db),
) -> CaregiverPage:
    items, total = list_caregivers(session, offset, limit)
    return CaregiverPage(items=items, total=total, offset=offset, limit=limit)


@router.get(
    "/{caregiver_id}",
    response_model=CaregiverRead,
    summary="Get a caregiver",
)
def read_caregiver(
    caregiver_id: int = Path(gt=0),
    session: Session = Depends(get_db),
) -> CaregiverRead:
    return get_caregiver(session, caregiver_id)
