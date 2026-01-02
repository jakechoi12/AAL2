/**
 * AAL Application - Employment Module
 * 고용/실업률 통계 관련 기능 모듈
 * 
 * 담당 패널: #employment-panel
 */

// ============================================================
// MODULE MARKER
// ============================================================
window.employmentModuleLoaded = true;

// ============================================================
// CONFIGURATION
// ============================================================

const EMPLOYMENT_CONFIG = {
    apiCategory: 'unemployment-international',
    panelId: 'employment-panel',
    title: 'Unemployment Rate',
    description: '국제 주요국 실업률(계절변동조정)',
    cycle: 'M',
    unit: '%',
    chartPrefix: 'employment'
};

// ============================================================
// STATE
// ============================================================

const employmentState = {
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

const employmentCountryMap = [
    { keywords: ['한국', 'kor', 'korea'], name: 'Korea', color: 'var(--c-interest-kor)' },
    { keywords: ['호주', 'aus', 'australia'], name: 'Australia', color: 'var(--c-interest-aus)' },
    { keywords: ['오스트리아', 'aut', 'austria'], name: 'Austria', color: '#E74C3C' },
    { keywords: ['벨기에', 'bel', 'belgium'], name: 'Belgium', color: '#F39C12' },
    { keywords: ['캐나다', 'can', 'canada'], name: 'Canada', color: 'var(--c-interest-can)' },
    { keywords: ['칠레', 'chl', 'chile'], name: 'Chile', color: 'var(--c-interest-chl)' },
    { keywords: ['체코', 'cze', 'czech'], name: 'Czech Republic', color: 'var(--c-interest-cze)' },
    { keywords: ['덴마크', 'dnk', 'denmark'], name: 'Denmark', color: 'var(--c-interest-dnk)' },
    { keywords: ['에스토니아', 'est', 'estonia'], name: 'Estonia', color: '#1ABC9C' },
    { keywords: ['핀란드', 'fin', 'finland'], name: 'Finland', color: '#3498DB' },
    { keywords: ['프랑스', 'fra', 'france'], name: 'France', color: 'var(--c-interest-fra)' },
    { keywords: ['독일', 'deu', 'germany'], name: 'Germany', color: 'var(--c-interest-deu)' },
    { keywords: ['그리스', 'grc', 'greece'], name: 'Greece', color: '#2980B9' },
    { keywords: ['헝가리', 'hun', 'hungary'], name: 'Hungary', color: 'var(--c-interest-hun)' },
    { keywords: ['아이슬란드', 'isl', 'iceland'], name: 'Iceland', color: '#7FB3D5' },
    { keywords: ['아일랜드', 'irl', 'ireland'], name: 'Ireland', color: '#27AE60' },
    { keywords: ['이스라엘', 'isr', 'israel'], name: 'Israel', color: 'var(--c-interest-isr)' },
    { keywords: ['이탈리아', 'ita', 'italy'], name: 'Italy', color: 'var(--c-interest-ita)' },
    { keywords: ['일본', 'jpn', 'japan'], name: 'Japan', color: 'var(--c-interest-jpn)' },
    { keywords: ['룩셈부르크', 'lux', 'luxembourg'], name: 'Luxembourg', color: '#F5B041' },
    { keywords: ['멕시코', 'mex', 'mexico'], name: 'Mexico', color: 'var(--c-interest-mex)' },
    { keywords: ['네덜란드', 'nld', 'netherlands'], name: 'Netherlands', color: '#E67E22' },
    { keywords: ['뉴질랜드', 'nzl', 'new zealand'], name: 'New Zealand', color: 'var(--c-interest-nzl)' },
    { keywords: ['노르웨이', 'nor', 'norway'], name: 'Norway', color: 'var(--c-interest-nor)' },
    { keywords: ['폴란드', 'pol', 'poland'], name: 'Poland', color: 'var(--c-interest-pol)' },
    { keywords: ['포르투갈', 'prt', 'portugal'], name: 'Portugal', color: '#9B59B6' },
    { keywords: ['슬로바키아', 'svk', 'slovakia'], name: 'Slovakia', color: '#34495E' },
    { keywords: ['슬로베니아', 'svn', 'slovenia'], name: 'Slovenia', color: '#16A085' },
    { keywords: ['스페인', 'esp', 'spain'], name: 'Spain', color: 'var(--c-interest-esp)' },
    { keywords: ['스웨덴', 'swe', 'sweden'], name: 'Sweden', color: 'var(--c-interest-swe)' },
    { keywords: ['스위스', 'che', 'switzerland'], name: 'Switzerland', color: 'var(--c-interest-che)' },
    { keywords: ['튀르키예', '터키', 'tur', 'turkey'], name: 'Turkey', color: 'var(--c-interest-tur)' },
    { keywords: ['영국', 'gbr', 'uk'], name: 'UK', color: 'var(--c-interest-gbr)' },
    { keywords: ['미국', 'usa', 'us ', 'united states'], name: 'USA', color: 'var(--c-interest-usa)' }
];

function getEmploymentCountryName(koreanName) {
    if (!koreanName) return koreanName;
    const n = koreanName.toLowerCase();
    for (const c of employmentCountryMap) {
        if (c.keywords.some(k => n.includes(k))) return c.name;
    }
    return koreanName;
}

function getEmploymentCountryColor(itemCode) {
    const info = employmentState.countryMapping[itemCode];
    if (!info) return '#4ECDC4';
    const n = info.name?.toLowerCase() || '';
    for (const c of employmentCountryMap) {
        if (c.keywords.some(k => n.includes(k))) return c.color;
    }
    return '#4ECDC4';
}

// ============================================================
// INITIALIZATION
// ============================================================

async function initEmployment() {
    const prefix = EMPLOYMENT_CONFIG.chartPrefix;
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
        
        startInput.addEventListener('change', () => validateEmploymentDateRange() && fetchEmploymentData());
        endInput.addEventListener('change', () => validateEmploymentDateRange() && fetchEmploymentData());
    }
    
    try {
        await fetchEmploymentCountryList();
        initEmploymentCountryChips();
        fetchEmploymentData();
    } catch (err) {
        console.error('Failed to init Employment:', err);
    }
    
    employmentState.isLoaded = true;
    window.employmentDataLoaded = true;
}

