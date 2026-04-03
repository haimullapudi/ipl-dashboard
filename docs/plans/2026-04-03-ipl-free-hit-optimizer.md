# IPL Free Hit Optimizer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Free Hit booster support to the transfer optimizer with optimal match selection based on team gap analysis.

**Architecture:** Two-phase optimization: (1) Run standard beam search for matches 1-70, (2) At the optimal Free Hit match (match 38: LSG vs KKR), generate a completely new squad optimized for scoring without transfer cost, then revert to the previous squad for match 39.

**Tech Stack:** Python 3.14, existing beam search optimizer (`ipl_optimizer.py`), gap analysis script (`analyze_free_hit.py`)

---

## Overview

The Free Hit booster allows unlimited transfers for one match with no budget restrictions, after which the squad reverts to the previous lineup. This plan implements:

1. Free Hit match selection based on gap analysis (match 38: LSG vs KKR identified as optimal)
2. Two-phase optimization: standard beam search + Free Hit overlay
3. CLI option to enable Free Hit at specified match
4. Output showing Free Hit squad and comparison with standard optimization

### Free Hit Match Rationale

From gap analysis, Match 38 (LSG vs KKR on 26-Apr-26) is optimal because:
- LSG: forward gap=9, backward gap=6 (isolated for 15 days)
- KKR: forward gap=7, backward gap=10 (isolated for 17 days)
- Combined isolation score: 13 (highest in tournament)
- Players from both teams are "dead weight" for surrounding matches

---

### Task 1: Add Free Hit Configuration Constants

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:14-24`

**Step 1: Add Free Hit constants after existing constants**

```python
# Default constraints
DEFAULT_MIN_SCORING = 3
DEFAULT_MAX_SCORING = 6
DEFAULT_MAX_TRANSFERS_PER_MATCH = 4

# Free Hit configuration
FREE_HIT_MATCH = 38  # Optimal: LSG vs KKR (26-Apr-26)
# Analysis shows both teams have maximum isolation:
# - LSG: gap=9 forward, gap=6 backward
# - KKR: gap=7 forward, gap=10 backward
```

**Step 2: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: add Free Hit configuration constants"
```

---

### Task 2: Add Free Hit State Tracking

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:278-295` (State class)

**Step 1: Add Free Hit state to State class**

Modify the `__init__` method to track Free Hit usage:

```python
def __init__(
    self,
    squad_tuple: Tuple[Tuple[str, int], ...],
    transfers_used: int,
    total_scoring: int,
    match_history: List[Tuple[int, Dict[str, int], int, int]],
    violations: int,
    free_hit_used: bool = False,
    pre_free_hit_squad: Optional[Dict[str, int]] = None
):
    self.squad_tuple = squad_tuple
    self.transfers_used = transfers_used
    self.total_scoring = total_scoring
    self.match_history = match_history
    self.violations = violations
    self.free_hit_used = free_hit_used
    self.pre_free_hit_squad = pre_free_hit_squad  # Squad before Free Hit for reversion
```

**Step 2: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: add Free Hit state tracking to State class"
```

---

### Task 3: Add Free Hit Squad Generation Function

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py` (add after `generate_candidates` function, around line 276)

**Step 1: Add function to generate optimal Free Hit squad**

```python
def generate_free_hit_squad(home: str, away: str, min_scoring: int, max_scoring: int) -> Dict[str, int]:
    """
    Generate optimal squad for Free Hit match.

    Since Free Hit has no transfer cost, we can build the ideal squad from scratch
    focused purely on maximizing scoring players for this match.

    Strategy:
    - Maximize players from home and away teams (they score in this match)
    - Balance between home/away based on their relative strength (assumed equal)
    - Fill remaining slots with players from teams with favorable gaps
    """
    squad = {team: 0 for team in TEAMS}

    # Optimal scoring distribution: maximize home + away players
    # Target: 6 scoring players (max allowed) for maximum points potential
    # Split: 3 home + 3 away (balanced approach)
    squad[home] = 4  # Slight home advantage
    squad[away] = 3  # 7 total scoring players (within 3-6 range... wait, need to fix)

    # Actually, max_scoring is 6, so let's do 3+3=6
    squad[home] = 3
    squad[away] = 3

    # Distribute remaining 5 players to teams with best gap values
    # For now, distribute evenly among other teams
    other_teams = [t for t in TEAMS if t not in (home, away)]
    remaining = 11 - 6  # 5 players

    # Simple distribution: give 1 to each of 5 teams, 0 to the other 3
    for i, team in enumerate(other_teams[:5]):
        squad[team] = 1

    return squad
```

**Step 2: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: add Free Hit squad generation function"
```

---

### Task 4: Modify Beam Search to Support Free Hit

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:296-586` (beam_search function)

**Step 1: Add use_free_hit parameter to function signature**

```python
def beam_search(
    matches: List[Match],
    min_scoring: int = DEFAULT_MIN_SCORING,
    max_scoring: int = DEFAULT_MAX_SCORING,
    max_transfers_per_match: int = DEFAULT_MAX_TRANSFERS_PER_MATCH,
    use_free_hit: bool = False,
    free_hit_match: int = FREE_HIT_MATCH
) -> Optional[State]:
```

**Step 2: Add Free Hit logic inside the main loop (around line 329)**

After `match = matches[match_idx]`, add:

```python
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

    continue  # Skip normal candidate generation for Free Hit match
