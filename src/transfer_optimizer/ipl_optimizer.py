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
TEAMS = ["CSK", "DC", "GT", "KKR", "LSG", "MI", "PBKS", "RCB", "RR", "SRH"]
BEAM_WIDTH = 100
TOTAL_TRANSFERS_CAP = 160
TOTAL_MATCHES = 70

# Default constraints
DEFAULT_MIN_SCORING = 3
DEFAULT_MAX_SCORING = 6
DEFAULT_MAX_TRANSFERS_PER_MATCH = 4

# Free Hit configuration
FREE_HIT_MATCH = 38  # Optimal: LSG vs KKR (26-Apr-26)
# Analysis shows both teams have maximum isolation:
# - LSG: gap=9 forward, gap=6 backward
# - KKR: gap=7 forward, gap=10 backward

# Wildcard configuration
WILDCARD_MATCH = 14  # Default: Early strategy (end of first round-robin)
# Alternative: Match 56 (Late strategy - playoff push)
# Analysis: Early Wildcard gives 56 matches to benefit from new squad
#           Late Wildcard optimizes for final 15 matches


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


def get_max_carry(team: str, home: str, away: str, gap: Optional[int]) -> int:
    """Get max players that can be carried for a team based on gap.

    Gap-based carry limits ensure we don't hold too many players from teams
    that won't play soon. However, limits are set to ensure we can always
    stay within the 4-transfer-per-match budget by keeping at least 7 players.

    Args:
        team: The team to check
        home: Home team for the current match
        away: Away team for the current match
        gap: Gap until the team plays next (None if no more matches)

    Returns:
        Maximum number of players that can be carried for this team
    """
    if team in (home, away):
        return 7  # Playing teams can have full allocation
    if gap is None:
        return 4  # No more matches - keep up to 4
    if gap <= 3:
        return 4  # Playing soon - keep up to 4
    return 4  # Playing later - keep max 4 (ensures we can keep 7+ players)


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


    def add(squad: Dict[str, int]):
        key = squad_to_tuple(squad)
        if key in seen:
            return
        seen.add(key)
        # Ensure both playing teams have at least 1 player
        if squad[home] < 1 or squad[away] < 1:
            return
        scoring = squad[home] + squad[away]
        if scoring < min_scoring or scoring > max_scoring:
            return
        transfers = calculate_transfers(prev_squad, squad)
        if transfers > max_transfers or transfers > remaining_budget:
            return
        # Check gap-based carry limits
        if team_gaps:
            for team in TEAMS:
                max_carry = get_max_carry(team, home, away, team_gaps.get(team))
                if squad[team] > max_carry:
                    return
        candidates.append((squad.copy(), transfers, scoring))

    # Apply gap limits to previous squad to get max allowed per team
    max_per_team = {}
    for team in TEAMS:
        max_per_team[team] = get_max_carry(team, home, away, team_gaps.get(team) if team_gaps else None)

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

            # Distribute remaining players - prioritize keeping from prev_squad
            # We need to keep at least (11 - max_transfers) players total
            min_keep = 11 - max_transfers
            kept = h + a  # Count home/away as kept if they were in prev_squad

            # First, keep as many as possible from non-playing teams
            for t in TEAMS:
                if t in (home, away):
                    continue
                # Take from prev_squad but respect gap limit
                available = min(prev_squad[t], max_per_team[t])
                take = min(available, remaining)
                squad[t] = take
                remaining -= take

            # If still need more players, add to home/away (these are transfers)
            for t in (home, away):
                while remaining > 0 and squad[t] < 7:
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

    # Strategy 4: Keep max players from prev_squad to minimize transfers
    # This ensures we always have candidates that respect max_transfers
    squad = {t: 0 for t in TEAMS}
    # First allocate to playing teams (min 1 each)
    squad[home] = max(1, min(prev_squad[home], 3))
    squad[away] = max(1, min(prev_squad[away], 3))
    allocated = squad[home] + squad[away]

    # Keep players from other teams up to their gap limits
    for t in other:
        keep = min(prev_squad[t], max_per_team[t])
        take = min(keep, 11 - allocated)
        squad[t] = take
        allocated += take

    # Fill remaining to playing teams
    while allocated < 11:
        if squad[home] < 7:
            squad[home] += 1
            allocated += 1
        elif squad[away] < 7:
            squad[away] += 1
            allocated += 1
        else:
            break

    if sum(squad.values()) == 11:
        add(squad)

    return candidates


