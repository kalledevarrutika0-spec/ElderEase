from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.responses import COMMON_ERROR_RESPONSES
from app.database import get_db
from app.schemas.dashboard import DashboardOverview
from app.services.dashboard_service import get_dashboard_overview

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get(
    "/overview",
    response_model=DashboardOverview,
    summary="Get dashboard overview",
)
def read_dashboard_overview(
    session: Session = Depends(get_db),
) -> DashboardOverview:
    return get_dashboard_overview(session)
