"""Main logic for creating Swiss tournaments."""

from typing import Optional, Dict, Any, Tuple

from .config import Config
from .lichess_api import LichessAPI, TournamentCreateResult, SwissTournament
from .schedule import TournamentSchedule, get_tournament_schedules, get_single_day_schedules
from .sequence import (
    get_next_sequence,
    get_existing_tournaments,
    check_duplicate_protection,
    TournamentInfo
)
from .validation import (
    TournamentConfig,
    validate_tournament_config,
    print_tournament_preview
)


class SwissTournamentCreator:
    """Creates SMC Swiss tournaments on Lichess."""

    # Tournament configuration constants
    ROUNDS = 5
    CLOCK_LIMIT = 900  # 15 minutes in seconds
    CLOCK_INCREMENT = 0  # No increment (15+0)
    RATED = True
    VARIANT = "standard"

    def __init__(self, config: Config):
        """
        Initialize the tournament creator.

        Args:
            config: Lichess API configuration
        """
        self.config = config
        self.api = LichessAPI(config.api_token)

    def create_tournament(self, schedule: TournamentSchedule,
                          dry_run: bool = False) -> TournamentCreateResult:
        """
        Create a single tournament.

        Args:
            schedule: Tournament schedule
            dry_run: If True, don't actually create

        Returns:
            TournamentCreateResult with outcome
        """
        # Check for duplicate first
        if check_duplicate_protection(self.api, self.config.team_id, schedule.name):
            return TournamentCreateResult(
                success=True,
                skipped=True,
                skip_reason=f"Tournament already exists: {schedule.name}"
            )

        # Create tournament config with rating restrictions
        # Lichess API requires specific maxRating values from predefined list
        min_rating = 1000 if schedule.category == 'Above 1000' else None
        max_rating = 1100 if schedule.category == 'Below 1000' else None  # As requested by user

        tournament_config = TournamentConfig(
            sequence=schedule.sequence,
            day=schedule.day,
            category=schedule.category,
            start_time=schedule.start_time,
            name=schedule.name,
            team_id=self.config.team_id,
            rounds=self.ROUNDS,
            clock_limit=self.CLOCK_LIMIT,
            clock_increment=self.CLOCK_INCREMENT,
            rated=self.RATED,
            variant=self.VARIANT,
            min_rating=min_rating,
            max_rating=max_rating
        )

        # Validate before creation
        validation = validate_tournament_config(tournament_config)
        if not validation.valid:
            return TournamentCreateResult(
                success=False,
                error_message="; ".join(validation.errors)
            )

        if dry_run:
            return TournamentCreateResult(
                success=True,
                skipped=False,
                # For dry run, we still return a "fake" tournament for display
                tournament=SwissTournament(
                    id="DRY_RUN_" + schedule.name,
                    name=schedule.name
                )
            )

        try:
            tournament = self.api.create_swiss_tournament(
                team_id=self.config.team_id,
                name=schedule.name,
                start_time=schedule.start_time,
                rounds=self.ROUNDS,
                clock_limit=self.CLOCK_LIMIT,
                clock_increment=self.CLOCK_INCREMENT,
                rated=self.RATED,
                variant=self.VARIANT,
                min_rating=min_rating,
                max_rating=max_rating
            )
            return TournamentCreateResult(
                success=True,
                tournament=tournament
            )
        except Exception as e:
            return TournamentCreateResult(
                success=False,
                error_message=str(e)
            )

    def create_for_day(self, day: str, sequence: int, dry_run: bool = False) -> dict:
        """
        Create tournaments for a specific day.

        Args:
            day: 'saturday' or 'sunday'
            sequence: Tournament sequence number
            dry_run: If True, don't create

        Returns:
            Dict with 'created', 'skipped', 'failed' lists and counts
        """
        schedules = get_single_day_schedules(sequence, day, self.config.timezone)

        results = {
            'created': [],
            'skipped': [],
            'failed': [],
            'counts': {'created': 0, 'skipped': 0, 'failed': 0}
        }

        for schedule in schedules:
            result = self.create_tournament(schedule, dry_run)

            if result.success:
                if result.skipped:
                    results['skipped'].append(result.skip_reason)
                    results['counts']['skipped'] += 1
                else:
                    results['created'].append(result.tournament)
                    results['counts']['created'] += 1
            else:
                results['failed'].append(f"{schedule.name}: {result.error_message}")
                results['counts']['failed'] += 1

        return results

    def create_for_week(self, sequence: Optional[int] = None, dry_run: bool = False) -> dict:
        """
        Create all four tournaments for the upcoming Saturday and Sunday.

        Args:
            sequence: Optional specific sequence number. If None, auto-determine.
            dry_run: If True, don't create

        Returns:
            Dict with results summary
        """
        # Get next sequence if not provided
        if sequence is None:
            sequence = get_next_sequence(self.api, self.config.team_id)

        # Get existing tournaments for this sequence
        existing = get_existing_tournaments(self.api, self.config.team_id, sequence)
        existing_names = {t.name for t in existing}

        results = {
            'sequence': sequence,
            'created': [],
            'skipped': [],
            'failed': [],
            'counts': {'created': 0, 'skipped': 0, 'failed': 0}
        }

        # Get all schedules
        schedules = get_tournament_schedules(sequence, self.config.timezone)

        for schedule in schedules:
            if schedule.name in existing_names:
                results['skipped'].append(f"Already exists — {schedule.name}")
                results['counts']['skipped'] += 1
                continue

            result = self.create_tournament(schedule, dry_run)

            if result.success:
                if result.skipped:
                    results['skipped'].append(f"Already exists — {schedule.name}")
                    results['counts']['skipped'] += 1
                else:
                    results['created'].append(result.tournament)
                    results['counts']['created'] += 1
            else:
                results['failed'].append(f"{schedule.name}: {result.error_message}")
                results['counts']['failed'] += 1

        results['schedules'] = schedules
        return results

    def get_next_sequence_number(self) -> int:
        """Get the next sequence number for SMC tournaments."""
        return get_next_sequence(self.api, self.config.team_id)

    def verify_team_access(self) -> Tuple[bool, str]:
        """
        Verify that the authenticated user can create tournaments for the team.

        Returns:
            Tuple of (success, message)
        """
        # Try to verify team access - test by listing team info
        try:
            team_info = self.api.get_team_info(self.config.team_id)
            if team_info:
                return True, f"Team '{team_info.get('name', 'verified')}' access confirmed"
            else:
                return False, "Could not verify team access"
        except Exception as e:
            return False, f"Authentication check failed: {e}"