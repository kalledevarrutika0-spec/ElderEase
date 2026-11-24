from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    DoseLog,
    DoseStatus,
    Medicine,
    StockTransaction,
    StockTransactionType,
)
from app.schemas.dose import DoseLogRequest
from app.services.datetime_utils import utc_day_bounds, utc_now
from app.services.errors import ConflictError, NotFoundError
from app.services.stock_service import dose_stock_transaction_note


def list_today_doses(
    session: Session, offset: int, limit: int
) -> tuple[list[DoseLog], int]:
    start, end = utc_day_bounds(utc_now())
    items = list(
        session.scalars(
            select(DoseLog)
            .where(DoseLog.scheduled_at >= start, DoseLog.scheduled_at < end)
            .order_by(DoseLog.scheduled_at, DoseLog.id)
            .offset(offset)
            .limit(limit)
        )
    )
    total = int(
        session.scalar(
            select(func.count())
            .select_from(DoseLog)
            .where(DoseLog.scheduled_at >= start, DoseLog.scheduled_at < end)
        )
    )
    return items, total


def log_dose(session: Session, dose_id: int, data: DoseLogRequest) -> DoseLog:
    try:
        with session.begin():
            dose = session.scalar(
                select(DoseLog).where(DoseLog.id == dose_id).with_for_update()
            )
            if dose is None:
                raise NotFoundError(f"Dose log {dose_id} was not found.")

            if (
                dose.status == DoseStatus.CONFIRMED
                and data.status != DoseStatus.CONFIRMED
            ):
                raise ConflictError(
                    "A confirmed dose cannot be reverted; record corrections separately."
                )

            if dose.status == DoseStatus.CONFIRMED:
                if "notes" in data.model_fields_set:
                    dose.notes = data.notes
            else:
                values = {
                    "status": data.status,
                    "logged_at": (
                        None if data.status == DoseStatus.PENDING else utc_now()
                    ),
                }
                if "notes" in data.model_fields_set:
                    values["notes"] = data.notes
                update_result = session.execute(
                    update(DoseLog)
                    .where(
                        DoseLog.id == dose.id,
                        DoseLog.status == dose.status,
                    )
                    .values(**values)
                    .execution_options(synchronize_session=False)
                )
                if update_result.rowcount != 1:
                    session.refresh(dose)
                    if not (
                        dose.status == DoseStatus.CONFIRMED
                        and data.status == DoseStatus.CONFIRMED
                    ):
                        raise ConflictError(
                            "Dose status changed concurrently; reload and retry."
                        )
                    if "notes" in data.model_fields_set:
                        dose.notes = data.notes
                else:
                    session.refresh(dose)
                    if data.status == DoseStatus.CONFIRMED:
                        _consume_stock_once(session, dose)
            session.flush()
    except IntegrityError as exc:
        raise ConflictError("The dose could not be logged due to a data conflict.") from exc
    return dose


def _consume_stock_once(session: Session, dose: DoseLog) -> None:
    transaction_note = dose_stock_transaction_note(dose.id)
    prior_transaction = session.scalar(
        select(StockTransaction.id).where(
            StockTransaction.medicine_id == dose.medicine_id,
            StockTransaction.transaction_type == StockTransactionType.CONSUMPTION,
            StockTransaction.notes == transaction_note,
        )
    )
    if prior_transaction is not None:
        return

    medicine = session.get(Medicine, dose.medicine_id)
    if medicine is None:
        raise NotFoundError(f"Medicine {dose.medicine_id} was not found.")

    update_result = session.execute(
        update(Medicine)
        .where(
            Medicine.id == medicine.id,
            Medicine.current_stock >= medicine.units_per_dose,
        )
        .values(current_stock=Medicine.current_stock - medicine.units_per_dose)
        .execution_options(synchronize_session=False)
    )
    if update_result.rowcount != 1:
        session.refresh(medicine, attribute_names=["current_stock"])
        if medicine.current_stock < medicine.units_per_dose:
            raise ConflictError(
                f"Insufficient stock to confirm this dose of medicine {medicine.id}."
            )
        raise ConflictError("Medicine stock changed concurrently; reload and retry.")
    session.refresh(medicine, attribute_names=["current_stock"])

    session.add(
        StockTransaction(
            medicine_id=medicine.id,
            quantity_change=-medicine.units_per_dose,
            transaction_type=StockTransactionType.CONSUMPTION,
            notes=transaction_note,
            recorded_by=dose.caregiver_id,
        )
    )
