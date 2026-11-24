from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base


class Caregiver(Base):
    __tablename__ = "caregivers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    relationship: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    medicines: Mapped[list[Medicine]] = orm_relationship(
        back_populates="assigned_caregiver"
    )
    dose_logs: Mapped[list[DoseLog]] = orm_relationship(back_populates="caregiver")
    appointments: Mapped[list[Appointment]] = orm_relationship(
        back_populates="assigned_caregiver"
    )
    notifications: Mapped[list[Notification]] = orm_relationship(
        back_populates="recipient",
        foreign_keys="Notification.recipient_id",
    )
    stock_transactions: Mapped[list[StockTransaction]] = orm_relationship(
        back_populates="recorder",
        foreign_keys="StockTransaction.recorded_by",
    )
