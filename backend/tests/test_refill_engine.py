from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select, update

from app.models import (
    DoseLog,
    DoseStatus,
    Medicine,
    StockTransaction,
    StockTransactionType,
)
from app.schemas.refill import RefillUrgency
from app.services.refill_engine import get_refill_forecast
from app.services.stock_service import dose_stock_transaction_note

NOW = datetime(2026, 1, 1, 7, 0, tzinfo=timezone.utc)


def _configure_medicine(
    session_factory,
    medicine_id: int,
    *,
    schedule: list[str],
    units: str = "1",
    stock: str = "20",
    threshold: str = "5",
) -> None:
    with session_factory() as session:
        medicine = session.get(Medicine, medicine_id)
        assert medicine is not None
        medicine.scheduled_times = schedule
        medicine.frequency_per_day = len(schedule)
        medicine.units_per_dose = Decimal(units)
        medicine.current_stock = Decimal(stock)
        medicine.refill_threshold = Decimal(threshold)
        session.commit()


def _forecast(session_factory, medicine_id: int):
    with session_factory() as session:
        return get_refill_forecast(session, medicine_id, now=NOW)


def test_daily_forecast_depletion_and_upcoming_threshold(api):
    medicine_id = api["ids"]["medicine"]
    _configure_medicine(
        api["session_factory"],
        medicine_id,
        schedule=["08:00"],
        units="1",
        stock="10",
        threshold="3",
    )

    forecast = _forecast(api["session_factory"], medicine_id)

    assert forecast.forecast_available is True
    assert len(forecast.upcoming_scheduled_doses) == 7
    assert forecast.expected_consumption == Decimal("7")
    assert forecast.estimated_remaining_supply == Decimal("3")
    assert forecast.estimated_depletion_at == datetime(
        2026, 1, 10, 8, 0, tzinfo=timezone.utc
    )
    assert forecast.urgency == RefillUrgency.UPCOMING


def test_multiple_daily_doses_use_units_per_dose(api):
    medicine_id = api["ids"]["medicine"]
    _configure_medicine(
        api["session_factory"],
        medicine_id,
        schedule=["08:00", "20:00"],
        units="2",
        stock="20",
        threshold="5",
    )

    forecast = _forecast(api["session_factory"], medicine_id)

    assert len(forecast.upcoming_scheduled_doses) == 14
    assert forecast.expected_consumption == Decimal("28")
    assert forecast.estimated_remaining_supply == Decimal("0")
    assert forecast.estimated_depletion_at == datetime(
        2026, 1, 5, 20, 0, tzinfo=timezone.utc
    )


def test_variable_schedule_order_and_pending_dose_is_not_missed(api):
    medicine_id = api["ids"]["medicine"]
    session_factory = api["session_factory"]
    _configure_medicine(
        session_factory,
        medicine_id,
        schedule=["23:00", "06:30", "11:15"],
        units="1",
        stock="50",
        threshold="5",
    )

    with session_factory() as session:
        session.add(
            DoseLog(
                medicine_id=medicine_id,
                caregiver_id=api["ids"]["caregiver"],
                scheduled_at=datetime(2026, 1, 1, 6, 30, tzinfo=timezone.utc),
                status=DoseStatus.PENDING,
            )
        )
        session.commit()

    forecast = _forecast(session_factory, medicine_id)

    assert forecast.upcoming_scheduled_doses[0].scheduled_at == datetime(
        2026, 1, 1, 6, 30, tzinfo=timezone.utc
    )
    assert forecast.upcoming_scheduled_doses[0].expected_at == NOW
    assert (
        forecast.upcoming_scheduled_doses[0].dose_log_status
        == DoseStatus.PENDING
    )
    assert forecast.upcoming_scheduled_doses[1].scheduled_at == datetime(
        2026, 1, 1, 11, 15, tzinfo=timezone.utc
    )


@pytest.mark.parametrize(
    ("stock", "units", "threshold", "urgency", "depletion_at"),
    [
        ("1", "2", "5", RefillUrgency.CRITICAL, datetime(2026, 1, 1, 8, tzinfo=timezone.utc)),
        ("0", "1", "5", RefillUrgency.CRITICAL, NOW),
        ("10", "1", "10", RefillUrgency.URGENT, datetime(2026, 1, 10, 8, tzinfo=timezone.utc)),
        ("11", "1", "10", RefillUrgency.UPCOMING, datetime(2026, 1, 11, 8, tzinfo=timezone.utc)),
        ("20", "1", "10", RefillUrgency.SAFE, datetime(2026, 1, 20, 8, tzinfo=timezone.utc)),
    ],
)
def test_urgency_stock_and_threshold_boundaries(
    api, stock, units, threshold, urgency, depletion_at
):
    medicine_id = api["ids"]["medicine"]
    _configure_medicine(
        api["session_factory"],
        medicine_id,
        schedule=["08:00"],
        units=units,
        stock=stock,
        threshold=threshold,
    )

    forecast = _forecast(api["session_factory"], medicine_id)

    assert forecast.urgency == urgency
    assert forecast.estimated_depletion_at == depletion_at


