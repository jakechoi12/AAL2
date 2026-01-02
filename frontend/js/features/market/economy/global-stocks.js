/**
 * AAL Application - Global Stocks Module
 * 국제 주가지수 관련 기능 모듈
 * 
 * 담당 패널: #global-stocks-panel
 */

// ============================================================
// MODULE MARKER
// ============================================================
window.globalStocksModuleLoaded = true;

// ============================================================
// CONFIGURATION
// ============================================================

const GLOBAL_STOCKS_CONFIG = {
    apiCategory: 'stock-index-international',
    panelId: 'global-stocks-panel',
    title: 'Global Stock Index',
    description: '국제 주요국 주가지수',
    cycle: 'M',
    unit: 'Index',
    chartPrefix: 'global-stocks'
};

// ============================================================
// STATE
// ============================================================

const globalStocksState = {
    countryMapping: {},
    activeCountries: [],
    countryData: {},
    yAxisRange: { min: 0, max: 0 },
    isLoaded: false,
    countryListLoaded: false
};

// ============================================================
// COUNTRY HELPERS
// ============================================================

const globalStocksCountryMap = [
    { keywords: ['한국', 'kor', 'korea', 'kospi'], name: 'Korea', color: 'var(--c-interest-kor)' },
    { keywords: ['미국', 'usa', 'us ', 'united states', 'dow', 's&p', 'nasdaq'], name: 'USA', color: 'var(--c-interest-usa)' },
    { keywords: ['중국', 'chn', 'china'], name: 'China', color: 'var(--c-interest-chn)' },
    { keywords: ['일본', 'jpn', 'japan', 'nikkei'], name: 'Japan', color: 'var(--c-interest-jpn)' },
    { keywords: ['독일', 'deu', 'germany', 'dax'], name: 'Germany', color: 'var(--c-interest-deu)' },
    { keywords: ['인도', 'ind', 'india', 'sensex'], name: 'India', color: 'var(--c-interest-ind)' },
    { keywords: ['영국', 'gbr', 'uk', 'ftse'], name: 'UK', color: 'var(--c-interest-gbr)' },
    { keywords: ['프랑스', 'fra', 'france', 'cac'], name: 'France', color: 'var(--c-interest-fra)' },
    { keywords: ['러시아', 'rus', 'russia'], name: 'Russia', color: 'var(--c-interest-rus)' },
    { keywords: ['캐나다', 'can', 'canada'], name: 'Canada', color: 'var(--c-interest-can)' },
    { keywords: ['이탈리아', 'ita', 'italy'], name: 'Italy', color: 'var(--c-interest-ita)' },
    { keywords: ['브라질', 'bra', 'brazil'], name: 'Brazil', color: 'var(--c-interest-bra)' },
    { keywords: ['호주', '오스트레일리아', 'aus', 'australia'], name: 'Australia', color: 'var(--c-interest-aus)' },
    { keywords: ['멕시코', 'mex', 'mexico'], name: 'Mexico', color: 'var(--c-interest-mex)' },
    { keywords: ['인도네시아', 'idn', 'indonesia'], name: 'Indonesia', color: 'var(--c-interest-idn)' },
    { keywords: ['튀르키예', '터키', 'tur', 'turkey'], name: 'Turkey', color: 'var(--c-interest-tur)' },
    { keywords: ['스위스', 'che', 'switzerland'], name: 'Switzerland', color: 'var(--c-interest-che)' },
    { keywords: ['스웨덴', 'swe', 'sweden'], name: 'Sweden', color: 'var(--c-interest-swe)' },
    { keywords: ['노르웨이', 'nor', 'norway'], name: 'Norway', color: 'var(--c-interest-nor)' },
    { keywords: ['남아프리카', 'zaf', 'south africa'], name: 'South Africa', color: 'var(--c-interest-zaf)' },
    { keywords: ['덴마크', 'dnk', 'denmark'], name: 'Denmark', color: 'var(--c-interest-dnk)' },
    { keywords: ['뉴질랜드', 'nzl', 'new zealand'], name: 'New Zealand', color: 'var(--c-interest-nzl)' }
];

