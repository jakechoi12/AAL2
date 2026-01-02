/**
 * AAL Application - GDP Module
 * GDP 관련 기능 모듈
 * 
 * 담당 패널: #gdp-indicator-panel
 * 주요 기능: GDP 차트, 국가별 비교
 */

// ============================================================
// MODULE MARKER
// ============================================================
window.gdpModuleLoaded = true;

// ============================================================
// CONFIGURATION
// ============================================================

const GDP_CONFIG = {
    apiCategory: 'gdp-international',
    panelId: 'gdp-indicator-panel',
    title: 'GDP',
    description: '국제 주요국 국내총생산(GDP)',
    cycle: 'A',
    unit: 'M USD',
    unitType: 'million-usd',
    chartPrefix: 'gdp-indicator'
};

// ============================================================
// STATE MANAGEMENT
// ============================================================

const gdpState = {
    countryMapping: {},
    activeCountries: [],
    countryData: {},
    yAxisRange: { min: 0, max: 0 },
    cycle: 'A',
    isLoaded: false,
    countryListLoaded: false
};

// ============================================================
// COUNTRY INFO MAPPING
// ============================================================

const gdpCountryInfoMap = [
    { keywords: ['호주', '오스트레일리아', 'aus', 'australia'], englishName: 'Australia', color: 'var(--c-interest-aus)' },
    { keywords: ['오스트리아', 'aut', 'austria'], englishName: 'Austria', color: '#E74C3C' },
    { keywords: ['벨기에', 'bel', 'belgium'], englishName: 'Belgium', color: '#F39C12' },
    { keywords: ['브라질', 'bra', 'brazil'], englishName: 'Brazil', color: 'var(--c-interest-bra)' },
    { keywords: ['캐나다', 'can', 'canada'], englishName: 'Canada', color: 'var(--c-interest-can)' },
    { keywords: ['스위스', 'che', 'switzerland'], englishName: 'Switzerland', color: 'var(--c-interest-che)' },
    { keywords: ['칠레', 'chl', 'chile'], englishName: 'Chile', color: 'var(--c-interest-chl)' },
    { keywords: ['중국', 'chn', 'china'], englishName: 'China', color: 'var(--c-interest-chn)' },
    { keywords: ['체코', 'cze', 'czech'], englishName: 'Czech Republic', color: 'var(--c-interest-cze)' },
    { keywords: ['독일', 'deu', 'germany'], englishName: 'Germany', color: 'var(--c-interest-deu)' },
    { keywords: ['덴마크', 'dnk', 'denmark'], englishName: 'Denmark', color: 'var(--c-interest-dnk)' },
    { keywords: ['에스토니아', 'est', 'estonia'], englishName: 'Estonia', color: '#1ABC9C' },
    { keywords: ['스페인', 'esp', 'spain'], englishName: 'Spain', color: 'var(--c-interest-esp)' },
    { keywords: ['핀란드', 'fin', 'finland'], englishName: 'Finland', color: '#3498DB' },
    { keywords: ['프랑스', 'fra', 'france'], englishName: 'France', color: 'var(--c-interest-fra)' },
    { keywords: ['영국', 'gbr', 'uk', 'united kingdom'], englishName: 'UK', color: 'var(--c-interest-gbr)' },
    { keywords: ['그리스', 'grc', 'greece'], englishName: 'Greece', color: '#2980B9' },
    { keywords: ['헝가리', 'hun', 'hungary'], englishName: 'Hungary', color: 'var(--c-interest-hun)' },
    { keywords: ['아이슬란드', 'isl', 'iceland'], englishName: 'Iceland', color: '#7FB3D5' },
    { keywords: ['인도네시아', 'idn', 'indonesia'], englishName: 'Indonesia', color: 'var(--c-interest-idn)' },
    { keywords: ['아일랜드', 'irl', 'ireland'], englishName: 'Ireland', color: '#27AE60' },
    { keywords: ['이스라엘', 'isr', 'israel'], englishName: 'Israel', color: 'var(--c-interest-isr)' },
    { keywords: ['인도', 'ind', 'india'], englishName: 'India', color: 'var(--c-interest-ind)' },
    { keywords: ['이탈리아', 'ita', 'italy'], englishName: 'Italy', color: 'var(--c-interest-ita)' },
    { keywords: ['일본', 'jpn', 'japan'], englishName: 'Japan', color: 'var(--c-interest-jpn)' },
    { keywords: ['한국', 'kor', 'korea'], englishName: 'Korea', color: 'var(--c-interest-kor)' },
    { keywords: ['라트비아', 'lva', 'latvia'], englishName: 'Latvia', color: '#A569BD' },
    { keywords: ['룩셈부르크', 'lux', 'luxembourg'], englishName: 'Luxembourg', color: '#F5B041' },
    { keywords: ['멕시코', 'mex', 'mexico'], englishName: 'Mexico', color: 'var(--c-interest-mex)' },
    { keywords: ['네덜란드', 'nld', 'netherlands'], englishName: 'Netherlands', color: '#E67E22' },
    { keywords: ['노르웨이', 'nor', 'norway'], englishName: 'Norway', color: 'var(--c-interest-nor)' },
    { keywords: ['뉴질랜드', 'nzl', 'zealand'], englishName: 'New Zealand', color: 'var(--c-interest-nzl)' },
    { keywords: ['폴란드', 'pol', 'poland'], englishName: 'Poland', color: 'var(--c-interest-pol)' },
    { keywords: ['포르투갈', 'prt', 'portugal'], englishName: 'Portugal', color: '#9B59B6' },
    { keywords: ['러시아', 'rus', 'russia'], englishName: 'Russia', color: 'var(--c-interest-rus)' },
    { keywords: ['슬로바키아', 'svk', 'slovakia'], englishName: 'Slovakia', color: '#34495E' },
    { keywords: ['슬로베니아', 'svn', 'slovenia'], englishName: 'Slovenia', color: '#16A085' },
    { keywords: ['스웨덴', 'swe', 'sweden'], englishName: 'Sweden', color: 'var(--c-interest-swe)' },
    { keywords: ['튀르키예', '터키', 'tur', 'turkey', 'turkiye'], englishName: 'Turkey', color: 'var(--c-interest-tur)' },
    { keywords: ['미국', 'usa', 'us ', 'united states'], englishName: 'USA', color: 'var(--c-interest-usa)' },
    { keywords: ['남아프리카', '남아공', 'zaf', 'south africa'], englishName: 'South Africa', color: 'var(--c-interest-zaf)' },
    { keywords: ['유로', 'eur', 'eurozone', 'euro area'], englishName: 'Eurozone', color: 'var(--c-interest-eur)' }
];

