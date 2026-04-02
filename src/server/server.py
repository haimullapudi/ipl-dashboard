#!/usr/bin/env python3
"""Flask server for IPL Fantasy Players Dashboard."""

from flask import Flask, jsonify, send_from_directory
import json
import urllib.request
import http.cookiejar
from urllib.parse import unquote
import csv
from datetime import datetime, date, timedelta
import os

# Get the directory containing this script
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SERVER_DIR))  # Go up two levels to project root

# Set up paths relative to project root
CLIENT_DIR = os.path.join(PROJECT_ROOT, 'src', 'client')
SCHEDULE_FILE = os.path.join(PROJECT_ROOT, 'src', 'transfer_optimizer', 'ipl26.csv')
TRANSFERS_FILE = os.path.join(PROJECT_ROOT, 'src', 'transfer_optimizer', 'ipl26_computed.csv')

# IPL 2026 season start date
SEASON_START_DATE = date(2026, 3, 28)

def load_env_vars():
    """Load environment variables from .env file."""
    env_path = os.path.join(PROJECT_ROOT, '.env')
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"Warning: Could not load .env: {e}")
    return env_vars

ENV = load_env_vars()
AUTH_TOKEN = ENV.get('MY11C_AUTH_TOKEN', '')
MY11_CLASSIC_GAME = ENV.get('MY11_CLASSIC_GAME', '')
USER_GUID = '70b39912-2a45-11f1-af7d-02ce50028faf'  # From MY11_CLASSIC_GAME

def get_current_gameday():
    """Calculate the current game day based on days since season start."""
    today = date.today()
    if today < SEASON_START_DATE:
        return 1
    delta = today - SEASON_START_DATE
    return delta.days + 1  # Day 1 is the start date itself

def get_players_api_url():
    """Get the API URL with dynamic tourgamedayId."""
    gameday = get_current_gameday()
    return f"https://fantasy.iplt20.com/classic/api/feed/gamedayplayers?lang=en&tourgamedayId={gameday}"

app = Flask(__name__, static_folder=CLIENT_DIR, static_url_path='')


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


@app.route('/')
def index():
    return send_from_directory(CLIENT_DIR, 'index.html')


@app.route('/api/players')
def get_players():
    api_url = get_players_api_url()
    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            raw_players = data.get('Data', {}).get('Value', {}).get('Players', [])
            gameday_players = []
            for p in raw_players:
                gameday_players.append({
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
            return jsonify({'gamedayPlayers': gameday_players})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/today-matches')
def get_today_matches():
    try:
        today_matches, next_matches = get_today_and_next_match()
        return jsonify({
            'today': today_matches,
            'next': next_matches,
            'today_match_nos': get_today_match_nos()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/transfers')
def get_transfers():
    try:
        transfers = load_transfers_data()
        return jsonify(transfers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/my-team')
def get_my_team():
    """Fetch user's fantasy team from authenticated IPL API."""
    gameday = get_current_gameday()
    url = f"https://fantasy.iplt20.com/classic/api/user/{USER_GUID}/team-get?gamedayId={gameday}"

    # Build cookie header manually for reliability
    cookie_header = f"my11c-authToken={AUTH_TOKEN}; my11_classic_game={MY11_CLASSIC_GAME}"

    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Cookie': cookie_header
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)