function getGlobalStocksCountryName(koreanName) {
    if (!koreanName) return koreanName;
    const n = koreanName.toLowerCase();
    for (const c of globalStocksCountryMap) {
        if (c.keywords.some(k => n.includes(k))) return c.name;
    }
    return koreanName;
}

function getGlobalStocksCountryColor(itemCode) {
    const info = globalStocksState.countryMapping[itemCode];
    if (!info) return '#4ECDC4';
    const n = info.name?.toLowerCase() || '';
    for (const c of globalStocksCountryMap) {
        if (c.keywords.some(k => n.includes(k))) return c.color;
    }
    return '#4ECDC4';
}

// ============================================================
// INITIALIZATION
// ============================================================

async function initGlobalStocks() {
    const prefix = GLOBAL_STOCKS_CONFIG.chartPrefix;
    const startInput = document.getElementById(`${prefix}-start-date`);
    const endInput = document.getElementById(`${prefix}-end-date`);
    
    if (startInput && endInput) {
        const now = new Date();
        const start = new Date();
        start.setFullYear(now.getFullYear() - 2);
        
        startInput.value = start.toISOString().split('T')[0];
        endInput.value = now.toISOString().split('T')[0];
        startInput.max = endInput.value;
        endInput.max = endInput.value;
        
        startInput.addEventListener('change', () => validateGlobalStocksDateRange() && fetchGlobalStocksData());
        endInput.addEventListener('change', () => validateGlobalStocksDateRange() && fetchGlobalStocksData());
    }
    
    try {
        await fetchGlobalStocksCountryList();
        initGlobalStocksCountryChips();
        fetchGlobalStocksData();
    } catch (err) {
        console.error('Failed to init Global Stocks:', err);
    }
    
    globalStocksState.isLoaded = true;
    window.globalStocksDataLoaded = true;
}

async function fetchGlobalStocksCountryList() {
    if (globalStocksState.countryListLoaded) return globalStocksState.countryMapping;
    
    const res = await fetch(`${API_BASE}/market/categories?category=${GLOBAL_STOCKS_CONFIG.apiCategory}`);
    if (res.ok) {
        const data = await res.json();
        if (data.items) {
            globalStocksState.countryMapping = data.items;
            globalStocksState.countryListLoaded = true;
            const codes = Object.keys(data.items);
            const korCode = codes.find(c => {
                const n = data.items[c].name;
                return n && (n.includes('한국') || n.toLowerCase().includes('korea') || n.toLowerCase().includes('kospi'));
            });
            globalStocksState.activeCountries = korCode ? [korCode] : (codes.length ? [codes[0]] : []);
        }
    }
    return globalStocksState.countryMapping;
}

function initGlobalStocksCountryChips() {
    const container = document.getElementById(`${GLOBAL_STOCKS_CONFIG.chartPrefix}-country-chips`);
    if (!container) return;
    container.innerHTML = '';
    
    Object.keys(globalStocksState.countryMapping).forEach(code => {
        const info = globalStocksState.countryMapping[code];
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.setAttribute('data-item-code', code);
        
        const isActive = globalStocksState.activeCountries.includes(code);
        if (isActive) chip.classList.add('active');
        
        const color = getGlobalStocksCountryColor(code);
        const dot = document.createElement('div');
        dot.className = 'chip-dot';
        dot.style.background = isActive ? color : 'currentColor';
        if (isActive) { chip.style.borderColor = color; chip.style.color = color; }
        
        chip.appendChild(dot);
        chip.appendChild(document.createTextNode(getGlobalStocksCountryName(info.name)));
        chip.addEventListener('click', () => toggleGlobalStocksCountry(code));
        container.appendChild(chip);
    });
}

function toggleGlobalStocksCountry(itemCode) {
    const idx = globalStocksState.activeCountries.indexOf(itemCode);
    if (idx === -1) globalStocksState.activeCountries.push(itemCode);
    else globalStocksState.activeCountries.splice(idx, 1);
    initGlobalStocksCountryChips();
    if (validateGlobalStocksDateRange()) fetchGlobalStocksData();
}

function validateGlobalStocksDateRange() {
    const prefix = GLOBAL_STOCKS_CONFIG.chartPrefix;
    const s = document.getElementById(`${prefix}-start-date`);
    const e = document.getElementById(`${prefix}-end-date`);
    return s && e && new Date(s.value) <= new Date(e.value);
}

