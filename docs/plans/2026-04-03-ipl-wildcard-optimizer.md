# IPL Wildcard Booster Implementation Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:writing-plans to create the implementation plan after this design is approved.

**Goal:** Add Wildcard booster support to the transfer optimizer with early (match 14) and late (match 56) strategy options.

**Architecture:** Two-phase optimization similar to Free Hit: (1) Standard beam search, (2) At Wildcard match, generate new squad with unlimited transfers that persists for remaining matches.

**Tech Stack:** Python 3.14, existing beam search optimizer (`ipl_optimizer.py`), Free Hit implementation as reference

---

## Overview

The Wildcard booster allows unlimited transfers for one match with a persistent squad change (no reversion). This design implements:

1. Wildcard match selection with two strategies: Early (match 14) vs Late (match 56)
2. Beam search modification to handle Wildcard with persistent squad
3. CLI options to enable Wildcard and specify match
4. Comparison output showing Early vs Late strategy impact

### Wildcard vs Free Hit Comparison

| Aspect | Free Hit | Wildcard |
|--------|----------|----------|
| Transfers | Unlimited | Unlimited |
| Budget | No restrictions | No restrictions |
| Squad after | Reverts to pre-match | **Persists** |
| State tracking | `pre_free_hit_squad` | `wildcard_used` flag only |
| Optimal use | Isolated matches (gap analysis) | Squad reconstruction |
| Default match | 38 (LSG vs KKR) | 14 (early) or 56 (late) |

### Wildcard Match Rationale

**Early Wildcard (Match 14):**
- End of first round-robin (all teams have played ~7 matches)
- Form patterns established
- Maximum remaining matches (56) to benefit from new squad
- Good for: Establishing optimal long-term squad

**Late Wildcard (Match 56):**
- Start of final 15 matches (playoff push)
- Injury/form changes accommodated
- Good for: Maximizing final stretch scoring

---

## Architecture

### Data Flow

```
Match 1-13: Standard beam search
    ↓
Match 14 (Wildcard): Generate optimal squad (6+5 from playing teams)
    ↓
Match 15-70: Continue beam search with new squad as baseline
```

### State Changes

**State class additions:**
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
    self.wildcard_used = wildcard_used
```

### Beam Search Modifications

**Function signature:**
```python
def beam_search(
    matches: List[Match],
    min_scoring: int = DEFAULT_MIN_SCORING,
    max_scoring: int = DEFAULT_MAX_SCORING,
    max_transfers_per_match: int = DEFAULT_MAX_TRANSFERS_PER_MATCH,
    use_free_hit: bool = False,
    free_hit_match: int = FREE_HIT_MATCH,
    use_wildcard: bool = False,
    wildcard_match: int = 14  # Default early strategy
) -> Optional[State]:
```

**Wildcard match handling:**
```python
is_wildcard_match = use_wildcard and (match.match_no == wildcard_match)

if is_wildcard_match:
    wildcard_squad = generate_wildcard_squad(
        home=match.home,
        away=match.away,
        min_scoring=min_scoring,
        max_scoring=max_scoring
    )

    for state in beam:
        new_state = State(
            squad_tuple=squad_to_tuple(wildcard_squad),
            transfers_used=state.transfers_used,  # No transfer cost
            total_scoring=state.total_scoring + calculate_scoring_players(...),
            match_history=state.match_history + [(match.match_no, wildcard_squad.copy(), 0, ...)],
            violations=state.violations,
            free_hit_used=state.free_hit_used,
            pre_free_hit_squad=state.pre_free_hit_squad,
            wildcard_used=True  # Mark as used
        )
        new_beam.append(new_state)

    continue  # Skip normal candidate generation
```

**No reversion logic needed** - squad persists naturally since we update `squad_tuple` directly.

---

## Components

### 1. Wildcard Squad Generation

```python
def generate_wildcard_squad(home: str, away: str, min_scoring: int, max_scoring: int) -> Dict[str, int]:
    """
    Generate optimal squad for Wildcard match.

    Strategy: All 11 players from playing teams (6 home + 5 away)
    Same as Free Hit since both benefit from maximizing scoring players.
    """
    squad = {team: 0 for team in TEAMS}
    squad[home] = 6  # Home advantage
    squad[away] = 5  # 11 total scoring players
    return squad
```

### 2. CLI Interface

```python
parser.add_argument('--wildcard', action='store_true', help='Use Wildcard booster at early match (match 14)')
parser.add_argument('--wildcard-match', type=int, help='Specify custom Wildcard match number')
```

### 3. Summary Output

```python
if wildcard_used:
    wc_match = matches[wildcard_match - 1]
    print(f"\nWILDCARD USED: Match {wildcard_match} ({wc_match.home} vs {wc_match.away})")
    print(f"  Wildcard squad scoring: {wc_match.scoring_players} players")
    print(f"  Squad persists for remaining matches (no reversion)")
```

---

## Testing Strategy

### Comparison Runs

1. **Early Wildcard:**
   ```bash
   python3 ipl_optimizer.py --wildcard --output ipl26_wildcard_early.csv
   ```

2. **Late Wildcard:**
   ```bash
   python3 ipl_optimizer.py --wildcard --wildcard-match 56 --output ipl26_wildcard_late.csv
   ```

3. **Standard (no booster):**
   ```bash
   python3 ipl_optimizer.py --output ipl26_standard.csv
   ```

### Evaluation Metrics

| Metric | Early Wildcard | Late Wildcard | Winner |
|--------|----------------|---------------|--------|
| Total scoring players | TBD | TBD | Higher wins |
| Average per match | TBD | TBD | Higher wins |
| Transfers used | TBD | TBD | Lower wins |
| Transfer efficiency | TBD | TBD | scoring/transfers |

### Test Cases

1. **Wildcard functionality test:**
   - Run with `--wildcard` at match 3 (minimal test data)
   - Verify: `wildcard_used=True`, match 3 has 0 transfers, squad persists at match 4

2. **Early vs Late comparison:**
   - Run full 70-match optimization with both strategies
   - Compare total scoring and transfer efficiency

---

## Error Handling

1. **Invalid Wildcard match:**
   - If `wildcard_match < 1` or `> 70`: Exit with error

2. **Both boosters at same match:**
   - If `free_hit_match == wildcard_match`: Exit with error (can't use both on same match)

3. **Wildcard after Free Hit:**
   - Valid scenario: Free Hit at 38, Wildcard at 56
   - Each operates independently

---

## YAGNI Decisions

**Not implementing:**
- Player credit system (user confirmed unlimited transfers)
- Complex pricing logic
- Automatic optimal match selection (user will compare Early vs Late manually)
- Combined Free Hit + Wildcard optimization (handle independently first)

**Keeping simple:**
- Same 6+5 squad strategy as Free Hit
- No state tracking for reversion (unlike Free Hit)
- CLI mirrors Free Hit interface for consistency

---

## Summary

This design implements Wildcard booster support:

1. **State tracking** - Add `wildcard_used` flag (no reversion tracking needed)
2. **Beam search** - Handle Wildcard match with unlimited transfers, persistent squad
3. **Squad generation** - Reuse Free Hit's 6+5 strategy for playing teams
4. **CLI** - `--wildcard` and `--wildcard-match` options
5. **Testing** - Compare Early (14) vs Late (56) strategies
6. **Output** - Show Wildcard impact in summary

### Expected Benefits

- **Early Wildcard:** More matches to benefit from optimized squad
- **Late Wildcard:** Better for playoff push with established form
- **Flexibility:** User can specify custom match or compare both strategies
