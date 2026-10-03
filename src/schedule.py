"""Tournament scheduling utilities."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List
import pytz


@dataclass
class TournamentSchedule:
    """Schedule information for a tournament."""

    sequence: int
    day: str  # 'saturday' or 'sunday'
    category: str  # 'Above 1000' or 'Below 1000'
    start_time: datetime  # in Pacific timezone
    name: str

    @property
    def full_name(self) -> str:
        """Return the full tournament name."""
        return f"{self.sequence} SMC {self.day.capitalize()} {self.category}"


def get_next_saturday_12pm(timezone_name: str = "America/Los_Angeles") -> datetime:
    """
    Get the next Saturday at 12:00 PM Pacific time.

    If called on a Saturday before noon, returns today.
    If called on a Saturday at or after noon, returns next Saturday.
    """
    tz = pytz.timezone(timezone_name)
    now = datetime.now(tz)

    # Calculate days until next Saturday (weekday 5)
    days_ahead = 5 - now.weekday()
    if days_ahead == 0 and now.hour >= 12:
        days_ahead = 7  # Next Saturday

    # Create Saturday at 12:00 PM - use astimezone to handle timezone properly
    next_saturday = now + timedelta(days=days_ahead)
    saturday_noon = next_saturday.replace(hour=12, minute=0, second=0, microsecond=0)

    return saturday_noon.astimezone(tz)


def get_next_sunday_12pm(timezone_name: str = "America/Los_Angeles") -> datetime:
    """
    Get the next Sunday at 12:00 PM Pacific time.

    If called on a Sunday before noon, returns today.
    If called on a Sunday at or after noon, returns next Sunday.
    """
    tz = pytz.timezone(timezone_name)
    now = datetime.now(tz)

    # Calculate days until next Sunday (weekday 6)
    days_ahead = 6 - now.weekday()
    if days_ahead == 0 and now.hour >= 12:
        days_ahead = 7  # Next Sunday

    # Create Sunday at 12:00 PM - use astimezone to handle timezone properly
    next_sunday = now + timedelta(days=days_ahead)
    sunday_noon = next_sunday.replace(hour=12, minute=0, second=0, microsecond=0)

    return sunday_noon.astimezone(tz)


def datetime_to_millis(dt: datetime) -> int:
    """Convert datetime to milliseconds since epoch (UTC)."""
    utc_dt = dt.astimezone(pytz.UTC)
    return int(utc_dt.timestamp() * 1000)


def format_datetime_for_display(dt: datetime) -> str:
    """Format datetime for human display."""
    return dt.strftime("%Y-%m-%d %H:%M %Z")


def get_tournament_schedules(sequence: int, timezone_name: str = "America/Los_Angeles") -> List[TournamentSchedule]:
    """
    Get all four tournament schedules for a given sequence.

    Returns:
        List of 4 TournamentSchedule objects in order:
        - Saturday Above 1000
        - Saturday Below 1000
        - Sunday Above 1000
        - Sunday Below 1000
    """
    # Saturday should be before Sunday
    saturday = get_next_saturday_12pm(timezone_name)
    # Sunday should be the Sunday of the same week (or next week if Saturday is today)
    sunday = get_next_sunday_12pm(timezone_name)

    # If Saturday and Sunday are in the same week, we need to adjust
    # The Sunday should be the Sunday AFTER the Saturday for a proper weekly sequence
    sat_week = saturday.isocalendar()[:2]  # (year, week_number)
    sun_week = sunday.isocalendar()[:2]

    # If we're scheduling for the same week, and Saturday comes before Sunday
    # we want Sunday to be the Sunday of the same week
    # But if today is Saturday afternoon, sunday might be next week's Sunday
    if sat_week[0] == sun_week[0] and sat_week[1] == sun_week[1]:
        # Same week - ensure Sunday is after Saturday
        if sunday <= saturday:
            sunday = sunday + timedelta(days=7)

    return [
        TournamentSchedule(
            sequence=sequence,
            day='saturday',
            category='Above 1000',
            start_time=saturday,
            name=f"{sequence} SMC Saturday Above 1000"
        ),
        TournamentSchedule(
            sequence=sequence,
            day='saturday',
            category='Below 1000',
            start_time=saturday,
            name=f"{sequence} SMC Saturday Below 1000"
        ),
        TournamentSchedule(
            sequence=sequence,
            day='sunday',
            category='Above 1000',
            start_time=sunday,
            name=f"{sequence} SMC Sunday Above 1000"
        ),
        TournamentSchedule(
            sequence=sequence,
            day='sunday',
            category='Below 1000',
            start_time=sunday,
            name=f"{sequence} SMC Sunday Below 1000"
        ),
    ]


def get_single_day_schedules(sequence: int, day: str, timezone_name: str = "America/Los_Angeles") -> List[TournamentSchedule]:
    """
    Get tournament schedules for a specific day.

    Args:
        sequence: The tournament sequence number
        day: 'saturday' or 'sunday'
        timezone_name: IANA timezone name

    Returns:
        List of 2 TournamentSchedule objects for the specified day
    """
    if day.lower() == 'saturday':
        start = get_next_saturday_12pm(timezone_name)
    elif day.lower() == 'sunday':
        start = get_next_sunday_12pm(timezone_name)
    else:
        raise ValueError(f"Invalid day: {day}. Must be 'saturday' or 'sunday'.")

    return [
        TournamentSchedule(
            sequence=sequence,
            day=day.lower(),
            category='Above 1000',
            start_time=start,
            name=f"{sequence} SMC {day.capitalize()} Above 1000"
        ),
        TournamentSchedule(
            sequence=sequence,
            day=day.lower(),
            category='Below 1000',
            start_time=start,
            name=f"{sequence} SMC {day.capitalize()} Below 1000"
        ),
    ]