# IPL Players Dashboard - Flask Web Application Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert the static IPL Fantasy Players Dashboard to a dynamic Flask web application with real-time API fetching.

**Architecture:** Flask backend serves HTML and proxies API requests; frontend uses fetch() to load data dynamically on page load.

**Tech Stack:** Python 3, Flask 3.x, urllib (standard library), JavaScript ES6, HTML5, CSS3

---

### Task 1: Create Flask Server (server.py)

**Files:**
- Create: `server.py`
- Test: Run `python3 server.py` and verify server starts

**Step 1: Create Flask server with basic route**

```python
#!/usr/bin/env python3
"""
Flask server for IPL Fantasy Players Dashboard.
Serves static HTML and proxies API requests to bypass CORS.
"""

from flask import Flask, jsonify, send_from_directory
import json
import urllib.request
import csv
from datetime import datetime, date

app = Flask(__name__, static_folder='.', static_url_path='')

API_URL = "https://fantasy.iplt20.com/classic/api/feed/gamedayplayers?lang=en&tourgamedayId=5"
SCHEDULE_FILE = "ipl26.csv"
TRANSFERS_FILE = "ipl26_computed.csv"

# ... helper functions (parse_date, load_match_schedule, etc.)

@app.route('/')
def index():
    """Serve main HTML page."""
    return send_from_directory('.', 'players.html')

@app.route('/api/players')
def get_players():
    """Fetch players data from IPL Fantasy API."""
    req = urllib.request.Request(
        API_URL,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**Step 2: Run server and verify it starts**

```bash
python3 server.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

**Step 3: Test health endpoint**

```bash
curl http://localhost:5000/api/health
```

Expected: `{"status":"healthy","timestamp":"..."}`

**Step 4: Commit**

```bash
git add server.py
git commit -m "Add Flask server with basic routes"
```

---

### Task 2: Add CSV Helper Functions to server.py

**Files:**
- Modify: `server.py`

**Step 1: Add parse_date function**

```python
def parse_date(date_str):
    """Parse date string like '28-Mar-26' to date object."""
    try:
        return datetime.strptime(date_str, '%d-%b-%y').date()
    except:
        return None
```

**Step 2: Add load_match_schedule function**

```python
def load_match_schedule():
    """Load match schedule from CSV and return matches grouped by date."""
    matches_by_date = {}
    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                match_date = parse_date(row['Date'])
                if match_date:
                    if match_date not in matches_by_date:
                        matches_by_date[match_date] = []
                    matches_by_date[match_date].append({
                        'home': row['Home'],
                        'away': row['Away'],
                        'match_no': int(row['Match No'])
                    })
    except Exception as e:
        print(f"Warning: Could not load schedule: {e}")
    return matches_by_date
```

**Step 3: Add get_today_and_next_match function**

```python
def get_today_and_next_match():
    """Get today's matches and next match day teams from schedule."""
    matches_by_date = load_match_schedule()
    today = date.today()

    today_matches = matches_by_date.get(today, [])
    today_teams_list = [[m['home'], m['away']] for m in today_matches]

    next_teams_list = []
    for match_date in sorted(matches_by_date.keys()):
        if match_date > today:
            next_teams_list = [[m['home'], m['away']] for m in matches_by_date[match_date]]
            break

    return today_teams_list, next_teams_list
```

**Step 4: Add load_transfers_data function**

```python
def load_transfers_data():
    """Load transfers data from ipl26_computed.csv."""
    transfers = []
    try:
        with open(TRANSFERS_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                transfers.append({
                    'match_no': int(row['Match No']),
                    'date': row['Date'],
                    'home': row['Home'],
                    'away': row['Away'],
                    'team1_gap': row.get('Team-1 Gap', ''),
                    'team2_gap': row.get('Team-2 Gap', ''),
                    'CSK': row.get('CSK', ''),
                    'DC': row.get('DC', ''),
                    'GT': row.get('GT', ''),
                    'KKR': row.get('KKR', ''),
                    'LSG': row.get('LSG', ''),
                    'MI': row.get('MI', ''),
                    'PBKS': row.get('PBKS', ''),
                    'RCB': row.get('RCB', ''),
                    'RR': row.get('RR', ''),
                    'SRH': row.get('SRH', ''),
                    'total': row.get('Total', '11'),
                    'transfers': row.get('Transfers', ''),
                    'scoring_players': row.get('Scoring Players', '')
                })
    except Exception as e:
        print(f"Warning: Could not load transfers data: {e}")
    return transfers
```

