// All Players Tab
let playersData = null;
let currentSort = { field: 'isPlaying', dir: 'desc', type: 'boolean' };
let sortedPlayers = [];

async function loadData() {
    try {
        // Fetch from static JSON (for GitHub Pages)
        const response = await fetch('api/players.json');
        if (!response.ok) throw new Error('Failed to fetch players');

        playersData = await response.json();

        // Update last updated time
        const now = new Date();
        document.getElementById('lastUpdated').textContent =
            'Last updated: ' + now.toLocaleString('en-US', {
                month: 'long', day: 'numeric', hour: 'numeric', minute: '2-digit'
            });

        initStats();
        initLegend();
        refreshPlayers();
    } catch (error) {
        console.error('Error loading data:', error);
        showError('playersBody', error.message);
    }
}

function initStats() {
    const players = playersData.gamedayPlayers || [];
    const totalPlayers = players.length;
    const announcedCount = players.filter(p => p.isAnnounced).length;
    const playingCount = players.filter(p => p.isPlaying).length;
    const avgPoints = players.length > 0
        ? (players.reduce((sum, p) => sum + (p.overallPoints || 0), 0) / players.length).toFixed(1)
        : 0;

    document.getElementById('statsSummary').innerHTML = `
        <div class="stat-card">
            <h3>${totalPlayers}</h3>
            <p>Total Players</p>
        </div>
        <div class="stat-card">
            <h3>${announcedCount}</h3>
            <p>Announced Squad</p>
        </div>
        <div class="stat-card">
            <h3>${avgPoints}</h3>
            <p>Avg Points</p>
        </div>
        <div class="stat-card">
            <h3>${playingCount}</h3>
            <p>Playing XI</p>
        </div>
    `;

    document.getElementById('totalCount').textContent = totalPlayers;
}

function initLegend() {
    document.getElementById('legend').innerHTML = `
        <div class="legend-item">
            <span class="legend-color green"></span>
            <span>Playing XI / High Points (>50)</span>
        </div>
        <div class="legend-item">
            <span class="legend-color yellow"></span>
            <span>Medium Points (20-50)</span>
        </div>
        <div class="legend-item">
            <span class="legend-color red"></span>
            <span>Low Points (<20)</span>
        </div>
    `;
}

function refreshPlayers() {
    const players = playersData.gamedayPlayers || [];
    sortedPlayers = sortPlayers(players, currentSort.field, currentSort.type);
    renderTable();
    document.getElementById('filteredCount').textContent = players.length;
}

function renderTable() {
    const tbody = document.getElementById('playersBody');

    if (sortedPlayers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="no-results">No players found</td></tr>';
        return;
    }

    tbody.innerHTML = sortedPlayers.map(p => `
        <tr data-team="${p.teamShortName || ''}" data-playing="${p.isPlaying ? '1' : '0'}">
            <td class="${p.isPlaying ? 'playing-player' : ''}">
                ${p.fullName || p.shortName || '-'}
                ${p.isImpactPlayer ? '<span class="impact-tag">IMP</span>' : ''}
            </td>
            <td>${p.teamShortName || '-'}</td>
            <td>${p.skillName || '-'}</td>
            <td>${formatNumber(p.value)}</td>
            <td>${formatPercent(p.selectedPer)}</td>
            <td>${formatPercent(p.capSelectedPer)}</td>
            <td>${formatPercent(p.vCapSelectedPer)}</td>
            <td>${formatNumber(p.gamedayPoints)}</td>
            <td class="${getPointsClass(p.overallPoints)}">${formatNumber(p.overallPoints)}</td>
        </tr>
    `).join('');

    applyFilters();
}

function applyFilters() {
    const teamFilter = document.getElementById('teamFilter').value;
    const playingXi = document.getElementById('playingXi').checked;
    const rows = document.querySelectorAll('#playersBody tr');

    let visibleCount = 0;

    rows.forEach(row => {
        const team = row.dataset.team;
        const isPlaying = row.dataset.playing === '1';

        let show = true;

        if (teamFilter && team !== teamFilter) {
            show = false;
        }

        if (playingXi && !isPlaying) {
            show = false;
        }

        row.classList.toggle('hidden', !show);
        if (show) visibleCount++;
    });

    document.getElementById('filteredCount').textContent = visibleCount;

    const table = document.getElementById('playersTable');
    if (visibleCount === 0) {
        let existingMsg = table.querySelector('.no-results');
        if (!existingMsg) {
            existingMsg = document.createElement('div');
            existingMsg.className = 'no-results';
            existingMsg.style.padding = '40px 20px';
            existingMsg.textContent = 'No players match the selected filters';
            table.appendChild(existingMsg);
        }
    } else {
        const existingMsg = table.querySelector('.no-results');
        if (existingMsg) existingMsg.remove();
    }
}

function resetFilters() {
    document.getElementById('teamFilter').value = '';
    document.getElementById('playingXi').checked = false;
    applyFilters();
}

document.addEventListener('DOMContentLoaded', loadData);
