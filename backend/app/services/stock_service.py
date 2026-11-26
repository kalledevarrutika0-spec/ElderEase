from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Caregiver,
    Medicine,
    StockTransaction,
    StockTransactionType,
)
from app.schemas.stock import StockAdjustmentRequest
from app.services.errors import ConflictError, NotFoundError


def dose_stock_transaction_note(dose_id: int) -> str:
    return f"Dose confirmation stock deduction for dose log {dose_id}."


def get_medicine_stock(
    session: Session, medicine_id: int, family_id: int | None = None
) -> tuple[Medicine, list[StockTransaction]]:
    medicine = session.get(Medicine, medicine_id)
    if medicine is None:
        raise NotFoundError(f"Medicine {medicine_id} was not found.")
    if family_id is not None and medicine.family_id != family_id:
        raise NotFoundError(f"Medicine {medicine_id} was not found.")
    transactions = list(
        session.scalars(
            select(StockTransaction)
            .where(StockTransaction.medicine_id == medicine_id)
            .order_by(StockTransaction.created_at.desc(), StockTransaction.id.desc())
        )
    )
    return medicine, transactions


def adjust_medicine_stock(
    session: Session,
    medicine_id: int,
    data: StockAdjustmentRequest,
    family_id: int | None = None,
) -> tuple[Medicine, list[StockTransaction]]:
    try:
        with session.begin():
            medicine = session.scalar(
                select(Medicine).where(Medicine.id == medicine_id).with_for_update()
            )
            if medicine is None:
                raise NotFoundError(f"Medicine {medicine_id} was not found.")
            if family_id is not None and medicine.family_id != family_id:
                raise NotFoundError(f"Medicine {medicine_id} was not found.")
            caregiver = session.get(Caregiver, data.recorded_by)
            if caregiver is None:
                raise NotFoundError(f"Caregiver {data.recorded_by} was not found.")
            if family_id is not None and caregiver.family_id != family_id:
                raise NotFoundError(f"Caregiver {data.recorded_by} was not found.")

            update_result = session.execute(
                update(Medicine)
                .where(
                    Medicine.id == medicine.id,
                    Medicine.current_stock + data.quantity_change >= 0,
                )
                .values(
                    current_stock=Medicine.current_stock + data.quantity_change
                )
                .execution_options(synchronize_session=False)
            )
            if update_result.rowcount != 1:
                session.refresh(medicine, attribute_names=["current_stock"])
                if medicine.current_stock + data.quantity_change < 0:
                    raise ConflictError("This adjustment would make stock negative.")
                raise ConflictError("Medicine stock changed concurrently; reload and retry.")
            session.refresh(medicine, attribute_names=["current_stock"])

            transaction_type = StockTransactionType(data.transaction_type)
            transaction = StockTransaction(
                medicine=medicine,
                quantity_change=data.quantity_change,
                transaction_type=transaction_type,
                notes=data.notes,
                recorder=caregiver,
            )
            session.add(transaction)
            session.flush()
    except IntegrityError as exc:
        raise ConflictError("The stock adjustment could not be recorded.") from exc

    transactions = list(
        session.scalars(
            select(StockTransaction)
            .where(StockTransaction.medicine_id == medicine_id)
            .order_by(StockTransaction.created_at.desc(), StockTransaction.id.desc())
        )
    )
    return medicine, transactions
