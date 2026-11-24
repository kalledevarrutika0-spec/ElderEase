from datetime import datetime
from typing import Literal

from app.schemas.common import ORMResponse


class FamilyActivity(ORMResponse):
    activity_type: Literal["dose", "stock_transaction", "appointment", "notification"]
    description: str
    occurred_at: datetime
    caregiver_name: str | None


class DashboardOverview(ORMResponse):
    total_medicine_count: int
    confirmed_doses_today: int
    pending_doses_today: int
    skipped_doses_today: int
    upcoming_appointment_count: int
    low_stock_medicine_count: int
    recent_family_activity: list[FamilyActivity]