// ============================================================
// DATA FETCHING
// ============================================================

async function fetchGlobalStocksData() {
    const prefix = GLOBAL_STOCKS_CONFIG.chartPrefix;
    if (!validateGlobalStocksDateRange() || globalStocksState.activeCountries.length === 0) {
        updateGlobalStocksChart();
        return;
    }
    
    const startDate = formatDateForAPI(document.getElementById(`${prefix}-start-date`).value);
    const endDate = formatDateForAPI(document.getElementById(`${prefix}-end-date`).value);
    
    const container = document.getElementById(`${prefix}-chart-container`);
    if (container) container.style.opacity = '0.5';
    
    try {
        const results = await Promise.all(globalStocksState.activeCountries.map(async code => {
            const url = `${API_BASE}/market/indices?type=${GLOBAL_STOCKS_CONFIG.apiCategory}&itemCode=${code}&startDate=${startDate}&endDate=${endDate}&cycle=M`;
            try {
                const res = await fetch(url);
                return { itemCode: code, data: await res.json() };
            } catch (e) {
                return { itemCode: code, data: { error: e.message } };
            }
        }));
        
        globalStocksState.countryData = {};
        results.forEach(({ itemCode, data }) => {
            if (!data.error && data.StatisticSearch?.row) {
                globalStocksState.countryData[itemCode] = data.StatisticSearch.row
                    .map(r => ({ date: r.TIME, value: parseFloat(r.DATA_VALUE) }))
                    .filter(i => !isNaN(i.value))
                    .sort((a, b) => a.date.localeCompare(b.date));
            }
        });
        
        updateGlobalStocksChart();
    } finally {
        if (container) container.style.opacity = '1';
    }
}

// ============================================================
// CHART RENDERING
// ============================================================

function updateGlobalStocksChart() {
    const prefix = GLOBAL_STOCKS_CONFIG.chartPrefix;
    const svg = document.getElementById(`${prefix}-chart-svg`);
    const pathsGroup = document.getElementById(`${prefix}-paths-group`);
    const pointsGroup = document.getElementById(`${prefix}-data-points`);
    
    if (!svg) return;
    if (pathsGroup) pathsGroup.innerHTML = '';
    else svg.querySelectorAll('.chart-path').forEach(e => e.remove());
    if (pointsGroup) pointsGroup.innerHTML = '';
    
    const allDates = new Set();
    Object.values(globalStocksState.countryData).forEach(d => d.forEach(i => allDates.add(i.date)));
    const sortedDates = Array.from(allDates).sort();
    
    if (sortedDates.length === 0) {
        renderGlobalStocksYAxis();
        renderGlobalStocksXAxis([]);
        return;
    }
    
    const allVals = [];
    Object.values(globalStocksState.countryData).forEach(d => d.forEach(i => allVals.push(i.value)));
    const min = Math.min(...allVals);
    const max = Math.max(...allVals);
    const range = max - min || 1;
    globalStocksState.yAxisRange = { min: Math.max(0, min - range * 0.05), max: max + range * 0.05 };
    
    renderGlobalStocksYAxis();
    
    globalStocksState.activeCountries.forEach(code => {
        const data = globalStocksState.countryData[code];
        if (!data?.length) return;
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.classList.add('chart-path', 'visible');
        path.setAttribute('stroke', getGlobalStocksCountryColor(code));
        path.setAttribute('stroke-width', '2.5');
        path.setAttribute('fill', 'none');
        
        const sortedData = sortedDates.map(d => data.find(i => i.date === d) || null).filter(Boolean);
        if (sortedData.length) {
            path.setAttribute('d', generateGlobalStocksPath(sortedData));
            (pathsGroup || svg).appendChild(path);
        }
    });
    
    renderGlobalStocksXAxis(sortedDates);
    setupGlobalStocksInteractivity();
    updateGlobalStocksHeader();
}

