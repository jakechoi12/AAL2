/**
 * AAL Application - GDP per Capita Module
 * 1인당 GDP 관련 기능 모듈
 * 
 * 담당 패널: #gdp-per-capita-panel
 */

// ============================================================
// MODULE MARKER
// ============================================================
window.gdpPerCapitaModuleLoaded = true;

// ============================================================
// CONFIGURATION
// ============================================================

const GDP_PER_CAPITA_CONFIG = {
    apiCategory: 'gdp-per-capita-international',
    panelId: 'gdp-per-capita-panel',
    title: 'GDP per Capita',
    description: '국제 주요국 1인당 GDP',
    cycle: 'A',
    unit: 'USD',
    unitType: 'usd',
    chartPrefix: 'gdp-per-capita'
};

// ============================================================
// STATE MANAGEMENT
// ============================================================

const gdpPerCapitaState = {
    countryMapping: {},
    activeCountries: [],
    countryData: {},
    yAxisRange: { min: 0, max: 0 },
    cycle: 'A',
    isLoaded: false,
    countryListLoaded: false
};

// ============================================================
// COUNTRY INFO (shared logic)
// ============================================================

const gdppcCountryInfoMap = [
    { keywords: ['호주', 'aus', 'australia'], englishName: 'Australia', color: 'var(--c-interest-aus)' },
    { keywords: ['브라질', 'bra', 'brazil'], englishName: 'Brazil', color: 'var(--c-interest-bra)' },
    { keywords: ['캐나다', 'can', 'canada'], englishName: 'Canada', color: 'var(--c-interest-can)' },
    { keywords: ['스위스', 'che', 'switzerland'], englishName: 'Switzerland', color: 'var(--c-interest-che)' },
    { keywords: ['중국', 'chn', 'china'], englishName: 'China', color: 'var(--c-interest-chn)' },
    { keywords: ['독일', 'deu', 'germany'], englishName: 'Germany', color: 'var(--c-interest-deu)' },
    { keywords: ['프랑스', 'fra', 'france'], englishName: 'France', color: 'var(--c-interest-fra)' },
    { keywords: ['영국', 'gbr', 'uk'], englishName: 'UK', color: 'var(--c-interest-gbr)' },
    { keywords: ['인도', 'ind', 'india'], englishName: 'India', color: 'var(--c-interest-ind)' },
    { keywords: ['이탈리아', 'ita', 'italy'], englishName: 'Italy', color: 'var(--c-interest-ita)' },
    { keywords: ['일본', 'jpn', 'japan'], englishName: 'Japan', color: 'var(--c-interest-jpn)' },
    { keywords: ['한국', 'kor', 'korea'], englishName: 'Korea', color: 'var(--c-interest-kor)' },
    { keywords: ['멕시코', 'mex', 'mexico'], englishName: 'Mexico', color: 'var(--c-interest-mex)' },
    { keywords: ['러시아', 'rus', 'russia'], englishName: 'Russia', color: 'var(--c-interest-rus)' },
    { keywords: ['미국', 'usa', 'us '], englishName: 'USA', color: 'var(--c-interest-usa)' },
    { keywords: ['유로', 'eur', 'eurozone'], englishName: 'Eurozone', color: 'var(--c-interest-eur)' }
];

function getGDPPCCountryName(koreanName) {
    if (!koreanName) return koreanName;
    const name = koreanName.toLowerCase();
    for (const info of gdppcCountryInfoMap) {
        if (info.keywords.some(k => name.includes(k))) return info.englishName;
    }
    return koreanName;
}

function getGDPPCCountryColor(itemCode) {
    const info = gdpPerCapitaState.countryMapping[itemCode];
    if (!info) return '#4ECDC4';
    const name = info.name?.toLowerCase() || '';
    for (const c of gdppcCountryInfoMap) {
        if (c.keywords.some(k => name.includes(k))) return c.color;
    }
    return '#4ECDC4';
}

// ============================================================
// HELPERS
// ============================================================

function getUsdKrwRatePC() {
    return window.exchangeRates?.USD || 1350;
}

function convertToKRWPC(value) {
    if (!Number.isFinite(value)) return null;
    const krwMan = value * getUsdKrwRatePC() / 10000;
    return krwMan >= 1 ? `≈${krwMan.toLocaleString('en-US', {maximumFractionDigits: 0})}만 원` : null;
}

function compareGDPPCDates(a, b) {
    return parseInt(a, 10) - parseInt(b, 10);
}

