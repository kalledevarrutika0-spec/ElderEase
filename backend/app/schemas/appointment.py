from datetime import datetime, timezone

from pydantic import AwareDatetime, Field, field_validator

from app.models.enums import AppointmentStatus
from app.schemas.common import APIRequest, ORMResponse, PageResponse


class AppointmentFields(APIRequest):
    title: str = Field(min_length=1, max_length=160)
    doctor_name: str = Field(min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=240)
    appointment_datetime: AwareDatetime
    assigned_caregiver_id: int | None = Field(default=None, gt=0)
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("title", "doctor_name")
    @classmethod
    def require_nonblank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("appointment_datetime")
    @classmethod
    def normalize_appointment_datetime(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)


class AppointmentCreate(AppointmentFields):
    pass


class AppointmentUpdate(AppointmentFields):
    pass


class AppointmentRead(ORMResponse):
    id: int
    title: str
    doctor_name: str
    location: str | None
    appointment_datetime: datetime
    assigned_caregiver_id: int | None
    status: AppointmentStatus
    notes: str | None
    created_at: datetime


class AppointmentPage(PageResponse[AppointmentRead]):
    pass
