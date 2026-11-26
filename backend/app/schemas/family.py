from datetime import datetime

from pydantic import Field

from app.schemas.common import APIRequest, ORMResponse


class FamilyProfileCreate(APIRequest):
    family_name: str = Field(min_length=2, max_length=120)
    elder_name: str = Field(min_length=2, max_length=120)
    elder_age: int | None = Field(default=None, ge=0, le=130)
    elder_care_notes: str | None = Field(default=None, max_length=1000)
    caregiver_name: str = Field(min_length=2, max_length=120)
    relationship: str = Field(min_length=2, max_length=40)
    role: str = Field(default="Primary caregiver", max_length=80)


class FamilyProfileUpdate(APIRequest):
    family_name: str = Field(min_length=2, max_length=120)
    elder_name: str = Field(min_length=2, max_length=120)
    elder_age: int | None = Field(default=None, ge=0, le=130)
    elder_care_notes: str | None = Field(default=None, max_length=1000)


class FamilyMemberLink(APIRequest):
    invite_code: str = Field(min_length=6, max_length=32)
    caregiver_name: str = Field(min_length=2, max_length=120)
    relationship: str = Field(min_length=2, max_length=40)
    role: str = Field(default="Caregiver", max_length=80)


class FamilyMemberRead(ORMResponse):
    id: int
    caregiver_id: int
    caregiver_name: str
    relationship: str
    role: str
    is_primary: bool
    created_at: datetime


class FamilyProfileRead(ORMResponse):
    id: int
    family_name: str
    elder_name: str
    elder_age: int | None
    elder_care_notes: str | None
    invite_code: str
    primary_caregiver_id: int | None
    members: list[FamilyMemberRead]
    created_at: datetime
    updated_at: datetime
