// Shared utility functions for IPL Dashboard

function formatNumber(num) {
    if (num === null || num === undefined || num === '') return '-';
    return num.toString();
}

function formatPercent(num) {
    if (num === null || num === undefined || num === 0) return '-';
    return num.toFixed(1) + '%';
}

// Dynamic thresholds for points classification (calculated from data)
let _pointsThresholds = { high: 50, med: 20 };

/**
 * Calculate percentile-based thresholds for points classification
 * Uses 67th percentile for high (top 33%) and 33rd percentile for med (bottom 33%)
 * @param {Array} players - Array of player objects with overallPoints
 */
function calculatePointsThresholds(players) {
    const points = players
        .map(p => p.overallPoints)
        .filter(p => p !== null && p !== undefined)
        .sort((a, b) => a - b); // Sort ascending: low to high

    if (points.length === 0) {
        _pointsThresholds = { high: 50, med: 20 };
        return _pointsThresholds;
    }

    // Calculate indices for percentiles (ascending order)
    // 33rd percentile: value below which 33% of data falls (med threshold)
    // 67th percentile: value below which 67% of data falls (high threshold)
    const medIdx = Math.floor(points.length * 0.33);
    const highIdx = Math.floor(points.length * 0.67);

    const medValue = points[medIdx] || 0;
    const highValue = points[highIdx] || 0;

    // Ensure high > med (in case of skewed data with many zeros)
    _pointsThresholds = {
        high: Math.max(highValue, medValue + 1),
        med: medValue
    };

    console.log('Points distribution:', {
        total: points.length,
        min: points[0],
        max: points[points.length - 1],
        medIdx: medIdx,
        highIdx: highIdx,
        medValue: medValue,
        highValue: highValue
    });

    return _pointsThresholds;
}

/**
 * Get points class based on dynamic percentile thresholds
 * @param {number} points - Player's overall points
 * @returns {string} CSS class name (points-high, points-med, points-low)
 */
function getPointsClass(points) {
    if (points === null || points === undefined) return '';
    if (points > _pointsThresholds.high) return 'points-high';
    if (points > _pointsThresholds.med) return 'points-med';
    return 'points-low';
}

/**
 * Get thresholds for display/debugging
 */
function getPointsThresholds() {
    return _pointsThresholds;
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

/**
 * Get current gameday from tour fixtures data
 * @param {Array} fixtures - Tour fixtures array
 * @returns {number} Current gameday ID
 */
function getCurrentGamedayFromFixtures(fixtures) {
    const now = new Date();
    now.setMilliseconds(0, 0);

    let currentGameday = 1;

    for (const match of fixtures) {
        const matchDtStr = match.MatchdateTime || '';
        if (matchDtStr) {
            try {
                // Parse "MM/DD/YYYY HH:MM:SS" format (UTC)
                const matchDt = new Date(matchDtStr + ' UTC');
                if (matchDt <= now) {
                    const tourGamedayId = match.TourGamedayId || 1;
                    if (tourGamedayId && tourGamedayId > currentGameday) {
                        currentGameday = tourGamedayId;
                    }
                }
            } catch (e) {
                console.warn('Could not parse match dateTime:', e);
            }
        }
    }

    return currentGameday;
}

/**
 * Get today's and next matches from tour fixtures
 * @param {Array} fixtures - Tour fixtures array
 * @returns {{today: Array, next: Array}} Today and next matches
 */
function getTodayAndNextMatches(fixtures) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const todayMatches = [];
    const futureMatches = [];

    for (const match of fixtures) {
        const matchDtStr = match.MatchdateTime || '';
        if (matchDtStr) {
            try {
                const matchDt = new Date(matchDtStr + ' UTC');
                const matchDate = new Date(matchDt.getFullYear(), matchDt.getMonth(), matchDt.getDate());

                if (matchDate.getTime() === today.getTime()) {
                    todayMatches.push({
                        home: match.HomeTeamShortName || 'Unknown',
                        away: match.AwayTeamShortName || 'Unknown',
                        match_no: match.TourGamedayId || 0,
                        dateTime: matchDt
                    });
                } else if (matchDate > today) {
                    futureMatches.push({
                        home: match.HomeTeamShortName || 'Unknown',
                        away: match.AwayTeamShortName || 'Unknown',
                        match_no: match.TourGamedayId || 0,
                        dateTime: matchDt
                    });
                }
            } catch (e) {
                console.warn('Could not parse match dateTime:', e);
            }
        }
    }

    // Sort future matches by date and get the earliest ones
    futureMatches.sort((a, b) => a.dateTime - b.dateTime);
    const nextDate = futureMatches.length > 0 ? futureMatches[0].dateTime : null;
    const nextMatches = futureMatches.filter(m =>
        m.dateTime.getDate() === nextDate?.getDate() &&
        m.dateTime.getMonth() === nextDate?.getMonth() &&
        m.dateTime.getFullYear() === nextDate?.getFullYear()
    );

    return {
        today: todayMatches.map(m => [m.home, m.away]),
        next: nextMatches.map(m => [m.home, m.away])
    };
}
