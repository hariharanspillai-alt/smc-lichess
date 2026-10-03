#!/usr/bin/env python3
"""
SMC Lichess Tournament Creator - Main Entry Point

This script provides a CLI for creating SMC Academy Chess Club weekly
Swiss tournaments on Lichess.

Usage:
    python smc_tournaments.py --help
    python smc_tournaments.py create --day saturday
    python smc_tournaments.py create --day sunday
    python smc_tournaments.py week
    python smc_tournaments.py week --dry-run
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cli import main

if __name__ == '__main__':
    main()