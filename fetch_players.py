#!/usr/bin/env python3
"""
Fetch IPL Fantasy players data and generate a static HTML page.
Run this daily to update the player data.
"""

import json
import urllib.request
import csv
from datetime import datetime, date

API_URL = "https://fantasy.iplt20.com/classic/api/feed/gamedayplayers?lang=en&tourgamedayId=4"
PLAYERS_DATA_FILE = "players_data.json"
OUTPUT_HTML_FILE = "players.html"
SCHEDULE_FILE = "ipl26.csv"

def parse_date(date_str):
    """Parse date string like '28-Mar-26' to date object."""
    try:
        return datetime.strptime(date_str, '%d-%b-%y').date()
    except:
        return None

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

def get_today_and_next_match():
    """Get today's matches and next match day teams from schedule."""
    matches_by_date = load_match_schedule()
    today = date.today()

    # Find all today's matches
    today_matches = matches_by_date.get(today, [])
    today_teams_list = []
    for match in today_matches:
        today_teams_list.append([match['home'], match['away']])

    # Find all matches on the next match day (first date after today with matches)
    next_teams_list = []
    for match_date in sorted(matches_by_date.keys()):
        if match_date > today:
            for match in matches_by_date[match_date]:
                next_teams_list.append([match['home'], match['away']])
            break

    return today_teams_list, next_teams_list

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

def get_today_match_nos():
    """Get today's match number(s) from schedule."""
    matches_by_date = load_match_schedule()
    today = date.today()
    today_matches = matches_by_date.get(today, [])
    return [m['match_no'] for m in today_matches]