async function fetchEmploymentCountryList() {
    if (employmentState.countryListLoaded) return employmentState.countryMapping;
    
    const res = await fetch(`${API_BASE}/market/categories?category=${EMPLOYMENT_CONFIG.apiCategory}`);
    if (res.ok) {
        const data = await res.json();
        if (data.items) {
            employmentState.countryMapping = data.items;
            employmentState.countryListLoaded = true;
            const codes = Object.keys(data.items);
            const korCode = codes.find(c => {
                const n = data.items[c].name;
                return n && (n.includes('한국') || n.toLowerCase().includes('korea'));
            });
            employmentState.activeCountries = korCode ? [korCode] : (codes.length ? [codes[0]] : []);
        }
    }
    return employmentState.countryMapping;
}

function initEmploymentCountryChips() {
    const container = document.getElementById(`${EMPLOYMENT_CONFIG.chartPrefix}-country-chips`);
    if (!container) return;
    container.innerHTML = '';
    
    Object.keys(employmentState.countryMapping).forEach(code => {
        const info = employmentState.countryMapping[code];
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.setAttribute('data-item-code', code);
        
        const isActive = employmentState.activeCountries.includes(code);
        if (isActive) chip.classList.add('active');
        
        const color = getEmploymentCountryColor(code);
        const dot = document.createElement('div');
        dot.className = 'chip-dot';
        dot.style.background = isActive ? color : 'currentColor';
        if (isActive) { chip.style.borderColor = color; chip.style.color = color; }
        
        chip.appendChild(dot);
        chip.appendChild(document.createTextNode(getEmploymentCountryName(info.name)));
        chip.addEventListener('click', () => toggleEmploymentCountry(code));
        container.appendChild(chip);
    });
}

function toggleEmploymentCountry(itemCode) {
    const idx = employmentState.activeCountries.indexOf(itemCode);
    if (idx === -1) employmentState.activeCountries.push(itemCode);
    else employmentState.activeCountries.splice(idx, 1);
    initEmploymentCountryChips();
    if (validateEmploymentDateRange()) fetchEmploymentData();
}

function validateEmploymentDateRange() {
    const prefix = EMPLOYMENT_CONFIG.chartPrefix;
    const s = document.getElementById(`${prefix}-start-date`);
    const e = document.getElementById(`${prefix}-end-date`);
    return s && e && new Date(s.value) <= new Date(e.value);
}

// ============================================================
// DATA FETCHING
// ============================================================

