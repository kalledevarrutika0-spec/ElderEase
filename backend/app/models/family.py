from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base


class FamilyProfile(Base):
    __tablename__ = "family_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    family_name: Mapped[str] = mapped_column(String(120), nullable=False)
    elder_name: Mapped[str] = mapped_column(String(120), nullable=False)
    elder_age: Mapped[int | None] = mapped_column(nullable=True)
    elder_care_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    invite_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    primary_caregiver_id: Mapped[int | None] = mapped_column(
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    members: Mapped[list[FamilyMember]] = orm_relationship(
        back_populates="family",
        cascade="all, delete-orphan",
        foreign_keys="FamilyMember.family_id",
    )


class FamilyMember(Base):
    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey("family_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    caregiver_id: Mapped[int] = mapped_column(
        ForeignKey("caregivers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    auth_user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    relationship: Mapped[str] = mapped_column(String(40), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    family: Mapped[FamilyProfile] = orm_relationship(
        back_populates="members",
        foreign_keys=[family_id],
    )
    caregiver: Mapped[Caregiver] = orm_relationship(
        foreign_keys=[caregiver_id]
    )

    @property
    def caregiver_name(self) -> str:
        return self.caregiver.name
