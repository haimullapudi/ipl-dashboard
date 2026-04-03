# IPL Wildcard Booster Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Add Wildcard booster support to the transfer optimizer with early (match 14) and late (match 56) strategy options.

**Architecture:** Two-phase optimization similar to Free Hit: (1) Standard beam search, (2) At Wildcard match, generate new squad with unlimited transfers that persists for remaining matches.

**Tech Stack:** Python 3.14, existing beam search optimizer (`ipl_optimizer.py`), Free Hit implementation as reference

---

### Task 1: Add Wildcard Configuration Constants

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:25-29`

**Step 1: Add Wildcard constants after Free Hit configuration**

Add after line 29:
```python
# Wildcard configuration
WILDCARD_MATCH = 14  # Default: Early strategy (end of first round-robin)
# Alternative: Match 56 (Late strategy - playoff push)
# Analysis: Early Wildcard gives 56 matches to benefit from new squad
#           Late Wildcard optimizes for final 15 matches
```

**Step 2: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: add Wildcard configuration constants"
```

---

### Task 2: Add Wildcard State Tracking

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:318-338` (State class)

**Step 1: Add Wildcard state to State class**

Modify the `__init__` method to track Wildcard usage:

```python
def __init__(
    self,
    squad_tuple: Tuple[Tuple[str, int], ...],
    transfers_used: int,
    total_scoring: int,
    match_history: List[Tuple[int, Dict[str, int], int, int]],
    violations: int,
    free_hit_used: bool = False,
    pre_free_hit_squad: Optional[Dict[str, int]] = None,
    wildcard_used: bool = False  # NEW: Track Wildcard usage
):
    self.squad_tuple = squad_tuple
    self.transfers_used = transfers_used
    self.total_scoring = total_scoring
    self.match_history = match_history
    self.violations = violations
    self.free_hit_used = free_hit_used
    self.pre_free_hit_squad = pre_free_hit_squad
    self.wildcard_used = wildcard_used  # No reversion needed - squad persists
```

**Step 2: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: add Wildcard state tracking to State class"
```

---

### Task 3: Add Wildcard Squad Generation Function

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:315-316` (add after `generate_free_hit_squad`)

**Step 1: Add Wildcard squad generation function**

Add after `generate_free_hit_squad` function:

```python
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
```

**Step 2: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: add Wildcard squad generation function"
```

---

### Task 4: Modify Beam Search to Support Wildcard

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:340-347` (beam_search signature)
- Modify: `src/transfer_optimizer/ipl_optimizer.py:380-420` (main loop - approximate location)

**Step 1: Add use_wildcard parameter to function signature**

```python
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
```

**Step 2: Add Wildcard match handling in main loop**

Find the Free Hit handling block (around line 380+) and add Wildcard handling similarly:

```python
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
```

**Note:** Unlike Free Hit, NO reversion logic is needed - the Wildcard squad persists naturally.

**Step 3: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: modify beam search to support Wildcard at specified match"
```

---

### Task 5: Add CLI Option for Wildcard

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:780-800` (main function, argparse section - approximate)

**Step 1: Add --wildcard argument**

Find the argparse section and add:

```python
parser.add_argument('--wildcard', action='store_true', help='Use Wildcard booster at early match (match 14)')
parser.add_argument('--wildcard-match', type=int, help='Specify custom Wildcard match number')
```

**Step 2: Pass Wildcard params to beam_search**

Find the beam_search call and update:

```python
best_state = beam_search(
    matches,
    min_scoring=args.min_scoring,
    max_scoring=args.max_scoring,
    max_transfers_per_match=args.max_transfers,
    use_free_hit=args.free_hit or (args.free_hit_match is not None),
    free_hit_match=args.free_hit_match if args.free_hit_match else FREE_HIT_MATCH,
    use_wildcard=args.wildcard or (args.wildcard_match is not None),
    wildcard_match=args.wildcard_match if args.wildcard_match else WILDCARD_MATCH
)
```

**Step 3: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: add CLI options for Wildcard booster"
```

