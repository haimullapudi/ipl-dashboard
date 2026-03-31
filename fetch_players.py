#!/usr/bin/env python3
"""
Fetch IPL Fantasy players data and generate a static HTML page.
Run this daily to update the player data.
"""

import json
import urllib.request
from datetime import datetime

API_URL = "https://fantasy.iplt20.com/classic/api/feed/gamedayplayers?lang=en&tourgamedayId=4"
PLAYERS_DATA_FILE = "players_data.json"
OUTPUT_HTML_FILE = "players.html"

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
                    'isAnnounced': p.get('IsAnnounced', False),
                    'isInjured': p.get('isInjured', '0') == '1',
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
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        header h1 { font-size: 2.5rem; margin-bottom: 10px; color: #f0a500; }
        header p { color: #aaa; font-size: 1.1rem; }
        .data-info {
            background: rgba(240, 165, 0, 0.2);
            padding: 10px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            color: #fbbf24;
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
        }
        tbody tr {
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            transition: background 0.3s ease;
        }
        tbody tr:hover { background: rgba(255, 255, 255, 0.1); }
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
        .stats-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
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
        @media (max-width: 768px) {
            header h1 { font-size: 1.5rem; }
            th, td { padding: 8px 6px; font-size: 0.85rem; }
            .team-badge { padding: 2px 6px; font-size: 0.75rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏏 IPL Fantasy Players</h1>
            <p>Today's Squad & Player Statistics</p>
        </header>
        <div class="data-info">Data fetched: ''' + fetched_at + ''' | Game Day ID: ''' + str(data['_tourgamedayId']) + '''</div>
        <div id="content"></div>
    </div>
    <script>
        window.playersData = ''' + players_json + ''';

        const teamColors = {
            'CSK': '#f9cd08', 'DC': '#004c93', 'GT': '#1c2e4a',
            'KKR': '#3a225a', 'LSG': '#a6192e', 'MI': '#004ba0',
            'PK': '#ed1b24', 'RCB': '#ec1c24', 'RR': '#254aa5', 'SRH': '#f7a721'
        };

        function getTeamColor(team) { return teamColors[team] || '#666'; }
        function formatNumber(n) { return (n === null || n === undefined) ? '-' : n.toLocaleString(); }
        function formatPercent(n) { return (n === null || n === undefined) ? '-' : n.toFixed(1) + '%'; }
        function getPointsClass(p) { return p >= 100 ? 'points-high' : p >= 50 ? 'points-medium' : 'points-low'; }

        function renderTable(data) {
            const players = data.gamedayPlayers || [];
            const announcedCount = players.filter(p => p.isAnnounced).length;
            const avgPoints = players.reduce((s, p) => s + (p.gamedayPoints || 0), 0) / players.length;
            const topScorer = players.reduce((max, p) => p.gamedayPoints > max.gamedayPoints ? p : max, players[0]);

            const summaryHTML = `
                <div class="stats-summary">
                    <div class="stat-card"><h3>${players.length}</h3><p>Total Players</p></div>
                    <div class="stat-card"><h3>${announcedCount}</h3><p>In Today's Squad</p></div>
                    <div class="stat-card"><h3>${avgPoints.toFixed(1)}</h3><p>Avg Game Day Points</p></div>
                    <div class="stat-card"><h3>${topScorer?.gamedayPoints || 0}</h3><p>Top Scorer (${topScorer?.shortName || '-'})</p></div>
                </div>
                <div class="legend">
                    <div class="legend-item"><div class="legend-color announced"></div><span>In Today's Squad (Announced)</span></div>
                    <div class="legend-item"><div class="legend-color normal"></div><span>Not Announced</span></div>
                </div>
            `;

            const tableHTML = `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th><th>Team</th><th>Skill</th><th>Value (Cr)</th>
                                <th>Active</th><th>Selected %</th><th>Captain %</th>
                                <th>VCaptain %</th><th>Game Points</th><th>Overall Points</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${players.map(p => `
                                <tr>
                                    <td class="${p.isAnnounced ? 'announced-player' : ''}">${p.isAnnounced ? '✓ ' : ''}${p.fullName || p.shortName}</td>
                                    <td><span class="team-badge" style="background: ${getTeamColor(p.teamShortName)}; color: #fff;">${p.teamShortName || '-'}</span></td>
                                    <td>${p.skillName || '-'}</td>
                                    <td>${formatNumber(p.value)}</td>
                                    <td>${p.isActive ? 'Yes' : 'No'}</td>
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

            document.getElementById('content').innerHTML = summaryHTML + tableHTML;
        }

        renderTable(window.playersData);
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
