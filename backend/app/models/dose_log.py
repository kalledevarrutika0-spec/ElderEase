from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base
from app.models.enums import DoseStatus


class DoseLog(Base):
    __tablename__ = "dose_logs"
    __table_args__ = (
        UniqueConstraint(
            "medicine_id",
            "scheduled_at",
            name="uq_dose_logs_medicine_scheduled_at",
        ),
        Index("ix_dose_logs_scheduled_at", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    medicine_id: Mapped[int] = mapped_column(
        ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False
    )
    caregiver_id: Mapped[int] = mapped_column(
        ForeignKey("caregivers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[DoseStatus] = mapped_column(
        SAEnum(
            DoseStatus,
            native_enum=False,
            values_callable=lambda enum_class: [member.value for member in enum_class],
            create_constraint=True,
            name="dose_status",
        ),
        nullable=False,
        default=DoseStatus.PENDING,
        server_default=DoseStatus.PENDING.value,
        index=True,
    )
    logged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    medicine: Mapped[Medicine] = orm_relationship(back_populates="dose_logs")
    caregiver: Mapped[Caregiver] = orm_relationship(back_populates="dose_logs")
