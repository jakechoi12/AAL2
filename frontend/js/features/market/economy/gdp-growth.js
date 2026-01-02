/**
 * AAL Application - GDP Growth Rate Module
 * 경제성장률 관련 기능 모듈
 * 
 * 담당 패널: #gdp-growth-panel
 */

// ============================================================
// MODULE MARKER
// ============================================================
window.gdpGrowthModuleLoaded = true;

// ============================================================
// CONFIGURATION
// ============================================================

const GDP_GROWTH_CONFIG = {
    apiCategory: 'gdp-growth-international',
    panelId: 'gdp-growth-panel',
    title: 'Economy Growth Rate',
    description: '국제 주요국 경제성장률',
    cycle: 'A',
    unit: '%',
    chartPrefix: 'gdp-growth'
};

// ============================================================
// STATE
// ============================================================

const gdpGrowthState = {
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

const gdpGrowthCountryMap = [
    { keywords: ['호주', '오스트레일리아', 'aus', 'australia'], name: 'Australia', color: 'var(--c-interest-aus)' },
    { keywords: ['오스트리아', 'aut', 'austria'], name: 'Austria', color: '#E74C3C' },
    { keywords: ['벨기에', 'bel', 'belgium'], name: 'Belgium', color: '#F39C12' },
    { keywords: ['캐나다', 'can', 'canada'], name: 'Canada', color: 'var(--c-interest-can)' },
    { keywords: ['스위스', 'che', 'switzerland'], name: 'Switzerland', color: 'var(--c-interest-che)' },
    { keywords: ['칠레', 'chl', 'chile'], name: 'Chile', color: 'var(--c-interest-chl)' },
    { keywords: ['중국', 'chn', 'china'], name: 'China', color: 'var(--c-interest-chn)' },
    { keywords: ['체코', 'cze', 'czech'], name: 'Czech Republic', color: 'var(--c-interest-cze)' },
    { keywords: ['독일', 'deu', 'germany'], name: 'Germany', color: 'var(--c-interest-deu)' },
    { keywords: ['덴마크', 'dnk', 'denmark'], name: 'Denmark', color: 'var(--c-interest-dnk)' },
    { keywords: ['에스토니아', 'est', 'estonia'], name: 'Estonia', color: '#1ABC9C' },
    { keywords: ['스페인', 'esp', 'spain'], name: 'Spain', color: 'var(--c-interest-esp)' },
    { keywords: ['핀란드', 'fin', 'finland'], name: 'Finland', color: '#3498DB' },
    { keywords: ['프랑스', 'fra', 'france'], name: 'France', color: 'var(--c-interest-fra)' },
    { keywords: ['영국', 'gbr', 'uk', 'united kingdom'], name: 'UK', color: 'var(--c-interest-gbr)' },
    { keywords: ['그리스', 'grc', 'greece'], name: 'Greece', color: '#2980B9' },
    { keywords: ['헝가리', 'hun', 'hungary'], name: 'Hungary', color: 'var(--c-interest-hun)' },
    { keywords: ['아이슬란드', 'isl', 'iceland'], name: 'Iceland', color: '#7FB3D5' },
    { keywords: ['인도네시아', 'idn', 'indonesia'], name: 'Indonesia', color: 'var(--c-interest-idn)' },
    { keywords: ['아일랜드', 'irl', 'ireland'], name: 'Ireland', color: '#27AE60' },
    { keywords: ['이스라엘', 'isr', 'israel'], name: 'Israel', color: 'var(--c-interest-isr)' },
    { keywords: ['이탈리아', 'ita', 'italy'], name: 'Italy', color: 'var(--c-interest-ita)' },
    { keywords: ['일본', 'jpn', 'japan'], name: 'Japan', color: 'var(--c-interest-jpn)' },
    { keywords: ['한국', 'kor', 'korea'], name: 'Korea', color: 'var(--c-interest-kor)' },
    { keywords: ['라트비아', 'lva', 'latvia'], name: 'Latvia', color: '#A569BD' },
    { keywords: ['룩셈부르크', 'lux', 'luxembourg'], name: 'Luxembourg', color: '#F5B041' },
    { keywords: ['멕시코', 'mex', 'mexico'], name: 'Mexico', color: 'var(--c-interest-mex)' },
    { keywords: ['네덜란드', 'nld', 'netherlands'], name: 'Netherlands', color: '#E67E22' },
    { keywords: ['노르웨이', 'nor', 'norway'], name: 'Norway', color: 'var(--c-interest-nor)' },
    { keywords: ['뉴질랜드', 'nzl', 'zealand'], name: 'New Zealand', color: 'var(--c-interest-nzl)' },
    { keywords: ['폴란드', 'pol', 'poland'], name: 'Poland', color: 'var(--c-interest-pol)' },
    { keywords: ['포르투갈', 'prt', 'portugal'], name: 'Portugal', color: '#9B59B6' },
    { keywords: ['러시아', 'rus', 'russia'], name: 'Russia', color: 'var(--c-interest-rus)' },
    { keywords: ['슬로바키아', 'svk', 'slovakia'], name: 'Slovakia', color: '#34495E' },
    { keywords: ['슬로베니아', 'svn', 'slovenia'], name: 'Slovenia', color: '#16A085' },
    { keywords: ['스웨덴', 'swe', 'sweden'], name: 'Sweden', color: 'var(--c-interest-swe)' },
    { keywords: ['튀르키예', '터키', 'tur', 'turkey', 'turkiye'], name: 'Turkey', color: 'var(--c-interest-tur)' },
    { keywords: ['미국', 'usa', 'us ', 'united states'], name: 'USA', color: 'var(--c-interest-usa)' }
];

function getGDPGrowthCountryName(koreanName) {
    if (!koreanName) return koreanName;
    const n = koreanName.toLowerCase();
    for (const c of gdpGrowthCountryMap) {
        if (c.keywords.some(k => n.includes(k))) return c.name;
    }
    return koreanName;
}

function getGDPGrowthCountryColor(itemCode) {
    const info = gdpGrowthState.countryMapping[itemCode];
    if (!info) return '#4ECDC4';
    const n = info.name?.toLowerCase() || '';
    for (const c of gdpGrowthCountryMap) {
        if (c.keywords.some(k => n.includes(k))) return c.color;
    }
    return '#4ECDC4';
}

// ============================================================
// INITIALIZATION
// ============================================================

async function initGDPGrowth() {
    const prefix = GDP_GROWTH_CONFIG.chartPrefix;
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
        
        startInput.addEventListener('change', () => validateGDPGrowthDateRange() && fetchGDPGrowthData());
        endInput.addEventListener('change', () => validateGDPGrowthDateRange() && fetchGDPGrowthData());
    }
    
    try {
        await fetchGDPGrowthCountryList();
        initGDPGrowthCountryChips();
        fetchGDPGrowthData();
    } catch (err) {
        console.error('Failed to init GDP Growth:', err);
    }
    
    gdpGrowthState.isLoaded = true;
    window.gdpGrowthDataLoaded = true;
}

