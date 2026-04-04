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

### Free Hit Match Details

| Parameter | Value |
|-----------|-------|
| **Match Number** | **38** |
| **Date** | 26-Apr-26 |
| **Teams** | LSG vs KKR |
| **Stadium** | Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium |
| **City** | Lucknow |
| **Strategy** | Maximum team isolation |

### Optimal Free Hit Match Analysis

Both teams have maximum isolation, making their players "dead weight" in surrounding matches. Using Free Hit here allows a complete squad overhaul focused purely on this match.

| Team | Forward Gap | Backward Gap | Isolation |
|------|-------------|--------------|-----------|
| LSG  | 9 matches   | 6 matches    | 15 days   |
| KKR  | 7 matches   | 10 matches   | 17 days   |

## Wildcard Booster

The Wildcard booster allows unlimited transfers for one match with a persistent squad change (doesn't revert).

### Wildcard vs Free Hit

| Aspect | Free Hit | Wildcard |
|--------|----------|----------|
| Transfers | Unlimited | Unlimited |
| Squad after | Reverts to pre-match | **Persists** |
| Best for | Isolated matches (gap analysis) | Squad reconstruction |
| Default match | 38 (LSG vs KKR) | **14 (Early)** or 52 (Late) |

### Wildcard Match Details

| Parameter | Early Wildcard | Late Wildcard |
|-----------|----------------|---------------|
| **Match Number** | **14** | **52** |
| **Date** | 08-Apr-26 | 02-May-26 |
| **Teams** | DC vs GT | PBKS vs RR |
| **Strategy** | Full squad reset | Playoff push |

### Wildcard Strategies

### Wildcard Strategies

**Early Wildcard (Match 14):**
- End of first round-robin
- 56 remaining matches to benefit from new squad
- Recommended: +6 scoring players vs Late strategy
- Smart accumulation: Automatically accumulates players from teams playing before Wildcard (e.g., RR, MI before Match 14)

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
| Standard | 283 | 4.04 | 160 |
| Early Wildcard (14) | 291 | 4.16 | 160 |
| Late Wildcard (52) | 283 | 4.04 | 158 |

### Booster Match Numbers

| Booster | Match Number | Match Details | Date |
|---------|--------------|---------------|------|
| Wildcard | **14** | DC vs GT | 08-Apr-26 |
| Free Hit | **38** | LSG vs KKR | 26-Apr-26 |

### Booster Strategy Summary

| Booster | Best Match | Why |
|---------|------------|-----|
| **Wildcard** | 14 | End of round-robin, full squad reset |
| **Free Hit** | 38 | Maximum team isolation (15+ day gaps) |

### Using Both Boosters Together

For maximum scoring, use both Wildcard and Free Hit in the same season:

```bash
# Both boosters: Wildcard at Match 14 + Free Hit at Match 38
python3 ipl_optimizer.py --wildcard --free-hit
```

**Results with Both Boosters:**

| Metric | Value | Improvement vs Standard |
|--------|-------|------------------------|
| Total Scoring Players | **304** | +21 (+7.4%) |
| Average per Match | **4.34** | +0.30 |
| Transfers Used | 160/160 | 160 |
| Min-Scoring Violations | 0 | 0 |

**Booster Match Details:**
| Booster | Match | Teams | Scoring | Strategy |
|---------|-------|-------|---------|----------|
| Wildcard | 14 | DC vs GT | 11 players | Accumulate RR, MI players first; reset squad |
| Free Hit | 38 | LSG vs KKR | 11 players | Maximum isolation (gap=15+ days) |

**Strategy:**
1. **Wildcard (Match 14)**: Accumulate players from teams playing before Match 14 (RR, MI), then reset to DC+GT squad
2. **Free Hit (Match 38)**: Full squad overhaul for isolated LSG vs KKR match
3. **Combined benefit**: +21 scoring players over the season

## Final Match Boost

The **Final Match Boost** applies dead-weight discarding logic for matches 68-70, similar to the Wildcard strategy.

### How It Works

Teams that won't play in the final stretch are minimized to free up slots for teams that will play:

| Team | Last Match Before 68-70 | Gap |
|------|------------------------|-----|
| DC   | Match 62               | 8 matches (biggest dead weight) |
| GT   | Match 66               | 4 matches |
| Others | Varies | 1-5 matches |

**DC is the biggest dead weight** - last plays Match 62, then doesn't play again until Match 70 (gap=8).

### Usage

```bash
# Final Match Boost only
python3 ipl_optimizer.py --final-boost

# Combined with other boosters
python3 ipl_optimizer.py --wildcard --free-hit --final-boost
```

### Results

| Strategy | Total Scoring | Avg/Match | Transfers |
|----------|---------------|-----------|-----------|
| Standard | 283 | 4.04 | 160 |
| Final Boost only | 283 | 4.04 | 160 |
| Wildcard + Free Hit | **304** | **4.34** | 160 |
| All 3 Boosters | 303 | 4.33 | 160 |

**Note:** Final Match Boost provides the most benefit when transfer budget is tight. With Wildcard+Free Hit already using the full 160 transfers optimally, the additional boost has minimal impact.

## Installation

No dependencies required - uses Python 3 standard library only.

```bash
# Navigate to the transfer_optimizer directory
cd transfer_optimizer
```

## Usage

### Basic Run (API-First)

```bash
python3 ipl_optimizer.py
```

This fetches match data from the tour-fixtures API and generates `ipl26_computed.csv`. CSV input is used only as a fallback when the API is unavailable.

### Basic Run (CSV Fallback)

```bash
python3 ipl_optimizer.py --input ipl26.csv
```

This reads matches from `ipl26.csv` (fallback when API fails).

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
| `--input` | *empty* (API) | Input CSV file (empty = fetch from API) |
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

### Booster Match Summary

| Booster | Match | Date | Teams | Venue | Scoring |
|---------|-------|------|-------|-------|---------|
| **Wildcard** | **14** | 08-Apr-26 | DC vs GT | Delhi | 11 players |
| **Free Hit** | **38** | 26-Apr-26 | LSG vs KKR | Lucknow | 11 players |

### Strategy Comparison

| Strategy | Total Scoring | Avg/Match | Transfers | Boosters Used |
|----------|---------------|-----------|-----------|---------------|
| Standard | 283 | 4.04 | 160 | None |
| Wildcard (14) | 291 | 4.16 | 160 | Wildcard |
| Free Hit (38) | 295 | 4.21 | 160 | Free Hit |
| Wildcard + Free Hit | **304** | **4.34** | 160 | Both |
| All 3 Boosters | 303 | 4.33 | 160 | Both + Final |

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

### Final Match Boost Results

| Strategy | Total Scoring | Avg/Match | Notes |
|----------|---------------|-----------|-------|
| Standard | 283 | 4.04 | Baseline |
| Final Boost only | 283 | 4.04 | Minimal impact with 160 transfers |
| All 3 Boosters | 303 | 4.33 | Wildcard+Free Hit already optimal |

**Note:** Final Match Boost provides the most benefit when transfer budget is tight. With Wildcard+Free Hit already using the full 160 transfers optimally, the additional boost has minimal impact.

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