---

### Task 6: Update Summary Output for Wildcard

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:741-760` (print_summary function - approximate)

**Step 1: Add Wildcard info to summary**

Update the function signature and body:

```python
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
```

**Step 2: Update call to print_summary in main()**

```python
print_summary(
    matches,
    free_hit_used=args.free_hit or (args.free_hit_match is not None),
    free_hit_match=args.free_hit_match if args.free_hit_match else FREE_HIT_MATCH,
    wildcard_used=args.wildcard or (args.wildcard_match is not None),
    wildcard_match=args.wildcard_match if args.wildcard_match else WILDCARD_MATCH
)
```

**Step 3: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: add Wildcard info to summary output"
```

---

### Task 7: Add Validation for Booster Conflicts

**Files:**
- Modify: `src/transfer_optimizer/ipl_optimizer.py:800-820` (main function, before beam_search call - approximate)

**Step 1: Add validation logic**

Add before calling beam_search:

```python
# Validate booster configuration
if args.free_hit_match is not None and args.wildcard_match is not None:
    if args.free_hit_match == args.wildcard_match:
        print("Error: Cannot use Free Hit and Wildcard at the same match")
        sys.exit(1)
```

**Step 2: Commit**

```bash
git add src/transfer_optimizer/ipl_optimizer.py
git commit -m "feat: validate Free Hit and Wildcard are not used at same match"
```

---

### Task 8: Add Test for Wildcard Functionality

**Files:**
- Modify: `src/transfer_optimizer/test_optimizer.py:367-368` (add after TestFreeHit class)

**Step 1: Add Wildcard test class**

Add after `TestFreeHit` class:

```python
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

            # Squad should be similar (may have small optimizations)
            # The key is it doesn't revert to pre-Wildcard squad
            assert best_state.wildcard_used, "Wildcard flag should persist"

            print("Wildcard test PASSED")

        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
```

**Step 2: Run test**

```bash
cd src/transfer_optimizer
python3 test_optimizer.py
```

Expected: All tests pass including new Wildcard test

**Step 3: Commit**

```bash
git add src/transfer_optimizer/test_optimizer.py
git commit -m "test: add Wildcard functionality test"
```

---

### Task 9: Run Full Optimization with Early Wildcard

**Files:**
- N/A (verification task)

**Step 1: Run Early Wildcard optimization**

```bash
cd src/transfer_optimizer
python3 ipl_optimizer.py --wildcard --output ipl26_wildcard_early.csv
```

Expected output:
- Beam search progress every 5 matches
- Match 14 shows Wildcard usage
- Total scoring players, transfers used displayed

**Step 2: Verify output**

```bash
# Check Wildcard match details
grep "^14," ipl26_wildcard_early.csv
```

Expected: Match 14 shows 0 transfers, 11 scoring players (6 home + 5 away)

**Step 3: Commit output**

```bash
git add ipl26_wildcard_early.csv
git commit -m "chore: generate Wildcard Early strategy output"
```

---

### Task 10: Run Full Optimization with Late Wildcard

**Files:**
- N/A (verification task)

**Step 1: Run Late Wildcard optimization**

```bash
cd src/transfer_optimizer
python3 ipl_optimizer.py --wildcard --wildcard-match 56 --output ipl26_wildcard_late.csv
```

**Step 2: Verify output**

```bash
# Check Wildcard match details
grep "^56," ipl26_wildcard_late.csv
```

Expected: Match 56 shows 0 transfers, 11 scoring players

**Step 3: Commit output**

```bash
git add ipl26_wildcard_late.csv
git commit -m "chore: generate Wildcard Late strategy output"
```

---

### Task 11: Compare Early vs Late Wildcard Strategies

**Files:**
- N/A (analysis task)

**Step 1: Compare results**

