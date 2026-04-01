#!/usr/bin/env python3
"""
Fetch IPL Fantasy players data and save to JSON.

Optional utility script - the web app fetches data dynamically from the API.
Use this script to:
- Pre-fetch data for offline use
- Create backups of API data
- Test API connectivity

Run: python3 src/utils/fetch_players.py
"""

import json
import urllib.request
import csv
from datetime import datetime, date
import os
import sys

# Adjust paths when running from utils/ directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

API_URL = "https://fantasy.iplt20.com/classic/api/feed/gamedayplayers?lang=en&tourgamedayId=5"
PLAYERS_DATA_FILE = os.path.join(PROJECT_ROOT, "players_data.json")
SCHEDULE_FILE = os.path.join(PROJECT_ROOT, "transfer_optimizer", "ipl26.csv")
TRANSFERS_FILE = os.path.join(PROJECT_ROOT, "transfer_optimizer", "ipl26_computed.csv")


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
            for match in matches_by_date[match_date]:
                next_teams_list.append([match['home'], match['away']])
            break

    return today_teams_list, next_teams_list


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


def get_today_match_nos():
    matches_by_date = load_match_schedule()
    today = date.today()
    today_matches = matches_by_date.get(today, [])
    return [m['match_no'] for m in today_matches]


def fetch_players():
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

            players_list = raw_data.get('Data', {}).get('Value', {}).get('Players', [])

            data = {
                '_fetched_at': datetime.now().isoformat(),
                '_tourgamedayId': 5,
                'gamedayPlayers': []
            }

            for p in players_list:
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


def main():
    data = fetch_players()
    if data:
        print("\n✓ Complete! Data saved for the web app.")
        print("  The web app fetches data dynamically from the API.")
        print("  Run the server with: python3 server.py")
        print("  Or use this script to pre-fetch data for offline use.")
    else:
        print("\n✗ Failed to fetch data. Check your internet connection and try again.")


if __name__ == '__main__':
    main()
