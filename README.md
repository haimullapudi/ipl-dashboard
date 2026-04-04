# IPL Dashboard

A Flask web application that displays IPL Fantasy players data fetched in real-time from the official API, along with a transfer optimizer for generating optimal transfer plans.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server
python3 src/server/server.py
```

The application will be available at `http://localhost:8000`

## Features

- **Real-time API fetching** - Data fetched on-demand from IPL Fantasy API
- **Four pages**:
  - **All Players** - Full player list with filters and sorting
  - **Today's Match** - Side-by-side home/away team tables
  - **Next Match** - Side-by-side tables for all teams (upcoming match planning)
  - **Transfers** - Complete match-by-match transfer history with team-wise player counts
- **Sortable columns** - Click any header to sort (default: Playing XI first)
- **Team filter** - Filter players by team
- **Playing XI filter** - Show only players in today's squad
- **Visual indicators**:
  - Green text = Playing XI
  - Bold text = Announced squad
- **Stats cards** - Total players, announced squad, avg points, playing XI count

## Recent Updates

### Venue Column in Transfers Tab
The Transfers page now includes a **Venue** column showing the match location (city extracted from stadium data).

### API-First Transfer Optimizer
The optimizer now defaults to fetching match data from the tour-fixtures API. CSV input is used only as a fallback when API calls fail.

## Dashboard Columns

| Column | Description |
|--------|-------------|
| Name | Player name (green if playing XI) |
| Team | Team short name |
| Skill | Player role (Batsman, Bowler, All Rounder, WK) |
| Value | Player value in credits |
| Sel By (%) | Percentage of users who selected this player |
| Cap (%) | Percentage who made this player captain |
| VCap (%) | Percentage who made this player vice-captain |
| Game Points | Points scored in current game day |
| Overall Points | Total season points |

## Deployment

### GitHub Pages (Recommended)

Deploy to GitHub Pages for free hosting. The site fetches fresh data via GitHub Actions.

1. **Enable GitHub Pages**:
   - Go to your repository **Settings > Pages**
   - Under "Source", select **GitHub Actions**

2. **Deploy**:
   - The workflow automatically deploys on push to `main`
   - Scheduled data updates run daily at 9:30-9:40 UTC (every 2 minutes)
   - Your site will be available at `https://your-username.github.io/ipl-dashboard/`

3. **Manual trigger**:
   - Go to **Actions** > "Deploy to GitHub Pages" > "Run workflow"

## Project Structure

```
ipl-dashboard/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── specs.md                           # Functional specifications
├── .github/                           # GitHub Actions workflows
└── src/
    ├── client/                        # Frontend files
    │   ├── index.html                 # All Players page (main entry)
    │   ├── todays-match.html          # Today's Match page
    │   ├── next-match.html            # Next Match page
    │   ├── transfers.html             # Transfers page
    │   ├── css/
    │   │   └── styles.css             # Shared styles
    │   └── js/
    │       ├── shared.js              # Shared utilities
    │       ├── all-players.js         # All Players logic
    │       ├── todays-match.js        # Today's Match logic
    │       ├── next-match.js          # Next Match logic
    │       └── transfers.js           # Transfers logic
    ├── server/
    │   └── server.py                  # Flask server with API endpoints
    ├── transfer_optimizer/            # Transfer optimizer module
    │   ├── README.md                  # Optimizer documentation
    │   ├── ipl_optimizer.py           # Main optimizer script
    │   ├── test_optimizer.py          # Test suite
    │   ├── ipl26.csv                  # Input match schedule
    │   └── ipl26_computed.csv         # Computed output
    └── utils/
        └── fetch_players.py           # Optional pre-fetch utility
docs/
    └── plans/                         # Design documents
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve main HTML page |
| `/api/players` | GET | Fetch players from IPL Fantasy API |
| `/api/today-matches` | GET | Get today's and next match info |
| `/api/transfers` | GET | Get transfer history data |
| `/api/health` | GET | Health check endpoint |

## Transfer Optimizer

The project includes a transfer optimizer that generates optimal transfer plans across the 70-match IPL league stage using a total budget of 160 transfers.

See [src/transfer_optimizer/README.md](src/transfer_optimizer/README.md) for details on:
- How the beam search optimization works
- Input/output file formats
- Command line options
- Running the optimizer and tests

## Utility Scripts

### fetch_players.py

Optional utility to pre-fetch API data (useful for offline use or backups):

```bash
python3 src/utils/fetch_players.py
```

Note: The web app fetches data dynamically from the API, so this script is optional.

## License

MIT License
