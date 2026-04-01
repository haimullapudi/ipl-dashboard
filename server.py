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
    today_teams_list = [[m['home'], m['away']] for m in today_matches]

    # Find all matches on the next match day
    next_teams_list = []
    for match_date in sorted(matches_by_date.keys()):
        if match_date > today:
            next_teams_list = [[m['home'], m['away']] for m in matches_by_date[match_date]]
            break

    return today_teams_list, next_teams_list


def get_today_match_nos():
    """Get today's match numbers from schedule."""
    matches_by_date = load_match_schedule()
    today = date.today()
    today_matches = matches_by_date.get(today, [])
    return [m['match_no'] for m in today_matches]


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


@app.route('/api/today-matches')
def get_today_matches():
    """Get today's and next match day matches from schedule."""
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
    """Load transfers data from ipl26_computed.csv."""
    try:
        transfers = load_transfers_data()
        return jsonify(transfers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
