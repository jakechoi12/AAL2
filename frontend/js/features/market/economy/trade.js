/**
 * AAL Application - Trade Module (International Export/Import)
 * 국제 수출입 통계 관련 기능 모듈
 * 
 * 담당 패널: #trade-panel
 * 주요 기능: 국제 주요국 수출/수입 차트, 국가별 비교
 */

// ============================================================
// MODULE MARKER
// ============================================================
window.tradeModuleLoaded = true;

// ============================================================
// CONFIGURATION
// ============================================================

const TRADE_CONFIG = {
    exportCategory: 'export-international',
    importCategory: 'import-international',
    panelId: 'trade-panel',
    title: 'Export x Import',
    description: '국제 주요국 수출입 통계',
    availableCycles: ['A', 'M', 'Q'],
    unit: 'M USD',
    chartPrefix: 'trade'
};

// ============================================================
// STATE MANAGEMENT
// ============================================================

const tradeState = {
    countryMapping: {},
    activeCountries: [],
    countryData: {},      // { itemCode: { export: [], import: [], balance: [] } }
    yAxisRange: { min: 0, max: 0 },
    cycle: 'M',
    isLoaded: false,
    countryListLoaded: false,
    showExport: true,
    showImport: true,
    showBalance: true  // Trade Balance = Export - Import
};

// Trade indicator colors
const TRADE_COLORS = {
    export: '#2196F3',   // Blue
    import: '#F44336',   // Red
    balance: '#4CAF50'   // Green
};

// ============================================================
// COUNTRY INFO MAPPING
// ============================================================

const tradeCountryInfoMap = [
    { keywords: ['호주', 'aus', 'australia'], englishName: 'Australia', color: 'var(--c-interest-aus)' },
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
    { keywords: ['스페인', 'esp', 'spain'], englishName: 'Spain', color: 'var(--c-interest-esp)' },
    { keywords: ['에스토니아', 'est', 'estonia'], englishName: 'Estonia', color: '#1ABC9C' },
    { keywords: ['핀란드', 'fin', 'finland'], englishName: 'Finland', color: '#3498DB' },
    { keywords: ['프랑스', 'fra', 'france'], englishName: 'France', color: 'var(--c-interest-fra)' },
    { keywords: ['영국', 'gbr', 'uk', 'united kingdom'], englishName: 'UK', color: 'var(--c-interest-gbr)' },
    { keywords: ['그리스', 'grc', 'greece'], englishName: 'Greece', color: '#2980B9' },
    { keywords: ['헝가리', 'hun', 'hungary'], englishName: 'Hungary', color: 'var(--c-interest-hun)' },
    { keywords: ['인도네시아', 'idn', 'indonesia'], englishName: 'Indonesia', color: 'var(--c-interest-idn)' },
    { keywords: ['아일랜드', 'irl', 'ireland'], englishName: 'Ireland', color: '#27AE60' },
    { keywords: ['이스라엘', 'isr', 'israel'], englishName: 'Israel', color: 'var(--c-interest-isr)' },
    { keywords: ['인도', 'ind', 'india'], englishName: 'India', color: 'var(--c-interest-ind)' },
    { keywords: ['이탈리아', 'ita', 'italy'], englishName: 'Italy', color: 'var(--c-interest-ita)' },
    { keywords: ['일본', 'jpn', 'japan'], englishName: 'Japan', color: 'var(--c-interest-jpn)' },
    { keywords: ['한국', 'kor', 'korea'], englishName: 'Korea', color: 'var(--c-interest-kor)' },
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
    { keywords: ['아이슬란드', 'isl', 'iceland'], englishName: 'Iceland', color: '#7FB3D5' },
    { keywords: ['라트비아', 'lva', 'latvia'], englishName: 'Latvia', color: '#A569BD' },
    { keywords: ['룩셈부르크', 'lux', 'luxembourg'], englishName: 'Luxembourg', color: '#F5B041' }
];

