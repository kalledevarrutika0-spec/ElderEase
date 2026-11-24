import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DoseLog, DoseStatus, Medicine, StockTransaction, StockTransactionType
from app.schemas.refill import (
    RefillForecast,
    RefillUrgency,
    UpcomingScheduledDose,
)
from app.services.datetime_utils import as_utc, utc_now
from app.services.errors import NotFoundError
from app.services.stock_service import dose_stock_transaction_note

FORECAST_HORIZON_DAYS = 7
_TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")


def get_refill_forecast(
    session: Session,
    medicine_id: int,
    now: datetime | None = None,
) -> RefillForecast:
    medicine = session.get(Medicine, medicine_id)
    if medicine is None:
        raise NotFoundError(f"Medicine {medicine_id} was not found.")
    return _build_forecast(session, medicine, as_utc(now or utc_now()))


def list_refill_forecasts(
    session: Session,
    offset: int,
    limit: int,
    now: datetime | None = None,
) -> tuple[list[RefillForecast], int]:
    medicines = list(
        session.scalars(
            select(Medicine).order_by(Medicine.id).offset(offset).limit(limit)
        )
    )
    total = int(session.scalar(select(func.count()).select_from(Medicine)))
    forecast_at = as_utc(now or utc_now())
    return [
        _build_forecast(session, medicine, forecast_at) for medicine in medicines
    ], total


def _build_forecast(
    session: Session, medicine: Medicine, now: datetime
) -> RefillForecast:
    stock = _as_decimal(medicine.current_stock)
    units = _as_decimal(medicine.units_per_dose)
    threshold = _as_decimal(medicine.refill_threshold)
    invalid_values = []

    if stock is None or stock < 0:
        invalid_values.append("current_stock must be a nonnegative finite number")
    if units is None or units <= 0:
        invalid_values.append("units_per_dose must be a positive finite number")
    if threshold is None or threshold < 0:
        invalid_values.append("refill_threshold must be a nonnegative finite number")

    schedule, schedule_error = _parse_schedule(
        medicine.scheduled_times, medicine.frequency_per_day
    )
    if invalid_values or schedule_error:
        warnings = invalid_values
        if schedule_error:
            warnings.append(schedule_error)
        return _unavailable_forecast(medicine, stock, threshold, warnings)

    if not schedule:
        return _unavailable_forecast(
            medicine,
            stock,
            threshold,
            ["No scheduled_times are configured; consumption and depletion cannot be estimated."],
        )

    horizon_end = now + timedelta(days=FORECAST_HORIZON_DAYS)
    upcoming = _upcoming_doses(session, medicine, schedule, units, now, horizon_end)
    expected_consumption = units * len(upcoming)
    remaining_after_horizon = max(stock - expected_consumption, Decimal("0"))
    depletion_at = _estimate_depletion(
        stock, units, upcoming, schedule, horizon_end, now
    )
    urgency = _classify_urgency(
        stock, threshold, remaining_after_horizon, upcoming, units
    )

    return RefillForecast(
        medicine_id=medicine.id,
        medicine_name=medicine.name,
        forecast_available=True,
        current_available_stock=stock,
        upcoming_scheduled_doses=upcoming,
        expected_consumption=expected_consumption,
        forecast_horizon_days=FORECAST_HORIZON_DAYS,
        estimated_remaining_supply=remaining_after_horizon,
        estimated_depletion_at=depletion_at,
        refill_threshold=threshold,
        urgency=urgency,
        explanation=_explanation(
            stock, units, expected_consumption, remaining_after_horizon, depletion_at
        ),
        data_warnings=[],
    )


def _as_decimal(value: object) -> Decimal | None:
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return result if result.is_finite() else None


def _parse_schedule(
    scheduled_times: object, frequency_per_day: object
) -> tuple[list[time] | None, str | None]:
    if scheduled_times is None:
        return [], None
    if not isinstance(scheduled_times, list):
        return None, "scheduled_times must be a list of 24-hour HH:MM values"
    if not scheduled_times:
        return [], None
    if not all(
        isinstance(value, str) and _TIME_PATTERN.fullmatch(value)
        for value in scheduled_times
    ):
        return None, "scheduled_times contains an invalid HH:MM value"
    if len(set(scheduled_times)) != len(scheduled_times):
        return None, "scheduled_times contains duplicate values"
    if not isinstance(frequency_per_day, int) or frequency_per_day != len(
        scheduled_times
    ):
        return None, "frequency_per_day does not match scheduled_times"

    times = sorted(time.fromisoformat(value) for value in scheduled_times)
    return times, None


