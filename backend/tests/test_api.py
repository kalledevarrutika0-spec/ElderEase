from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select

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


def _medicine_payload(caregiver_id: int | None, stock: str = "0") -> dict:
    return {
        "name": "New Demo Medicine",
        "dosage": "1 tablet",
        "units_per_dose": "1",
        "frequency_per_day": 2,
        "scheduled_times": ["09:00", "21:00"],
        "current_stock": stock,
        "refill_threshold": "3",
        "assigned_caregiver_id": caregiver_id,
        "instructions": "Synthetic test data.",
    }


def _appointment_payload(caregiver_id: int | None) -> dict:
    appointment_time = (datetime.now(timezone.utc) + timedelta(days=8)).isoformat()
    return {
        "title": "New demo appointment",
        "doctor_name": "Dr. Example",
        "location": "Demo Clinic",
        "appointment_datetime": appointment_time,
        "assigned_caregiver_id": caregiver_id,
        "status": "scheduled",
        "notes": "Synthetic test appointment.",
    }


def test_health_endpoint_and_openapi(api):
    client = api["client"]
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    assert "/api/dashboard/overview" in openapi.json()["paths"]
    assert "/api/medicines/{medicine_id}/stock" in openapi.json()["paths"]


def test_dashboard_metrics_match_database(api):
    client = api["client"]
    session_factory = api["session_factory"]
    response = client.get("/api/dashboard/overview")
    assert response.status_code == 200
    payload = response.json()

    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    with session_factory() as session:
        expected = {
            "total_medicine_count": session.scalar(
                select(func.count()).select_from(Medicine)
            ),
            "confirmed_doses_today": session.scalar(
                select(func.count())
                .select_from(DoseLog)
                .where(
                    DoseLog.status == DoseStatus.CONFIRMED,
                    DoseLog.scheduled_at >= day_start,
                    DoseLog.scheduled_at < day_end,
                )
            ),
            "pending_doses_today": session.scalar(
                select(func.count())
                .select_from(DoseLog)
                .where(
                    DoseLog.status == DoseStatus.PENDING,
                    DoseLog.scheduled_at >= day_start,
                    DoseLog.scheduled_at < day_end,
                )
            ),
            "skipped_doses_today": session.scalar(
                select(func.count())
                .select_from(DoseLog)
                .where(
                    DoseLog.status == DoseStatus.SKIPPED,
                    DoseLog.scheduled_at >= day_start,
                    DoseLog.scheduled_at < day_end,
                )
            ),
            "upcoming_appointment_count": session.scalar(
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
            ),
            "low_stock_medicine_count": session.scalar(
                select(func.count())
                .select_from(Medicine)
                .where(Medicine.current_stock <= Medicine.refill_threshold)
            ),
        }
    assert {key: payload[key] for key in expected} == expected
    assert payload["recent_family_activity"]
    assert payload["pending_doses_today"] == 2


