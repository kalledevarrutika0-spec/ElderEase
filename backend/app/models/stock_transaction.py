from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Numeric,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base
from app.models.enums import StockTransactionType


class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    __table_args__ = (
        CheckConstraint(
            "(transaction_type = 'purchase' AND quantity_change > 0) OR "
            "(transaction_type = 'consumption' AND quantity_change < 0) OR "
            "(transaction_type = 'correction' AND quantity_change != 0)",
            name="ck_stock_transactions_quantity_sign",
        ),
        Index("ix_stock_transactions_medicine_created", "medicine_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    medicine_id: Mapped[int] = mapped_column(
        ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False
    )
    quantity_change: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    transaction_type: Mapped[StockTransactionType] = mapped_column(
        SAEnum(
            StockTransactionType,
            native_enum=False,
            values_callable=lambda enum_class: [member.value for member in enum_class],
            create_constraint=True,
            name="stock_transaction_type",
        ),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    recorded_by: Mapped[int] = mapped_column(
        ForeignKey("caregivers.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    medicine: Mapped[Medicine] = orm_relationship(back_populates="stock_transactions")
    recorder: Mapped[Caregiver] = orm_relationship(
        back_populates="stock_transactions",
        foreign_keys=[recorded_by],
    )
