// Today's Match Tab
let playersData = null;
let todayMatches = [];
let matchSortField = 'overallPoints';
let matchSortDir = 'desc';

async function loadData() {
    try {
        // Get fixtures from shared cache (single API call)
        const fixtures = await getTourFixtures();

        // Get current gameday from shared cache
        const gameday = await getCurrentGameday();

        // Fetch players from shared cache (5-min TTL)
        playersData = await getPlayers(gameday);

        // Calculate dynamic points thresholds based on all player data
        const players = playersData.gamedayPlayers || [];
        calculatePointsThresholds(players);
        console.log('Points thresholds:', getPointsThresholds());

        // Calculate today's matches from fixtures
        const { today } = getTodayAndNextMatches(fixtures);
        todayMatches = today;

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

        // If no playing XI available, show all players (like next-match tab)
        if (displayPlayers.length === 0) {
            displayPlayers = teamPlayers;
        }

        const sorted = [...displayPlayers].sort((a, b) => {
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
                                    <td class="${p.isPlaying ? 'playing-player' : ''}">
                                        ${p.fullName || p.shortName}
                                        ${p.isImpactPlayer ? '<span class="impact-tag">IMP</span>' : ''}
                                        ${p.is_FP ? '<span class="foreign-tag">FP</span>' : ''}
                                        ${!p.isPlaying && p.isAnnounced ? '<span class="impact-tag" style="background: rgba(255,255,255,0.2); color: #aaa; border: 1px solid #aaa;">NP</span>' : ''}
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
