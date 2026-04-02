// Today's Match Tab
let playersData = null;
let todayMatches = [];
let matchSortField = 'overallPoints';
let matchSortDir = 'desc';

async function loadData() {
    try {
        // Try API first (for local dev server), fall back to static JSON (for GitHub Pages)
        let playersRes, matchesRes;
        try {
            playersRes = await fetch('/api/players');
            matchesRes = await fetch('/api/today-matches');
            if (!playersRes.ok || !matchesRes.ok) {
                throw new Error('API not available');
            }
        } catch (e) {
            playersRes = await fetch('api/players.json');
            matchesRes = await fetch('api/today-matches.json');
        }

        if (!playersRes.ok || !matchesRes.ok) throw new Error('Failed to fetch data');

        playersData = await playersRes.json();
        const matchesData = await matchesRes.json();
        todayMatches = matchesData.today || [];

        renderTodayMatchTables();
    } catch (error) {
        console.error('Error loading data:', error);
        showError('match-content', error.message);
    }
}

function sortMatchPlayers(field) {
    if (matchSortField === field) {
        matchSortDir = matchSortDir === 'asc' ? 'desc' : 'asc';
    } else {
        matchSortField = field;
        matchSortDir = 'desc';
    }
    renderTodayMatchTables();
}

function renderSingleMatchTable(homeTeam, awayTeam) {
    const players = playersData.gamedayPlayers || [];

    const playersByTeam = {};
    players.forEach(p => {
        const team = p.teamShortName;
        if (team) {
            if (!playersByTeam[team]) playersByTeam[team] = [];
            playersByTeam[team].push(p);
        }
    });

    const homePlayers = playersByTeam[homeTeam] || [];
    const awayPlayers = playersByTeam[awayTeam] || [];

    const renderTeamTable = (teamName, teamPlayers) => {
        // Show only playing XI players (P) first
        let displayPlayers = teamPlayers.filter(p => p.isPlaying);

        // If no playing XI available, show all announced players (P + NP)
        if (displayPlayers.length === 0) {
            displayPlayers = teamPlayers.filter(p => p.isAnnounced);
        }

        const sorted = [...displayPlayers].sort((a, b) => {
            let aVal = a[matchSortField] || 0;
            let bVal = b[matchSortField] || 0;
            return matchSortDir === 'desc' ? bVal - aVal : aVal - bVal;
        });

        if (sorted.length === 0) {
            return `
                <div class="team-table-container">
                    <table class="team-table">
                        <thead>
                            <tr><th colspan="7" class="team-name-header">${teamName}</th></tr>
                        </thead>
                    </table>
                    <div class="no-results" style="padding: 20px; text-align: center;">No players available</div>
                </div>
            `;
        }

        return `
            <div class="team-table-container">
                <table class="team-table">
                    <thead>
                        <tr><th colspan="7" class="team-name-header">${teamName}</th></tr>
                        <tr>
                            <th class="sortable" onclick="sortMatchPlayers('fullName')">Name <span class="sort-icon">⇅</span></th>
                            <th>Skill</th>
                            <th class="sortable" onclick="sortMatchPlayers('value')">Value <span class="sort-icon">⇅</span></th>
                            <th>Sel By (%)</th>
                            <th>Cap (%)</th>
                            <th>VCap (%)</th>
                            <th class="sortable" onclick="sortMatchPlayers('overallPoints')">Points <span class="sort-icon">⇅</span></th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sorted.map(p => `
                            <tr>
                                <td class="${p.isPlaying ? 'playing-player' : ''}">
                                    ${p.fullName || p.shortName}
                                    ${p.isImpactPlayer ? '<span class="impact-tag">IMP</span>' : ''}
                                    ${!p.isPlaying && p.isAnnounced ? '<span class="impact-tag" style="background: rgba(255,255,255,0.2); color: #aaa; border: 1px solid #aaa;">NP</span>' : ''}
                                </td>
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
            ${renderTeamTable(homeTeam, homePlayers)}
            ${renderTeamTable(awayTeam, awayPlayers)}
        </div>
    `;
}

function renderTodayMatchTables() {
    const container = document.getElementById('match-content');

    if (todayMatches.length === 0) {
        container.innerHTML = `
            <div class="table-container">
                <div class="no-results">No matches scheduled for today</div>
            </div>
        `;
        return;
    }

    const html = todayMatches.map(match =>
        renderSingleMatchTable(match[0], match[1])
    ).join('<hr style="border: 1px solid rgba(255,255,255,0.1); margin: 30px 0;">');

    container.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', loadData);
