#!/usr/bin/env python3
"""
Build static site for GitHub Pages deployment.
Fetches data from IPL API and generates static JSON files.
"""

import json
import urllib.request
import http.cookiejar
import csv
from datetime import datetime, date, timezone
import os
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = SCRIPT_DIR
STATIC_DIR = os.path.join(SCRIPT_DIR, 'static')
API_URL = "https://fantasy.iplt20.com/classic/api/feed/gamedayplayers?lang=en"
TRANSFERS_FILE = os.path.join(SCRIPT_DIR, 'src', 'transfer_optimizer', 'ipl26_computed.csv')

# Cache for tour fixtures
_tour_fixtures_cache = None

def get_current_gameday():
    """Get the current TourGamedayId based on UTC date and match fixtures."""
    global _tour_fixtures_cache

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today = now.date()

    if _tour_fixtures_cache is None:
        try:
            url = "https://fantasy.iplt20.com/classic/api/feed/tour-fixtures"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                _tour_fixtures_cache = data.get('Data', {}).get('Value', [])
        except Exception as e:
            print(f"Warning: Could not fetch tour-fixtures: {e}")
            _tour_fixtures_cache = []

    # Find the current gameday based on match dateTime (UTC)
    # MatchdateTime format: "03/28/2026 14:00:00"
    current_gameday = 1
    found_started_match = False

    for match in _tour_fixtures_cache:
        match_dt_str = match.get('MatchdateTime', '')
        if match_dt_str:
            try:
                match_dt = datetime.strptime(match_dt_str, '%m/%d/%Y %H:%M:%S')
                match_date = match_dt.date()

                # Only consider matches scheduled for today or earlier
                if match_date <= today:
                    tour_gameday_id = match.get('TourGamedayId', 1)
                    if tour_gameday_id:
                        if match_dt <= now:
                            # Match has started - use this gameday
                            if tour_gameday_id > current_gameday:
                                current_gameday = tour_gameday_id
                                found_started_match = True
                        elif not found_started_match:
                            # Match hasn't started yet, but it's today's earliest upcoming match
                            if tour_gameday_id > current_gameday:
                                current_gameday = tour_gameday_id
            except Exception as e:
                print(f"Warning: Could not parse match dateTime: {e}")

    return current_gameday

def load_match_schedule():
    """Load matches from tour-fixtures API."""
    global _tour_fixtures_cache

    if _tour_fixtures_cache is None:
        try:
            url = "https://fantasy.iplt20.com/classic/api/feed/tour-fixtures"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                _tour_fixtures_cache = data.get('Data', {}).get('Value', [])
        except Exception as e:
            print(f"Warning: Could not fetch tour-fixtures: {e}")
            _tour_fixtures_cache = []

    # Convert to match schedule format
    matches_by_date = {}
    for match in _tour_fixtures_cache:
        match_dt_str = match.get('MatchdateTime', '')
        if match_dt_str:
            try:
                match_dt = datetime.strptime(match_dt_str, '%m/%d/%Y %H:%M:%S')
                match_date = match_dt.date()
                if match_date not in matches_by_date:
                    matches_by_date[match_date] = []
                matches_by_date[match_date].append({
                    'home': match.get('HomeTeamShortName', 'Unknown'),
                    'away': match.get('AwayTeamShortName', 'Unknown'),
                    'match_no': match.get('TourGamedayId', 0),
                    'dateTime': match_dt
                })
            except Exception as e:
                print(f"Warning: Could not parse match dateTime: {e}")

    return matches_by_date

def get_today_and_next_match():
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

def get_today_match_nos():
    matches_by_date = load_match_schedule()
    today = date.today()
    today_matches = matches_by_date.get(today, [])
    return [m['match_no'] for m in today_matches if m.get('match_no', 0) > 0]

def load_transfers_data():
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


def fetch_my_team_data():
    """Fetch user's fantasy team data."""
    # First try environment variables (for GitHub Actions), then fall back to .env file
    auth_token = os.environ.get('MY11C_AUTH_TOKEN', '')
    my11_classic_game = os.environ.get('MY11_CLASSIC_GAME', '')
    user_guid = '70b39912-2a45-11f1-af7d-02ce50028faf'

    # If not in environment, try loading from .env file (for local builds)
    if not auth_token:
        env_path = os.path.join(PROJECT_ROOT, '.env')
        env_vars = {}
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
            auth_token = env_vars.get('MY11C_AUTH_TOKEN', '')
            my11_classic_game = env_vars.get('MY11_CLASSIC_GAME', '')
        except Exception as e:
            print(f"Warning: Could not load .env: {e}")

    if not auth_token:
        print("Warning: MY11C_AUTH_TOKEN not found - skipping my-team fetch")
        return None

    gameday = get_current_gameday()
    url = f"https://fantasy.iplt20.com/classic/api/user/{user_guid}/team-get?gamedayId={gameday}"
    print(f"[API] Fetching my-team from: {url}")

    # Build cookie header manually for reliability
    cookie_header = f"my11c-authToken={auth_token}; my11_classic_game={my11_classic_game}"

    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Cookie': cookie_header
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            team_info = data.get('Data', {}).get('Value', {})
            if team_info:
                print(f"[API] My Team fetched: TeamID={team_info.get('temid')}, Captain={team_info.get('mcapt')}, VC={team_info.get('vcapt')}, Players={len(team_info.get('plyid', []))}")
            return data
    except Exception as e:
        print(f"Warning: Could not fetch my-team: {e}")
        return None

