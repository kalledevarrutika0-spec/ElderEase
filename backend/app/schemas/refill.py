from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field

from app.models.enums import DoseStatus
from app.schemas.common import ORMResponse, PageResponse


class RefillUrgency(str, Enum):
    CRITICAL = "CRITICAL"
    URGENT = "URGENT"
    UPCOMING = "UPCOMING"
    SAFE = "SAFE"


class UpcomingScheduledDose(ORMResponse):
    scheduled_at: datetime
    expected_at: datetime
    units: Decimal
    dose_log_id: int | None
    dose_log_status: DoseStatus | None


class RefillForecast(ORMResponse):
    medicine_id: int
    medicine_name: str
    forecast_available: bool
    current_available_stock: Decimal | None
    upcoming_scheduled_doses: list[UpcomingScheduledDose]
    expected_consumption: Decimal | None
    forecast_horizon_days: int = Field(ge=1)
    estimated_remaining_supply: Decimal | None
    estimated_depletion_at: datetime | None
    refill_threshold: Decimal | None
    urgency: RefillUrgency | None
    explanation: str
    data_warnings: list[str]


class RefillForecastPage(PageResponse[RefillForecast]):
    pass
