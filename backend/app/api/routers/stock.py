from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.api.responses import COMMON_ERROR_RESPONSES
from app.database import get_db
from app.schemas.stock import MedicineStockRead, StockAdjustmentRequest
from app.services.stock_service import adjust_medicine_stock, get_medicine_stock
from app.core.auth import get_family_member
from app.models import Caregiver, FamilyMember, Medicine
from app.services.errors import NotFoundError

router = APIRouter(
    prefix="/medicines",
    tags=["stock"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get(
    "/{medicine_id}/stock",
    response_model=MedicineStockRead,
    summary="Get medicine stock and transaction history",
)
def read_medicine_stock(
    medicine_id: int = Path(gt=0),
    session: Session = Depends(get_db),
    member: FamilyMember = Depends(get_family_member),
) -> MedicineStockRead:
    medicine, transactions = get_medicine_stock(
        session, medicine_id, member.family_id
    )
    return MedicineStockRead(
        medicine_id=medicine.id,
        current_stock=medicine.current_stock,
        transactions=transactions,
    )


@router.post(
    "/{medicine_id}/stock",
    response_model=MedicineStockRead,
    status_code=status.HTTP_200_OK,
    summary="Record a purchase or stock correction",
)
def add_stock_transaction(
    data: StockAdjustmentRequest,
    medicine_id: int = Path(gt=0),
    session: Session = Depends(get_db),
    member: FamilyMember = Depends(get_family_member),
) -> MedicineStockRead:
    medicine, transactions = adjust_medicine_stock(
        session, medicine_id, data, member.family_id
    )
    return MedicineStockRead(
        medicine_id=medicine.id,
        current_stock=medicine.current_stock,
        transactions=transactions,
    )