**Step 5: Commit**

```bash
git add server.py
git commit -m "Add CSV helper functions to server"
```

---

### Task 3: Add Match and Transfers API Endpoints

**Files:**
- Modify: `server.py`

**Step 1: Add /api/today-matches endpoint**

```python
@app.route('/api/today-matches')
def get_today_matches():
    """Get today's and next match day matches from schedule."""
    try:
        today_matches, next_matches = get_today_and_next_match()
        return jsonify({
            'today': today_matches,
            'next': next_matches,
            'today_match_nos': [
                m['match_no'] for m in load_match_schedule().get(date.today(), [])
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Step 2: Add /api/transfers endpoint**

```python
@app.route('/api/transfers')
def get_transfers():
    """Load transfers data from ipl26_computed.csv."""
    try:
        transfers = load_transfers_data()
        return jsonify(transfers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Step 3: Test endpoints**

```bash
curl http://localhost:5000/api/today-matches
curl http://localhost:5000/api/transfers | head -20
```

**Step 4: Commit**

```bash
git add server.py
git commit -m "Add match and transfers API endpoints"
```

---

### Task 4: Create requirements.txt and Procfile

**Files:**
- Create: `requirements.txt`
- Create: `Procfile`

**Step 1: Create requirements.txt**

```
Flask==3.0.0
gunicorn==21.2.0
```

**Step 2: Create Procfile**

```
web: gunicorn server:app --workers 2 --threads 4
```

**Step 3: Create .gitignore (or update)**

```
__pycache__/
*.pyc
.env
venv/
.DS_Store
players_data.json
*.log
```

**Step 4: Commit**

```bash
git add requirements.txt Procfile .gitignore
git commit -m "Add deployment configuration files"
```

---

### Task 5: Modify players.html - Remove Embedded Data

**Files:**
- Modify: `players.html`

**Step 1: Remove embedded window.data assignments**

Find and remove:
```javascript
window.playersData = {/* large JSON */};
window.todayMatches = {/* ... */};
window.nextMatches = {/* ... */};
window.transfersData = {/* ... */};
window.todayMatchNos = {/* ... */};
```

**Step 2: Add fetch functions at top of script**

```javascript
// Data loaded from server
window.playersData = null;
window.todayMatches = null;
window.nextMatches = null;
window.transfersData = null;
window.todayMatchNos = [];

// Loading state
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '<div class="loading-spinner">Loading...</div>';
    }
}

// Error state
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="table-container">
                <div class="error-message">
                    <p>⚠️ ${message}</p>
                    <button class="retry-btn" onclick="location.reload()">Retry</button>
                </div>
            </div>
        `;
    }
}

// Load all data
async function loadAllData() {
    try {
        const [playersRes, matchesRes, transfersRes] = await Promise.all([
            fetch('/api/players'),
            fetch('/api/today-matches'),
            fetch('/api/transfers')
        ]);

        window.playersData = await playersRes.json();
        const matchesData = await matchesRes.json();
        window.todayMatches = matchesData.today;
        window.nextMatches = matchesData.next;
        window.todayMatchNos = matchesData.today_match_nos || [];
        window.transfersData = await transfersRes.json();

        // Render all tabs
        renderTable(window.playersData);
        renderTodayMatchTables(window.playersData);
        renderNextMatchTables(window.playersData);
        renderTransfersTable(window.transfersData);
    } catch (error) {
        console.error('Failed to load data:', error);
        showError('content', 'Failed to load data. Please refresh.');
    }
}
```

**Step 3: Update initialization**

Replace:
```javascript
// Initialize with default tab
const players = window.playersData.gamedayPlayers || [];
// ...
```

With:
```javascript
// Load data on page ready
document.addEventListener('DOMContentLoaded', loadAllData);
```

**Step 4: Add loading/error CSS**

In `<style>` section, add:
```css
.loading-spinner {
    text-align: center;
    padding: 50px;
    color: #f0a500;
    font-size: 1.2rem;
}

