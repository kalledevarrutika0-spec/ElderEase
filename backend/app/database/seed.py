from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.database.init_db import init_db
from app.models import (
    Appointment,
    AppointmentStatus,
    Caregiver,
    DoseLog,
    DoseStatus,
    Medicine,
    Notification,
    NotificationStatus,
    StockTransaction,
    StockTransactionType,
)

DEMO_CARE_PROFILE = {
    "name": "Demo Care Recipient",
    "age_years": 78,
    "synthetic": True,
    "context": "Synthetic, non-identifying demo profile; not a real care record.",
}
DEMO_NOTE = "Synthetic Elderease demo data; not a real person's care record."

CAREGIVER_DATA = (
    {
        "key": "daughter",
        "name": "Asha Sample",
        "relationship": "daughter",
        "email": "asha.sample@example.invalid",
    },
    {
        "key": "son",
        "name": "Neil Sample",
        "relationship": "son",
        "email": "neil.sample@example.invalid",
    },
    {
        "key": "spouse",
        "name": "Mira Sample",
        "relationship": "spouse",
        "email": "mira.sample@example.invalid",
    },
)

MEDICINE_DATA = (
    {
        "name": "Demo Medication A",
        "dosage": "1 tablet",
        "units_per_dose": Decimal("1"),
        "frequency_per_day": 2,
        "scheduled_times": ["08:00", "20:00"],
        "current_stock": Decimal("4"),
        "refill_threshold": Decimal("8"),
        "caregiver": "daughter",
    },
    {
        "name": "Demo Medication B",
        "dosage": "1 capsule",
        "units_per_dose": Decimal("1"),
        "frequency_per_day": 1,
        "scheduled_times": ["09:00"],
        "current_stock": Decimal("28"),
        "refill_threshold": Decimal("7"),
        "caregiver": "son",
    },
    {
        "name": "Demo Medication C",
        "dosage": "5 mL",
        "units_per_dose": Decimal("5"),
        "frequency_per_day": 3,
        "scheduled_times": ["08:00", "14:00", "20:00"],
        "current_stock": Decimal("40"),
        "refill_threshold": Decimal("10"),
        "caregiver": "spouse",
    },
    {
        "name": "Demo Medication D",
        "dosage": "2 tablets",
        "units_per_dose": Decimal("2"),
        "frequency_per_day": 1,
        "scheduled_times": ["12:00"],
        "current_stock": Decimal("8"),
        "refill_threshold": Decimal("10"),
        "caregiver": "daughter",
    },
)

STOCK_TRANSACTION_DATA = (
    (
        "Demo Medication A",
        "daughter",
        Decimal("4"),
        StockTransactionType.PURCHASE,
        "Demo opening purchase A.",
    ),
    (
        "Demo Medication B",
        "son",
        Decimal("30"),
        StockTransactionType.PURCHASE,
        "Demo opening purchase B.",
    ),
    (
        "Demo Medication B",
        "son",
        Decimal("-2"),
        StockTransactionType.CONSUMPTION,
        "Demo recorded consumption B.",
    ),
    (
        "Demo Medication C",
        "spouse",
        Decimal("42"),
        StockTransactionType.PURCHASE,
        "Demo opening purchase C.",
    ),
    (
        "Demo Medication C",
        "spouse",
        Decimal("-2"),
        StockTransactionType.CORRECTION,
        "Demo count correction C.",
    ),
    (
        "Demo Medication D",
        "daughter",
        Decimal("12"),
        StockTransactionType.PURCHASE,
        "Demo opening purchase D.",
    ),
    (
        "Demo Medication D",
        "daughter",
        Decimal("-4"),
        StockTransactionType.CONSUMPTION,
        "Demo recorded consumption D.",
    ),
)


def _upsert_caregivers(session: Session) -> dict[str, Caregiver]:
    caregivers: dict[str, Caregiver] = {}
    for data in CAREGIVER_DATA:
        caregiver = session.scalar(
            select(Caregiver).where(Caregiver.email == data["email"])
        )
        if caregiver is None:
            caregiver = Caregiver()
            session.add(caregiver)
        caregiver.name = data["name"]
        caregiver.relationship = data["relationship"]
        caregiver.email = data["email"]
        caregiver.phone = None
        caregiver.telegram_chat_id = None
        caregivers[data["key"]] = caregiver

    session.flush()
    return caregivers


def _upsert_medicines(
    session: Session, caregivers: dict[str, Caregiver]
) -> dict[str, Medicine]:
    medicines: dict[str, Medicine] = {}
    for data in MEDICINE_DATA:
        medicine = session.scalar(
            select(Medicine).where(Medicine.name == data["name"])
        )
        if medicine is None:
            medicine = Medicine()
            session.add(medicine)
        medicine.name = data["name"]
        medicine.dosage = data["dosage"]
        medicine.units_per_dose = data["units_per_dose"]
        medicine.frequency_per_day = data["frequency_per_day"]
        medicine.scheduled_times = data["scheduled_times"]
        medicine.current_stock = data["current_stock"]
        medicine.refill_threshold = data["refill_threshold"]
        medicine.assigned_caregiver = caregivers[data["caregiver"]]
        medicine.instructions = DEMO_NOTE
        medicines[data["name"]] = medicine

    session.flush()
    return medicines


