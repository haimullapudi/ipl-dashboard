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

function calculateOverallAverages() {
    let totalTransfers = 0;
    let totalScoring = 0;
    let matchCount = 0;

    for (let i = 1; i < transfersData.length; i++) {
        totalTransfers += parseInt(transfersData[i].transfers) || 0;
        totalScoring += parseInt(transfersData[i].scoring_players) || 0;
        matchCount++;
    }

    return {
        avgTransfers: matchCount > 0 ? (totalTransfers / matchCount).toFixed(2) : '0.00',
        avgScoring: matchCount > 0 ? (totalScoring / matchCount).toFixed(2) : '0.00'
    };
}

function renderTransfersTable() {
    const tbody = document.getElementById('transfers-content');
    const overallAvgs = calculateOverallAverages();

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
                        <th>No</th>
                        <th>Date</th>
                        <th>Venue</th>
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
                        <th>Transfers<br><span class="avg-subheader">Avg: ${overallAvgs.avgTransfers}</span></th>
                        <th>Cumm.<br>Transfers</th>
                        <th>Scoring<br><span class="avg-subheader">Avg: ${overallAvgs.avgScoring}</span></th>
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

                        return `<tr class="${rowClass}">
                            <td>${match.match_no}</td>
                            <td>${match.date}</td>
                            <td>${match.venue || ''}</td>
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
                            <td>${match.SRH || ''}</td>
                            <td>${match.total}</td>
                            <td>${match.transfers}</td>
                            <td>${match.cumm_transfers || ''}</td>
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