function getGDPCountryNameEnglish(koreanName) {
    if (!koreanName) return koreanName;
    const name = koreanName.toLowerCase();
    for (const info of gdpCountryInfoMap) {
        if (info.keywords.some(keyword => name.includes(keyword))) {
            return info.englishName;
        }
    }
    return koreanName;
}

function getGDPCountryColor(itemCode) {
    const countryInfo = gdpState.countryMapping[itemCode];
    if (!countryInfo) {
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE'];
        let hash = 0;
        for (let i = 0; i < itemCode.length; i++) {
            hash = ((hash << 5) - hash) + itemCode.charCodeAt(i);
        }
        return colors[Math.abs(hash) % colors.length];
    }
    
    const name = countryInfo.name?.toLowerCase() || '';
    for (const info of gdpCountryInfoMap) {
        if (info.keywords.some(keyword => name.includes(keyword))) {
            return info.color;
        }
    }
    
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE'];
    let hash = 0;
    for (let i = 0; i < itemCode.length; i++) {
        hash = ((hash << 5) - hash) + itemCode.charCodeAt(i);
    }
    return colors[Math.abs(hash) % colors.length];
}

// ============================================================
// VALUE FORMATTING
// ============================================================

function getUsdKrwRateForGDP() {
    if (window.exchangeRates && window.exchangeRates.USD) {
        return window.exchangeRates.USD;
    }
    return 1350;
}

