# IPL Fantasy Players Dashboard - Design Document

## Overview

A static webpage that displays IPL Fantasy players data fetched from the official IPL Fantasy API. The page is generated daily with embedded JSON data to bypass CORS restrictions.

## Data Source

**API Endpoint:** `https://fantasy.iplt20.com/classic/api/feed/gamedayplayers?lang=en&tourgamedayId=4`

**Key API Fields:**

| Field | Type | Description |
|-------|------|-------------|
| Id | int | Player unique ID |
| Name | string | Full player name |
| ShortName | string | Short player name |
| TeamId | int | Team ID |
| TeamName | string | Full team name |
| TeamShortName | string | Team short code (CSK, MI, etc.) |
| SkillName | string | Player role (BATSMAN, BOWLER, ALL ROUNDER, WICKET KEEPER) |
| Value | float | Player value in credits |
| IsActive | bool | Whether player is active |
| SelectedPer | float | Selection percentage |
| CapSelectedPer | float | Captain selection percentage |
| VCapSelectedPer | float | Vice-captain selection percentage |
| GamedayPoints | float | Points in current game day |
| OverallPoints | float | Total season points |
| IsAnnounced | string | 'P'=Playing, 'NP'=Not Playing, 'S'=Substitute, ''=Empty |
| IS_FP | string | '1'=In final playing XI, '0'=Not in playing XI |

## Architecture

### Components

1. **fetch_players()** - Fetches data from IPL Fantasy API using urllib (bypasses CORS)
2. **generate_html(data)** - Generates static HTML with embedded JSON
3. **renderTable(data)** - JavaScript function to render player table
4. **sortPlayers()** - JavaScript function for column sorting
5. **applyFilters()** - JavaScript function for filtering

### Data Flow

```
IPL Fantasy API → urllib.request → Python dict → JSON → Embedded in HTML → Browser renders
```

**Why Static HTML:**
- Browser fetch() would fail due to CORS restrictions
- Server-side urllib has no CORS restrictions
- Static HTML can be hosted anywhere (GitHub Pages, Netlify, etc.)
- Daily data updates by re-running the script

## Features

### Table Columns

| Column | Sortable | Description |
|--------|----------|-------------|
| ✓ | Yes (boolean) | Playing XI indicator - green checkmark |
| Name | Yes (string) | Player name |
| Team | Yes (string) | Team badge with color |
| Skill | Yes (string) | Player role |
| Value | Yes (number) | Player value in credits |
| Sel By (%) | Yes (number) | Selection percentage |
| Cap (%) | Yes (number) | Captain percentage |
| VCap (%) | Yes (number) | Vice-captain percentage |
| Game Points | Yes (number) | Current game day points |
| Overall Points | Yes (number) | Total season points |

### Visual Indicators

| Indicator | Meaning |
|-----------|---------|
| Green checkmark (✓) + green text | Player in Playing XI (IsAnnounced='P') |
| Bold text | Player in Announced Squad (IsAnnounced='P' or 'NP') |
| Team badge color | Team-specific color coding |

### Filters

1. **Team Filter** - Dropdown (single select)
   - All Teams (default)
   - CSK, DC, GT, KKR, LSG, MI, PBKS, RCB, RR, SRH

2. **Playing XI Filter** - Checkbox
   - "Show Playing XI Only"
   - Filters to show only players with IsAnnounced='P'

### Sorting

- Default sort: Playing XI (descending) - playing players first
- Click any header to sort by that column
- Click again to toggle ascending/descending
- Visual indicator shows current sort column

### Sidebar Layout

Right sidebar (320px, sticky):
1. Data fetched banner (date + Game Day ID)
2. Filters panel (team dropdown, Playing XI checkbox)
3. Stats cards (2x2 grid):
   - Total Players
   - Announced Squad
   - Avg Game Day Points
   - Playing XI
4. Legend (green box = Playing, white box = Not Playing)

## Implementation

### Python Script (fetch_players.py)

```python
# Fetch data
API_URL = "https://fantasy.iplt20.com/classic/api/feed/gamedayplayers?lang=en&tourgamedayId=4"
req = urllib.request.Request(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
response = urllib.request.urlopen(req, timeout=30)
raw_data = json.loads(response.read().decode('utf-8'))

# Extract players from nested structure
players_list = raw_data.get('Data', {}).get('Value', {}).get('Players', [])

# Normalize fields
player = {
    'isPlaying': p.get('IsAnnounced') == 'P',      # Green + checkmark
    'isAnnounced': p.get('IsAnnounced') in ['P', 'NP'],  # Bold text
    'teamShortName': p.get('TeamShortName'),
    # ... other fields
}

# Generate HTML with embedded JSON
html_content = f'''<!DOCTYPE html>
<html>
<script>
    window.playersData = {players_json};
    // ... render functions
</script>
</html>'''
```

### JavaScript Functions

```javascript
// Sort players
function sortPlayers(players, field, type) {
    const dir = currentSort.direction === 'asc' ? 1 : -1;
    return [...players].sort((a, b) => {
        if (type === 'string') return dir * (a[field] || '').localeCompare(b[field] || '');
        if (type === 'number') return dir * ((a[field] || 0) - (b[field] || 0));
        if (type === 'boolean') return dir === -1 ? (b[field] ? 1 : 0) - (a[field] ? 1 : 0) : (a[field] ? 1 : 0) - (b[field] ? 1 : 0);
    });
}

// Apply filters
function applyFilters() {
    const teamFilter = document.getElementById('teamFilter').value;
    const playingXi = document.getElementById('playingXi').checked;
    rows.forEach(row => {
        const team = row.dataset.team;
        const isPlaying = row.dataset.playing === '1';
        let show = true;
        if (teamFilter && team !== teamFilter) show = false;
        if (playingXi && !isPlaying) show = false;
        row.classList.toggle('hidden', !show);
    });
}
```

## CSS Styling

- **Dark theme** - Gradient background (#1a1a2e to #16213e)
- **Gold accents** - Primary color #f0a500
- **Glassmorphism** - backdrop-filter: blur(10px) on cards
- **Team colors** - Specific hex codes for each IPL team
- **Responsive** - Sidebar stacks on mobile (<1024px)

## Usage

```bash
# Fetch latest data and generate dashboard
python3 fetch_players.py

# Output:
# ✓ Successfully fetched 256 players
# ✓ 43 players announced for today's squad
# ✓ Data saved to players_data.json
# ✓ Generated players.html
```

## Files

| File | Description |
|------|-------------|
| `fetch_players.py` | Python script to fetch API and generate HTML |
| `players.html` | Generated static dashboard |
| `players_data.json` | Raw API data backup |

## Future Enhancements

- [ ] Add impact player indicator
- [ ] Show points breakdown (batting, bowling, fielding)
- [ ] Add player form (last 5 matches)
- [ ] Export to CSV functionality
- [ ] Dark/light theme toggle
- [ ] Mobile-optimized view improvements
