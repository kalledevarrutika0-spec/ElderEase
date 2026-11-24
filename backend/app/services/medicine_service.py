from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import DoseLog, Medicine, StockTransaction, StockTransactionType
from app.schemas.medicine import MedicineCreate, MedicineUpdate
from app.services.caregiver_service import get_optional_caregiver
from app.services.errors import ConflictError, NotFoundError


def list_medicines(
    session: Session, offset: int, limit: int
) -> tuple[list[Medicine], int]:
    items = list(
        session.scalars(
            select(Medicine).order_by(Medicine.id).offset(offset).limit(limit)
        )
    )
    total = int(session.scalar(select(func.count()).select_from(Medicine)))
    return items, total


def get_medicine(session: Session, medicine_id: int) -> Medicine:
    medicine = session.get(Medicine, medicine_id)
    if medicine is None:
        raise NotFoundError(f"Medicine {medicine_id} was not found.")
    return medicine


def create_medicine(session: Session, data: MedicineCreate) -> Medicine:
    try:
        with session.begin():
            caregiver = get_optional_caregiver(
                session, data.assigned_caregiver_id
            )
            medicine = Medicine(
                name=data.name.strip(),
                dosage=data.dosage.strip(),
                units_per_dose=data.units_per_dose,
                frequency_per_day=data.frequency_per_day,
                scheduled_times=data.scheduled_times,
                current_stock=data.current_stock,
                refill_threshold=data.refill_threshold,
                assigned_caregiver=caregiver,
                instructions=data.instructions,
            )
            session.add(medicine)
            session.flush()

            if data.current_stock > 0 and caregiver is not None:
                session.add(
                    StockTransaction(
                        medicine_id=medicine.id,
                        quantity_change=data.current_stock,
                        transaction_type=StockTransactionType.PURCHASE,
                        notes="Opening stock recorded when medicine was created.",
                        recorded_by=caregiver.id,
                    )
                )
    except IntegrityError as exc:
        raise ConflictError(
            "The medicine could not be created due to a data conflict."
        ) from exc
    return medicine


def update_medicine(
    session: Session, medicine_id: int, data: MedicineUpdate
) -> Medicine:
    try:
        with session.begin():
            medicine = session.get(Medicine, medicine_id)
            if medicine is None:
                raise NotFoundError(f"Medicine {medicine_id} was not found.")
            caregiver = get_optional_caregiver(
                session, data.assigned_caregiver_id
            )
            medicine.name = data.name.strip()
            medicine.dosage = data.dosage.strip()
            medicine.units_per_dose = data.units_per_dose
            medicine.frequency_per_day = data.frequency_per_day
            medicine.scheduled_times = data.scheduled_times
            medicine.refill_threshold = data.refill_threshold
            medicine.assigned_caregiver = caregiver
            medicine.instructions = data.instructions
            session.flush()
    except IntegrityError as exc:
        raise ConflictError(
            "The medicine could not be updated due to a data conflict."
        ) from exc
    return medicine


def delete_medicine(session: Session, medicine_id: int) -> None:
    with session.begin():
        medicine = session.get(Medicine, medicine_id)
        if medicine is None:
            raise NotFoundError(f"Medicine {medicine_id} was not found.")
        has_dose_history = session.scalar(
            select(DoseLog.id).where(DoseLog.medicine_id == medicine_id).limit(1)
        )
        has_stock_history = session.scalar(
            select(StockTransaction.id)
            .where(StockTransaction.medicine_id == medicine_id)
            .limit(1)
        )
        if has_dose_history or has_stock_history:
            raise ConflictError(
                "Medicine with dose or stock history cannot be deleted."
            )
        session.delete(medicine)


