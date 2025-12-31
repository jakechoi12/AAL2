/**
 * AAL Application - International Indicators Module
 * 국제 주요국 지표 기능 모듈 (GDP, GDP per Capita, GNI, Employment, Global Stocks)
 * 
 * 담당 패널: #gdp-indicator-panel, #gdp-per-capita-panel, #gni-panel, #employment-panel, #global-stocks-panel
 */

// ============================================================
// MODULE MARKER
// ============================================================
window.internationalIndicatorsModuleLoaded = true;

// ============================================================
// CONFIGURATION
// ============================================================

const INTERNATIONAL_INDICATORS_CONFIG = {
    'gdp-indicator': {
        apiCategory: 'gdp-international',
        panelId: 'gdp-indicator-panel',
        title: 'GDP',
        description: '국제 주요국 국내총생산(GDP)',
        cycle: 'A', // Annual
        unit: 'Billion USD',
        dateInputType: 'number', // year input
        chartPrefix: 'gdp-indicator'
    },
    'gdp-per-capita': {
        apiCategory: 'gdp-per-capita-international',
        panelId: 'gdp-per-capita-panel',
        title: 'GDP per Capita',
        description: '국제 주요국 1인당 GDP',
        cycle: 'A', // Annual
        unit: 'USD',
        dateInputType: 'number',
        chartPrefix: 'gdp-per-capita'
    },
    'gni': {
        apiCategory: 'gni-international',
        panelId: 'gni-panel',
        title: 'GNI',
        description: '국제 주요국 국민총소득(GNI)',
        cycle: 'A', // Annual
        unit: 'Billion USD',
        dateInputType: 'number',
        chartPrefix: 'gni'
    },
    'employment': {
        apiCategory: 'unemployment-international',
        panelId: 'employment-panel',
        title: 'Unemployment Rate',
        description: '국제 주요국 실업률(계절변동조정)',
        cycle: 'M', // Monthly
        unit: '%',
        dateInputType: 'date',
        chartPrefix: 'employment'
    },
    'global-stocks': {
        apiCategory: 'stock-index-international',
        panelId: 'global-stocks-panel',
        title: 'Global Stock Index',
        description: '국제 주요국 주가지수',
        cycle: 'M', // Monthly
        unit: 'Index',
        dateInputType: 'date',
        chartPrefix: 'global-stocks'
    }
};

// ============================================================
// STATE MANAGEMENT
// ============================================================

const indicatorState = {};

function getIndicatorState(indicatorType) {
    if (!indicatorState[indicatorType]) {
        indicatorState[indicatorType] = {
            countryMapping: {},
            activeCountries: [],
            countryData: {},
            yAxisRange: { min: 0, max: 0 },
            cycle: INTERNATIONAL_INDICATORS_CONFIG[indicatorType]?.cycle || 'M',
            isLoaded: false,
            countryListLoaded: false
        };
    }
    return indicatorState[indicatorType];
}

// ============================================================
// COUNTRY INFO MAPPING
// ============================================================