def _upsert_dose_logs(
    session: Session,
    medicines: dict[str, Medicine],
    caregivers: dict[str, Caregiver],
    now: datetime,
) -> None:
    for data in MEDICINE_DATA:
        medicine = medicines[data["name"]]
        caregiver = caregivers[data["caregiver"]]
        for scheduled_time in medicine.scheduled_times:
            scheduled_at = datetime.combine(
                now.date(), time.fromisoformat(scheduled_time), tzinfo=timezone.utc
            )
            status = DoseStatus.CONFIRMED if scheduled_at <= now else DoseStatus.PENDING
            dose_log = session.scalar(
                select(DoseLog).where(
                    DoseLog.medicine_id == medicine.id,
                    DoseLog.scheduled_at == scheduled_at,
                )
            )
            if dose_log is None:
                dose_log = DoseLog(
                    medicine=medicine,
                    scheduled_at=scheduled_at,
                )
                session.add(dose_log)
            dose_log.caregiver = caregiver
            dose_log.status = status
            dose_log.logged_at = now if status == DoseStatus.CONFIRMED else None
            dose_log.notes = DEMO_NOTE


def _upsert_appointments(
    session: Session, caregivers: dict[str, Caregiver], now: datetime
) -> None:
    data = (
        {
            "title": "Demo check-in appointment",
            "doctor_name": "Dr. Example One",
            "location": "Demo Community Clinic",
            "days_ahead": 4,
            "caregiver": "daughter",
        },
        {
            "title": "Demo follow-up appointment",
            "doctor_name": "Dr. Example Two",
            "location": "Demo Family Health Centre",
            "days_ahead": 11,
            "caregiver": "son",
        },
    )
    for item in data:
        appointment = session.scalar(
            select(Appointment).where(
                Appointment.title == item["title"],
                Appointment.notes == DEMO_NOTE,
            )
        )
        if appointment is None:
            appointment = Appointment()
            session.add(appointment)
        appointment.title = item["title"]
        appointment.doctor_name = item["doctor_name"]
        appointment.location = item["location"]
        appointment.appointment_datetime = (
            now + timedelta(days=item["days_ahead"])
        ).replace(hour=10, minute=0, second=0, microsecond=0)
        appointment.assigned_caregiver = caregivers[item["caregiver"]]
        appointment.status = AppointmentStatus.SCHEDULED
        appointment.notes = DEMO_NOTE


def _upsert_stock_transactions(
    session: Session,
    medicines: dict[str, Medicine],
    caregivers: dict[str, Caregiver],
) -> None:
    for (
        medicine_name,
        caregiver_key,
        quantity,
        transaction_type,
        detail,
    ) in STOCK_TRANSACTION_DATA:
        notes = f"{detail} {DEMO_NOTE}"
        medicine = medicines[medicine_name]
        transaction = session.scalar(
            select(StockTransaction).where(
                StockTransaction.medicine_id == medicine.id,
                StockTransaction.notes == notes,
            )
        )
        if transaction is None:
            transaction = StockTransaction(
                medicine=medicine,
                notes=notes,
            )
            session.add(transaction)
        transaction.quantity_change = quantity
        transaction.transaction_type = transaction_type
        transaction.recorded_by = caregivers[caregiver_key].id


def _upsert_notifications(session: Session, caregivers: dict[str, Caregiver]) -> None:
    data = (
        (
            "daughter",
            "Demo: today's care schedule is ready.",
            "care_schedule",
            NotificationStatus.ACKNOWLEDGED,
        ),
        (
            "son",
            "Demo: an upcoming appointment is on the family calendar.",
            "appointment_reminder",
            NotificationStatus.PENDING,
        ),
        (
            "spouse",
            "Demo: a sample medicine stock record is below its refill threshold.",
            "stock_notice",
            NotificationStatus.SENT,
        ),
    )
    now = datetime.now(timezone.utc)
    for caregiver_key, message, notification_type, status in data:
        caregiver = caregivers[caregiver_key]
        notification = session.scalar(
            select(Notification).where(
                Notification.recipient_id == caregiver.id,
                Notification.message == message,
            )
        )
        if notification is None:
            notification = Notification(
                recipient=caregiver,
                message=message,
            )
            session.add(notification)
        notification.notification_type = notification_type
        notification.status = status
        notification.acknowledged_at = (
            now if status == NotificationStatus.ACKNOWLEDGED else None
        )


def seed_demo_data() -> None:
    init_db()
    now = datetime.now(timezone.utc)

    with SessionLocal.begin() as session:
        caregivers = _upsert_caregivers(session)
        medicines = _upsert_medicines(session, caregivers)
        _upsert_dose_logs(session, medicines, caregivers, now)
        _upsert_appointments(session, caregivers, now)
        _upsert_stock_transactions(session, medicines, caregivers)
        _upsert_notifications(session, caregivers)

    with SessionLocal() as session:
        counts = {
            "caregivers": session.scalar(select(func.count()).select_from(Caregiver)),
            "medicines": session.scalar(select(func.count()).select_from(Medicine)),
            "dose_logs": session.scalar(select(func.count()).select_from(DoseLog)),
            "appointments": session.scalar(select(func.count()).select_from(Appointment)),
            "notifications": session.scalar(select(func.count()).select_from(Notification)),
            "stock_transactions": session.scalar(
                select(func.count()).select_from(StockTransaction)
            ),
        }
    print(f"Seeded synthetic care profile {DEMO_CARE_PROFILE['name']}: {counts}")


if __name__ == "__main__":
    seed_demo_data()