async function fetchGDPGrowthCountryList() {
    if (gdpGrowthState.countryListLoaded) return gdpGrowthState.countryMapping;
    
    const res = await fetch(`${API_BASE}/market/categories?category=${GDP_GROWTH_CONFIG.apiCategory}`);
    if (res.ok) {
        const data = await res.json();
        if (data.items) {
            gdpGrowthState.countryMapping = data.items;
            gdpGrowthState.countryListLoaded = true;
            const codes = Object.keys(data.items);
            const korCode = codes.find(c => {
                const n = data.items[c].name;
                return n && (n.includes('한국') || n.toLowerCase().includes('korea'));
            });
            gdpGrowthState.activeCountries = korCode ? [korCode] : (codes.length ? [codes[0]] : []);
        }
    }
    return gdpGrowthState.countryMapping;
}

function initGDPGrowthCountryChips() {
    const container = document.getElementById(`${GDP_GROWTH_CONFIG.chartPrefix}-country-chips`);
    if (!container) return;
    container.innerHTML = '';
    
    Object.keys(gdpGrowthState.countryMapping).forEach(code => {
        const info = gdpGrowthState.countryMapping[code];
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.setAttribute('data-item-code', code);
        
        const isActive = gdpGrowthState.activeCountries.includes(code);
        if (isActive) chip.classList.add('active');
        
        const color = getGDPGrowthCountryColor(code);
        const dot = document.createElement('div');
        dot.className = 'chip-dot';
        dot.style.background = isActive ? color : 'currentColor';
        if (isActive) { chip.style.borderColor = color; chip.style.color = color; }
        
        chip.appendChild(dot);
        chip.appendChild(document.createTextNode(getGDPGrowthCountryName(info.name)));
        chip.addEventListener('click', () => toggleGDPGrowthCountry(code));
        container.appendChild(chip);
    });
}