function generateGlobalStocksPath(data) {
    const svg = document.getElementById(`${GLOBAL_STOCKS_CONFIG.chartPrefix}-chart-svg`);
    if (!svg || !data.length) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const pad = { top: 20, bottom: 30, left: 60, right: 20 };
    const cw = width - pad.left - pad.right;
    const ch = height - pad.top - pad.bottom;
    const { min, max } = globalStocksState.yAxisRange;
    const range = max - min || 1;
    
    return data.map((p, i) => {
        const x = pad.left + (i / (data.length - 1 || 1)) * cw;
        const y = pad.top + (1 - (p.value - min) / range) * ch;
        return i === 0 ? `M ${x},${y}` : `L ${x},${y}`;
    }).join(' ');
}

function renderGlobalStocksYAxis() {
    const g = document.getElementById(`${GLOBAL_STOCKS_CONFIG.chartPrefix}-y-axis-labels`);
    if (!g) return;
    g.innerHTML = '';
    const { min, max } = globalStocksState.yAxisRange;
    for (let i = 0; i <= 5; i++) {
        const val = max - (i / 5) * (max - min);
        const y = 20 + (i / 5) * 330;
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', '55');
        t.setAttribute('y', y);
        t.setAttribute('class', 'chart-yaxis-label');
        t.setAttribute('text-anchor', 'end');
        t.textContent = val.toLocaleString('en-US', { maximumFractionDigits: 0 });
        g.appendChild(t);
    }
}

function renderGlobalStocksXAxis(dates) {
    const g = document.getElementById(`${GLOBAL_STOCKS_CONFIG.chartPrefix}-x-axis-labels`);
    if (!g || !dates.length) return;
    g.innerHTML = '';
    
    const svg = document.getElementById(`${GLOBAL_STOCKS_CONFIG.chartPrefix}-chart-svg`);
    const { width } = getSvgViewBoxSize(svg);
    const cw = width - 80;
    const interval = Math.max(1, Math.floor(dates.length / 8));
    
    dates.forEach((d, i) => {
        if (i % interval !== 0 && i !== dates.length - 1) return;
        const x = 60 + (i / (dates.length - 1 || 1)) * cw;
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', x);
        t.setAttribute('y', '370');
        t.setAttribute('class', 'chart-xaxis-label');
        t.setAttribute('text-anchor', 'middle');
        t.textContent = d.length === 6 ? `${d.slice(2, 4)}.${d.slice(4)}` : d;
        g.appendChild(t);
    });
}

let globalStocksCrosshairX = null;
let globalStocksCrosshairY = null;

function setupGlobalStocksInteractivity() {
    const prefix = GLOBAL_STOCKS_CONFIG.chartPrefix;
    const container = document.getElementById(`${prefix}-chart-container`);
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    const svg = document.getElementById(`${prefix}-chart-svg`);
    if (!container || !tooltip || !svg) return;
    
    if (tooltip.parentElement !== document.body) document.body.appendChild(tooltip);
    
    // Create crosshair elements
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 60, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const crosshairs = createCrosshairElements(svg, padding, chartWidth, chartHeight);
    globalStocksCrosshairX = crosshairs.crosshairX;
    globalStocksCrosshairY = crosshairs.crosshairY;
    
    const newC = container.cloneNode(true);
    container.parentNode.replaceChild(newC, container);
    
    newC.addEventListener('mousemove', e => showGlobalStocksTooltip(e));
    newC.addEventListener('mouseleave', () => {
        hideGlobalStocksTooltip();
        hideCrosshair(globalStocksCrosshairX, globalStocksCrosshairY);
    });
}

