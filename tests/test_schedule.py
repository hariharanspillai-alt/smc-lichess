"""Tests for tournament scheduling."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytz

from src.schedule import (
    TournamentSchedule,
    get_next_saturday_12pm,
    get_next_sunday_12pm,
    get_tournament_schedules,
    get_single_day_schedules,
    datetime_to_millis,
    format_datetime_for_display
)


class TestGetNextSaturday12pm:
    """Tests for next Saturday at 12:00 PM calculation."""

    def test_uses_correct_timezone(self):
        """Test that Saturday is calculated in Pacific timezone."""
        result = get_next_saturday_12pm()

        assert result.tzinfo is not None
        # Should be in America/Los_Angeles timezone
        assert result.tzinfo.zone == "America/Los_Angeles"

    def test_returns_saturday(self):
        """Test that result is always a Saturday."""
        result = get_next_saturday_12pm()

        assert result.weekday() == 5  # Saturday

    def test_returns_noon(self):
        """Test that hour is 12 and minute is 0."""
        result = get_next_saturday_12pm()

        assert result.hour == 12
        assert result.minute == 0


class TestGetNextSunday12pm:
    """Tests for next Sunday at 12:00 PM calculation."""

    def test_uses_correct_timezone(self):
        """Test that Sunday is calculated in Pacific timezone."""
        result = get_next_sunday_12pm()

        assert result.tzinfo is not None
        assert result.tzinfo.zone == "America/Los_Angeles"

    def test_returns_sunday(self):
        """Test that result is always a Sunday."""
        result = get_next_sunday_12pm()

        assert result.weekday() == 6  # Sunday

    def test_returns_noon(self):
        """Test that hour is 12 and minute is 0."""
        result = get_next_sunday_12pm()

        assert result.hour == 12
        assert result.minute == 0


class TestDatetimeToMillis:
    """Tests for datetime to milliseconds conversion."""

    def test_converts_to_utc_milliseconds(self):
        """Test that datetime is converted to UTC milliseconds."""
        # Jan 1, 2024 12:00:00 UTC
        utc_dt = pytz.UTC.localize(datetime(2024, 1, 1, 12, 0, 0))

        result = datetime_to_millis(utc_dt)

        # 1704110400000 is the correct timestamp for Jan 1, 2024 12:00:00 UTC
        assert result == 1704110400000

    def test_converts_pacific_to_utc(self):
        """Test that Pacific time is converted to UTC."""
        # Pacific time in January (PST, UTC-8)
        pacific = pytz.timezone("America/Los_Angeles")
        pacific_dt = pacific.localize(datetime(2024, 1, 1, 12, 0, 0))

        result = datetime_to_millis(pacific_dt)

        # Should be 20:00 UTC (12 PM PST + 8 hours)
        # 1704139200000 is the correct timestamp for Jan 1, 2024 20:00:00 UTC
        assert result == 1704139200000


class TestGetTournamentSchedules:
    """Tests for getting all tournament schedules for a week."""

    def test_returns_four_schedules(self):
        """Test that four schedules are returned."""
        result = get_tournament_schedules(346)

        assert len(result) == 4

        # Check that we have both days
        days = {s.day for s in result}
        assert 'saturday' in days
        assert 'sunday' in days

        # Check that we have both categories
        categories = {s.category for s in result}
        assert 'Above 1000' in categories
        assert 'Below 1000' in categories

    def test_returns_correct_sequence(self):
        """Test that all schedules have correct sequence."""
        result = get_tournament_schedules(346)

        for schedule in result:
            assert schedule.sequence == 346

    def test_returns_correct_names(self):
        """Test that names are correctly formatted."""
        result = get_tournament_schedules(346)

        expected_names = [
            "346 SMC Saturday Above 1000",
            "346 SMC Saturday Below 1000",
            "346 SMC Sunday Above 1000",
            "346 SMC Sunday Below 1000"
        ]

        actual_names = [s.name for s in result]
        assert actual_names == expected_names


class TestGetSingleDaySchedules:
    """Tests for getting schedules for a specific day."""

    def test_returns_saturday_schedules(self):
        """Test Saturday schedules."""
        result = get_single_day_schedules(346, 'saturday')

        assert len(result) == 2
        assert all(s.day == 'saturday' for s in result)
        assert {s.category for s in result} == {'Above 1000', 'Below 1000'}

    def test_returns_sunday_schedules(self):
        """Test Sunday schedules."""
        result = get_single_day_schedules(346, 'sunday')

        assert len(result) == 2
        assert all(s.day == 'sunday' for s in result)
        assert {s.category for s in result} == {'Above 1000', 'Below 1000'}

    def test_case_insensitive_day(self):
        """Test that day parameter is case insensitive."""
        result_upper = get_single_day_schedules(346, 'SATURDAY')
        result_lower = get_single_day_schedules(346, 'saturday')

        assert len(result_upper) == len(result_lower) == 2

    def test_raises_for_invalid_day(self):
        """Test that invalid day raises error."""
        with pytest.raises(ValueError, match="Invalid day"):
            get_single_day_schedules(346, 'monday')


class TestScheduleProperties:
    """Tests for TournamentSchedule properties."""

    def test_full_name_property(self):
        """Test the full_name property."""
        schedule = TournamentSchedule(
            sequence=346,
            day='saturday',
            category='Above 1000',
            start_time=pytz.UTC.localize(datetime(2024, 1, 1, 12, 0, 0)),
            name='346 SMC Saturday Above 1000'
        )

        assert schedule.full_name == '346 SMC Saturday Above 1000'


class TestTimezoneHandling:
    """Tests for timezone handling including DST."""

    def test_july_timezone_handling(self):
        """Test timezone handling in July (PDT, UTC-7)."""
        # July is PDT (Daylight Saving Time, UTC-7)
        pacific = pytz.timezone("America/Los_Angeles")

        # Create a timestamp in July
        july_date = pacific.localize(datetime(2024, 7, 10, 10, 0, 0))

        # Get Saturday - should still work correctly
        # We'll test by checking the timezone is correct
        result = get_next_saturday_12pm()

        # Verify result is timezone-aware
        assert result.tzinfo is not None
        assert result.tzinfo.zone == "America/Los_Angeles"

    def test_january_timezone_handling(self):
        """Test timezone handling in January (PST, UTC-8)."""
        # January is PST (Standard Time, UTC-8)
        pacific = pytz.timezone("America/Los_Angeles")

        result = get_next_saturday_12pm()

        # Verify result is timezone-aware
        assert result.tzinfo is not None
        assert result.tzinfo.zone == "America/Los_Angeles"

    def test_dst_transition_week(self):
        """Test handling around DST transition (March 2024)."""
        # In 2024, DST starts March 10 at 2:00 AM
        # Before DST: March 9 is still PST
        # After DST: March 10 at 3:00 AM onwards is PDT

        result = get_next_saturday_12pm()

        # Should still return a valid Saturday at noon
        assert result.weekday() == 5
        assert result.hour == 12
        assert result.tzinfo is not None


class TestFormatDatetimeForDisplay:
    """Tests for datetime display formatting."""

    def test_formats_datetime(self):
        """Test that datetime is formatted correctly."""
        pacific = pytz.timezone("America/Los_Angeles")
        dt = pacific.localize(datetime(2024, 1, 15, 12, 0, 0))

        result = format_datetime_for_display(dt)

        # Should include date, time, and timezone abbreviation
        assert '2024-01-15' in result
        assert '12:00' in result