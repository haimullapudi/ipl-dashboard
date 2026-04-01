# IPL Transfers Tab Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Transfers" tab to the IPL Fantasy Players Dashboard that displays match-by-match transfer data from `src/transfer_optimizer/ipl26_computed.csv` with visual indicators for today's matches (highlighted) and past matches (greyed out).

**Architecture:** Python script reads CSV and embeds data as JSON in HTML, JavaScript renders the table with sorting and match status highlighting.

**Tech Stack:** Python 3 (standard library), JavaScript ES6, CSS3

---

### Task 1: Add CSV Loading Function to fetch_players.py

**Files:**
- Modify: `fetch_players.py`
- Test: Run `python3 fetch_players.py` and verify output

**Step 1: Add load_transfers_data function**

Add after `get_today_and_next_match()` function:

```python
def load_transfers_data():
    """Load transfers data from ipl26_computed.csv."""
    transfers = []
    try:
        with open('ipl26_computed.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                transfers.append({
                    'match_no': int(row['Match No']),
                    'date': row['Date'],
                    'home': row['Home'],
                    'away': row['Away'],
                    'team1_gap': row['Team-1 Gap'] if row['Team-1 Gap'] else '',
                    'team2_gap': row['Team-2 Gap'] if row['Team-2 Gap'] else '',
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

def get_today_match_no():
    """Get today's match number(s) from schedule."""
    matches_by_date = load_match_schedule()
    today = date.today()
    today_matches = matches_by_date.get(today, [])
    return [m['match_no'] for m in today_matches]
```

**Step 2: Update generate_html to embed transfers data**

In `generate_html()`, add after the today_matches/next_matches lines:

```python
transfers_data = load_transfers_data()
transfers_json = json.dumps(transfers_data)
today_match_nos = get_today_match_no()
today_match_nos_json = json.dumps(today_match_nos)
```

Then embed in HTML template:

```javascript
window.transfersData = ''' + transfers_json + ''';
window.todayMatchNos = ''' + today_match_nos_json + ''';
```

**Step 3: Run and verify**

```bash
python3 fetch_players.py
```

Expected output: "✓ Successfully fetched X players", "✓ Generated players.html"

**Step 4: Commit**

```bash
git add fetch_players.py
git commit -m "Add transfers data loading for Transfers tab"
```

---

### Task 2: Add Transfers Tab HTML Structure

**Files:**
- Modify: `fetch_players.py` (the HTML template in `generate_html()`)

**Step 1: Add Transfers tab button**

In the HTML template, find the tab buttons div and add:

```html
<button class="tab-btn active" onclick="switchTab('all')">All Players</button>
<button class="tab-btn" onclick="switchTab('match')">Today's Match</button>
<button class="tab-btn" onclick="switchTab('next')">Next Match</button>
<button class="tab-btn" onclick="switchTab('transfers')">Transfers</button>
```

**Step 2: Add Transfers tab content div**

After the `next-match-content` div, add:

```html
<div id="transfers-content" class="tab-content">
    <div class="table-container">
        <table class="transfers-table">
            <thead>
                <tr>
                    <th onclick="sortTransfers('match_no')">Match No</th>
                    <th onclick="sortTransfers('date')">Date</th>
                    <th onclick="sortTransfers('home')">Home</th>
                    <th onclick="sortTransfers('away')">Away</th>
                    <th onclick="sortTransfers('team1_gap')">Gap-1</th>
                    <th onclick="sortTransfers('team2_gap')">Gap-2</th>
                    <th onclick="sortTransfers('CSK')">CSK</th>
                    <th onclick="sortTransfers('DC')">DC</th>
                    <th onclick="sortTransfers('GT')">GT</th>
                    <th onclick="sortTransfers('KKR')">KKR</th>
                    <th onclick="sortTransfers('LSG')">LSG</th>
                    <th onclick="sortTransfers('MI')">MI</th>
                    <th onclick="sortTransfers('PBKS')">PBKS</th>
                    <th onclick="sortTransfers('RCB')">RCB</th>
                    <th onclick="sortTransfers('RR')">RR</th>
                    <th onclick="sortTransfers('SRH')">SRH</th>
                    <th onclick="sortTransfers('total')">Total</th>
                    <th onclick="sortTransfers('transfers')">Transfers</th>
                    <th onclick="sortTransfers('scoring_players')">Scoring</th>
                </tr>
            </thead>
            <tbody id="transfers-tbody">
            </tbody>
        </table>
    </div>
</div>
```

