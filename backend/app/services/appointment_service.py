from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Appointment, Caregiver
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.caregiver_service import get_optional_caregiver
from app.services.errors import ConflictError, NotFoundError


def list_appointments(
    session: Session, offset: int, limit: int
) -> tuple[list[Appointment], int]:
    items = list(
        session.scalars(
            select(Appointment)
            .order_by(Appointment.appointment_datetime, Appointment.id)
            .offset(offset)
            .limit(limit)
        )
    )
    total = int(session.scalar(select(func.count()).select_from(Appointment)))
    return items, total


def create_appointment(session: Session, data: AppointmentCreate) -> Appointment:
    try:
        with session.begin():
            caregiver = get_optional_caregiver(
                session, data.assigned_caregiver_id
            )
            appointment = Appointment(
                title=data.title.strip(),
                doctor_name=data.doctor_name.strip(),
                location=data.location,
                appointment_datetime=data.appointment_datetime,
                assigned_caregiver=caregiver,
                status=data.status,
                notes=data.notes,
            )
            session.add(appointment)
            session.flush()
    except IntegrityError as exc:
        raise ConflictError("The appointment could not be created.") from exc
    return appointment


def update_appointment(
    session: Session, appointment_id: int, data: AppointmentUpdate
) -> Appointment:
    try:
        with session.begin():
            appointment = session.get(Appointment, appointment_id)
            if appointment is None:
                raise NotFoundError(f"Appointment {appointment_id} was not found.")
            caregiver = get_optional_caregiver(
                session, data.assigned_caregiver_id
            )
            appointment.title = data.title.strip()
            appointment.doctor_name = data.doctor_name.strip()
            appointment.location = data.location
            appointment.appointment_datetime = data.appointment_datetime
            appointment.assigned_caregiver = caregiver
            appointment.status = data.status
            appointment.notes = data.notes
            session.flush()
    except IntegrityError as exc:
        raise ConflictError("The appointment could not be updated.") from exc
    return appointment


def delete_appointment(session: Session, appointment_id: int) -> None:
    with session.begin():
        appointment = session.get(Appointment, appointment_id)
        if appointment is None:
            raise NotFoundError(f"Appointment {appointment_id} was not found.")
        session.delete(appointment)
