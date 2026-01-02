/**
 * AAL Application - Trade Module
 * 수출입 통계 관련 기능 모듈
 * 
 * 담당 패널: #trade-panel
 * 주요 기능: 수출입 차트, 무역수지
 */

// ============================================================
// MODULE MARKER
// ============================================================
window.tradeModuleLoaded = true;

// ============================================================
// CONFIGURATION
// ============================================================

const TRADE_CONFIG = {
    apiCategory: 'trade',
    panelId: 'trade-panel',
    title: 'Export x Import',
    description: '한국 수출입 통계',
    cycle: 'M',
    unit: 'M USD',
    chartPrefix: 'trade'
};

// ============================================================
// STATE
// ============================================================

const tradeState = {
    exportData: [],
    importData: [],
    balanceData: [],
    yAxisRange: { min: 0, max: 0 },
    isLoaded: false,
    activeIndicators: ['export', 'import', 'balance']
};

// ============================================================
// INITIALIZATION
// ============================================================

async function initTrade() {
    const prefix = TRADE_CONFIG.chartPrefix;
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
        
        startInput.addEventListener('change', () => validateTradeDateRange() && fetchTradeData());
        endInput.addEventListener('change', () => validateTradeDateRange() && fetchTradeData());
    }
    
    // Initialize indicator toggles
    initTradeIndicatorToggles();
    
    try {
        await fetchTradeData();
    } catch (err) {
        console.error('Failed to init Trade:', err);
    }
    
    tradeState.isLoaded = true;
    window.tradeDataLoaded = true;
}

function initTradeIndicatorToggles() {
    const prefix = TRADE_CONFIG.chartPrefix;
    const container = document.getElementById(`${prefix}-indicator-toggles`);
    if (!container) return;
    
    container.innerHTML = '';
    
    const indicators = [
        { id: 'export', name: 'Export', color: 'var(--c-trade-export)' },
        { id: 'import', name: 'Import', color: 'var(--c-trade-import)' },
        { id: 'balance', name: 'Trade Balance', color: 'var(--c-trade-balance)' }
    ];
    
    indicators.forEach(ind => {
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.setAttribute('data-indicator', ind.id);
        
        const isActive = tradeState.activeIndicators.includes(ind.id);
        if (isActive) chip.classList.add('active');
        
        const dot = document.createElement('div');
        dot.className = 'chip-dot';
        dot.style.background = isActive ? ind.color : 'currentColor';
        if (isActive) { chip.style.borderColor = ind.color; chip.style.color = ind.color; }
        
        chip.appendChild(dot);
        chip.appendChild(document.createTextNode(ind.name));
        chip.addEventListener('click', () => toggleTradeIndicator(ind.id));
        container.appendChild(chip);
    });
}

function toggleTradeIndicator(indicatorId) {
    const idx = tradeState.activeIndicators.indexOf(indicatorId);
    if (idx === -1) tradeState.activeIndicators.push(indicatorId);
    else if (tradeState.activeIndicators.length > 1) tradeState.activeIndicators.splice(idx, 1);
    
    initTradeIndicatorToggles();
    updateTradeChart();
}

function validateTradeDateRange() {
    const prefix = TRADE_CONFIG.chartPrefix;
    const s = document.getElementById(`${prefix}-start-date`);
    const e = document.getElementById(`${prefix}-end-date`);
    return s && e && new Date(s.value) <= new Date(e.value);
}

// ============================================================
// DATA FETCHING
// ============================================================

async function fetchTradeData() {
    const prefix = TRADE_CONFIG.chartPrefix;
    if (!validateTradeDateRange()) {
        updateTradeChart();
        return;
    }
    
    const startInput = document.getElementById(`${prefix}-start-date`);
    const endInput = document.getElementById(`${prefix}-end-date`);
    const startDate = formatDateForAPI(startInput.value);
    const endDate = formatDateForAPI(endInput.value);
    
    const container = document.getElementById(`${prefix}-chart-container`);
    if (container) container.style.opacity = '0.5';
    
    try {
        // Fetch export data
        const exportUrl = `${API_BASE}/market/indices?type=trade-export&startDate=${startDate}&endDate=${endDate}&cycle=M`;
        const importUrl = `${API_BASE}/market/indices?type=trade-import&startDate=${startDate}&endDate=${endDate}&cycle=M`;
        
        const [exportRes, importRes] = await Promise.all([
            fetch(exportUrl).then(r => r.json()),
            fetch(importUrl).then(r => r.json())
        ]);
        
        tradeState.exportData = processTradeApiData(exportRes);
        tradeState.importData = processTradeApiData(importRes);
        
        // Calculate trade balance
        const allDates = new Set([
            ...tradeState.exportData.map(d => d.date),
            ...tradeState.importData.map(d => d.date)
        ]);
        
        tradeState.balanceData = Array.from(allDates).sort().map(date => {
            const exp = tradeState.exportData.find(d => d.date === date);
            const imp = tradeState.importData.find(d => d.date === date);
            return {
                date,
                value: (exp?.value || 0) - (imp?.value || 0)
            };
        });
        
        updateTradeChart();
    } catch (err) {
        console.error('Failed to fetch trade data:', err);
    } finally {
        if (container) container.style.opacity = '1';
    }
}

