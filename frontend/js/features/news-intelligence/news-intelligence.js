/**
 * News Intelligence Module
 * 
 * Handles the News Intelligence dashboard functionality:
 * - Loading and displaying news articles
 * - Category and type filtering
 * - Map visualization (crisis heatmap)
 * - Word cloud generation
 * - Real-time clock updates
 * - Chart rendering
 */

// API Base URL
const NEWS_API_BASE = '/api/news-intelligence';

// State management
const state = {
    articles: [],
    currentPage: 1,
    pageSize: 20,
    totalPages: 1,
    newsType: 'all',
    category: null,
    categories: [],
    mapData: null,
    wordcloudData: null,
    status: null,
    isLoading: false,
    map: null,
    chart: null,
};

// Country code to name mapping
const COUNTRY_NAMES = {
    US: 'United States', CN: 'China', KR: 'South Korea', JP: 'Japan',
    DE: 'Germany', NL: 'Netherlands', GB: 'United Kingdom', SG: 'Singapore',
    HK: 'Hong Kong', TW: 'Taiwan', VN: 'Vietnam', IN: 'India',
    ID: 'Indonesia', MY: 'Malaysia', TH: 'Thailand', PH: 'Philippines',
    AU: 'Australia', CA: 'Canada', MX: 'Mexico', BR: 'Brazil',
    RU: 'Russia', FR: 'France', IT: 'Italy', ES: 'Spain',
    BE: 'Belgium', EG: 'Egypt', PA: 'Panama', AE: 'UAE',
    SA: 'Saudi Arabia', IL: 'Israel', TR: 'Turkey', UA: 'Ukraine',
    YE: 'Yemen', IR: 'Iran', GR: 'Greece',
};

// Country coordinates for map markers
const COUNTRY_COORDS = {
    US: [39.8, -98.5], CN: [35.0, 105.0], KR: [36.5, 127.8], JP: [36.2, 138.2],
    DE: [51.2, 10.5], NL: [52.1, 5.3], GB: [55.4, -3.4], SG: [1.3, 103.8],
    HK: [22.3, 114.2], TW: [23.7, 121.0], VN: [14.1, 108.3], IN: [20.6, 79.0],
    ID: [-0.8, 113.9], MY: [4.2, 101.9], TH: [15.9, 100.9], PH: [12.9, 121.8],
    AU: [-25.3, 133.8], CA: [56.1, -106.3], MX: [23.6, -102.5], BR: [-14.2, -51.9],
    RU: [61.5, 105.3], FR: [46.2, 2.2], IT: [41.9, 12.6], ES: [40.5, -3.7],
    BE: [50.5, 4.5], EG: [26.8, 30.8], PA: [9.0, -79.5], AE: [23.4, 53.8],
    SA: [23.9, 45.1], IL: [31.0, 34.9], TR: [38.9, 35.2], UA: [48.4, 31.2],
    YE: [15.6, 48.5], IR: [32.4, 53.7], GR: [39.1, 21.8],
};

/**
 * Initialize the News Intelligence dashboard
 */
async function initNewsIntelligence() {
    console.log('🚀 Initializing News Intelligence...');
    
    // Start clock updates
    updateClocks();
    setInterval(updateClocks, 1000);
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    await Promise.all([
        loadStatus(),
        loadCategories(),
        loadMapData(),
        loadWordcloudData(),
        loadCriticalAlerts(),
    ]);
    
    // Load articles
    await loadArticles();
    
    // Initialize map
    initMap();
    
    console.log('✅ News Intelligence initialized');
}

/**
 * Setup event listeners for filters and tabs
 */
function setupEventListeners() {
    // News type tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            document.querySelector('.tab-btn.active')?.classList.remove('active');
            this.classList.add('active');
            state.newsType = this.dataset.type;
            state.currentPage = 1;
            await loadArticles();
        });
    });
    
    // Category chips
    document.querySelectorAll('.category-chip').forEach(chip => {
        chip.addEventListener('click', async function() {
            document.querySelector('.category-chip.active')?.classList.remove('active');
            this.classList.add('active');
            state.category = this.dataset.category === 'all' ? null : this.dataset.category;
            state.currentPage = 1;
            await loadArticles();
        });
    });
}

/**
 * Update UTC and KST clocks
 */