**Step 3: Update switchTab function**

Add handling for transfers tab:

```javascript
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    event.target.classList.add('active');

    // Hide sidebar for match and transfers tabs
    const sidebar = document.querySelector('.sidebar');
    const mainLayout = document.querySelector('.main-layout');
    if (tab === 'match' || tab === 'next' || tab === 'transfers') {
        sidebar.classList.add('hidden');
        mainLayout.classList.add('no-sidebar');
    } else {
        sidebar.classList.remove('hidden');
        mainLayout.classList.remove('no-sidebar');
    }

    // Render appropriate content
    if (tab === 'all') {
        renderTable(window.playersData);
    } else if (tab === 'match') {
        renderTodayMatchTables(window.playersData);
    } else if (tab === 'next') {
        renderNextMatchTables(window.playersData);
    } else if (tab === 'transfers') {
        renderTransfersTable(window.transfersData);
    }
}
```

**Step 4: Run and verify**

```bash
python3 fetch_players.py
# Open players.html in browser, click Transfers tab
```

Expected: Tab button visible, empty table structure shown

**Step 5: Commit**

```bash
git add fetch_players.py
git commit -m "Add Transfers tab HTML structure"
```

---

### Task 3: Implement renderTransfersTable Function

**Files:**
- Modify: `fetch_players.py` (JavaScript in HTML template)

**Step 1: Add renderTransfersTable function**

Add in the JavaScript section:

```javascript
function renderTransfersTable(data) {
    const tbody = document.getElementById('transfers-tbody');
    const todayMatchNos = window.todayMatchNos || [];

    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="19" class="no-results">No transfer data available</td></tr>';
        return;
    }

    const html = data.map(match => {
        const isToday = todayMatchNos.includes(match.match_no);
        const isPast = isMatchPast(match.date);
        const rowClass = isToday ? 'match-today' : (isPast ? 'match-past' : '');

        return `<tr class="${rowClass}">
            <td>${match.match_no}</td>
            <td>${match.date}</td>
            <td>${match.home}</td>
            <td>${match.away}</td>
            <td>${match.team1_gap}</td>
            <td>${match.team2_gap}</td>
            <td>${match.CSK || ''}</td>
            <td>${match.DC || ''}</td>
            <td>${match.GT || ''}</td>
            <td>${match.KKR || ''}</td>
            <td>${match.LSG || ''}</td>
            <td>${match.MI || ''}</td>
            <td>${match.PBKS || ''}</td>
            <td>${match.RCB || ''}</td>
            <td>${match.RR || ''}</td>
            <td>${match.SRH || ''}</td>
            <td>${match.total}</td>
            <td>${match.transfers}</td>
            <td>${match.scoring_players}</td>
        </tr>`;
    }).join('');

    tbody.innerHTML = html;
}

function isMatchPast(dateStr) {
    const matchDate = parseDate(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return matchDate < today;
}

function parseDate(dateStr) {
    // Parse "28-Mar-26" format
    const months = { 'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
                     'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11 };
    const parts = dateStr.split('-');
    const day = parseInt(parts[0]);
    const month = months[parts[1]];
    const year = 2000 + parseInt(parts[2]);
    return new Date(year, month, day);
}
```

**Step 2: Run and verify**

```bash
python3 fetch_players.py
# Open players.html, click Transfers tab
```

Expected: Table populated with 70 rows of match data

**Step 3: Commit**

```bash
git add fetch_players.py
git commit -m "Implement renderTransfersTable function"
```

---

### Task 4: Add CSS Styling for Transfers Tab

**Files:**
- Modify: `fetch_players.py` (CSS in HTML template)

**Step 1: Add match status styles**

In the `<style>` section, add:

