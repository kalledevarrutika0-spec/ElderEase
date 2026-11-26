from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
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
    FamilyProfile,
    FamilyMember,
)
from app.core.auth import get_family_member


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

    def override_get_family_member(session=None):
        with test_session_factory() as current_session:
            member = current_session.scalar(
                select(FamilyMember).where(FamilyMember.auth_user_id == "test-user")
            )
            return SimpleNamespace(
                family_id=member.family_id,
                caregiver_id=member.caregiver_id,
            )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_family_member] = override_get_family_member

    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    with test_session_factory.begin() as session:
        profile = FamilyProfile(
            family_name="Test Family",
            elder_name="Test Elder",
            elder_age=78,
            elder_care_notes="Synthetic test profile.",
            invite_code="TESTFAMILY1",
            primary_caregiver_id=None,
        )
        session.add(profile)
        session.flush()
        daughter = Caregiver(
            name="Dara Demo",
            relationship="daughter",
            email="dara.demo@example.invalid",
            family_id=profile.id,
        )
        son = Caregiver(
            name="Sam Demo",
            relationship="son",
            email="sam.demo@example.invalid",
            family_id=profile.id,
        )
        session.add_all([daughter, son])
        session.flush()
        member = FamilyMember(
            family_id=profile.id,
            caregiver_id=daughter.id,
            auth_user_id="test-user",
            role="Primary caregiver",
            relationship="daughter",
            is_primary=True,
        )
        session.add(member)
        session.flush()
        profile.primary_caregiver_id = daughter.id

        medicine = Medicine(
            name="Demo Medicine One",
            dosage="1 tablet",
            units_per_dose=Decimal("2"),
            frequency_per_day=3,
            scheduled_times=["08:00", "12:00", "18:00"],
            current_stock=Decimal("10"),
            refill_threshold=Decimal("3"),
            assigned_caregiver=daughter,
            family_id=profile.id,
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
            family_id=profile.id,
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
            family_id=profile.id,
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
