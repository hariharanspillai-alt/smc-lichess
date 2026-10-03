#!/usr/bin/env python3
"""CLI for SMC Lichess tournament creator."""

import sys
from typing import Optional, List

import click

from .config import Config, get_config
from .lichess_api import LichessAPI
from .schedule import TournamentSchedule, get_tournament_schedules, get_single_day_schedules
from .swiss_creator import SwissTournamentCreator
from .validation import TournamentConfig
from . import __version__


def print_header():
    """Print the application header."""
    print("=" * 60)
    print("SMC Lichess Tournament Creator")
    print(f"Version: {__version__}")
    print("=" * 60)
    print()


def print_dry_run(sequence: int, schedules: List['TournamentSchedule'], team_id: str):
    """Print a dry run preview of tournaments that would be created."""
    print("DRY RUN - No tournaments will be created")
    print()
    print(f"Sequence: {sequence}")
    print()

    # Group by day
    saturday = [s for s in schedules if s.day == 'saturday']
    sunday = [s for s in schedules if s.day == 'sunday']

    print("Saturday:")
    for s in saturday:
        min_rating = 1000 if s.category == 'Above 1000' else None
        max_rating = 999 if s.category == 'Below 1000' else None

        tournament_config = TournamentConfig(
            sequence=s.sequence,
            day=s.day,
            category=s.category,
            start_time=s.start_time,
            name=s.name,
            team_id=team_id,
            rounds=5,
            clock_limit=900,
            clock_increment=30,
            rated=True,
            variant="standard",
            min_rating=min_rating,
            max_rating=max_rating
        )

        print(f"  {s.name}")
        print(f"    Start: {s.start_time.strftime('%Y-%m-%d %H:%M %Z')}")
        print(f"    Timezone: Pacific Time (America/Los_Angeles)")
        print(f"    Rounds: 5")
        print(f"    Clock: 15+30")
        print(f"    Rated: yes")
        print(f"    Variant: standard")
        print(f"    Team: {team_id}")
        print()

    print("Sunday:")
    for s in sunday:
        min_rating = 1000 if s.category == 'Above 1000' else None
        max_rating = 999 if s.category == 'Below 1000' else None

        tournament_config = TournamentConfig(
            sequence=s.sequence,
            day=s.day,
            category=s.category,
            start_time=s.start_time,
            name=s.name,
            team_id=team_id,
            rounds=5,
            clock_limit=900,
            clock_increment=30,
            rated=True,
            variant="standard",
            min_rating=min_rating,
            max_rating=max_rating
        )

        print(f"  {s.name}")
        print(f"    Start: {s.start_time.strftime('%Y-%m-%d %H:%M %Z')}")
        print(f"    Timezone: Pacific Time (America/Los_Angeles)")
        print(f"    Rounds: 5")
        print(f"    Clock: 15+30")
        print(f"    Rated: yes")
        print(f"    Variant: standard")
        print(f"    Team: {team_id}")
        print()


def print_results(results: dict):
    """Print the results of tournament creation."""
    print()
    print("SUCCESS" if results['counts']['failed'] == 0 else "PARTIAL SUCCESS")

    for t in results['created']:
        url = f"https://lichess.org/swiss/{t.id}"
        print(f"\n{t.name}")
        print(url)

    for skip in results['skipped']:
        print(skip)

    for fail in results['failed']:
        print(f"FAILED: {fail}")

    print()
    print(f"Created: {results['counts']['created']}")
    print(f"Skipped: {results['counts']['skipped']}")
    print(f"Failed: {results['counts']['failed']}")


@click.group()
@click.version_option(version=__version__, prog_name='smc-tournaments')
def cli():
    """SMC Lichess Tournament Creator CLI.

    Create and manage SMC Academy Swiss tournaments on Lichess.
    """
    pass


@cli.command()
@click.option('--day', type=click.Choice(['saturday', 'sunday']), required=True,
              help='Day to create tournaments for')
@click.option('--sequence', type=int, default=None, help='Sequence number (auto-detected if not provided)')
@click.option('--dry-run', is_flag=True, default=False, help='Show what would be created without creating')
def create(day: str, sequence: Optional[int], dry_run: bool):
    """Create tournaments for a specific day.

    Creates two tournaments (Above 1000 and Below 1000) for the specified day.
    """
    print_header()

    try:
        config = get_config()
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # Verify team access
    creator = SwissTournamentCreator(config)
    success, message = creator.verify_team_access()
    if not success:
        print(f"ERROR: {message}", file=sys.stderr)
        sys.exit(1)

    # Get next sequence if not provided
    if sequence is None:
        sequence = creator.get_next_sequence_number()

    if dry_run:
        schedules = get_single_day_schedules(sequence, day, config.timezone)
        print_dry_run(sequence, schedules, config.team_id)
        return

    print(f"Creating tournaments for {day.capitalize()}...")
    results = creator.create_for_day(day, sequence, dry_run=False)

    print_results(results)

    if results['counts']['failed'] > 0:
        sys.exit(1)


