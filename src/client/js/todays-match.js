// Today's Match Tab
let playersData = null;
let todayMatches = [];
let matchSortField = 'overallPoints';
let matchSortDir = 'desc';

async function loadData() {
    try {
        // Try API first, fall back to static JSON for GitHub Pages
        let playersRes, matchesRes;
        try {
            playersRes = await fetch('/api/players');
            matchesRes = await fetch('/api/today-matches');
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

    const homePlayingCount = homePlayers.filter(p => p.isPlaying).length;
    const awayPlayingCount = awayPlayers.filter(p => p.isPlaying).length;
    const homeHasPlaying = homePlayingCount > 0;
    const awayHasPlaying = awayPlayingCount > 0;

    const renderTeamTable = (teamName, teamPlayers, showPlayingOnly) => {
        let displayPlayers = teamPlayers;
        if (showPlayingOnly) {
            // Show only playing XI players (IsAnnounced = 'P')
            displayPlayers = teamPlayers.filter(p => p.isPlaying);
        } else {
            // Fall back to all announced players if no playing XI available
            displayPlayers = teamPlayers.filter(p => p.isAnnounced);
        }

        const sorted = [...displayPlayers].sort((a, b) => {
            // Playing XI always first
            if (a.isPlaying && !b.isPlaying) return -1;
            if (!a.isPlaying && b.isPlaying) return 1;

            // Then sort by selected field
            let aVal = a[matchSortField] || 0;
            let bVal = b[matchSortField] || 0;
            return matchSortDir === 'desc' ? bVal - aVal : aVal - bVal;
        });

        if (sorted.length === 0) {
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
                            <th class="sortable" onclick="sortMatchPlayers('value')">Value <span class="sort-icon">⇅</span></th>
                            <th>Sel By (%)</th>
                            <th>Cap (%)</th>
                            <th>VCap (%)</th>
                            <th class="sortable" onclick="sortMatchPlayers('overallPoints')">Overall Points <span class="sort-icon">⇅</span></th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sorted.map(p => `
                            <tr>
                                <td class="${p.isPlaying ? 'playing-player' : ''}">
                                    ${p.fullName || p.shortName}
                                    ${p.isImpactPlayer ? '<span class="impact-tag">IMP</span>' : ''}
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
            ${renderTeamTable(homeTeam, homePlayers, homeHasPlaying)}
            ${renderTeamTable(awayTeam, awayPlayers, awayHasPlaying)}
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
