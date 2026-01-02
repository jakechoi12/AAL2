/**
 * AAL Application - Exchange Rate USD Module
 * 대미달러 환율 관련 기능 모듈
 * 
 * 담당 패널: #exchange-rate-usd-panel
 * 주요 기능: USD 기준 환율 차트, 통화 비교
 * API: 731Y002 (대미달러 환율)
 */

// ============================================================
// MODULE MARKER
// ============================================================
window.exchangeRateUsdModuleLoaded = true;

// ============================================================
// USD Exchange Rate State
// ============================================================
const UsdExchangeState = {
    exchangeRates: {},
    activeCurrencies: ['JPY'],
    chartData: {},
    previousRates: {},
    yAxisRange: { min: 0, max: 0 },
    tooltipCache: { allDates: [], perCurrency: {} },
    currentRangeKey: null,
    chartInteractivitySetup: false
};

// ============================================================
// DATE INPUT FUNCTIONS
// ============================================================

function initUsdDateInputs() {
    const panel = document.getElementById('exchange-rate-usd-panel');
    if (!panel) return;
    
    const dateInputs = panel.querySelectorAll('.date-input');
    if (dateInputs.length < 2) return;
    
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 90);
    
    const startDateStr = start.toISOString().split('T')[0];
    const endDateStr = end.toISOString().split('T')[0];
    
    dateInputs[0].value = startDateStr;
    dateInputs[1].value = endDateStr;
    dateInputs[0].max = endDateStr;
    dateInputs[1].max = endDateStr;
}

function validateUsdDateRange() {
    const panel = document.getElementById('exchange-rate-usd-panel');
    if (!panel) return false;
    
    const dateInputs = panel.querySelectorAll('.date-input');
    if (dateInputs.length < 2) return false;
    
    const startDate = new Date(dateInputs[0].value);
    const endDate = new Date(dateInputs[1].value);
    
    if (startDate > endDate) {
        alert('Start date must be before end date.');
        return false;
    }
    
    return true;
}

function setUsdDateRange(days, periodKey = null) {
    const panel = document.getElementById('exchange-rate-usd-panel');
    if (!panel) return;
    
    const dateInputs = panel.querySelectorAll('.date-input');
    if (dateInputs.length < 2) return;
    
    const end = new Date();
    let start;
    
    if (periodKey === '1Y') {
        start = new Date(end.getFullYear(), end.getMonth() - 11, 1);
    } else {
        start = new Date();
        start.setDate(start.getDate() - days);
    }
    
    const startDateStr = start.toISOString().split('T')[0];
    const endDateStr = end.toISOString().split('T')[0];
    
    dateInputs[0].value = startDateStr;
    dateInputs[1].value = endDateStr;
    
    panel.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (validateUsdDateRange()) {
        fetchUsdExchangeRateData();
    }
}

function handleUsdPeriodClick(period) {
    const days = {
        '1W': 7,
        '1M': 30,
        '3M': 90,
        '1Y': 365
    };
    
    if (days[period]) {
        UsdExchangeState.currentRangeKey = period;
        setUsdDateRange(days[period], period);
    }
}

// ============================================================
// API FUNCTIONS
// ============================================================