function processTradeApiData(apiData) {
    if (!apiData?.StatisticSearch?.row) return [];
    return apiData.StatisticSearch.row
        .map(r => ({ date: r.TIME, value: parseFloat(r.DATA_VALUE) }))
        .filter(i => !isNaN(i.value))
        .sort((a, b) => a.date.localeCompare(b.date));
}

// ============================================================
// CHART RENDERING
// ============================================================

function updateTradeChart() {
    const prefix = TRADE_CONFIG.chartPrefix;
    const svg = document.getElementById(`${prefix}-chart-svg`);
    const pathsGroup = document.getElementById(`${prefix}-paths-group`);
    const pointsGroup = document.getElementById(`${prefix}-data-points`);
    
    if (!svg) return;
    if (pathsGroup) pathsGroup.innerHTML = '';
    else svg.querySelectorAll('.chart-path').forEach(e => e.remove());
    if (pointsGroup) pointsGroup.innerHTML = '';
    
    const allDates = new Set();
    if (tradeState.activeIndicators.includes('export')) {
        tradeState.exportData.forEach(d => allDates.add(d.date));
    }
    if (tradeState.activeIndicators.includes('import')) {
        tradeState.importData.forEach(d => allDates.add(d.date));
    }
    if (tradeState.activeIndicators.includes('balance')) {
        tradeState.balanceData.forEach(d => allDates.add(d.date));
    }
    
    const sortedDates = Array.from(allDates).sort();
    
    if (sortedDates.length === 0) {
        renderTradeYAxis();
        renderTradeXAxis([]);
        return;
    }
    
    // Calculate Y-axis range
    const allVals = [];
    if (tradeState.activeIndicators.includes('export')) {
        tradeState.exportData.forEach(d => allVals.push(d.value));
    }
    if (tradeState.activeIndicators.includes('import')) {
        tradeState.importData.forEach(d => allVals.push(d.value));
    }
    if (tradeState.activeIndicators.includes('balance')) {
        tradeState.balanceData.forEach(d => allVals.push(d.value));
    }
    
    const min = Math.min(...allVals);
    const max = Math.max(...allVals);
    const range = max - min || 1;
    tradeState.yAxisRange = { min: min - range * 0.05, max: max + range * 0.05 };
    
    renderTradeYAxis();
    
    // Render paths
    const datasets = [
        { id: 'export', data: tradeState.exportData, color: 'var(--c-trade-export)' },
        { id: 'import', data: tradeState.importData, color: 'var(--c-trade-import)' },
        { id: 'balance', data: tradeState.balanceData, color: 'var(--c-trade-balance)' }
    ];
    
    datasets.forEach(ds => {
        if (!tradeState.activeIndicators.includes(ds.id) || !ds.data?.length) return;
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.classList.add('chart-path', 'visible');
        path.setAttribute('stroke', ds.color);
        path.setAttribute('stroke-width', '2.5');
        path.setAttribute('fill', 'none');
        
        path.setAttribute('d', generateTradePath(ds.data, sortedDates));
        (pathsGroup || svg).appendChild(path);
    });
    
    renderTradeXAxis(sortedDates);
    setupTradeInteractivity(sortedDates);
    updateTradeHeader();
}

function generateTradePath(data, sortedDates) {
    const svg = document.getElementById(`${TRADE_CONFIG.chartPrefix}-chart-svg`);
    if (!svg || !data.length) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const pad = { top: 20, bottom: 30, left: 60, right: 20 };
    const cw = width - pad.left - pad.right;
    const ch = height - pad.top - pad.bottom;
    const { min, max } = tradeState.yAxisRange;
    const range = max - min || 1;
    
    const sortedData = sortedDates.map(d => data.find(i => i.date === d) || null).filter(Boolean);
    
    return sortedData.map((p, i) => {
        const x = pad.left + (i / (sortedData.length - 1 || 1)) * cw;
        const y = pad.top + (1 - (p.value - min) / range) * ch;
        return i === 0 ? `M ${x},${y}` : `L ${x},${y}`;
    }).join(' ');
}

