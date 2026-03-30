# IPL Fantasy League Transfer Optimizer

A Python program that generates optimal transfer plans across the 70-match IPL league stage using a total budget of 160 transfers.

## Overview

The optimizer uses **beam search with backtracking** to maximize scoring players (players from teams playing in each match) while respecting all constraints:

- **Squad size**: Exactly 11 players per match
- **Max per team**: 7 players per team per match
- **Transfer cap**: 160 total transfers across matches 2-70
- **Scoring bounds**: 3-6 scoring players per match (home + away team players)

## Installation

No dependencies required - uses Python 3 standard library only.

```bash
# Clone or navigate to the project directory
cd /path/to/ipl
```

## Usage

### Basic Run

```bash
python3 ipl_optimizer.py
```

This reads `ipl26.csv` and generates `ipl26_computed.csv` with all columns populated.

### Command Line Options

```bash
# Only compute gaps (updates input file directly)
python3 ipl_optimizer.py --populate-gap

# Custom scoring bounds
python3 ipl_optimizer.py --min-scoring 2 --max-scoring 5

# Custom transfer limits
python3 ipl_optimizer.py --max-transfers 5

# All options
python3 ipl_optimizer.py --min-scoring 3 --max-scoring 6 \
                         --max-transfers 4 \
                         --input ipl26.csv \
                         --output ipl26_computed.csv
```

### Options Summary

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | `ipl26.csv` | Input CSV file |
| `--output` | `ipl26_computed.csv` | Output CSV file |
| `--min-scoring` | `3` | Minimum scoring players per match |
| `--max-scoring` | `6` | Maximum scoring players per match |
| `--max-transfers` | `4` | Maximum transfers per match |
| `--populate-gap` | - | Only compute gaps, skip optimization |

## Input Format

**File:** `ipl26.csv`

| Column | Name | Description |
|--------|------|-------------|
| 1 | Match No | Sequential match number (1-70) |
| 2 | Date | Match date |
| 3 | Home | Home team |
| 4 | Away | Away team |
| 5-19 | (computed) | Gap columns, team player counts, Total, Transfers, Scoring Players |

## Output Format

**File:** `ipl26_computed.csv`

| Column | Name | Description |
|--------|------|-------------|
| 5-6 | Team-1 Gap, Team-2 Gap | Matches until each team's next match |
| 7-16 | Team columns | Player count from each team in squad |
| 17 | Total | Sum of team columns (always = 11) |
| 18 | Transfers | Players added vs previous match |
| 19 | Scoring Players | Sum of home + away team players in squad |

## Algorithm

### Beam Search Optimization

1. **Initialize** beam with Match 1 squad
2. **For each match** (2-70):
   - Generate all valid candidate squads
   - Calculate transfers needed from each previous state
   - Create new states with updated scoring and transfer counts
   - Sort by: violations → budget adherence → scoring
   - Keep top 100 states (beam width)
3. **Select best** final state (0 violations, highest scoring)

### Gap Computation

Gaps are computed by forward scanning the schedule:
- **Gap = Next match number - Current match number**
- Measured in match numbers, not calendar days
- Empty string if team has no further league matches

## Results

The optimizer achieves:

| Metric | Value | Target |
|--------|-------|--------|
| Total Scoring Players | **301** | 280+ |
| Average per Match | **4.30** | > 4.0 |
| Transfers Used | **160/160** | 160 |
| Min-Scoring Violations | **0** | 0 |
| Max Players per Team | **7** | ≤ 7 |

### Transfer Distribution

| Segment | Transfers | Avg/Match |
|---------|-----------|-----------|
| Matches 1-10 | 34 | 3.4 |
| Matches 11-20 | 21 | 2.1 |
| Matches 21-30 | 22 | 2.2 |
| Matches 31-40 | 20 | 2.0 |
| Matches 41-50 | 19 | 1.9 |
| Matches 51-60 | 21 | 2.1 |
| Matches 61-70 | 9 | 0.9 |

## Running Tests

```bash
python3 test_optimizer.py
```

The test suite validates:
- Gap computation (forward scan, match numbers not days)
- Squad constraints (11 players, max 7 per team)
- Transfer constraints (160 cap, Match 1 = 0)
- Scoring players (formula, min/max bounds)
- Output format (all columns, 70 matches)
- Optimization quality (total scoring, transfer efficiency)

## Progress Output

The optimizer prints progress every 5 matches:

```
Loading matches from ipl26.csv...
Loaded 70 matches
Computing gaps...
Running beam search optimization...
  Match 5/70: Total scoring=27 (avg=5.4), Total transfers=16 (avg=3.2),
              Last 5: avg_t=3.2, avg_s=5.4, Beam=63
  Match 10/70: Total scoring=54 (avg=5.4), Total transfers=35 (avg=3.5),
               Last 5: avg_t=3.8, avg_s=5.4, Beam=100
  ...
  Match 70/70: Total scoring=301 (avg=4.3), Total transfers=160 (avg=2.3),
               Last 5: avg_t=0.0, avg_s=6.0, Beam=2

Validation passed!
```

## Project Structure

```
ipl/
├── README.md                          # This file
├── specs.md                           # Design specification
├── ipl_optimizer.py                   # Main optimizer script
├── test_optimizer.py                  # Test suite
├── ipl26.csv                          # Input file (match schedule)
├── ipl26_computed.csv                 # Output file (computed)
└── docs/
    └── plans/
        └── 2026-03-30-ipl-transfer-optimizer-design.md
```

## License

MIT License