const countryInfoMap = [
    // A
    { keywords: ['호주', '오스트레일리아', 'aus', 'australia'], englishName: 'Australia', color: 'var(--c-interest-aus)' },
    { keywords: ['오스트리아', 'aut', 'austria'], englishName: 'Austria', color: '#E74C3C' },
    // B
    { keywords: ['벨기에', 'bel', 'belgium'], englishName: 'Belgium', color: '#F39C12' },
    { keywords: ['브라질', 'bra', 'brazil'], englishName: 'Brazil', color: 'var(--c-interest-bra)' },
    // C
    { keywords: ['캐나다', 'can', 'canada'], englishName: 'Canada', color: 'var(--c-interest-can)' },
    { keywords: ['스위스', 'che', 'switzerland'], englishName: 'Switzerland', color: 'var(--c-interest-che)' },
    { keywords: ['칠레', 'chl', 'chile'], englishName: 'Chile', color: 'var(--c-interest-chl)' },
    { keywords: ['중국', 'chn', 'china'], englishName: 'China', color: 'var(--c-interest-chn)' },
    { keywords: ['체코', 'cze', 'czech'], englishName: 'Czech Republic', color: 'var(--c-interest-cze)' },
    // D
    { keywords: ['독일', 'deu', 'germany'], englishName: 'Germany', color: 'var(--c-interest-deu)' },
    { keywords: ['덴마크', 'dnk', 'denmark'], englishName: 'Denmark', color: 'var(--c-interest-dnk)' },
    // E
    { keywords: ['에스토니아', 'est', 'estonia'], englishName: 'Estonia', color: '#1ABC9C' },
    { keywords: ['스페인', 'esp', 'spain'], englishName: 'Spain', color: 'var(--c-interest-esp)' },
    // F
    { keywords: ['핀란드', 'fin', 'finland'], englishName: 'Finland', color: '#3498DB' },
    { keywords: ['프랑스', 'fra', 'france'], englishName: 'France', color: 'var(--c-interest-fra)' },
    // G
    { keywords: ['영국', 'gbr', 'uk', 'united kingdom'], englishName: 'UK', color: 'var(--c-interest-gbr)' },
    { keywords: ['그리스', 'grc', 'greece'], englishName: 'Greece', color: '#2980B9' },
    // H
    { keywords: ['헝가리', 'hun', 'hungary'], englishName: 'Hungary', color: 'var(--c-interest-hun)' },
    // I
    { keywords: ['인도네시아', 'idn', 'indonesia'], englishName: 'Indonesia', color: 'var(--c-interest-idn)' },
    { keywords: ['아일랜드', 'irl', 'ireland'], englishName: 'Ireland', color: '#27AE60' },
    { keywords: ['이스라엘', 'isr', 'israel'], englishName: 'Israel', color: 'var(--c-interest-isr)' },
    { keywords: ['인도', 'ind', 'india'], englishName: 'India', color: 'var(--c-interest-ind)' },
    { keywords: ['아이슬란드', 'isl', 'iceland'], englishName: 'Iceland', color: 'var(--c-interest-isl)' },
    { keywords: ['이탈리아', 'ita', 'italy'], englishName: 'Italy', color: 'var(--c-interest-ita)' },
    // J
    { keywords: ['일본', 'jpn', 'japan'], englishName: 'Japan', color: 'var(--c-interest-jpn)' },
    // K
    { keywords: ['한국', 'kor', 'korea'], englishName: 'Korea', color: 'var(--c-interest-kor)' },
    // L
    { keywords: ['룩셈부르크', 'lux', 'luxembourg'], englishName: 'Luxembourg', color: '#8E44AD' },
    { keywords: ['라트비아', 'lva', 'latvia'], englishName: 'Latvia', color: '#9B59B6' },
    // M
    { keywords: ['멕시코', 'mex', 'mexico'], englishName: 'Mexico', color: 'var(--c-interest-mex)' },
    // N
    { keywords: ['네덜란드', 'nld', 'netherlands'], englishName: 'Netherlands', color: '#E67E22' },
    { keywords: ['노르웨이', 'nor', 'norway'], englishName: 'Norway', color: 'var(--c-interest-nor)' },
    { keywords: ['뉴질랜드', 'nzl', 'zealand'], englishName: 'New Zealand', color: 'var(--c-interest-nzl)' },
    // P
    { keywords: ['폴란드', 'pol', 'poland'], englishName: 'Poland', color: 'var(--c-interest-pol)' },
    { keywords: ['포르투갈', 'prt', 'portugal'], englishName: 'Portugal', color: '#16A085' },
    // R
    { keywords: ['러시아', 'rus', 'russia'], englishName: 'Russia', color: 'var(--c-interest-rus)' },
    // S
    { keywords: ['스웨덴', 'swe', 'sweden'], englishName: 'Sweden', color: 'var(--c-interest-swe)' },
    { keywords: ['슬로베니아', 'svn', 'slovenia'], englishName: 'Slovenia', color: '#1E8449' },
    { keywords: ['슬로바키아', 'svk', 'slovakia'], englishName: 'Slovakia', color: '#2ECC71' },
    // T
    { keywords: ['튀르키예', '터키', 'tur', 'turkey', 'turkiye'], englishName: 'Turkey', color: 'var(--c-interest-tur)' },
    // U
    { keywords: ['미국', 'usa', 'us ', 'united states'], englishName: 'USA', color: 'var(--c-interest-usa)' },
    // Z
    { keywords: ['남아프리카', '남아공', 'zaf', 'south africa'], englishName: 'South Africa', color: 'var(--c-interest-zaf)' },
    // Eurozone
    { keywords: ['유로', 'eur', 'eurozone', 'euro area'], englishName: 'Eurozone', color: 'var(--c-interest-eur)' }
];