def fetch_players():
    gameday = get_current_gameday()
    url = f"{API_URL}&tourgamedayId={gameday}"
    print(f"[API] Fetching players from: {url} (gamedayId={gameday})")

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            raw_players = data.get('Data', {}).get('Value', {}).get('Players', [])

            players = []
            for p in raw_players:
                players.append({
                    'id': p.get('Id'),
                    'fullName': p.get('Name'),
                    'shortName': p.get('ShortName'),
                    'teamId': p.get('TeamId'),
                    'teamShortName': p.get('TeamShortName'),
                    'skillName': p.get('SkillName'),
                    'skillId': p.get('SkillId'),
                    'value': p.get('Value'),
                    'selectedPer': p.get('SelectedPer'),
                    'capSelectedPer': p.get('CapSelectedPer'),
                    'vCapSelectedPer': p.get('VCapSelectedPer'),
                    'overallPoints': p.get('OverallPoints'),
                    'gamedayPoints': p.get('GamedayPoints'),
                    'isAnnounced': p.get('IsAnnounced') in ['P', 'NP'],
                    'isPlaying': p.get('IsAnnounced') == 'P',
                    'isInjured': p.get('isInjured') == '1',
                    'isActive': p.get('IsActive') == 1,
                    'playerDesc': p.get('PlayerDesc'),
                    'isImpactPlayer': p.get('isImpactPlayer') == 1
                })
            return {'gamedayPlayers': players}
    except Exception as e:
        print(f"Error fetching players: {e}")
        return None

def main():
    # Create static directory
    if os.path.exists(STATIC_DIR):
        shutil.rmtree(STATIC_DIR)
    os.makedirs(STATIC_DIR)

    # Copy client files
    client_dir = os.path.join(SCRIPT_DIR, 'src', 'client')
    for item in os.listdir(client_dir):
        src = os.path.join(client_dir, item)
        dst = os.path.join(STATIC_DIR, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # Create API directory and fetch data
    api_dir = os.path.join(STATIC_DIR, 'api')
    os.makedirs(api_dir, exist_ok=True)

    print("\n" + "="*60)
    print("BUILD SUMMARY - API Data Fetch")
    print("="*60)

    # Fetch and save tour-fixtures first (source of truth for matches and gameday)
    global _tour_fixtures_cache
    _tour_fixtures_cache = None  # Reset cache
    _ = get_current_gameday()  # This populates _tour_fixtures_cache
    if _tour_fixtures_cache:
        with open(os.path.join(api_dir, 'tour-fixtures.json'), 'w') as f:
            json.dump(_tour_fixtures_cache, f, indent=2)
        print(f"[SAVE] tour-fixtures.json - {len(_tour_fixtures_cache)} fixtures")

    # Fetch and save players data
    players_data = fetch_players()
    if players_data:
        player_count = len(players_data.get('gamedayPlayers', []))
        with open(os.path.join(api_dir, 'players.json'), 'w') as f:
            json.dump(players_data, f, indent=2)
        print(f"[SAVE] players.json - {player_count} players")

    # Save match data
    today_matches, next_matches = get_today_and_next_match()
    matches_data = {
        'today': today_matches,
        'next': next_matches,
        'today_match_nos': get_today_match_nos()
    }
    with open(os.path.join(api_dir, 'today-matches.json'), 'w') as f:
        json.dump(matches_data, f, indent=2)
    print(f"[SAVE] today-matches.json - {len(today_matches)} today, {len(next_matches)} next")

    # Save transfers data
    transfers = load_transfers_data()
    with open(os.path.join(api_dir, 'transfers.json'), 'w') as f:
        json.dump(transfers, f, indent=2)
    print(f"[SAVE] transfers.json - {len(transfers)} records")

    # Save my-team data
    my_team_data = fetch_my_team_data()
    if my_team_data:
        with open(os.path.join(api_dir, 'my-team.json'), 'w') as f:
            json.dump(my_team_data, f, indent=2)
        team_info = my_team_data.get('Data', {}).get('Value', {})
        if team_info:
            print(f"[SAVE] my-team.json - TeamID={team_info.get('temid')}, Captain={team_info.get('mcapt')}, VC={team_info.get('vcapt')}")
        else:
            print("[SAVE] my-team.json - No team data returned")
    else:
        print("[SKIP] my-team.json - No authentication token")

    print("="*60)
    print(f"Build complete! Static files in: {STATIC_DIR}")
    print("="*60)

if __name__ == '__main__':
    main()
