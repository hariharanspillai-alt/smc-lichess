"""Tests for tournament validation."""

import pytest
from datetime import datetime
from unittest.mock import patch

import pytz

from src.validation import (
    TournamentConfig,
    validate_tournament_config,
    validate_config,
    ValidationResult
)
from src.config import Config


class TestValidateTournamentConfig:
    """Tests for tournament configuration validation."""

    @staticmethod
    def valid_config(**overrides) -> TournamentConfig:
        """Get a valid tournament config with overrides."""
        tz = pytz.timezone("America/Los_Angeles")
        defaults = {
            "sequence": 346,
            "day": "saturday",
            "category": "Above 1000",
            "start_time": tz.localize(datetime(2030, 1, 20, 12, 0, 0)),  # Far future
            "name": "346 SMC Saturday Above 1000",
            "team_id": "test-team",
            "rounds": 5,
            "clock_limit": 900,
            "clock_increment": 30,
            "rated": True,
            "variant": "standard",
            "min_rating": None,
            "max_rating": None
        }
        defaults.update(overrides)
        return TournamentConfig(**defaults)

    def test_valid_config_passes(self):
        """Test that valid configuration passes validation."""
        config = self.valid_config()

        result = validate_tournament_config(config)

        assert result.valid is True

    def test_invalid_name_empty(self):
        """Test that empty name fails."""
        config = self.valid_config(name="")

        result = validate_tournament_config(config)

        assert result.valid is False

    def test_valid_name_at_min_length(self):
        """Test that name at minimum valid length passes."""
        config = self.valid_config(name="AB")  # 2 characters - minimum

        result = validate_tournament_config(config)

        assert result.valid is True

    def test_valid_name_at_max_length(self):
        """Test that name at maximum length passes."""
        config = self.valid_config(name="A" * 30)  # 30 characters - maximum

        result = validate_tournament_config(config)

        assert result.valid is True

    def test_invalid_name_too_long(self):
        """Test that name too long fails."""
        config = self.valid_config(name="X" * 31)  # 31 characters, exceeds max of 30

        result = validate_tournament_config(config)

        assert result.valid is False

    def test_invalid_day_fails(self):
        """Test that invalid day fails."""
        config = self.valid_config(day="monday")

        result = validate_tournament_config(config)

        assert result.valid is False
        assert any("day" in e.lower() for e in result.errors)

    def test_invalid_category_fails(self):
        """Test that invalid category fails."""
        config = self.valid_config(category="Mid 1000")

        result = validate_tournament_config(config)

        assert result.valid is False
        assert any("category" in e.lower() or "invalid" in e.lower() for e in result.errors)

    def test_invalid_rounds_too_few(self):
        """Test that rounds < 3 fails."""
        config = self.valid_config(rounds=2)

        result = validate_tournament_config(config)

        assert result.valid is False
        assert any("round" in e.lower() for e in result.errors)

    def test_invalid_rounds_too_many(self):
        """Test that rounds > 100 fails."""
        config = self.valid_config(rounds=101)

        result = validate_tournament_config(config)

        assert result.valid is False
        assert any("round" in e.lower() for e in result.errors)

    def test_negative_clock_limit_fails(self):
        """Test that negative clock limit fails."""
        config = self.valid_config(clock_limit=-1)

        result = validate_tournament_config(config)

        assert result.valid is False
        assert any("clock" in e.lower() for e in result.errors)

    def test_invalid_clock_increment_fails(self):
        """Test that clock increment > 120 fails."""
        config = self.valid_config(clock_increment=121)

        result = validate_tournament_config(config)

        assert result.valid is False
        assert any("clock" in e.lower() for e in result.errors)

    def test_valid_clock_increment_max(self):
        """Test that clock increment at max passes."""
        config = self.valid_config(clock_increment=120)

        result = validate_tournament_config(config)

        assert result.valid is True

    def test_invalid_min_rating_too_low(self):
        """Test that min rating < 1000 fails."""
        config = self.valid_config(min_rating=999)

        result = validate_tournament_config(config)

        assert result.valid is False
        assert any("min" in e.lower() and "rating" in e.lower() for e in result.errors)

    def test_invalid_min_rating_too_high(self):
        """Test that min rating > 2600 fails."""
        config = self.valid_config(min_rating=2601)

        result = validate_tournament_config(config)

        assert result.valid is False

    def test_valid_min_rating(self):
        """Test that valid min rating passes."""
        config = self.valid_config(min_rating=1000)

        result = validate_tournament_config(config)

        assert result.valid is True

    def test_invalid_max_rating_too_low(self):
        """Test that max rating < 800 fails."""
        config = self.valid_config(
            name="346 SMC Saturday Below 1000",
            max_rating=799,
            min_rating=None
        )

        result = validate_tournament_config(config)

        assert result.valid is False

    def test_valid_max_rating_below_1000(self):
        """Test that max rating 900 (below 1000) is valid."""
        # Lichess API requires specific values; 900 is the highest "below 1000"
        config = self.valid_config(
            name="346 SMC Saturday Below 1000",
            max_rating=900,
            min_rating=None
        )

        result = validate_tournament_config(config)

        assert result.valid is True

    def test_valid_max_rating_1000(self):
        """Test that max rating 1000 is valid."""
        config = self.valid_config(
            name="346 SMC Saturday Above 1000",
            max_rating=1000,
            min_rating=None
        )

        result = validate_tournament_config(config)

        assert result.valid is True