```bash
cd src/transfer_optimizer
echo "=== Early Wildcard (Match 14) ==="
tail -1 ipl26_wildcard_early.csv | awk -F',' '{print "Total Scoring: " $18}'

echo "=== Late Wildcard (Match 56) ==="
tail -1 ipl26_wildcard_late.csv | awk -F',' '{print "Total Scoring: " $18}'
```

**Step 2: Manual comparison**

Compare:
- Total scoring players (higher = better)
- Average scoring per match
- Transfer efficiency

**Step 3: Update README with findings**

Add Wildcard section to `README.md` with:
- Wildcard vs Free Hit comparison
- Early vs Late strategy results
- CLI usage examples

---

### Task 12: Update README with Wildcard Documentation

**Files:**
- Modify: `src/transfer_optimizer/README.md`

**Step 1: Add Wildcard section**

Add after Free Hit section:

```markdown
## Wildcard Booster

The Wildcard booster allows unlimited transfers for one match with a persistent squad change.

### Wildcard vs Free Hit

| Aspect | Free Hit | Wildcard |
|--------|----------|----------|
| Transfers | Unlimited | Unlimited |
| Squad after | Reverts to pre-match | Persists |
| Best for | Isolated matches | Squad reconstruction |
| Default match | 38 (LSG vs KKR) | 14 (Early) or 56 (Late) |

### Wildcard Strategies

**Early Wildcard (Match 14):**
- End of first round-robin
- 56 remaining matches to benefit from new squad
- Good for: Establishing optimal long-term squad

**Late Wildcard (Match 56):**
- Start of final 15 matches
- Playoff push optimization
- Good for: Maximizing final stretch scoring

### Usage

```bash
# Early Wildcard (default match 14)
python3 ipl_optimizer.py --wildcard --output ipl26_wildcard_early.csv

# Late Wildcard (match 56)
python3 ipl_optimizer.py --wildcard --wildcard-match 56 --output ipl26_wildcard_late.csv

# Custom Wildcard match
python3 ipl_optimizer.py --wildcard --wildcard-match 25 --output ipl26_custom.csv
```

### Results Comparison

| Strategy | Total Scoring | Avg/Match | Transfers |
|----------|---------------|-----------|-----------|
| Standard | TBD | TBD | TBD |
| Early Wildcard | TBD | TBD | TBD |
| Late Wildcard | TBD | TBD | TBD |
```

**Step 2: Commit**

```bash
git add src/transfer_optimizer/README.md
git commit -m "docs: add Wildcard booster documentation"
```

---

### Task 13: Final Verification

**Files:**
- N/A (verification task)

**Step 1: Run all tests**

```bash
cd src/transfer_optimizer
python3 test_optimizer.py
```

Expected: All tests pass

**Step 2: Verify standard optimization still works**

```bash
python3 ipl_optimizer.py --output ipl26_standard.csv
```

**Step 3: Verify Free Hit still works**

```bash
python3 ipl_optimizer.py --free-hit --output ipl26_freehit.csv
```

**Step 4: Verify Wildcard works**

```bash
python3 ipl_optimizer.py --wildcard --output ipl26_wildcard_early.csv
```

All commands should complete successfully with valid output files.

---

## Summary

This plan implements Wildcard booster support:

1. **Configuration** - Constants for default Wildcard match (14)
2. **State tracking** - Add `wildcard_used` flag (no reversion tracking)
3. **Squad generation** - Reuse 6+5 strategy from Free Hit
4. **Beam search** - Handle Wildcard with persistent squad
5. **CLI** - `--wildcard` and `--wildcard-match` options
6. **Validation** - Prevent Free Hit + Wildcard at same match
7. **Testing** - Verify Wildcard functionality
8. **Comparison** - Run Early (14) vs Late (56) strategies
9. **Documentation** - Update README with Wildcard info

### Expected Benefits

- **Early Wildcard:** More matches to benefit from optimized squad
- **Late Wildcard:** Better for playoff push
- **Flexibility:** User can specify custom match or compare both strategies