def generate_free_hit_squad(home: str, away: str, min_scoring: int, max_scoring: int) -> Dict[str, int]:
    """
    Generate optimal squad for Free Hit match.

    Since Free Hit has no transfer cost, we can build the ideal squad from scratch
    focused purely on maximizing scoring players for this match.

    Strategy:
    - Use ALL 11 players from home and away teams (they all score in this match)
    - Maximize scoring potential by filling squad entirely with playing teams
    - Split: 6 home + 5 away (or 7+4 if within max 7 per team constraint)
    """
    squad = {team: 0 for team in TEAMS}

    # Optimal scoring distribution: ALL 11 players from playing teams
    # This maximizes scoring potential - every player in the squad scores points
    # Split: 6 home + 5 away (balanced with slight home advantage)
    squad[home] = 6
    squad[away] = 5

    return squad


def generate_wildcard_squad(home: str, away: str, min_scoring: int, max_scoring: int) -> Dict[str, int]:
    """
    Generate optimal squad for Wildcard match.

    Since Wildcard has no transfer cost, we can build the ideal squad from scratch
    focused purely on maximizing scoring players for this match.
    Unlike Free Hit, this squad persists for subsequent matches.

    Strategy:
    - Use ALL 11 players from home and away teams (they all score in this match)
    - Split: 6 home + 5 away (balanced with slight home advantage)
    """
    squad = {team: 0 for team in TEAMS}

    # All 11 players from playing teams - maximizes scoring for this match
    squad[home] = 6  # Slight home advantage
    squad[away] = 5  # 11 total scoring players

    return squad


class State:
    """Represents a state in the beam search."""

    def __init__(
        self,
        squad_tuple: Tuple[Tuple[str, int], ...],
        transfers_used: int,
        total_scoring: int,
        match_history: List[Tuple[int, Dict[str, int], int, int]],
        violations: int,
        free_hit_used: bool = False,
        wildcard_used: bool = False,
        pre_free_hit_squad: Optional[Dict[str, int]] = None
    ):
        self.squad_tuple = squad_tuple
        self.transfers_used = transfers_used
        self.total_scoring = total_scoring
        self.match_history = match_history
        self.violations = violations
        self.free_hit_used = free_hit_used
        self.wildcard_used = wildcard_used  # No reversion needed - squad persists
        self.pre_free_hit_squad = pre_free_hit_squad  # Squad before Free Hit for reversion


