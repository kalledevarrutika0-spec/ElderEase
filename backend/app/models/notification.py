from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base
from app.models.enums import NotificationStatus


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("caregivers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(
            NotificationStatus,
            native_enum=False,
            values_callable=lambda enum_class: [member.value for member in enum_class],
            create_constraint=True,
            name="notification_status",
        ),
        nullable=False,
        default=NotificationStatus.PENDING,
        server_default=NotificationStatus.PENDING.value,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    recipient: Mapped[Caregiver] = orm_relationship(back_populates="notifications")