// ============================================================
// INITIALIZATION
// ============================================================

async function initGDPPerCapita() {
    const prefix = GDP_PER_CAPITA_CONFIG.chartPrefix;
    
    const startInput = document.getElementById(`${prefix}-start-date`);
    const endInput = document.getElementById(`${prefix}-end-date`);
    
    if (startInput && endInput) {
        const now = new Date();
        startInput.value = now.getFullYear() - 10;
        endInput.value = now.getFullYear();
        startInput.min = 1960;
        endInput.min = 1960;
        startInput.max = now.getFullYear();
        endInput.max = now.getFullYear();
        
        startInput.addEventListener('change', () => validateGDPPCDateRange() && fetchGDPPCData());
        endInput.addEventListener('change', () => validateGDPPCDateRange() && fetchGDPPCData());
    }
    
    try {
        await fetchGDPPCCountryList();
        initGDPPCCountryChips();
        fetchGDPPCData();
    } catch (err) {
        console.error('Failed to init GDP per Capita:', err);
    }
    
    gdpPerCapitaState.isLoaded = true;
    window.gdpPerCapitaDataLoaded = true;
}

// ============================================================
// COUNTRY LIST
// ============================================================

async function fetchGDPPCCountryList() {
    if (gdpPerCapitaState.countryListLoaded) return gdpPerCapitaState.countryMapping;
    
    const url = `${API_BASE}/market/categories?category=${GDP_PER_CAPITA_CONFIG.apiCategory}`;
    const res = await fetch(url);
    if (res.ok) {
        const data = await res.json();
        if (data.items) {
            gdpPerCapitaState.countryMapping = data.items;
            gdpPerCapitaState.countryListLoaded = true;
            
            const codes = Object.keys(data.items);
            const korCode = codes.find(c => {
                const n = data.items[c].name;
                return n && (n.includes('한국') || n.toLowerCase().includes('korea'));
            });
            gdpPerCapitaState.activeCountries = korCode ? [korCode] : (codes.length ? [codes[0]] : []);
        }
    }
    return gdpPerCapitaState.countryMapping;
}

function initGDPPCCountryChips() {
    const container = document.getElementById(`${GDP_PER_CAPITA_CONFIG.chartPrefix}-country-chips`);
    if (!container) return;
    container.innerHTML = '';
    
    Object.keys(gdpPerCapitaState.countryMapping).forEach(itemCode => {
        const info = gdpPerCapitaState.countryMapping[itemCode];
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.setAttribute('data-item-code', itemCode);
        
        const isActive = gdpPerCapitaState.activeCountries.includes(itemCode);
        if (isActive) chip.classList.add('active');
        
        const color = getGDPPCCountryColor(itemCode);
        const dot = document.createElement('div');
        dot.className = 'chip-dot';
        dot.style.background = isActive ? color : 'currentColor';
        
        if (isActive) {
            chip.style.borderColor = color;
            chip.style.color = color;
        }
        
        chip.appendChild(dot);
        chip.appendChild(document.createTextNode(getGDPPCCountryName(info.name)));
        chip.addEventListener('click', () => toggleGDPPCCountry(itemCode));
        container.appendChild(chip);
    });
}

function toggleGDPPCCountry(itemCode) {
    const idx = gdpPerCapitaState.activeCountries.indexOf(itemCode);
    if (idx === -1) gdpPerCapitaState.activeCountries.push(itemCode);
    else gdpPerCapitaState.activeCountries.splice(idx, 1);
    
    initGDPPCCountryChips();
    if (validateGDPPCDateRange()) fetchGDPPCData();
}

function validateGDPPCDateRange() {
    const prefix = GDP_PER_CAPITA_CONFIG.chartPrefix;
    const s = document.getElementById(`${prefix}-start-date`);
    const e = document.getElementById(`${prefix}-end-date`);
    if (!s || !e) return false;
    return parseInt(s.value, 10) <= parseInt(e.value, 10);
}

// ============================================================
// DATA FETCHING
// ============================================================

