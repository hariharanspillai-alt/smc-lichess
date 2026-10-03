"""Lichess API client for tournament management."""

import json
import time
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

import requests
import pytz
from dateutil import parser as date_parser


@dataclass
class SwissTournament:
    """Represents a Swiss tournament from Lichess API."""

    id: str
    name: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    status: Optional[str] = None
    nb_ongoing: int = 0
    nb_players: int = 0
    nb_rounds: int = 0
    round_num: int = 0
    rated: bool = False
    variant: str = "standard"
    starts_at: Optional[datetime] = None

    @classmethod
    def from_json(cls, data: dict) -> 'SwissTournament':
        """Create SwissTournament from API response JSON."""

        # Parse datetime fields
        created_at = None
        if data.get('createdAt'):
            created_at = date_parser.isoparse(data['createdAt'])

        starts_at = None
        if data.get('startsAt'):
            starts_at = date_parser.isoparse(data['startsAt'])

        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            created_by=data.get('createdBy'),
            created_at=created_at,
            status=data.get('status'),
            nb_ongoing=data.get('nbOngoing', 0),
            nb_players=data.get('nbPlayers', 0),
            nb_rounds=data.get('nbRounds', 0),
            round_num=data.get('round', 0),
            rated=data.get('rated', False),
            variant=data.get('variant', 'standard'),
            starts_at=starts_at,
        )


@dataclass
class TournamentCreateResult:
    """Result of creating a tournament."""

    success: bool
    tournament: Optional[SwissTournament] = None
    error_message: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None


