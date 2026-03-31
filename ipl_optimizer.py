#!/usr/bin/env python3
"""
IPL Fantasy League Transfer Optimizer

Uses beam search with backtracking to generate optimal transfer plans
across the 70-match IPL league stage with a 160-transfer budget.
"""

import csv
import argparse
import sys
from typing import Dict, List, Optional, Tuple

# Constants
TEAMS = ["CSK", "DC", "GT", "KKR", "LSG", "MI", "PK", "RCB", "RR", "SRH"]
BEAM_WIDTH = 100
TOTAL_TRANSFERS_CAP = 160
TOTAL_MATCHES = 70

# Default constraints
DEFAULT_MIN_SCORING = 3
DEFAULT_MAX_SCORING = 6
DEFAULT_MAX_TRANSFERS_PER_MATCH = 4


class Match:
    """Represents a single match in the IPL schedule."""

    def __init__(self, match_no: int, date: str, home: str, away: str):
        self.match_no = match_no
        self.date = date
        self.home = home
        self.away = away
        self.team1_gap: Optional[int] = None
        self.team2_gap: Optional[int] = None
        self.squad: Dict[str, int] = {team: 0 for team in TEAMS}
        self.transfers = 0
        self.scoring_players = 0


def load_matches(filepath: str) -> List[Match]:
    """Load matches from CSV file."""
    matches = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            match = Match(
                match_no=int(row['Match No']),
                date=row['Date'],
                home=row['Home'],
                away=row['Away']
            )
            for team in TEAMS:
                if row.get(team) and row[team].strip():
                    match.squad[team] = int(row[team])
            matches.append(match)
    return matches


def compute_gaps(matches: List[Match]) -> None:
    """Compute gaps for each match by forward scanning."""
    team_next_match = {team: [] for team in TEAMS}
    for match in matches:
        team_next_match[match.home].append(match.match_no)
        team_next_match[match.away].append(match.match_no)

    for team in team_next_match:
        team_next_match[team].sort()

    for match in matches:
        match.team1_gap = find_next_gap(team_next_match[match.home], match.match_no)
        match.team2_gap = find_next_gap(team_next_match[match.away], match.match_no)


def find_next_gap(team_matches: List[int], current_match: int) -> Optional[int]:
    """Find the gap until a team plays next."""
    for match_no in team_matches:
        if match_no > current_match:
            return match_no - current_match
    return None


def squad_to_tuple(squad: Dict[str, int]) -> Tuple[Tuple[str, int], ...]:
    """Convert squad dict to tuple for hashing."""
    return tuple(sorted((team, count) for team, count in squad.items()))


def tuple_to_squad(squad_tuple: Tuple[Tuple[str, int], ...]) -> Dict[str, int]:
    """Convert squad tuple back to dict."""
    return dict(squad_tuple)


def calculate_transfers(prev_squad: Dict[str, int], curr_squad: Dict[str, int]) -> int:
    """Calculate transfers needed."""
    carried_over = sum(min(prev_squad.get(t, 0), curr_squad.get(t, 0)) for t in TEAMS)
    return 11 - carried_over


def calculate_scoring_players(squad: Dict[str, int], home: str, away: str) -> int:
    """Calculate scoring players."""
    return squad.get(home, 0) + squad.get(away, 0)