function convertGDPToKRW(value) {
    if (!Number.isFinite(value)) return null;
    const rate = getUsdKrwRateForGDP();
    const krwBillion = value * rate / 1000;
    const krwTrillion = krwBillion / 1000;
    
    if (krwTrillion >= 1) {
        return `≈${krwTrillion.toLocaleString('en-US', {maximumFractionDigits: 0})}조 원`;
    } else if (krwBillion >= 1) {
        return `≈${krwBillion.toLocaleString('en-US', {maximumFractionDigits: 0})}억 원`;
    }
    return null;
}

// ============================================================
// DATE HELPERS
// ============================================================

function parseGDPDate(dateStr) {
    if (!dateStr || dateStr.length !== 4) return null;
    return new Date(parseInt(dateStr, 10), 0, 1);
}

function compareGDPDates(a, b) {
    const da = parseGDPDate(a);
    const db = parseGDPDate(b);
    if (!da || !db) return String(a).localeCompare(String(b));
    return da.getTime() - db.getTime();
}

// ============================================================
// INITIALIZATION
// ============================================================

async function initGDPIndicator() {
    const prefix = GDP_CONFIG.chartPrefix;
    
    const startDateInput = document.getElementById(`${prefix}-start-date`);
    const endDateInput = document.getElementById(`${prefix}-end-date`);
    
    if (startDateInput && endDateInput) {
        const end = new Date();
        const start = new Date();
        start.setFullYear(end.getFullYear() - 10);
        
        startDateInput.value = start.getFullYear();
        endDateInput.value = end.getFullYear();
        startDateInput.min = 1960;
        endDateInput.min = 1960;
        startDateInput.max = end.getFullYear();
        endDateInput.max = end.getFullYear();
        
        startDateInput.addEventListener('change', () => {
            if (validateGDPDateRange()) {
                fetchGDPData();
            }
        });
        endDateInput.addEventListener('change', () => {
            if (validateGDPDateRange()) {
                fetchGDPData();
            }
        });
    }
    
    try {
        await fetchGDPCountryList();
        initGDPCountryChips();
        fetchGDPData();
    } catch (err) {
        console.error('Failed to initialize GDP:', err);
    }
    
    gdpState.isLoaded = true;
    window.gdpIndicatorDataLoaded = true;
}

// ============================================================
// COUNTRY LIST
// ============================================================

async function fetchGDPCountryList() {
    if (gdpState.countryListLoaded && Object.keys(gdpState.countryMapping).length > 0) {
        return gdpState.countryMapping;
    }
    
    try {
        const url = `${API_BASE}/market/categories?category=${GDP_CONFIG.apiCategory}`;
        const response = await fetch(url);
        
        if (response.ok) {
            const data = await response.json();
            if (data.items && Object.keys(data.items).length > 0) {
                gdpState.countryMapping = data.items;
                gdpState.countryListLoaded = true;
                
                const itemCodes = Object.keys(gdpState.countryMapping);
                const korCode = itemCodes.find(code => {
                    const name = gdpState.countryMapping[code].name;
                    return name && (name.includes('한국') || name.includes('KOR') || name.toLowerCase().includes('korea'));
                });
                if (korCode) {
                    gdpState.activeCountries = [korCode];
                } else if (itemCodes.length > 0) {
                    gdpState.activeCountries = [itemCodes[0]];
                }
                
                return gdpState.countryMapping;
            }
        }
        throw new Error('Failed to fetch country list');
    } catch (err) {
        console.error('Failed to fetch GDP country list:', err);
        throw err;
    }
}