def test_medicine_list_create_get_update_delete_and_opening_stock(api):
    client = api["client"]
    ids = api["ids"]

    listed = client.get("/api/medicines")
    assert listed.status_code == 200
    assert listed.json()["total"] == 2
    assert len(listed.json()["items"]) == 2

    created = client.post(
        "/api/medicines",
        json=_medicine_payload(ids["caregiver"], stock="5"),
    )
    assert created.status_code == 201
    medicine = created.json()
    assert medicine["current_stock"] == "5.000"
    assert client.get(f"/api/medicines/{medicine['id']}").status_code == 200

    stock = client.get(f"/api/medicines/{medicine['id']}/stock").json()
    assert len(stock["transactions"]) == 1
    assert stock["transactions"][0]["transaction_type"] == "purchase"

    update = _medicine_payload(ids["second_caregiver"])
    update.pop("current_stock")
    updated = client.put(f"/api/medicines/{medicine['id']}", json=update)
    assert updated.status_code == 200
    assert updated.json()["current_stock"] == "5.000"
    assert updated.json()["assigned_caregiver_id"] == ids["second_caregiver"]

    cannot_delete_with_history = client.delete(f"/api/medicines/{medicine['id']}")
    assert cannot_delete_with_history.status_code == 409

    empty_medicine = _medicine_payload(None)
    empty_medicine["name"] = "Disposable Demo Medicine"
    empty = client.post("/api/medicines", json=empty_medicine)
    assert empty.status_code == 201
    assert client.delete(f"/api/medicines/{empty.json()['id']}").status_code == 204


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "   "},
        {"current_stock": "-1"},
        {"scheduled_times": ["08:00"]},
        {"scheduled_times": ["8:00", "21:00"]},
        {"units_per_dose": "0"},
    ],
)
def test_invalid_medicine_input_returns_422(api, overrides):
    payload = _medicine_payload(api["ids"]["caregiver"])
    payload.update(overrides)
    response = api["client"].post("/api/medicines", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_medicine_unknown_ids_and_untracked_stock_update_rejected(api):
    client = api["client"]
    missing_id = 99999
    update = _medicine_payload(api["ids"]["caregiver"])
    update.pop("current_stock")
    stock_request = {
        "quantity_change": "1",
        "transaction_type": "purchase",
        "recorded_by": api["ids"]["caregiver"],
    }
    assert client.get(f"/api/medicines/{missing_id}").status_code == 404
    assert client.put(f"/api/medicines/{missing_id}", json=update).status_code == 404
    assert client.delete(f"/api/medicines/{missing_id}").status_code == 404
    assert client.get(f"/api/medicines/{missing_id}/stock").status_code == 404
    assert (
        client.post(
            f"/api/medicines/{missing_id}/stock",
            json=stock_request,
        ).status_code
        == 404
    )

    update_with_stock = {**update, "current_stock": "25"}
    assert (
        client.put(
            f"/api/medicines/{api['ids']['medicine']}",
            json=update_with_stock,
        ).status_code
        == 422
    )


def test_today_doses_and_unconfirmed_doses_remain_pending(api):
    response = api["client"].get("/api/doses/today")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 4
    assert any(
        dose["id"] == api["ids"]["pending_dose"] and dose["status"] == "pending"
        for dose in payload["items"]
    )
    assert any(dose["status"] == "skipped" for dose in payload["items"])


@pytest.mark.parametrize("dose_status", ["pending", "delayed", "skipped"])
def test_dose_status_logging_without_confirmation_does_not_consume_stock(
    api, dose_status
):
    response = api["client"].post(
        f"/api/doses/{api['ids']['pending_dose']}/log",
        json={"status": dose_status},
    )
    assert response.status_code == 200
    assert response.json()["status"] == dose_status
    stock = api["client"].get(
        f"/api/medicines/{api['ids']['medicine']}/stock"
    ).json()
    assert stock["current_stock"] == "10.000"
    assert stock["transactions"] == []


def test_confirming_a_dose_consumes_stock_once_and_is_idempotent(api):
    client = api["client"]
    dose_id = api["ids"]["pending_dose"]
    medicine_id = api["ids"]["medicine"]
    request = {"status": "confirmed", "notes": "Synthetic dose confirmation."}

    confirmed = client.post(f"/api/doses/{dose_id}/log", json=request)
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert confirmed.json()["logged_at"].endswith(("Z", "+00:00"))

    repeated = client.post(
        f"/api/doses/{dose_id}/log",
        json={"status": "confirmed", "notes": "Edited confirmation note."},
    )
    assert repeated.status_code == 200
    assert repeated.json()["notes"] == "Edited confirmation note."
    stock = client.get(f"/api/medicines/{medicine_id}/stock").json()
    assert stock["current_stock"] == "8.000"
    assert len(stock["transactions"]) == 1
    assert stock["transactions"][0]["transaction_type"] == "consumption"

    reverted = client.post(
        f"/api/doses/{dose_id}/log",
        json={"status": "skipped"},
    )
    assert reverted.status_code == 409


def test_dose_insufficient_stock_rolls_back_status_and_stock(api):
    client = api["client"]
    dose_id = api["ids"]["low_stock_dose"]
    medicine_id = api["ids"]["low_stock_medicine"]
    response = client.post(
        f"/api/doses/{dose_id}/log",
        json={"status": "confirmed"},
    )
    assert response.status_code == 409
    assert client.get("/api/doses/today").json()["items"][-1]["status"] == "pending"
    stock = client.get(f"/api/medicines/{medicine_id}/stock").json()
    assert stock["current_stock"] == "1.000"
    assert stock["transactions"] == []


def test_invalid_and_missing_dose_logs(api):
    client = api["client"]
    assert (
        client.post(
            f"/api/doses/{api['ids']['pending_dose']}/log",
            json={"status": "missed"},
        ).status_code
        == 422
    )
    assert (
        client.post("/api/doses/99999/log", json={"status": "confirmed"}).status_code
        == 404
    )


def test_stock_purchase_correction_and_negative_guard(api):
    client = api["client"]
    medicine_id = api["ids"]["medicine"]
    caregiver_id = api["ids"]["caregiver"]

    purchase = client.post(
        f"/api/medicines/{medicine_id}/stock",
        json={
            "quantity_change": "5",
            "transaction_type": "purchase",
            "recorded_by": caregiver_id,
            "notes": "Test purchase.",
        },
    )
    assert purchase.status_code == 200
    assert purchase.json()["current_stock"] == "15.000"

    correction = client.post(
        f"/api/medicines/{medicine_id}/stock",
        json={
            "quantity_change": "-3",
            "transaction_type": "correction",
            "recorded_by": caregiver_id,
            "notes": "Test correction.",
        },
    )
    assert correction.status_code == 200
    assert correction.json()["current_stock"] == "12.000"
    assert len(correction.json()["transactions"]) == 2

    negative = client.post(
        f"/api/medicines/{medicine_id}/stock",
        json={
            "quantity_change": "-100",
            "transaction_type": "correction",
            "recorded_by": caregiver_id,
        },
    )
    assert negative.status_code == 409
    stock = client.get(f"/api/medicines/{medicine_id}/stock").json()
    assert stock["current_stock"] == "12.000"
    assert len(stock["transactions"]) == 2

    invalid_purchase = client.post(
        f"/api/medicines/{medicine_id}/stock",
        json={
            "quantity_change": "-1",
            "transaction_type": "purchase",
            "recorded_by": caregiver_id,
        },
    )
    assert invalid_purchase.status_code == 422


def test_stock_missing_caregiver_and_invalid_medicine_ids(api):
    client = api["client"]
    medicine_id = api["ids"]["medicine"]
    assert client.get("/api/medicines/99999/stock").status_code == 404
    missing_caregiver = client.post(
        f"/api/medicines/{medicine_id}/stock",
        json={
            "quantity_change": "1",
            "transaction_type": "purchase",
            "recorded_by": 99999,
        },
    )
    assert missing_caregiver.status_code == 404


def test_appointment_list_create_update_delete_and_assignment(api):
    client = api["client"]
    ids = api["ids"]
    listed = client.get("/api/appointments")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    created = client.post(
        "/api/appointments",
        json=_appointment_payload(ids["caregiver"]),
    )
    assert created.status_code == 201
    appointment_id = created.json()["id"]
    assert created.json()["assigned_caregiver_id"] == ids["caregiver"]
    assert created.json()["appointment_datetime"].endswith(("Z", "+00:00"))

    update = _appointment_payload(ids["second_caregiver"])
    update["status"] = "confirmed"
    updated = client.put(
        f"/api/appointments/{appointment_id}",
        json=update,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "confirmed"
    assert updated.json()["assigned_caregiver_id"] == ids["second_caregiver"]

    assert client.delete(f"/api/appointments/{appointment_id}").status_code == 204


def test_appointment_validation_and_missing_ids(api):
    client = api["client"]
    payload = _appointment_payload(api["ids"]["caregiver"])
    payload["appointment_datetime"] = "2030-01-01T10:00:00"
    assert client.post("/api/appointments", json=payload).status_code == 422

    payload = _appointment_payload(99999)
    assert client.post("/api/appointments", json=payload).status_code == 404
    assert client.put("/api/appointments/99999", json=payload).status_code == 404
    assert client.delete("/api/appointments/99999").status_code == 404


def test_caregiver_list_and_detail(api):
    client = api["client"]
    listed = client.get("/api/caregivers")
    assert listed.status_code == 200
    assert listed.json()["total"] == 2
    assert client.get(f"/api/caregivers/{api['ids']['caregiver']}").status_code == 200
    assert client.get("/api/caregivers/99999").status_code == 404


def test_notification_list_acknowledgement_and_missing_id(api):
    client = api["client"]
    listed = client.get("/api/notifications")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    notification_id = api["ids"]["notification"]
    acknowledged = client.patch(
        f"/api/notifications/{notification_id}/acknowledge"
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"
    first_acknowledged_at = acknowledged.json()["acknowledged_at"]
    repeated = client.patch(
        f"/api/notifications/{notification_id}/acknowledge"
    )
    assert repeated.status_code == 200
    assert repeated.json()["acknowledged_at"] == first_acknowledged_at
    assert client.patch("/api/notifications/99999/acknowledge").status_code == 404