function updateClocks() {
    const now = new Date();
    
    // UTC Format
    const utcFormatter = new Intl.DateTimeFormat('en-GB', {
        weekday: 'short', day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: false, timeZone: 'UTC'
    });
    
    const parts = utcFormatter.formatToParts(now);
    const utcStr = `${parts.find(p => p.type === 'weekday').value}, ${parts.find(p => p.type === 'day').value} ${parts.find(p => p.type === 'month').value} ${parts.find(p => p.type === 'year').value} ${parts.find(p => p.type === 'hour').value}:${parts.find(p => p.type === 'minute').value}:${parts.find(p => p.type === 'second').value} UTC`;
    
    const utcEl = document.getElementById('utc-time');
    if (utcEl) utcEl.textContent = utcStr;
    
    // KST Format
    const kstFormatter = new Intl.DateTimeFormat('ko-KR', {
        year: 'numeric', month: 'numeric', day: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: true, timeZone: 'Asia/Seoul'
    });
    
    const kstEl = document.getElementById('kst-time');
    if (kstEl) kstEl.textContent = 'Seoul (KST): ' + kstFormatter.format(now);
}

/**
 * Load collection status and summary
 */
async function loadStatus() {
    try {
        const response = await fetch(`${NEWS_API_BASE}/status`);
        const data = await response.json();
        state.status = data;
        
        // Update UI
        const totalEl = document.getElementById('total-articles');
        if (totalEl) totalEl.textContent = (data.total_articles || 0).toLocaleString();
        
        const krEl = document.getElementById('kr-count');
        if (krEl) krEl.textContent = (data.kr_count || 0).toLocaleString();
        
        const globalEl = document.getElementById('global-count');
        if (globalEl) globalEl.textContent = (data.global_count || 0).toLocaleString();
        
        const updatedEl = document.getElementById('last-updated');
        if (updatedEl && data.last_updated_utc) {
            const date = new Date(data.last_updated_utc);
            updatedEl.textContent = `Last Updated: ${date.toLocaleString()}`;
        }
        
    } catch (error) {
        console.error('Error loading status:', error);
    }
}

/**
 * Load categories for chart
 */
async function loadCategories() {
    try {
        const response = await fetch(`${NEWS_API_BASE}/categories`);
        const data = await response.json();
        state.categories = data.categories || [];
        
        // Render chart
        renderCategoryChart();
        
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

/**
 * Render category donut chart
 */
function renderCategoryChart() {
    const canvas = document.getElementById('categoryChart');
    if (!canvas || !state.categories.length) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (state.chart) {
        state.chart.destroy();
    }
    
    const colors = {
        'Crisis': '#ef4444',
        'Ocean': '#3b82f6',
        'Air': '#10b981',
        'Inland': '#f59e0b',
        'Economy': '#8b5cf6',
        'ETC': '#6b7280',
    };
    
    const labels = state.categories.map(c => c.name);
    const values = state.categories.map(c => c.count);
    const bgColors = state.categories.map(c => colors[c.name] || '#6b7280');
    
    state.chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: bgColors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#9ca3af',
                        usePointStyle: true,
                        font: { size: 10 },
                        padding: 12
                    }
                }
            }
        }
    });
}

/**
 * Load map data (crisis by country)
 */
async function loadMapData() {
    try {
        const response = await fetch(`${NEWS_API_BASE}/map`);
        const data = await response.json();
        state.mapData = data;
        
        // Update map if already initialized
        if (state.map) {
            updateMapMarkers();
        }
        
    } catch (error) {
        console.error('Error loading map data:', error);
    }
}

/**
 * Initialize Leaflet map
 */
function initMap() {
    const mapContainer = document.getElementById('news-map');
    if (!mapContainer) return;
    
    // Create map
    state.map = L.map('news-map', {
        zoomControl: false,
        attributionControl: false
    }).setView([20, 10], 2);
    
    // Add dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(state.map);
    
    // Add markers for crisis data
    updateMapMarkers();
}

/**
 * Update map markers based on crisis data
 */