function initGDPCountryChips() {
    const chipsContainer = document.getElementById(`${GDP_CONFIG.chartPrefix}-country-chips`);
    if (!chipsContainer) return;
    
    chipsContainer.innerHTML = '';
    
    const itemCodes = Object.keys(gdpState.countryMapping);
    if (itemCodes.length === 0) {
        chipsContainer.innerHTML = '<span style="color: var(--text-sub); font-size: 0.8rem;">Loading...</span>';
        return;
    }
    
    itemCodes.forEach(itemCode => {
        const countryInfo = gdpState.countryMapping[itemCode];
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.setAttribute('data-item-code', itemCode);
        chip.setAttribute('title', countryInfo.name);
        
        const isActive = gdpState.activeCountries.includes(itemCode);
        if (isActive) chip.classList.add('active');
        
        const countryColor = getGDPCountryColor(itemCode);
        const chipDot = document.createElement('div');
        chipDot.className = 'chip-dot';
        
        if (isActive) {
            chipDot.style.background = countryColor;
            chip.style.borderColor = countryColor;
            chip.style.color = countryColor;
            const tempEl = document.createElement('div');
            tempEl.style.color = countryColor;
            document.body.appendChild(tempEl);
            const computedColor = window.getComputedStyle(tempEl).color;
            document.body.removeChild(tempEl);
            const rgbMatch = computedColor.match(/\d+/g);
            if (rgbMatch && rgbMatch.length >= 3) {
                chip.style.background = `rgba(${rgbMatch[0]}, ${rgbMatch[1]}, ${rgbMatch[2]}, 0.2)`;
            }
        } else {
            chipDot.style.background = 'currentColor';
        }
        
        chip.appendChild(chipDot);
        const englishName = getGDPCountryNameEnglish(countryInfo.name);
        chip.appendChild(document.createTextNode(englishName));
        
        chip.addEventListener('click', () => toggleGDPCountry(itemCode));
        chipsContainer.appendChild(chip);
    });
}

function toggleGDPCountry(itemCode) {
    const index = gdpState.activeCountries.indexOf(itemCode);
    
    if (index === -1) {
        gdpState.activeCountries.push(itemCode);
    } else {
        gdpState.activeCountries.splice(index, 1);
    }
    
    const chip = document.querySelector(`#${GDP_CONFIG.chartPrefix}-country-chips [data-item-code="${itemCode}"]`);
    if (chip) {
        const chipDot = chip.querySelector('.chip-dot');
        const isActive = gdpState.activeCountries.includes(itemCode);
        
        if (isActive) {
            chip.classList.add('active');
            const countryColor = getGDPCountryColor(itemCode);
            if (chipDot) chipDot.style.background = countryColor;
            chip.style.borderColor = countryColor;
            chip.style.color = countryColor;
            const tempEl = document.createElement('div');
            tempEl.style.color = countryColor;
            document.body.appendChild(tempEl);
            const computedColor = window.getComputedStyle(tempEl).color;
            document.body.removeChild(tempEl);
            const rgbMatch = computedColor.match(/\d+/g);
            if (rgbMatch && rgbMatch.length >= 3) {
                chip.style.background = `rgba(${rgbMatch[0]}, ${rgbMatch[1]}, ${rgbMatch[2]}, 0.2)`;
            }
        } else {
            chip.classList.remove('active');
            if (chipDot) chipDot.style.background = 'currentColor';
            chip.style.borderColor = '';
            chip.style.color = '';
            chip.style.background = '';
        }
    }
    
    if (validateGDPDateRange()) {
        fetchGDPData();
    }
}

// ============================================================
// DATE VALIDATION
// ============================================================

function validateGDPDateRange() {
    const prefix = GDP_CONFIG.chartPrefix;
    const startInput = document.getElementById(`${prefix}-start-date`);
    const endInput = document.getElementById(`${prefix}-end-date`);
    
    if (!startInput || !endInput) return false;
    
    const startYear = parseInt(startInput.value, 10);
    const endYear = parseInt(endInput.value, 10);
    return !(isNaN(startYear) || isNaN(endYear) || startYear > endYear);
}

// ============================================================
// DATA FETCHING
// ============================================================

