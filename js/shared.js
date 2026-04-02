// Shared utility functions for IPL Dashboard

function formatNumber(num) {
    if (num === null || num === undefined || num === '') return '-';
    return num.toString();
}

function formatPercent(num) {
    if (num === null || num === undefined || num === 0) return '-';
    return num.toFixed(1) + '%';
}

function getPointsClass(points) {
    if (points === null || points === undefined) return '';
    if (points > 50) return 'points-high';
    if (points > 20) return 'points-med';
    return 'points-low';
}

function sortPlayers(players, field, type) {
    return [...players].sort((a, b) => {
        let aVal = a[field];
        let bVal = b[field];

        if (type === 'boolean') {
            if (aVal && !bVal) return -1;
            if (!aVal && bVal) return 1;
            return 0;
        }

        if (type === 'number') {
            aVal = aVal || 0;
            bVal = bVal || 0;
            return bVal - aVal;
        }

        aVal = (aVal || '').toString().toLowerCase();
        bVal = (bVal || '').toString().toLowerCase();
        return aVal.localeCompare(bVal);
    });
}

function parseMatchDate(dateStr) {
    const months = { 'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
                     'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11 };
    const parts = dateStr.split('-');
    const day = parseInt(parts[0]);
    const month = months[parts[1]];
    const year = 2000 + parseInt(parts[2]);
    return new Date(year, month, day);
}

function isMatchPast(dateStr) {
    const matchDate = parseMatchDate(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return matchDate < today;
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="error-message">
            <p>Failed to load data: ${message}</p>
            <button class="retry-btn" onclick="loadData()">Retry</button>
        </div>
    `;
}

function showLoading(containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <span>Loading data...</span>
        </div>
    `;
}
