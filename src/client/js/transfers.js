// Transfers Tab
let transfersData = null;
let todayMatchNos = [];

async function loadData() {
    try {
        // Try API first (for local dev server), fall back to static JSON (for GitHub Pages)
        let transfersRes, matchesRes;
        try {
            transfersRes = await fetch('/api/transfers');
            matchesRes = await fetch('/api/today-matches');
            if (!transfersRes.ok || !matchesRes.ok) {
                throw new Error('API not available');
            }
        } catch (e) {
            transfersRes = await fetch('api/transfers.json');
            matchesRes = await fetch('api/today-matches.json');
        }

        if (!transfersRes.ok || !matchesRes.ok) throw new Error('Failed to fetch data');

        transfersData = await transfersRes.json();
        const matchesData = await matchesRes.json();
        todayMatchNos = matchesData.today_match_nos || [];

        renderTransfersTable();
    } catch (error) {
        console.error('Error loading data:', error);
        showError('transfers-content', error.message);
    }
}

function renderTransfersTable() {
    const tbody = document.getElementById('transfers-content');

    if (!transfersData || transfersData.length === 0) {
        tbody.innerHTML = `
            <div class="table-container">
                <div class="no-results">No transfer data available</div>
            </div>
        `;
        return;
    }

    const html = `
        <div class="table-container">
            <table class="transfers-table">
                <thead>
                    <tr>
                        <th>Match No</th>
                        <th>Date</th>
                        <th>Home</th>
                        <th>Away</th>
                        <th>Gap-1</th>
                        <th>Gap-2</th>
                        <th>CSK</th>
                        <th>DC</th>
                        <th>GT</th>
                        <th>KKR</th>
                        <th>LSG</th>
                        <th>MI</th>
                        <th>PBKS</th>
                        <th>RCB</th>
                        <th>RR</th>
                        <th>SRH</th>
                        <th>Total</th>
                        <th>Transfers</th>
                        <th>Scoring</th>
                    </tr>
                </thead>
                <tbody>
                    ${transfersData.map(match => {
                        const isToday = todayMatchNos.includes(match.match_no);
                        const isPast = isMatchPast(match.date);
                        const isFreeHit = match.match_no === 38; // Free Hit booster match

                        let rowClass = '';
                        if (isFreeHit) {
                            rowClass = 'match-free-hit';
                        } else if (isToday) {
                            rowClass = 'match-today';
                        } else if (isPast) {
                            rowClass = 'match-past';
                        }

                        const tooltip = isFreeHit ? ' title="🚀 Free Hit Booster: Unlimited transfers (0 cost), all 11 players score. Squad resets to Match 37 lineup after this match."' : '';

                        return `<tr class="${rowClass}"${tooltip}>
                            <td>${match.match_no}</td>
                            <td>${match.date}</td>
                            <td>${match.home}</td>
                            <td>${match.away}</td>
                            <td>${match.team1_gap}</td>
                            <td>${match.team2_gap}</td>
                            <td>${match.CSK || ''}</td>
                            <td>${match.DC || ''}</td>
                            <td>${match.GT || ''}</td>
                            <td>${match.KKR || ''}</td>
                            <td>${match.LSG || ''}</td>
                            <td>${match.MI || ''}</td>
                            <td>${match.PBKS || ''}</td>
                            <td>${match.RCB || ''}</td>
                            <td>${match.RR || ''}</td>
                            <td>${match.total}</td>
                            <td>${match.transfers}</td>
                            <td>${match.scoring_players}</td>
                        </tr>`;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;

    tbody.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', loadData);
