# IPL Transfer Optimizer

A Python program that generates optimal transfer plans across the 70-match IPL league stage using a total budget of 160 transfers.

## Overview

The optimizer uses **beam search with backtracking** to maximize scoring players (players from teams playing in each match) while respecting all constraints:

- **Squad size**: Exactly 11 players per match
- **Max per team**: 7 players per team per match
- **Transfer cap**: 160 total transfers across matches 2-70
- **Scoring bounds**: 3-6 scoring players per match (home + away team players)
- **Max transfers**: 4 per match

## Free Hit Booster

The optimizer supports the **Free Hit** booster, which allows unlimited transfers for one match with no budget restrictions. After the Free Hit match, the squad reverts to the previous lineup.

### Optimal Free Hit Match

The optimizer automatically identifies **Match 38 (LSG vs KKR on 26-Apr-26)** as the optimal Free Hit match based on gap analysis:

| Team | Forward Gap | Backward Gap | Isolation |
|------|-------------|--------------|-----------|
| LSG  | 9 matches   | 6 matches    | 15 days   |
| KKR  | 7 matches   | 10 matches   | 17 days   |

Both teams have maximum isolation, making their players "dead weight" in surrounding matches. Using Free Hit here allows a complete squad overhaul focused purely on this match.

### Free Hit Strategy

- **All 11 players** from the two playing teams (6 home + 5 away)
- **Maximum scoring**: All 11 players score points in the Free Hit match
- **Zero transfer cost**: Free Hit transfers don't count against the 160 budget
- **Automatic reversion**: Squad reverts to pre-Free Hit lineup for the next match

## Wildcard Booster

The Wildcard booster allows unlimited transfers for one match with a persistent squad change.

### Wildcard vs Free Hit

| Aspect | Free Hit | Wildcard |
|--------|----------|----------|
| Transfers | Unlimited | Unlimited |
| Squad after | Reverts to pre-match | Persists |
| Best for | Isolated matches (gap analysis) | Squad reconstruction |
| Default match | 38 (LSG vs KKR) | 14 (Early) or 52 (Late) |

### Wildcard Strategies

**Early Wildcard (Match 14):**
- End of first round-robin
- 56 remaining matches to benefit from new squad
- Recommended: +6 scoring players vs Late strategy

**Late Wildcard (Match 52):**
- Start of final 19 matches
- Playoff push optimization
- Note: Match 56+ fails due to transfer budget exhaustion

### Usage

```bash
# Early Wildcard (default match 14)
python3 ipl_optimizer.py --wildcard --output ipl26_wildcard_early.csv

# Late Wildcard (custom match)
python3 ipl_optimizer.py --wildcard --wildcard-match 52 --output ipl26_wildcard_late.csv

# Custom Wildcard match
python3 ipl_optimizer.py --wildcard --wildcard-match 25 --output ipl26_custom.csv
```

### Results Comparison

| Strategy | Total Scoring | Avg/Match | Transfers |
|----------|---------------|-----------|-----------|
| Standard | TBD | TBD | TBD |
| Early Wildcard (14) | 289 | 4.13 | 160 |
| Late Wildcard (52) | 283 | 4.04 | 158 |

## Installation

No dependencies required - uses Python 3 standard library only.

```bash
# Navigate to the transfer_optimizer directory
cd transfer_optimizer
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

# Use Free Hit booster at optimal match (Match 38)
python3 ipl_optimizer.py --free-hit

# Custom Free Hit match number
python3 ipl_optimizer.py --free-hit-match 45

# All options
python3 ipl_optimizer.py --min-scoring 3 --max-scoring 6 \
                         --max-transfers 4 \
                         --free-hit \
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
| `--free-hit` | - | Use Free Hit booster at optimal match (38) |
| `--free-hit-match` | - | Specify custom match number for Free Hit |

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

### Standard Optimization (No Free Hit)

| Metric | Value | Target |
|--------|-------|--------|
| Total Scoring Players | **283** | 280+ |
| Average per Match | **4.04** | ≥ 4.0 |
| Transfers Used | **160/160** | 160 |
| Min-Scoring Violations | **0** | 0 |
| Max Players per Team | **7** | ≤ 7 |
| Max Transfers per Match | **4** | ≤ 4 |
| Both Teams with Players | **All 70** | ≥ 1 each |

### Free Hit Optimization (Match 38)

| Metric | Value | Improvement |
|--------|-------|-------------|
| Total Scoring Players | **295** | +12 (+4.2%) |
| Average per Match | **4.21** | +0.17 |
| Match 38 Scoring | **11 players** | All squad scores |
| Match 38 Transfers | **0** | ~4 saved |

### Transfer Distribution (Standard)

| Segment | Transfers | Avg/Match |
|---------|-----------|-----------|
| Matches 1-10 | 31 | 3.1 |
| Matches 11-20 | 20 | 2.0 |
| Matches 21-30 | 21 | 2.1 |
| Matches 31-40 | 21 | 2.1 |
| Matches 41-50 | 20 | 2.0 |
| Matches 51-60 | 18 | 1.8 |
| Matches 61-70 | 15 | 1.5 |

## Running Tests

```bash
python3 test_optimizer.py
```

The test suite validates (22 tests total):
- Gap computation (forward scan, match numbers not days)
- Squad constraints (11 players, max 7 per team, both playing teams ≥ 1 player)
- Transfer constraints (160 cap, Match 1 = 0, max 4 per match, correct calculation)
- Scoring players (formula, min/max bounds)
- Output format (all columns, 70 matches)
- Optimization quality (total scoring, transfer efficiency)
- Free Hit functionality (booster generates 0 transfers at specified match)

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
transfer_optimizer/
├── README.md                          # This file
├── ipl_optimizer.py                   # Main optimizer script
├── test_optimizer.py                  # Test suite
├── ipl26.csv                          # Input file (match schedule)
└── ipl26_computed.csv                 # Output file (computed)
```