function toggleGDPGrowthCountry(itemCode) {
    const idx = gdpGrowthState.activeCountries.indexOf(itemCode);
    if (idx === -1) gdpGrowthState.activeCountries.push(itemCode);
    else gdpGrowthState.activeCountries.splice(idx, 1);
    initGDPGrowthCountryChips();
    if (validateGDPGrowthDateRange()) fetchGDPGrowthData();
}

function validateGDPGrowthDateRange() {
    const prefix = GDP_GROWTH_CONFIG.chartPrefix;
    const s = document.getElementById(`${prefix}-start-date`);
    const e = document.getElementById(`${prefix}-end-date`);
    return s && e && parseInt(s.value, 10) <= parseInt(e.value, 10);
}

// ============================================================
// DATA FETCHING
// ============================================================

async function fetchGDPGrowthData() {
    const prefix = GDP_GROWTH_CONFIG.chartPrefix;
    if (!validateGDPGrowthDateRange() || gdpGrowthState.activeCountries.length === 0) {
        updateGDPGrowthChart();
        return;
    }
    
    const startDate = `${document.getElementById(`${prefix}-start-date`).value}0101`;
    const endDate = `${document.getElementById(`${prefix}-end-date`).value}1231`;
    
    const container = document.getElementById(`${prefix}-chart-container`);
    if (container) container.style.opacity = '0.5';
    
    try {
        const results = await Promise.all(gdpGrowthState.activeCountries.map(async code => {
            const url = `${API_BASE}/market/indices?type=${GDP_GROWTH_CONFIG.apiCategory}&itemCode=${code}&startDate=${startDate}&endDate=${endDate}&cycle=A`;
            try {
                const res = await fetch(url);
                return { itemCode: code, data: await res.json() };
            } catch (e) {
                return { itemCode: code, data: { error: e.message } };
            }
        }));
        
        gdpGrowthState.countryData = {};
        results.forEach(({ itemCode, data }) => {
            if (!data.error && data.StatisticSearch?.row) {
                gdpGrowthState.countryData[itemCode] = data.StatisticSearch.row
                    .map(r => ({ date: r.TIME, value: parseFloat(r.DATA_VALUE) }))
                    .filter(i => !isNaN(i.value))
                    .sort((a, b) => parseInt(a.date) - parseInt(b.date));
            }
        });
        
        updateGDPGrowthChart();
    } finally {
        if (container) container.style.opacity = '1';
    }
}

// ============================================================
// CHART RENDERING
// ============================================================

