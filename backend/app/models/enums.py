from enum import Enum


class DoseStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DELAYED = "delayed"
    SKIPPED = "skipped"


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"


class StockTransactionType(str, Enum):
    PURCHASE = "purchase"
    CONSUMPTION = "consumption"
    CORRECTION = "correction"
