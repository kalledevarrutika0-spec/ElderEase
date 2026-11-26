from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.responses import COMMON_ERROR_RESPONSES
from app.database import get_db
from app.schemas.dose import DoseLogRequest, DosePage, DoseRead
from app.services.dose_service import list_today_doses, log_dose
from app.core.auth import get_family_member
from app.models import FamilyMember

router = APIRouter(
    prefix="/doses",
    tags=["doses"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get("/today", response_model=DosePage, summary="List today's scheduled doses")
def read_today_doses(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db),
    member: FamilyMember = Depends(get_family_member),
) -> DosePage:
    doses, total = list_today_doses(
        session, offset, limit, member.family_id
    )
    return DosePage(
        items=doses,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/{dose_id}/log",
    response_model=DoseRead,
    summary="Log a dose status",
)
def record_dose(
    data: DoseLogRequest,
    dose_id: int = Path(gt=0),
    session: Session = Depends(get_db),
    member: FamilyMember = Depends(get_family_member),
) -> DoseRead:
    return log_dose(
        session,
        dose_id,
        data,
        member.family_id,
    )