def test_purchase_and_correction_are_reflected_from_authoritative_stock(api):
    client = api["client"]
    medicine_id = api["ids"]["medicine"]
    caregiver_id = api["ids"]["caregiver"]
    purchase = client.post(
        f"/api/medicines/{medicine_id}/stock",
        json={
            "quantity_change": "5",
            "transaction_type": "purchase",
            "recorded_by": caregiver_id,
        },
    )
    correction = client.post(
        f"/api/medicines/{medicine_id}/stock",
        json={
            "quantity_change": "-3",
            "transaction_type": "correction",
            "recorded_by": caregiver_id,
        },
    )
    assert purchase.status_code == 200
    assert correction.status_code == 200

    response = client.get(f"/api/medicines/{medicine_id}/refill-forecast")

    assert response.status_code == 200
    assert response.json()["current_available_stock"] == "12.000"
    assert len(response.json()["upcoming_scheduled_doses"]) > 0
    stock = client.get(f"/api/medicines/{medicine_id}/stock").json()
    assert stock["current_stock"] == "12.000"
    assert len(stock["transactions"]) == 2


def test_confirmed_and_accounted_doses_are_not_projected_twice(api):
    medicine_id = api["ids"]["medicine"]
    session_factory = api["session_factory"]
    _configure_medicine(
        session_factory,
        medicine_id,
        schedule=["08:00", "20:00"],
        units="1",
        stock="20",
        threshold="5",
    )

    with session_factory() as session:
        caregiver_id = api["ids"]["caregiver"]
        already_accounted_pending = DoseLog(
            medicine_id=medicine_id,
            caregiver_id=caregiver_id,
            scheduled_at=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
            status=DoseStatus.PENDING,
        )
        confirmed = DoseLog(
            medicine_id=medicine_id,
            caregiver_id=caregiver_id,
            scheduled_at=datetime(2026, 1, 1, 20, 0, tzinfo=timezone.utc),
            status=DoseStatus.CONFIRMED,
        )
        session.add_all([already_accounted_pending, confirmed])
        session.flush()
        session.add_all(
            [
                StockTransaction(
                    medicine_id=medicine_id,
                    quantity_change=Decimal("-1"),
                    transaction_type=StockTransactionType.CONSUMPTION,
                    notes=dose_stock_transaction_note(already_accounted_pending.id),
                    recorded_by=caregiver_id,
                ),
                StockTransaction(
                    medicine_id=medicine_id,
                    quantity_change=Decimal("-1"),
                    transaction_type=StockTransactionType.CONSUMPTION,
                    notes=dose_stock_transaction_note(confirmed.id),
                    recorded_by=caregiver_id,
                ),
            ]
        )
        session.commit()

    forecast = _forecast(session_factory, medicine_id)

    assert len(forecast.upcoming_scheduled_doses) == 12
    assert forecast.expected_consumption == Decimal("12")
    assert all(
        dose.scheduled_at != datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
        for dose in forecast.upcoming_scheduled_doses
    )
    assert all(
        dose.scheduled_at != datetime(2026, 1, 1, 20, 0, tzinfo=timezone.utc)
        for dose in forecast.upcoming_scheduled_doses
    )

    with session_factory() as session:
        medicine = session.get(Medicine, medicine_id)
        transaction_count = session.scalar(
            select(func.count())
            .select_from(StockTransaction)
            .where(StockTransaction.medicine_id == medicine_id)
        )
        assert medicine is not None
        assert medicine.current_stock == Decimal("20.000")
        assert transaction_count == 2


@pytest.mark.parametrize(
    ("scheduled_times", "warning"),
    [
        (["8:00"], "invalid HH:MM"),
        (["08:00", "08:00"], "duplicate"),
        ([], "No scheduled_times"),
    ],
)
def test_invalid_or_missing_schedules_return_unavailable_forecast(
    api, scheduled_times, warning
):
    medicine_id = api["ids"]["medicine"]
    session_factory = api["session_factory"]
    with session_factory() as session:
        session.execute(
            update(Medicine)
            .where(Medicine.id == medicine_id)
            .values(
                scheduled_times=scheduled_times,
                frequency_per_day=max(len(scheduled_times), 1),
            )
        )
        session.commit()

    forecast = _forecast(session_factory, medicine_id)

    assert forecast.forecast_available is False
    assert forecast.expected_consumption is None
    assert forecast.estimated_depletion_at is None
    assert any(warning in value for value in forecast.data_warnings)


def test_frequency_mismatch_returns_unavailable_forecast(api):
    medicine_id = api["ids"]["medicine"]
    session_factory = api["session_factory"]
    with session_factory() as session:
        session.execute(
            update(Medicine)
            .where(Medicine.id == medicine_id)
            .values(scheduled_times=["08:00", "20:00"], frequency_per_day=1)
        )
        session.commit()

    forecast = _forecast(session_factory, medicine_id)

    assert forecast.forecast_available is False
    assert "frequency_per_day does not match scheduled_times" in forecast.data_warnings


def test_refill_forecast_routes_and_not_found(api):
    client = api["client"]
    medicine_id = api["ids"]["medicine"]

    collection = client.get("/api/medicines/refill-forecast")
    detail = client.get(f"/api/medicines/{medicine_id}/refill-forecast")

    assert collection.status_code == 200
    assert collection.json()["total"] == 2
    assert detail.status_code == 200
    assert detail.json()["medicine_id"] == medicine_id
    assert (
        client.get("/api/medicines/99999/refill-forecast").status_code == 404
    )
