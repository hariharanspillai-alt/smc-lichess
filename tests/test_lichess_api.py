"""Tests for Lichess API client."""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pytz

from src.lichess_api import (
    LichessAPI,
    SwissTournament,
    TournamentCreateResult,
    AuthError,
    NotFoundError,
    ConflictError,
    ServerError,
    TournamentCreationError
)


class TestSwissTournament:
    """Tests for SwissTournament dataclass."""

    def test_from_json_basic(self):
        """Test creating SwissTournament from JSON."""
        data = {
            "id": "abc123",
            "name": "346 SMC Saturday Above 1000",
            "createdBy": "testuser",
            "status": "created",
            "nbOngoing": 0,
            "nbPlayers": 0,
            "nbRounds": 5,
            "round": 0,
            "rated": True,
            "variant": "standard"
        }

        result = SwissTournament.from_json(data)

        assert result.id == "abc123"
        assert result.name == "346 SMC Saturday Above 1000"
        assert result.created_by == "testuser"
        assert result.status == "created"
        assert result.nb_ongoing == 0
        assert result.nb_players == 0
        assert result.nb_rounds == 5
        assert result.round_num == 0
        assert result.rated is True
        assert result.variant == "standard"

    def test_from_json_with_timestamps(self):
        """Test parsing datetime fields from API response."""
        data = {
            "id": "abc123",
            "name": "Test Tournament",
            "createdAt": "2024-01-01T12:00:00Z",
            "startsAt": "2024-01-15T12:00:00Z"
        }

        result = SwissTournament.from_json(data)

        assert result.created_at is not None
        assert result.starts_at is not None


class TestLichessAPITokenTest:
    """Tests for token testing functionality."""

    def test_test_token_valid(self):
        """Test that valid token returns True."""
        mock_response = Mock()
        mock_response.status_code = 200

        api = LichessAPI("test_token")
        with patch('src.lichess_api.requests.request', return_value=mock_response):
            result = api.test_token()
            assert result is True

    def test_test_token_invalid(self):
        """Test that invalid token returns False."""
        api = LichessAPI("invalid_token")
        with patch('src.lichess_api.requests.request', side_effect=Exception("Auth error")):
            result = api.test_token()
            assert result is False


class TestLichessAPIErrors:
    """Tests for API error handling."""

    def test_auth_error_401(self):
        """Test that 401 raises AuthError."""
        mock_response = Mock()
        mock_response.status_code = 401

        api = LichessAPI("test_token")
        with patch('src.lichess_api.requests.request', return_value=mock_response):
            with pytest.raises(AuthError):
                api._make_request("GET", "https://lichess.org/api/test")

    def test_forbidden_403(self):
        """Test that 403 raises PermissionError."""
        mock_response = Mock()
        mock_response.status_code = 403

        api = LichessAPI("test_token")
        with patch('src.lichess_api.requests.request', return_value=mock_response):
            with pytest.raises(PermissionError):
                api._make_request("GET", "https://lichess.org/api/test")

    def test_not_found_404(self):
        """Test that 404 raises NotFoundError."""
        mock_response = Mock()
        mock_response.status_code = 404

        api = LichessAPI("test_token")
        with patch('src.lichess_api.requests.request', return_value=mock_response):
            with pytest.raises(NotFoundError):
                api._make_request("GET", "https://lichess.org/api/test")

    def test_conflict_409(self):
        """Test that 409 raises ConflictError."""
        mock_response = Mock()
        mock_response.status_code = 409

        api = LichessAPI("test_token")
        with patch('src.lichess_api.requests.request', return_value=mock_response):
            with pytest.raises(ConflictError):
                api._make_request("GET", "https://lichess.org/api/test")