.error-message {
    background: rgba(220, 38, 38, 0.2);
    border: 1px solid #dc2626;
    color: #fca5a5;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    margin: 20px;
}

.retry-btn {
    background: linear-gradient(135deg, #f0a500, #ff8c00);
    color: #1a1a2e;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    cursor: pointer;
    margin-top: 10px;
    font-weight: 600;
}

.retry-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(240, 165, 0, 0.4);
}
```

**Step 5: Test in browser**

```bash
python3 server.py
# Open http://localhost:5000
```

Expected: Page loads with spinner, then displays data

**Step 6: Commit**

```bash
git add players.html
git commit -m "Convert players.html to use fetch() for real-time data"
```

---

### Task 6: Add Last Updated Indicator

**Files:**
- Modify: `players.html`

**Step 1: Add last updated element in sidebar**

In the `.data-info` div, add:
```html
<div class="data-info">
    <span class="date">Data fetched: <span id="last-updated">Loading...</span></span>
    <span class="gameday">Game Day ID: 5</span>
    <span class="last-updated" id="update-time"></span>
</div>
```

**Step 2: Update timestamp on load**

In `loadAllData()` function, after data loads:
```javascript
function updateTimestamp() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
    document.getElementById('update-time').textContent = `Updated at ${timeStr}`;
}

// Call in loadAllData after data loads
updateTimestamp();
```

**Step 3: Add CSS for last-updated**

```css
.last-updated {
    display: block;
    font-size: 0.75rem;
    color: #aaa;
    margin-top: 5px;
    opacity: 0.8;
}
```

**Step 4: Commit**

```bash
git add players.html
git commit -m "Add last updated timestamp indicator"
```

---

### Task 7: Update README.md

**Files:**
- Modify: `README.md`

**Step 1: Add Web Application section**

After "Installation" section, add:

```markdown
## Web Application (Real-time Data)

The dashboard now runs as a Flask web application with real-time data fetching.

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python3 server.py

# Open browser
http://localhost:5000
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Main dashboard |
| `/api/players` | Players data from IPL API |
| `/api/today-matches` | Today's and next match data |
| `/api/transfers` | Transfer history data |
| `/api/health` | Health check |

### Deployment (Railway/Render)

1. **Railway:**
   - Connect GitHub repository
   - Auto-deploys on push
   - Free tier available

2. **Render:**
   - Create Web Service
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn server:app --workers 2 --threads 4`

### Static Version (Legacy)

The original static HTML version is still available:

```bash
python3 fetch_players.py
open players.html
```
```

**Step 2: Update Features section**

Add to Features:
- **Real-time data** - Fresh data on every page load via Flask backend
- **Auto-refresh** - No manual updates needed

**Step 3: Commit**

```bash
git add README.md
git commit -m "Update README with web application instructions"
```

---

### Task 8: Final Testing and Push

**Files:**
- All modified files

**Step 1: Full local test**

```bash
# Kill any running server
pkill -f "python3 server.py"

# Start fresh
python3 server.py
```

**Step 2: Test all tabs in browser**

- All Players tab: Check data loads, filters work, sorting works
- Today's Match tab: Check teams display correctly
- Next Match tab: Check next match teams display
- Transfers tab: Check all 70 matches with highlighting

**Step 3: Verify static version still works**

```bash
python3 fetch_players.py
```

**Step 4: Push all changes**

```bash
git push
```

**Step 5: Verify on GitHub**

Check https://github.com/haimullapudi/ipl-transfers for all commits

---

## Success Criteria

- [ ] Server starts successfully on port 5000
- [ ] All API endpoints return valid JSON
- [ ] Page loads with spinner, then displays data
- [ ] All four tabs work correctly
- [ ] Filters and sorting work
- [ ] Today's matches highlighted, past matches greyed
- [ ] Last updated timestamp shows
- [ ] Static version (`fetch_players.py`) still works
- [ ] Deployed to Railway/Render successfully

## Rollback Plan

If issues occur:
1. Static `players.html` still works standalone
2. Revert to previous commit: `git checkout <commit> -- players.html`
3. Run `python3 fetch_players.py` for static version