function updateGDPGrowthChart() {
    const prefix = GDP_GROWTH_CONFIG.chartPrefix;
    const svg = document.getElementById(`${prefix}-chart-svg`);
    const pathsGroup = document.getElementById(`${prefix}-paths-group`);
    const pointsGroup = document.getElementById(`${prefix}-data-points`);
    
    if (!svg) return;
    if (pathsGroup) pathsGroup.innerHTML = '';
    else svg.querySelectorAll('.chart-path').forEach(e => e.remove());
    if (pointsGroup) pointsGroup.innerHTML = '';
    
    const allDates = new Set();
    Object.values(gdpGrowthState.countryData).forEach(d => d.forEach(i => allDates.add(i.date)));
    const sortedDates = Array.from(allDates).sort((a, b) => parseInt(a) - parseInt(b));
    
    if (sortedDates.length === 0) {
        renderGDPGrowthYAxis();
        renderGDPGrowthXAxis([]);
        return;
    }
    
    const allVals = [];
    Object.values(gdpGrowthState.countryData).forEach(d => d.forEach(i => allVals.push(i.value)));
    const min = Math.min(...allVals, 0);
    const max = Math.max(...allVals);
    const range = max - min || 1;
    gdpGrowthState.yAxisRange = { min: min - range * 0.05, max: max + range * 0.05 };
    
    renderGDPGrowthYAxis();
    
    gdpGrowthState.activeCountries.forEach(code => {
        const data = gdpGrowthState.countryData[code];
        if (!data?.length) return;
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.classList.add('chart-path', 'visible');
        path.setAttribute('stroke', getGDPGrowthCountryColor(code));
        path.setAttribute('stroke-width', '2.5');
        path.setAttribute('fill', 'none');
        
        const sortedData = sortedDates.map(d => data.find(i => i.date === d) || null).filter(Boolean);
        if (sortedData.length) {
            path.setAttribute('d', generateGDPGrowthPath(sortedData));
            (pathsGroup || svg).appendChild(path);
        }
    });
    
    renderGDPGrowthXAxis(sortedDates);
    setupGDPGrowthInteractivity();
    updateGDPGrowthHeader();
}

function generateGDPGrowthPath(data) {
    const svg = document.getElementById(`${GDP_GROWTH_CONFIG.chartPrefix}-chart-svg`);
    if (!svg || !data.length) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const pad = { top: 20, bottom: 30, left: 60, right: 20 };
    const cw = width - pad.left - pad.right;
    const ch = height - pad.top - pad.bottom;
    const { min, max } = gdpGrowthState.yAxisRange;
    const range = max - min || 1;
    
    return data.map((p, i) => {
        const x = pad.left + (i / (data.length - 1 || 1)) * cw;
        const y = pad.top + (1 - (p.value - min) / range) * ch;
        return i === 0 ? `M ${x},${y}` : `L ${x},${y}`;
    }).join(' ');
}

function renderGDPGrowthYAxis() {
    const g = document.getElementById(`${GDP_GROWTH_CONFIG.chartPrefix}-y-axis-labels`);
    if (!g) return;
    g.innerHTML = '';
    const { min, max } = gdpGrowthState.yAxisRange;
    for (let i = 0; i <= 5; i++) {
        const val = max - (i / 5) * (max - min);
        const y = 20 + (i / 5) * 330;
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', '55');
        t.setAttribute('y', y);
        t.setAttribute('class', 'chart-yaxis-label');
        t.setAttribute('text-anchor', 'end');
        t.textContent = val.toFixed(1) + '%';
        g.appendChild(t);
    }
}