```css
/* Transfers tab table */
.transfers-table {
    width: 100%;
    border-collapse: collapse;
    background: rgba(255, 255, 255, 0.05);
}

.transfers-table th,
.transfers-table td {
    padding: 12px 8px;
    text-align: left;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.transfers-table th {
    background: rgba(240, 165, 0, 0.2);
    color: #f0a500;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
}

.transfers-table th:hover {
    background: rgba(240, 165, 0, 0.3);
}

.transfers-table tbody tr:hover {
    background: rgba(255, 255, 255, 0.05);
}

/* Match status indicators */
.match-today {
    border-left: 4px solid #f0a500 !important;
    background: rgba(240, 165, 0, 0.15) !important;
}

.match-today td {
    border-left: 1px solid rgba(240, 165, 0, 0.3);
}

.match-past {
    opacity: 0.5;
}

.match-past td {
    color: rgba(255, 255, 255, 0.6);
}

/* Table container for horizontal scroll */
.table-container {
    overflow-x: auto;
    max-height: 70vh;
    overflow-y: auto;
}
```

**Step 2: Run and verify**

```bash
python3 fetch_players.py
# Open players.html, click Transfers tab
```

Expected:
- Today's matches have gold left border and background
- Past matches are greyed out (50% opacity)
- Table scrolls horizontally if needed

**Step 3: Commit**

```bash
git add fetch_players.py
git commit -m "Add CSS styling for Transfers tab"
```

---

### Task 5: Implement Column Sorting

**Files:**
- Modify: `fetch_players.py` (JavaScript in HTML template)

**Step 1: Add sortTransfers function**

```javascript
let transfersSortField = 'match_no';
let transfersSortDir = 'asc';

function sortTransfers(field) {
    if (transfersSortField === field) {
        transfersSortDir = transfersSortDir === 'asc' ? 'desc' : 'asc';
    } else {
        transfersSortField = field;
        transfersSortDir = 'asc';
    }

    const data = window.transfersData || [];
    const sorted = [...data].sort((a, b) => {
        let aVal = a[field];
        let bVal = b[field];

        // Handle numeric vs string comparison
        if (field === 'match_no' || field === 'total' || field === 'transfers' || field === 'scoring_players') {
            aVal = parseInt(aVal) || 0;
            bVal = parseInt(bVal) || 0;
            return transfersSortDir === 'asc' ? aVal - bVal : bVal - aVal;
        }

        aVal = (aVal || '').toString().toLowerCase();
        bVal = (bVal || '').toString().toLowerCase();
        return transfersSortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });

    window.transfersData = sorted;
    renderTransfersTable(sorted);
}
```

**Step 2: Run and verify**

```bash
python3 fetch_players.py
# Open players.html, click Transfers tab, click column headers
```

Expected: Clicking headers sorts ascending/descending

**Step 3: Commit**

```bash
git add fetch_players.py
git commit -m "Add column sorting for Transfers tab"
```

---

### Task 6: Update Documentation

**Files:**
- Modify: `README.md`, `specs.md`, `docs/plans/2026-03-31-ipl-players-dashboard-design.md`

**Step 1: Update README.md**

Add Transfers tab to the Features section:

```markdown
- **Four tabs**:
  - **All Players** - Full player list with filters and sorting
  - **Today's Match** - Side-by-side home/away team tables
  - **Next Match** - Side-by-side tables for all teams (upcoming match planning)
  - **Transfers** - Complete match-by-match transfer history with team-wise player counts
```

**Step 2: Update specs.md**

Add Transfers tab to the Dashboard Features section.

**Step 3: Update design doc**

Add Transfers tab architecture to `docs/plans/2026-03-31-ipl-players-dashboard-design.md`.

**Step 4: Commit**

```bash
git add README.md specs.md docs/plans/2026-03-31-ipl-players-dashboard-design.md
git commit -m "Document Transfers tab feature"
```

---

### Task 7: Final Verification

**Step 1: Run full test**

```bash
python3 fetch_players.py
# Open players.html in browser
```

**Step 2: Verify all tabs work**

- All Players: Shows players with filters
- Today's Match: Shows today's matches
- Next Match: Shows next match day matches
- Transfers: Shows 70 matches with highlighting

**Step 3: Push all changes**

```bash
git push
```

---

## Success Criteria

- [ ] Transfers tab displays all 70 matches
- [ ] Today's matches highlighted with gold border
- [ ] Past matches greyed out (50% opacity)
- [ ] All 19 columns visible and sortable
- [ ] Sidebar hidden when Transfers tab active
- [ ] Horizontal scroll works on mobile
- [ ] Documentation updated