function renderTradeYAxis() {
    const g = document.getElementById(`${TRADE_CONFIG.chartPrefix}-y-axis-labels`);
    if (!g) return;
    g.innerHTML = '';
    const { min, max } = tradeState.yAxisRange;
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

function renderTradeXAxis(dates) {
    const g = document.getElementById(`${TRADE_CONFIG.chartPrefix}-x-axis-labels`);
    if (!g || !dates.length) return;
    g.innerHTML = '';
    
    const svg = document.getElementById(`${TRADE_CONFIG.chartPrefix}-chart-svg`);
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
        // Format: YYYYMM -> YY.MM
        t.textContent = d.length === 6 ? `${d.slice(2, 4)}.${d.slice(4)}` : d;
        g.appendChild(t);
    });
}

function setupTradeInteractivity(sortedDates) {
    const prefix = TRADE_CONFIG.chartPrefix;
    const container = document.getElementById(`${prefix}-chart-container`);
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    if (!container || !tooltip) return;
    
    if (tooltip.parentElement !== document.body) document.body.appendChild(tooltip);
    
    const newC = container.cloneNode(true);
    container.parentNode.replaceChild(newC, container);
    
    newC.addEventListener('mousemove', e => showTradeTooltip(e, sortedDates));
    newC.addEventListener('mouseleave', () => hideTradeTooltip());
}

function showTradeTooltip(event, sortedDates) {
    const prefix = TRADE_CONFIG.chartPrefix;
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    const svg = document.getElementById(`${prefix}-chart-svg`);
    if (!tooltip || !svg || !sortedDates?.length) return;
    
    const rect = svg.getBoundingClientRect();
    const { width } = getSvgViewBoxSize(svg);
    const x = event.clientX - rect.left;
    const idx = Math.round(((x / rect.width * width) - 60) / (width - 80) * (sortedDates.length - 1));
    const date = sortedDates[Math.max(0, Math.min(sortedDates.length - 1, idx))];
    
    let content = '';
    const items = [
        { id: 'export', data: tradeState.exportData, name: 'Export', color: 'var(--c-trade-export)' },
        { id: 'import', data: tradeState.importData, name: 'Import', color: 'var(--c-trade-import)' },
        { id: 'balance', data: tradeState.balanceData, name: 'Balance', color: 'var(--c-trade-balance)' }
    ];
    
    items.forEach(item => {
        if (!tradeState.activeIndicators.includes(item.id)) return;
        const val = item.data.find(d => d.date === date);
        if (!val) return;
        content += `<div class="chart-tooltip-item">
            <div class="chart-tooltip-currency"><div class="chart-tooltip-dot" style="background:${item.color}"></div><span>${item.name}</span></div>
            <span class="chart-tooltip-value">${val.value.toLocaleString()} M USD</span>
        </div>`;
    });
    
    if (!content) return hideTradeTooltip();
    
    document.getElementById(`${prefix}-tooltip-content`).innerHTML = content;
    document.getElementById(`${prefix}-tooltip-date`).textContent = 
        date.length === 6 ? `${date.slice(0, 4)}.${date.slice(4)}` : date;
    
    tooltip.classList.add('visible');
    tooltip.style.left = (event.clientX + 15) + 'px';
    tooltip.style.top = (event.clientY + 15) + 'px';
    tooltip.style.visibility = 'visible';
}

function hideTradeTooltip() {
    const t = document.getElementById(`${TRADE_CONFIG.chartPrefix}-chart-tooltip`);
    if (t) { t.classList.remove('visible'); t.style.visibility = 'hidden'; }
}

function updateTradeHeader() {
    const prefix = TRADE_CONFIG.chartPrefix;
    
    const title = document.getElementById(`${prefix}-chart-main-title`);
    if (title) title.textContent = 'Korea Export x Import';
    
    // Use export data for main value
    if (tradeState.exportData.length) {
        const current = tradeState.exportData[tradeState.exportData.length - 1];
        const value = document.getElementById(`${prefix}-chart-main-value`);
        if (value) {
            value.innerHTML = `${current.value.toLocaleString()} <span style="font-size:50%;opacity:0.8">M USD (Export)</span>`;
        }
        
        const vals = tradeState.exportData.map(i => i.value);
        const high = document.getElementById(`${prefix}-stat-high`);
        const low = document.getElementById(`${prefix}-stat-low`);
        const avg = document.getElementById(`${prefix}-stat-average`);
        if (high) high.textContent = Math.max(...vals).toLocaleString();
        if (low) low.textContent = Math.min(...vals).toLocaleString();
        if (avg) avg.textContent = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length).toLocaleString();
    }
}

// ============================================================
// EXPORTS
// ============================================================

window.initTrade = initTrade;
window.toggleTradeIndicator = toggleTradeIndicator;

console.log('🚢 Trade module loaded');