function renderGDPGrowthXAxis(dates) {
    const g = document.getElementById(`${GDP_GROWTH_CONFIG.chartPrefix}-x-axis-labels`);
    if (!g || !dates.length) return;
    g.innerHTML = '';
    
    const svg = document.getElementById(`${GDP_GROWTH_CONFIG.chartPrefix}-chart-svg`);
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

let gdpGrowthCrosshairX = null;
let gdpGrowthCrosshairY = null;

function setupGDPGrowthInteractivity() {
    const prefix = GDP_GROWTH_CONFIG.chartPrefix;
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
    gdpGrowthCrosshairX = crosshairs.crosshairX;
    gdpGrowthCrosshairY = crosshairs.crosshairY;
    
    const newC = container.cloneNode(true);
    container.parentNode.replaceChild(newC, container);
    
    newC.addEventListener('mousemove', e => showGDPGrowthTooltip(e));
    newC.addEventListener('mouseleave', () => {
        hideGDPGrowthTooltip();
        hideCrosshair(gdpGrowthCrosshairX, gdpGrowthCrosshairY);
    });
}

function showGDPGrowthTooltip(event) {
    const prefix = GDP_GROWTH_CONFIG.chartPrefix;
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    const svg = document.getElementById(`${prefix}-chart-svg`);
    if (!tooltip || !svg) return;
    
    const allDates = new Set();
    Object.values(gdpGrowthState.countryData).forEach(d => d.forEach(i => allDates.add(i.date)));
    const dates = Array.from(allDates).sort((a, b) => parseInt(a) - parseInt(b));
    if (!dates.length) {
        hideCrosshair(gdpGrowthCrosshairX, gdpGrowthCrosshairY);
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
    if (gdpGrowthCrosshairX) {
        gdpGrowthCrosshairX.setAttribute('x1', crosshairXPos);
        gdpGrowthCrosshairX.setAttribute('x2', crosshairXPos);
        gdpGrowthCrosshairX.style.opacity = '1';
    }
    
    // Calculate average Y for crosshair
    let sumY = 0, countY = 0;
    gdpGrowthState.activeCountries.forEach(code => {
        const item = gdpGrowthState.countryData[code]?.find(d => d.date === date);
        if (item && Number.isFinite(item.value)) { sumY += item.value; countY++; }
    });
    
    if (countY > 0 && gdpGrowthCrosshairY) {
        const avgVal = sumY / countY;
        const { min, max } = gdpGrowthState.yAxisRange;
        const normY = (avgVal - min) / (max - min || 1);
        const crosshairYPos = pad.top + (1 - normY) * ch;
        gdpGrowthCrosshairY.setAttribute('y1', crosshairYPos);
        gdpGrowthCrosshairY.setAttribute('y2', crosshairYPos);
        gdpGrowthCrosshairY.style.opacity = '1';
    }
    
    let content = '';
    gdpGrowthState.activeCountries.forEach(code => {
        const item = gdpGrowthState.countryData[code]?.find(d => d.date === date);
        if (!item) return;
        const name = getGDPGrowthCountryName(gdpGrowthState.countryMapping[code]?.name || code);
        const color = getGDPGrowthCountryColor(code);
        content += `<div class="chart-tooltip-item">
            <div class="chart-tooltip-currency"><div class="chart-tooltip-dot" style="background:${color}"></div><span>${name}</span></div>
            <span class="chart-tooltip-value">${item.value.toFixed(1)}%</span>
        </div>`;
    });
    
    if (!content) return hideGDPGrowthTooltip();
    
    document.getElementById(`${prefix}-tooltip-content`).innerHTML = content;
    document.getElementById(`${prefix}-tooltip-date`).textContent = date;
    
    tooltip.classList.add('visible');
    tooltip.style.left = (event.clientX + 15) + 'px';
    tooltip.style.top = (event.clientY + 15) + 'px';
    tooltip.style.visibility = 'visible';
}

function hideGDPGrowthTooltip() {
    const t = document.getElementById(`${GDP_GROWTH_CONFIG.chartPrefix}-chart-tooltip`);
    if (t) { t.classList.remove('visible'); t.style.visibility = 'hidden'; }
    hideCrosshair(gdpGrowthCrosshairX, gdpGrowthCrosshairY);
}

function updateGDPGrowthHeader() {
    const prefix = GDP_GROWTH_CONFIG.chartPrefix;
    const code = gdpGrowthState.activeCountries[0];
    const data = gdpGrowthState.countryData[code];
    if (!data?.length) return;
    
    const vals = data.map(i => i.value);
    const current = vals[vals.length - 1];
    const name = getGDPGrowthCountryName(gdpGrowthState.countryMapping[code]?.name || code);
    
    const title = document.getElementById(`${prefix}-chart-main-title`);
    if (title) title.textContent = `Economy Growth Rate - ${name}`;
    
    const value = document.getElementById(`${prefix}-chart-main-value`);
    if (value) value.innerHTML = `${current.toFixed(1)}<span style="font-size:50%;opacity:0.8">%</span>`;
    
    const high = document.getElementById(`${prefix}-stat-high`);
    const low = document.getElementById(`${prefix}-stat-low`);
    const avg = document.getElementById(`${prefix}-stat-average`);
    if (high) high.textContent = Math.max(...vals).toFixed(1) + '%';
    if (low) low.textContent = Math.min(...vals).toFixed(1) + '%';
    if (avg) avg.textContent = (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) + '%';
}

// ============================================================
// EXPORTS
// ============================================================

window.initGDPGrowth = initGDPGrowth;
window.toggleGDPGrowthCountry = toggleGDPGrowthCountry;

console.log('📈 GDP Growth module loaded');