class LichessAPI:
    """Client for Lichess API operations."""

    BASE_URL = "https://lichess.org/api"

    def __init__(self, api_token: str, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize Lichess API client.

        Args:
            api_token: Lichess personal access token
            max_retries: Maximum number of retries for failed requests
            base_delay: Base delay for exponential backoff (seconds)
        """
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
            "User-Agent": "SMC-Tournament-Creator/1.0"
        })
        self.max_retries = max_retries
        self.base_delay = base_delay

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an API request with retry logic and rate limit handling.

        Implements:
        - Retry with exponential backoff for 429, 500, 502, 503, 504
        - Proper error handling for 401, 403, 404, 409
        """
        headers = kwargs.pop('headers', {})
        headers.update(self.session.headers)
        kwargs['headers'] = headers

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = requests.request(method, url, **kwargs)

                # Handle specific status codes
                if response.status_code == 401:
                    raise AuthError("Authentication failed. Check LICHESS_API_TOKEN.")

                if response.status_code == 403:
                    # Check if it's a team permission issue
                    raise PermissionError("Authenticated Lichess account does not have permission for this action.")

                if response.status_code == 404:
                    raise NotFoundError("Resource not found.")

                if response.status_code == 409:
                    raise ConflictError("Conflict - resource already exists or request is invalid.")

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        wait_time = float(retry_after)
                    else:
                        wait_time = self.base_delay * (2 ** attempt)
                        # Cap at 60 seconds
                        wait_time = min(wait_time, 60)

                    time.sleep(wait_time)
                    continue

                if response.status_code >= 500:
                    # Server error - wait and retry
                    time.sleep(self.base_delay * (2 ** attempt))
                    last_exception = ServerError(f"Server error: {response.status_code}")
                    continue

                # Success or client error - return response as-is
                return response

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.base_delay * (2 ** attempt))
                    continue
                raise

        if last_exception:
            raise last_exception

        # Should not reach here, but just in case
        raise ServerError("Max retries exceeded")

    def test_token(self) -> bool:
        """
        Test if the API token is valid.

        Uses the /api/token/test endpoint.

        Returns:
            True if token is valid, False otherwise
        """
        try:
            response = self._make_request(
                "GET",
                f"{self.BASE_URL}/token/test"
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_token_info(self) -> dict:
        """
        Get information about the current token (scopes, expiration).

        Returns:
            Dict with userId, scopes, expires
        """
        response = self._make_request(
            "GET",
            f"{self.BASE_URL}/token/test"
        )
        return response.json() if response.status_code == 200 else {}

    def list_team_swiss_tournaments(self, team_id: str, max_results: int = 100,
                                    status: Optional[str] = None) -> List[SwissTournament]:
        """
        List Swiss tournaments for a team.

        Args:
            team_id: Team identifier
            max_results: Maximum number of tournaments to fetch
            status: Optional filter by status (created, started, finished)

        Returns:
            List of SwissTournament objects (newest first)
        """
        url = f"{self.BASE_URL}/team/{team_id}/swiss?max={max_results}"
        if status:
            url += f"&status={status}"

        response = self._make_request("GET", url)

        if response.status_code != 200:
            return []

        tournaments = []
        for line in response.text.strip().split('\n'):
            if line.strip():
                try:
                    data = json.loads(line)
                    tournaments.append(SwissTournament.from_json(data))
                except (json.JSONDecodeError, KeyError):
                    continue

        return tournaments

    def get_team_info(self, team_id: str) -> dict:
        """
        Get information about a team.

        Args:
            team_id: Team identifier

        Returns:
            Team information dict
        """
        response = self._make_request(
            "GET",
            f"{self.BASE_URL}/team/{team_id}"
        )

        if response.status_code == 200:
            return response.json()
        return {}

    def create_swiss_tournament(self, team_id: str, name: str,
                                start_time: datetime,
                                rounds: int = 5,
                                clock_limit: int = 900,  # 15 minutes in seconds
                                clock_increment: int = 30,
                                rated: bool = True,
                                variant: str = "standard",
                                description: Optional[str] = None,
                                min_rating: Optional[int] = None,
                                max_rating: Optional[int] = None) -> SwissTournament:
        """
        Create a new Swiss tournament for a team.

        Args:
            team_id: Team identifier
            name: Tournament name
            start_time: Start time (datetime object, will be converted to UTC milliseconds)
            rounds: Number of rounds (3-100, default 5)
            clock_limit: Initial clock time in seconds (default 900 = 15 minutes)
            clock_increment: Clock increment in seconds (default 30)
            rated: Whether games are rated (default True)
            variant: Chess variant (default 'standard')
            description: Optional description
            min_rating: Optional minimum rating (1000-2600)
            max_rating: Optional maximum rating (800-2200)

        Returns:
            Created SwissTournament object

        Raises:
            AuthError: If authentication fails
            PermissionError: If user lacks permission
            ConflictError: If tournament creation fails
        """
        # Convert start time to milliseconds since epoch (UTC)
        if start_time.tzinfo is None:
            # Assume UTC if no timezone
            start_time_utc = start_time
        else:
            start_time_utc = start_time.astimezone(pytz.UTC)

        starts_at_millis = int(start_time_utc.timestamp() * 1000)

        # Build form data
        data = {
            "name": name,
            "startsAt": str(starts_at_millis),
            "clock.limit": str(clock_limit),
            "clock.increment": str(clock_increment),
            "nbRounds": str(rounds),
            "rated": str(rated).lower(),
            "variant": variant,
        }

        # Add rating restrictions if provided
        if min_rating is not None:
            data["conditions.minRating.rating"] = str(min_rating)
        if max_rating is not None:
            data["conditions.maxRating.rating"] = str(max_rating)

        # Add description if provided
        if description:
            data["description"] = description

        url = f"{self.BASE_URL}/swiss/new/{team_id}"

        response = self._make_request(
            "POST",
            url,
            data=data
        )

        if response.status_code == 200:
            return SwissTournament.from_json(response.json())

        if response.status_code == 409:
            raise ConflictError("Tournament may already exist or request is invalid.")

        # Try to get error message from response
        try:
            error_data = response.json()
            error_msg = error_data.get('error', f"HTTP {response.status_code}")
        except:
            error_msg = f"HTTP {response.status_code}"

        raise TournamentCreationError(error_msg)

    def verify_team_permission(self, team_id: str) -> bool:
        """
        Verify that the authenticated user has permission to create Swiss tournaments for the team.

        Returns:
            True if user has permission, False otherwise
        """
        try:
            team_info = self.get_team_info(team_id)
            # If we can get team info and there's no permission error, assume OK
            return bool(team_info)
        except PermissionError:
            return False
        except Exception:
            return False


# Custom exceptions
class LichessAPIError(Exception):
    """Base exception for Lichess API errors."""
    pass


class AuthError(LichessAPIError):
    """Authentication failed."""
    pass


class NotFoundError(LichessAPIError):
    """Resource not found."""
    pass


class ConflictError(LichessAPIError):
    """Resource already exists or request is invalid."""
    pass


class ServerError(LichessAPIError):
    """Server-side error."""
    pass


class TournamentCreationError(LichessAPIError):
    """Failed to create tournament."""
    pass