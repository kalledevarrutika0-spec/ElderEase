from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (
    Appointment,
    AppointmentStatus,
    Caregiver,
    DoseLog,
    DoseStatus,
    Medicine,
    Notification,
)


@pytest.fixture
def api():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def enable_test_foreign_keys(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=test_engine)
    test_session_factory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )
    previous_overrides = app.dependency_overrides.copy()

    def override_get_db():
        with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    with test_session_factory.begin() as session:
        daughter = Caregiver(
            name="Dara Demo",
            relationship="daughter",
            email="dara.demo@example.invalid",
        )
        son = Caregiver(
            name="Sam Demo",
            relationship="son",
            email="sam.demo@example.invalid",
        )
        session.add_all([daughter, son])
        session.flush()

        medicine = Medicine(
            name="Demo Medicine One",
            dosage="1 tablet",
            units_per_dose=Decimal("2"),
            frequency_per_day=3,
            scheduled_times=["08:00", "12:00", "18:00"],
            current_stock=Decimal("10"),
            refill_threshold=Decimal("3"),
            assigned_caregiver=daughter,
        )
        low_stock_medicine = Medicine(
            name="Demo Medicine Two",
            dosage="1 capsule",
            units_per_dose=Decimal("2"),
            frequency_per_day=1,
            scheduled_times=["20:00"],
            current_stock=Decimal("1"),
            refill_threshold=Decimal("4"),
            assigned_caregiver=son,
        )
        session.add_all([medicine, low_stock_medicine])
        session.flush()

        confirmed_dose = DoseLog(
            medicine=medicine,
            caregiver=daughter,
            scheduled_at=datetime.combine(
                day_start.date(), time(8), tzinfo=timezone.utc
            ),
            status=DoseStatus.CONFIRMED,
            logged_at=now,
        )
        pending_dose = DoseLog(
            medicine=medicine,
            caregiver=daughter,
            scheduled_at=datetime.combine(
                day_start.date(), time(12), tzinfo=timezone.utc
            ),
            status=DoseStatus.PENDING,
        )
        skipped_dose = DoseLog(
            medicine=medicine,
            caregiver=daughter,
            scheduled_at=datetime.combine(
                day_start.date(), time(18), tzinfo=timezone.utc
            ),
            status=DoseStatus.SKIPPED,
            logged_at=now,
        )
        low_stock_dose = DoseLog(
            medicine=low_stock_medicine,
            caregiver=son,
            scheduled_at=datetime.combine(
                day_start.date(), time(20), tzinfo=timezone.utc
            ),
            status=DoseStatus.PENDING,
        )
        session.add_all(
            [confirmed_dose, pending_dose, skipped_dose, low_stock_dose]
        )
        appointment = Appointment(
            title="Demo appointment",
            doctor_name="Dr. Test",
            location="Demo Clinic",
            appointment_datetime=now + timedelta(days=5),
            assigned_caregiver=daughter,
            status=AppointmentStatus.SCHEDULED,
        )
        notification = Notification(
            recipient=daughter,
            message="Demo notification",
            notification_type="test",
        )
        session.add_all([appointment, notification])
        session.flush()

        ids = {
            "caregiver": daughter.id,
            "second_caregiver": son.id,
            "medicine": medicine.id,
            "low_stock_medicine": low_stock_medicine.id,
            "confirmed_dose": confirmed_dose.id,
            "pending_dose": pending_dose.id,
            "skipped_dose": skipped_dose.id,
            "low_stock_dose": low_stock_dose.id,
            "appointment": appointment.id,
            "notification": notification.id,
        }

    with TestClient(app) as client:
        yield {
            "client": client,
            "ids": ids,
            "session_factory": test_session_factory,
        }

    app.dependency_overrides = previous_overrides
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