async function fetchGDPData() {
    const prefix = GDP_CONFIG.chartPrefix;
    
    if (!validateGDPDateRange()) return;
    if (gdpState.activeCountries.length === 0) {
        updateGDPChart();
        return;
    }
    
    const startInput = document.getElementById(`${prefix}-start-date`);
    const endInput = document.getElementById(`${prefix}-end-date`);
    
    const startDate = `${startInput.value}0101`;
    const endDate = `${endInput.value}1231`;
    
    const chartContainer = document.getElementById(`${prefix}-chart-container`);
    if (chartContainer) chartContainer.style.opacity = '0.5';
    
    try {
        const fetchPromises = gdpState.activeCountries.map(async (itemCode) => {
            const url = `${API_BASE}/market/indices?type=${GDP_CONFIG.apiCategory}&itemCode=${itemCode}&startDate=${startDate}&endDate=${endDate}&cycle=${gdpState.cycle}`;
            
            try {
                const response = await fetch(url);
                const json = await response.json();
                return { itemCode, data: json };
            } catch (err) {
                console.error(`Failed to fetch ${itemCode}:`, err);
                return { itemCode, data: { error: err.message } };
            }
        });
        
        const results = await Promise.all(fetchPromises);
        processGDPData(results);
        
    } catch (err) {
        console.error('Failed to fetch GDP data:', err);
    } finally {
        if (chartContainer) chartContainer.style.opacity = '1';
    }
}

function processGDPData(results) {
    gdpState.countryData = {};
    
    results.forEach(({ itemCode, data }) => {
        if (data.error || !data.StatisticSearch) {
            console.error(`Error processing ${itemCode}:`, data.error);
            return;
        }
        
        const rows = data.StatisticSearch.row || [];
        const values = rows.map(row => ({
            date: row.TIME,
            value: parseFloat(row.DATA_VALUE)
        })).filter(item => !isNaN(item.value));
        
        values.sort((a, b) => compareGDPDates(a.date, b.date));
        gdpState.countryData[itemCode] = values;
    });
    
    updateGDPChart();
}

// ============================================================
// CHART RENDERING
// ============================================================

function updateGDPChart() {
    const prefix = GDP_CONFIG.chartPrefix;
    const svg = document.getElementById(`${prefix}-chart-svg`);
    const pointsGroup = document.getElementById(`${prefix}-data-points`);
    const pathsGroup = document.getElementById(`${prefix}-paths-group`);
    
    if (!svg) return;
    
    if (pathsGroup) {
        pathsGroup.innerHTML = '';
    } else {
        svg.querySelectorAll('.chart-path').forEach(el => el.remove());
    }
    if (pointsGroup) pointsGroup.innerHTML = '';
    
    if (gdpState.activeCountries.length === 0) {
        renderGDPYAxisLabels([]);
        renderGDPXAxisLabels([]);
        return;
    }
    
    const allDates = new Set();
    Object.values(gdpState.countryData).forEach(data => {
        data.forEach(item => allDates.add(item.date));
    });
    const sortedDates = Array.from(allDates).sort((a, b) => compareGDPDates(a, b));
    
    if (sortedDates.length === 0) {
        renderGDPYAxisLabels([]);
        renderGDPXAxisLabels([]);
        return;
    }
    
    const allValues = [];
    Object.values(gdpState.countryData).forEach(data => {
        data.forEach(item => allValues.push(item.value));
    });
    
    if (allValues.length === 0) {
        renderGDPYAxisLabels([]);
        renderGDPXAxisLabels(sortedDates);
        return;
    }
    
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const range = maxValue - minValue || 1;
    gdpState.yAxisRange = {
        min: Math.max(0, minValue - range * 0.05),
        max: maxValue + range * 0.05
    };
    
    renderGDPYAxisLabels(sortedDates);
    
    gdpState.activeCountries.forEach(itemCode => {
        const data = gdpState.countryData[itemCode];
        if (!data || data.length === 0) return;
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.classList.add('chart-path', 'visible');
        path.setAttribute('stroke', getGDPCountryColor(itemCode));
        path.setAttribute('stroke-width', '2.5');
        path.setAttribute('fill', 'none');
        
        const sortedData = sortedDates.map(date => {
            const found = data.find(item => item.date === date);
            return found || { date, value: null };
        }).filter(item => item.value !== null);
        
        if (sortedData.length > 0) {
            const pathData = generateGDPSVGPath(sortedData);
            path.setAttribute('d', pathData);
            if (pathsGroup) {
                pathsGroup.appendChild(path);
            } else {
                svg.insertBefore(path, pointsGroup);
            }
        }
    });
    
    renderGDPXAxisLabels(sortedDates);
    setupGDPChartInteractivity();
    updateGDPChartHeader();
}