async function fetchGDPPCData() {
    const prefix = GDP_PER_CAPITA_CONFIG.chartPrefix;
    if (!validateGDPPCDateRange() || gdpPerCapitaState.activeCountries.length === 0) {
        updateGDPPCChart();
        return;
    }
    
    const startDate = `${document.getElementById(`${prefix}-start-date`).value}0101`;
    const endDate = `${document.getElementById(`${prefix}-end-date`).value}1231`;
    
    const container = document.getElementById(`${prefix}-chart-container`);
    if (container) container.style.opacity = '0.5';
    
    try {
        const results = await Promise.all(gdpPerCapitaState.activeCountries.map(async code => {
            const url = `${API_BASE}/market/indices?type=${GDP_PER_CAPITA_CONFIG.apiCategory}&itemCode=${code}&startDate=${startDate}&endDate=${endDate}&cycle=A`;
            try {
                const res = await fetch(url);
                return { itemCode: code, data: await res.json() };
            } catch (e) {
                return { itemCode: code, data: { error: e.message } };
            }
        }));
        
        gdpPerCapitaState.countryData = {};
        results.forEach(({ itemCode, data }) => {
            if (!data.error && data.StatisticSearch?.row) {
                gdpPerCapitaState.countryData[itemCode] = data.StatisticSearch.row
                    .map(r => ({ date: r.TIME, value: parseFloat(r.DATA_VALUE) }))
                    .filter(i => !isNaN(i.value))
                    .sort((a, b) => compareGDPPCDates(a.date, b.date));
            }
        });
        
        updateGDPPCChart();
    } finally {
        if (container) container.style.opacity = '1';
    }
}

// ============================================================
// CHART RENDERING
// ============================================================

function updateGDPPCChart() {
    const prefix = GDP_PER_CAPITA_CONFIG.chartPrefix;
    const svg = document.getElementById(`${prefix}-chart-svg`);
    const pathsGroup = document.getElementById(`${prefix}-paths-group`);
    const pointsGroup = document.getElementById(`${prefix}-data-points`);
    
    if (!svg) return;
    if (pathsGroup) pathsGroup.innerHTML = '';
    else svg.querySelectorAll('.chart-path').forEach(e => e.remove());
    if (pointsGroup) pointsGroup.innerHTML = '';
    
    const allDates = new Set();
    Object.values(gdpPerCapitaState.countryData).forEach(d => d.forEach(i => allDates.add(i.date)));
    const sortedDates = Array.from(allDates).sort(compareGDPPCDates);
    
    if (sortedDates.length === 0) {
        renderGDPPCYAxis([]);
        renderGDPPCXAxis([]);
        return;
    }
    
    const allVals = [];
    Object.values(gdpPerCapitaState.countryData).forEach(d => d.forEach(i => allVals.push(i.value)));
    const min = Math.min(...allVals), max = Math.max(...allVals);
    const range = max - min || 1;
    gdpPerCapitaState.yAxisRange = { min: Math.max(0, min - range * 0.05), max: max + range * 0.05 };
    
    renderGDPPCYAxis(sortedDates);
    
    gdpPerCapitaState.activeCountries.forEach(code => {
        const data = gdpPerCapitaState.countryData[code];
        if (!data?.length) return;
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.classList.add('chart-path', 'visible');
        path.setAttribute('stroke', getGDPPCCountryColor(code));
        path.setAttribute('stroke-width', '2.5');
        path.setAttribute('fill', 'none');
        
        const sortedData = sortedDates.map(d => data.find(i => i.date === d) || null).filter(Boolean);
        if (sortedData.length) {
            path.setAttribute('d', generateGDPPCPath(sortedData));
            (pathsGroup || svg).appendChild(path);
        }
    });
    
    renderGDPPCXAxis(sortedDates);
    setupGDPPCInteractivity();
    updateGDPPCHeader();
}

function generateGDPPCPath(data) {
    const svg = document.getElementById(`${GDP_PER_CAPITA_CONFIG.chartPrefix}-chart-svg`);
    if (!svg || !data.length) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const pad = { top: 20, bottom: 30, left: 60, right: 20 };
    const cw = width - pad.left - pad.right;
    const ch = height - pad.top - pad.bottom;
    const { min, max } = gdpPerCapitaState.yAxisRange;
    const range = max - min || 1;
    
    return data.map((p, i) => {
        const x = pad.left + (i / (data.length - 1 || 1)) * cw;
        const y = pad.top + (1 - (p.value - min) / range) * ch;
        return i === 0 ? `M ${x},${y}` : `L ${x},${y}`;
    }).join(' ');
}