function getCountryNameEnglish(koreanName) {
    if (!koreanName) return koreanName;
    const name = koreanName.toLowerCase();
    for (const info of countryInfoMap) {
        if (info.keywords.some(keyword => name.includes(keyword))) {
            return info.englishName;
        }
    }
    return koreanName;
}

function getCountryColor(itemCode, countryMapping) {
    const countryInfo = countryMapping[itemCode];
    if (!countryInfo) {
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE'];
        let hash = 0;
        for (let i = 0; i < itemCode.length; i++) {
            hash = ((hash << 5) - hash) + itemCode.charCodeAt(i);
        }
        return colors[Math.abs(hash) % colors.length];
    }
    
    const name = countryInfo.name?.toLowerCase() || '';
    for (const info of countryInfoMap) {
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
// DATE HELPERS
// ============================================================

function parseIndicatorDate(dateStr, cycle) {
    if (!dateStr) return null;
    if (cycle === 'A' || cycle === 'Y') {
        if (dateStr.length === 4) {
            return new Date(parseInt(dateStr, 10), 0, 1);
        }
    } else if (cycle === 'M') {
        if (dateStr.length === 6) {
            const year = parseInt(dateStr.substring(0, 4), 10);
            const month = parseInt(dateStr.substring(4, 6), 10) - 1;
            return new Date(year, month, 1);
        }
    } else if (cycle === 'Q') {
        const match = dateStr.match(/^(\d{4})Q([1-4])$/);
        if (match) {
            const year = parseInt(match[1], 10);
            const q = parseInt(match[2], 10);
            const month = (q - 1) * 3;
            return new Date(year, month, 1);
        }
    }
    return null;
}

function compareIndicatorDates(a, b, cycle) {
    const da = parseIndicatorDate(a, cycle);
    const db = parseIndicatorDate(b, cycle);
    if (!da || !db) return String(a).localeCompare(String(b));
    return da.getTime() - db.getTime();
}

function formatIndicatorDateLabel(dateStr, cycle) {
    if (!dateStr) return '';
    if ((cycle === 'A' || cycle === 'Y') && dateStr.length === 4) {
        return dateStr;
    }
    if (cycle === 'M' && dateStr.length === 6) {
        const yy = dateStr.substring(2, 4);
        const mm = dateStr.substring(4, 6);
        return `${yy}.${mm}`;
    }
    if (cycle === 'Q') {
        const match = dateStr.match(/^(\d{4})Q([1-4])$/);
        if (match) {
            const yy = match[1].substring(2, 4);
            return `${yy}Q${match[2]}`;
        }
    }
    return dateStr;
}

// ============================================================
// INITIALIZATION FUNCTIONS
// ============================================================

async function initIndicator(indicatorType) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    if (!config) {
        console.error(`Unknown indicator type: ${indicatorType}`);
        return;
    }
    
    const state = getIndicatorState(indicatorType);
    const prefix = config.chartPrefix;
    
    // Initialize date inputs
    const startDateInput = document.getElementById(`${prefix}-start-date`);
    const endDateInput = document.getElementById(`${prefix}-end-date`);
    
    if (startDateInput && endDateInput) {
        const end = new Date();
        const start = new Date();
        
        if (config.cycle === 'A') {
            // Annual: 10 years back
            start.setFullYear(end.getFullYear() - 10);
            startDateInput.value = start.getFullYear();
            endDateInput.value = end.getFullYear();
            startDateInput.min = 1960;
            endDateInput.min = 1960;
            startDateInput.max = end.getFullYear();
            endDateInput.max = end.getFullYear();
        } else {
            // Monthly/Quarterly: 2 years back
            start.setFullYear(end.getFullYear() - 2);
            startDateInput.value = start.toISOString().split('T')[0];
            endDateInput.value = end.toISOString().split('T')[0];
            startDateInput.max = endDateInput.value;
            endDateInput.max = endDateInput.value;
        }
        
        // Add change listeners
        startDateInput.addEventListener('change', () => {
            if (validateIndicatorDateRange(indicatorType)) {
                fetchIndicatorData(indicatorType);
            }
        });
        endDateInput.addEventListener('change', () => {
            if (validateIndicatorDateRange(indicatorType)) {
                fetchIndicatorData(indicatorType);
            }
        });
    }
    
    // Initialize cycle buttons if they exist
    document.querySelectorAll(`.${prefix}-cycle-btn`).forEach(btn => {
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        newBtn.addEventListener('click', function() {
            document.querySelectorAll(`.${prefix}-cycle-btn`).forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            state.cycle = this.getAttribute('data-cycle');
            fetchIndicatorData(indicatorType);
        });
    });
    
    // Load country list
    try {
        await fetchIndicatorCountryList(indicatorType);
        initIndicatorCountryChips(indicatorType);
        fetchIndicatorData(indicatorType);
    } catch (err) {
        console.error(`Failed to initialize ${indicatorType}:`, err);
    }
    
    state.isLoaded = true;
}

// ============================================================
// COUNTRY LIST FUNCTIONS
// ============================================================

async function fetchIndicatorCountryList(indicatorType) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    
    if (state.countryListLoaded && Object.keys(state.countryMapping).length > 0) {
        return state.countryMapping;
    }
    
    try {
        const url = `${API_BASE}/market/categories?category=${config.apiCategory}`;
        const response = await fetch(url);
        
        if (response.ok) {
            const data = await response.json();
            if (data.items && Object.keys(data.items).length > 0) {
                state.countryMapping = data.items;
                state.countryListLoaded = true;
                
                // Default: Korea only
                const itemCodes = Object.keys(state.countryMapping);
                const korCode = itemCodes.find(code => {
                    const name = state.countryMapping[code].name;
                    return name && (name.includes('한국') || name.includes('KOR') || name.toLowerCase().includes('korea'));
                });
                if (korCode) {
                    state.activeCountries = [korCode];
                } else if (itemCodes.length > 0) {
                    state.activeCountries = [itemCodes[0]];
                }
                
                return state.countryMapping;
            }
        }
        
        throw new Error('Failed to fetch country list');
    } catch (err) {
        console.error(`Failed to fetch ${indicatorType} country list:`, err);
        throw err;
    }
}

