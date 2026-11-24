import re
from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator, model_validator

from app.schemas.common import APIRequest, ORMResponse, PageResponse

_TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")


class MedicineCreate(APIRequest):
    name: str = Field(min_length=1, max_length=120)
    dosage: str = Field(min_length=1, max_length=80)
    units_per_dose: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    frequency_per_day: int = Field(ge=1, le=24)
    scheduled_times: list[str] = Field(min_length=1, max_length=24)
    current_stock: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=3)
    refill_threshold: Decimal = Field(ge=0, max_digits=12, decimal_places=3)
    assigned_caregiver_id: int | None = Field(default=None, gt=0)
    instructions: str | None = Field(default=None, max_length=4000)

    @field_validator("name", "dosage")
    @classmethod
    def require_nonblank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @model_validator(mode="after")
    def validate_schedule_and_opening_stock(self) -> "MedicineCreate":
        _validate_schedule(self.scheduled_times, self.frequency_per_day)
        if self.current_stock > 0 and self.assigned_caregiver_id is None:
            raise ValueError(
                "assigned_caregiver_id is required to audit opening stock"
            )
        return self


class MedicineUpdate(APIRequest):
    name: str = Field(min_length=1, max_length=120)
    dosage: str = Field(min_length=1, max_length=80)
    units_per_dose: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    frequency_per_day: int = Field(ge=1, le=24)
    scheduled_times: list[str] = Field(min_length=1, max_length=24)
    refill_threshold: Decimal = Field(ge=0, max_digits=12, decimal_places=3)
    assigned_caregiver_id: int | None = Field(default=None, gt=0)
    instructions: str | None = Field(default=None, max_length=4000)

    @field_validator("name", "dosage")
    @classmethod
    def require_nonblank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @model_validator(mode="after")
    def validate_schedule(self) -> "MedicineUpdate":
        _validate_schedule(self.scheduled_times, self.frequency_per_day)
        return self


class MedicineRead(ORMResponse):
    id: int
    name: str
    dosage: str
    units_per_dose: Decimal
    frequency_per_day: int
    scheduled_times: list[str]
    current_stock: Decimal
    refill_threshold: Decimal
    assigned_caregiver_id: int | None
    instructions: str | None
    created_at: datetime
    updated_at: datetime


class MedicinePage(PageResponse[MedicineRead]):
    pass


def _validate_schedule(times: list[str], frequency_per_day: int) -> None:
    if any(not _TIME_PATTERN.fullmatch(value) for value in times):
        raise ValueError("scheduled_times must use 24-hour HH:MM values")
    if len(set(times)) != len(times):
        raise ValueError("scheduled_times cannot contain duplicates")
    if len(times) != frequency_per_day:
        raise ValueError("scheduled_times count must match frequency_per_day")
