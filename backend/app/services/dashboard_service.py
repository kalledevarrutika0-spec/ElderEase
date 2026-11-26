from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Appointment,
    AppointmentStatus,
    Caregiver,
    DoseLog,
    DoseStatus,
    Medicine,
    Notification,
    StockTransaction,
)
from app.schemas.dashboard import DashboardOverview, FamilyActivity
from app.services.datetime_utils import as_utc, utc_day_bounds, utc_now


def get_dashboard_overview(
    session: Session, family_id: int | None = None
) -> DashboardOverview:
    now = utc_now()
    day_start, day_end = utc_day_bounds(now)

    metrics = {
        "total_medicine_count": _count(
            session, Medicine, family_id=family_id
        ),
        "confirmed_doses_today": _count_doses(
            session, DoseStatus.CONFIRMED, day_start, day_end, family_id
        ),
        "pending_doses_today": _count_doses(
            session, DoseStatus.PENDING, day_start, day_end, family_id
        ),
        "skipped_doses_today": _count_doses(
            session, DoseStatus.SKIPPED, day_start, day_end, family_id
        ),
        "upcoming_appointment_count": int(
            session.scalar(
                select(func.count())
                .select_from(Appointment)
                .where(
                    Appointment.appointment_datetime >= now,
                    Appointment.status.in_(
                        [
                            AppointmentStatus.SCHEDULED,
                            AppointmentStatus.CONFIRMED,
                        ]
                    ),
                )
                if family_id is None
                else select(func.count())
                .select_from(Appointment)
                .where(
                    Appointment.appointment_datetime >= now,
                    Appointment.status.in_(
                        [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
                    ),
                    Appointment.family_id == family_id,
                )
            )
        ),
        "low_stock_medicine_count": int(
            session.scalar(
                select(func.count())
                .select_from(Medicine)
                .where(Medicine.current_stock <= Medicine.refill_threshold)
                if family_id is None
                else select(func.count())
                .select_from(Medicine)
                .where(
                    Medicine.current_stock <= Medicine.refill_threshold,
                    Medicine.family_id == family_id,
                )
            )
        ),
    }

    return DashboardOverview(
        **metrics,
        recent_family_activity=_recent_activity(session, family_id),
    )


def _count(
    session: Session, model: type, family_id: int | None = None
) -> int:
    statement = select(func.count()).select_from(model)
    if family_id is not None and hasattr(model, "family_id"):
        statement = statement.where(model.family_id == family_id)
    return int(session.scalar(statement))


def _count_doses(
    session: Session,
    status: DoseStatus,
    start: datetime,
    end: datetime,
    family_id: int | None = None,
) -> int:
    statement = (
        select(func.count())
        .select_from(DoseLog)
        .join(DoseLog.medicine)
        .where(
            DoseLog.status == status,
            DoseLog.scheduled_at >= start,
            DoseLog.scheduled_at < end,
        )
    )
    if family_id is not None:
        statement = statement.where(Medicine.family_id == family_id)
    return int(
        session.scalar(statement)
    )


def _recent_activity(
    session: Session, family_id: int | None = None
) -> list[FamilyActivity]:
    activity: list[FamilyActivity] = []

    dose_logs = session.scalars(
        select(DoseLog)
        .options(joinedload(DoseLog.caregiver), joinedload(DoseLog.medicine))
        .join(DoseLog.medicine)
        .where(
            DoseLog.logged_at.is_not(None),
            Medicine.family_id == family_id if family_id is not None else True,
        )
        .order_by(DoseLog.logged_at.desc())
        .limit(10)
    )
    for dose in dose_logs:
        activity.append(
            FamilyActivity(
                activity_type="dose",
                description=(
                    f"{dose.caregiver.name} marked {dose.medicine.name} "
                    f"{dose.status.value}."
                ),
                occurred_at=as_utc(dose.logged_at),
                caregiver_name=dose.caregiver.name,
            )
        )

    transactions = session.scalars(
        select(StockTransaction)
        .options(
            joinedload(StockTransaction.recorder),
            joinedload(StockTransaction.medicine),
        )
        .join(StockTransaction.medicine)
        .where(
            Medicine.family_id == family_id if family_id is not None else True
        )
        .order_by(StockTransaction.created_at.desc())
        .limit(10)
    )
    for transaction in transactions:
        activity.append(
            FamilyActivity(
                activity_type="stock_transaction",
                description=(
                    f"{transaction.recorder.name} recorded "
                    f"{transaction.transaction_type.value} "
                    f"({transaction.quantity_change:+}) for "
                    f"{transaction.medicine.name}."
                ),
                occurred_at=as_utc(transaction.created_at),
                caregiver_name=transaction.recorder.name,
            )
        )

    appointments = session.scalars(
        select(Appointment)
        .options(joinedload(Appointment.assigned_caregiver))
        .where(
            Appointment.family_id == family_id if family_id is not None else True
        )
        .order_by(Appointment.created_at.desc())
        .limit(10)
    )
    for appointment in appointments:
        caregiver_name = (
            appointment.assigned_caregiver.name
            if appointment.assigned_caregiver is not None
            else None
        )
        activity.append(
            FamilyActivity(
                activity_type="appointment",
                description=f"Appointment added: {appointment.title}.",
                occurred_at=as_utc(appointment.created_at),
                caregiver_name=caregiver_name,
            )
        )

    notifications = session.scalars(
        select(Notification)
        .options(joinedload(Notification.recipient))
        .join(Notification.recipient)
        .where(
            Notification.acknowledged_at.is_not(None),
            Caregiver.family_id == family_id if family_id is not None else True,
        )
        .order_by(Notification.acknowledged_at.desc())
        .limit(10)
    )
    for notification in notifications:
        activity.append(
            FamilyActivity(
                activity_type="notification",
                description=f"{notification.recipient.name} acknowledged a notification.",
                occurred_at=as_utc(notification.acknowledged_at),
                caregiver_name=notification.recipient.name,
            )
        )

    return sorted(activity, key=lambda item: item.occurred_at, reverse=True)[:10]