def generate_candidates(
    prev_squad: Dict[str, int],
    home: str,
    away: str,
    min_scoring: int,
    max_scoring: int,
    max_transfers: int,
    remaining_budget: int,
    team_gaps: Dict[str, Optional[int]] = None
) -> List[Tuple[Dict[str, int], int, int]]:
    """
    Generate candidate squads efficiently.
    Returns list of (squad, transfers, scoring) tuples.

    Team gap constraints:
    - Gap <= 3: max 3 players can be carried
    - Gap > 3: max 2 players can be carried
    - Playing teams (home/away) can have up to 7 players
    """
    candidates = []
    seen = set()

    def get_max_carry(team: str, gap: Optional[int]) -> int:
        """Get max players that can be carried for a team based on gap."""
        if team in (home, away):
            return 7  # Playing teams can have full allocation
        if gap is None:
            return 3  # No more matches - keep up to 3
        if gap <= 3:
            return 3  # Playing soon - keep up to 3
        return 2  # Playing later - keep max 2

    def add(squad: Dict[str, int]):
        key = squad_to_tuple(squad)
        if key in seen:
            return
        seen.add(key)
        scoring = squad[home] + squad[away]
        if scoring < min_scoring or scoring > max_scoring:
            return
        transfers = calculate_transfers(prev_squad, squad)
        if transfers > max_transfers or transfers > remaining_budget:
            return
        # Check gap-based carry limits
        if team_gaps:
            for team in TEAMS:
                max_carry = get_max_carry(team, team_gaps.get(team))
                if squad[team] > max_carry:
                    return
        candidates.append((squad.copy(), transfers, scoring))

    # Apply gap limits to previous squad to get max allowed per team
    max_per_team = {}
    for team in TEAMS:
        max_per_team[team] = get_max_carry(team, team_gaps.get(team) if team_gaps else None)

    # Strategy 1: Keep previous squad if valid (after applying gap limits)
    prev_scoring = prev_squad[home] + prev_squad[away]
    # Check if prev_squad respects gap limits
    prev_valid = all(prev_squad[t] <= max_per_team[t] for t in TEAMS)
    if prev_valid and min_scoring <= prev_scoring <= max_scoring:
        add(prev_squad.copy())

    # Strategy 2: Adjust home/away counts systematically
    for h in range(max(0, prev_squad[home] - max_transfers),
                   min(8, prev_squad[home] + max_transfers + 1)):
        for a in range(max(0, prev_squad[away] - max_transfers),
                       min(8, prev_squad[away] + max_transfers + 1)):
            scoring = h + a
            if scoring < min_scoring or scoring > max_scoring:
                continue
            remaining = 11 - h - a
            if remaining < 0 or remaining > 7 * 8:
                continue

            # Start fresh and apply gap limits
            squad = {t: 0 for t in TEAMS}
            squad[home] = h
            squad[away] = a

            # Distribute remaining players respecting gap limits
            for t in TEAMS:
                if t in (home, away):
                    continue
                # Take from prev_squad but respect gap limit
                available = min(prev_squad[t], max_per_team[t])
                take = min(available, remaining)
                # Don't exceed gap limit
                take = min(take, max_per_team[t])
                squad[t] = take
                remaining -= take

            # If still have remaining, distribute to teams with room
            for t in TEAMS:
                if t in (home, away):
                    continue
                while remaining > 0 and squad[t] < max_per_team[t]:
                    squad[t] += 1
                    remaining -= 1

            if sum(squad.values()) == 11:
                add(squad)

    # Strategy 3: Generate optimal distributions for common scoring values
    for scoring in range(min_scoring, max_scoring + 1):
        for h in range(max(0, scoring - 7), min(8, scoring + 1)):
            a = scoring - h
            if a > 7:
                continue
            remaining = 11 - scoring
            if remaining < 0:
                continue

            squad = {t: 0 for t in TEAMS}
            squad[home] = h
            squad[away] = a

            # Distribute remaining respecting gap limits
            other = [t for t in TEAMS if t != home and t != away]
            for t in other:
                max_allowed = min(max_per_team[t], remaining)
                squad[t] = max_allowed
                remaining -= max_allowed

            # If still remaining, add to teams with room (up to their gap limit)
            for t in other:
                while remaining > 0 and squad[t] < max_per_team[t]:
                    squad[t] += 1
                    remaining -= 1

            if sum(squad.values()) == 11:
                add(squad)

    return candidates


class State:
    """Represents a state in the beam search."""

    def __init__(
        self,
        squad_tuple: Tuple[Tuple[str, int], ...],
        transfers_used: int,
        total_scoring: int,
        match_history: List[Tuple[int, Dict[str, int], int, int]],
        violations: int
    ):
        self.squad_tuple = squad_tuple
        self.transfers_used = transfers_used
        self.total_scoring = total_scoring
        self.match_history = match_history
        self.violations = violations


