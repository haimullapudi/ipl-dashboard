# IPL Fantasy League Transfer Optimizer - Design Document

## Overview

Create a Python program that generates the optimal transfer plan across the 70-match league stage of the IPL Fantasy League using a total budget of 160 transfers. the initial team setup is available for match-1. Gap Computation is a one time activity, so accept an input flag to populate the gap. when this input flag is passed only update the input file directly (ie. ipl26.csv). Use backtracking and show progress

## Input

**File:** `ipl26.csv`

| Column | Name | Description |
|--------|------|-------------|
| 1 | Match No | Sequential match number (1-70) |
| 2 | Date | Match date |
| 3 | Home | Home team |
| 4 | Away | Away team |
| 5-19 | (computed) | Gap columns, team player counts, Total, Transfers, Scoring Players |

## Output

**File:** `ipl26_computed.csv` - The original schedule with columns 5-19 fully populated.

| Column | Name | Description |
|--------|------|-------------|
| 5-6 | Team-1 Gap, Team-2 Gap | Days until each team's next match |
| 7-16 | Team columns | Player count from each team in squad |
| 17 | Total | Sum of team columns (always = 11) |
| 18 | Transfers | Players added vs previous match squad |
| 19 | Scoring Players | Sum of home + away team players in squad |

## Algorithm Design

### 1. Gap Computation (Columns 5-6)

For each match, compute `Team-1 Gap` and `Team-2 Gap`:
- Scan forward in the schedule to find the next match where the same team appears (either as Home or Away)
- **Gap = (Match number of next match) - (Current match number)**
- Gap is measured in **match numbers**, not calendar days
- This is important because some days have multiple matches (e.g., Match 7 and 8 are both on "Sat, 04-Apr")
- Empty string `""` if the team has no further league-stage matches

**Example:**
- Match 2: MI vs KKR → MI gap = 6 (MI plays again at Match 7), KKR gap = 4 (KKR plays again at Match 5)
- Match 7 & 8: Both on same date "Sat, 04-Apr" but gaps are 6 and 5 respectively based on match numbers

### 2. Squad Allocation (Columns 7-16)

**Constraints:**
- Squad size: Exactly 11 players per match
- Maximum: 7 players per team per match

**Allocation Strategy:**
1. **Priority 1:** Players from the two teams playing in the current match (Home + Away)
   - Allocate up to 7 players per playing team
   - Fill to 11 total, balancing between the two teams
2. **Priority 2:** If slots remain after maxing playing teams, fill from non-playing teams
   - Prioritize teams with shortest gap to their next match
   - This maximizes future coverage potential

**Initial Squad (Match 1):**
- Build 11-player squad from the two playing teams
- Transfers for Match 1 do NOT count toward the 160 cap

### 3. Transfer Calculation (Column 18)

**For Match 1:**
- Transfers = 0 (initial squad build, does not count toward cap)

**For Matches 2-70:**
- Carry over as many players as possible from previous match
- Match players by team (e.g., if previous match had RCB=5 and current has RCB=3, carry over 3)
- Transfers = New players added (not carried over)
- Example: Previous RCB=5, SRH=6 → Current RCB=3, SRH=4, MI=3
  - Carried over: 3 (RCB) + 4 (SRH) = 7
  - Transfers: 11 - 7 = 4 (the 3 MI + 1 new RCB/SRH if any)

**Transfer Cap Enforcement:**
- Global cap: 160 total transfers across matches 2-70
- If approaching cap, freeze non-playing team slots and only swap playing-team players

### 4. Optimization Strategy - Beam Search with Backtracking

**Primary Objective: Maximize Scoring Players**

The "Scoring Players" column (column 19) represents the sum of players from the two teams playing in each match (Home + Away). This is the key metric to maximize across all 70 matches.

**Scoring Players Definition:**
```
Scoring Players = squad[home_team] + squad[away_team]
```