function updateMapMarkers() {
    if (!state.map || !state.mapData) return;
    
    const countries = state.mapData.countries || {};
    
    // Clear existing markers
    state.map.eachLayer(layer => {
        if (layer instanceof L.CircleMarker) {
            layer.remove();
        }
    });
    
    // Add markers for each country with crisis
    Object.entries(countries).forEach(([code, count]) => {
        const coords = COUNTRY_COORDS[code];
        if (!coords) return;
        
        // Calculate color intensity based on crisis count
        let color;
        if (count >= 6) {
            color = '#991b1b'; // Dark red
        } else if (count >= 3) {
            color = '#dc2626'; // Medium red
        } else {
            color = '#f87171'; // Light red
        }
        
        // Calculate radius based on count
        const radius = Math.min(8 + count * 3, 25);
        
        const marker = L.circleMarker(coords, {
            radius: radius,
            fillColor: color,
            color: color,
            fillOpacity: 0.7,
            weight: 1
        }).addTo(state.map);
        
        // Add tooltip with basic info
        const countryName = COUNTRY_NAMES[code] || code;
        marker.bindTooltip(`
            <div class="country-tooltip">
                <div class="country-name">${countryName}</div>
                <div class="crisis-count">${count} crisis alert${count > 1 ? 's' : ''}</div>
                <div class="tooltip-hint">Click for details</div>
            </div>
        `, { permanent: false, direction: 'top' });
        
        // Add click handler to show popup with news list
        marker.on('click', () => showCountryPopup(code, countryName, coords));
    });
}

/**
 * Show popup with news list for a country
 */
