from decimal import Decimal
from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from app.models.enums import StockTransactionType
from app.schemas.common import APIRequest, ORMResponse


class StockAdjustmentRequest(APIRequest):
    quantity_change: Decimal = Field(
        max_digits=12,
        decimal_places=3,
    )
    transaction_type: Literal["purchase", "correction"]
    recorded_by: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_transaction(self) -> "StockAdjustmentRequest":
        if self.quantity_change == 0:
            raise ValueError("quantity_change cannot be zero")
        if (
            self.transaction_type == "purchase"
            and self.quantity_change <= 0
        ):
            raise ValueError("purchase quantity_change must be positive")
        return self


class StockTransactionRead(ORMResponse):
    id: int
    medicine_id: int
    quantity_change: Decimal
    transaction_type: StockTransactionType
    notes: str | None
    created_at: datetime
    recorded_by: int


class MedicineStockRead(ORMResponse):
    medicine_id: int
    current_stock: Decimal
    transactions: list[StockTransactionRead]
