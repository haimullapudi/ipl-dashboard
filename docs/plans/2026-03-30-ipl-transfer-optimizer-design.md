# IPL Fantasy League Transfer Optimizer - Design Document

## Overview

A Python program that generates optimal transfer plans across the 70-match IPL league stage using a budget of 160 transfers. The optimizer uses beam search with backtracking to maximize scoring players while respecting all constraints.

## Input/Output

### Input: `src/transfer_optimizer/ipl26.csv`
- 70 matches with columns: Match No, Date, Home, Away, Gap columns (5-6), Team columns (7-16), Total, Transfers, Scoring Players
- Initial squad data may be present for Match 1

### Output: `src/transfer_optimizer/ipl26_computed.csv`
- Same structure with columns 5-19 fully populated:
  - Columns 5-6: Team-1 Gap, Team-2 Gap (matches until next game)
  - Columns 7-16: Player count per team
  - Column 17: Total (always 11)
  - Column 18: Transfers (vs previous match)
  - Column 19: Scoring Players (home + away team players)

## Architecture

### Components

1. **GapComputer** - Computes gaps via forward scan
2. **SquadAllocator** - Generates valid squad candidates
3. **TransferCalculator** - Computes transfers between squads
4. **BeamSearchOptimizer** - Main optimization loop
5. **CSVHandler** - Input/output handling

### Data Structures

```python
TEAMS = ["CSK", "DC", "GT", "KKR", "LSG", "MI", "PK", "RCB", "RR", "SRH"]

Match = {
    "match_no": int,
    "date": str,
    "home": str,
    "away": str,
    "team1_gap": Optional[int],
    "team2_gap": Optional[int],
    "squad": Dict[str, int],
    "transfers": int,
    "scoring_players": int
}

State = {
    "squad_tuple": Tuple[Tuple[str, int], ...],  # For hashing
    "transfers_used": int,
    "total_scoring": int,
    "match_history": List[Tuple[int, Dict, int, int]],
    "violations": int
}
```

## Algorithm

### Gap Computation
For each match, scan forward to find next occurrence of each team:
- Gap = next_match_number - current_match_number
- Empty string if no further matches

### Beam Search Optimization

1. Initialize beam with Match 1 state
2. For each match 2-70:
   - Generate all valid squad candidates
   - Calculate transfers from each previous state
   - Create new states with updated metrics
   - Sort by: violations (asc) → budget adherence (asc) → scoring (desc)
   - Keep top 100 states (beam width)
3. Select best final state (0 violations, highest scoring)

### Candidate Generation Constraints

- Squad size = 11
- Max 7 players per team
- Min 3, Max 6 scoring players (home + away)
- Max 4 transfers per match
- Stay within remaining budget

### Transfer Calculation

- Match 1: Transfers = 0 (initial build)
- Matches 2-70: Transfers = 11 - carried_over
- Carry over by matching team counts from previous squad

## CLI Interface

```bash
# Default run
python3 ipl_optimizer.py

# Gap computation only (updates input file)
python3 ipl_optimizer.py --populate-gap

# Custom constraints
python3 ipl_optimizer.py --min-scoring 2 --max-scoring 5
python3 ipl_optimizer.py --max-transfers 5
```

## Success Metrics

| Metric | Target |
|--------|--------|
| Total Scoring Players | Maximize (target: 280+) |
| Average per Match | > 4.0 |
| Transfers Used | 160/160 |
| Min-Scoring Violations | 0 |
| Max Players per Team | ≤ 7 |

## Files

| File | Purpose |
|------|---------|
| `ipl_optimizer.py` | Main optimizer |
| `test_optimizer.py` | Test suite |
| `src/transfer_optimizer/ipl26.csv` | Input |
| `src/transfer_optimizer/ipl26_computed.csv` | Output |