**Why Maximize Scoring Players:**
- In IPL Fantasy League, only players from teams that are playing can score points
- A squad with 3 home + 3 away players has 6 scoring players (maximum possible)
- A squad with 1 home + 1 away players has only 2 scoring players (9 players get 0 points)
- Higher scoring players = more potential points per match

**Beam Search Algorithm:**

The optimizer uses beam search with backtracking to explore multiple squad allocation possibilities at each match:

1. **State Representation:**
```python
state = (
    squad_tuple,      # Tuple of (team, count) pairs for hashing
    transfers_used,   # Cumulative transfers used so far
    total_scoring,    # Sum of scoring players across all matches
    match_history,    # List of (match_idx, squad, transfers, scoring) tuples
    violations        # Count of min-scoring violations
)
```

2. **Beam Width:** 100 states kept at each match

3. **Candidate Generation:** For each state, generate all valid squad candidates that:
   - Meet min_scoring constraint (>= 3 scoring players)
   - Don't exceed max_scoring constraint (<= 6 scoring players)
   - Stay within transfer budget
   - Don't exceed max_transfers per match

4. **State Pruning:** After each match, sort states by:
   - Violations (ascending) - prioritize 0 violations
   - Budget adherence (ascending) - penalize states spending too fast
   - Total scoring (descending) - maximize scoring
   Keep only top 100 states

5. **Budget Management:**
   - Target: ~2.35 transfers per match (160 / 68 matches)
   - Reserve budget for remaining matches to ensure min_scoring can be met
   - Early matches constrained to stay on budget track

**Transfer Budget Strategy:**
- Use all 160 transfers across 70 matches (no benefit to saving)
- Target rate: ~2.35 transfers per match (160 / 68 matches)
- Balance transfer usage to maintain scoring potential throughout the season
- Budget-aware sorting prevents aggressive early spending

**Fixture-Density Weighting:**
- Teams with shorter gaps play more frequently
- Prioritize retaining players from teams with shorter upcoming gaps
- This maximizes the likelihood that squad players will be in upcoming matches

**Carry-Over Strategy:**
- Maximize players retained from previous match to minimize transfers
- When selecting which players to drop, drop from teams with longest gaps first
- Only use carry-forward if it meets min_scoring OR budget exhausted

## Data Structures

```python
# Team names (fixed order for columns)
TEAMS = ["CSK", "DC", "GT", "KKR", "LSG", "MI", "PBKS", "RCB", "RR", "SRH"]

# Match data structure
match = {
    "match_no": int,       # Sequential match number (1-70)
    "date": str,           # Match date string
    "date_obj": datetime,  # Parsed date (used for sorting, not gap calculation)
    "home": str,           # Home team
    "away": str,           # Away team
    "team1_gap": Optional[int],  # Matches until home team plays again (not days!)
    "team2_gap": Optional[int],  # Matches until away team plays again (not days!)
    "squad": {team: count for team in TEAMS},  # sum = 11
    "transfers": int,      # Transfers for this match
    "scoring_players": int # squad[home] + squad[away]
}

# Beam search state
state = (
    squad_tuple,      # Tuple of (team, count) pairs for hashing
    transfers_used,   # Cumulative transfers used so far
    total_scoring,    # Sum of scoring players across all matches
    match_history,    # List of (match_idx, squad, transfers, scoring) tuples
    violations        # Count of min-scoring violations
)

# Beam width: 100 states kept at each match
BEAM_WIDTH = 100
```

## Implementation Steps

1. **Parse input CSV** - Load all 70 matches with squad data
2. **Parse dates and build match schedule** - Convert date strings to datetime objects
3. **Compute gaps (forward scan)** - For each match, find days until each team plays again
4. **Initialize first match squad** - Use existing squad from input or build initial 11-player squad
5. **Beam Search Optimization:**
   - Initialize beam with match 1 state, if provided.
   - For each subsequent match (2-70):
     - Generate all valid candidate squads meeting constraints
     - Calculate transfers needed from each previous state
     - Create new states with updated scoring and transfer counts
     - Sort states by: violations → budget adherence → scoring
     - Keep top 100 states (beam width)
     - Print progress every 10 matches
   - Select best final state (0 violations, highest scoring)