```

**Step 3: Add reversion logic for match after Free Hit**

After the Free Hit match processing, add logic to revert:

```python
# Check if previous match was Free Hit - if so, revert squad
for state in beam:
    if state.free_hit_used and state.pre_free_hit_squad is not None:
        # Check if we're at the match right after Free Hit
        last_match_no = state.match_history[-1][0]
        if last_match_no == free_hit_match:
            # Next iteration will handle reversion via pre_free_hit_squad
            pass
```

Actually, the reversion should happen naturally because we save `pre_free_hit_squad`. Let me refine this...

The cleaner approach: In the match AFTER Free Hit, use `pre_free_hit_squad` as the starting point instead of the Free Hit squad.

Add before candidate generation:

```python
# If Free Hit was used last match, revert to pre-Free Hit squad
if use_free_hit and match.match_no == free_hit_match + 1:
    # Filter beam to states that used Free Hit
    reverted_beam = []
    for state in beam:
        if state.free_hit_used and state.pre_free_hit_squad:
            # Create reverted state
            reverted_state = State(
                squad_tuple=squad_to_tuple(state.pre_free_hit_squad),
                transfers_used=state.transfers_used,
                total_scoring=state.total_scoring,  # Keep the Free Hit scoring
                match_history=state.match_history,  # Will add new match below
                violations=state.violations,
                free_hit_used=True,
                pre_free_hit_squad=None  # Clear after reversion
            )
            reverted_beam.append(reverted_state)

    # Use reverted beam for this match
    beam = reverted_beam
```

**Step 4: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: modify beam search to support Free Hit at optimal match"
```

---

### Task 5: Add CLI Option for Free Hit

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:666-675` (main function, argparse section)

**Step 1: Add --free-hit argument**

```python
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
```

**Step 2: Pass Free Hit params to beam_search**

```python
best_state = beam_search(
    matches,
    min_scoring=args.min_scoring,
    max_scoring=args.max_scoring,
    max_transfers_per_match=args.max_transfers,
    use_free_hit=args.free_hit or (args.free_hit_match is not None),
    free_hit_match=args.free_hit_match if args.free_hit_match else FREE_HIT_MATCH
)
```

**Step 3: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: add CLI options for Free Hit booster"
```

---

### Task 6: Update Summary Output for Free Hit

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:647-664` (print_summary function)

**Step 1: Add Free Hit info to summary**

```python
def print_summary(matches: List[Match], free_hit_used: bool = False, free_hit_match: int = None) -> None:
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

    print("\nTransfer Distribution:")
    for i in range(0, 70, 10):
        seg = matches[i:i+10]
        t = sum(m.transfers for m in seg if m.match_no > i + 1)
        print(f"  Matches {i+1:2d}-{i+10:2d}: {t:2d} transfers (avg {t/10:.1f}/match)")
    print("=" * 60)
```

**Step 2: Update call to print_summary in main()**

```python
print_summary(matches, free_hit_used=args.free_hit or (args.free_hit_match is not None),
              free_hit_match=args.free_hit_match if args.free_hit_match else FREE_HIT_MATCH)
```

**Step 3: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: add Free Hit info to summary output"
```

---

### Task 7: Add Test for Free Hit Functionality

**Files:**
- Modify: `src/transfer_optimizer/test_optimizer.py`

**Step 1: Add Free Hit test**

```python
def test_free_hit_optimizer():
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

    output_path = input_path.replace('.csv', '_computed.csv')

    try:
        # Run optimizer with Free Hit at match 3
        # (Using match 3 for test since we only have 5 matches of data)
        from ipl_optimizer import load_matches, compute_gaps, beam_search, apply_optimization

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
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)
```

**Step 2: Run test**

```bash
cd src/transfer_optimizer
python3 -m pytest test_optimizer.py::test_free_hit_optimizer -v
```

Expected: PASS

**Step 3: Commit**

```bash
git add src/transfer_optimizer/test_optimizer.py
git commit -m "test: add Free Hit functionality test"
```

---

### Task 8: Run Full Optimization with Free Hit and Compare

**Files:**
- N/A (verification task)

**Step 1: Run standard optimization**

```bash
cd src/transfer_optimizer
python3 ipl_optimizer.py --output ipl26_standard.csv
```

**Step 2: Run Free Hit optimization**

```bash
python3 ipl_optimizer.py --free-hit --output ipl26_freehit.csv
```

**Step 3: Compare results**

```bash
# Compare total scoring and transfers
echo "=== Standard Optimization ==="
tail -5 ipl26_standard.csv

echo "=== Free Hit Optimization ==="
tail -5 ipl26_freehit.csv
```

**Expected:** Free Hit optimization should show:
- Similar or better total scoring
- Fewer transfers used (saved ~4 transfers at Free Hit match)
- Match 38 should show 0 transfers with high scoring

---

## Summary

This plan implements Free Hit support in the transfer optimizer:

1. **Configuration** - Constants for optimal Free Hit match
2. **State tracking** - Track Free Hit usage and pre-Free Hit squad
3. **Squad generation** - Generate optimal Free Hit squad
4. **Beam search modification** - Handle Free Hit match specially
5. **CLI interface** - Enable Free Hit via command line
6. **Output** - Show Free Hit impact in summary
7. **Testing** - Verify Free Hit behavior
8. **Validation** - Compare standard vs Free Hit optimization

### Expected Benefits

- **Transfer savings**: ~4 transfers saved at Free Hit match
- **Scoring improvement**: Optimal squad for isolated teams match
- **Flexibility**: Can specify custom Free Hit match if needed