class TestValidateConfig:
    """Tests for main configuration validation."""

    def test_valid_config_passes(self):
        """Test that valid config passes."""
        config = Config(api_token="test_token", team_id="test-team")

        result = validate_config(config)

        assert result.valid is True

    def test_missing_token_fails(self):
        """Test that missing token fails."""
        config = Config(api_token="", team_id="test-team")

        result = validate_config(config)

        assert result.valid is False
        assert any("token" in e.lower() for e in result.errors)

    def test_missing_team_id_fails(self):
        """Test that missing team ID fails."""
        config = Config(api_token="test_token", team_id="")

        result = validate_config(config)

        assert result.valid is False
        assert any("team" in e.lower() and "id" in e.lower() for e in result.errors)


class TestValidationResult:
    """Tests for ValidationResult helper methods."""

    def test_success_creates_valid_result(self):
        """Test that success() creates a valid result."""
        result = ValidationResult.success()

        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_failure_creates_invalid_result(self):
        """Test that failure() creates an invalid result."""
        result = ValidationResult.failure(["Error 1", "Error 2"], ["Warning 1"])

        assert result.valid is False
        assert result.errors == ["Error 1", "Error 2"]
        assert result.warnings == ["Warning 1"]


class TestRatingRestrictions:
    """Tests for rating restriction validation."""

    @staticmethod
    def base_config(**overrides) -> dict:
        """Get base configuration."""
        tz = pytz.timezone("America/Los_Angeles")
        defaults = {
            "sequence": 346,
            "day": "saturday",
            "category": "Above 1000",
            "start_time": tz.localize(datetime(2030, 1, 20, 12, 0, 0)),
            "team_id": "test-team",
            "name": "346 SMC Saturday Above 1000",
        }
        defaults.update(overrides)
        return defaults

    def test_above_1000_category_uses_min_rating(self):
        """Test that Above 1000 category uses min_rating."""
        config = TournamentConfig(**self.base_config(min_rating=1000, max_rating=None))

        result = validate_tournament_config(config)

        assert result.valid is True

    def test_below_1000_category_uses_max_rating(self):
        """Test that Below 1000 category uses max_rating."""
        # Lichess API requires specific values; 900 is the highest "below 1000"
        config = TournamentConfig(
            **self.base_config(
                name="346 SMC Saturday Below 1000",
                category="Below 1000",
                max_rating=900,
                min_rating=None
            )
        )

        result = validate_tournament_config(config)

        assert result.valid is True

    def test_both_ratings_valid(self):
        """Test that both min and max rating can be set."""
        config = TournamentConfig(**self.base_config(min_rating=1000, max_rating=1500))

        result = validate_tournament_config(config)

        assert result.valid is True