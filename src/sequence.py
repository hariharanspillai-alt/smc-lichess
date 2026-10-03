"""Tournament sequence number management."""

import re
from dataclasses import dataclass
from typing import Optional, List, Dict

from .lichess_api import LichessAPI, SwissTournament


# Regex pattern to match tournament names and extract sequence
# Matches: "346 SMC Saturday Above 1000" or "346 SMC Sunday Below 1000"
TOURNAMENT_NAME_PATTERN = re.compile(
    r'^(\d+)\s+SMC\s+(Saturday|Sunday)\s+(Above 1000|Below 1000)$'
)


@dataclass
class TournamentInfo:
    """Information about a tournament."""
    sequence: int
    day: str  # 'Saturday' or 'Sunday'
    category: str  # 'Above 1000' or 'Below 1000'
    name: str  # Full tournament name


@dataclass
class SequenceState:
    """Tracks which tournament sequences exist."""
    next_sequence: int
    saturday_exists: set  # Set of categories that exist for Saturday
    sunday_exists: set    # Set of categories that exist for Sunday

    def get_expected_categories(self, sequence: int) -> set:
        """Get the expected categories for a given sequence."""
        # All four categories should exist for a complete week
        return {'Above 1000', 'Below 1000'}


def parse_tournament_name(name: str) -> Optional[TournamentInfo]:
    """
    Parse a tournament name to extract sequence, day, and category.

    Returns TournamentInfo if name matches expected pattern, None otherwise.
    """
    match = TOURNAMENT_NAME_PATTERN.match(name)
    if not match:
        return None

    sequence = int(match.group(1))
    day = match.group(2)
    category = match.group(3)

    return TournamentInfo(
        sequence=sequence,
        day=day,
        category=category,
        name=name
    )


def get_next_sequence(api: LichessAPI, team_id: str) -> int:
    """
    Determine the next sequence number for SMC tournaments.

    Strategy:
    1. Fetch all Swiss tournaments for the team
    2. Parse tournament names to extract sequence numbers
    3. Find the highest sequence number
    4. Return highest + 1

    This ensures we don't skip sequence numbers or create duplicates.
    """
    tournaments = api.list_team_swiss_tournaments(team_id, max_results=100)

    sequences = set()

    for t in tournaments:
        info = parse_tournament_name(t.name)
        if info:
            sequences.add(info.sequence)

    if not sequences:
        return 345  # Starting sequence as specified in requirements

    return max(sequences) + 1


def get_existing_tournaments(api: LichessAPI, team_id: str, sequence: int) -> List[TournamentInfo]:
    """
    Get all existing tournaments for a given sequence.

    Returns list of TournamentInfo objects for tournaments that already exist.
    """
    all_tournaments = api.list_team_swiss_tournaments(team_id, max_results=100)

    existing = []
    for t in all_tournaments:
        info = parse_tournament_name(t.name)
        if info and info.sequence == sequence:
            existing.append(info)

    return existing


def check_duplicate_protection(api: LichessAPI, team_id: str, name: str) -> bool:
    """
    Check if a tournament with the given name already exists.

    Returns True if tournament exists (should skip creation), False otherwise.
    """
    tournaments = api.list_team_swiss_tournaments(team_id, max_results=100)

    for t in tournaments:
        if t.name == name:
            return True

    return False


def group_existing_by_sequence(api: LichessAPI, team_id: str) -> Dict[int, List[TournamentInfo]]:
    """
    Group existing SMC tournaments by their sequence number.

    Returns dict mapping sequence -> list of TournamentInfo for that sequence.
    This helps understand the state of existing tournaments.
    """
    tournaments = api.list_team_swiss_tournaments(team_id, max_results=100)

    by_sequence = {}
    for t in tournaments:
        info = parse_tournament_name(t.name)
        if info:
            if info.sequence not in by_sequence:
                by_sequence[info.sequence] = []
            by_sequence[info.sequence].append(info)

    return by_sequence