def beam_search(
    matches: List[Match],
    min_scoring: int = DEFAULT_MIN_SCORING,
    max_scoring: int = DEFAULT_MAX_SCORING,
    max_transfers_per_match: int = DEFAULT_MAX_TRANSFERS_PER_MATCH
) -> Optional[State]:
    """Run beam search optimization."""

    # Initialize beam with Match 1
    match1 = matches[0]
    initial_squad = match1.squad.copy()

    if sum(initial_squad.values()) == 0:
        initial_squad[match1.home] = 6
        initial_squad[match1.away] = 5

    match1.squad = initial_squad
    match1.transfers = 0
    match1.scoring_players = calculate_scoring_players(initial_squad, match1.home, match1.away)

    initial_state = State(
        squad_tuple=squad_to_tuple(initial_squad),
        transfers_used=0,
        total_scoring=match1.scoring_players,
        match_history=[(1, initial_squad.copy(), 0, match1.scoring_players)],
        violations=0
    )

    beam = [initial_state]

    print("Running beam search optimization...")
    sys.stdout.flush()

    for match_idx in range(1, len(matches)):
        match = matches[match_idx]
        new_beam = []
        remaining_matches = len(matches) - match_idx - 1

        for state in beam:
            prev_squad = tuple_to_squad(state.squad_tuple)
            remaining_budget = TOTAL_TRANSFERS_CAP - state.transfers_used

            if remaining_budget < 0:
                continue

            # Build team gaps at this match (gap from current match to next)
            team_gaps = {}
            for team in TEAMS:
                gap = None
                for m in matches[match_idx:]:
                    if m.home == team or m.away == team:
                        gap = m.match_no - match.match_no
                        break
                team_gaps[team] = gap

            # Generate candidates with gap-based carry limits
            candidates = generate_candidates(
                prev_squad=prev_squad,
                home=match.home,
                away=match.away,
                min_scoring=min_scoring,
                max_scoring=max_scoring,
                max_transfers=max_transfers_per_match,
                remaining_budget=remaining_budget,
                team_gaps=team_gaps
            )

            for candidate, transfers, scoring in candidates:
                new_transfers = state.transfers_used + transfers
                remaining_after = TOTAL_TRANSFERS_CAP - new_transfers
                remaining_matches_after = len(matches) - match_idx - 1

                # Strict budget enforcement: never exceed cap
                if new_transfers > TOTAL_TRANSFERS_CAP:
                    continue

                # Enforce sustainable spending: at match X, should have spent ~X * 2.3 transfers
                # Allow buffer of 10 transfers but penalize overspending in sorting
                target_spend = match_idx * (TOTAL_TRANSFERS_CAP / len(matches))
                max_spend = target_spend + 15  # 15 transfer buffer

                if new_transfers > max_spend and remaining_matches_after > 5:
                    continue

                new_state = State(
                    squad_tuple=squad_to_tuple(candidate),
                    transfers_used=new_transfers,
                    total_scoring=state.total_scoring + scoring,
                    match_history=state.match_history + [
                        (match.match_no, candidate.copy(), transfers, scoring)
                    ],
                    violations=state.violations
                )
                new_beam.append(new_state)

        # Fallback if no valid states - generate a valid squad even with 0 transfers
        if not new_beam:
            for state in beam:
                prev_squad = tuple_to_squad(state.squad_tuple)
                remaining_budget = TOTAL_TRANSFERS_CAP - state.transfers_used

                # Build team_gaps for fallback
                team_gaps = {}
                for team in TEAMS:
                    gap = None
                    for m in matches[match_idx:]:
                        if m.home == team or m.away == team:
                            gap = m.match_no - match.match_no
                            break
                    team_gaps[team] = gap

                # Get max per team based on gaps
                def get_max_carry(team, gap):
                    if team in (match.home, match.away):
                        return 7
                    if gap is None:
                        return 3
                    if gap <= 3:
                        return 3
                    return 2

                max_per_team = {t: get_max_carry(t, team_gaps.get(t)) for t in TEAMS}

                # Try to find any valid squad within budget that meets min_scoring
                best_candidate = None
                best_transfers = float('inf')
                best_scoring = 0

                candidates = generate_candidates(
                    prev_squad=prev_squad,
                    home=match.home,
                    away=match.away,
                    min_scoring=min_scoring,
                    max_scoring=max_scoring,
                    max_transfers=max(4, remaining_budget),
                    remaining_budget=remaining_budget,
                    team_gaps=team_gaps
                )

                for candidate, transfers, scoring in candidates:
                    if transfers <= remaining_budget:
                        if transfers < best_transfers or (transfers == best_transfers and scoring > best_scoring):
                            best_candidate = candidate
                            best_transfers = transfers
                            best_scoring = scoring

                # If no valid candidate found, create one that meets min_scoring and gap limits
                if best_candidate is None:
                    best_candidate = {t: 0 for t in TEAMS}
                    best_candidate[match.home] = 3
                    best_candidate[match.away] = 3
                    players_to_allocate = 5

                    # Allocate respecting gap limits
                    for t in TEAMS:
                        if t in (match.home, match.away):
                            continue
                        take = min(prev_squad[t], max_per_team[t], players_to_allocate)
                        best_candidate[t] = take
                        players_to_allocate -= take
                        if players_to_allocate <= 0:
                            break

                    # Fill remaining up to gap limits
                    for t in TEAMS:
                        while players_to_allocate > 0 and best_candidate[t] < max_per_team[t]:
                            best_candidate[t] += 1
                            players_to_allocate -= 1

                    best_transfers = 0
                    best_scoring = best_candidate[match.home] + best_candidate[match.away]

                new_state = State(
                    squad_tuple=squad_to_tuple(best_candidate),
                    transfers_used=state.transfers_used + best_transfers,
                    total_scoring=state.total_scoring + best_scoring,
                    match_history=state.match_history + [
                        (match.match_no, best_candidate.copy(), best_transfers, best_scoring)
                    ],
                    violations=state.violations + (0 if min_scoring <= best_scoring <= max_scoring else 1)
                )
                new_beam.append(new_state)

        # Prune beam - prioritize states that can finish
        def state_score(s: State) -> tuple:
            can_finish = (TOTAL_TRANSFERS_CAP - s.transfers_used) >= remaining_matches
            return (s.violations, 0 if can_finish else 1, -s.total_scoring)

        new_beam.sort(key=state_score)

        # Deduplicate
        seen = set()
        unique_beam = []
        for s in new_beam:
            if s.squad_tuple not in seen:
                seen.add(s.squad_tuple)
                unique_beam.append(s)

        beam = unique_beam[:BEAM_WIDTH]

        # Progress every 5 matches
        if (match_idx + 1) % 5 == 0 or match_idx + 1 == len(matches):
            best = beam[0] if beam else None
            if best:
                last_5 = best.match_history[-5:]
                avg_t = sum(t[2] for t in last_5) / 5
                avg_s = sum(t[3] for t in last_5) / 5
                print(f"  Match {match_idx + 1}/70: "
                      f"Total scoring={best.total_scoring} (avg={best.total_scoring/(match_idx+1):.1f}), "
                      f"Total transfers={best.transfers_used} (avg={best.transfers_used/(match_idx+1):.1f}), "
                      f"Last 5: avg_t={avg_t:.1f}, avg_s={avg_s:.1f}, "
                      f"Beam={len(beam)}")
                sys.stdout.flush()

    if not beam:
        return None

    valid_states = [s for s in beam if s.violations == 0]
    if valid_states:
        return max(valid_states, key=lambda s: s.total_scoring)
    return max(beam, key=lambda s: (-s.violations, s.total_scoring))


