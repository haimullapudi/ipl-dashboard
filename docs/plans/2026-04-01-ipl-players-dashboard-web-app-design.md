# IPL Players Dashboard - Web Application Design Document

## Overview

Transform the static IPL Fantasy Players Dashboard into a dynamic web application with a Flask backend server that fetches API data in real-time, eliminating the need for daily manual data updates and static JSON storage.

## Architecture

### System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Browser   │────▶│  Flask Server │────▶│  IPL Fantasy API │
│  (Frontend) │◀────│   (Backend)   │◀────│  (External API)  │
└─────────────┘     └──────────────┘     └──────────────────┘
       │                    │
       │                    ▼
       │            ┌──────────────┐
       └────────────│  ipl26.csv   │
                    │  ipl26_      │
                    │  computed.csv│
                    └──────────────┘
```

### Data Flow

1. **Page Load:** Browser requests `/` from Flask server
2. **HTML Serve:** Server returns `index.html` template
3. **API Calls:** Frontend JavaScript fetches data via `/api/*` endpoints
4. **Proxy:** Flask server fetches from IPL Fantasy API using urllib (bypasses CORS)
5. **Render:** Frontend receives JSON and renders tables dynamically

## Backend Design

### Technology Stack

- **Framework:** Flask 3.x
- **HTTP Client:** urllib (standard library, no CORS restrictions)
- **JSON:** json (standard library)
- **CSV:** csv (standard library)
- **Server:** Flask development server (local) / gunicorn (production)

### File Structure

```
ipl/
├── server.py              # Flask backend server
├── fetch_players.py       # Keep for standalone CLI usage
├── players.html           # Modified: Use fetch() API calls
├── ipl26.csv              # Match schedule
├── ipl26_computed.csv     # Transfer optimizer output
├── requirements.txt       # Python dependencies
├── Procfile               # Railway/Render deployment config
├── .gitignore             # Exclude __pycache__, .env, etc.
└── docs/plans/
    └── 2026-04-01-ipl-players-dashboard-web-app-design.md
```

### API Endpoints

| Route | Method | Response | Description |
|-------|--------|----------|-------------|
| `/` | GET | HTML | Serve main dashboard page |
| `/api/players` | GET | JSON | Players data from IPL Fantasy API |
| `/api/today-matches` | GET | JSON | Today's matches from CSV schedule |
| `/api/next-matches` | GET | JSON | Next match day matches from CSV |
| `/api/transfers` | GET | JSON | Transfer data from ipl26_computed.csv |
| `/api/health` | GET | JSON | Health check endpoint |

### Endpoint Implementation

#### `/api/players`
```python
@app.route('/api/players')
def get_players():
    """Fetch players data from IPL Fantasy API."""
    API_URL = "https://fantasy.iplt20.com/classic/api/feed/gamedayplayers?lang=en&tourgamedayId=5"
    req = urllib.request.Request(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### `/api/today-matches`
```python
@app.route('/api/today-matches')
def get_today_matches():
    """Get today's matches from schedule CSV."""
    # Use existing load_match_schedule() and get_today_and_next_match()
    today_matches, next_matches = get_today_and_next_match()
    return jsonify({
        'today': today_matches,
        'next': next_matches
    })
```

#### `/api/transfers`
```python
@app.route('/api/transfers')
def get_transfers():
    """Load transfers data from ipl26_computed.csv."""
    # Use existing load_transfers_data()
    transfers = load_transfers_data()
    return jsonify(transfers)
```

#### `/api/health`
```python
@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })
```

## Frontend Changes

### Current Implementation (Static)
```javascript
window.playersData = {/* embedded JSON */};
renderTable(window.playersData);
```

### New Implementation (Dynamic)
```javascript
// Loading state
function showLoading() {
    document.getElementById('content').innerHTML = `
        <div class="loading-spinner">Loading...</div>
    `;
}

// Fetch and render
async function loadPlayersData() {
    showLoading();
    try {
        const response = await fetch('/api/players');
        const data = await response.json();
        if (data.error) {
            showError(data.error);
        } else {
            renderTable(data);
        }
    } catch (error) {
        showError('Failed to load data');
    }
}

