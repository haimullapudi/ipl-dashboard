// Shared utility functions for IPL Dashboard

// Cache for tour fixtures and gameday
let _fixturesCache = null;
let _fixturesTimestamp = null;
let _gamedayCache = null;

// Cache for players data with 5-minute TTL
let _playersCache = null;
let _playersTimestamp = null;
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

/**
 * Check if cached data is stale (older than TTL)
 * @param {number} timestamp - Cache timestamp
 * @returns {boolean} True if cache is stale
 */
function isCacheStale(timestamp) {
    if (!timestamp) return true;
    return (Date.now() - timestamp) > CACHE_TTL_MS;
}

/**
 * Fetch tour fixtures with caching (single API call across all modules)
 * Cache expires after 5 minutes
 * @returns {Promise<Array>} Tour fixtures array
 */
async function getTourFixtures() {
    if (_fixturesCache && !isCacheStale(_fixturesTimestamp)) {
        return _fixturesCache;
    }

    try {
        let response;
        try {
            response = await fetch('/api/tour-fixtures');
            if (!response.ok) {
                response = await fetch('api/tour-fixtures.json');
            }
        } catch (e) {
            response = await fetch('api/tour-fixtures.json');
        }

        if (response.ok) {
            _fixturesCache = await response.json();
            _fixturesTimestamp = Date.now();
            return _fixturesCache;
        }
    } catch (e) {
        console.warn('Could not fetch tour-fixtures:', e);
    }

    return _fixturesCache || [];
}

/**
 * Get current gameday (uses cached fixtures)
 * @returns {Promise<number>} Current gameday ID
 */
async function getCurrentGameday() {
    if (_gamedayCache !== null) {
        return _gamedayCache;
    }

    const fixtures = await getTourFixtures();
    _gamedayCache = getCurrentGamedayFromFixtures(fixtures);
    return _gamedayCache;
}

/**
 * Fetch players data with caching (5-minute TTL)
 * @param {number} gameday - Gameday ID for tourgamedayId param
 * @returns {Promise<Object>} Players data with gamedayPlayers array
 */
async function getPlayers(gameday) {
    if (_playersCache && !isCacheStale(_playersTimestamp)) {
        return _playersCache;
    }

    try {
        let response;
        try {
            response = await fetch(`/api/players?tourgamedayId=${gameday}`);
            if (!response.ok) {
                response = await fetch('api/players.json');
            }
        } catch (e) {
            response = await fetch('api/players.json');
        }

        if (response.ok) {
            const rawData = await response.json();
            // Handle API response format: Data.Value.Players
            let rawPlayers = rawData?.Data?.Value?.Players || [];
            let players = [];

            if (rawPlayers.length > 0) {
                // API format - transform IS_FP (string) to is_FP (boolean)
                players = rawPlayers.map(p => ({
                    ...p,
                    is_FP: p.IS_FP === '1'
                }));
            } else if (rawData.gamedayPlayers) {
                // Static file format - gamedayPlayers array
                // Check if is_FP already exists (from build_static.py)
                if (rawData.gamedayPlayers[0] && 'is_FP' in rawData.gamedayPlayers[0]) {
                    players = rawData.gamedayPlayers;
                } else {
                    // Fallback: try IS_FP field
                    players = rawData.gamedayPlayers.map(p => ({
                        ...p,
                        is_FP: p.IS_FP === '1'
                    }));
                }
            }

            _playersCache = {
                gamedayPlayers: players
            };
            _playersTimestamp = Date.now();
            return _playersCache;
        }
    } catch (e) {
        console.warn('Could not fetch players:', e);
    }

    return _playersCache || { gamedayPlayers: [] };
}

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
 * Calculate thresholds based on percentage of maximum points
 * High: > 60% of max points
 * Med: > 30% of max points
 * This accounts for players who don't play every match
 * @param {Array} players - Array of player objects with overallPoints
 */