function initIndicatorCountryChips(indicatorType) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    const chipsContainer = document.getElementById(`${config.chartPrefix}-country-chips`);
    
    if (!chipsContainer) return;
    
    chipsContainer.innerHTML = '';
    
    const itemCodes = Object.keys(state.countryMapping);
    if (itemCodes.length === 0) {
        chipsContainer.innerHTML = '<span style="color: var(--text-sub); font-size: 0.8rem;">Loading...</span>';
        return;
    }
    
    itemCodes.forEach(itemCode => {
        const countryInfo = state.countryMapping[itemCode];
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.setAttribute('data-item-code', itemCode);
        chip.setAttribute('title', countryInfo.name);
        
        const isActive = state.activeCountries.includes(itemCode);
        if (isActive) {
            chip.classList.add('active');
        }
        
        const countryColor = getCountryColor(itemCode, state.countryMapping);
        
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
        const englishName = getCountryNameEnglish(countryInfo.name);
        chip.appendChild(document.createTextNode(englishName));
        
        chip.addEventListener('click', () => toggleIndicatorCountry(indicatorType, itemCode));
        
        chipsContainer.appendChild(chip);
    });
}

function toggleIndicatorCountry(indicatorType, itemCode) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    const index = state.activeCountries.indexOf(itemCode);
    
    if (index === -1) {
        state.activeCountries.push(itemCode);
    } else {
        state.activeCountries.splice(index, 1);
    }
    
    // Update UI
    const chip = document.querySelector(`#${config.chartPrefix}-country-chips [data-item-code="${itemCode}"]`);
    if (chip) {
        const chipDot = chip.querySelector('.chip-dot');
        const isActive = state.activeCountries.includes(itemCode);
        
        if (isActive) {
            chip.classList.add('active');
            const countryColor = getCountryColor(itemCode, state.countryMapping);
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
    
    if (validateIndicatorDateRange(indicatorType)) {
        fetchIndicatorData(indicatorType);
    }
}

// ============================================================
// DATE VALIDATION
// ============================================================

function validateIndicatorDateRange(indicatorType) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const prefix = config.chartPrefix;
    const startInput = document.getElementById(`${prefix}-start-date`);
    const endInput = document.getElementById(`${prefix}-end-date`);
    
    if (!startInput || !endInput) return false;
    
    if (config.cycle === 'A') {
        const startYear = parseInt(startInput.value, 10);
        const endYear = parseInt(endInput.value, 10);
        if (isNaN(startYear) || isNaN(endYear) || startYear > endYear) {
            return false;
        }
    } else {
        const startDate = new Date(startInput.value);
        const endDate = new Date(endInput.value);
        if (isNaN(startDate.getTime()) || isNaN(endDate.getTime()) || startDate > endDate) {
            return false;
        }
    }
    
    return true;
}

