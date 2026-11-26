from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.api.responses import COMMON_ERROR_RESPONSES
from app.database import get_db
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentPage,
    AppointmentRead,
    AppointmentUpdate,
)
from app.services.appointment_service import (
    create_appointment,
    delete_appointment,
    list_appointments,
    update_appointment,
)
from app.core.auth import get_family_member
from app.models import Appointment, FamilyMember
from app.services.caregiver_service import get_caregiver

router = APIRouter(
    prefix="/appointments",
    tags=["appointments"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get("", response_model=AppointmentPage, summary="List appointments")
def read_appointments(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db),
    member: FamilyMember = Depends(get_family_member),
) -> AppointmentPage:
    items, total = list_appointments(
        session, offset, limit, member.family_id
    )
    return AppointmentPage(items=items, total=total, offset=offset, limit=limit)


@router.post(
    "",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an appointment",
)
def add_appointment(
    data: AppointmentCreate,
    session: Session = Depends(get_db),
    member: FamilyMember = Depends(get_family_member),
) -> AppointmentRead:
    return create_appointment(session, data, member.family_id)


@router.put(
    "/{appointment_id}",
    response_model=AppointmentRead,
    summary="Update an appointment",
)
def replace_appointment(
    data: AppointmentUpdate,
    appointment_id: int = Path(gt=0),
    session: Session = Depends(get_db),
    member: FamilyMember = Depends(get_family_member),
) -> AppointmentRead:
    return update_appointment(session, appointment_id, data, member.family_id)


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an appointment",
)
def remove_appointment(
    appointment_id: int = Path(gt=0),
    session: Session = Depends(get_db),
    member: FamilyMember = Depends(get_family_member),
) -> Response:
    delete_appointment(session, appointment_id, member.family_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