function calculatePointsThresholds(players) {
    const points = players
        .map(p => p.overallPoints)
        .filter(p => p !== null && p !== undefined);

    if (points.length === 0) {
        _pointsThresholds = { high: 50, med: 20 };
        return _pointsThresholds;
    }

    const maxPoints = Math.max(...points);

    // Thresholds based on percentage of max points
    // High: > 60% of max (elite performers)
    // Med: > 30% of max (decent contributors)
    _pointsThresholds = {
        high: Math.round(maxPoints * 0.6),
        med: Math.round(maxPoints * 0.3)
    };

    console.log('Points thresholds:', {
        maxPoints: maxPoints,
        high: _pointsThresholds.high + ' (>60% of max)',
        med: _pointsThresholds.med + ' (>30% of max)'
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
    // Use UTC time for comparison (matches are scheduled in UTC)
    const now = new Date();
    const nowUtc = new Date(now.getTime() + (now.getTimezoneOffset() * 60000));
    const todayUtc = new Date(Date.UTC(nowUtc.getUTCFullYear(), nowUtc.getUTCMonth(), nowUtc.getUTCDate()));
    const endOfTodayUtc = new Date(todayUtc.getTime() + (23 * 60 * 60 * 1000) + (59 * 60 * 1000) + (59 * 1000));

    let currentGameday = 1;
    let foundStartedMatch = false;

    for (const match of fixtures) {
        const matchDtStr = match.MatchdateTime || '';
        if (matchDtStr) {
            try {
                // Parse "MM/DD/YYYY HH:MM:SS" format (UTC)
                const matchDt = new Date(matchDtStr + ' UTC');
                const matchDateUtc = new Date(Date.UTC(matchDt.getUTCFullYear(), matchDt.getUTCMonth(), matchDt.getUTCDate()));

                // Only consider matches scheduled for today or earlier (UTC comparison)
                if (matchDateUtc <= endOfTodayUtc) {
                    const tourGamedayId = match.TourGamedayId || 1;
                    if (tourGamedayId) {
                        if (matchDt <= nowUtc) {
                            // Match has started - use this gameday
                            if (tourGamedayId > currentGameday) {
                                currentGameday = tourGamedayId;
                                foundStartedMatch = true;
                            }
                        } else if (!foundStartedMatch) {
                            // Match hasn't started yet, but it's today's earliest upcoming match
                            if (tourGamedayId > currentGameday) {
                                currentGameday = tourGamedayId;
                            }
                        }
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

/**
 * Get the currently active match from today's matches (for multi-match days)
 * Returns the match that is in progress or the next upcoming match in UTC time
 * @param {Array} fixtures - Tour fixtures array
 * @returns {Object|null} Active match with home/away teams, or null if no active match
 */
function getActiveMatch(fixtures) {
    // Use UTC time for comparison (matches are scheduled in UTC)
    const now = new Date();
    const nowUtc = new Date(now.getTime() + (now.getTimezoneOffset() * 60000));
    const todayUtc = new Date(Date.UTC(nowUtc.getUTCFullYear(), nowUtc.getUTCMonth(), nowUtc.getUTCDate()));
    const endOfTodayUtc = new Date(todayUtc.getTime() + (23 * 60 * 60 * 1000) + (59 * 60 * 1000) + (59 * 1000));

    // First pass: find the match with the latest datetime that has started
    let latestStartedMatch = null;
    for (const match of fixtures) {
        const matchDtStr = match.MatchdateTime || '';
        if (matchDtStr) {
            try {
                const matchDt = new Date(matchDtStr + ' UTC');
                const matchDateUtc = new Date(Date.UTC(matchDt.getUTCFullYear(), matchDt.getUTCMonth(), matchDt.getUTCDate()));

                // Only consider today's matches
                if (matchDateUtc.getTime() === todayUtc.getTime()) {
                    // Check if match has started (match time <= now)
                    if (matchDt <= nowUtc) {
                        if (!latestStartedMatch || matchDt > latestStartedMatch.dateTime) {
                            latestStartedMatch = {
                                home: match.HomeTeamShortName || 'Unknown',
                                away: match.AwayTeamShortName || 'Unknown',
                                match_no: match.TourGamedayId || 0,
                                dateTime: matchDt
                            };
                        }
                    }
                }
            } catch (e) {
                console.warn('Could not parse match dateTime for active match:', e);
            }
        }
    }

    // If a started match found, return it (most recent match)
    if (latestStartedMatch) {
        return latestStartedMatch;
    }

    // Second pass: find all upcoming matches for today
    // If nowUtc is early enough that all matches are still upcoming, return all
    const upcomingMatches = [];
    for (const match of fixtures) {
        const matchDtStr = match.MatchdateTime || '';
        if (matchDtStr) {
            try {
                const matchDt = new Date(matchDtStr + ' UTC');
                const matchDateUtc = new Date(Date.UTC(matchDt.getUTCFullYear(), matchDt.getUTCMonth(), matchDt.getUTCDate()));

                // Only consider today's matches that haven't started yet
                if (matchDateUtc.getTime() === todayUtc.getTime() && matchDt > nowUtc) {
                    upcomingMatches.push({
                        home: match.HomeTeamShortName || 'Unknown',
                        away: match.AwayTeamShortName || 'Unknown',
                        match_no: match.TourGamedayId || 0,
                        dateTime: matchDt
                    });
                }
            } catch (e) {
                console.warn('Could not parse match dateTime for active match:', e);
            }
        }
    }

    // If no matches have started and no upcoming matches today, return null
    if (upcomingMatches.length === 0) {
        return null;
    }

    // Calculate today's matches to check if all matches are upcoming
    const todayMatches = [];
    for (const match of fixtures) {
        const matchDtStr = match.MatchdateTime || '';
        if (matchDtStr) {
            try {
                const matchDt = new Date(matchDtStr + ' UTC');
                const matchDateUtc = new Date(Date.UTC(matchDt.getUTCFullYear(), matchDt.getUTCMonth(), matchDt.getUTCDate()));
                if (matchDateUtc.getTime() === todayUtc.getTime()) {
                    todayMatches.push({
                        home: match.HomeTeamShortName || 'Unknown',
                        away: match.AwayTeamShortName || 'Unknown'
                    });
                }
            } catch (e) {
                console.warn('Could not parse match dateTime for today matches:', e);
            }
        }
    }

    // If all today's matches are upcoming (none have started yet), show them all
    if (upcomingMatches.length === todayMatches.length) {
        // All today's matches are upcoming (none have started yet), show them all
        const firstMatchTime = upcomingMatches[0]?.dateTime;
        return {
            home: upcomingMatches.map(m => m.home).join(' vs '),
            away: upcomingMatches.map(m => m.away).join(' '),
            match_no: upcomingMatches.map(m => m.match_no).join(', '),
            dateTime: firstMatchTime,
            multiMatch: true
        };
    }

    // Return the next upcoming match
    upcomingMatches.sort((a, b) => a.dateTime - b.dateTime);
    return upcomingMatches[0];
}