function renderGDPPCYAxis() {
    const g = document.getElementById(`${GDP_PER_CAPITA_CONFIG.chartPrefix}-y-axis-labels`);
    if (!g) return;
    g.innerHTML = '';
    const { min, max } = gdpPerCapitaState.yAxisRange;
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

function renderGDPPCXAxis(dates) {
    const g = document.getElementById(`${GDP_PER_CAPITA_CONFIG.chartPrefix}-x-axis-labels`);
    if (!g || !dates.length) return;
    g.innerHTML = '';
    
    const svg = document.getElementById(`${GDP_PER_CAPITA_CONFIG.chartPrefix}-chart-svg`);
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
        t.textContent = d;
        g.appendChild(t);
    });
}

function setupGDPPCInteractivity() {
    const prefix = GDP_PER_CAPITA_CONFIG.chartPrefix;
    const container = document.getElementById(`${prefix}-chart-container`);
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    if (!container || !tooltip) return;
    
    if (tooltip.parentElement !== document.body) document.body.appendChild(tooltip);
    
    const newC = container.cloneNode(true);
    container.parentNode.replaceChild(newC, container);
    
    newC.addEventListener('mousemove', e => showGDPPCTooltip(e));
    newC.addEventListener('mouseleave', () => hideGDPPCTooltip());
}

function showGDPPCTooltip(event) {
    const prefix = GDP_PER_CAPITA_CONFIG.chartPrefix;
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    const svg = document.getElementById(`${prefix}-chart-svg`);
    if (!tooltip || !svg) return;
    
    const allDates = new Set();
    Object.values(gdpPerCapitaState.countryData).forEach(d => d.forEach(i => allDates.add(i.date)));
    const dates = Array.from(allDates).sort(compareGDPPCDates);
    if (!dates.length) return;
    
    const rect = svg.getBoundingClientRect();
    const { width } = getSvgViewBoxSize(svg);
    const x = event.clientX - rect.left;
    const idx = Math.round(((x / rect.width * width) - 60) / (width - 80) * (dates.length - 1));
    const date = dates[Math.max(0, Math.min(dates.length - 1, idx))];
    
    let content = '';
    gdpPerCapitaState.activeCountries.forEach(code => {
        const item = gdpPerCapitaState.countryData[code]?.find(d => d.date === date);
        if (!item) return;
        const name = getGDPPCCountryName(gdpPerCapitaState.countryMapping[code]?.name || code);
        const color = getGDPPCCountryColor(code);
        const krw = convertToKRWPC(item.value);
        content += `<div class="chart-tooltip-item">
            <div class="chart-tooltip-currency"><div class="chart-tooltip-dot" style="background:${color}"></div><span>${name}</span></div>
            <span class="chart-tooltip-value">${item.value.toLocaleString()} USD${krw ? ` (${krw})` : ''}</span>
        </div>`;
    });
    
    if (!content) return hideGDPPCTooltip();
    
    document.getElementById(`${prefix}-tooltip-content`).innerHTML = content;
    document.getElementById(`${prefix}-tooltip-date`).textContent = date;
    
    tooltip.classList.add('visible');
    tooltip.style.left = (event.clientX + 15) + 'px';
    tooltip.style.top = (event.clientY + 15) + 'px';
    tooltip.style.visibility = 'visible';
}

function hideGDPPCTooltip() {
    const t = document.getElementById(`${GDP_PER_CAPITA_CONFIG.chartPrefix}-chart-tooltip`);
    if (t) { t.classList.remove('visible'); t.style.visibility = 'hidden'; }
}

function updateGDPPCHeader() {
    const prefix = GDP_PER_CAPITA_CONFIG.chartPrefix;
    const code = gdpPerCapitaState.activeCountries[0];
    const data = gdpPerCapitaState.countryData[code];
    if (!data?.length) return;
    
    const vals = data.map(i => i.value);
    const current = vals[vals.length - 1];
    const name = getGDPPCCountryName(gdpPerCapitaState.countryMapping[code]?.name || code);
    
    const title = document.getElementById(`${prefix}-chart-main-title`);
    if (title) title.textContent = `GDP per Capita - ${name}`;
    
    const value = document.getElementById(`${prefix}-chart-main-value`);
    if (value) {
        const krw = convertToKRWPC(current);
        value.innerHTML = `${current.toLocaleString()} <span style="font-size:50%;opacity:0.8">USD${krw ? ` (${krw})` : ''}</span>`;
    }
    
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

window.initGDPPerCapita = initGDPPerCapita;
window.toggleGDPPerCapitaCountry = toggleGDPPCCountry;

console.log('💰 GDP per Capita module loaded');