def fetch_players():
    """Fetch players data from IPL Fantasy API."""
    print(f"Fetching data from {API_URL}...")

    try:
        req = urllib.request.Request(
            API_URL,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            raw_data = json.loads(response.read().decode('utf-8'))

            # Extract players from the nested structure
            players_list = raw_data.get('Data', {}).get('Value', {}).get('Players', [])

            # Normalize the data structure to match expected format
            data = {
                '_fetched_at': datetime.now().isoformat(),
                '_tourgamedayId': 4,
                'gamedayPlayers': []
            }

            for p in players_list:
                # Map API fields to expected format
                player = {
                    'id': p.get('Id'),
                    'fullName': p.get('Name'),
                    'shortName': p.get('ShortName'),
                    'teamId': p.get('TeamId'),
                    'teamName': p.get('TeamName'),
                    'teamShortName': p.get('TeamShortName'),
                    'skillName': p.get('SkillName'),
                    'skillId': p.get('SkillId'),
                    'value': p.get('Value'),
                    'isActive': p.get('IsActive', 0) == 1,
                    'selectedPer': p.get('SelectedPer', 0),
                    'capSelectedPer': p.get('CapSelectedPer', 0),
                    'vCapSelectedPer': p.get('vCapSelectedPer', 0),
                    'gamedayPoints': p.get('GamedayPoints', 0),
                    'overallPoints': p.get('OverallPoints', 0),
                    'isPlaying': p.get('IsAnnounced') == 'P',
                    'isAnnounced': p.get('IsAnnounced') in ['P', 'NP'],
                }
                data['gamedayPlayers'].append(player)

            # Save raw data to JSON file
            with open(PLAYERS_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            player_count = len(data.get('gamedayPlayers', []))
            announced_count = sum(1 for p in data.get('gamedayPlayers', []) if p.get('isAnnounced'))

            print(f"✓ Successfully fetched {player_count} players")
            print(f"✓ {announced_count} players announced for today's squad")
            print(f"✓ Data saved to {PLAYERS_DATA_FILE}")

            return data

    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        return None

def generate_html(data):
    """Generate static HTML with embedded data."""
    print(f"Generating {OUTPUT_HTML_FILE}...")

    players_json = json.dumps(data, ensure_ascii=False)
    fetched_at = datetime.fromisoformat(data['_fetched_at']).strftime('%B %d, %Y at %I:%M %p')

    # Get today's and next match teams from schedule
    today_matches, next_matches = get_today_and_next_match()
    today_matches_json = json.dumps(today_matches)
    next_matches_json = json.dumps(next_matches)

    # Load transfers data and today's match numbers
    transfers_data = load_transfers_data()
    transfers_json = json.dumps(transfers_data)
    today_match_nos = get_today_match_nos()
    today_match_nos_json = json.dumps(today_match_nos)

    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IPL Fantasy Players - Today's Squad</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }
        .container { max-width: 1800px; margin: 0 auto; }
        .main-layout {
            display: grid;
            grid-template-columns: 1fr 320px;
            gap: 20px;
        }
        .main-layout.no-sidebar {
            grid-template-columns: 1fr;
        }
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .stats-summary {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        .stat-card h3 { font-size: 2rem; color: #f0a500; margin-bottom: 5px; }
        .stat-card p { color: #aaa; font-size: 0.9rem; }
        .data-info {
            background: rgba(240, 165, 0, 0.2);
            padding: 10px 20px;
            border-radius: 8px;
            margin-bottom: 0;
            text-align: center;
            color: #fbbf24;
        }
        .data-info .date { display: block; margin-bottom: 4px; font-size: 0.9rem; }
        .data-info .gameday { display: block; font-size: 0.9rem; opacity: 0.8; }
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 20px;
            position: sticky;
            top: 20px;
            align-self: start;
        }
        .filter-panel {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        .stats-summary {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        .filter-panel h3 {
            color: #f0a500;
            margin-bottom: 15px;
            font-size: 1.1rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .filter-group {
            margin-bottom: 20px;
        }
        .filter-group label {
            display: block;
            color: #aaa;
            font-size: 0.85rem;
            margin-bottom: 8px;
        }
        .filter-group select {
            width: 100%;
            padding: 10px 12px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: #fff;
            font-size: 0.95rem;
            cursor: pointer;
        }
        .filter-group select:focus {
            outline: none;
            border-color: #f0a500;
        }
        .filter-group select option {
            background: #1a1a2e;
            color: #fff;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            cursor: pointer;
        }
        .checkbox-group input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
            accent-color: #4ade80;
        }
        .checkbox-group span {
            color: #fff;
            font-size: 0.95rem;
        }
        .filter-stats {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        .filter-stats p {
            color: #aaa;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }
        .filter-stats .count {
            color: #f0a500;
            font-weight: 600;
            font-size: 1.2rem;
        }
        .reset-btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #f0a500, #ff8c00);
            border: none;
            border-radius: 8px;
            color: #1a1a2e;
            font-weight: 600;
            cursor: pointer;
            margin-top: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .reset-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(240, 165, 0, 0.4);
        }
        .table-container {
            overflow-x: auto;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
        thead { background: linear-gradient(135deg, #f0a500 0%, #ff8c00 100%); }
        th {
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            color: #1a1a2e;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.5px;
            white-space: nowrap;
            cursor: pointer;
            user-select: none;
            position: relative;
        }
        th:hover { background: rgba(240, 165, 0, 0.8); }
        th .sort-icon { margin-left: 5px; opacity: 0.5; }
        th:hover .sort-icon { opacity: 1; }
        th.sorted .sort-icon { opacity: 1; }
        tbody tr {
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            transition: background 0.3s ease;
        }
        tbody tr:hover { background: rgba(255, 255, 255, 0.1); }
        tbody tr.hidden { display: none; }
        td { padding: 12px; vertical-align: middle; }
        .team-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .announced-player {
            font-weight: 700 !important;
        }
        .playing-player {
            font-weight: 700 !important;
            color: #4ade80 !important;
            text-shadow: 0 0 10px rgba(74, 222, 128, 0.5);
        }
        .points-high { color: #4ade80; font-weight: 600; }
        .points-medium { color: #fbbf24; font-weight: 600; }
        .points-low { color: #9ca3af; }
        .selected-per-bar { display: flex; align-items: center; gap: 8px; }
        .bar-container {
            width: 80px;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
        }
        .bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #f0a500, #ff8c00);
            border-radius: 4px;
        }
        .legend {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .legend-item { display: flex; align-items: center; gap: 8px; }
        .legend-color { width: 20px; height: 20px; border-radius: 4px; }
        .legend-color.announced {
            background: #4ade80;
            box-shadow: 0 0 10px rgba(74, 222, 128, 0.5);
        }
        .legend-color.normal { background: #fff; }
        .no-results {
            text-align: center;
            padding: 40px;
            color: #aaa;
            font-size: 1.1rem;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 10px;
        }
        .sidebar.hidden {
            display: none;
        }
        .tab-btn {
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            border-radius: 8px;
            color: #aaa;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.3s;
        }
        .tab-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            color: #fff;
        }
        .tab-btn.active {
            background: linear-gradient(135deg, #f0a500, #ff8c00);
            color: #1a1a2e;
            font-weight: 600;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .match-players-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .team-table-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            overflow: hidden;
        }
        .team-table-header {
            background: linear-gradient(135deg, #f0a500 0%, #ff8c00 100%);
            padding: 15px;
            text-align: center;
        }
        .team-table-header h3 {
            color: #1a1a2e;
            font-size: 1.2rem;
            font-weight: 700;
            margin: 0;
        }
        .team-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
        }
        .team-table thead {
            background: rgba(240, 165, 0, 0.2);
        }
        .team-table th {
            padding: 10px 8px;
            text-align: left;
            font-weight: 600;
            color: #f0a500;
            font-size: 0.75rem;
            text-transform: uppercase;
        }
        .team-table td {
            padding: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            vertical-align: middle;
        }
        .team-table tbody tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        .team-table .playing-player {
            font-weight: 700 !important;
            color: #4ade80 !important;
            text-shadow: 0 0 8px rgba(74, 222, 128, 0.4);
        }
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
            white-space: nowrap;
        }
        .transfers-table th {
            background: rgba(240, 165, 0, 0.2);
            color: #f0a500;
            font-weight: 600;
            cursor: pointer;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
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
        @media (max-width: 1024px) {
            .main-layout {
                grid-template-columns: 1fr;
            }
            .sidebar {
                order: 2;
            }
            .match-players-layout {
                grid-template-columns: 1fr;
            }
        }
        @media (max-width: 768px) {
            header h1 { font-size: 1.5rem; }
            th, td { padding: 8px 6px; font-size: 0.85rem; }
            .team-badge { padding: 2px 6px; font-size: 0.75rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('all')">All Players</button>
            <button class="tab-btn" onclick="switchTab('match')">Today's Match</button>
            <button class="tab-btn" onclick="switchTab('next')">Next Match</button>
            <button class="tab-btn" onclick="switchTab('transfers')">Transfers</button>
        </div>
        <div class="main-layout">
            <div id="content" class="tab-content active"></div>
            <div id="match-content" class="tab-content"></div>
            <div id="next-match-content" class="tab-content"></div>
            <div id="transfers-content" class="tab-content"></div>
            <div class="sidebar">
                <div class="data-info">
                    <span class="date">Data fetched: ''' + fetched_at + '''</span>
                    <span class="gameday">Game Day ID: ''' + str(data['_tourgamedayId']) + '''</span>
                </div>
                <div class="filter-panel">
                    <h3>Filters</h3>
                <div class="filter-group">
                    <label for="teamFilter">Filter by Team</label>
                    <select id="teamFilter" onchange="applyFilters()">
                        <option value="">All Teams</option>
                        <option value="CSK">CSK</option>
                        <option value="DC">DC</option>
                        <option value="GT">GT</option>
                        <option value="KKR">KKR</option>
                        <option value="LSG">LSG</option>
                        <option value="MI">MI</option>
                        <option value="PBKS">PBKS</option>
                        <option value="RCB">RCB</option>
                        <option value="RR">RR</option>
                        <option value="SRH">SRH</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Display Options</label>
                    <label class="checkbox-group" style="cursor: pointer;">
                        <input type="checkbox" id="playingXi" onchange="applyFilters()">
                        <span>Show Playing XI Only</span>
                    </label>
                </div>
                <div class="filter-stats">
                    <p>Showing <span class="count" id="filteredCount">0</span> of <span class="count" id="totalCount">0</span> players</p>
                </div>
                <button class="reset-btn" onclick="resetFilters()">Reset Filters</button>
            </div>
                <div class="stats-summary" id="statsSummary"></div>
                <div class="legend" id="legend"></div>
            </div>
        </div>
    </div>
    <script>
        window.playersData = ''' + players_json + ''';
        window.todayMatches = ''' + today_matches_json + ''';
        window.nextMatches = ''' + next_matches_json + ''';
        window.transfersData = ''' + transfers_json + ''';
        window.todayMatchNos = ''' + today_match_nos_json + ''';

        const teamColors = {
            'CSK': '#f9cd08', 'DC': '#004c93', 'GT': '#1c2e4a',
            'KKR': '#3a225a', 'LSG': '#a6192e', 'MI': '#004ba0',
            'PBKS': '#ed1b24', 'RCB': '#ec1c24', 'RR': '#254aa5', 'SRH': '#f7a721'
        };

        function getTeamColor(team) { return teamColors[team] || '#666'; }
        function formatNumber(n) { return (n === null || n === undefined) ? '-' : n.toLocaleString(); }
        function formatPercent(n) { return (n === null || n === undefined) ? '-' : n.toFixed(1) + '%'; }
        function getPointsClass(p) { return p >= 100 ? 'points-high' : p >= 50 ? 'points-medium' : 'points-low'; }

        let currentSort = { field: 'isPlaying', direction: 'desc' };

        function sortPlayers(players, field, type) {
            const dir = currentSort.direction === 'asc' ? 1 : -1;
            return [...players].sort((a, b) => {
                let aVal = a[field];
                let bVal = b[field];
                if (type === 'string') {
                    return dir * (aVal || '').localeCompare(bVal || '');
                } else if (type === 'number') {
                    return dir * ((aVal || 0) - (bVal || 0));
                } else if (type === 'boolean') {
                    // For boolean: true (playing) should come first in desc mode
                    const aNum = aVal ? 1 : 0;
                    const bNum = bVal ? 1 : 0;
                    return dir === -1 ? (bNum - aNum) : (aNum - bNum);
                }
                return 0;
            });
        }

        let sortedPlayers = [];

        function renderTable(data) {
            const players = data.gamedayPlayers || [];
            const announcedCount = players.filter(p => p.isAnnounced).length;
            const playingCount = players.filter(p => p.isPlaying).length;
            const avgPoints = players.reduce((s, p) => s + (p.gamedayPoints || 0), 0) / players.length;
            const topScorer = players.reduce((max, p) => p.gamedayPoints > max.gamedayPoints ? p : max, players[0]);

            // Default sort by playing XI (descending)
            sortedPlayers = sortPlayers(players, currentSort.field, 'boolean');

            // Render stats to sidebar
            document.getElementById('statsSummary').innerHTML = `
                <div class="stat-card"><h3>${players.length}</h3><p>Total Players</p></div>
                <div class="stat-card"><h3>${announcedCount}</h3><p>Announced Squad</p></div>
                <div class="stat-card"><h3>${avgPoints.toFixed(1)}</h3><p>Avg Game Day Points</p></div>
                <div class="stat-card"><h3>${playingCount}</h3><p>Playing XI</p></div>
            `;

            // Render legend to sidebar
            document.getElementById('legend').innerHTML = `
                <div class="legend-item"><div class="legend-color announced"></div><span>Playing XI</span></div>
                <div class="legend-item"><div class="legend-color normal"></div><span>Not Playing</span></div>
            `;

            const tableHTML = `
                <div class="table-container">
                    <table id="playersTable">
                        <thead>
                            <tr>
                                <th data-sort="isPlaying" data-type="boolean" style="text-align:center;"><span style="color:#4ade80;">✓</span> <span class="sort-icon">⇅</span></th>
                                <th data-sort="fullName" data-type="string">Name <span class="sort-icon">⇅</span></th>
                                <th data-sort="teamShortName" data-type="string">Team <span class="sort-icon">⇅</span></th>
                                <th data-sort="skillName" data-type="string">Skill <span class="sort-icon">⇅</span></th>
                                <th data-sort="value" data-type="number">Value <span class="sort-icon">⇅</span></th>
                                <th data-sort="selectedPer" data-type="number">Sel By (%) <span class="sort-icon">⇅</span></th>
                                <th data-sort="capSelectedPer" data-type="number">Cap (%) <span class="sort-icon">⇅</span></th>
                                <th data-sort="vCapSelectedPer" data-type="number">VCap (%) <span class="sort-icon">⇅</span></th>
                                <th data-sort="gamedayPoints" data-type="number">Game Points <span class="sort-icon">⇅</span></th>
                                <th data-sort="overallPoints" data-type="number">Overall Points <span class="sort-icon">⇅</span></th>
                            </tr>
                        </thead>
                        <tbody id="playersBody">
                            ${sortedPlayers.map((p, idx) => `
                                <tr data-idx="${idx}" data-team="${p.teamShortName || ''}" data-announced="${p.isAnnounced ? '1' : '0'}" data-playing="${p.isPlaying ? '1' : '0'}">
                                    <td style="text-align:center;" class="${p.isPlaying ? 'playing-player' : ''}">${p.isPlaying ? '✓' : ''}</td>
                                    <td class="${p.isPlaying ? 'playing-player' : ''}${p.isAnnounced ? ' announced-player' : ''}">${p.fullName || p.shortName}</td>
                                    <td><span class="team-badge" style="background: ${getTeamColor(p.teamShortName)}; color: #fff;">${p.teamShortName || '-'}</span></td>
                                    <td>${p.skillName || '-'}</td>
                                    <td>${formatNumber(p.value)}</td>
                                    <td>
                                        <div class="selected-per-bar">
                                            <span>${formatPercent(p.selectedPer)}</span>
                                            <div class="bar-container">
                                                <div class="bar-fill" style="width: ${Math.min(p.selectedPer || 0, 100)}%"></div>
                                            </div>
                                        </div>
                                    </td>
                                    <td>${formatPercent(p.capSelectedPer)}</td>
                                    <td>${formatPercent(p.vCapSelectedPer)}</td>
                                    <td class="${getPointsClass(p.gamedayPoints)}">${formatNumber(p.gamedayPoints)}</td>
                                    <td class="${getPointsClass(p.overallPoints)}">${formatNumber(p.overallPoints)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;

            document.getElementById('content').innerHTML = tableHTML;

            // Initialize filter stats
            document.getElementById('totalCount').textContent = players.length;

            // Add click handlers for sorting
            document.querySelectorAll('th[data-sort]').forEach(th => {
                th.addEventListener('click', () => {
                    const field = th.dataset.sort;
                    const type = th.dataset.type;

                    // Toggle direction if same field, otherwise default to desc
                    if (currentSort.field === field) {
                        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
                    } else {
                        currentSort.field = field;
                        currentSort.direction = 'desc';
                    }

                    // Update sorted players and re-render
                    sortedPlayers = sortPlayers(players, field, type);

                    // Update visual indicators
                    document.querySelectorAll('th').forEach(h => h.classList.remove('sorted'));
                    th.classList.add('sorted');

                    // Re-render table body with sorted players
                    const tbody = document.getElementById('playersBody');
                    tbody.innerHTML = sortedPlayers.map((p, idx) => `
                        <tr data-idx="${idx}" data-team="${p.teamShortName || ''}" data-announced="${p.isAnnounced ? '1' : '0'}" data-playing="${p.isPlaying ? '1' : '0'}">
                            <td style="text-align:center;" class="${p.isPlaying ? 'playing-player' : ''}">${p.isPlaying ? '✓' : ''}</td>
                            <td class="${p.isPlaying ? 'playing-player' : ''}${p.isAnnounced ? ' announced-player' : ''}">${p.fullName || p.shortName}</td>
                            <td><span class="team-badge" style="background: ${getTeamColor(p.teamShortName)}; color: #fff;">${p.teamShortName || '-'}</span></td>
                            <td>${p.skillName || '-'}</td>
                            <td>${formatNumber(p.value)}</td>
                            <td>
                                <div class="selected-per-bar">
                                    <span>${formatPercent(p.selectedPer)}</span>
                                    <div class="bar-container">
                                        <div class="bar-fill" style="width: ${Math.min(p.selectedPer || 0, 100)}%"></div>
                                    </div>
                                </div>
                            </td>
                            <td>${formatPercent(p.capSelectedPer)}</td>
                            <td>${formatPercent(p.vCapSelectedPer)}</td>
                            <td class="${getPointsClass(p.gamedayPoints)}">${formatNumber(p.gamedayPoints)}</td>
                            <td class="${getPointsClass(p.overallPoints)}">${formatNumber(p.overallPoints)}</td>
                        </tr>
                    `).join('');

                    applyFilters();
                });
            });

            applyFilters();
        }

        function applyFilters() {
            const teamFilter = document.getElementById('teamFilter').value;
            const playingXi = document.getElementById('playingXi').checked;
            const rows = document.querySelectorAll('#playersBody tr');

            let visibleCount = 0;

            rows.forEach(row => {
                const team = row.dataset.team;
                const isPlaying = row.dataset.playing === '1';

                let show = true;

                // Apply team filter
                if (teamFilter && team !== teamFilter) {
                    show = false;
                }

                // Apply playing XI filter
                if (playingXi && !isPlaying) {
                    show = false;
                }

                row.classList.toggle('hidden', !show);
                if (show) visibleCount++;
            });

            // Update count
            document.getElementById('filteredCount').textContent = visibleCount;

            // Show no results message if needed
            const table = document.getElementById('playersTable');
            if (visibleCount === 0) {
                let existingMsg = table.querySelector('.no-results');
                if (!existingMsg) {
                    existingMsg = document.createElement('div');
                    existingMsg.className = 'no-results';
                    existingMsg.textContent = 'No players match the selected filters';
                    table.appendChild(existingMsg);
                }
            } else {
                const existingMsg = table.querySelector('.no-results');
                if (existingMsg) existingMsg.remove();
            }
        }

        function resetFilters() {
            document.getElementById('teamFilter').value = '';
            document.getElementById('playingXi').checked = false;
            applyFilters();
        }

        function switchTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            event.target.classList.add('active');

            // Hide sidebar for match and transfers tabs (no filters needed)
            const sidebar = document.querySelector('.sidebar');
            const mainLayout = document.querySelector('.main-layout');
            if (tab === 'match' || tab === 'next' || tab === 'transfers') {
                sidebar.classList.add('hidden');
                mainLayout.classList.add('no-sidebar');
            } else {
                sidebar.classList.remove('hidden');
                mainLayout.classList.remove('no-sidebar');
            }

            // Show appropriate content and render
            if (tab === 'all') {
                document.getElementById('content').classList.add('active');
                renderTable(window.playersData);
            } else if (tab === 'match') {
                document.getElementById('match-content').classList.add('active');
                renderTodayMatchTables(window.playersData);
            } else if (tab === 'next') {
                document.getElementById('next-match-content').classList.add('active');
                renderNextMatchTables(window.playersData);
            } else if (tab === 'transfers') {
                document.getElementById('transfers-content').classList.add('active');
                renderTransfersTable(window.transfersData);
            }
        }

        function renderSingleMatchTable(data, homeTeam, awayTeam) {
            const players = data.gamedayPlayers || [];

            // Group players by team
            const playersByTeam = {};
            players.forEach(p => {
                const team = p.teamShortName;
                if (team) {
                    if (!playersByTeam[team]) playersByTeam[team] = [];
                    playersByTeam[team].push(p);
                }
            });

            // Get players for both teams
            const homePlayers = playersByTeam[homeTeam] || [];
            const awayPlayers = playersByTeam[awayTeam] || [];

            // Check if playing XI is announced for these specific teams
            const homePlayingCount = homePlayers.filter(p => p.isPlaying).length;
            const awayPlayingCount = awayPlayers.filter(p => p.isPlaying).length;
            const playingXiAnnounced = homePlayingCount > 0 || awayPlayingCount > 0;

            const renderTeamTable = (teamName, teamPlayers, filterPlayingOnly) => {
                let displayPlayers = teamPlayers;
                if (filterPlayingOnly) {
                    displayPlayers = teamPlayers.filter(p => p.isPlaying);
                }

                const sortedPlayers = displayPlayers.sort((a, b) => {
                    if (a.isPlaying && !b.isPlaying) return -1;
                    if (!a.isPlaying && b.isPlaying) return 1;
                    return (b.overallPoints || 0) - (a.overallPoints || 0);
                });

                if (sortedPlayers.length === 0) {
                    return `
                        <div class="team-table-container">
                            <div class="team-table-header">
                                <h3>${teamName}</h3>
                            </div>
                            <div class="no-results" style="padding: 20px;">No players available</div>
                        </div>
                    `;
                }

                return `
                    <div class="team-table-container">
                        <div class="team-table-header">
                            <h3>${teamName}</h3>
                        </div>
                        <table class="team-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Skill</th>
                                    <th>Value</th>
                                    <th>Sel By (%)</th>
                                    <th>Cap (%)</th>
                                    <th>VCap (%)</th>
                                    <th>Overall Points</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${sortedPlayers.map(p => `
                                    <tr>
                                        <td class="${p.isPlaying ? 'playing-player' : ''}">${p.fullName || p.shortName}</td>
                                        <td>${p.skillName || '-'}</td>
                                        <td>${formatNumber(p.value)}</td>
                                        <td>${formatPercent(p.selectedPer)}</td>
                                        <td>${formatPercent(p.capSelectedPer)}</td>
                                        <td>${formatPercent(p.vCapSelectedPer)}</td>
                                        <td class="${getPointsClass(p.overallPoints)}">${formatNumber(p.overallPoints)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            };

            return `
                <div class="match-players-layout">
                    ${renderTeamTable(homeTeam, homePlayers, playingXiAnnounced)}
                    ${renderTeamTable(awayTeam, awayPlayers, playingXiAnnounced)}
                </div>
            `;
        }

        function renderTodayMatchTables(data) {
            const matches = window.todayMatches || [];
            if (matches.length === 0) {
                document.getElementById('match-content').innerHTML = `
                    <div class="table-container">
                        <div class="no-results">No matches scheduled for today</div>
                    </div>
                `;
                return;
            }

            const html = matches.map(match => renderSingleMatchTable(data, match[0], match[1])).join('<hr style="border: 1px solid rgba(255,255,255,0.1); margin: 30px 0;">');
            document.getElementById('match-content').innerHTML = html;
        }

        function renderNextMatchTables(data) {
            const matches = window.nextMatches || [];
            if (matches.length === 0) {
                document.getElementById('next-match-content').innerHTML = `
                    <div class="table-container">
                        <div class="no-results">No upcoming matches found</div>
                    </div>
                `;
                return;
            }

            const html = matches.map(match => renderSingleMatchTable(data, match[0], match[1])).join('<hr style="border: 1px solid rgba(255,255,255,0.1); margin: 30px 0;">');
            document.getElementById('next-match-content').innerHTML = html;
        }

        function parseMatchDate(dateStr) {
            // Parse "28-Mar-26" format
            const months = { 'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
                             'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11 };
            const parts = dateStr.split('-');
            const day = parseInt(parts[0]);
            const month = months[parts[1]];
            const year = 2000 + parseInt(parts[2]);
            return new Date(year, month, day);
        }

        function isMatchPast(dateStr) {
            const matchDate = parseMatchDate(dateStr);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            return matchDate < today;
        }

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

        function renderTransfersTable(data) {
            const tbody = document.getElementById('transfers-content');
            const todayMatchNos = window.todayMatchNos || [];

            if (!data || data.length === 0) {
                tbody.innerHTML = `
                    <div class="table-container">
                        <div class="no-results">No transfer data available</div>
                    </div>
                `;
                return;
            }

            const html = `
                <div class="table-container">
                    <table class="transfers-table">
                        <thead>
                            <tr>
                                <th onclick="sortTransfers('match_no')">Match No <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('date')">Date <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('home')">Home <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('away')">Away <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('team1_gap')">Gap-1 <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('team2_gap')">Gap-2 <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('CSK')">CSK <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('DC')">DC <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('GT')">GT <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('KKR')">KKR <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('LSG')">LSG <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('MI')">MI <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('PBKS')">PBKS <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('RCB')">RCB <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('RR')">RR <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('SRH')">SRH <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('total')">Total <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('transfers')">Transfers <span class="sort-icon">⇅</span></th>
                                <th onclick="sortTransfers('scoring_players')">Scoring <span class="sort-icon">⇅</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.map(match => {
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
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            `;

            tbody.innerHTML = html;
        }

        // Initialize with default tab
        const players = window.playersData.gamedayPlayers || [];
        sortedPlayers = sortPlayers(players, currentSort.field, 'boolean');
        renderTable(window.playersData);
        renderTodayMatchTables(window.playersData);
        renderNextMatchTables(window.playersData);
        renderTransfersTable(window.transfersData);
    </script>
</body>
</html>
'''

    with open(OUTPUT_HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ Generated {OUTPUT_HTML_FILE}")

def main():
    data = fetch_players()
    if data:
        generate_html(data)
        print(f"\n✓ Complete! Open {OUTPUT_HTML_FILE} in your browser.")
        print("  To update data daily, run: python3 fetch_players.py")
    else:
        print("\n✗ Failed to fetch data. Check your internet connection and try again.")

if __name__ == '__main__':
    main()