6. **Write output CSV** - All columns populated with gaps, squads, transfers, scoring

## Validation Rules

- Total column (17) must equal 11 for every match
- No team can exceed 7 players in any match
- Sum of Transfers column (matches 2-70) must be ≤ 160
- Team player counts must be non-negative integers
- Scoring Players column (19) = Home team count + Away team count for each match

## Success Metrics

- **Total Scoring Players:** Sum of column 19 across all 70 matches (target: maximize)
- **Average Scoring Players per Match:** Total / 70 (target: > 4.0, or > 3.8 with 6-player cap)
- **Transfer Efficiency:** All 160 transfers used (no leftover budget)
- **Min-Scoring Compliance:** Zero matches with scoring < 3 (hard constraint)

## Achieved Results

The beam search optimizer achieves:

| Metric | Value | Target |
|--------|-------|--------|
| Total Scoring Players | **280** | Maximize |
| Average per Match | **4.06** | > 4.0 |
| Transfers Used | **160/160** | 160 |
| Min-Scoring Violations | **0** | 0 |
| Max Players per Team | **7** | ≤ 7 |

### Transfer Distribution (Balanced)

| Segment | Transfers | Avg/Match |
|---------|-----------|-----------|
| Matches 1-10 | 32 | 3.2 |
| Matches 11-20 | 25 | 2.5 |
| Matches 21-30 | 22 | 2.2 |
| Matches 31-40 | 24 | 2.4 |
| Matches 41-50 | 23 | 2.3 |
| Matches 51-60 | 23 | 2.3 |
| Matches 61-70 | 22 | 2.4 |

## Implementation Notes

### Initial Squad (Match 1)
- If the initial squad for Match 1 is provided in the input file (`ipl26.csv`)
- Do NOT regenerate - use the existing squad data from columns 7-16
- Transfers for Match 1 still do NOT count toward the 160 cap

### Scoring Players Bounds
- **MAX_SCORING_PLAYERS** (default: 6, configurable via `--max-scoring`)
  - Limits home + away players per match
  - Purpose: Ensure consistent scoring coverage throughout the season
  - Prevents over-investment in single matches at the expense of others
  - **Hard constraint** - never exceeded
- **MIN_SCORING_PLAYERS** (default: 3, configurable via `--min-scoring`)
  - Ensures minimum players from playing teams in every match
  - Guarantees baseline scoring potential for each match
  - **Hard constraint** - enforced in candidate generation
- Expected average with bounds: ~3.8-4.5 scoring players per match

### Transfer Limits
- **MAX_TRANSFERS_PER_MATCH** (default: 4, configurable via `--max-transfers`)
  - Limits transfers in any single match
  - Prevents aggressive early spending that leaves later matches starved
  - **Hard constraint** - never exceeded
- **MIN_TRANSFERS_PER_MATCH** (default: 0, configurable via `--min-transfers`)
  - Minimum transfers per match (useful for enforcing active management)
  - **Hard constraint** - candidates below this are filtered
- **Budget Management:**
  - Target: ~2.35 transfers per match (160 / 68 matches)
  - Beam search sorts states by budget adherence to prevent overspending early
  - Reserve budget for remaining matches to ensure min_scoring can always be met

### CLI Options
```bash
# Default run (max 4 transfers, 3-6 scoring)
python3 ipl_optimizer.py

# Custom transfer limits (max 5 transfers per match)
python3 ipl_optimizer.py --max-transfers 5

# Custom scoring bounds
python3 ipl_optimizer.py --min-scoring 2 --max-scoring 5

# All options
python3 ipl_optimizer.py --min-scoring 3 --max-scoring 6 --min-transfers 0 --max-transfers 4

# Gap computation only (updates input file)
python3 ipl_optimizer.py --populate-gap
```

### Output Format - Empty Cells
- Team columns (7-16) should show empty string `""` for teams with 0 players
- Do NOT write `0` - leave the cell empty
- This improves readability of the output CSV