async function fetchEmploymentData() {
    const prefix = EMPLOYMENT_CONFIG.chartPrefix;
    if (!validateEmploymentDateRange() || employmentState.activeCountries.length === 0) {
        updateEmploymentChart();
        return;
    }
    
    const startDate = formatDateForAPI(document.getElementById(`${prefix}-start-date`).value);
    const endDate = formatDateForAPI(document.getElementById(`${prefix}-end-date`).value);
    
    const container = document.getElementById(`${prefix}-chart-container`);
    if (container) container.style.opacity = '0.5';
    
    try {
        const results = await Promise.all(employmentState.activeCountries.map(async code => {
            const url = `${API_BASE}/market/indices?type=${EMPLOYMENT_CONFIG.apiCategory}&itemCode=${code}&startDate=${startDate}&endDate=${endDate}&cycle=M`;
            try {
                const res = await fetch(url);
                return { itemCode: code, data: await res.json() };
            } catch (e) {
                return { itemCode: code, data: { error: e.message } };
            }
        }));
        
        employmentState.countryData = {};
        results.forEach(({ itemCode, data }) => {
            if (!data.error && data.StatisticSearch?.row) {
                employmentState.countryData[itemCode] = data.StatisticSearch.row
                    .map(r => ({ date: r.TIME, value: parseFloat(r.DATA_VALUE) }))
                    .filter(i => !isNaN(i.value))
                    .sort((a, b) => a.date.localeCompare(b.date));
            }
        });
        
        updateEmploymentChart();
    } finally {
        if (container) container.style.opacity = '1';
    }
}

// ============================================================
// CHART RENDERING
// ============================================================

function updateEmploymentChart() {
    const prefix = EMPLOYMENT_CONFIG.chartPrefix;
    const svg = document.getElementById(`${prefix}-chart-svg`);
    const pathsGroup = document.getElementById(`${prefix}-paths-group`);
    const pointsGroup = document.getElementById(`${prefix}-data-points`);
    
    if (!svg) return;
    if (pathsGroup) pathsGroup.innerHTML = '';
    else svg.querySelectorAll('.chart-path').forEach(e => e.remove());
    if (pointsGroup) pointsGroup.innerHTML = '';
    
    const allDates = new Set();
    Object.values(employmentState.countryData).forEach(d => d.forEach(i => allDates.add(i.date)));
    const sortedDates = Array.from(allDates).sort();
    
    if (sortedDates.length === 0) {
        renderEmploymentYAxis();
        renderEmploymentXAxis([]);
        return;
    }
    
    const allVals = [];
    Object.values(employmentState.countryData).forEach(d => d.forEach(i => allVals.push(i.value)));
    const min = Math.min(...allVals);
    const max = Math.max(...allVals);
    const range = max - min || 1;
    employmentState.yAxisRange = { min: Math.max(0, min - range * 0.1), max: max + range * 0.1 };
    
    renderEmploymentYAxis();
    
    employmentState.activeCountries.forEach(code => {
        const data = employmentState.countryData[code];
        if (!data?.length) return;
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.classList.add('chart-path', 'visible');
        path.setAttribute('stroke', getEmploymentCountryColor(code));
        path.setAttribute('stroke-width', '2.5');
        path.setAttribute('fill', 'none');
        
        const sortedData = sortedDates.map(d => data.find(i => i.date === d) || null).filter(Boolean);
        if (sortedData.length) {
            path.setAttribute('d', generateEmploymentPath(sortedData));
            (pathsGroup || svg).appendChild(path);
        }
    });
    
    renderEmploymentXAxis(sortedDates);
    setupEmploymentInteractivity();
    updateEmploymentHeader();
}

function generateEmploymentPath(data) {
    const svg = document.getElementById(`${EMPLOYMENT_CONFIG.chartPrefix}-chart-svg`);
    if (!svg || !data.length) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const pad = { top: 20, bottom: 30, left: 60, right: 20 };
    const cw = width - pad.left - pad.right;
    const ch = height - pad.top - pad.bottom;
    const { min, max } = employmentState.yAxisRange;
    const range = max - min || 1;
    
    return data.map((p, i) => {
        const x = pad.left + (i / (data.length - 1 || 1)) * cw;
        const y = pad.top + (1 - (p.value - min) / range) * ch;
        return i === 0 ? `M ${x},${y}` : `L ${x},${y}`;
    }).join(' ');
}