def _upcoming_doses(
    session: Session,
    medicine: Medicine,
    schedule: list[time],
    units: Decimal,
    now: datetime,
    horizon_end: datetime,
) -> list[UpcomingScheduledDose]:
    day_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    dose_logs = list(
        session.scalars(
            select(DoseLog).where(
                DoseLog.medicine_id == medicine.id,
                DoseLog.scheduled_at >= day_start,
                DoseLog.scheduled_at < horizon_end,
            )
        )
    )
    logs_by_slot: dict[tuple[date, str], DoseLog] = {}
    for dose_log in dose_logs:
        scheduled_at = as_utc(dose_log.scheduled_at)
        key = (scheduled_at.date(), scheduled_at.strftime("%H:%M"))
        if key in logs_by_slot:
            continue
        logs_by_slot[key] = dose_log

    dose_transaction_notes = [
        dose_stock_transaction_note(dose_log.id) for dose_log in dose_logs
    ]
    accounted_notes = set()
    if dose_transaction_notes:
        accounted_notes = set(
            session.scalars(
                select(StockTransaction.notes).where(
                    StockTransaction.medicine_id == medicine.id,
                    StockTransaction.transaction_type
                    == StockTransactionType.CONSUMPTION,
                    StockTransaction.notes.in_(dose_transaction_notes),
                )
            )
        )

    upcoming = []
    for day_offset in range(FORECAST_HORIZON_DAYS + 1):
        schedule_date = now.date() + timedelta(days=day_offset)
        for scheduled_time in schedule:
            scheduled_at = datetime.combine(
                schedule_date, scheduled_time, tzinfo=timezone.utc
            )
            if scheduled_at >= horizon_end:
                continue

            dose_log = logs_by_slot.get(
                (scheduled_at.date(), scheduled_at.strftime("%H:%M"))
            )
            if dose_log is not None and (
                dose_log.status in (DoseStatus.CONFIRMED, DoseStatus.SKIPPED)
                or dose_stock_transaction_note(dose_log.id) in accounted_notes
            ):
                continue

            upcoming.append(
                UpcomingScheduledDose(
                    scheduled_at=scheduled_at,
                    expected_at=max(scheduled_at, now),
                    units=units,
                    dose_log_id=dose_log.id if dose_log is not None else None,
                    dose_log_status=dose_log.status if dose_log is not None else None,
                )
            )

    return sorted(upcoming, key=lambda dose: (dose.expected_at, dose.scheduled_at))


def _classify_urgency(
    stock: Decimal,
    threshold: Decimal,
    remaining_after_horizon: Decimal,
    upcoming: list[UpcomingScheduledDose],
    units_per_dose: Decimal,
) -> RefillUrgency:
    if stock <= 0 or (upcoming and stock < units_per_dose):
        return RefillUrgency.CRITICAL
    if stock <= threshold:
        return RefillUrgency.URGENT
    if remaining_after_horizon <= threshold:
        return RefillUrgency.UPCOMING
    return RefillUrgency.SAFE


def _estimate_depletion(
    stock: Decimal,
    units_per_dose: Decimal,
    upcoming: list[UpcomingScheduledDose],
    schedule: list[time],
    horizon_end: datetime,
    now: datetime,
) -> datetime:
    if stock <= 0:
        return now

    remaining = stock
    for dose in upcoming:
        if remaining <= dose.units:
            return dose.expected_at
        remaining -= dose.units

    doses_until_depletion = int(
        (remaining / units_per_dose).to_integral_value(rounding=ROUND_CEILING)
    )
    first_event_at, first_event_index = _first_scheduled_event(schedule, horizon_end)
    return _nth_scheduled_event(
        schedule, first_event_at.date(), first_event_index, doses_until_depletion
    )


def _first_scheduled_event(
    schedule: list[time], start_at: datetime
) -> tuple[datetime, int]:
    for day_offset in range(2):
        event_date = start_at.date() + timedelta(days=day_offset)
        for index, scheduled_time in enumerate(schedule):
            event_at = datetime.combine(
                event_date, scheduled_time, tzinfo=timezone.utc
            )
            if event_at >= start_at:
                return event_at, index
    raise RuntimeError("A daily medicine schedule did not produce a future dose.")


def _nth_scheduled_event(
    schedule: list[time],
    first_event_date: date,
    first_event_index: int,
    number: int,
) -> datetime:
    doses_left_today = len(schedule) - first_event_index
    if number <= doses_left_today:
        index = first_event_index + number - 1
        return datetime.combine(
            first_event_date, schedule[index], tzinfo=timezone.utc
        )

    remaining_number = number - doses_left_today
    day_offset = 1 + (remaining_number - 1) // len(schedule)
    schedule_index = (remaining_number - 1) % len(schedule)
    return datetime.combine(
        first_event_date + timedelta(days=day_offset),
        schedule[schedule_index],
        tzinfo=timezone.utc,
    )


def _unavailable_forecast(
    medicine: Medicine,
    stock: Decimal | None,
    threshold: Decimal | None,
    warnings: list[str],
) -> RefillForecast:
    return RefillForecast(
        medicine_id=medicine.id,
        medicine_name=medicine.name,
        forecast_available=False,
        current_available_stock=stock,
        upcoming_scheduled_doses=[],
        expected_consumption=None,
        forecast_horizon_days=FORECAST_HORIZON_DAYS,
        estimated_remaining_supply=None,
        estimated_depletion_at=None,
        refill_threshold=threshold,
        urgency=None,
        explanation=(
            "Forecast unavailable because required schedule or stock data is "
            "missing or invalid. No medicine data was changed; this estimate "
            "is not medical advice."
        ),
        data_warnings=warnings,
    )


def _explanation(
    stock: Decimal,
    units_per_dose: Decimal,
    expected_consumption: Decimal,
    remaining: Decimal,
    depletion_at: datetime,
) -> str:
    depletion_text = depletion_at.isoformat()
    return (
        f"Available stock uses medicines.current_stock ({stock}), which already "
        "reflects recorded stock transactions. Confirmed and skipped dose logs "
        "are not projected again; pending, delayed, and unlogged scheduled doses "
        "remain in the forecast. Expected consumption is "
        f"{expected_consumption} units across the next {FORECAST_HORIZON_DAYS} "
        f"days ({units_per_dose} units per scheduled dose). Estimated remaining "
        f"supply after that horizon is {remaining}. Depletion is estimated at "
        f"{depletion_text}, when the remaining stock is consumed or a scheduled "
        "dose cannot be fully covered. "
        "Elapsed unconfirmed doses are projected from now, not classified as missed. "
        "Estimate only; not medical advice."
    )