### Progress Reporting
The optimizer prints progress every 10 matches:
```
Running beam search optimization...
  Match 10/70: Best scoring=43, Transfers used=21, Violations=0, Beam size=100
  Match 20/70: Best scoring=82, Transfers used=46, Violations=0, Beam size=100
  ...
```

## Error Handling

- Validate input CSV has all 70 matches
- Validate team names match expected values
- Handle date parsing for gap calculation
- Report if transfer cap would be exceeded
- Handle UTF-8 BOM in input CSV (encoding='utf-8-sig')
- Fallback to greedy optimization if beam search fails (should not happen with proper constraints)

## Files

| File | Description |
|------|-------------|
| `ipl_optimizer.py` | Main optimizer script with beam search algorithm |
| `test_optimizer.py` | Test suite with validation rules |
| `ipl26.csv` | Input file (match schedule + initial squad) |
| `ipl26_computed.csv` | Output file (fully populated) |
| `fetch_players.py` | IPL Fantasy API fetcher and dashboard generator |
| `players.html` | Generated static dashboard |
| `players_data.json` | Raw API data backup |
| `docs/plans/2026-03-29-ipl-transfer-optimizer.md` | Implementation plan |
| `specs.md` | This design document |

## IPL Fantasy Players Dashboard

A static webpage that displays IPL Fantasy players data from the official API.

### Data Source

API Endpoint: `https://fantasy.iplt20.com/classic/api/feed/gamedayplayers?lang=en&tourgamedayId=4`

### Key Fields

| Field | Description |
|-------|-------------|
| IsAnnounced | 'P' = Playing, 'NP' = Not Playing, 'S' = Substitute, '' = Not announced |
| IS_FP | '1' = In final playing XI, '0' = Not in playing XI |
| SelectedPer | Percentage of users who selected the player |
| CapSelectedPer | Percentage who made this player captain |
| VCapSelectedPer | Percentage who made this player vice-captain |
| GamedayPoints | Points scored in current game day |
| OverallPoints | Total season points |

### Dashboard Features

- **Four Tabs**:
  - **All Players** - Full player list with filters, sorting, and stats sidebar
  - **Today's Match** - Side-by-side home/away team tables (sidebar hidden)
  - **Next Match** - Side-by-side tables for all teams (sidebar hidden)
  - **Transfers** - Complete match-by-match transfer history with team-wise player counts (sidebar hidden)
- **Playing XI Detection**: Players with `IsAnnounced='P'` shown with green text and checkmark
- **Announced Squad**: Players with `IsAnnounced='P'` or `'NP'` shown in bold
- **Sortable Columns**: Click any header to sort (default: Playing XI first)
- **Team Filter**: Dropdown to filter by team (All Players tab only)
- **Playing XI Filter**: Checkbox to show only playing XI members (All Players tab only)
- **Today's Match Tab**:
  - Side-by-side tables for home and away teams
  - Columns: Name, Skill, Value, Sel By (%), Cap (%), VCap (%), Overall Points
  - Compact styling (0.8rem font) for side-by-side display
  - If Playing XI announced: shows only playing XI members (isPlaying=true)
  - If only squad announced: shows all team members
  - Green text for playing players
- **Next Match Tab**:
  - Same layout as Today's Match
  - Teams determined from `ipl26.csv` schedule file
  - Shows home/away teams for the next match date after today
  - Useful for planning transfers for upcoming matches
- **Transfers Tab**:
  - Displays all 70 matches with complete transfer data from `ipl26_computed.csv`
  - Columns: Match No, Date, Home, Away, Gap-1, Gap-2, CSK, DC, GT, KKR, LSG, MI, PBKS, RCB, RR, SRH, Total, Transfers, Scoring Players
  - Today's matches highlighted with gold left border and background
  - Past matches greyed out (50% opacity)
  - All columns sortable by clicking header
  - Horizontal scroll for mobile responsiveness
- **Responsive Layout**: Sidebar with stats, filters, and legend; main table area
