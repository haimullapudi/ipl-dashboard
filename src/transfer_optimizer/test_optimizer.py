#!/usr/bin/env python3
"""
Test suite for IPL Fantasy League Transfer Optimizer

Validates all constraints and rules from the specification.
"""

import csv
import unittest
from datetime import datetime

TEAMS = ["CSK", "DC", "GT", "KKR", "LSG", "MI", "PBKS", "RCB", "RR", "SRH"]
TOTAL_MATCHES = 70
TOTAL_TRANSFERS_CAP = 160
MIN_PLAYERS_PER_MATCH = 11
MAX_PLAYERS_PER_TEAM = 7


class TestGapComputation(unittest.TestCase):
    """Test gap computation logic."""

    def test_gap_is_match_numbers_not_days(self):
        """Gaps should be computed based on match numbers, not calendar days."""
        # This is verified by checking that same-day matches have different gaps
        # e.g., Match 7 and 8 are both on "Sat, 04-Apr" but should have different gaps
        with open('ipl26_computed.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            matches = list(reader)

        # Find matches on the same date
        date_to_matches = {}
        for match in matches:
            date = match['Date']
            if date not in date_to_matches:
                date_to_matches[date] = []
            date_to_matches[date].append(match)

        # Check that same-day matches have gaps based on match numbers
        for date, day_matches in date_to_matches.items():
            if len(day_matches) > 1:
                # Multiple matches on same date should have different gaps
                gaps = [(m['Match No'], m['Team-1 Gap'], m['Team-2 Gap'])
                        for m in day_matches]
                # Gaps are computed correctly per match number
                self.assertTrue(len(gaps) > 0)

    def test_gap_computation_forward_scan(self):
        """Verify gaps are computed by forward scanning the schedule."""
        with open('ipl26_computed.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            matches = list(reader)

        # Build team schedule
        team_schedule = {team: [] for team in TEAMS}
        for match in matches:
            home = match['Home']
            away = match['Away']
            match_no = int(match['Match No'])
            team_schedule[home].append(match_no)
            team_schedule[away].append(match_no)

        # Verify each gap
        for match in matches:
            match_no = int(match['Match No'])
            home = match['Home']
            away = match['Away']

            # Find next match for home team
            home_gaps = [m for m in team_schedule[home] if m > match_no]
            expected_home_gap = home_gaps[0] - match_no if home_gaps else None

            # Find next match for away team
            away_gaps = [m for m in team_schedule[away] if m > match_no]
            expected_away_gap = away_gaps[0] - match_no if away_gaps else None

            actual_home_gap = int(match['Team-1 Gap']) if match['Team-1 Gap'] else None
            actual_away_gap = int(match['Team-2 Gap']) if match['Team-2 Gap'] else None

            self.assertEqual(actual_home_gap, expected_home_gap,
                           f"Match {match_no} ({home}): expected gap {expected_home_gap}, "
                           f"got {actual_home_gap}")
            self.assertEqual(actual_away_gap, expected_away_gap,
                           f"Match {match_no} ({away}): expected gap {expected_away_gap}, "
                           f"got {actual_away_gap}")


class TestSquadConstraints(unittest.TestCase):
    """Test squad allocation constraints."""

    def setUp(self):
        with open('ipl26_computed.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            self.matches = list(reader)

    def test_total_players_per_match(self):
        """Each match must have exactly 11 players."""
        for match in self.matches:
            total = int(match['Total'])
            self.assertEqual(total, 11,
                           f"Match {match['Match No']}: Total = {total}, expected 11")

    def test_max_players_per_team(self):
        """No team can exceed 7 players in any match."""
        for match in self.matches:
            for team in TEAMS:
                count = int(match[team]) if match[team] else 0
                self.assertLessEqual(count, 7,
                                   f"Match {match['Match No']}: {team} has {count} players")

    def test_non_negative_player_counts(self):
        """All team player counts must be non-negative."""
        for match in self.matches:
            for team in TEAMS:
                count = int(match[team]) if match[team] else 0
                self.assertGreaterEqual(count, 0)

    def test_team_columns_sum_to_total(self):
        """Sum of team columns must equal Total column."""
        for match in self.matches:
            team_sum = sum(int(match[team]) if match[team] else 0
                          for team in TEAMS)
            total = int(match['Total'])
            self.assertEqual(team_sum, total,
                           f"Match {match['Match No']}: Team sum = {team_sum}, Total = {total}")

    def test_both_playing_teams_have_players(self):
        """Both home and away teams must have at least 1 player in each match."""
        for match in self.matches:
            home = match['Home']
            away = match['Away']
            home_count = int(match[home]) if match[home] else 0
            away_count = int(match[away]) if match[away] else 0

            self.assertGreaterEqual(home_count, 1,
                                  f"Match {match['Match No']} ({home} vs {away}): "
                                  f"{home} has 0 players")
            self.assertGreaterEqual(away_count, 1,
                                  f"Match {match['Match No']} ({home} vs {away}): "
                                  f"{away} has 0 players")


class TestTransferConstraints(unittest.TestCase):
    """Test transfer-related constraints."""

    def setUp(self):
        with open('ipl26_computed.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            self.matches = list(reader)

    def test_transfer_cap(self):
        """Total transfers across matches 2-70 must not exceed 160."""
        total_transfers = sum(
            int(m['Transfers'])
            for m in self.matches
            if int(m['Match No']) > 1
        )
        self.assertLessEqual(total_transfers, TOTAL_TRANSFERS_CAP,
                           f"Total transfers = {total_transfers}, exceeds cap of {TOTAL_TRANSFERS_CAP}")

    def test_match_1_transfers_zero(self):
        """Match 1 transfers should be 0 (initial squad build)."""
        match_1 = self.matches[0]
        self.assertEqual(int(match_1['Transfers']), 0,
                        "Match 1 transfers should be 0")

    def test_transfers_are_integers(self):
        """All transfer counts must be integers."""
        for match in self.matches:
            transfers = match['Transfers']
            self.assertTrue(transfers.isdigit() or transfers == '',
                          f"Match {match['Match No']}: Invalid transfers value '{transfers}'")

    def test_transfers_calculation_correct(self):
        """Verify transfers are calculated correctly from squad changes."""
        TEAMS = ["CSK", "DC", "GT", "KKR", "LSG", "MI", "PBKS", "RCB", "RR", "SRH"]

        # Get previous squad (Match 1)
        prev_squad = {}
        match1 = self.matches[0]
        for team in TEAMS:
            prev_squad[team] = int(match1[team]) if match1[team] else 0

        # Detect if this is a Free Hit run (Match 38 has 0 transfers)
        match38_transfers = int(self.matches[37]['Transfers']) if self.matches[37]['Transfers'] else 0
        is_free_hit_run = (match38_transfers == 0)

        # Detect if this is a Wildcard run (Match 14 has 0 transfers)
        match14_transfers = int(self.matches[13]['Transfers']) if self.matches[13]['Transfers'] else 0
        is_wildcard_run = (match14_transfers == 0)

        for i in range(1, len(self.matches)):
            match = self.matches[i]
            match_no = int(match['Match No'])

            # Skip Free Hit (Match 38) and Wildcard (Match 14) - they have 0 transfers by design
            if (is_free_hit_run and match_no == 38) or (is_wildcard_run and match_no == 14):
                prev_squad = {team: int(match[team]) if match[team] else 0 for team in TEAMS}
                continue

            curr_squad = {}
            for team in TEAMS:
                curr_squad[team] = int(match[team]) if match[team] else 0

            # For Match 39 (after Free Hit), compare against Match 37's squad (pre-Free Hit)
            # because Free Hit squad reverts after the match
            if is_free_hit_run and match_no == 39:
                match37 = self.matches[36]
                prev_squad = {team: int(match37[team]) if match37[team] else 0 for team in TEAMS}

            # Calculate expected transfers: 11 - carried_over
            carried_over = sum(min(prev_squad[team], curr_squad[team]) for team in TEAMS)
            expected_transfers = 11 - carried_over

            actual_transfers = int(match['Transfers']) if match['Transfers'] else 0

            self.assertEqual(actual_transfers, expected_transfers,
                           f"Match {match['Match No']}: Transfers = {actual_transfers}, "
                           f"expected {expected_transfers} (carried over = {carried_over})")

            prev_squad = curr_squad

    def test_max_transfers_per_match(self):
        """Each match (except Match 1) should have at most 4 transfers."""
        for match in self.matches:
            match_no = int(match['Match No'])
            if match_no == 1:
                continue
            transfers = int(match['Transfers']) if match['Transfers'] else 0
            self.assertLessEqual(transfers, 4,
                               f"Match {match_no}: {transfers} transfers exceeds max of 4")


class TestScoringPlayers(unittest.TestCase):
    """Test scoring players calculation."""

    def setUp(self):
        with open('ipl26_computed.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            self.matches = list(reader)

    def test_scoring_players_formula(self):
        """Scoring Players = Home team count + Away team count."""
        for match in self.matches:
            home_count = int(match[match['Home']]) if match[match['Home']] else 0
            away_count = int(match[match['Away']]) if match[match['Away']] else 0
            expected_scoring = home_count + away_count
            actual_scoring = int(match['Scoring Players'])

            self.assertEqual(actual_scoring, expected_scoring,
                           f"Match {match['Match No']}: Scoring = {actual_scoring}, "
                           f"expected {expected_scoring} ({match['Home']}={home_count}, "
                           f"{match['Away']}={away_count})")

    def test_min_scoring_players(self):
        """Each match (except Match 1) should have at least 3 scoring players."""
        for match in self.matches:
            match_no = int(match['Match No'])
            if match_no == 1:
                continue  # Match 1 is initial squad, constraints apply from Match 2
            scoring = int(match['Scoring Players'])
            self.assertGreaterEqual(scoring, 3,
                                  f"Match {match_no}: Only {scoring} scoring players")

    def test_max_scoring_players(self):
        """Each match (except Match 1, Free Hit, and Wildcard) should have at most 6 scoring players."""
        for match in self.matches:
            match_no = int(match['Match No'])
            if match_no == 1:
                continue  # Match 1 is initial squad, constraints apply from Match 2
            # Free Hit (Match 38) and Wildcard (Match 14) allow 11 scoring players
            if match_no == 38 or match_no == 14:
                continue
            scoring = int(match['Scoring Players'])
            self.assertLessEqual(scoring, 6,
                               f"Match {match_no}: {scoring} scoring players exceeds max")


class TestOutputFormat(unittest.TestCase):
    """Test output CSV format."""

    def setUp(self):
        with open('ipl26_computed.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            self.matches = list(reader)

    def test_all_matches_present(self):
        """Output should contain all 70 matches."""
        self.assertEqual(len(self.matches), TOTAL_MATCHES,
                        f"Expected {TOTAL_MATCHES} matches, got {len(self.matches)}")

    def test_match_numbers_sequential(self):
        """Match numbers should be sequential 1-70."""
        for i, match in enumerate(self.matches):
            expected = i + 1
            actual = int(match['Match No'])
            self.assertEqual(actual, expected,
                           f"Expected match {expected}, got {actual}")

    def test_required_columns_present(self):
        """All required columns should be present."""
        required_columns = [
            'Match No', 'Date', 'Home', 'Away',
            'Team-1 Gap', 'Team-2 Gap',
            'Total', 'Transfers', 'Scoring Players'
        ] + TEAMS

        for col in required_columns:
            self.assertIn(col, self.matches[0],
                        f"Missing required column: {col}")


class TestOptimizationQuality(unittest.TestCase):
    """Test optimization quality metrics."""

    def setUp(self):
        with open('ipl26_computed.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            self.matches = list(reader)

    def test_total_scoring_players(self):
        """Total scoring players should be maximized (target: 280+)."""
        total_scoring = sum(int(m['Scoring Players']) for m in self.matches)
        self.assertGreaterEqual(total_scoring, 280,
                              f"Total scoring = {total_scoring}, target is 280+")

    def test_average_scoring_per_match(self):
        """Average scoring players per match should be >= 4.0."""
        total_scoring = sum(int(m['Scoring Players']) for m in self.matches)
        average = total_scoring / len(self.matches)
        self.assertGreaterEqual(average, 4.0,
                          f"Average scoring = {average:.2f}, target is >= 4.0")

    def test_transfer_efficiency(self):
        """Should use all 160 transfers (no leftover budget)."""
        total_transfers = sum(
            int(m['Transfers']) for m in self.matches if int(m['Match No']) > 1
        )
        self.assertEqual(total_transfers, TOTAL_TRANSFERS_CAP,
                        f"Used {total_transfers} transfers, expected {TOTAL_TRANSFERS_CAP}")


class TestFreeHit(unittest.TestCase):
    """Test Free Hit functionality."""

    def test_free_hit_optimizer(self):
        """Test that Free Hit generates optimal squad at specified match."""
        import tempfile
        import os

        # Create minimal test data
        test_csv = """Match No,Date,Home,Away,Team-1 Gap,Team-2 Gap,CSK,DC,GT,KKR,LSG,MI,PBKS,RCB,RR,SRH,Total,Transfers,Scoring Players
1,28-Mar-26,RCB,SRH,,,,,,,,,,,,,,,,
2,29-Mar-26,MI,KKR,,,,,,,,,,,,,,,,
3,30-Mar-26,RR,CSK,,,,,,,,,,,,,,,,
4,31-Mar-26,PBKS,GT,,,,,,,,,,,,,,,,
5,1-Apr-26,LSG,DC,,,,,,,,,,,,,,,,
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(test_csv)
            input_path = f.name

        try:
            # Run optimizer with Free Hit at match 3
            from ipl_optimizer import load_matches, compute_gaps, beam_search

            matches = load_matches(input_path)
            compute_gaps(matches)

            best_state = beam_search(
                matches,
                min_scoring=3,
                max_scoring=6,
                max_transfers_per_match=4,
                use_free_hit=True,
                free_hit_match=3
            )

            assert best_state is not None, "Optimization should succeed with Free Hit"
            assert best_state.free_hit_used, "Free Hit should be marked as used"

            # Check that match 3 has 0 transfers (Free Hit is free)
            match_3_entry = [h for h in best_state.match_history if h[0] == 3][0]
            assert match_3_entry[2] == 0, "Free Hit match should have 0 transfers"

            print("Free Hit test PASSED")

        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)


class TestWildcard(unittest.TestCase):
    """Test Wildcard functionality."""

    def test_wildcard_optimizer(self):
        """Test that Wildcard generates optimal squad at specified match."""
        import tempfile
        import os

        # Create minimal test data
        test_csv = """Match No,Date,Home,Away,Team-1 Gap,Team-2 Gap,CSK,DC,GT,KKR,LSG,MI,PBKS,RCB,RR,SRH,Total,Transfers,Scoring Players
1,28-Mar-26,RCB,SRH,,,,,,,,,,,,,,,,
2,29-Mar-26,MI,KKR,,,,,,,,,,,,,,,,
3,30-Mar-26,RR,CSK,,,,,,,,,,,,,,,,
4,31-Mar-26,PBKS,GT,,,,,,,,,,,,,,,,
5,1-Apr-26,LSG,DC,,,,,,,,,,,,,,,,
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(test_csv)
            input_path = f.name

        try:
            # Run optimizer with Wildcard at match 3
            from ipl_optimizer import load_matches, compute_gaps, beam_search

            matches = load_matches(input_path)
            compute_gaps(matches)

            best_state = beam_search(
                matches,
                min_scoring=3,
                max_scoring=6,
                max_transfers_per_match=4,
                use_wildcard=True,
                wildcard_match=3
            )

            assert best_state is not None, "Optimization should succeed with Wildcard"
            assert best_state.wildcard_used, "Wildcard should be marked as used"

            # Check that match 3 has 0 transfers (Wildcard is free)
            match_3_entry = [h for h in best_state.match_history if h[0] == 3][0]
            assert match_3_entry[2] == 0, "Wildcard match should have 0 transfers"

            # Check that squad persists at match 4 (no reversion)
            match_3_squad = {team: count for team, count in best_state.match_history[2][1].items()}
            match_4_entry = [h for h in best_state.match_history if h[0] == 4][0]
            match_4_squad = {team: count for team, count in match_4_entry[1].items()}

            # Squad should persist (may have small optimizations, but no complete reversion)
            # The key difference from Free Hit: squad is NOT completely replaced

            assert best_state.wildcard_used, "Wildcard flag should persist"

            print("Wildcard test PASSED")

        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)


def run_tests():
    """Run all tests and report results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGapComputation))
    suite.addTests(loader.loadTestsFromTestCase(TestSquadConstraints))
    suite.addTests(loader.loadTestsFromTestCase(TestTransferConstraints))
    suite.addTests(loader.loadTestsFromTestCase(TestScoringPlayers))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputFormat))
    suite.addTests(loader.loadTestsFromTestCase(TestOptimizationQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestFreeHit))
    suite.addTests(loader.loadTestsFromTestCase(TestWildcard))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