function generateGDPSVGPath(data) {
    if (!data || data.length === 0) return '';
    
    const svg = document.getElementById(`${GDP_CONFIG.chartPrefix}-chart-svg`);
    if (!svg) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 60, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const minValue = gdpState.yAxisRange.min;
    const maxValue = gdpState.yAxisRange.max;
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

function renderGDPYAxisLabels(sortedDates) {
    const yAxisGroup = document.getElementById(`${GDP_CONFIG.chartPrefix}-y-axis-labels`);
    if (!yAxisGroup) return;
    
    yAxisGroup.innerHTML = '';
    
    const minValue = gdpState.yAxisRange.min;
    const maxValue = gdpState.yAxisRange.max;
    const steps = 5;
    
    for (let i = 0; i <= steps; i++) {
        const value = maxValue - (i / steps) * (maxValue - minValue);
        const y = 20 + (i / steps) * 330;
        
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', '55');
        label.setAttribute('y', y);
        label.setAttribute('class', 'chart-yaxis-label');
        label.setAttribute('text-anchor', 'end');
        label.setAttribute('dominant-baseline', 'middle');
        label.textContent = value.toLocaleString('en-US', { maximumFractionDigits: 0 });
        
        yAxisGroup.appendChild(label);
    }
}

function renderGDPXAxisLabels(sortedDates) {
    const xAxisGroup = document.getElementById(`${GDP_CONFIG.chartPrefix}-x-axis-labels`);
    if (!xAxisGroup || !sortedDates || sortedDates.length === 0) return;
    
    xAxisGroup.innerHTML = '';
    
    const svg = document.getElementById(`${GDP_CONFIG.chartPrefix}-chart-svg`);
    if (!svg) return;
    
    const { width } = getSvgViewBoxSize(svg);
    const padding = { left: 60, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    
    const labelInterval = Math.max(1, Math.floor(sortedDates.length / 8));
    
    sortedDates.forEach((date, index) => {
        if (index % labelInterval !== 0 && index !== sortedDates.length - 1) return;
        
        const x = padding.left + (index / (sortedDates.length - 1 || 1)) * chartWidth;
        const y = 370;
        
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', x);
        label.setAttribute('y', y);
        label.setAttribute('class', 'chart-xaxis-label');
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('dominant-baseline', 'middle');
        label.textContent = date;
        
        xAxisGroup.appendChild(label);
    });
}

// ============================================================
// CHART INTERACTIVITY
// ============================================================

let gdpCrosshairX = null;
let gdpCrosshairY = null;

function setupGDPChartInteractivity() {
    const prefix = GDP_CONFIG.chartPrefix;
    const chartContainer = document.getElementById(`${prefix}-chart-container`);
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    const svg = document.getElementById(`${prefix}-chart-svg`);
    
    if (!chartContainer || !tooltip || !svg) return;
    
    if (tooltip.parentElement !== document.body) {
        document.body.appendChild(tooltip);
    }
    
    // Create crosshair elements
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 60, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const crosshairs = createCrosshairElements(svg, padding, chartWidth, chartHeight);
    gdpCrosshairX = crosshairs.crosshairX;
    gdpCrosshairY = crosshairs.crosshairY;
    
    const newContainer = chartContainer.cloneNode(true);
    chartContainer.parentNode.replaceChild(newContainer, chartContainer);
    
    let rafId = null;
    
    newContainer.addEventListener('mousemove', (event) => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
            rafId = null;
            showGDPTooltip(event);
        });
    });
    
    newContainer.addEventListener('mouseleave', () => {
        if (rafId) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
        hideGDPTooltip();
        hideCrosshair(gdpCrosshairX, gdpCrosshairY);
    });
}