async function fetchUsdExchangeRateData() {
    if (!validateUsdDateRange()) return;
    
    const panel = document.getElementById('exchange-rate-usd-panel');
    if (!panel) return;
    
    const dateInputs = panel.querySelectorAll('.date-input');
    if (dateInputs.length < 2) return;
    
    const startDate = formatDateForAPI(dateInputs[0].value);
    const endDate = formatDateForAPI(dateInputs[1].value);
    
    const validCurrencies = UsdExchangeState.activeCurrencies.filter(curr => USD_CURRENCY_MAPPING[curr]);
    
    if (validCurrencies.length === 0) {
        console.warn('No valid USD currencies selected');
        return;
    }
    
    const chartContainer = document.getElementById('usd-chart-container');
    if (chartContainer) {
        chartContainer.style.opacity = '0.5';
    }
    
    try {
        const fetchPromises = validCurrencies.map(async (currency) => {
            const itemCode = USD_CURRENCY_MAPPING[currency];
            const url = `${API_BASE}/market/indices?type=exchange-usd&itemCode=${itemCode}&startDate=${startDate}&endDate=${endDate}`;
            
            try {
                const response = await fetch(url);
                const json = await response.json();
                return { currency, data: json };
            } catch (err) {
                console.error(`Failed to fetch USD ${currency}:`, err);
                return { currency, data: { error: err.message } };
            }
        });
        
        const results = await Promise.all(fetchPromises);
        processUsdExchangeRateData(results);
        
    } catch (err) {
        console.error('Failed to fetch USD exchange rate data:', err);
    } finally {
        if (chartContainer) {
            chartContainer.style.opacity = '1';
        }
    }
}

