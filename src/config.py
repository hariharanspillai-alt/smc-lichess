"""Configuration management for SMC Lichess tournament creator."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration for Lichess API access and team settings."""

    api_token: str
    team_id: str
    timezone: str = "America/Los_Angeles"

    @classmethod
    def from_env(cls) -> 'Config':
        """
        Load configuration from environment variables.

        Raises:
            ValueError: If required environment variables are missing.
        """
        load_dotenv()

        api_token = os.getenv('LICHESS_API_TOKEN', '').strip()
        team_id = os.getenv('LICHESS_TEAM_ID', '').strip()

        if not api_token:
            raise ValueError("ERROR: LICHESS_API_TOKEN is not configured.")

        if not team_id:
            raise ValueError("ERROR: LICHESS_TEAM_ID is not configured.")

        return cls(
            api_token=api_token,
            team_id=team_id
        )

    def validate(self) -> bool:
        """Validate that the configuration is correct."""
        return bool(self.api_token) and bool(self.team_id)

    def token_header(self) -> dict:
        """Get the Authorization header for API requests."""
        return {"Authorization": f"Bearer {self.api_token}"}


def get_config() -> Config:
    """Get configuration, raising clear error if missing."""
    try:
        return Config.from_env()
    except ValueError as e:
        raise ValueError(str(e))