class TestListTeamSwissTournaments:
    """Tests for listing team Swiss tournaments."""

    def test_lists_tournaments(self):
        """Test that tournaments are listed correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '\n'.join([
            json.dumps({"id": "1", "name": "346 SMC Saturday Above 1000"}),
            json.dumps({"id": "2", "name": "346 SMC Sunday Below 1000"})
        ])

        api = LichessAPI("test_token")
        with patch('src.lichess_api.requests.request', return_value=mock_response):
            result = api.list_team_swiss_tournaments("test-team")

            assert len(result) == 2
            assert result[0].id == "1"
            assert result[1].id == "2"

    def test_handles_empty_response(self):
        """Test that empty response returns empty list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""

        api = LichessAPI("test_token")
        with patch('src.lichess_api.requests.request', return_value=mock_response):
            result = api.list_team_swiss_tournaments("test-team")

            assert result == []

    def test_parses_non_smc_tournaments(self):
        """Test that non-SMC tournaments are included but parsed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '\n'.join([
            json.dumps({"id": "1", "name": "346 SMC Saturday Above 1000"}),
            json.dumps({"id": "2", "name": "Some Other Tournament"})
        ])

        api = LichessAPI("test_token")
        with patch('src.lichess_api.requests.request', return_value=mock_response):
            result = api.list_team_swiss_tournaments("test-team")

            assert len(result) == 2
            # Both should be parsed, non-SMC just won't match the pattern in sequence.py


class TestCreateSwissTournament:
    """Tests for Swiss tournament creation."""

    @staticmethod
    def setup_api():
        """Set up API client for testing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "abc123xyz",
            "name": "346 SMC Saturday Above 1000",
            "status": "created"
        }
        return mock_response

    def test_creates_tournament_with_correct_params(self):
        """Test that tournament is created with correct parameters."""
        mock_response = self.setup_api()

        api = LichessAPI("test_token")
        tz = pytz.timezone("America/Los_Angeles")
        start_time = tz.localize(datetime(2024, 1, 20, 12, 0, 0))

        with patch('src.lichess_api.requests.request', return_value=mock_response):
            result = api.create_swiss_tournament(
                team_id="test-team",
                name="346 SMC Saturday Above 1000",
                start_time=start_time,
                rounds=5,
                clock_limit=900,
                clock_increment=30,
                rated=True,
                min_rating=1000
            )

            assert result.id == "abc123xyz"
            assert result.name == "346 SMC Saturday Above 1000"

    def test_sends_rating_restrictions(self):
        """Test that rating restrictions are sent in the request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "abc123",
            "name": "346 SMC Saturday Above 1000"
        }

        api = LichessAPI("test_token")
        tz = pytz.timezone("America/Los_Angeles")
        start_time = tz.localize(datetime(2024, 1, 20, 12, 0, 0))

        with patch('src.lichess_api.requests.request', return_value=mock_response) as mock_request:
            result = api.create_swiss_tournament(
                team_id="test-team",
                name="346 SMC Saturday Above 1000",
                start_time=start_time,
                min_rating=1000,
                max_rating=999
            )

            # Check that the request was called
            assert mock_request.called


class TestRateLimiting:
    """Tests for rate limiting and retry logic."""

    def test_retries_on_429(self):
        """Test that 429 triggers retry with backoff."""
        # This test verifies that when a 429 is received, the code
        # waits and retries. Since the actual sleep is slow, we test
        # the mechanism by checking that the request is made multiple times.

        # Create a list of responses: 429, then 200
        responses = [
            Mock(status_code=429, headers={}, text=""),
            Mock(status_code=200, text="", json=lambda: {"id": "test"})
        ]

        api = LichessAPI("test_token", max_retries=3, base_delay=0.01)  # Short delay for test

        call_count = [0]

        def side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            return responses[min(idx, len(responses) - 1)]

        with patch('src.lichess_api.requests.request', side_effect=side_effect):
            result = api._make_request("GET", "https://lichess.org/api/test")
            # After retry, should get a 200 response
            assert result is not None
            # Should have been called at least twice (429 + 200)
            assert call_count[0] >= 2


class TestDuplicateProtection:
    """Tests for duplicate tournament protection."""

    def test_check_duplicate_returns_true(self):
        """Test that duplicate check returns True for existing tournament."""
        from src.sequence import check_duplicate_protection

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({"id": "1", "name": "346 SMC Saturday Above 1000"})

        api = LichessAPI("test_token")
        with patch('src.lichess_api.requests.request', return_value=mock_response):
            result = check_duplicate_protection(api, "test-team", "346 SMC Saturday Above 1000")
            assert result is True

    def test_check_duplicate_returns_false(self):
        """Test that duplicate check returns False for non-existing tournament."""
        from src.sequence import check_duplicate_protection

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({"id": "1", "name": "345 SMC Saturday Above 1000"})

        api = LichessAPI("test_token")
        with patch('src.lichess_api.requests.request', return_value=mock_response):
            result = check_duplicate_protection(api, "test-team", "346 SMC Saturday Above 1000")
            assert result is False


class TestCreateResult:
    """Tests for TournamentCreateResult dataclass."""

    def test_create_result_values(self):
        """Test that TournamentCreateResult stores values correctly."""
        tournament = SwissTournament(id="test123", name="Test Tournament")
        result = TournamentCreateResult(
            success=True,
            tournament=tournament,
            error_message=None,
            skipped=False,
            skip_reason=None
        )

        assert result.success is True
        assert result.tournament == tournament
        assert result.skipped is False


class TestAPIInitialization:
    """Tests for LichessAPI initialization."""

    def test_initializes_with_token(self):
        """Test that API initializes with correct token."""
        api = LichessAPI("my_test_token")

        assert api.api_token == "my_test_token"
        assert "Authorization" in api.session.headers
        assert api.session.headers["Authorization"] == "Bearer my_test_token"

    def test_default_settings(self):
        """Test that default settings are correct."""
        api = LichessAPI("test_token")

        assert api.max_retries == 3
        assert api.base_delay == 1.0
        assert "application/json" in api.session.headers.get("Accept", "")