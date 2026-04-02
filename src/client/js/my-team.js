// My Team Tab
let myTeamData = null;
let playersData = null;
let todayMatches = [];
let matchSortField = 'overallPoints';
let matchSortDir = 'desc';

function sortMatchPlayers(field) {
    if (matchSortField === field) {
        matchSortDir = matchSortDir === 'asc' ? 'desc' : 'asc';
    } else {
        matchSortField = field;
        matchSortDir = 'desc';
    }
    renderMyTeam();
}

async function loadData() {
    try {
        let myTeamRes, playersRes, matchesRes;
        try {
            myTeamRes = await fetch('/api/my-team');
            playersRes = await fetch('/api/players');
            matchesRes = await fetch('/api/today-matches');
            if (!myTeamRes.ok || !playersRes.ok || !matchesRes.ok) {
                throw new Error('API not available');
            }
        } catch (e) {
            myTeamRes = await fetch('api/my-team.json');
            playersRes = await fetch('api/players.json');
            matchesRes = await fetch('api/today-matches.json');
        }

        if (!myTeamRes.ok || !playersRes.ok || !matchesRes.ok) {
            throw new Error('Failed to fetch data');
        }

        myTeamData = await myTeamRes.json();
        playersData = await playersRes.json();
        const matchesData = await matchesRes.json();
        todayMatches = matchesData.today || [];

        renderMyTeam();
    } catch (error) {
        console.error('Error loading data:', error);
        showError('my-team-content', error.message);
    }
}

function renderMyTeam() {
    const container = document.getElementById('my-team-content');

    // Extract team info from API response
    const teamInfo = myTeamData?.Data?.Value;
    if (!teamInfo) {
        container.innerHTML = '<div class="error-message">No team data available</div>';
        return;
    }

    const teamName = 'My Team';  // Use static name since API doesn't provide it
    const playerIds = teamInfo.plyid || [];
    const captainId = teamInfo.mcapt;
    const viceCaptainId = teamInfo.vcapt;

    // Match player IDs with gameday players data
    const allPlayers = playersData?.gamedayPlayers || [];
    const myTeamPlayers = allPlayers.filter(p => playerIds.includes(p.id));

    console.log('Player IDs:', playerIds);
    console.log('My team players found:', myTeamPlayers.length);
    console.log('Captain ID:', captainId, 'VC ID:', viceCaptainId);

    // Group players by skill (matching API skill names)
    const skillOrder = ['WICKET KEEPER', 'BATSMAN', 'ALL ROUNDER', 'BOWLER'];
    const skillDisplayNames = {
        'WICKET KEEPER': 'Wicket-Keeper',
        'BATSMAN': 'Batsman',
        'ALL ROUNDER': 'All Rounder',
        'BOWLER': 'Bowler'
    };
    const playersBySkill = {};
    skillOrder.forEach(skill => {
        playersBySkill[skill] = myTeamPlayers.filter(p => p.skillName === skill);
    });

    // Render My Team section (simplified cards)
    const renderMyTeamSection = () => {
        let html = `<div class="team-table-container"><div class="team-table-header"><h3>${teamName}</h3></div><div class="my-team-list">`;

        skillOrder.forEach(skill => {
            const players = playersBySkill[skill] || [];
            if (players.length > 0) {
                html += `<div class="skill-group"><h4>${skillDisplayNames[skill]}</h4>`;
                players.forEach(p => {
                    const isCaptain = p.id === captainId;
                    const isViceCaptain = p.id === viceCaptainId;
                    const cvTag = isCaptain ? '<span class="cv-tag captain">C</span>' :
                                  isViceCaptain ? '<span class="cv-tag vice-captain">VC</span>' : '';
                    const teamTag = p.teamShortName ? `<span class="team-tag team-${p.teamShortName}">${p.teamShortName}</span>` : '';
                    html += `
                        <div class="my-team-player">
                            <span class="player-name">${p.fullName || p.shortName}${teamTag}</span>
                            ${cvTag}
                            <span class="player-value">${formatNumber(p.value)}</span>
                        </div>
                    `;
                });
                html += '</div>';
            }
        });

        html += '</div></div>';
        return html;
    };

    // Render Home/Away teams (reuse today's match logic)
    const renderMatchTeams = () => {
        if (todayMatches.length === 0) {
            return '<div class="no-results">No matches scheduled for today</div>';
        }

        return todayMatches.map(match => {
            const homeTeam = match[0];
            const awayTeam = match[1];

            const playersByTeam = {};
            allPlayers.forEach(p => {
                const team = p.teamShortName;
                if (team) {
                    if (!playersByTeam[team]) playersByTeam[team] = [];
                    playersByTeam[team].push(p);
                }
            });

            const renderTeamTable = (teamName, teamPlayers) => {
                // Show only playing XI players (P) first
                let displayPlayers = teamPlayers.filter(p => p.isPlaying);

                // If no playing XI available, show all players (like next-match tab)
                if (displayPlayers.length === 0) {
                    displayPlayers = teamPlayers;
                }

                const sorted = [...displayPlayers].sort((a, b) => (b.overallPoints || 0) - (a.overallPoints || 0));

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
                <div class="match-teams-row">
                    ${renderTeamTable(homeTeam, playersByTeam[homeTeam] || [])}
                    ${renderTeamTable(awayTeam, playersByTeam[awayTeam] || [])}
                </div>
            `;
        }).join('');
    };

    container.innerHTML = `
        <div class="my-team-layout">
            <div class="my-team-section">${renderMyTeamSection()}</div>
            <div class="match-teams-section">
                ${renderMatchTeams()}
            </div>
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', loadData);
