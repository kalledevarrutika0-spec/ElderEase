from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship
from sqlalchemy.orm import validates

from app.database import Base

_TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")


class Medicine(Base):
    __tablename__ = "medicines"
    __table_args__ = (
        CheckConstraint(
            "units_per_dose > 0", name="ck_medicines_units_per_dose_positive"
        ),
        CheckConstraint(
            "frequency_per_day >= 1", name="ck_medicines_frequency_per_day_positive"
        ),
        CheckConstraint("current_stock >= 0", name="ck_medicines_stock_nonnegative"),
        CheckConstraint(
            "refill_threshold >= 0", name="ck_medicines_threshold_nonnegative"
        ),
        Index("ix_medicines_assigned_caregiver_id", "assigned_caregiver_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    dosage: Mapped[str] = mapped_column(String(80), nullable=False)
    units_per_dose: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    frequency_per_day: Mapped[int] = mapped_column(nullable=False)
    scheduled_times: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    current_stock: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    refill_threshold: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    assigned_caregiver_id: Mapped[int | None] = mapped_column(
        ForeignKey("caregivers.id", ondelete="SET NULL"), nullable=True
    )
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    assigned_caregiver: Mapped[Caregiver | None] = orm_relationship(
        back_populates="medicines"
    )
    dose_logs: Mapped[list[DoseLog]] = orm_relationship(back_populates="medicine")
    stock_transactions: Mapped[list[StockTransaction]] = orm_relationship(
        back_populates="medicine"
    )

    @validates("scheduled_times")
    def validate_scheduled_times(self, key: str, value: list[str]) -> list[str]:
        if not isinstance(value, list) or not all(
            isinstance(item, str) and _TIME_PATTERN.fullmatch(item) for item in value
        ):
            raise ValueError("scheduled_times must be a list of 24-hour HH:MM strings")
        if len(set(value)) != len(value):
            raise ValueError("scheduled_times cannot contain duplicates")
        return value
