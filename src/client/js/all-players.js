// All Players Tab
let playersData = null;
let currentSort = { field: 'overallPoints', dir: 'desc', type: 'number' };
let sortedPlayers = [];

async function loadData() {
    try {
        // Get current gameday (uses cached fixtures - single API call)
        const gameday = await getCurrentGameday();

        // Fetch players from shared cache (5-min TTL)
        playersData = await getPlayers(gameday);

        // Calculate dynamic points thresholds based on player data
        const players = playersData.gamedayPlayers || [];
        calculatePointsThresholds(players);
        console.log('Points thresholds:', getPointsThresholds());

        // Update last updated time
        const now = new Date();
        document.getElementById('lastUpdated').textContent =
            'Last updated: ' + now.toLocaleString('en-US', {
                month: 'long', day: 'numeric', hour: 'numeric', minute: '2-digit'
            });

        // Display current gameday (uses cached fixtures)
        document.getElementById('gamedayDisplay').textContent = `Game Day ${gameday}`;

        initStats();
        initLegend(); // Called after calculatePointsThresholds so it has correct values
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
    const thresholds = getPointsThresholds();
    document.getElementById('legend').innerHTML = `
        <div class="legend-item">
            <span class="legend-color green"></span>
            <span>Playing XI / High Points (>${thresholds.high})</span>
        </div>
        <div class="legend-item">
            <span class="legend-color yellow"></span>
            <span>Medium Points (${thresholds.med}-${thresholds.high})</span>
        </div>
        <div class="legend-item">
            <span class="legend-color red"></span>
            <span>Low Points (<${thresholds.med})</span>
        </div>
    `;
}

function sortTable(field, type) {
    if (currentSort.field === field) {
        currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.field = field;
        currentSort.dir = 'desc';
    }
    currentSort.type = type;
    refreshPlayers();
}

function refreshPlayers() {
    const players = playersData.gamedayPlayers || [];
    sortedPlayers = sortPlayers(players, currentSort.field, currentSort.type);
    renderTable();
    updateSortIcons();
    document.getElementById('filteredCount').textContent = players.length;
}

function updateSortIcons() {
    // Remove sorted class from all sortable headers
    document.querySelectorAll('.sortable').forEach(th => {
        th.classList.remove('sorted');
        const icon = th.querySelector('.sort-icon');
        if (icon) icon.textContent = '⇅';
    });

    // Add sorted class to current sort column
    const currentHeader = document.querySelector(`[data-sort="${currentSort.field}"]`);
    if (currentHeader) {
        currentHeader.classList.add('sorted');
        const icon = currentHeader.querySelector('.sort-icon');
        if (icon) {
            icon.textContent = currentSort.dir === 'desc' ? '⇩' : '⇧';
        }
    }
}

function renderTable() {
    const tbody = document.getElementById('playersBody');

    if (sortedPlayers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="no-results">No players found</td></tr>';
        return;
    }

    // Update table header with sortable columns
    const thead = document.querySelector('#playersTable thead');
    if (thead) {
        thead.innerHTML = `
            <tr>
                <th>Name</th>
                <th>Team</th>
                <th>Skill</th>
                <th class="sortable" onclick="sortTable('value', 'number')" data-sort="value">Value <span class="sort-icon">⇅</span></th>
                <th>Sel By (%)</th>
                <th>Cap (%)</th>
                <th>VCap (%)</th>
                <th>Game Points</th>
                <th class="sortable" onclick="sortTable('overallPoints', 'number')" data-sort="overallPoints">Overall Points <span class="sort-icon">⇅</span></th>
            </tr>
        `;
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

        if (teamFilter && team.trim().toLowerCase() !== teamFilter.trim().toLowerCase()) {
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