// Load all data on page ready
document.addEventListener('DOMContentLoaded', () => {
    loadPlayersData();
    loadTransfersData();
    loadMatchData();
});
```

### UI/UX Enhancements

1. **Loading Spinner:** Show while fetching data
2. **Error State:** Display error message with retry button
3. **Last Updated:** Show "Last updated: <timestamp>" in sidebar
4. **Auto-refresh:** Optional refresh button (manual trigger)

### CSS Additions

```css
/* Loading spinner */
.loading-spinner {
    text-align: center;
    padding: 50px;
    color: #f0a500;
    font-size: 1.2rem;
}

.loading-spinner::after {
    content: ' ⏳';
}

/* Error state */
.error-message {
    background: rgba(220, 38, 38, 0.2);
    border: 1px solid #dc2626;
    color: #fca5a5;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
}

.retry-btn {
    background: linear-gradient(135deg, #f0a500, #ff8c00);
    color: #1a1a2e;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    cursor: pointer;
    margin-top: 10px;
}

/* Last updated indicator */
.last-updated {
    font-size: 0.8rem;
    color: #aaa;
    margin-top: 5px;
}
```

## Error Handling

### API Errors

| Error | Handling |
|-------|----------|
| Timeout (>30s) | Show "API timeout" with retry button |
| API unavailable (5xx) | Show "API unavailable" message |
| Invalid JSON | Log error, show "Invalid data" message |
| Network error | Show "Network error" message |

### CSV Errors

| Error | Handling |
|-------|----------|
| File not found | Log warning, return empty array |
| Parse error | Log warning, return partial data |

### Error UI Component

```javascript
function showError(message) {
    return `
        <div class="table-container">
            <div class="error-message">
                <p>⚠️ ${message}</p>
                <button class="retry-btn" onclick="location.reload()">Retry</button>
            </div>
        </div>
    `;
}
```

## Deployment Configuration

### requirements.txt
```
Flask==3.0.0
gunicorn==21.2.0
```

### Procfile (Railway/Render)
```
web: gunicorn server:app --workers 2 --threads 4
```

### .gitignore
```
__pycache__/
*.pyc
.env
venv/
.DS_Store
players_data.json
```

### Environment Variables (Optional)
```
# .env file (local development)
FLASK_ENV=development
FLASK_PORT=5000
API_TIMEOUT=30
```

## Deployment Steps

### Local Development
```bash
pip install -r requirements.txt
python3 server.py
# Open http://localhost:5000
```

### Railway Deployment
1. Connect GitHub repository to Railway
2. Add `requirements.txt` and `Procfile`
3. Deploy automatically on push
4. Set environment variables if needed

### Render Deployment
1. Create new Web Service
2. Connect GitHub repository
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn server:app --workers 2 --threads 4`

## Success Metrics

- **Page Load Time:** < 3 seconds (including API fetch)
- **API Response Time:** < 2 seconds
- **Error Rate:** < 1% failed requests
- **UI Consistency:** Identical visual design to static version
- **Real-time Data:** Fresh data on every page load

## Migration Plan

1. **Create server.py** - Flask backend with all API endpoints
2. **Modify players.html** - Replace embedded JSON with fetch() calls
3. **Add loading/error states** - UX improvements
4. **Add deployment files** - requirements.txt, Procfile, .gitignore
5. **Test locally** - Verify all tabs and features work
6. **Deploy to Railway** - Set up production environment
7. **Update documentation** - README with new setup instructions

## Files to Modify/Create

| File | Action | Purpose |
|------|--------|---------|
| `server.py` | Create | Flask backend server |
| `players.html` | Modify | Use fetch() instead of embedded data |
| `fetch_players.py` | Keep | Standalone CLI usage |
| `requirements.txt` | Create | Python dependencies |
| `Procfile` | Create | Deployment config |
| `.gitignore` | Create/Update | Exclude cache files |
| `README.md` | Update | New setup and deployment instructions |

## Future Enhancements

- **Caching:** Cache API responses for 5 minutes to reduce IPL API calls
- **WebSockets:** Real-time updates during live matches
- **Rate Limiting:** Prevent API abuse
- **Analytics:** Track page views and popular players
- **PWA:** Offline support with cached data