function showGDPTooltip(event) {
    const prefix = GDP_CONFIG.chartPrefix;
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    const svg = document.getElementById(`${prefix}-chart-svg`);
    if (!tooltip || !svg) return;
    
    const rect = svg.getBoundingClientRect();
    const x = event.clientX - rect.left;
    
    const { width, height } = getSvgViewBoxSize(svg);
    const chartPadding = { left: 60, right: 20, top: 20, bottom: 30 };
    const chartWidth = width - chartPadding.left - chartPadding.right;
    const chartHeight = height - chartPadding.top - chartPadding.bottom;
    
    const allDates = new Set();
    Object.values(gdpState.countryData).forEach(data => {
        data.forEach(item => allDates.add(item.date));
    });
    const sortedDates = Array.from(allDates).sort((a, b) => compareGDPDates(a, b));
    
    if (sortedDates.length === 0) {
        hideCrosshair(gdpCrosshairX, gdpCrosshairY);
        return;
    }
    
    const dateIndex = Math.round(((x / rect.width * width) - chartPadding.left) / chartWidth * (sortedDates.length - 1));
    const dateIndexClamped = Math.max(0, Math.min(sortedDates.length - 1, dateIndex));
    const date = sortedDates[dateIndexClamped];
    
    // Update crosshair X position
    const crosshairXPos = chartPadding.left + (dateIndexClamped / (sortedDates.length - 1 || 1)) * chartWidth;
    if (gdpCrosshairX) {
        gdpCrosshairX.setAttribute('x1', crosshairXPos);
        gdpCrosshairX.setAttribute('x2', crosshairXPos);
        gdpCrosshairX.style.opacity = '1';
    }
    
    // Calculate average Y for crosshair
    let sumY = 0;
    let countY = 0;
    gdpState.activeCountries.forEach(itemCode => {
        const data = gdpState.countryData[itemCode];
        if (data) {
            const item = data.find(d => d.date === date);
            if (item && Number.isFinite(item.value)) {
                sumY += item.value;
                countY++;
            }
        }
    });
    
    if (countY > 0 && gdpCrosshairY) {
        const avgValue = sumY / countY;
        const normalizedY = (avgValue - gdpState.yAxisRange.min) / (gdpState.yAxisRange.max - gdpState.yAxisRange.min || 1);
        const crosshairYPos = chartPadding.top + (1 - normalizedY) * chartHeight;
        gdpCrosshairY.setAttribute('y1', crosshairYPos);
        gdpCrosshairY.setAttribute('y2', crosshairYPos);
        gdpCrosshairY.style.opacity = '1';
    }
    
    let content = '';
    gdpState.activeCountries.forEach(itemCode => {
        const data = gdpState.countryData[itemCode];
        if (!data) return;
        
        const item = data.find(d => d.date === date);
        if (!item) return;
        
        const countryInfo = gdpState.countryMapping[itemCode];
        const countryName = countryInfo ? getGDPCountryNameEnglish(countryInfo.name) : itemCode;
        const color = getGDPCountryColor(itemCode);
        
        const tempEl = document.createElement('div');
        tempEl.style.color = color;
        document.body.appendChild(tempEl);
        const computedColor = window.getComputedStyle(tempEl).color;
        document.body.removeChild(tempEl);
        
        const formattedVal = item.value.toLocaleString('en-US', { maximumFractionDigits: 0 });
        const krwVal = convertGDPToKRW(item.value);
        let valueText = formattedVal + `<span style="font-size: 80%; opacity: 0.8;"> ${GDP_CONFIG.unit}`;
        if (krwVal) valueText += ` (${krwVal})`;
        valueText += '</span>';
        
        content += `
            <div class="chart-tooltip-item">
                <div class="chart-tooltip-currency">
                    <div class="chart-tooltip-dot" style="background: ${computedColor}"></div>
                    <span>${countryName}</span>
                </div>
                <span class="chart-tooltip-value">${valueText}</span>
            </div>
        `;
    });
    
    if (!content) {
        hideGDPTooltip();
        return;
    }
    
    const tooltipContent = document.getElementById(`${prefix}-tooltip-content`);
    const tooltipDate = document.getElementById(`${prefix}-tooltip-date`);
    
    if (tooltipContent) tooltipContent.innerHTML = content;
    if (tooltipDate) tooltipDate.textContent = date;
    
    tooltip.style.visibility = 'hidden';
    tooltip.classList.add('visible');
    
    const tooltipRect = tooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const tooltipPadding = 15;
    
    let left = event.clientX + tooltipPadding;
    let top = event.clientY + tooltipPadding;
    
    if (left + tooltipRect.width > viewportWidth - tooltipPadding) {
        left = event.clientX - tooltipRect.width - tooltipPadding;
    }
    if (left < tooltipPadding) left = tooltipPadding;
    if (top + tooltipRect.height > viewportHeight - tooltipPadding) {
        top = event.clientY - tooltipRect.height - tooltipPadding;
    }
    if (top < tooltipPadding) top = tooltipPadding;
    
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    tooltip.style.visibility = 'visible';
}

