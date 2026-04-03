#!/usr/bin/env python3
"""
Analyze optimal Free Hit match based on team gaps.

Free Hit is most valuable when:
- Both teams in the match have large gaps (no recent/upcoming games)
- This means players from these teams are "dead weight" in your squad
- Free Hit lets you completely overhaul for one match without transfer cost
"""

import csv
from typing import List, Dict, Optional, Tuple

TEAMS = ["CSK", "DC", "GT", "KKR", "LSG", "MI", "PBKS", "RCB", "RR", "SRH"]


class Match:
    def __init__(self, match_no: int, date: str, home: str, away: str):
        self.match_no = match_no
        self.date = date
        self.home = home
        self.away = away
        self.team1_gap: Optional[int] = None
        self.team2_gap: Optional[int] = None


def load_matches(filepath: str) -> List[Match]:
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


def compute_backward_gap(team_matches: List[int], current_match: int) -> Optional[int]:
    """Find the gap since a team last played."""
    for match_no in reversed(team_matches):
        if match_no < current_match:
            return current_match - match_no
    return None


def analyze_free_hit_opportunities(matches: List[Match]) -> None:
    """Analyze each match for Free Hit potential."""

    # Pre-compute all team match schedules
    team_matches = {team: [] for team in TEAMS}
    for match in matches:
        team_matches[match.home].append(match.match_no)
        team_matches[match.away].append(match.match_no)

    for team in team_matches:
        team_matches[team].sort()

    print("=" * 80)
    print("FREE HIT ANALYSIS - OPTIMAL MATCH SELECTION")
    print("=" * 80)
    print("\nFree Hit is valuable when BOTH teams have:")
    print("  - Large FORWARD gap (won't play for many matches)")
    print("  - Large BACKWARD gap (haven't played recently)")
    print("  => Players from these teams are 'dead weight' in your squad\n")

    # Score each match
    match_scores = []

    for match in matches:
        # Forward gaps (already computed)
        home_forward_gap = match.team1_gap
        away_forward_gap = match.team2_gap

        # Backward gaps
        home_backward_gap = compute_backward_gap(team_matches[match.home], match.match_no)
        away_backward_gap = compute_backward_gap(team_matches[match.away], match.match_no)

        # Combined gap score (higher = better Free Hit candidate)
        # Use minimum of forward/backward for each team (the "isolation" factor)
        home_isolation = min(
            home_forward_gap if home_forward_gap else 0,
            home_backward_gap if home_backward_gap else 0
        )
        away_isolation = min(
            away_forward_gap if away_forward_gap else 0,
            away_backward_gap if away_backward_gap else 0
        )

        # Combined score
        combined_isolation = home_isolation + away_isolation

        # Also track the minimum gap (we want BOTH teams to have high gaps)
        min_gap = min(
            home_forward_gap if home_forward_gap else 999,
            away_forward_gap if away_forward_gap else 999
        )

        match_scores.append({
            'match': match,
            'home_forward': home_forward_gap,
            'away_forward': away_forward_gap,
            'home_backward': home_backward_gap,
            'away_backward': away_backward_gap,
            'home_isolation': home_isolation,
            'away_isolation': away_isolation,
            'combined_isolation': combined_isolation,
            'min_forward_gap': min_gap
        })

    # Sort by combined isolation score
    match_scores.sort(key=lambda x: x['combined_isolation'], reverse=True)

    print("\n" + "=" * 80)
    print("TOP 10 FREE HIT CANDIDATES (ranked by team isolation)")
    print("=" * 80)

    for i, ms in enumerate(match_scores[:10], 1):
        m = ms['match']
        print(f"\n{i}. Match {m.match_no}: {m.home} vs {m.away} ({m.date})")
        print(f"   {m.home}: forward gap={ms['home_forward']}, backward gap={ms['home_backward']}")
        print(f"   {m.away}: forward gap={ms['away_forward']}, backward gap={ms['away_backward']}")
        print(f"   Combined isolation score: {ms['combined_isolation']}")
        print(f"   Min forward gap: {ms['min_forward_gap']}")

    # Find matches where BOTH teams have forward gap >= 5
    print("\n" + "=" * 80)
    print("MATCHES WHERE BOTH TEAMS HAVE FORWARD GAP >= 5")
    print("=" * 80)

    high_gap_matches = [ms for ms in match_scores if ms['min_forward_gap'] >= 5]

    if high_gap_matches:
        for ms in high_gap_matches:
            m = ms['match']
            print(f"  Match {m.match_no}: {m.home} (gap={ms['home_forward']}) vs {m.away} (gap={ms['away_forward']})")
    else:
        print("  No matches found where both teams have gap >= 5")

    # Find matches where BOTH teams have forward gap >= 4
    print("\n" + "=" * 80)
    print("MATCHES WHERE BOTH TEAMS HAVE FORWARD GAP >= 4")
    print("=" * 80)

    med_gap_matches = [ms for ms in match_scores if ms['min_forward_gap'] >= 4]

    if med_gap_matches:
        for ms in med_gap_matches:
            m = ms['match']
            print(f"  Match {m.match_no}: {m.home} (gap={ms['home_forward']}) vs {m.away} (gap={ms['away_forward']})")
    else:
        print("  No matches found where both teams have gap >= 4")

    # Summary statistics
    print("\n" + "=" * 80)
    print("GAP DISTRIBUTION SUMMARY")
    print("=" * 80)

    gap_counts = {i: 0 for i in range(1, 11)}
    for ms in match_scores:
        gap = ms['min_forward_gap']
        if gap and gap <= 10:
            gap_counts[gap] += 1

    for gap in range(1, 11):
        count = gap_counts[gap]
        if count > 0:
            print(f"  Matches with min gap >= {gap}: {count}")


if __name__ == '__main__':
    print("Loading matches...")
    matches = load_matches('ipl26.csv')
    print(f"Loaded {len(matches)} matches")

    print("Computing gaps...")
    compute_gaps(matches)

    analyze_free_hit_opportunities(matches)