@cli.command()
@click.option('--sequence', type=int, default=None, help='Sequence number (auto-detected if not provided)')
@click.option('--dry-run', is_flag=True, default=False, help='Show what would be created without creating')
def week(sequence: Optional[int], dry_run: bool):
    """Create all four tournaments for the upcoming Saturday and Sunday.

    Creates:
    - <N> SMC Saturday Above 1000
    - <N> SMC Saturday Below 1000
    - <N> SMC Sunday Above 1000
    - <N> SMC Sunday Below 1000
    """
    print_header()

    try:
        config = get_config()
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # Verify team access
    creator = SwissTournamentCreator(config)
    success, message = creator.verify_team_access()
    if not success:
        print(f"ERROR: {message}", file=sys.stderr)
        sys.exit(1)

    if dry_run:
        if sequence is None:
            sequence = creator.get_next_sequence_number()

        schedules = get_tournament_schedules(sequence, config.timezone)
        print_dry_run(sequence, schedules, config.team_id)
        return

    # Auto-determine sequence if not provided
    results = creator.create_for_week(sequence, dry_run=False)

    print(f"\nSequence: {results['sequence']}")
    print()

    # Print Saturday tournaments
    saturday_schedules = [s for s in results['schedules'] if s.day == 'saturday']
    sunday_schedules = [s for s in results['schedules'] if s.day == 'sunday']

    print("Saturday:")
    for t in results['created']:
        if t.name in [s.name for s in saturday_schedules]:
            url = f"https://lichess.org/swiss/{t.id}"
            print(f"  Created: {t.name}")
            print(f"    {url}")

    for skip in results['skipped']:
        if 'Saturday' in skip or 'Above 1000' in skip or 'Below 1000' in skip:
            print(f"  {skip}")

    print()
    print("Sunday:")
    for t in results['created']:
        if t.name in [s.name for s in sunday_schedules]:
            url = f"https://lichess.org/swiss/{t.id}"
            print(f"  Created: {t.name}")
            print(f"    {url}")

    for skip in results['skipped']:
        if 'Sunday' in skip:
            print(f"  {skip}")

    print()
    print(f"Created: {results['counts']['created']}")
    print(f"Skipped: {results['counts']['skipped']}")
    print(f"Failed: {results['counts']['failed']}")

    if results['counts']['failed'] > 0:
        sys.exit(1)


@cli.command()
def sequence():
    """Display the next sequence number that would be used."""
    print_header()

    try:
        config = get_config()
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    creator = SwissTournamentCreator(config)
    next_seq = creator.get_next_sequence_number()

    print(f"Next sequence number: {next_seq}")

    # Show existing tournaments if any
    from .sequence import group_existing_by_sequence
    existing = group_existing_by_sequence(creator.api, config.team_id)

    if existing:
        print()
        print("Existing sequences:")
        for seq in sorted(existing.keys(), reverse=True)[:5]:
            tournaments = existing[seq]
            print(f"  {seq}:")
            for t in tournaments:
                print(f"    - {t.name}")


@cli.command()
def status():
    """Check authentication and configuration status."""
    print_header()

    try:
        config = get_config()
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    print(f"Team ID: {config.team_id}")

    # Test authentication
    try:
        api = LichessAPI(config.api_token)
        token_info = api.get_token_info()

        print(f"Token valid: yes")
        print(f"Scopes: {', '.join(token_info.get('scopes', []))}")

        # Verify team access
        creator = SwissTournamentCreator(config)
        success, message = creator.verify_team_access()
        print(f"Team access: {message}")

    except Exception as e:
        print(f"Authentication check failed: {e}", file=sys.stderr)
        sys.exit(1)


@cli.command()
@click.argument('day', type=click.Choice(['saturday', 'sunday']))
@click.argument('sequence', type=int)
@click.option('--dry-run', is_flag=True, default=True, help='Show what would be created')
def show(day: str, sequence: int, dry_run: bool):
    """Show tournament configuration for a given day and sequence.

    This is useful for verifying the schedule before creating tournaments.
    """
    print_header()

    try:
        config = get_config()
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    print(f"Configuration for sequence {sequence}, {day}:")
    print()

    schedules = get_single_day_schedules(sequence, day, config.timezone)
    print_dry_run(sequence, schedules, config.team_id)


# Main entry point
def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()