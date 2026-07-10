# Date/Time Utility Functions.

from datetime import date, datetime, timedelta, timezone
from typing import Optional


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def days_between(start: date, end: date) -> int:
    """Calculate days between two dates."""
    return (end - start).days


def add_business_days(start_date: date, days: int) -> date:
    current = start_date
    added = 0
    
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            added += 1
    
    return current


def get_month_start_end(reference_date: Optional[date] = None) -> tuple:
    if reference_date is None:
        reference_date = date.today()
    
    month_start = reference_date.replace(day=1)
    
    # Calculate next month start, then subtract one day
    if reference_date.month == 12:
        next_month = reference_date.replace(year=reference_date.year + 1, month=1, day=1)
    else:
        next_month = reference_date.replace(month=reference_date.month + 1, day=1)
    
    month_end = next_month - timedelta(days=1)
    
    return month_start, month_end


def parse_iso_date(date_string: str) -> Optional[date]:
    try:
        return datetime.fromisoformat(date_string.replace("Z", "+00:00")).date()
    except (ValueError, AttributeError):
        return None


# TODO: Add Kenyan timezone handling (EAT, UTC+3)
# TODO: Add public holiday calendar
# TODO: Add loan repayment date calculations