// ============================================================
// DATA FETCHING
// ============================================================

async function fetchIndicatorData(indicatorType) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    const prefix = config.chartPrefix;
    
    if (!validateIndicatorDateRange(indicatorType)) return;
    if (state.activeCountries.length === 0) {
        updateIndicatorChart(indicatorType);
        return;
    }
    
    const startInput = document.getElementById(`${prefix}-start-date`);
    const endInput = document.getElementById(`${prefix}-end-date`);
    
    let startDate, endDate;
    if (config.cycle === 'A') {
        startDate = `${startInput.value}0101`;
        endDate = `${endInput.value}1231`;
    } else {
        startDate = formatDateForAPI(startInput.value);
        endDate = formatDateForAPI(endInput.value);
    }
    
    const chartContainer = document.getElementById(`${prefix}-chart-container`);
    if (chartContainer) chartContainer.style.opacity = '0.5';
    
    try {
        const fetchPromises = state.activeCountries.map(async (itemCode) => {
            const url = `${API_BASE}/market/indices?type=${config.apiCategory}&itemCode=${itemCode}&startDate=${startDate}&endDate=${endDate}&cycle=${state.cycle}`;
            
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
        processIndicatorData(indicatorType, results);
        
    } catch (err) {
        console.error(`Failed to fetch ${indicatorType} data:`, err);
    } finally {
        if (chartContainer) chartContainer.style.opacity = '1';
    }
}

function processIndicatorData(indicatorType, results) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    
    state.countryData = {};
    
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
        
        values.sort((a, b) => compareIndicatorDates(a.date, b.date, state.cycle));
        state.countryData[itemCode] = values;
    });
    
    updateIndicatorChart(indicatorType);
}