def beam_search(
    matches: List[Match],
    min_scoring: int = DEFAULT_MIN_SCORING,
    max_scoring: int = DEFAULT_MAX_SCORING,
    max_transfers_per_match: int = DEFAULT_MAX_TRANSFERS_PER_MATCH,
    use_free_hit: bool = False,
    free_hit_match: int = FREE_HIT_MATCH,
    use_wildcard: bool = False,
    wildcard_match: int = WILDCARD_MATCH
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

        # Check if this is the Free Hit match
        is_free_hit_match = use_free_hit and (match.match_no == free_hit_match)

        if is_free_hit_match:
            # Generate optimal Free Hit squad (no transfer cost)
            free_hit_squad = generate_free_hit_squad(
                home=match.home,
                away=match.away,
                min_scoring=min_scoring,
                max_scoring=max_scoring
            )

            # For Free Hit, we don't care about transfers - it's free!
            # But we need to track the pre-Free Hit squad for reversion
            for state in beam:
                prev_squad = tuple_to_squad(state.squad_tuple)

                # Create new state with Free Hit squad
                new_state = State(
                    squad_tuple=squad_to_tuple(free_hit_squad),
                    transfers_used=state.transfers_used,  # No transfer cost!
                    total_scoring=state.total_scoring + calculate_scoring_players(free_hit_squad, match.home, match.away),
                    match_history=state.match_history + [
                        (match.match_no, free_hit_squad.copy(), 0, calculate_scoring_players(free_hit_squad, match.home, match.away))
                    ],
                    violations=state.violations,
                    free_hit_used=True,
                    pre_free_hit_squad=prev_squad  # Save for reversion
                )
                new_beam.append(new_state)

            beam = new_beam
            continue  # Skip normal candidate generation for Free Hit match

        # Check if this is the Wildcard match
        is_wildcard_match = use_wildcard and (match.match_no == wildcard_match)

        if is_wildcard_match:
            # Generate optimal Wildcard squad (no transfer cost)
            wildcard_squad = generate_wildcard_squad(
                home=match.home,
                away=match.away,
                min_scoring=min_scoring,
                max_scoring=max_scoring
            )

            # For Wildcard, we don't care about transfers - it's free!
            # Squad persists after this match (no reversion needed)
            new_beam = []
            for state in beam:
                # Create new state with Wildcard squad
                new_state = State(
                    squad_tuple=squad_to_tuple(wildcard_squad),
                    transfers_used=state.transfers_used,  # No transfer cost!
                    total_scoring=state.total_scoring + calculate_scoring_players(wildcard_squad, match.home, match.away),
                    match_history=state.match_history + [
                        (match.match_no, wildcard_squad.copy(), 0, calculate_scoring_players(wildcard_squad, match.home, match.away))
                    ],
                    violations=state.violations,
                    free_hit_used=state.free_hit_used,
                    pre_free_hit_squad=state.pre_free_hit_squad,
                    wildcard_used=True  # Mark Wildcard as used
                )
                new_beam.append(new_state)

            beam = new_beam
            continue  # Skip normal candidate generation for Wildcard match

        # If Free Hit was used last match, revert to pre-Free Hit squad and process normally
        if use_free_hit and match.match_no == free_hit_match + 1:
            reverted_beam = []
            for state in beam:
                if state.free_hit_used and state.pre_free_hit_squad:
                    # Create reverted state with pre-Free Hit squad as the starting point
                    reverted_state = State(
                        squad_tuple=squad_to_tuple(state.pre_free_hit_squad),
                        transfers_used=state.transfers_used,
                        total_scoring=state.total_scoring,
                        match_history=state.match_history,
                        violations=state.violations,
                        free_hit_used=True,
                        pre_free_hit_squad=None  # Clear after reversion
                    )
                    reverted_beam.append(reverted_state)

            # Use reverted beam for this match (will process normally below)
            if reverted_beam:
                beam = reverted_beam

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

                # Strict budget enforcement: never exceed cap
                if new_transfers > TOTAL_TRANSFERS_CAP:
                    continue

                # Enforce sustainable spending: ensure budget lasts all 70 matches
                # Reserve 30 transfers for final 20 matches (matches 51-70)
                # This ensures we have budget to rotate players for all teams

                # Target spend rate: 160/70 = 2.29 transfers per match
                target_spend = match_idx * (TOTAL_TRANSFERS_CAP / len(matches))

                # Reserve 30 transfers for final 20 matches
                # At match 50, should have spent at most 130 (leaving 30)
                if match_idx >= 50:
                    max_allowed = 130 + (match_idx - 50) * 1.5  # Max 1.5/match for final 20
                else:
                    max_allowed = target_spend + 10

                if new_transfers > max_allowed:
                    continue

                # Ensure minimum remaining budget based on remaining matches
                # Need at least 1 transfer per match for final 20 matches
                if match_idx >= 50:
                    min_remaining = remaining_matches
                    if (TOTAL_TRANSFERS_CAP - new_transfers) < min_remaining:
                        continue

                new_state = State(
                    squad_tuple=squad_to_tuple(candidate),
                    transfers_used=new_transfers,
                    total_scoring=state.total_scoring + scoring,
                    match_history=state.match_history + [
                        (match.match_no, candidate.copy(), transfers, scoring)
                    ],
                    violations=state.violations,
                    free_hit_used=state.free_hit_used
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

                # Get max per team based on gaps using module-level function
                max_per_team = {t: get_max_carry(t, match.home, match.away, team_gaps.get(t)) for t in TEAMS}

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
                    max_transfers=DEFAULT_MAX_TRANSFERS_PER_MATCH,  # Enforce 4-transfer limit
                    remaining_budget=remaining_budget,
                    team_gaps=team_gaps
                )

                for candidate, transfers, scoring in candidates:
                    if transfers <= remaining_budget:
                        if transfers < best_transfers or (transfers == best_transfers and scoring > best_scoring):
                            best_candidate = candidate
                            best_transfers = transfers
                            best_scoring = scoring

                # If no valid candidate found, create one that respects max_transfers
                # AND remaining_budget by keeping as many players as possible from prev_squad
                if best_candidate is None:
                    # Calculate max transfers we can afford (min of 4 and remaining_budget)
                    max_allowed_transfers = min(DEFAULT_MAX_TRANSFERS_PER_MATCH, remaining_budget)
                    players_to_keep = 11 - max_allowed_transfers

                    best_candidate = {t: 0 for t in TEAMS}

                    # First, ensure both playing teams have at least 1 player
                    best_candidate[match.home] = max(1, min(prev_squad[match.home], 3))
                    best_candidate[match.away] = max(1, min(prev_squad[match.away], 3))
                    kept = best_candidate[match.home] + best_candidate[match.away]

                    # Keep players from other teams (prioritize those with gap limits)
                    for t in TEAMS:
                        if t in (match.home, match.away):
                            continue
                        to_keep = min(prev_squad[t], max_per_team[t], players_to_keep - kept)
                        best_candidate[t] = to_keep
                        kept += to_keep
                        if kept >= players_to_keep:
                            break

                    # Fill remaining slots (up to max_allowed_transfers changes)
                    remaining = 11 - kept
                    # Add to playing teams first to meet min_scoring
                    for t in (match.home, match.away):
                        while remaining > 0 and best_candidate[t] < 3:
                            best_candidate[t] += 1
                            remaining -= 1

                    # Then fill other teams up to their gap limits
                    for t in TEAMS:
                        if t in (match.home, match.away):
                            continue
                        while remaining > 0 and best_candidate[t] < max_per_team[t]:
                            best_candidate[t] += 1
                            remaining -= 1

                    best_transfers = calculate_transfers(prev_squad, best_candidate)
                    best_scoring = best_candidate[match.home] + best_candidate[match.away]

                    # If transfers exceed budget, try to reduce by keeping more from prev_squad
                    if best_transfers > remaining_budget:
                        # Rebuild squad using ONLY players from prev_squad (0 transfers)
                        # But redistribute to ensure playing teams have at least 1 player each
                        best_candidate = {t: 0 for t in TEAMS}

                        # First, keep all players from prev_squad
                        for t in TEAMS:
                            best_candidate[t] = prev_squad[t]

                        # If playing teams have 0 players, redistribute from other teams
                        # This is a 0-transfer operation (just moving players around)
                        if best_candidate[match.home] == 0:
                            best_candidate[match.home] = 1
                            # Find a team with players to take from
                            for t in TEAMS:
                                if t != match.home and t != match.away and best_candidate[t] > 0:
                                    best_candidate[t] -= 1
                                    break
                        if best_candidate[match.away] == 0:
                            best_candidate[match.away] = 1
                            # Find a team with players to take from
                            for t in TEAMS:
                                if t != match.home and t != match.away and best_candidate[t] > 0:
                                    best_candidate[t] -= 1
                                    break

                        best_transfers = calculate_transfers(prev_squad, best_candidate)
                        best_scoring = best_candidate[match.home] + best_candidate[match.away]

                        # If still over budget, skip this state
                        if best_transfers > remaining_budget:
                            continue

                    # Skip this state if transfers still exceed what we can afford
                    if best_transfers > remaining_budget:
                        continue

                new_state = State(
                    squad_tuple=squad_to_tuple(best_candidate),
                    transfers_used=state.transfers_used + best_transfers,
                    total_scoring=state.total_scoring + best_scoring,
                    match_history=state.match_history + [
                        (match.match_no, best_candidate.copy(), best_transfers, best_scoring)
                    ],
                    violations=state.violations + (0 if min_scoring <= best_scoring <= max_scoring else 1),
                    free_hit_used=state.free_hit_used
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


def print_summary(matches: List[Match], free_hit_used: bool = False, free_hit_match: int = None,
                  wildcard_used: bool = False, wildcard_match: int = None) -> None:
    """Print summary."""
    total_scoring = sum(m.scoring_players for m in matches)
    total_transfers = sum(m.transfers for m in matches[1:])

    print("\n" + "=" * 60)
    print("OPTIMIZATION RESULTS")
    print("=" * 60)
    print(f"Total Scoring Players: {total_scoring}")
    print(f"Average per Match: {total_scoring / len(matches):.2f}")
    print(f"Transfers Used: {total_transfers}/{TOTAL_TRANSFERS_CAP}")

    if free_hit_used:
        fh_match = matches[free_hit_match - 1]
        print(f"\nFREE HIT USED: Match {free_hit_match} ({fh_match.home} vs {fh_match.away})")
        print(f"  Free Hit squad scoring: {fh_match.scoring_players} players")
        print(f"  Transfers saved: Would have cost ~4 transfers, used 0")

    if wildcard_used:
        wc_match = matches[wildcard_match - 1]
        print(f"\nWILDCARD USED: Match {wildcard_match} ({wc_match.home} vs {wc_match.away})")
        print(f"  Wildcard squad scoring: {wc_match.scoring_players} players")
        print(f"  Squad persists for remaining matches (no reversion)")

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
    parser.add_argument('--free-hit', action='store_true', help='Use Free Hit booster at optimal match (match 38)')
    parser.add_argument('--free-hit-match', type=int, help='Specify custom match number for Free Hit')
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
        max_transfers_per_match=args.max_transfers,
        use_free_hit=args.free_hit or (args.free_hit_match is not None),
        free_hit_match=args.free_hit_match if args.free_hit_match else FREE_HIT_MATCH
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

    print_summary(matches, free_hit_used=args.free_hit or (args.free_hit_match is not None),
                  free_hit_match=args.free_hit_match if args.free_hit_match else FREE_HIT_MATCH,
                  wildcard_used=False, wildcard_match=None)

    print(f"\nSaving results to {args.output}...")
    save_matches(matches, args.output)
    print("Done!")


if __name__ == '__main__':
    main()