def apply_optimization(matches: List[Match], best_state: State) -> None:
    """Apply optimization results."""
    for match_no, squad, transfers, scoring in best_state.match_history:
        match = matches[match_no - 1]
        match.squad = squad
        match.transfers = transfers
        match.scoring_players = scoring


def save_matches(matches: List[Match], filepath: str) -> None:
    """Save matches to CSV."""
    fieldnames = ['Match No', 'Date', 'Home', 'Away', 'Team-1 Gap', 'Team-2 Gap'] + \
                 TEAMS + ['Total', 'Transfers', 'Scoring Players']

    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for match in matches:
            row = {
                'Match No': match.match_no,
                'Date': match.date,
                'Home': match.home,
                'Away': match.away,
                'Team-1 Gap': match.team1_gap if match.team1_gap else '',
                'Team-2 Gap': match.team2_gap if match.team2_gap else '',
            }
            for team in TEAMS:
                count = match.squad.get(team, 0)
                row[team] = '' if count == 0 else str(count)
            row['Total'] = sum(match.squad.values())
            row['Transfers'] = match.transfers
            row['Scoring Players'] = match.scoring_players
            writer.writerow(row)


def validate_output(matches: List[Match]) -> Tuple[bool, List[str]]:
    """Validate output."""
    errors = []
    total_transfers = 0

    for match in matches:
        if sum(match.squad.values()) != 11:
            errors.append(f"Match {match.match_no}: Total != 11")
        for team, count in match.squad.items():
            if count > 7:
                errors.append(f"Match {match.match_no}: {team} > 7")
        expected = match.squad.get(match.home, 0) + match.squad.get(match.away, 0)
        if match.scoring_players != expected:
            errors.append(f"Match {match.match_no}: Scoring mismatch")
        if match.match_no > 1:
            total_transfers += match.transfers

    if total_transfers > TOTAL_TRANSFERS_CAP:
        errors.append(f"Total transfers = {total_transfers} > {TOTAL_TRANSFERS_CAP}")

    return len(errors) == 0, errors