function showGlobalStocksTooltip(event) {
    const prefix = GLOBAL_STOCKS_CONFIG.chartPrefix;
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    const svg = document.getElementById(`${prefix}-chart-svg`);
    if (!tooltip || !svg) return;
    
    const allDates = new Set();
    Object.values(globalStocksState.countryData).forEach(d => d.forEach(i => allDates.add(i.date)));
    const dates = Array.from(allDates).sort();
    if (!dates.length) {
        hideCrosshair(globalStocksCrosshairX, globalStocksCrosshairY);
        return;
    }
    
    const rect = svg.getBoundingClientRect();
    const { width, height } = getSvgViewBoxSize(svg);
    const pad = { top: 20, bottom: 30, left: 60, right: 20 };
    const cw = width - pad.left - pad.right;
    const ch = height - pad.top - pad.bottom;
    const x = event.clientX - rect.left;
    const idx = Math.round(((x / rect.width * width) - 60) / (width - 80) * (dates.length - 1));
    const clampedIdx = Math.max(0, Math.min(dates.length - 1, idx));
    const date = dates[clampedIdx];
    
    // Update crosshair X position
    const crosshairXPos = pad.left + (clampedIdx / (dates.length - 1 || 1)) * cw;
    if (globalStocksCrosshairX) {
        globalStocksCrosshairX.setAttribute('x1', crosshairXPos);
        globalStocksCrosshairX.setAttribute('x2', crosshairXPos);
        globalStocksCrosshairX.style.opacity = '1';
    }
    
    // Calculate average Y for crosshair
    let sumY = 0, countY = 0;
    globalStocksState.activeCountries.forEach(code => {
        const item = globalStocksState.countryData[code]?.find(d => d.date === date);
        if (item && Number.isFinite(item.value)) { sumY += item.value; countY++; }
    });
    
    if (countY > 0 && globalStocksCrosshairY) {
        const avgVal = sumY / countY;
        const { min, max } = globalStocksState.yAxisRange;
        const normY = (avgVal - min) / (max - min || 1);
        const crosshairYPos = pad.top + (1 - normY) * ch;
        globalStocksCrosshairY.setAttribute('y1', crosshairYPos);
        globalStocksCrosshairY.setAttribute('y2', crosshairYPos);
        globalStocksCrosshairY.style.opacity = '1';
    }
    
    let content = '';
    globalStocksState.activeCountries.forEach(code => {
        const item = globalStocksState.countryData[code]?.find(d => d.date === date);
        if (!item) return;
        const name = getGlobalStocksCountryName(globalStocksState.countryMapping[code]?.name || code);
        const color = getGlobalStocksCountryColor(code);
        content += `<div class="chart-tooltip-item">
            <div class="chart-tooltip-currency"><div class="chart-tooltip-dot" style="background:${color}"></div><span>${name}</span></div>
            <span class="chart-tooltip-value">${item.value.toLocaleString()}</span>
        </div>`;
    });
    
    if (!content) return hideGlobalStocksTooltip();
    
    document.getElementById(`${prefix}-tooltip-content`).innerHTML = content;
    document.getElementById(`${prefix}-tooltip-date`).textContent = 
        date.length === 6 ? `${date.slice(0, 4)}.${date.slice(4)}` : date;
    
    tooltip.classList.add('visible');
    tooltip.style.left = (event.clientX + 15) + 'px';
    tooltip.style.top = (event.clientY + 15) + 'px';
    tooltip.style.visibility = 'visible';
}

function hideGlobalStocksTooltip() {
    const t = document.getElementById(`${GLOBAL_STOCKS_CONFIG.chartPrefix}-chart-tooltip`);
    if (t) { t.classList.remove('visible'); t.style.visibility = 'hidden'; }
    hideCrosshair(globalStocksCrosshairX, globalStocksCrosshairY);
}

function updateGlobalStocksHeader() {
    const prefix = GLOBAL_STOCKS_CONFIG.chartPrefix;
    const code = globalStocksState.activeCountries[0];
    const data = globalStocksState.countryData[code];
    if (!data?.length) return;
    
    const vals = data.map(i => i.value);
    const current = vals[vals.length - 1];
    const name = getGlobalStocksCountryName(globalStocksState.countryMapping[code]?.name || code);
    
    const title = document.getElementById(`${prefix}-chart-main-title`);
    if (title) title.textContent = `Stock Index - ${name}`;
    
    const value = document.getElementById(`${prefix}-chart-main-value`);
    if (value) value.innerHTML = `${current.toLocaleString()}`;
    
    const high = document.getElementById(`${prefix}-stat-high`);
    const low = document.getElementById(`${prefix}-stat-low`);
    const avg = document.getElementById(`${prefix}-stat-average`);
    if (high) high.textContent = Math.max(...vals).toLocaleString();
    if (low) low.textContent = Math.min(...vals).toLocaleString();
    if (avg) avg.textContent = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length).toLocaleString();
}

// ============================================================
// EXPORTS
// ============================================================

window.initGlobalStocks = initGlobalStocks;
window.toggleGlobalStocksCountry = toggleGlobalStocksCountry;

console.log('📊 Global Stocks module loaded');