function hideGDPTooltip() {
    const tooltip = document.getElementById(`${GDP_CONFIG.chartPrefix}-chart-tooltip`);
    if (tooltip) {
        tooltip.classList.remove('visible');
        tooltip.style.visibility = 'hidden';
    }
    hideCrosshair(gdpCrosshairX, gdpCrosshairY);
}

function updateGDPChartHeader() {
    const prefix = GDP_CONFIG.chartPrefix;
    
    if (gdpState.activeCountries.length === 0) return;
    
    const firstCountryCode = gdpState.activeCountries[0];
    const firstCountryData = gdpState.countryData[firstCountryCode];
    
    if (!firstCountryData || firstCountryData.length === 0) return;
    
    const values = firstCountryData.map(item => item.value);
    const high = Math.max(...values);
    const low = Math.min(...values);
    const average = values.reduce((sum, v) => sum + v, 0) / values.length;
    const current = firstCountryData[firstCountryData.length - 1].value;
    
    const countryInfo = gdpState.countryMapping[firstCountryCode];
    const countryName = countryInfo ? getGDPCountryNameEnglish(countryInfo.name) : firstCountryCode;
    
    const titleEl = document.getElementById(`${prefix}-chart-main-title`);
    if (titleEl) titleEl.textContent = `${GDP_CONFIG.title} - ${countryName}`;
    
    const valueEl = document.getElementById(`${prefix}-chart-main-value`);
    if (valueEl) {
        const formattedValue = current.toLocaleString('en-US', { maximumFractionDigits: 0 });
        let unitHtml = `<span style="font-size: 50%; opacity: 0.8;"> ${GDP_CONFIG.unit}`;
        const krwValue = convertGDPToKRW(current);
        if (krwValue) unitHtml += ` (${krwValue})`;
        unitHtml += '</span>';
        valueEl.innerHTML = formattedValue + unitHtml;
    }
    
    const formatStat = (val) => val.toLocaleString('en-US', { maximumFractionDigits: 0 });
    
    const highEl = document.getElementById(`${prefix}-stat-high`);
    const lowEl = document.getElementById(`${prefix}-stat-low`);
    const avgEl = document.getElementById(`${prefix}-stat-average`);
    
    if (highEl) highEl.textContent = formatStat(high);
    if (lowEl) lowEl.textContent = formatStat(low);
    if (avgEl) avgEl.textContent = formatStat(average);
}

// ============================================================
// GLOBAL EXPORTS
// ============================================================

window.initGDPIndicator = initGDPIndicator;
window.toggleGDPIndicatorCountry = toggleGDPCountry;

console.log('🏦 GDP module loaded');