// ============================================================
// CHART RENDERING
// ============================================================

function updateIndicatorChart(indicatorType) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    const prefix = config.chartPrefix;
    
    const svg = document.getElementById(`${prefix}-chart-svg`);
    const pointsGroup = document.getElementById(`${prefix}-data-points`);
    const pathsGroup = document.getElementById(`${prefix}-paths-group`);
    
    if (!svg) return;
    
    // Clear existing paths - both from pathsGroup and directly from SVG
    if (pathsGroup) {
        pathsGroup.innerHTML = '';
    } else {
        // If no pathsGroup, remove any existing chart-path elements from SVG
        svg.querySelectorAll('.chart-path').forEach(el => el.remove());
    }
    if (pointsGroup) pointsGroup.innerHTML = '';
    
    if (state.activeCountries.length === 0) {
        renderIndicatorYAxisLabels(indicatorType, []);
        renderIndicatorXAxisLabels(indicatorType, []);
        return;
    }
    
    // Merge all dates
    const allDates = new Set();
    Object.values(state.countryData).forEach(data => {
        data.forEach(item => allDates.add(item.date));
    });
    const sortedDates = Array.from(allDates).sort((a, b) => 
        compareIndicatorDates(a, b, state.cycle)
    );
    
    if (sortedDates.length === 0) {
        renderIndicatorYAxisLabels(indicatorType, []);
        renderIndicatorXAxisLabels(indicatorType, []);
        return;
    }
    
    // Calculate Y-axis range
    const allValues = [];
    Object.values(state.countryData).forEach(data => {
        data.forEach(item => allValues.push(item.value));
    });
    
    if (allValues.length === 0) {
        renderIndicatorYAxisLabels(indicatorType, []);
        renderIndicatorXAxisLabels(indicatorType, sortedDates);
        return;
    }
    
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const range = maxValue - minValue || 1;
    const paddingPercent = 0.05;
    state.yAxisRange = {
        min: Math.max(0, minValue - range * paddingPercent),
        max: maxValue + range * paddingPercent
    };
    
    renderIndicatorYAxisLabels(indicatorType, sortedDates);
    
    // Render paths for each country
    state.activeCountries.forEach(itemCode => {
        const data = state.countryData[itemCode];
        if (!data || data.length === 0) return;
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.classList.add('chart-path', 'visible');
        path.setAttribute('stroke', getCountryColor(itemCode, state.countryMapping));
        path.setAttribute('stroke-width', '2.5');
        path.setAttribute('fill', 'none');
        
        // Generate path data
        const sortedData = sortedDates.map(date => {
            const found = data.find(item => item.date === date);
            return found || { date, value: null };
        }).filter(item => item.value !== null);
        
        if (sortedData.length > 0) {
            const pathData = generateIndicatorSVGPath(indicatorType, sortedData);
            path.setAttribute('d', pathData);
            if (pathsGroup) {
                pathsGroup.appendChild(path);
            } else {
                svg.insertBefore(path, pointsGroup);
            }
        }
    });
    
    renderIndicatorXAxisLabels(indicatorType, sortedDates);
    setupIndicatorChartInteractivity(indicatorType);
    updateIndicatorChartHeader(indicatorType);
}

function generateIndicatorSVGPath(indicatorType, data) {
    if (!data || data.length === 0) return '';
    
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    const svg = document.getElementById(`${config.chartPrefix}-chart-svg`);
    if (!svg) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 60, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const minValue = state.yAxisRange.min;
    const maxValue = state.yAxisRange.max;
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

function renderIndicatorYAxisLabels(indicatorType, sortedDates) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    const yAxisGroup = document.getElementById(`${config.chartPrefix}-y-axis-labels`);
    if (!yAxisGroup) return;
    
    yAxisGroup.innerHTML = '';
    
    const minValue = state.yAxisRange.min;
    const maxValue = state.yAxisRange.max;
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
        
        // Format based on unit
        if (config.unit === '%') {
            label.textContent = value.toFixed(1) + '%';
        } else if (config.unit === 'Index') {
            label.textContent = value.toLocaleString('en-US', { maximumFractionDigits: 0 });
        } else {
            label.textContent = value.toLocaleString('en-US', { maximumFractionDigits: 0 });
        }
        
        yAxisGroup.appendChild(label);
    }
}

