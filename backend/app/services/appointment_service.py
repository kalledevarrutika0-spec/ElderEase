from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Appointment, Caregiver
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.caregiver_service import get_optional_caregiver
from app.services.errors import ConflictError, NotFoundError


def list_appointments(
    session: Session, offset: int, limit: int, family_id: int | None = None
) -> tuple[list[Appointment], int]:
    statement = select(Appointment)
    count_statement = select(func.count()).select_from(Appointment)
    if family_id is not None:
        statement = statement.where(Appointment.family_id == family_id)
        count_statement = count_statement.where(Appointment.family_id == family_id)
    items = list(
        session.scalars(
            statement
            .order_by(Appointment.appointment_datetime, Appointment.id)
            .offset(offset)
            .limit(limit)
        )
    )
    total = int(session.scalar(count_statement))
    return items, total


def create_appointment(
    session: Session,
    data: AppointmentCreate,
    family_id: int | None = None,
) -> Appointment:
    try:
        with session.begin():
            caregiver = get_optional_caregiver(
                session, data.assigned_caregiver_id
            )
            if (
                caregiver is not None
                and family_id is not None
                and caregiver.family_id != family_id
            ):
                raise NotFoundError(
                    f"Caregiver {data.assigned_caregiver_id} was not found."
                )
            appointment = Appointment(
                title=data.title.strip(),
                doctor_name=data.doctor_name.strip(),
                location=data.location,
                appointment_datetime=data.appointment_datetime,
                assigned_caregiver=caregiver,
                status=data.status,
                notes=data.notes,
                family_id=(
                    caregiver.family_id
                    if caregiver is not None
                    else family_id
                ),
            )
            session.add(appointment)
            session.flush()
    except IntegrityError as exc:
        raise ConflictError("The appointment could not be created.") from exc
    return appointment


def update_appointment(
    session: Session,
    appointment_id: int,
    data: AppointmentUpdate,
    family_id: int | None = None,
) -> Appointment:
    try:
        with session.begin():
            appointment = session.get(Appointment, appointment_id)
            if appointment is None:
                raise NotFoundError(f"Appointment {appointment_id} was not found.")
            if family_id is not None and appointment.family_id != family_id:
                raise NotFoundError(f"Appointment {appointment_id} was not found.")
            caregiver = get_optional_caregiver(
                session, data.assigned_caregiver_id
            )
            if (
                caregiver is not None
                and family_id is not None
                and caregiver.family_id != family_id
            ):
                raise NotFoundError(
                    f"Caregiver {data.assigned_caregiver_id} was not found."
                )
            appointment.title = data.title.strip()
            appointment.doctor_name = data.doctor_name.strip()
            appointment.location = data.location
            appointment.appointment_datetime = data.appointment_datetime
            appointment.assigned_caregiver = caregiver
            if caregiver is not None:
                appointment.family_id = caregiver.family_id
            appointment.status = data.status
            appointment.notes = data.notes
            session.flush()
    except IntegrityError as exc:
        raise ConflictError("The appointment could not be updated.") from exc
    return appointment


def delete_appointment(
    session: Session,
    appointment_id: int,
    family_id: int | None = None,
) -> None:
    with session.begin():
        appointment = session.get(Appointment, appointment_id)
        if appointment is None:
            raise NotFoundError(f"Appointment {appointment_id} was not found.")
        if family_id is not None and appointment.family_id != family_id:
            raise NotFoundError(f"Appointment {appointment_id} was not found.")
        session.delete(appointment)
