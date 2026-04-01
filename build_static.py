#!/usr/bin/env python3
"""
Build static site for GitHub Pages deployment.
Fetches data from IPL API and generates static JSON files.
"""

import json
import urllib.request
import csv
from datetime import datetime, date
import os
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(SCRIPT_DIR, 'static')
API_URL = "https://fantasy.iplt20.com/classic/api/feed/gamedayplayers?lang=en"
SCHEDULE_FILE = os.path.join(SCRIPT_DIR, 'transfer_optimizer', 'ipl26.csv')
TRANSFERS_FILE = os.path.join(SCRIPT_DIR, 'transfer_optimizer', 'ipl26_computed.csv')

# IPL 2026 season start date
SEASON_START_DATE = date(2026, 3, 28)

def get_current_gameday():
    """Calculate the current game day based on days since season start."""
    today = date.today()
    if today < SEASON_START_DATE:
        return 1
    delta = today - SEASON_START_DATE
    return delta.days + 1

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%d-%b-%y').date()
    except:
        return None

def load_match_schedule():
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
    return [m['match_no'] for m in today_matches]

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

def fetch_players():
    gameday = get_current_gameday()
    url = f"{API_URL}&tourgamedayId={gameday}"
    print(f"Fetching players from {url}...")

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

    # Fetch and save players data
    players_data = fetch_players()
    if players_data:
        with open(os.path.join(api_dir, 'players.json'), 'w') as f:
            json.dump(players_data, f, indent=2)
        print(f"Saved {len(players_data.get('gamedayPlayers', []))} players")

    # Save match data
    today_matches, next_matches = get_today_and_next_match()
    matches_data = {
        'today': today_matches,
        'next': next_matches,
        'today_match_nos': get_today_match_nos()
    }
    with open(os.path.join(api_dir, 'today-matches.json'), 'w') as f:
        json.dump(matches_data, f, indent=2)
    print(f"Saved matches: {len(today_matches)} today, {len(next_matches)} next")

    # Save transfers data
    transfers = load_transfers_data()
    with open(os.path.join(api_dir, 'transfers.json'), 'w') as f:
        json.dump(transfers, f, indent=2)
    print(f"Saved {len(transfers)} transfer records")

    # Update JS to use static JSON
    print("\nBuild complete! Static files in:", STATIC_DIR)
    print("\nTo deploy to GitHub Pages:")
    print("1. Configure GitHub Pages to serve from /static folder")
    print("   OR")
    print("2. Move contents of /static to root and push to gh-pages branch")

if __name__ == '__main__':
    main()