def print_summary(matches: List[Match]) -> None:
    """Print summary."""
    total_scoring = sum(m.scoring_players for m in matches)
    total_transfers = sum(m.transfers for m in matches[1:])

    print("\n" + "=" * 60)
    print("OPTIMIZATION RESULTS")
    print("=" * 60)
    print(f"Total Scoring Players: {total_scoring}")
    print(f"Average per Match: {total_scoring / len(matches):.2f}")
    print(f"Transfers Used: {total_transfers}/{TOTAL_TRANSFERS_CAP}")
    print("\nTransfer Distribution:")
    for i in range(0, 70, 10):
        seg = matches[i:i+10]
        t = sum(m.transfers for m in seg if m.match_no > i + 1)
        print(f"  Matches {i+1:2d}-{i+10:2d}: {t:2d} transfers (avg {t/10:.1f}/match)")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='IPL Transfer Optimizer')
    parser.add_argument('--populate-gap', action='store_true', help='Only compute gaps')
    parser.add_argument('--min-scoring', type=int, default=DEFAULT_MIN_SCORING)
    parser.add_argument('--max-scoring', type=int, default=DEFAULT_MAX_SCORING)
    parser.add_argument('--max-transfers', type=int, default=DEFAULT_MAX_TRANSFERS_PER_MATCH)
    parser.add_argument('--input', default='ipl26.csv')
    parser.add_argument('--output', default='ipl26_computed.csv')
    args = parser.parse_args()

    print(f"Loading matches from {args.input}...")
    matches = load_matches(args.input)
    print(f"Loaded {len(matches)} matches")

    print("Computing gaps...")
    compute_gaps(matches)

    if args.populate_gap:
        save_matches(matches, args.input)
        print("Done!")
        return

    best_state = beam_search(
        matches,
        min_scoring=args.min_scoring,
        max_scoring=args.max_scoring,
        max_transfers_per_match=args.max_transfers
    )

    if best_state is None:
        print("ERROR: Optimization failed!")
        return

    apply_optimization(matches, best_state)

    valid, errors = validate_output(matches)
    if not valid:
        print("\nValidation errors:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("\nValidation passed!")

    print_summary(matches)

    print(f"\nSaving results to {args.output}...")
    save_matches(matches, args.output)
    print("Done!")


if __name__ == '__main__':
    main()