async function showCountryPopup(countryCode, countryName, coords) {
    if (!state.map) return;
    
    // Create popup with loading state
    const popup = L.popup({
        maxWidth: 350,
        maxHeight: 300,
        className: 'country-news-popup'
    })
    .setLatLng(coords)
    .setContent(`
        <div class="popup-content">
            <div class="popup-header">
                <h4>${countryName}</h4>
            </div>
            <div class="popup-loading">
                <div class="spinner-small"></div>
                Loading news...
            </div>
        </div>
    `)
    .openOn(state.map);
    
    try {
        // Fetch country articles
        const response = await fetch(`${NEWS_API_BASE}/map/country/${countryCode}?limit=10`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        const articles = data.articles || [];
        const total = data.total || 0;
        
        // Build articles HTML
        let articlesHtml = '';
        if (articles.length === 0) {
            articlesHtml = '<div class="no-articles">No crisis news for this country</div>';
        } else {
            articlesHtml = `
                <div class="popup-articles-list">
                    ${articles.map(article => `
                        <div class="popup-article-item">
                            <a href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer" class="popup-article-title">
                                ${escapeHtml(article.title?.substring(0, 80) || 'Untitled')}${article.title?.length > 80 ? '...' : ''}
                            </a>
                            <div class="popup-article-meta">
                                <span class="source">${escapeHtml(article.source_name || '')}</span>
                                ${article.published_at_utc ? `<span class="time">${formatTimeShort(article.published_at_utc)}</span>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Update popup content
        popup.setContent(`
            <div class="popup-content">
                <div class="popup-header">
                    <h4>${countryName}</h4>
                    <span class="popup-count">${total} crisis alert${total > 1 ? 's' : ''}</span>
                </div>
                ${articlesHtml}
            </div>
        `);
        
    } catch (error) {
        console.error('Error loading country articles:', error);
        popup.setContent(`
            <div class="popup-content">
                <div class="popup-header">
                    <h4>${countryName}</h4>
                </div>
                <div class="popup-error">Failed to load news</div>
            </div>
        `);
    }
}

/**
 * Format time for short display
 */
function formatTimeShort(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 hour
    if (diff < 3600000) {
        const mins = Math.floor(diff / 60000);
        return `${mins}m ago`;
    }
    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
    }
    // More than 24 hours
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Load word cloud data
 */
async function loadWordcloudData() {
    try {
        const response = await fetch(`${NEWS_API_BASE}/wordcloud`);
        const data = await response.json();
        state.wordcloudData = data;
        
        // Render word cloud
        renderWordcloud();
        
    } catch (error) {
        console.error('Error loading wordcloud data:', error);
    }
}

/**
 * Render word cloud
 */
function renderWordcloud() {
    const container = document.getElementById('wordcloud-content');
    if (!container || !state.wordcloudData) return;
    
    const keywords = state.wordcloudData.keywords || {};
    const entries = Object.entries(keywords);
    
    if (entries.length === 0) {
        container.innerHTML = '<span class="empty-state">No keywords available</span>';
        return;
    }
    
    // Find max frequency for scaling
    const maxFreq = Math.max(...entries.map(([_, freq]) => freq));
    
    // Generate word cloud HTML
    const words = entries.map(([word, freq]) => {
        // Calculate font size (1rem to 2.5rem based on frequency)
        const sizeScale = freq / maxFreq;
        const fontSize = 1 + sizeScale * 1.5;
        
        // Alternate colors
        const colors = ['#ffffff', '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#a855f7'];
        const color = colors[Math.floor(Math.random() * colors.length)];
        
        return `<span class="keyword-item" style="font-size: ${fontSize}rem; color: ${color};" title="${freq} mentions">${word}</span>`;
    }).join('');
    
    container.innerHTML = words;
}

/**
 * Load critical alerts
 */
async function loadCriticalAlerts() {
    try {
        const response = await fetch(`${NEWS_API_BASE}/critical-alerts?limit=5`);
        const data = await response.json();
        
        const container = document.getElementById('critical-alerts-list');
        if (!container) return;
        
        if (!data.alerts || data.alerts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No critical alerts at this time</p>
                </div>
            `;
            return;
        }
        
        const alertsHtml = data.alerts.map(alert => {
            // Determine severity class
            let severityClass = 'severity-default';
            if (alert.goldstein_scale !== null) {
                if (alert.goldstein_scale <= -8) severityClass = 'severity-extreme';
                else if (alert.goldstein_scale <= -6) severityClass = 'severity-severe';
                else if (alert.goldstein_scale <= -4) severityClass = 'severity-high';
            }
            
            return `
                <div class="critical-alert-item ${severityClass}">
                    <div class="alert-title">${escapeHtml(alert.title)}</div>
                    <div class="alert-summary">${escapeHtml(alert.content_summary?.substring(0, 100) || '')}...</div>
                    <div class="alert-meta">
                        <span><i class="fas fa-clock"></i> ${formatTime(alert.published_at_utc || alert.collected_at_utc)}</span>
                        ${alert.source_name ? `<span>${alert.source_name}</span>` : ''}
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = alertsHtml;
        
    } catch (error) {
        console.error('Error loading critical alerts:', error);
    }
}

/**
 * Load news articles with current filters
 */
async function loadArticles() {
    const container = document.getElementById('news-list');
    if (!container) return;
    
    // Show loading state
    state.isLoading = true;
    container.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            Loading articles...
        </div>
    `;
    
    try {
        // Build query params
        const params = new URLSearchParams({
            page: state.currentPage,
            page_size: state.pageSize,
        });
        
        if (state.newsType !== 'all') {
            params.append('news_type', state.newsType);
        }
        
        if (state.category) {
            params.append('category', state.category);
        }
        
        const response = await fetch(`${NEWS_API_BASE}/articles?${params}`);
        const data = await response.json();
        
        state.articles = data.articles || [];
        state.totalPages = data.total_pages || 1;
        
        // Render articles
        renderArticles();
        
        // Render pagination
        renderPagination();
        
    } catch (error) {
        console.error('Error loading articles:', error);
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Error Loading Articles</h3>
                <p>Please try again later</p>
            </div>
        `;
    } finally {
        state.isLoading = false;
    }
}

/**
 * Render news articles list
 */
function renderArticles() {
    const container = document.getElementById('news-list');
    if (!container) return;
    
    if (state.articles.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-newspaper"></i>
                <h3>No Articles Found</h3>
                <p>Try adjusting your filters</p>
            </div>
        `;
        return;
    }
    
    const articlesHtml = state.articles.map(article => {
        // Build badges
        let badges = '';
        
        // News type badge
        if (article.news_type === 'KR') {
            badges += '<span class="badge badge-kr">Korea</span>';
        } else {
            badges += '<span class="badge badge-global">Global</span>';
        }
        
        // GDELT badge
        if (article.source_name === 'GDELT') {
            badges += '<span class="badge badge-gdelt">GDELT</span>';
        }
        
        // Category label (already shows Crisis if applicable)
        const categoryLabel = `<span class="category-label">${article.category || 'Uncategorized'}</span>`;
        
        // GDELT metrics section
        let gdeltMetrics = '';
        if (article.source_name === 'GDELT' && article.goldstein_scale !== null) {
            const goldsteinPercent = Math.abs(article.goldstein_scale) * 10;
            let barColor = '#f59e0b';
            let severityLabel = 'Moderate';
            
            if (article.goldstein_scale <= -8) {
                barColor = '#991b1b';
                severityLabel = 'Extreme';
            } else if (article.goldstein_scale <= -6) {
                barColor = '#dc2626';
                severityLabel = 'Severe';
            } else if (article.goldstein_scale <= -4) {
                barColor = '#ea580c';
                severityLabel = 'High';
            }
            
            gdeltMetrics = `
                <div class="gdelt-metrics">
                    <div class="gdelt-header">
                        <span>Goldstein Scale</span>
                        <span style="color: ${barColor}">${article.goldstein_scale.toFixed(1)} (${severityLabel})</span>
                    </div>
                    <div class="goldstein-bar-bg">
                        <div class="goldstein-bar-fill" style="width: ${goldsteinPercent}%; background: ${barColor};"></div>
                    </div>
                    <div class="gdelt-stats">
                        ${article.avg_tone !== null ? `<span class="gdelt-stat"><i class="fas fa-wave-square"></i> Avg Tone: <b>${article.avg_tone.toFixed(1)}</b></span>` : ''}
                        ${article.num_mentions ? `<span class="gdelt-stat"><i class="fas fa-bullhorn"></i> Mentions: <b>${article.num_mentions}</b></span>` : ''}
                        ${article.num_sources ? `<span class="gdelt-stat"><i class="fas fa-newspaper"></i> Sources: <b>${article.num_sources}</b></span>` : ''}
                    </div>
                </div>
            `;
        }
        
        // Country tags
        let countryTags = '';
        if (article.country_tags && article.country_tags.length > 0) {
            countryTags = `
                <span class="country-tags">
                    ${article.country_tags.map(code => `<span class="country-tag">${COUNTRY_NAMES[code] || code}</span>`).join('')}
                </span>
            `;
        }
        
        // Format time
        const timeDisplay = formatTimeWithKST(article.published_at_utc || article.collected_at_utc);
        
        return `
            <article class="news-card">
                <div class="news-content">
                    <div class="news-meta">
                        ${badges}
                        ${categoryLabel}
                    </div>
                    <h3 class="news-title">
                        <a href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer">
                            ${escapeHtml(article.title)}
                        </a>
                    </h3>
                    ${gdeltMetrics}
                    <p class="news-excerpt">${escapeHtml(article.content_summary || '')}</p>
                    <div class="news-footer">
                        <span><i class="far fa-calendar"></i> ${timeDisplay}</span>
                        <span><i class="fas fa-external-link-alt"></i> ${escapeHtml(article.source_name)}</span>
                        ${countryTags}
                    </div>
                </div>
            </article>
        `;
    }).join('');
    
    container.innerHTML = articlesHtml;
}

/**
 * Render pagination controls
 */
function renderPagination() {
    const container = document.getElementById('pagination');
    if (!container) return;
    
    if (state.totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let buttons = [];
    
    // Previous button
    buttons.push(`
        <button class="page-btn" onclick="goToPage(${state.currentPage - 1})" ${state.currentPage === 1 ? 'disabled' : ''}>
            <i class="fas fa-chevron-left"></i>
        </button>
    `);
    
    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, state.currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(state.totalPages, startPage + maxVisible - 1);
    startPage = Math.max(1, endPage - maxVisible + 1);
    
    for (let i = startPage; i <= endPage; i++) {
        buttons.push(`
            <button class="page-btn ${i === state.currentPage ? 'active' : ''}" onclick="goToPage(${i})">
                ${i}
            </button>
        `);
    }
    
    // Next button
    buttons.push(`
        <button class="page-btn" onclick="goToPage(${state.currentPage + 1})" ${state.currentPage === state.totalPages ? 'disabled' : ''}>
            <i class="fas fa-chevron-right"></i>
        </button>
    `);
    
    container.innerHTML = buttons.join('');
}

/**
 * Navigate to a specific page
 */
async function goToPage(page) {
    if (page < 1 || page > state.totalPages || page === state.currentPage) return;
    state.currentPage = page;
    await loadArticles();
    
    // Scroll to top of news list
    document.getElementById('news-list')?.scrollIntoView({ behavior: 'smooth' });
}

// Helper functions

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
    });
}

function formatTimeWithKST(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    
    // UTC time
    const utc = date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'UTC',
        hour12: false
    });
    
    // KST time
    const kst = date.toLocaleString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Seoul',
        hour12: false
    });
    
    return `${utc} UTC (${kst} KST)`;
}

// Make functions globally available
window.goToPage = goToPage;

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNewsIntelligence);
} else {
    initNewsIntelligence();
}

