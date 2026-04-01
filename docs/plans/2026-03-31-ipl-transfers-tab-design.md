# IPL Transfers Tab - Design Document

## Overview

Add a "Transfers" tab to the IPL Fantasy Players Dashboard that displays the complete transfer history from `ipl26_computed.csv` with visual indicators for match status.

## Architecture

### Data Source

**File:** `ipl26_computed.csv`

| Column | Name | Description |
|--------|------|-------------|
| 1 | Match No | Sequential match number (1-70) |
| 2 | Date | Match date (e.g., "28-Mar-26") |
| 3 | Home | Home team |
| 4 | Away | Away team |
| 5 | Team-1 Gap | Matches until home team plays again |
| 6 | Team-2 Gap | Matches until away team plays again |
| 7-16 | Team columns | Player count per team (CSK, DC, GT, KKR, LSG, MI, PBKS, RCB, RR, SRH) |
| 17 | Total | Sum of team columns (always 11) |
| 18 | Transfers | Players added vs previous match |
| 19 | Scoring Players | Home + Away team players in squad |

### Implementation

1. **Python Script (fetch_players.py)**
   - Add `load_transfers_data()` function to read `ipl26_computed.csv`
   - Convert CSV data to JSON and embed in HTML
   - Determine today's match number for highlighting

2. **JavaScript Rendering**
   - `renderTransfersTable(data)` - Render the transfers table
   - `sortTransfers()` - Column sorting functionality
   - Match status classification (past/today/future)

3. **CSS Styling**
   - `.match-today` - Gold border/background for today's matches
   - `.match-past` - Greyed out (opacity: 0.5) for completed matches
   - `.match-future` - Normal display for upcoming matches
   - Horizontal scroll for table on mobile

## Table Columns

All 19 columns displayed:

| Column | Sortable | Type |
|--------|----------|------|
| Match No | Yes | Number |
| Date | Yes | String |
| Home | Yes | String |
| Away | Yes | String |
| Team-1 Gap | Yes | Number |
| Team-2 Gap | Yes | Number |
| CSK | Yes | Number |
| DC | Yes | Number |
| GT | Yes | Number |
| KKR | Yes | Number |
| LSG | Yes | Number |
| MI | Yes | Number |
| PBKS | Yes | Number |
| RCB | Yes | Number |
| RR | Yes | Number |
| SRH | Yes | Number |
| Total | Yes | Number |
| Transfers | Yes | Number |
| Scoring Players | Yes | Number |

## Visual States

| State | Styling |
|-------|---------|
| Today's Match | Gold left border (4px solid #f0a500), slight glow |
| Past Matches | Opacity 0.5, muted colors |
| Future Matches | Normal display |

## Data Flow

```
ipl26_computed.csv → Python CSV reader → JSON → Embedded in HTML → Browser renders
```

## Implementation Steps

1. Add CSV loading function in `fetch_players.py`
2. Embed transfers data as JSON in HTML template
3. Create "Transfers" tab button and content div
4. Implement `renderTransfersTable()` JavaScript function
5. Add match status highlighting logic
6. Implement column sorting
7. Add CSS for visual states
8. Hide sidebar when Transfers tab is active

## CSS Styling

```css
/* Match status indicators */
.match-today {
    border-left: 4px solid #f0a500;
    background: rgba(240, 165, 0, 0.1);
}

.match-past {
    opacity: 0.5;
}

/* Table styling */
.transfers-table-container {
    overflow-x: auto;
}

.transfers-table {
    min-width: 1200px; /* Ensure all columns fit */
}
```

## Files to Modify

| File | Changes |
|------|---------|
| `fetch_players.py` | Add `load_transfers_data()`, embed JSON |
| `players.html` | Add tab button, content div, render function |
| `README.md` | Document new tab |
| `specs.md` | Update with Transfers tab |
| `docs/plans/2026-03-31-ipl-players-dashboard-design.md` | Update architecture |