function renderIndicatorXAxisLabels(indicatorType, sortedDates) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    const xAxisGroup = document.getElementById(`${config.chartPrefix}-x-axis-labels`);
    if (!xAxisGroup || !sortedDates || sortedDates.length === 0) return;
    
    xAxisGroup.innerHTML = '';
    
    const svg = document.getElementById(`${config.chartPrefix}-chart-svg`);
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
        label.textContent = formatIndicatorDateLabel(date, state.cycle);
        
        xAxisGroup.appendChild(label);
    });
}

// ============================================================
// CHART INTERACTIVITY
// ============================================================

function setupIndicatorChartInteractivity(indicatorType) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    const prefix = config.chartPrefix;
    
    const chartContainer = document.getElementById(`${prefix}-chart-container`);
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    
    if (!chartContainer || !tooltip) return;
    
    // Move tooltip to body
    if (tooltip.parentElement !== document.body) {
        document.body.appendChild(tooltip);
    }
    
    // Remove existing listeners
    const newContainer = chartContainer.cloneNode(true);
    chartContainer.parentNode.replaceChild(newContainer, chartContainer);
    
    let rafId = null;
    
    newContainer.addEventListener('mousemove', (event) => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
            rafId = null;
            showIndicatorTooltip(indicatorType, event);
        });
    });
    
    newContainer.addEventListener('mouseleave', () => {
        if (rafId) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
        hideIndicatorTooltip(indicatorType);
    });
}

function showIndicatorTooltip(indicatorType, event) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    const prefix = config.chartPrefix;
    
    const tooltip = document.getElementById(`${prefix}-chart-tooltip`);
    const svg = document.getElementById(`${prefix}-chart-svg`);
    if (!tooltip || !svg) return;
    
    const rect = svg.getBoundingClientRect();
    const x = event.clientX - rect.left;
    
    const { width } = getSvgViewBoxSize(svg);
    const chartPadding = { left: 60, right: 20 };
    const chartWidth = width - chartPadding.left - chartPadding.right;
    
    // Merge all dates
    const allDates = new Set();
    Object.values(state.countryData).forEach(data => {
        data.forEach(item => allDates.add(item.date));
    });
    const sortedDates = Array.from(allDates).sort((a, b) => 
        compareIndicatorDates(a, b, state.cycle)
    );
    
    if (sortedDates.length === 0) return;
    
    const dateIndex = Math.round(((x / rect.width * width) - chartPadding.left) / chartWidth * (sortedDates.length - 1));
    const dateIndexClamped = Math.max(0, Math.min(sortedDates.length - 1, dateIndex));
    const date = sortedDates[dateIndexClamped];
    
    const dateLabel = formatIndicatorDateLabel(date, state.cycle);
    
    let content = '';
    state.activeCountries.forEach(itemCode => {
        const data = state.countryData[itemCode];
        if (!data) return;
        
        const item = data.find(d => d.date === date);
        if (!item) return;
        
        const countryInfo = state.countryMapping[itemCode];
        const countryName = countryInfo ? getCountryNameEnglish(countryInfo.name) : itemCode;
        const color = getCountryColor(itemCode, state.countryMapping);
        
        const tempEl = document.createElement('div');
        tempEl.style.color = color;
        document.body.appendChild(tempEl);
        const computedColor = window.getComputedStyle(tempEl).color;
        document.body.removeChild(tempEl);
        
        let valueText;
        if (config.unit === '%') {
            valueText = item.value.toFixed(1) + '%';
        } else if (config.unit === 'Index') {
            valueText = item.value.toLocaleString('en-US', { maximumFractionDigits: 2 });
        } else {
            valueText = item.value.toLocaleString('en-US', { maximumFractionDigits: 2 });
        }
        
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
        hideIndicatorTooltip(indicatorType);
        return;
    }
    
    const tooltipContent = document.getElementById(`${prefix}-tooltip-content`);
    const tooltipDate = document.getElementById(`${prefix}-tooltip-date`);
    
    if (tooltipContent) tooltipContent.innerHTML = content;
    if (tooltipDate) tooltipDate.textContent = dateLabel;
    
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

function hideIndicatorTooltip(indicatorType) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const tooltip = document.getElementById(`${config.chartPrefix}-chart-tooltip`);
    if (tooltip) {
        tooltip.classList.remove('visible');
        tooltip.style.visibility = 'hidden';
    }
}

