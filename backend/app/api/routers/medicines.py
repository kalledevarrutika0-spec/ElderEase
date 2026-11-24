from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.api.responses import COMMON_ERROR_RESPONSES
from app.database import get_db
from app.schemas.medicine import (
    MedicineCreate,
    MedicinePage,
    MedicineRead,
    MedicineUpdate,
)
from app.schemas.refill import RefillForecast, RefillForecastPage
from app.services.medicine_service import (
    create_medicine,
    delete_medicine,
    get_medicine,
    list_medicines,
    update_medicine,
)
from app.services.refill_engine import (
    get_refill_forecast,
    list_refill_forecasts,
)

router = APIRouter(
    prefix="/medicines",
    tags=["medicines"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get("", response_model=MedicinePage, summary="List medicines")
def read_medicines(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db),
) -> MedicinePage:
    items, total = list_medicines(session, offset, limit)
    return MedicinePage(items=items, total=total, offset=offset, limit=limit)


@router.post(
    "",
    response_model=MedicineRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a medicine",
)
def add_medicine(
    data: MedicineCreate,
    session: Session = Depends(get_db),
) -> MedicineRead:
    return create_medicine(session, data)


@router.get(
    "/refill-forecast",
    response_model=RefillForecastPage,
    summary="Forecast refills for all medicines",
)
def read_refill_forecasts(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db),
) -> RefillForecastPage:
    forecasts, total = list_refill_forecasts(session, offset, limit)
    return RefillForecastPage(
        items=forecasts,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{medicine_id}/refill-forecast",
    response_model=RefillForecast,
    summary="Forecast a medicine refill",
)
def read_medicine_refill_forecast(
    medicine_id: int = Path(gt=0),
    session: Session = Depends(get_db),
) -> RefillForecast:
    return get_refill_forecast(session, medicine_id)


@router.get(
    "/{medicine_id}",
    response_model=MedicineRead,
    summary="Get a medicine",
)
def read_medicine(
    medicine_id: int = Path(gt=0),
    session: Session = Depends(get_db),
) -> MedicineRead:
    return get_medicine(session, medicine_id)


@router.put(
    "/{medicine_id}",
    response_model=MedicineRead,
    summary="Update medicine details",
)
def replace_medicine(
    data: MedicineUpdate,
    medicine_id: int = Path(gt=0),
    session: Session = Depends(get_db),
) -> MedicineRead:
    return update_medicine(session, medicine_id, data)


@router.delete(
    "/{medicine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a medicine without history",
)
def remove_medicine(
    medicine_id: int = Path(gt=0),
    session: Session = Depends(get_db),
) -> Response:
    delete_medicine(session, medicine_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
