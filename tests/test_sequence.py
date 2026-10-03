"""Tests for sequence number determination."""

import pytest
from unittest.mock import Mock, patch

from src.sequence import (
    parse_tournament_name,
    get_next_sequence,
    get_existing_tournaments,
    check_duplicate_protection,
    group_existing_by_sequence,
    TournamentInfo
)
from src.lichess_api import SwissTournament


class TestParseTournamentName:
    """Tests for tournament name parsing."""

    def test_parse_exact_match(self):
        """Test parsing a well-formed tournament name."""
        result = parse_tournament_name("346 SMC Saturday Above 1000")
        assert result is not None
        assert result.sequence == 346
        assert result.day == "Saturday"
        assert result.category == "Above 1000"

    def test_parse_below_1000(self):
        """Test parsing Below 1000 category."""
        result = parse_tournament_name("346 SMC Sunday Below 1000")
        assert result is not None
        assert result.sequence == 346
        assert result.day == "Sunday"
        assert result.category == "Below 1000"

    def test_parse_invalid_name(self):
        """Test parsing an invalid tournament name returns None."""
        result = parse_tournament_name("Some Other Tournament")
        assert result is None

    def test_parse_wrong_format(self):
        """Test parsing a name with wrong format returns None."""
        result = parse_tournament_name("346-Above-1000")
        assert result is None


class TestGetNextSequence:
    """Tests for next sequence number determination."""

    def test_empty_tournaments_returns_345(self):
        """Test that empty tournament list returns starting sequence 345."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            mock_api_instance.list_team_swiss_tournaments.return_value = []

            result = get_next_sequence(mock_api_instance, "test-team")
            assert result == 345

    def test_existing_345_returns_346(self):
        """Test that existing sequence 345 returns next sequence 346."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            tournaments = [
                SwissTournament(id="1", name="345 SMC Saturday Above 1000"),
                SwissTournament(id="2", name="345 SMC Sunday Below 1000"),
            ]
            mock_api_instance.list_team_swiss_tournaments.return_value = tournaments

            result = get_next_sequence(mock_api_instance, "test-team")
            assert result == 346

    def test_existing_346_returns_347(self):
        """Test that existing sequence 346 returns next sequence 347."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            tournaments = [
                SwissTournament(id="1", name="346 SMC Saturday Above 1000"),
                SwissTournament(id="2", name="346 SMC Saturday Below 1000"),
                SwissTournament(id="3", name="346 SMC Sunday Above 1000"),
                SwissTournament(id="4", name="346 SMC Sunday Below 1000"),
            ]
            mock_api_instance.list_team_swiss_tournaments.return_value = tournaments

            result = get_next_sequence(mock_api_instance, "test-team")
            assert result == 347

    def test_mixed_sequences_returns_highest_plus_one(self):
        """Test that highest sequence + 1 is always returned."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            tournaments = [
                SwissTournament(id="1", name="344 SMC Saturday Above 1000"),
                SwissTournament(id="2", name="345 SMC Saturday Above 1000"),
                SwissTournament(id="3", name="343 SMC Sunday Below 1000"),
                SwissTournament(id="4", name="346 SMC Saturday Below 1000"),
                SwissTournament(id="5", name="Not an SMC tournament"),
            ]
            mock_api_instance.list_team_swiss_tournaments.return_value = tournaments

            result = get_next_sequence(mock_api_instance, "test-team")
            assert result == 347

    def test_non_smc_tournaments_ignored(self):
        """Test that non-SMC tournaments are ignored."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            tournaments = [
                SwissTournament(id="1", name="Some Other Tournament"),
                SwissTournament(id="2", name="Another Tournament"),
            ]
            mock_api_instance.list_team_swiss_tournaments.return_value = tournaments

            result = get_next_sequence(mock_api_instance, "test-team")
            assert result == 345


class TestGetExistingTournaments:
    """Tests for getting existing tournaments for a sequence."""

    def test_returns_only_matching_sequence(self):
        """Test that only tournaments matching the sequence are returned."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            tournaments = [
                SwissTournament(id="1", name="345 SMC Saturday Above 1000"),
                SwissTournament(id="2", name="345 SMC Sunday Below 1000"),
                SwissTournament(id="3", name="346 SMC Saturday Above 1000"),
                SwissTournament(id="4", name="344 SMC Sunday Above 1000"),
            ]
            mock_api_instance.list_team_swiss_tournaments.return_value = tournaments

            result = get_existing_tournaments(mock_api_instance, "test-team", 345)
            assert len(result) == 2
            assert all(t.sequence == 345 for t in result)


