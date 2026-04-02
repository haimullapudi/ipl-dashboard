// Next Match Tab
let playersData = null;
let nextMatches = [];
let matchSortField = 'overallPoints';
let matchSortDir = 'desc';

async function loadData() {
    try {
        // Try API first (for local dev server), fall back to static JSON (for GitHub Pages)
        let playersRes, fixturesRes;
        try {
            playersRes = await fetch('/api/players');
            fixturesRes = await fetch('/api/tour-fixtures');
            if (!playersRes.ok || !fixturesRes.ok) {
                throw new Error('API not available');
            }
        } catch (e) {
            playersRes = await fetch('api/players.json');
            fixturesRes = await fetch('api/tour-fixtures.json');
        }

        if (!playersRes.ok || !fixturesRes.ok) throw new Error('Failed to fetch data');

        playersData = await playersRes.json();
        const fixtures = await fixturesRes.json();

        // Calculate next matches from fixtures
        const { next } = getTodayAndNextMatches(fixtures);
        nextMatches = next;

        renderNextMatchTables();
    } catch (error) {
        console.error('Error loading data:', error);
        showError('next-match-content', error.message);
    }
}

function sortMatchPlayers(field) {
    if (matchSortField === field) {
        matchSortDir = matchSortDir === 'asc' ? 'desc' : 'asc';
    } else {
        matchSortField = field;
        matchSortDir = 'desc';
    }
    renderNextMatchTables();
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
        // For next match, show all players - match hasn't started yet
        const sorted = [...teamPlayers].sort((a, b) => {
            let aVal = a[matchSortField] || 0;
            let bVal = b[matchSortField] || 0;
            return matchSortDir === 'desc' ? bVal - aVal : aVal - bVal;
        });

        if (sorted.length === 0) {
            return `
                <div class="team-table-wrapper">
                    <h3 class="team-table-title">${teamName}</h3>
                    <div class="team-table-container">
                        <div class="no-results" style="padding: 20px; text-align: center;">No players available</div>
                    </div>
                </div>
            `;
        }

        return `
            <div class="team-table-wrapper">
                <h3 class="team-table-title">${teamName}</h3>
                <div class="team-table-container">
                    <table class="team-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Skill</th>
                                <th class="sortable" onclick="sortMatchPlayers('value')">Value <span class="sort-icon">⇅</span></th>
                                <th class="sortable" onclick="sortMatchPlayers('overallPoints')">Points <span class="sort-icon">⇅</span></th>
                                <th>Sel By (%)</th>
                                <th>Cap (%)</th>
                                <th>VCap (%)</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${sorted.map(p => `
                                <tr>
                                    <td>
                                        ${p.fullName || p.shortName}
                                        ${p.isImpactPlayer ? '<span class="impact-tag">IMP</span>' : ''}
                                    </td>
                                    <td>${p.skillName || '-'}</td>
                                    <td>${formatNumber(p.value)}</td>
                                    <td class="${getPointsClass(p.overallPoints)}">${formatNumber(p.overallPoints)}</td>
                                    <td>${formatPercent(p.selectedPer)}</td>
                                    <td>${formatPercent(p.capSelectedPer)}</td>
                                    <td>${formatPercent(p.vCapSelectedPer)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
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

function renderNextMatchTables() {
    const container = document.getElementById('next-match-content');

    if (nextMatches.length === 0) {
        container.innerHTML = `
            <div class="table-container">
                <div class="no-results">No upcoming matches found</div>
            </div>
        `;
        return;
    }

    const html = nextMatches.map(match =>
        renderSingleMatchTable(match[0], match[1])
    ).join('<hr style="border: 1px solid rgba(255,255,255,0.1); margin: 30px 0;">');

    container.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', loadData);