function updateIndicatorChartHeader(indicatorType) {
    const config = INTERNATIONAL_INDICATORS_CONFIG[indicatorType];
    const state = getIndicatorState(indicatorType);
    const prefix = config.chartPrefix;
    
    if (state.activeCountries.length === 0) return;
    
    const firstCountryCode = state.activeCountries[0];
    const firstCountryData = state.countryData[firstCountryCode];
    
    if (!firstCountryData || firstCountryData.length === 0) return;
    
    const values = firstCountryData.map(item => item.value);
    const high = Math.max(...values);
    const low = Math.min(...values);
    const average = values.reduce((sum, v) => sum + v, 0) / values.length;
    const current = firstCountryData[firstCountryData.length - 1].value;
    
    const countryInfo = state.countryMapping[firstCountryCode];
    const countryName = countryInfo ? getCountryNameEnglish(countryInfo.name) : firstCountryCode;
    
    const titleEl = document.getElementById(`${prefix}-chart-main-title`);
    if (titleEl) titleEl.textContent = `${config.title} - ${countryName}`;
    
    const valueEl = document.getElementById(`${prefix}-chart-main-value`);
    if (valueEl) {
        if (config.unit === '%') {
            valueEl.textContent = current.toFixed(1) + '%';
        } else {
            valueEl.textContent = current.toLocaleString('en-US', { maximumFractionDigits: 2 });
        }
    }
    
    const formatStat = (val) => {
        if (config.unit === '%') return val.toFixed(1) + '%';
        return val.toLocaleString('en-US', { maximumFractionDigits: 2 });
    };
    
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

// Export init functions with proper window flag setting
window.initGDPIndicator = async () => {
    await initIndicator('gdp-indicator');
    window.gdpIndicatorDataLoaded = true;
};
window.initGDPPerCapita = async () => {
    await initIndicator('gdp-per-capita');
    window.gdpPerCapitaDataLoaded = true;
};
window.initGNI = async () => {
    await initIndicator('gni');
    window.gniDataLoaded = true;
};
window.initEmployment = async () => {
    await initIndicator('employment');
    window.employmentDataLoaded = true;
};
window.initGlobalStocks = async () => {
    await initIndicator('global-stocks');
    window.globalStocksDataLoaded = true;
};

// Export toggle functions
window.toggleGDPIndicatorCountry = (itemCode) => toggleIndicatorCountry('gdp-indicator', itemCode);
window.toggleGDPPerCapitaCountry = (itemCode) => toggleIndicatorCountry('gdp-per-capita', itemCode);
window.toggleGNICountry = (itemCode) => toggleIndicatorCountry('gni', itemCode);
window.toggleEmploymentCountry = (itemCode) => toggleIndicatorCountry('employment', itemCode);
window.toggleGlobalStocksCountry = (itemCode) => toggleIndicatorCountry('global-stocks', itemCode);

console.log('📊 International Indicators module loaded');