function renderEmploymentYAxis() {
    const g = document.getElementById(`${EMPLOYMENT_CONFIG.chartPrefix}-y-axis-labels`);
    if (!g) return;
    g.innerHTML = '';
    const { min, max } = employmentState.yAxisRange;
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

function renderEmploymentXAxis(dates) {
    const g = document.getElementById(`${EMPLOYMENT_CONFIG.chartPrefix}-x-axis-labels`);
    if (!g || !dates.length) return;
    g.innerHTML = '';
    
    const svg = document.getElementById(`${EMPLOYMENT_CONFIG.chartPrefix}-chart-svg`);
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

let employmentCrosshairX = null;
let employmentCrosshairY = null;

function setupEmploymentInteractivity() {
    const prefix = EMPLOYMENT_CONFIG.chartPrefix;
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
    employmentCrosshairX = crosshairs.crosshairX;
    employmentCrosshairY = crosshairs.crosshairY;
    
    const newC = container.cloneNode(true);
    container.parentNode.replaceChild(newC, container);
    
    newC.addEventListener('mousemove', e => showEmploymentTooltip(e));
    newC.addEventListener('mouseleave', () => {
        hideEmploymentTooltip();
        hideCrosshair(employmentCrosshairX, employmentCrosshairY);
    });
}

function showEmploymentTooltip(event) {
    const prefix = EMPLOYMENT_CONFIG.chartPrefix;
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    const svg = document.getElementById(`${prefix}-chart-svg`);
    if (!tooltip || !svg) return;
    
    const allDates = new Set();
    Object.values(employmentState.countryData).forEach(d => d.forEach(i => allDates.add(i.date)));
    const dates = Array.from(allDates).sort();
    if (!dates.length) {
        hideCrosshair(employmentCrosshairX, employmentCrosshairY);
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
    if (employmentCrosshairX) {
        employmentCrosshairX.setAttribute('x1', crosshairXPos);
        employmentCrosshairX.setAttribute('x2', crosshairXPos);
        employmentCrosshairX.style.opacity = '1';
    }
    
    // Calculate average Y for crosshair
    let sumY = 0, countY = 0;
    employmentState.activeCountries.forEach(code => {
        const item = employmentState.countryData[code]?.find(d => d.date === date);
        if (item && Number.isFinite(item.value)) { sumY += item.value; countY++; }
    });
    
    if (countY > 0 && employmentCrosshairY) {
        const avgVal = sumY / countY;
        const { min, max } = employmentState.yAxisRange;
        const normY = (avgVal - min) / (max - min || 1);
        const crosshairYPos = pad.top + (1 - normY) * ch;
        employmentCrosshairY.setAttribute('y1', crosshairYPos);
        employmentCrosshairY.setAttribute('y2', crosshairYPos);
        employmentCrosshairY.style.opacity = '1';
    }
    
    let content = '';
    employmentState.activeCountries.forEach(code => {
        const item = employmentState.countryData[code]?.find(d => d.date === date);
        if (!item) return;
        const name = getEmploymentCountryName(employmentState.countryMapping[code]?.name || code);
        const color = getEmploymentCountryColor(code);
        content += `<div class="chart-tooltip-item">
            <div class="chart-tooltip-currency"><div class="chart-tooltip-dot" style="background:${color}"></div><span>${name}</span></div>
            <span class="chart-tooltip-value">${item.value.toFixed(1)}%</span>
        </div>`;
    });
    
    if (!content) return hideEmploymentTooltip();
    
    document.getElementById(`${prefix}-tooltip-content`).innerHTML = content;
    document.getElementById(`${prefix}-tooltip-date`).textContent = 
        date.length === 6 ? `${date.slice(0, 4)}.${date.slice(4)}` : date;
    
    tooltip.classList.add('visible');
    tooltip.style.left = (event.clientX + 15) + 'px';
    tooltip.style.top = (event.clientY + 15) + 'px';
    tooltip.style.visibility = 'visible';
}

function hideEmploymentTooltip() {
    const t = document.getElementById(`${EMPLOYMENT_CONFIG.chartPrefix}-chart-tooltip`);
    if (t) { t.classList.remove('visible'); t.style.visibility = 'hidden'; }
    hideCrosshair(employmentCrosshairX, employmentCrosshairY);
}

function updateEmploymentHeader() {
    const prefix = EMPLOYMENT_CONFIG.chartPrefix;
    const code = employmentState.activeCountries[0];
    const data = employmentState.countryData[code];
    if (!data?.length) return;
    
    const vals = data.map(i => i.value);
    const current = vals[vals.length - 1];
    const name = getEmploymentCountryName(employmentState.countryMapping[code]?.name || code);
    
    const title = document.getElementById(`${prefix}-chart-main-title`);
    if (title) title.textContent = `Unemployment Rate - ${name}`;
    
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

window.initEmployment = initEmployment;
window.toggleEmploymentCountry = toggleEmploymentCountry;

console.log('👥 Employment module loaded');