class TestCheckDuplicateProtection:
    """Tests for duplicate tournament protection."""

    def test_returns_true_when_exists(self):
        """Test that True is returned when tournament exists."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            mock_api_instance.list_team_swiss_tournaments.return_value = [
                SwissTournament(id="1", name="346 SMC Saturday Above 1000"),
            ]

            result = check_duplicate_protection(mock_api_instance, "test-team",
                                               "346 SMC Saturday Above 1000")
            assert result is True

    def test_returns_false_when_not_exists(self):
        """Test that False is returned when tournament doesn't exist."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            mock_api_instance.list_team_swiss_tournaments.return_value = [
                SwissTournament(id="1", name="345 SMC Saturday Above 1000"),
            ]

            result = check_duplicate_protection(mock_api_instance, "test-team",
                                                 "346 SMC Saturday Above 1000")
            assert result is False


class TestGroupExistingBySequence:
    """Tests for grouping tournaments by sequence."""

    def test_groups_correctly(self):
        """Test that tournaments are correctly grouped by sequence."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            mock_api_instance.list_team_swiss_tournaments.return_value = [
                SwissTournament(id="1", name="345 SMC Saturday Above 1000"),
                SwissTournament(id="2", name="345 SMC Sunday Below 1000"),
                SwissTournament(id="3", name="346 SMC Saturday Above 1000"),
            ]

            result = group_existing_by_sequence(mock_api_instance, "test-team")

            assert 345 in result
            assert 346 in result
            assert len(result[345]) == 2
            assert len(result[346]) == 1


# Edge case tests for sequence determination

class TestSequenceEdgeCases:
    """Tests for edge cases in sequence determination."""

    def test_only_sunday_exists_preserves_sequence(self):
        """Test that existing Sunday tournament preserves sequence 346."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            tournaments = [
                SwissTournament(id="1", name="346 SMC Sunday Above 1000"),
                SwissTournament(id="2", name="346 SMC Sunday Below 1000"),
            ]
            mock_api_instance.list_team_swiss_tournaments.return_value = tournaments

            result = get_next_sequence(mock_api_instance, "test-team")
            # Should return 347 since 346 already exists
            assert result == 347

    def test_only_saturday_exists_preserves_sequence(self):
        """Test that existing Saturday tournament preserves sequence 346."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            tournaments = [
                SwissTournament(id="1", name="346 SMC Saturday Above 1000"),
            ]
            mock_api_instance.list_team_swiss_tournaments.return_value = tournaments

            result = get_next_sequence(mock_api_instance, "test-team")
            # Should return 347 since 346 already exists
            assert result == 347

    def test_non_smc_tournaments_not_ignored(self):
        """Test that only SMC tournaments with correct naming pattern are counted."""
        with patch('src.sequence.LichessAPI') as mock_api:
            mock_api_instance = Mock()
            # 347 SMC Tournament Name - should NOT be counted
            tournaments = [
                SwissTournament(id="1", name="347 SMC Tournament Name"),
            ]
            mock_api_instance.list_team_swiss_tournaments.return_value = tournaments

            result = get_next_sequence(mock_api_instance, "test-team")
            # Should return 345 since the 347 tournament doesn't match pattern
            assert result == 345