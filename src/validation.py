"""Validation utilities for tournament creation."""

from dataclasses import dataclass
from typing import Optional, List, Tuple
from datetime import datetime

import pytz

from .schedule import TournamentSchedule, format_datetime_for_display
from .config import Config


@dataclass
class ValidationResult:
    """Result of validating tournament configuration."""

    valid: bool
    errors: List[str]
    warnings: List[str]

    @classmethod
    def success(cls) -> 'ValidationResult':
        return cls(valid=True, errors=[], warnings=[])

    @classmethod
    def failure(cls, errors: List[str], warnings: List[str] = None) -> 'ValidationResult':
        if warnings is None:
            warnings = []
        return cls(valid=False, errors=errors, warnings=warnings)


@dataclass
class TournamentConfig:
    """Configuration for a single tournament."""

    sequence: int
    day: str  # 'saturday' or 'sunday'
    category: str  # 'Above 1000' or 'Below 1000'
    start_time: datetime
    name: str
    team_id: str
    team_name: str = "SMC Academy"
    rounds: int = 5
    clock_limit: int = 900  # 15 minutes in seconds
    clock_increment: int = 30  # 30 seconds
    rated: bool = True
    variant: str = "standard"
    description: Optional[str] = None
    min_rating: Optional[int] = None
    max_rating: Optional[int] = None


def validate_config(config: Config) -> ValidationResult:
    """
    Validate the general configuration.

    Checks:
    - Token is configured
    - Team ID is configured
    - Token is valid
    """
    errors = []
    warnings = []

    if not config.api_token:
        errors.append("LICHESS_API_TOKEN is not configured.")

    if not config.team_id:
        errors.append("LICHESS_TEAM_ID is not configured.")

    if errors:
        return ValidationResult.failure(errors, warnings)

    return ValidationResult.success()


def validate_tournament_config(tournament_config: TournamentConfig) -> ValidationResult:
    """
    Validate tournament-specific configuration.

    Checks:
    - Tournament name format
    - Start time is valid
    - Rounds is valid (3-100)
    - Clock settings are valid
    - Rating restrictions are valid
    """
    errors = []
    warnings = []

    # Validate tournament name
    if not tournament_config.name or len(tournament_config.name) > 30:
        errors.append(f"Tournament name must be 2-30 characters: {tournament_config.name}")

    # Validate day
    if tournament_config.day.lower() not in ('saturday', 'sunday'):
        errors.append(f"Invalid day: {tournament_config.day}")

    # Validate category
    if tournament_config.category not in ('Above 1000', 'Below 1000'):
        errors.append(f"Invalid category: {tournament_config.category}")

    # Validate start time
    if tournament_config.start_time is None:
        errors.append("Start time is required.")
    else:
        # Check if start time is in the future
        now = datetime.now(pytz.UTC)
        if tournament_config.start_time.tzinfo:
            start_utc = tournament_config.start_time.astimezone(pytz.UTC)
        else:
            start_utc = tournament_config.start_time

        if start_utc <= now:
            warnings.append("Start time should be in the future.")

    # Validate rounds
    if tournament_config.rounds < 3 or tournament_config.rounds > 100:
        errors.append(f"Number of rounds must be 3-100: {tournament_config.rounds}")

    # Validate clock settings
    if tournament_config.clock_limit < 0:
        errors.append(f"Clock limit must be non-negative: {tournament_config.clock_limit}")

    if tournament_config.clock_increment < 0 or tournament_config.clock_increment > 120:
        errors.append(f"Clock increment must be 0-120 seconds: {tournament_config.clock_increment}")

    # Validate rating restrictions
    if tournament_config.min_rating is not None:
        if tournament_config.min_rating < 1000 or tournament_config.min_rating > 2600:
            errors.append(f"Minimum rating must be 1000-2600: {tournament_config.min_rating}")

    if tournament_config.max_rating is not None:
        # Lichess API requires maxRating from a specific list: 800, 900, 1000, ...
        valid_ratings = [800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200]
        if tournament_config.max_rating not in valid_ratings:
            errors.append(f"Maximum rating must be one of {valid_ratings}: {tournament_config.max_rating}")

    if errors:
        return ValidationResult.failure(errors, warnings)

    return ValidationResult.success()


def print_tournament_preview(config: Config, tournament_config: TournamentConfig) -> None:
    """Print a preview of the tournament configuration."""
    print("Tournament:")
    print(f"  Name: {tournament_config.name}")
    print(f"  Sequence: {tournament_config.sequence}")
    print(f"  Day: {tournament_config.day}")
    print(f"  Category: {tournament_config.category}")
    print(f"  Start: {format_datetime_for_display(tournament_config.start_time)}")
    print(f"  Timezone: Pacific Time (America/Los_Angeles)")
    print(f"  Team: {tournament_config.team_id}")
    print(f"  Rounds: {tournament_config.rounds}")
    print(f"  Clock: {tournament_config.clock_limit // 60}+{tournament_config.clock_increment}")
    print(f"  Rated: {'yes' if tournament_config.rated else 'no'}")
    print(f"  Variant: {tournament_config.variant}")

    if tournament_config.min_rating is not None:
        print(f"  Min Rating: {tournament_config.min_rating}")
    if tournament_config.max_rating is not None:
        print(f"  Max Rating: {tournament_config.max_rating}")


def print_full_preview(config: Config, schedules: List['TournamentSchedule'],
                       sequence: int) -> None:
    """Print preview of all tournaments to be created."""

    for schedule in schedules:
        # Determine rating restrictions based on category
        min_rating = 1000 if schedule.category == 'Above 1000' else None
        max_rating = 999 if schedule.category == 'Below 1000' else None

        tournament_config = TournamentConfig(
            sequence=schedule.sequence,
            day=schedule.day,
            category=schedule.category,
            start_time=schedule.start_time,
            name=schedule.name,
            team_id=config.team_id,
            min_rating=min_rating,
            max_rating=max_rating
        )

        print_tournament_preview(config, tournament_config)
        print()


def validate_and_summarize(config: Config, schedules: List['TournamentSchedule'],
                           sequence: int) -> Tuple[bool, str]:
    """
    Validate all tournaments and return a summary.

    Returns:
        Tuple of (all_valid, error_message)
    """
    errors = []

    for schedule in schedules:
        min_rating = 1000 if schedule.category == 'Above 1000' else None
        max_rating = 999 if schedule.category == 'Below 1000' else None

        tournament_config = TournamentConfig(
            sequence=schedule.sequence,
            day=schedule.day,
            category=schedule.category,
            start_time=schedule.start_time,
            name=schedule.name,
            team_id=config.team_id,
            min_rating=min_rating,
            max_rating=max_rating
        )

        result = validate_tournament_config(tournament_config)
        if not result.valid:
            errors.extend([f"{schedule.name}: {e}" for e in result.errors])

    if errors:
        return False, "; ".join(errors)

    return True, "Validation passed"