function getTradeCountryNameEnglish(koreanName) {
    if (!koreanName) return koreanName;
    const name = koreanName.toLowerCase();
    for (const info of tradeCountryInfoMap) {
        if (info.keywords.some(keyword => name.includes(keyword))) {
            return info.englishName;
        }
    }
    return koreanName;
}

function getTradeCountryColor(itemCode) {
    const countryInfo = tradeState.countryMapping[itemCode];
    if (!countryInfo) {
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE'];
        let hash = 0;
        for (let i = 0; i < itemCode.length; i++) {
            hash = ((hash << 5) - hash) + itemCode.charCodeAt(i);
        }
        return colors[Math.abs(hash) % colors.length];
    }
    
    const name = countryInfo.name?.toLowerCase() || '';
    for (const info of tradeCountryInfoMap) {
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

function parseTradeDate(dateStr) {
    if (!dateStr) return null;
    if (dateStr.length === 4) {
        return new Date(parseInt(dateStr, 10), 0, 1);
    } else if (dateStr.length === 6) {
        const year = parseInt(dateStr.substring(0, 4), 10);
        const month = parseInt(dateStr.substring(4, 6), 10) - 1;
        return new Date(year, month, 1);
    } else if (dateStr.length === 7 && dateStr.includes('Q')) {
        const year = parseInt(dateStr.substring(0, 4), 10);
        const quarter = parseInt(dateStr.substring(5, 6), 10);
        return new Date(year, (quarter - 1) * 3, 1);
    }
    return null;
}

function compareTradeDates(a, b) {
    const da = parseTradeDate(a);
    const db = parseTradeDate(b);
    if (!da || !db) return String(a).localeCompare(String(b));
    return da.getTime() - db.getTime();
}

function formatTradeDateLabel(dateStr) {
    if (!dateStr) return '';
    if (dateStr.length === 4) return dateStr;
    if (dateStr.length === 6) {
        return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}`;
    }
    return dateStr;
}

// ============================================================
// INITIALIZATION
// ============================================================

async function initTrade() {
    const prefix = TRADE_CONFIG.chartPrefix;
    
    const startDateInput = document.getElementById(`${prefix}-start-date`);
    const endDateInput = document.getElementById(`${prefix}-end-date`);
    
    if (startDateInput && endDateInput) {
        const end = new Date();
        const start = new Date();
        start.setFullYear(end.getFullYear() - 5);
        
        // Set default values based on cycle
        if (tradeState.cycle === 'A') {
            startDateInput.type = 'number';
            endDateInput.type = 'number';
            startDateInput.value = start.getFullYear();
            endDateInput.value = end.getFullYear();
            startDateInput.min = 1960;
            endDateInput.min = 1960;
        } else {
            startDateInput.type = 'date';
            endDateInput.type = 'date';
            startDateInput.value = start.toISOString().split('T')[0];
            endDateInput.value = end.toISOString().split('T')[0];
        }
        
        startDateInput.addEventListener('change', () => {
            if (validateTradeDateRange()) fetchTradeData();
        });
        endDateInput.addEventListener('change', () => {
            if (validateTradeDateRange()) fetchTradeData();
        });
    }
    
    // Initialize cycle buttons
    initTradeCycleButtons();
    
    try {
        await fetchTradeCountryList();
        initTradeCountryChips();
        fetchTradeData();
    } catch (err) {
        console.error('Failed to initialize Trade:', err);
    }
    
    tradeState.isLoaded = true;
    window.tradeDataLoaded = true;
}

function initTradeCycleButtons() {
    const container = document.getElementById(`${TRADE_CONFIG.chartPrefix}-indicator-toggles`);
    if (!container) return;
    
    // Clear existing content
    container.innerHTML = '';
    
    // Add Export/Import/Balance toggles
    const indicators = [
        { id: 'export', name: 'Export', active: tradeState.showExport, color: TRADE_COLORS.export },
        { id: 'import', name: 'Import', active: tradeState.showImport, color: TRADE_COLORS.import },
        { id: 'balance', name: 'Trade Balance', active: tradeState.showBalance, color: TRADE_COLORS.balance }
    ];
    
    indicators.forEach(ind => {
        const chip = document.createElement('button');
        chip.className = 'chip' + (ind.active ? ' active' : '');
        chip.setAttribute('data-indicator', ind.id);
        
        const dot = document.createElement('div');
        dot.className = 'chip-dot';
        dot.style.background = ind.color;
        
        chip.appendChild(dot);
        chip.appendChild(document.createTextNode(ind.name));
        
        // Apply active styles
        if (ind.active) {
            chip.style.borderColor = ind.color;
            chip.style.color = ind.color;
            // Set semi-transparent background
            const r = parseInt(ind.color.slice(1, 3), 16);
            const g = parseInt(ind.color.slice(3, 5), 16);
            const b = parseInt(ind.color.slice(5, 7), 16);
            chip.style.background = `rgba(${r}, ${g}, ${b}, 0.2)`;
        }
        
        chip.addEventListener('click', () => {
            if (ind.id === 'export') {
                tradeState.showExport = !tradeState.showExport;
            } else if (ind.id === 'import') {
                tradeState.showImport = !tradeState.showImport;
            } else if (ind.id === 'balance') {
                tradeState.showBalance = !tradeState.showBalance;
            }
            
            chip.classList.toggle('active');
            
            // Update chip styles
            const isActive = chip.classList.contains('active');
            if (isActive) {
                chip.style.borderColor = ind.color;
                chip.style.color = ind.color;
                const r = parseInt(ind.color.slice(1, 3), 16);
                const g = parseInt(ind.color.slice(3, 5), 16);
                const b = parseInt(ind.color.slice(5, 7), 16);
                chip.style.background = `rgba(${r}, ${g}, ${b}, 0.2)`;
            } else {
                chip.style.borderColor = '';
                chip.style.color = '';
                chip.style.background = '';
            }
            
            updateTradeChart();
        });
        
        container.appendChild(chip);
    });
}

function updateTradeDateInputs() {
    const prefix = TRADE_CONFIG.chartPrefix;
    const startDateInput = document.getElementById(`${prefix}-start-date`);
    const endDateInput = document.getElementById(`${prefix}-end-date`);
    
    if (!startDateInput || !endDateInput) return;
    
    const end = new Date();
    const start = new Date();
    start.setFullYear(end.getFullYear() - 5);
    
    if (tradeState.cycle === 'A') {
        startDateInput.type = 'number';
        endDateInput.type = 'number';
        startDateInput.value = start.getFullYear();
        endDateInput.value = end.getFullYear();
        startDateInput.min = 1960;
        endDateInput.min = 1960;
    } else {
        startDateInput.type = 'date';
        endDateInput.type = 'date';
        startDateInput.value = start.toISOString().split('T')[0];
        endDateInput.value = end.toISOString().split('T')[0];
    }
}

// ============================================================
// COUNTRY LIST
// ============================================================

async function fetchTradeCountryList() {
    if (tradeState.countryListLoaded && Object.keys(tradeState.countryMapping).length > 0) {
        return tradeState.countryMapping;
    }
    
    try {
        const url = `${API_BASE}/market/categories?category=${TRADE_CONFIG.exportCategory}`;
        const response = await fetch(url);
        
        if (response.ok) {
            const data = await response.json();
            if (data.items && Object.keys(data.items).length > 0) {
                tradeState.countryMapping = data.items;
                tradeState.countryListLoaded = true;
                
                const itemCodes = Object.keys(tradeState.countryMapping);
                const korCode = itemCodes.find(code => {
                    const name = tradeState.countryMapping[code].name;
                    return name && (name.includes('한국') || code === 'KR' || name.toLowerCase().includes('korea'));
                });
                if (korCode) {
                    tradeState.activeCountries = [korCode];
                } else if (itemCodes.length > 0) {
                    tradeState.activeCountries = [itemCodes[0]];
                }
                
                return tradeState.countryMapping;
            }
        }
        throw new Error('Failed to fetch country list');
    } catch (err) {
        console.error('Failed to fetch Trade country list:', err);
        throw err;
    }
}

function initTradeCountryChips() {
    const chipsContainer = document.getElementById(`${TRADE_CONFIG.chartPrefix}-country-chips`);
    if (!chipsContainer) return;
    
    chipsContainer.innerHTML = '';
    
    const itemCodes = Object.keys(tradeState.countryMapping);
    if (itemCodes.length === 0) {
        chipsContainer.innerHTML = '<span style="color: var(--text-sub); font-size: 0.8rem;">Loading...</span>';
        return;
    }
    
    itemCodes.forEach(itemCode => {
        const countryInfo = tradeState.countryMapping[itemCode];
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.setAttribute('data-item-code', itemCode);
        chip.setAttribute('title', countryInfo.name);
        
        const isActive = tradeState.activeCountries.includes(itemCode);
        if (isActive) chip.classList.add('active');
        
        const countryColor = getTradeCountryColor(itemCode);
        const chipDot = document.createElement('div');
        chipDot.className = 'chip-dot';
        
        if (isActive) {
            chipDot.style.background = countryColor;
            chip.style.borderColor = countryColor;
            chip.style.color = countryColor;
        } else {
            chipDot.style.background = 'currentColor';
        }
        
        chip.appendChild(chipDot);
        const englishName = getTradeCountryNameEnglish(countryInfo.name);
        chip.appendChild(document.createTextNode(englishName));
        
        chip.addEventListener('click', () => toggleTradeCountry(itemCode));
        chipsContainer.appendChild(chip);
    });
}

function toggleTradeCountry(itemCode) {
    const index = tradeState.activeCountries.indexOf(itemCode);
    
    if (index === -1) {
        tradeState.activeCountries.push(itemCode);
    } else {
        tradeState.activeCountries.splice(index, 1);
    }
    
    const chip = document.querySelector(`#${TRADE_CONFIG.chartPrefix}-country-chips [data-item-code="${itemCode}"]`);
    if (chip) {
        const chipDot = chip.querySelector('.chip-dot');
        const isActive = tradeState.activeCountries.includes(itemCode);
        
        if (isActive) {
            chip.classList.add('active');
            const countryColor = getTradeCountryColor(itemCode);
            if (chipDot) chipDot.style.background = countryColor;
            chip.style.borderColor = countryColor;
            chip.style.color = countryColor;
        } else {
            chip.classList.remove('active');
            if (chipDot) chipDot.style.background = 'currentColor';
            chip.style.borderColor = '';
            chip.style.color = '';
        }
    }
    
    if (validateTradeDateRange()) fetchTradeData();
}

// ============================================================
// DATE VALIDATION
// ============================================================

function validateTradeDateRange() {
    const prefix = TRADE_CONFIG.chartPrefix;
    const startInput = document.getElementById(`${prefix}-start-date`);
    const endInput = document.getElementById(`${prefix}-end-date`);
    
    if (!startInput || !endInput) return false;
    
    if (tradeState.cycle === 'A') {
        const startYear = parseInt(startInput.value, 10);
        const endYear = parseInt(endInput.value, 10);
        return !(isNaN(startYear) || isNaN(endYear) || startYear > endYear);
    } else {
        const startDate = new Date(startInput.value);
        const endDate = new Date(endInput.value);
        return startDate <= endDate;
    }
}

// ============================================================
// DATA FETCHING
// ============================================================

async function fetchTradeData() {
    const prefix = TRADE_CONFIG.chartPrefix;
    
    if (!validateTradeDateRange()) return;
    if (tradeState.activeCountries.length === 0) {
        updateTradeChart();
        return;
    }
    
    const startInput = document.getElementById(`${prefix}-start-date`);
    const endInput = document.getElementById(`${prefix}-end-date`);
    
    let startDate, endDate;
    if (tradeState.cycle === 'A') {
        startDate = `${startInput.value}0101`;
        endDate = `${endInput.value}1231`;
    } else {
        startDate = startInput.value.replace(/-/g, '');
        endDate = endInput.value.replace(/-/g, '');
    }
    
    const chartContainer = document.getElementById(`${prefix}-chart-container`);
    if (chartContainer) chartContainer.style.opacity = '0.5';
    
    try {
        const fetchPromises = tradeState.activeCountries.map(async (itemCode) => {
            const exportUrl = `${API_BASE}/market/indices?type=${TRADE_CONFIG.exportCategory}&itemCode=${itemCode}&startDate=${startDate}&endDate=${endDate}&cycle=${tradeState.cycle}`;
            const importUrl = `${API_BASE}/market/indices?type=${TRADE_CONFIG.importCategory}&itemCode=${itemCode}&startDate=${startDate}&endDate=${endDate}&cycle=${tradeState.cycle}`;
            
            try {
                const [exportRes, importRes] = await Promise.all([
                    fetch(exportUrl).then(r => r.json()),
                    fetch(importUrl).then(r => r.json())
                ]);
                return { itemCode, exportData: exportRes, importData: importRes };
            } catch (err) {
                console.error(`Failed to fetch ${itemCode}:`, err);
                return { itemCode, exportData: { error: err.message }, importData: { error: err.message } };
            }
        });
        
        const results = await Promise.all(fetchPromises);
        processTradeData(results);
        
    } catch (err) {
        console.error('Failed to fetch Trade data:', err);
    } finally {
        if (chartContainer) chartContainer.style.opacity = '1';
    }
}

function processTradeData(results) {
    tradeState.countryData = {};
    
    results.forEach(({ itemCode, exportData, importData }) => {
        const exportValues = processTradeApiData(exportData);
        const importValues = processTradeApiData(importData);
        
        // Calculate Trade Balance (Export - Import)
        const balanceValues = calculateTradeBalance(exportValues, importValues);
        
        tradeState.countryData[itemCode] = {
            export: exportValues,
            import: importValues,
            balance: balanceValues
        };
    });
    
    updateTradeChart();
}

function calculateTradeBalance(exportData, importData) {
    // Create a map of dates to values for quick lookup
    const importMap = new Map();
    importData.forEach(item => {
        importMap.set(item.date, item.value);
    });
    
    // Calculate balance for each export date
    const balanceData = [];
    exportData.forEach(exportItem => {
        const importValue = importMap.get(exportItem.date);
        if (importValue !== undefined) {
            balanceData.push({
                date: exportItem.date,
                value: exportItem.value - importValue
            });
        }
    });
    
    return balanceData.sort((a, b) => compareTradeDates(a.date, b.date));
}

function processTradeApiData(apiData) {
    if (!apiData?.StatisticSearch?.row) return [];
    return apiData.StatisticSearch.row
        .map(row => ({
            date: row.TIME,
            value: parseFloat(row.DATA_VALUE)
        }))
        .filter(item => !isNaN(item.value))
        .sort((a, b) => compareTradeDates(a.date, b.date));
}

// ============================================================
// CHART RENDERING
// ============================================================

function updateTradeChart() {
    const prefix = TRADE_CONFIG.chartPrefix;
    const svg = document.getElementById(`${prefix}-chart-svg`);
    const pointsGroup = document.getElementById(`${prefix}-data-points`);
    const pathsGroup = document.getElementById(`${prefix}-paths-group`);
    
    if (!svg) return;
    
    if (pathsGroup) pathsGroup.innerHTML = '';
    else svg.querySelectorAll('.chart-path').forEach(el => el.remove());
    if (pointsGroup) pointsGroup.innerHTML = '';
    
    if (tradeState.activeCountries.length === 0) {
        renderTradeYAxisLabels([]);
        renderTradeXAxisLabels([]);
        return;
    }
    
    // Collect all dates
    const allDates = new Set();
    Object.values(tradeState.countryData).forEach(data => {
        if (tradeState.showExport) data.export.forEach(item => allDates.add(item.date));
        if (tradeState.showImport) data.import.forEach(item => allDates.add(item.date));
        if (tradeState.showBalance && data.balance) data.balance.forEach(item => allDates.add(item.date));
    });
    const sortedDates = Array.from(allDates).sort((a, b) => compareTradeDates(a, b));
    
    if (sortedDates.length === 0) {
        renderTradeYAxisLabels([]);
        renderTradeXAxisLabels([]);
        return;
    }
    
    // Calculate Y-axis range
    const allValues = [];
    Object.values(tradeState.countryData).forEach(data => {
        if (tradeState.showExport) data.export.forEach(item => allValues.push(item.value));
        if (tradeState.showImport) data.import.forEach(item => allValues.push(item.value));
        if (tradeState.showBalance && data.balance) data.balance.forEach(item => allValues.push(item.value));
    });
    
    if (allValues.length === 0) {
        renderTradeYAxisLabels([]);
        renderTradeXAxisLabels(sortedDates);
        return;
    }
    
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const range = maxValue - minValue || 1;
    // Allow negative values for Trade Balance
    tradeState.yAxisRange = {
        min: minValue - range * 0.05,
        max: maxValue + range * 0.05
    };
    
    renderTradeYAxisLabels(sortedDates);
    
    // Render paths for each country
    tradeState.activeCountries.forEach(itemCode => {
        const data = tradeState.countryData[itemCode];
        if (!data) return;
        
        // Export path (solid blue line)
        if (tradeState.showExport && data.export.length > 0) {
            const exportPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            exportPath.classList.add('chart-path', 'visible');
            exportPath.setAttribute('stroke', TRADE_COLORS.export);
            exportPath.setAttribute('stroke-width', '2.5');
            exportPath.setAttribute('fill', 'none');
            
            const sortedExport = sortedDates.map(date => {
                const found = data.export.find(item => item.date === date);
                return found || { date, value: null };
            }).filter(item => item.value !== null);
            
            if (sortedExport.length > 0) {
                const pathData = generateTradeSVGPath(sortedExport, sortedDates);
                exportPath.setAttribute('d', pathData);
                if (pathsGroup) pathsGroup.appendChild(exportPath);
                else svg.insertBefore(exportPath, pointsGroup);
            }
        }
        
        // Import path (solid red line)
        if (tradeState.showImport && data.import.length > 0) {
            const importPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            importPath.classList.add('chart-path', 'visible');
            importPath.setAttribute('stroke', TRADE_COLORS.import);
            importPath.setAttribute('stroke-width', '2.5');
            importPath.setAttribute('fill', 'none');
            
            const sortedImport = sortedDates.map(date => {
                const found = data.import.find(item => item.date === date);
                return found || { date, value: null };
            }).filter(item => item.value !== null);
            
            if (sortedImport.length > 0) {
                const pathData = generateTradeSVGPath(sortedImport, sortedDates);
                importPath.setAttribute('d', pathData);
                if (pathsGroup) pathsGroup.appendChild(importPath);
                else svg.insertBefore(importPath, pointsGroup);
            }
        }
        
        // Trade Balance path (solid green line)
        if (tradeState.showBalance && data.balance && data.balance.length > 0) {
            const balancePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            balancePath.classList.add('chart-path', 'visible');
            balancePath.setAttribute('stroke', TRADE_COLORS.balance);
            balancePath.setAttribute('stroke-width', '2.5');
            balancePath.setAttribute('fill', 'none');
            
            const sortedBalance = sortedDates.map(date => {
                const found = data.balance.find(item => item.date === date);
                return found || { date, value: null };
            }).filter(item => item.value !== null);
            
            if (sortedBalance.length > 0) {
                const pathData = generateTradeSVGPath(sortedBalance, sortedDates);
                balancePath.setAttribute('d', pathData);
                if (pathsGroup) pathsGroup.appendChild(balancePath);
                else svg.insertBefore(balancePath, pointsGroup);
            }
        }
    });
    
    renderTradeXAxisLabels(sortedDates);
    setupTradeChartInteractivity();
    updateTradeChartHeader();
}

function generateTradeSVGPath(data, allDates) {
    if (!data || data.length === 0) return '';
    
    const svg = document.getElementById(`${TRADE_CONFIG.chartPrefix}-chart-svg`);
    if (!svg) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 60, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const minValue = tradeState.yAxisRange.min;
    const maxValue = tradeState.yAxisRange.max;
    const valueRange = maxValue - minValue || 1;
    
    let pathData = '';
    data.forEach((point, index) => {
        const dateIndex = allDates.indexOf(point.date);
        const x = padding.left + (dateIndex / (allDates.length - 1 || 1)) * chartWidth;
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

function renderTradeYAxisLabels(sortedDates) {
    const yAxisGroup = document.getElementById(`${TRADE_CONFIG.chartPrefix}-y-axis-labels`);
    if (!yAxisGroup) return;
    
    yAxisGroup.innerHTML = '';
    
    const minValue = tradeState.yAxisRange.min;
    const maxValue = tradeState.yAxisRange.max;
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

function renderTradeXAxisLabels(sortedDates) {
    const xAxisGroup = document.getElementById(`${TRADE_CONFIG.chartPrefix}-x-axis-labels`);
    if (!xAxisGroup || !sortedDates || sortedDates.length === 0) return;
    
    xAxisGroup.innerHTML = '';
    
    const svg = document.getElementById(`${TRADE_CONFIG.chartPrefix}-chart-svg`);
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
        label.textContent = formatTradeDateLabel(date);
        
        xAxisGroup.appendChild(label);
    });
}

// ============================================================
// CHART INTERACTIVITY
// ============================================================

let tradeCrosshairX = null;
let tradeCrosshairY = null;

function setupTradeChartInteractivity() {
    const prefix = TRADE_CONFIG.chartPrefix;
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
    tradeCrosshairX = crosshairs.crosshairX;
    tradeCrosshairY = crosshairs.crosshairY;
    
    const newContainer = chartContainer.cloneNode(true);
    chartContainer.parentNode.replaceChild(newContainer, chartContainer);
    
    let rafId = null;
    
    newContainer.addEventListener('mousemove', (event) => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
            rafId = null;
            showTradeTooltip(event);
        });
    });
    
    newContainer.addEventListener('mouseleave', () => {
        if (rafId) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
        hideTradeTooltip();
        hideCrosshair(tradeCrosshairX, tradeCrosshairY);
    });
}

function showTradeTooltip(event) {
    const prefix = TRADE_CONFIG.chartPrefix;
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
    Object.values(tradeState.countryData).forEach(data => {
        if (tradeState.showExport) data.export.forEach(item => allDates.add(item.date));
        if (tradeState.showImport) data.import.forEach(item => allDates.add(item.date));
    });
    const sortedDates = Array.from(allDates).sort((a, b) => compareTradeDates(a, b));
    
    if (sortedDates.length === 0) {
        hideCrosshair(tradeCrosshairX, tradeCrosshairY);
        return;
    }
    
    const dateIndex = Math.round(((x / rect.width * width) - chartPadding.left) / chartWidth * (sortedDates.length - 1));
    const dateIndexClamped = Math.max(0, Math.min(sortedDates.length - 1, dateIndex));
    const date = sortedDates[dateIndexClamped];
    
    // Update crosshair X position
    const crosshairXPos = chartPadding.left + (dateIndexClamped / (sortedDates.length - 1 || 1)) * chartWidth;
    if (tradeCrosshairX) {
        tradeCrosshairX.setAttribute('x1', crosshairXPos);
        tradeCrosshairX.setAttribute('x2', crosshairXPos);
        tradeCrosshairX.style.opacity = '1';
    }
    
    // Calculate average Y for crosshair
    let sumY = 0, countY = 0;
    tradeState.activeCountries.forEach(itemCode => {
        const data = tradeState.countryData[itemCode];
        if (data) {
            if (tradeState.showExport) {
                const item = data.export.find(d => d.date === date);
                if (item && Number.isFinite(item.value)) { sumY += item.value; countY++; }
            }
            if (tradeState.showImport) {
                const item = data.import.find(d => d.date === date);
                if (item && Number.isFinite(item.value)) { sumY += item.value; countY++; }
            }
        }
    });
    
    if (countY > 0 && tradeCrosshairY) {
        const avgVal = sumY / countY;
        const { min, max } = tradeState.yAxisRange;
        const normY = (avgVal - min) / (max - min || 1);
        const crosshairYPos = chartPadding.top + (1 - normY) * chartHeight;
        tradeCrosshairY.setAttribute('y1', crosshairYPos);
        tradeCrosshairY.setAttribute('y2', crosshairYPos);
        tradeCrosshairY.style.opacity = '1';
    }
    
    let content = '';
    tradeState.activeCountries.forEach(itemCode => {
        const data = tradeState.countryData[itemCode];
        if (!data) return;
        
        const countryInfo = tradeState.countryMapping[itemCode];
        const countryName = countryInfo ? getTradeCountryNameEnglish(countryInfo.name) : itemCode;
        const color = getTradeCountryColor(itemCode);
        
        let itemContent = `<div class="chart-tooltip-currency"><div class="chart-tooltip-dot" style="background: ${color}"></div><span>${countryName}</span></div>`;
        
        if (tradeState.showExport) {
            const exportItem = data.export.find(d => d.date === date);
            if (exportItem) {
                const formattedVal = exportItem.value.toLocaleString('en-US', { maximumFractionDigits: 0 });
                itemContent += `<div style="margin-left: 20px;">Export: ${formattedVal} <span style="font-size: 80%; opacity: 0.8;">${TRADE_CONFIG.unit}</span></div>`;
            }
        }
        
        if (tradeState.showImport) {
            const importItem = data.import.find(d => d.date === date);
            if (importItem) {
                const formattedVal = importItem.value.toLocaleString('en-US', { maximumFractionDigits: 0 });
                itemContent += `<div style="margin-left: 20px;">Import: ${formattedVal} <span style="font-size: 80%; opacity: 0.8;">${TRADE_CONFIG.unit}</span></div>`;
            }
        }
        
        content += `<div class="chart-tooltip-item">${itemContent}</div>`;
    });
    
    if (!content) {
        hideTradeTooltip();
        return;
    }
    
    const tooltipContent = document.getElementById(`${prefix}-tooltip-content`);
    const tooltipDate = document.getElementById(`${prefix}-tooltip-date`);
    
    if (tooltipContent) tooltipContent.innerHTML = content;
    if (tooltipDate) tooltipDate.textContent = formatTradeDateLabel(date);
    
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

function hideTradeTooltip() {
    const tooltip = document.getElementById(`${TRADE_CONFIG.chartPrefix}-chart-tooltip`);
    if (tooltip) {
        tooltip.classList.remove('visible');
        tooltip.style.visibility = 'hidden';
    }
    hideCrosshair(tradeCrosshairX, tradeCrosshairY);
}

function updateTradeChartHeader() {
    const prefix = TRADE_CONFIG.chartPrefix;
    
    if (tradeState.activeCountries.length === 0) return;
    
    const firstCountryCode = tradeState.activeCountries[0];
    const firstCountryData = tradeState.countryData[firstCountryCode];
    
    if (!firstCountryData) return;
    
    // Use export data for header stats
    const data = tradeState.showExport ? firstCountryData.export : firstCountryData.import;
    if (!data || data.length === 0) return;
    
    const values = data.map(item => item.value);
    const high = Math.max(...values);
    const low = Math.min(...values);
    const average = values.reduce((sum, v) => sum + v, 0) / values.length;
    const current = data[data.length - 1].value;
    
    const countryInfo = tradeState.countryMapping[firstCountryCode];
    const countryName = countryInfo ? getTradeCountryNameEnglish(countryInfo.name) : firstCountryCode;
    
    const titleEl = document.getElementById(`${prefix}-chart-main-title`);
    if (titleEl) titleEl.textContent = `${TRADE_CONFIG.title} - ${countryName}`;
    
    const valueEl = document.getElementById(`${prefix}-chart-main-value`);
    if (valueEl) {
        const formattedValue = current.toLocaleString('en-US', { maximumFractionDigits: 0 });
        valueEl.innerHTML = formattedValue + `<span style="font-size: 50%; opacity: 0.8;"> ${TRADE_CONFIG.unit}</span>`;
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

window.initTrade = initTrade;
window.toggleTradeCountry = toggleTradeCountry;

console.log('📦 Trade module loaded');