async function fetchUsdExchangeRateStats(currency, startDate, endDate) {
    try {
        const itemCode = USD_CURRENCY_MAPPING[currency];
        if (!itemCode) return null;
        
        const url = `${API_BASE}/market/indices/stats?type=exchange-usd&itemCode=${itemCode}&startDate=${startDate}&endDate=${endDate}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.error) {
            console.error(`Stats error for USD ${currency}:`, data.error);
            return null;
        }
        
        return data;
    } catch (err) {
        console.error(`Failed to fetch USD stats for ${currency}:`, err);
        return null;
    }
}

// ============================================================
// DATA PROCESSING FUNCTIONS
// ============================================================

function processUsdExchangeRateData(results) {
    UsdExchangeState.chartData = {};
    
    const panel = document.getElementById('exchange-rate-usd-panel');
    let startDateStr = '';
    let endDateStr = '';
    
    if (panel) {
        const dateInputs = panel.querySelectorAll('.date-input');
        if (dateInputs.length >= 2) {
            startDateStr = dateInputs[0].value;
            endDateStr = dateInputs[1].value;
        }
    }
    
    results.forEach(result => {
        const { currency, data } = result;
        
        if (data.error) {
            console.error(`Error for USD ${currency}:`, data.error);
            return;
        }
        
        if (data.StatisticSearch && data.StatisticSearch.row) {
            const rows = data.StatisticSearch.row;
            
            const rawValues = rows.map(row => ({
                date: row.TIME,
                value: parseFloat(row.DATA_VALUE)
            }));
            
            let values = rawValues;
            if (startDateStr && endDateStr && typeof fillMissingDates === 'function') {
                values = fillMissingDates(rawValues, startDateStr, endDateStr);
            }
            
            UsdExchangeState.chartData[currency] = values;
            
            const actualValues = values.filter(v => v.isActual !== false);
            if (actualValues.length > 0) {
                const latest = actualValues[actualValues.length - 1];
                const previous = actualValues.length > 1 ? actualValues[actualValues.length - 2] : null;
                
                if (previous) {
                    UsdExchangeState.previousRates[currency] = previous.value;
                }
                
                UsdExchangeState.exchangeRates[currency] = latest.value;
            }
        }
    });
    
    rebuildUsdTooltipCache();
    updateUsdChart();
    setupUsdChartInteractivity();
    
    if (UsdExchangeState.activeCurrencies.length > 0) {
        const primaryCurrency = UsdExchangeState.activeCurrencies[0];
        if (panel) {
            const dateInputs = panel.querySelectorAll('.date-input');
            if (dateInputs.length >= 2) {
                const startDate = formatDateForAPI(dateInputs[0].value);
                const endDate = formatDateForAPI(dateInputs[1].value);
                fetchUsdExchangeRateStats(primaryCurrency, startDate, endDate)
                    .then(stats => {
                        if (stats) {
                            updateUsdChartHeader(primaryCurrency, stats);
                        }
                    });
            }
        }
    }
}

function rebuildUsdTooltipCache() {
    const perCurrency = {};
    const allDatesSet = new Set();

    Object.keys(UsdExchangeState.chartData || {}).forEach(curr => {
        const arr = UsdExchangeState.chartData[curr] || [];
        if (!Array.isArray(arr) || arr.length === 0) return;

        const map = {};
        const dates = new Array(arr.length);
        for (let i = 0; i < arr.length; i++) {
            const item = arr[i];
            map[item.date] = item;
            dates[i] = item.date;
            allDatesSet.add(item.date);
        }
        dates.sort();
        perCurrency[curr] = { map, dates };
    });

    UsdExchangeState.tooltipCache = {
        allDates: Array.from(allDatesSet).sort(),
        perCurrency
    };
}

// ============================================================
// CHART RENDERING FUNCTIONS
// ============================================================

function generateUsdSVGPath(currency, data) {
    if (!data || data.length === 0) return '';
    
    const svg = document.getElementById('usd-chart-svg');
    if (!svg) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const minValue = UsdExchangeState.yAxisRange.min;
    const maxValue = UsdExchangeState.yAxisRange.max;
    const valueRange = maxValue - minValue || 1;
    
    let pathData = '';
    data.forEach((point, index) => {
        const x = padding.left + (index / (data.length - 1 || 1)) * chartWidth;
        const normalizedValue = (point.value - minValue) / valueRange;
        const y = padding.top + (1 - normalizedValue) * chartHeight;
        
        if (index === 0) {
            pathData = `M ${x},${y}`;
        } else {
            pathData += ` L ${x},${y}`;
        }
    });
    
    return pathData;
}

function renderUsdYAxisLabels() {
    const svg = document.getElementById('usd-chart-svg');
    const g = document.getElementById('usd-y-axis-labels');
    if (!svg || !g) return;

    g.innerHTML = '';

    let minValue = Infinity;
    let maxValue = -Infinity;

    UsdExchangeState.activeCurrencies.forEach(currency => {
        const data = UsdExchangeState.chartData[currency];
        if (data && data.length > 0) {
            const values = data.map(d => d.value);
            const dataMin = Math.min(...values);
            const dataMax = Math.max(...values);
            minValue = Math.min(minValue, dataMin);
            maxValue = Math.max(maxValue, dataMax);
        }
    });

    if (minValue === Infinity || maxValue === Infinity) {
        UsdExchangeState.yAxisRange.min = 0;
        UsdExchangeState.yAxisRange.max = 0;
        return;
    }

    const range = maxValue - minValue;
    let paddingPercent = 0.01;
    if (range > 1000) paddingPercent = 0.003;
    else if (range > 100) paddingPercent = 0.005;
    
    const padding = range * paddingPercent;
    
    const calculatedMin = minValue - padding;
    const calculatedMax = maxValue + padding;
    
    const minValueRatio = minValue / (maxValue || 1);
    if (calculatedMin < 0 || (minValueRatio < 0.05 && minValue < range * 0.1)) {
        UsdExchangeState.yAxisRange.min = 0;
        UsdExchangeState.yAxisRange.max = maxValue + padding + Math.abs(Math.min(0, calculatedMin));
    } else {
        UsdExchangeState.yAxisRange.min = calculatedMin;
        UsdExchangeState.yAxisRange.max = calculatedMax;
    }
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding_axis = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartHeight = height - padding_axis.top - padding_axis.bottom;

    const numLabels = 6;
    const step = (UsdExchangeState.yAxisRange.max - UsdExchangeState.yAxisRange.min) / (numLabels - 1);

    for (let i = 0; i < numLabels; i++) {
        const value = UsdExchangeState.yAxisRange.max - (step * i);
        const y = padding_axis.top + (i / (numLabels - 1)) * chartHeight;

        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', String(padding_axis.left - 10));
        label.setAttribute('y', String(y));
        label.setAttribute('class', 'chart-yaxis-label');
        label.textContent = value.toLocaleString('en-US', { 
            minimumFractionDigits: 4, 
            maximumFractionDigits: 4 
        });
        g.appendChild(label);
    }
}

function renderUsdXAxisLabels() {
    const svg = document.getElementById('usd-chart-svg');
    const g = document.getElementById('usd-x-axis-labels');
    if (!svg || !g) return;

    g.innerHTML = '';

    const tooltipCache = UsdExchangeState.tooltipCache;
    const dates = (tooltipCache && tooltipCache.allDates) ? tooltipCache.allDates : [];
    if (!dates || dates.length === 0) return;

    const rangeKey = UsdExchangeState.currentRangeKey;
    
    const panel = document.getElementById('exchange-rate-usd-panel');
    let endDateOverride = null;
    if (panel) {
        const dateInputs = panel.querySelectorAll('.date-input');
        if (dateInputs.length >= 2 && dateInputs[1].value) {
            endDateOverride = dateInputs[1].value;
        }
    }
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { left: 40, right: 20, top: 20, bottom: 30 };
    const chartWidth = width - padding.left - padding.right;
    const y = height - padding.bottom + 15;

    const targets = buildXAxisTargets(rangeKey, dates, endDateOverride);
    const n = dates.length;

    for (const tInfo of targets) {
        const i = tInfo.idx;
        const x = padding.left + (i / (n - 1 || 1)) * chartWidth;
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', x.toFixed(2));
        t.setAttribute('y', String(y));
        t.setAttribute('text-anchor', 'middle');
        t.setAttribute('dominant-baseline', 'middle');
        t.setAttribute('class', 'chart-xaxis-label');
        t.textContent = tInfo.label;
        g.appendChild(t);
    }
}

function updateUsdChart() {
    const pathsGroup = document.getElementById('usd-paths-group');
    if (!pathsGroup) return;
    
    pathsGroup.innerHTML = '';
    
    renderUsdYAxisLabels();
    
    const colors = {
        'JPY': '#E53935',
        'EUR': '#1E88E5',
        'GBP': '#7B1FA2',
        'CNY': '#FDD835',
        'CAD': '#43A047',
        'CHF': '#F57C00',
        'HKD': '#00ACC1',
        'AUD': '#FFB300',
        'NZD': '#8E24AA',
        'SEK': '#00897B',
        'NOK': '#D81B60',
        'DKK': '#5E35B1',
        'RUB': '#3949AB',
        'INR': '#039BE5',
        'BRL': '#7CB342',
        'MXN': '#C0CA33'
    };
    
    UsdExchangeState.activeCurrencies.forEach(currency => {
        if (!USD_CURRENCY_MAPPING[currency]) return;
        
        const data = UsdExchangeState.chartData[currency];
        if (data && data.length > 0) {
            const pathData = generateUsdSVGPath(currency, data);
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('id', `usd-path-${currency}`);
            path.setAttribute('class', 'chart-path visible');
            path.setAttribute('d', pathData);
            path.setAttribute('style', `stroke: ${colors[currency] || '#888'};`);
            pathsGroup.appendChild(path);
        }
    });
    
    renderUsdXAxisLabels();
}

function toggleUsdCurrency(curr) {
    const panel = document.getElementById('exchange-rate-usd-panel');
    if (!panel) return;
    
    const btn = panel.querySelector(`.chip[data-curr="${curr}"]`);
    if (!btn) return;
    
    btn.classList.toggle('active');
    const isActive = btn.classList.contains('active');
    
    if (isActive) {
        if (!UsdExchangeState.activeCurrencies.includes(curr)) {
            UsdExchangeState.activeCurrencies.push(curr);
        }
    } else {
        UsdExchangeState.activeCurrencies = UsdExchangeState.activeCurrencies.filter(c => c !== curr);
    }
    
    if (isActive && (!UsdExchangeState.chartData[curr] || UsdExchangeState.chartData[curr].length === 0)) {
        fetchUsdExchangeRateData();
    } else {
        updateUsdChart();
        
        if (UsdExchangeState.activeCurrencies.length > 0) {
            const primaryCurrency = UsdExchangeState.activeCurrencies[0];
            const dateInputs = panel.querySelectorAll('.date-input');
            if (dateInputs.length >= 2) {
                const startDate = formatDateForAPI(dateInputs[0].value);
                const endDate = formatDateForAPI(dateInputs[1].value);
                fetchUsdExchangeRateStats(primaryCurrency, startDate, endDate)
                    .then(stats => {
                        if (stats) {
                            updateUsdChartHeader(primaryCurrency, stats);
                        }
                    });
            }
        }
    }
}

// ============================================================
// TOOLTIP & INTERACTIVITY
// ============================================================

function getUsdDateFromMouseX(mouseX) {
    const svg = document.getElementById('usd-chart-svg');
    if (!svg) return null;
    
    const svgRect = svg.getBoundingClientRect();
    const { width: vbW } = getSvgViewBoxSize(svg);
    const padding = { left: 40, right: 20 };
    const padLeftPx = (padding.left / vbW) * svgRect.width;
    const padRightPx = (padding.right / vbW) * svgRect.width;
    const chartWidthPx = Math.max(1, svgRect.width - padLeftPx - padRightPx);
    
    const relativeX = mouseX - svgRect.left - padLeftPx;
    const ratio = Math.max(0, Math.min(1, relativeX / chartWidthPx));
    
    const allDates = UsdExchangeState.tooltipCache.allDates || [];
    if (allDates.length === 0) return null;
    
    const index = Math.floor(ratio * (allDates.length - 1));
    return allDates[index];
}

function showUsdTooltip(event, date) {
    const tooltip = document.getElementById('usd-chart-tooltip');
    const tooltipDate = document.getElementById('usd-tooltip-date');
    const tooltipContent = document.getElementById('usd-tooltip-content');
    
    if (!tooltip || !tooltipDate || !tooltipContent || !date) return;
    
    const formattedDate = formatDate(date);
    tooltipDate.textContent = formattedDate;
    
    const tooltipCache = UsdExchangeState.tooltipCache;
    let content = '';
    
    const colors = {
        'JPY': '#E53935', 'EUR': '#1E88E5', 'GBP': '#7B1FA2', 'CNY': '#FDD835',
        'CAD': '#43A047', 'CHF': '#F57C00', 'HKD': '#00ACC1', 'AUD': '#FFB300',
        'NZD': '#8E24AA', 'SEK': '#00897B', 'NOK': '#D81B60', 'DKK': '#5E35B1',
        'RUB': '#3949AB', 'INR': '#039BE5', 'BRL': '#7CB342', 'MXN': '#C0CA33'
    };
    
    UsdExchangeState.activeCurrencies.forEach(currency => {
        const c = tooltipCache.perCurrency ? tooltipCache.perCurrency[currency] : null;
        if (c && c.dates && c.dates.length > 0) {
            let item = c.map[date];
            if (!item) {
                const closest = findClosestDate(c.dates, date);
                item = closest ? c.map[closest] : null;
            }
            
            if (item) {
                const color = colors[currency] || '#888';
                content += `
                    <div class="chart-tooltip-item">
                        <div class="chart-tooltip-currency">
                            <div class="chart-tooltip-dot" style="background: ${color}"></div>
                            <span>${currency}/USD</span>
                        </div>
                        <span class="chart-tooltip-value">${parseFloat(item.value).toFixed(4)}</span>
                    </div>
                `;
            }
        }
    });
    
    if (!content) {
        hideUsdTooltip();
        return;
    }
    
    tooltipContent.innerHTML = content;
    
    tooltip.style.visibility = 'hidden';
    tooltip.classList.add('visible');
    
    const tooltipRect = tooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    let left = event.clientX + 15;
    let top = event.clientY + 15;
    
    if (left + tooltipRect.width > viewportWidth - 10) {
        left = event.clientX - tooltipRect.width - 15;
    }
    if (top + tooltipRect.height > viewportHeight - 10) {
        top = event.clientY - tooltipRect.height - 15;
    }
    
    tooltip.style.transform = `translate3d(${left}px, ${top}px, 0)`;
    tooltip.style.visibility = 'visible';
}

function hideUsdTooltip() {
    const tooltip = document.getElementById('usd-chart-tooltip');
    if (tooltip) {
        tooltip.classList.remove('visible');
        tooltip.style.visibility = 'hidden';
    }
}

function showUsdCrosshair(mouseX, mouseY) {
    const svg = document.getElementById('usd-chart-svg');
    const crosshairX = document.getElementById('usd-crosshair-x');
    const crosshairY = document.getElementById('usd-crosshair-y');
    
    if (!svg || !crosshairX || !crosshairY) return;
    
    const svgRect = svg.getBoundingClientRect();
    const { width: vbW, height: vbH } = getSvgViewBoxSize(svg);
    
    // Convert mouse position to SVG coordinates
    const svgX = ((mouseX - svgRect.left) / svgRect.width) * vbW;
    const svgY = ((mouseY - svgRect.top) / svgRect.height) * vbH;
    
    // Check if within chart area
    const padding = { left: 40, right: 20, top: 20, bottom: 30 };
    if (svgX < padding.left || svgX > vbW - padding.right || 
        svgY < padding.top || svgY > vbH - padding.bottom) {
        crosshairX.style.display = 'none';
        crosshairY.style.display = 'none';
        return;
    }
    
    crosshairX.setAttribute('x1', svgX);
    crosshairX.setAttribute('x2', svgX);
    crosshairX.setAttribute('y1', padding.top);
    crosshairX.setAttribute('y2', vbH - padding.bottom);
    crosshairX.style.display = 'block';
    
    crosshairY.setAttribute('x1', padding.left);
    crosshairY.setAttribute('x2', vbW - padding.right);
    crosshairY.setAttribute('y1', svgY);
    crosshairY.setAttribute('y2', svgY);
    crosshairY.style.display = 'block';
}

function hideUsdCrosshair() {
    const crosshairX = document.getElementById('usd-crosshair-x');
    const crosshairY = document.getElementById('usd-crosshair-y');
    
    if (crosshairX) crosshairX.style.display = 'none';
    if (crosshairY) crosshairY.style.display = 'none';
}

function setupUsdChartInteractivity() {
    if (UsdExchangeState.chartInteractivitySetup) return;
    
    const chartContainer = document.getElementById('usd-chart-container');
    const tooltip = document.getElementById('usd-chart-tooltip');
    
    if (!chartContainer) return;
    
    // Move tooltip to body
    if (tooltip && tooltip.parentElement !== document.body) {
        document.body.appendChild(tooltip);
    }
    
    let rafId = null;
    let lastPoint = null;
    
    const handleMove = () => {
        rafId = null;
        if (!lastPoint) return;
        
        const date = getUsdDateFromMouseX(lastPoint.x);
        if (date) {
            showUsdTooltip({ clientX: lastPoint.x, clientY: lastPoint.y }, date);
            showUsdCrosshair(lastPoint.x, lastPoint.y);
        } else {
            hideUsdTooltip();
            hideUsdCrosshair();
        }
    };
    
    chartContainer.addEventListener('mousemove', (event) => {
        lastPoint = { x: event.clientX, y: event.clientY };
        if (rafId) return;
        rafId = requestAnimationFrame(handleMove);
    });
    
    chartContainer.addEventListener('mouseleave', () => {
        hideUsdTooltip();
        hideUsdCrosshair();
    });
    
    UsdExchangeState.chartInteractivitySetup = true;
}

// ============================================================
// HEADER UPDATE
// ============================================================

function updateUsdChartHeader(currency, stats) {
    const titleEl = document.getElementById('usd-chart-main-title');
    const valueEl = document.getElementById('usd-chart-main-value');
    const changeValueEl = document.getElementById('usd-change-value');
    const changePercentEl = document.getElementById('usd-change-percent');
    const statHighEl = document.getElementById('usd-stat-high');
    const statLowEl = document.getElementById('usd-stat-low');
    const statAverageEl = document.getElementById('usd-stat-average');
    
    if (titleEl) {
        titleEl.textContent = `${currency}/USD`;
    }
    
    if (!stats || stats.error) {
        if (valueEl) valueEl.textContent = '-';
        if (changeValueEl) changeValueEl.textContent = '-';
        if (changePercentEl) changePercentEl.textContent = '(-)';
        if (statHighEl) statHighEl.textContent = '-';
        if (statLowEl) statLowEl.textContent = '-';
        if (statAverageEl) statAverageEl.textContent = '-';
        return;
    }
    
    if (valueEl && stats.current != null) {
        valueEl.textContent = stats.current.toFixed(4);
    }
    
    const change = stats.change || 0;
    const changePercent = stats.changePercent || 0;
    const isUp = change >= 0;
    
    if (changeValueEl) {
        changeValueEl.textContent = `${isUp ? '+' : ''}${change.toFixed(4)}`;
        changeValueEl.className = `chart-change ${isUp ? 'up' : 'down'}`;
    }
    
    if (changePercentEl) {
        changePercentEl.textContent = `(${isUp ? '+' : ''}${changePercent.toFixed(2)}%)`;
        changePercentEl.className = `chart-change-percent ${isUp ? 'up' : 'down'}`;
    }
    
    if (statHighEl && stats.high != null) statHighEl.textContent = stats.high.toFixed(4);
    if (statLowEl && stats.low != null) statLowEl.textContent = stats.low.toFixed(4);
    if (statAverageEl && stats.average != null) statAverageEl.textContent = stats.average.toFixed(4);
}

// ============================================================
// INITIALIZATION
// ============================================================

function initExchangeRateUsd() {
    initUsdDateInputs();
    
    const panel = document.getElementById('exchange-rate-usd-panel');
    if (!panel) {
        console.warn('USD Exchange Rate panel not found');
        return;
    }
    
    const activeBtn = panel.querySelector('.period-btn.active');
    const initialKey = activeBtn ? activeBtn.textContent.trim() : '3M';
    UsdExchangeState.currentRangeKey = initialKey;
    
    // Period button events
    panel.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            panel.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            const period = e.target.textContent.trim();
            handleUsdPeriodClick(period);
        });
    });
    
    // Date input events
    panel.querySelectorAll('.date-input').forEach(input => {
        input.addEventListener('change', () => {
            if (validateUsdDateRange()) {
                panel.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                UsdExchangeState.currentRangeKey = null;
                fetchUsdExchangeRateData();
            }
        });
    });
    
    // Initial currency selection (JPY)
    UsdExchangeState.activeCurrencies = ['JPY'];
    panel.querySelectorAll('.chip').forEach(chip => {
        const curr = chip.getAttribute('data-curr');
        if (curr === 'JPY') {
            chip.classList.add('active');
        } else {
            chip.classList.remove('active');
        }
    });
    
    if (validateUsdDateRange()) {
        fetchUsdExchangeRateData();
    }
    
    console.log('✅ Exchange Rate USD module initialized');
}

// ============================================================
// EXPOSE TO WINDOW
// ============================================================
window.initExchangeRateUsd = initExchangeRateUsd;
window.handleUsdPeriodClick = handleUsdPeriodClick;
window.toggleUsdCurrency = toggleUsdCurrency;
window.fetchUsdExchangeRateData = fetchUsdExchangeRateData;
window.UsdExchangeState = UsdExchangeState;

console.log('📈 Exchange Rate USD module loaded');

