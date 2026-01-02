/**
 * AAL Application - Inflation (CPI) Module
 * 물가(소비자물가지수) 관련 기능 모듈
 * 
 * 담당 패널: #inflation-panel
 * 주요 기능: 국내/국제 물가지수 차트, CPI 비교
 */

// ============================================================
// MODULE MARKER - 이 모듈이 로드되었음을 표시
// ============================================================
window.inflationModuleLoaded = true;

// ============================================================
// 전역 변수 (물가 모듈 전용)
// ============================================================
// Raw CPI index-level series from API: { [itemCode]: [{date, value}] }
let inflationData = {};
// 단일 선택(라디오처럼 1개만 유지)
let activeInflationItems = ['CPI_TOTAL'];
// 표시 메트릭: 지수 레벨(원자료) + 전월비/전기비(변화량/변화율)
let inflationYAxisRange = { min: 0, max: 0 };
let inflationCycle = 'M'; // Current cycle (M, Q)

// International CPI Variables
let activeInflationCountries = []; // 활성화된 국가 목록 (item_code)
let inflationCountryData = {}; // 국가별 데이터 저장 { 'item_code': [{date, value}], ... }
let inflationCountryMapping = {}; // item_code → {code, name} 매핑
let inflationCountryListLoaded = false; // 국가 리스트 로드 여부

// 이벤트 핸들러 저장 (cleanup용)
let inflationMouseMoveHandler = null;
let inflationMouseLeaveHandler = null;

const INFLATION_ITEM_NAMES = {
    'CPI_TOTAL': '총지수',
    'CPI_FRESH': '신선식품',
    'CPI_INDUSTRIAL': '공업제품'
};

const INFLATION_ITEM_COLORS = {
    'CPI_TOTAL': 'var(--c-cpi-total)',
    'CPI_FRESH': 'var(--c-cpi-fresh)',
    'CPI_INDUSTRIAL': 'var(--c-cpi-industrial)'
};

// ============================================================
// DATE HELPERS
// ============================================================

function parseInflationDate(dateStr, cycle) {
    if (!dateStr) return null;
    if (cycle === 'M') {
        // YYYYMM
        if (dateStr.length === 6) {
            const year = parseInt(dateStr.substring(0, 4), 10);
            const month = parseInt(dateStr.substring(4, 6), 10) - 1;
            return new Date(year, month, 1);
        }
    } else if (cycle === 'Q') {
        // YYYYQn
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

function compareInflationDates(a, b, cycle) {
    const da = parseInflationDate(a, cycle);
    const db = parseInflationDate(b, cycle);
    if (!da || !db) return String(a).localeCompare(String(b));
    return da.getTime() - db.getTime();
}

function formatInflationPeriodLabel(dateStr, cycle) {
    if (!dateStr) return '';
    if (cycle === 'M' && dateStr.length === 6) {
        const yy = dateStr.substring(2, 4);
        const mm = dateStr.substring(4, 6);
        return `${yy}.${mm}`;
    }
    if (cycle === 'Q') {
        const match = dateStr.match(/^(\d{4})Q([1-4])$/);
        if (match) {
            const yy = match[1].substring(2, 4);
            const q = match[2];
            return `${yy}Q${q}`;
        }
    }
    return dateStr;
}

function getInflationMetricLabel(cycle) {
    // UI 요구사항: 월별은 전월비, 분기별은 전기비
    return cycle === 'Q' ? '전기비' : '전월비';
}

// ============================================================
// STATISTICS CALCULATION
// ============================================================

function calculateInflationIndexStats(rawSeries, cycle) {
    if (!Array.isArray(rawSeries) || rawSeries.length === 0) {
        return { current: 0, change: 0, changePercent: 0, high: 0, low: 0, average: 0, hasData: false };
    }
    const sorted = [...rawSeries].sort((a, b) => compareInflationDates(a.date, b.date, cycle));
    const values = sorted.map(d => d.value).filter(v => Number.isFinite(v));
    if (values.length === 0) {
        return { current: 0, change: 0, changePercent: 0, high: 0, low: 0, average: 0, hasData: false };
    }
    const current = values[values.length - 1];
    const prev = values.length >= 2 ? values[values.length - 2] : null;
    const change = prev == null ? 0 : (current - prev);
    // 전월비/전기비(%)는 직전 값 대비
    const changePercent = prev == null || prev === 0 ? 0 : (change / prev) * 100;
    const high = Math.max(...values);
    const low = Math.min(...values);
    const average = values.reduce((a, b) => a + b, 0) / values.length;
    return { current, change, changePercent, high, low, average, hasData: true };
}

// ============================================================
// INITIALIZATION
// ============================================================

function initInflation() {
    const startDateInput = document.getElementById('inflation-start-date');
    const endDateInput = document.getElementById('inflation-end-date');
    
    if (startDateInput && endDateInput) {
        const end = new Date();
        const start = new Date();
        // 월별 기본값: 현재 월을 포함해서 과거 12개월
        start.setMonth(end.getMonth() - 11); // 12개월 (현재월 포함)
        start.setDate(1); // 해당 월의 1일로 설정
        
        startDateInput.value = start.toISOString().split('T')[0];
        endDateInput.value = end.toISOString().split('T')[0];
        startDateInput.max = endDateInput.value;
        endDateInput.max = endDateInput.value;
        
        startDateInput.addEventListener('change', () => {
            if (validateInflationDateRange()) {
                fetchInflationData();
            }
        });
        endDateInput.addEventListener('change', () => {
            if (validateInflationDateRange()) {
                fetchInflationData();
            }
        });
    }
    
    // 주기 버튼 이벤트 리스너 추가 (Interest Rates와 동일)
    document.querySelectorAll('.inflation-cycle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.inflation-cycle-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            inflationCycle = this.getAttribute('data-cycle');
            
            const endDateInput = document.getElementById('inflation-end-date');
            const startDateInput = document.getElementById('inflation-start-date');
            
            if (!endDateInput || !startDateInput) {
                fetchInflationData();
                return;
            }
            
            // 월별(M) 선택 시 현재 월을 포함해서 과거 12개월
            if (inflationCycle === 'M') {
                const end = new Date();
                const start = new Date();
                start.setMonth(end.getMonth() - 11); // 12개월 (현재월 포함)
                start.setDate(1); // 해당 월의 1일로 설정
                
                startDateInput.value = start.toISOString().split('T')[0];
                endDateInput.value = end.toISOString().split('T')[0];
                startDateInput.max = endDateInput.value;
                endDateInput.max = endDateInput.value;
                
                // date input을 다시 표시
                startDateInput.type = 'date';
                endDateInput.type = 'date';
            }
            // 분기별(Q) 선택 시 현재일 기준으로 2개년 Period 자동 설정 (총 8개 분기)
            else if (inflationCycle === 'Q') {
                const end = new Date();
                const start = new Date();
                start.setFullYear(end.getFullYear() - 2); // 2개년 (현재년 포함)
                
                startDateInput.type = 'date';
                endDateInput.type = 'date';
                
                const startDateStr = start.toISOString().split('T')[0];
                const endDateStr = end.toISOString().split('T')[0];
                
                startDateInput.value = startDateStr;
                endDateInput.value = endDateStr;
                startDateInput.max = endDateStr;
                endDateInput.max = endDateStr;
            }
            
            fetchInflationData();
        });
    });
    
    fetchInflationData();
    // 국가 리스트 로드
    fetchInflationCountryList().then(() => {
        initInflationCountryChips();
    }).catch(err => {
        console.error('Failed to load inflation country list:', err);
    });
    window.inflationDataLoaded = true;
}

// ============================================================
// DATE VALIDATION
// ============================================================

function validateInflationDateRange() {
    const startDateInput = document.getElementById('inflation-start-date');
    const endDateInput = document.getElementById('inflation-end-date');
    
    if (!startDateInput || !endDateInput) return false;
    
    // 날짜 검증
    const startDate = new Date(startDateInput.value);
    const endDate = new Date(endDateInput.value);
    
    if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
        alert('유효한 날짜를 입력하세요.');
        return false;
    }
    
    if (startDate > endDate) {
        alert('시작일은 종료일보다 앞서야 합니다.');
        return false;
    }
    
    return true;
}

// ============================================================
// INTERNATIONAL CPI FUNCTIONS
// ============================================================

async function fetchInflationCountryList() {
    if (inflationCountryListLoaded && Object.keys(inflationCountryMapping).length > 0) {
        return inflationCountryMapping;
    }
    
    try {
        const url = `${API_BASE}/market/categories?category=cpi-international`;
        const response = await fetch(url);
        
        if (response.ok) {
            const data = await response.json();
            if (data.items && Object.keys(data.items).length > 0) {
                inflationCountryMapping = data.items;
                inflationCountryListLoaded = true;
                return inflationCountryMapping;
            }
        }
        
        throw new Error('Failed to fetch country list from categories endpoint');
        
    } catch (err) {
        console.error('Failed to fetch inflation country list:', err);
        throw err;
    }
}

// Country info mapping (Korean name → English name)
const inflationCountryInfoMap = [
    { keywords: ['오스트리아', 'aut', 'austria'], englishName: 'Austria' },
    { keywords: ['호주', 'aus', 'australia'], englishName: 'Australia' },
    { keywords: ['벨기에', 'bel', 'belgium'], englishName: 'Belgium' },
    { keywords: ['브라질', 'bra', 'brazil'], englishName: 'Brazil' },
    { keywords: ['캐나다', 'can', 'canada'], englishName: 'Canada' },
    { keywords: ['스위스', 'che', 'switzerland'], englishName: 'Switzerland' },
    { keywords: ['칠레', 'chl', 'chile'], englishName: 'Chile' },
    { keywords: ['중국', 'chn', 'china'], englishName: 'China' },
    { keywords: ['체코', 'cze', 'czech'], englishName: 'Czech Republic' },
    { keywords: ['독일', 'deu', 'germany'], englishName: 'Germany' },
    { keywords: ['덴마크', 'dnk', 'denmark'], englishName: 'Denmark' },
    { keywords: ['에스토니아', 'est', 'estonia'], englishName: 'Estonia' },
    { keywords: ['스페인', 'esp', 'spain'], englishName: 'Spain' },
    { keywords: ['핀란드', 'fin', 'finland'], englishName: 'Finland' },
    { keywords: ['프랑스', 'fra', 'france'], englishName: 'France' },
    { keywords: ['영국', 'gbr', 'uk', 'united kingdom'], englishName: 'UK' },
    { keywords: ['그리스', 'grc', 'greece'], englishName: 'Greece' },
    { keywords: ['헝가리', 'hun', 'hungary'], englishName: 'Hungary' },
    { keywords: ['인도네시아', 'idn', 'indonesia'], englishName: 'Indonesia' },
    { keywords: ['아일랜드', 'irl', 'ireland'], englishName: 'Ireland' },
    { keywords: ['이스라엘', 'isr', 'israel'], englishName: 'Israel' },
    { keywords: ['인도', 'ind', 'india'], englishName: 'India' },
    { keywords: ['아이슬란드', 'isl', 'iceland'], englishName: 'Iceland' },
    { keywords: ['이탈리아', 'ita', 'italy'], englishName: 'Italy' },
    { keywords: ['일본', 'jpn', 'japan'], englishName: 'Japan' },
    { keywords: ['한국', 'kor', 'korea'], englishName: 'Korea' },
    { keywords: ['룩셈부르크', 'lux', 'luxembourg'], englishName: 'Luxembourg' },
    { keywords: ['라트비아', 'lva', 'latvia'], englishName: 'Latvia' },
    { keywords: ['멕시코', 'mex', 'mexico'], englishName: 'Mexico' },
    { keywords: ['네덜란드', 'nld', 'netherlands', 'holland'], englishName: 'Netherlands' },
    { keywords: ['노르웨이', 'nor', 'norway'], englishName: 'Norway' },
    { keywords: ['뉴질랜드', 'nzl', 'zealand'], englishName: 'New Zealand' },
    { keywords: ['폴란드', 'pol', 'poland'], englishName: 'Poland' },
    { keywords: ['포르투갈', 'prt', 'portugal'], englishName: 'Portugal' },
    { keywords: ['러시아', 'rus', 'russia'], englishName: 'Russia' },
    { keywords: ['스웨덴', 'swe', 'sweden'], englishName: 'Sweden' },
    { keywords: ['슬로베니아', 'svn', 'slovenia'], englishName: 'Slovenia' },
    { keywords: ['슬로바키아', 'svk', 'slovakia'], englishName: 'Slovakia' },
    { keywords: ['튀르키예', 'tur', 'turkey'], englishName: 'Turkey' },
    { keywords: ['미국', 'usa', 'us ', 'united states'], englishName: 'USA' },
    { keywords: ['유로', 'eur', 'eurozone', 'euro area'], englishName: 'Eurozone' },
    { keywords: ['남아프리카', 'zaf', 'south africa'], englishName: 'South Africa' }
];

// itemCode에서 국가 코드 추출 (예: "AUS_CPI" -> "aus")
function extractInflationCountryCode(itemCode) {
    if (!itemCode) return null;
    const code = itemCode.toLowerCase();
    // 패턴: XXX_CPI, XXX_RATE 등에서 국가코드 추출
    const match = code.match(/^([a-z]{2,3})_/);
    if (match) return match[1];
    // 국가코드가 직접 포함된 경우
    const countryPattern = code.match(/^([a-z]{2,3})$/);
    if (countryPattern) return countryPattern[1];
    return null;
}

function getInflationCountryNameEnglish(koreanName, itemCode = null) {
    if (!koreanName && !itemCode) return koreanName;
    
    // 1. itemCode에서 국가 코드 추출하여 매칭 시도
    const countryCode = extractInflationCountryCode(itemCode);
    if (countryCode) {
        for (const info of inflationCountryInfoMap) {
            if (info.keywords.some(keyword => keyword.toLowerCase() === countryCode)) {
                return info.englishName;
            }
        }
    }
    
    // 2. 이름 기반 매칭
    const name = (koreanName || '').toLowerCase();
    for (const info of inflationCountryInfoMap) {
        if (info.keywords.some(keyword => name.includes(keyword.toLowerCase()))) {
            return info.englishName;
        }
    }
    return koreanName;
}

function initInflationCountryChips() {
    const chipsContainer = document.getElementById('inflation-country-chips');
    if (!chipsContainer) return;
    
    chipsContainer.innerHTML = '';
    
    const itemCodes = Object.keys(inflationCountryMapping);
    if (itemCodes.length === 0) {
        chipsContainer.innerHTML = '<span style="color: var(--text-sub); font-size: 0.8rem;">Loading country list...</span>';
        return;
    }
    
    // Set Korea as default if no countries selected yet
    if (activeInflationCountries.length === 0) {
        const korCode = itemCodes.find(code => {
            const name = inflationCountryMapping[code].name;
            return name.includes('한국') || name.includes('KOR') || code.includes('KOR');
        });
        if (korCode) {
            activeInflationCountries.push(korCode);
        }
    }
    
    itemCodes.forEach(itemCode => {
        const countryInfo = inflationCountryMapping[itemCode];
        
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.setAttribute('data-item-code', itemCode);
        chip.setAttribute('title', countryInfo.name);
        
        const isActive = activeInflationCountries.includes(itemCode);
        if (isActive) {
            chip.classList.add('active');
        }
        
        // 국가별 그래프 색상 가져오기
        const countryColor = getInflationCountryColor(itemCode);
        
        const chipDot = document.createElement('div');
        chipDot.className = 'chip-dot';
        // active 상태일 때만 색상 적용
        if (isActive) {
            chipDot.style.background = countryColor;
            chip.style.borderColor = countryColor;
            chip.style.color = countryColor;
            // CSS 변수를 실제 색상으로 변환하여 배경색 설정
            const tempEl = document.createElement('div');
            tempEl.style.color = countryColor;
            document.body.appendChild(tempEl);
            const computedColor = window.getComputedStyle(tempEl).color;
            document.body.removeChild(tempEl);
            // RGB 값을 추출하여 투명도 적용
            const rgbMatch = computedColor.match(/\d+/g);
            if (rgbMatch && rgbMatch.length >= 3) {
                chip.style.background = `rgba(${rgbMatch[0]}, ${rgbMatch[1]}, ${rgbMatch[2]}, 0.2)`;
            }
        } else {
            chipDot.style.background = 'currentColor';
        }
        
        chip.appendChild(chipDot);
        // Display country name in English
        const englishName = getInflationCountryNameEnglish(countryInfo.name, itemCode);
        chip.appendChild(document.createTextNode(englishName));
        
        chip.addEventListener('click', () => toggleInflationCountry(itemCode));
        
        chipsContainer.appendChild(chip);
    });
}

function getInflationCountryColor(itemCode) {
    // 국가별 색상 매핑 (exchange rate나 interest rate와 유사한 색상 사용)
    const colorMap = {
        '0000001': 'var(--c-usd)', // 미국
        '0000002': 'var(--c-jpy)', // 일본
        '0000003': 'var(--c-eur)', // 유로
        '0000004': 'var(--c-gbp)', // 영국
        '0000005': 'var(--c-cny)', // 중국
    };
    // 기본 색상 팔레트
    const defaultColors = [
        'var(--c-usd)', 'var(--c-jpy)', 'var(--c-eur)', 'var(--c-gbp)', 'var(--c-cny)',
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE'
    ];
    return colorMap[itemCode] || defaultColors[Object.keys(inflationCountryMapping).indexOf(itemCode) % defaultColors.length];
}

function toggleInflationCountry(itemCode) {
    const index = activeInflationCountries.indexOf(itemCode);
    
    // 토글: 있으면 제거, 없으면 추가
    if (index === -1) {
        activeInflationCountries.push(itemCode);
    } else {
        activeInflationCountries.splice(index, 1);
    }
    
    // UI 업데이트
    const chip = document.querySelector(`#inflation-country-chips [data-item-code="${itemCode}"]`);
    if (chip) {
        const chipDot = chip.querySelector('.chip-dot');
        const isActive = activeInflationCountries.includes(itemCode);
        
        if (isActive) {
            chip.classList.add('active');
            const countryColor = getInflationCountryColor(itemCode);
            if (chipDot) {
                chipDot.style.background = countryColor;
            }
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
            if (chipDot) {
                chipDot.style.background = 'currentColor';
            }
            chip.style.borderColor = '';
            chip.style.color = '';
            chip.style.background = '';
        }
    }
    
    // 데이터 재조회
    if (validateInflationDateRange()) {
        fetchInflationData();
    }
}

function toggleInflationItem(itemCode) {
    // 단일 선택(라디오): 항상 1개만 active 유지
    const panel = document.getElementById('inflation-panel');
    if (!panel) return;
    const chip = panel.querySelector(`.chip[data-item="${itemCode}"]`);
    if (!chip) return;
    
    // 모든 칩 비활성화
    panel.querySelectorAll('.chip[data-item]').forEach(btn => btn.classList.remove('active'));
    // 선택 칩 활성화
        chip.classList.add('active');
    activeInflationItems = [itemCode];
    
    fetchInflationData();
}

// ============================================================
// DATA FETCHING
// ============================================================

async function fetchInflationData() {
    if (!validateInflationDateRange()) return;
    
    const startDateInput = document.getElementById('inflation-start-date');
    const endDateInput = document.getElementById('inflation-end-date');
    
    const selectedItem = activeInflationItems && activeInflationItems.length > 0 ? activeInflationItems[0] : null;
    if (!startDateInput || !endDateInput || !selectedItem) {
        console.warn('Inflation: Missing inputs or no active items');
        return;
    }
    
    let startDate = formatDateForAPI(startDateInput.value);
    let endDate = formatDateForAPI(endDateInput.value);
    
    // API 호출 시 cycle 파라미터를 동적으로 사용
    const apiCycle = inflationCycle;
    
    console.log('Fetching inflation data:', {
        item: selectedItem,
        startDate,
        endDate,
        cycle: inflationCycle,
        apiCycle: apiCycle,
        countries: activeInflationCountries
    });
    
    const chartContainer = document.getElementById('inflation-chart-container');
    if (chartContainer) {
        chartContainer.style.opacity = '0.5';
    }
    
    try {
        // 1. 한국 데이터 조회 (기존 로직)
        const koreaUrl = `${API_BASE}/market/indices?type=inflation&itemCode=${selectedItem}&startDate=${startDate}&endDate=${endDate}&cycle=${apiCycle}`;
        console.log(`Fetching Korean inflation data from: ${koreaUrl}`);
        const koreaRes = await fetch(koreaUrl);
        if (!koreaRes.ok) {
            throw new Error(`HTTP ${koreaRes.status}: ${koreaRes.statusText}`);
        }
        const koreaData = await koreaRes.json();
        if (koreaData.error) {
            throw new Error(String(koreaData.error));
        }
        if (!koreaData.StatisticSearch || !Array.isArray(koreaData.StatisticSearch.row)) {
            throw new Error('Invalid API response (missing StatisticSearch.row)');
        }

        const koreaProcessed = koreaData.StatisticSearch.row.map(row => ({
            date: row.TIME,
            value: parseFloat(row.DATA_VALUE)
        })).filter(item => Number.isFinite(item.value) && item.value > 0);

        inflationData = { [selectedItem]: koreaProcessed };
        
        // 2. 선택된 국가들의 데이터 조회
        if (activeInflationCountries.length > 0) {
            const countryFetchPromises = activeInflationCountries.map(async (itemCode) => {
                const url = `${API_BASE}/market/indices?type=cpi-international&itemCode=${itemCode}&startDate=${startDate}&endDate=${endDate}&cycle=${apiCycle}`;
                try {
                    const res = await fetch(url);
                    if (!res.ok) {
                        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                    }
                    const data = await res.json();
                    if (data.error) {
                        throw new Error(String(data.error));
                    }
                    if (!data.StatisticSearch || !Array.isArray(data.StatisticSearch.row)) {
                        throw new Error('Invalid API response (missing StatisticSearch.row)');
                    }
                    
                    const processed = data.StatisticSearch.row.map(row => ({
                        date: row.TIME,
                        value: parseFloat(row.DATA_VALUE)
                    })).filter(item => Number.isFinite(item.value) && item.value > 0);
                    
                    return { itemCode, data: processed };
                } catch (err) {
                    console.error(`Failed to fetch CPI data for country ${itemCode}:`, err);
                    return { itemCode, data: [] };
                }
            });
            
            const countryResults = await Promise.all(countryFetchPromises);
            countryResults.forEach(({ itemCode, data }) => {
                inflationCountryData[itemCode] = data;
            });
        } else {
            inflationCountryData = {};
        }

        // Update chart (지수 레벨 기준 렌더링)
        updateInflationChart();
        
        // 헤더/통계는 첫 번째 선택된 국가 데이터 기준
        if (activeInflationCountries.length > 0) {
            const firstCountry = activeInflationCountries[0];
            const firstCountryData = inflationCountryData[firstCountry] || [];
            const stats = calculateInflationIndexStats(firstCountryData, inflationCycle);
            if (stats && stats.hasData) {
                updateInflationChartHeader(stats, selectedItem, firstCountry);
            } else {
                updateInflationChartHeader({ current: 0, change: 0, changePercent: 0, high: 0, low: 0, average: 0, hasData: false }, selectedItem);
            }
        } else {
            updateInflationChartHeader({ current: 0, change: 0, changePercent: 0, high: 0, low: 0, average: 0, hasData: false }, selectedItem);
        }
        
    } catch (err) {
        console.error('Failed to fetch inflation data:', err);
        alert('물가 데이터 조회 중 오류가 발생했습니다: ' + err.message);
    } finally {
        if (chartContainer) {
            chartContainer.style.opacity = '1';
        }
    }
}

// ============================================================
// CHART RENDERING
// ============================================================

function updateInflationChart() {
    const svg = document.getElementById('inflation-chart-svg');
    const pointsGroup = document.getElementById('inflation-data-points');
    const barGroup = document.getElementById('inflation-bar-chart');
    
    if (!svg || !pointsGroup) return;
    
    // 한국 항목 path 정리
    const allItems = ['CPI_TOTAL', 'CPI_FRESH', 'CPI_INDUSTRIAL'];
    allItems.forEach(itemCode => {
        const path = document.getElementById(`path-inflation-${itemCode}`);
        if (path) {
            path.setAttribute('d', '');
            path.classList.remove('visible');
        }
    });
    
    // 국가 path 정리
    Object.keys(inflationCountryMapping).forEach(itemCode => {
        let path = document.getElementById(`path-inflation-country-${itemCode}`);
        if (path) {
            path.setAttribute('d', '');
            path.classList.remove('visible');
        }
    });
    
    if (barGroup) barGroup.innerHTML = '';
    if (pointsGroup) pointsGroup.innerHTML = '';

    const selectedItem = activeInflationItems && activeInflationItems.length > 0 ? activeInflationItems[0] : null;
    
    // Only use country data from activeInflationCountries (no separate Korea domestic data)
    const allData = [];
    activeInflationCountries.forEach(itemCode => {
        const countryData = inflationCountryData[itemCode] || [];
        allData.push(...countryData);
    });
    
    // 공통 날짜 목록 생성
    const allDates = new Set();
    activeInflationCountries.forEach(itemCode => {
        const countryData = inflationCountryData[itemCode] || [];
        countryData.forEach(item => allDates.add(item.date));
    });
    const sortedDates = Array.from(allDates).sort((a, b) => compareInflationDates(a, b, inflationCycle));
    
    // Y축 범위 계산 (모든 데이터 기반)
    const allValues = allData.map(d => d.value).filter(v => Number.isFinite(v) && v > 0);
    if (allValues.length > 0) {
        const minValue = Math.min(...allValues);
        const maxValue = Math.max(...allValues);
        const range = maxValue - minValue || 1;
        const paddingPercent = 0.05;
        inflationYAxisRange = {
            min: Math.max(0, minValue - range * paddingPercent),
            max: maxValue + range * paddingPercent
        };
    } else {
        inflationYAxisRange = { min: 0, max: 0 };
    }
    
    // Y축 라벨 렌더링
    renderInflationYAxisLabels(allData);
    
    if (sortedDates.length === 0) {
        renderInflationXAxisLabels([], true);
        setupInflationChartInteractivity();
        return;
    }
    
    // 국가 데이터 렌더링 (Only render data for countries in activeInflationCountries)
    activeInflationCountries.forEach(itemCode => {
        const countryData = inflationCountryData[itemCode] || [];
        if (countryData.length === 0) return;
        
        let path = document.getElementById(`path-inflation-country-${itemCode}`);
        if (!path) {
            // path 요소 생성
            path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.id = `path-inflation-country-${itemCode}`;
            path.classList.add('chart-path');
            path.setAttribute('stroke', getInflationCountryColor(itemCode));
            path.setAttribute('stroke-width', '2.5');
            // Solid lines instead of dotted (removed stroke-dasharray)
            path.setAttribute('fill', 'none');
            svg.insertBefore(path, pointsGroup);
        }
        
        // 데이터를 공통 날짜 기준으로 정렬
        const sortedData = sortedDates.map(date => {
            const found = countryData.find(item => item.date === date);
            return found || { date, value: null };
        }).filter(item => item.value !== null);
        
        if (sortedData.length > 0) {
            const pathData = generateInflationSVGPath(sortedData);
            path.setAttribute('d', pathData);
            path.classList.add('visible');
        }
        
        // 국가 데이터 포인트 렌더링
        renderInflationCountryDataPoints(countryData, itemCode);
    });
    
    // X축 라벨 렌더링 (공통 날짜 사용)
    renderInflationXAxisLabels(sortedDates, sortedDates.length < 2);
    setupInflationChartInteractivity();
}

function renderInflationCountryDataPoints(data, itemCode) {
    // Data points (circles) are removed as per user request - showing only lines
    // No circles are rendered for country data
}

function generateInflationSVGPath(data) {
    if (!data || data.length === 0) return '';
    
    const svg = document.getElementById('inflation-chart-svg');
    if (!svg) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const minValue = inflationYAxisRange.min;
    const maxValue = inflationYAxisRange.max;
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

function renderInflationYAxisLabels(displaySeries) {
    const g = document.getElementById('inflation-y-axis-labels');
    if (!g) return;
    
    g.innerHTML = '';
    
    const values = (Array.isArray(displaySeries) ? displaySeries : [])
        .map(d => d.value)
        .filter(v => Number.isFinite(v));
    if (values.length === 0) return;

    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const range = maxValue - minValue || 1;
    
    // Dynamic padding
    const paddingPercent = range < 10 ? 0.01 : (range < 50 ? 0.005 : 0.003);
    const paddedMin = minValue - range * paddingPercent;
    const paddedMax = maxValue + range * paddingPercent;
    
    inflationYAxisRange = { min: paddedMin, max: paddedMax };
    
    const svg = document.getElementById('inflation-chart-svg');
    if (!svg) return;
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartHeight = height - padding.top - padding.bottom;
    
    const steps = 5;
    for (let i = 0; i <= steps; i++) {
        const value = paddedMax - (i / steps) * (paddedMax - paddedMin);
        const y = padding.top + (i / steps) * chartHeight;
        
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', String(padding.left - 10));
        t.setAttribute('y', String(y));
        t.setAttribute('text-anchor', 'end');
        t.setAttribute('dominant-baseline', 'middle');
        t.setAttribute('class', 'chart-yaxis-label');
        t.textContent = value.toFixed(2);
        g.appendChild(t);
    }
}

function renderInflationXAxisLabels(displaySeries, isSingleUnit = false) {
    const g = document.getElementById('inflation-x-axis-labels');
    if (!g) return;
    
    g.innerHTML = '';
    
    const data = Array.isArray(displaySeries) ? displaySeries : [];
    if (data.length === 0) return;
    const svg = document.getElementById('inflation-chart-svg');
    if (!svg) return;
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const y = height - padding.bottom + 20;
    
    // 1개 단위: 중앙에 라벨 표시 (표준 준수)
    if (isSingleUnit && data.length === 1) {
        const centerX = padding.left + chartWidth / 2;
        const dataPoint = data[0];
        const label = formatInflationPeriodLabel(dataPoint.date || dataPoint, inflationCycle);
        
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', String(centerX));
        t.setAttribute('y', String(y));
        t.setAttribute('text-anchor', 'middle');
        t.setAttribute('dominant-baseline', 'middle');
        t.setAttribute('class', 'chart-xaxis-label');
        t.textContent = label;
        g.appendChild(t);
        return;
    }
    
    // M: 2개마다, Q: 전부. 첫/끝은 항상 포함
    const labelIndices = [];
    if (inflationCycle === 'M') {
        for (let i = 0; i < data.length; i += 2) labelIndices.push(i);
        } else {
        for (let i = 0; i < data.length; i++) labelIndices.push(i);
    }
    if (labelIndices.length === 0 || labelIndices[0] !== 0) labelIndices.unshift(0);
    if (labelIndices[labelIndices.length - 1] !== data.length - 1) labelIndices.push(data.length - 1);
    const unique = [...new Set(labelIndices)].sort((a, b) => a - b);

    unique.forEach(index => {
        const point = data[index];
        const x = padding.left + (index / (data.length - 1 || 1)) * chartWidth;
        const label = formatInflationPeriodLabel(point.date || point, inflationCycle);
            const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            t.setAttribute('x', String(x));
            t.setAttribute('y', String(y));
            t.setAttribute('text-anchor', 'middle');
            t.setAttribute('dominant-baseline', 'middle');
            t.setAttribute('class', 'chart-xaxis-label');
            t.textContent = label;
            g.appendChild(t);
    });
}

function renderInflationBarChart(displaySeries, itemCode) {
    const barGroup = document.getElementById('inflation-bar-chart');
    if (!barGroup) return;
    
    barGroup.innerHTML = '';

    const data = Array.isArray(displaySeries) ? displaySeries : [];
    if (!itemCode || data.length === 0) return;
    
    const svg = document.getElementById('inflation-chart-svg');
    if (!svg) return;
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
        const dataPoint = data[0];
        const minValue = inflationYAxisRange.min;
        const maxValue = inflationYAxisRange.max;
        const valueRange = maxValue - minValue || 1;
        const normalizedValue = (dataPoint.value - minValue) / valueRange;
        const barHeight = normalizedValue * chartHeight;
        const barY = padding.top + (1 - normalizedValue) * chartHeight;
        
    const barWidth = Math.min(60, chartWidth * 0.3);
        const centerX = padding.left + chartWidth / 2;
    const barX = centerX - barWidth / 2;

    const color = INFLATION_ITEM_COLORS[itemCode] || 'var(--accent-color)';
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', String(barX));
        rect.setAttribute('y', String(barY));
        rect.setAttribute('width', String(barWidth));
        rect.setAttribute('height', String(barHeight));
        rect.setAttribute('fill', color);
        rect.setAttribute('rx', '4');
        barGroup.appendChild(rect);
}

function renderInflationDataPoints(displaySeries, itemCode) {
    // Data points (circles) are removed as per user request - showing only lines
    const g = document.getElementById('inflation-data-points');
    if (g) {
        g.innerHTML = '';
    }
}

// ============================================================
// CHART INTERACTIVITY
// ============================================================

let inflationCrosshairX = null;
let inflationCrosshairY = null;

function setupInflationChartInteractivity() {
    const chartContainer = document.getElementById('inflation-chart-container');
    const svg = document.getElementById('inflation-chart-svg');
    
    if (!chartContainer || !svg) return;
    
    // Ensure tooltip is in body
    const tooltip = document.getElementById('inflation-chart-tooltip');
    if (tooltip && tooltip.parentElement !== document.body) {
        document.body.appendChild(tooltip);
    }
    
    // Create crosshair elements
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const crosshairs = createCrosshairElements(svg, padding, chartWidth, chartHeight);
    inflationCrosshairX = crosshairs.crosshairX;
    inflationCrosshairY = crosshairs.crosshairY;
    
    // Remove existing listeners if they exist
    if (inflationMouseMoveHandler) {
        chartContainer.removeEventListener('mousemove', inflationMouseMoveHandler);
    }
    if (inflationMouseLeaveHandler) {
        chartContainer.removeEventListener('mouseleave', inflationMouseLeaveHandler);
    }
    
    // Add new listeners
    let rafId = null;
    
    inflationMouseMoveHandler = (e) => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
            rafId = null;
            
            const firstItem = activeInflationItems[0];
            const raw = firstItem ? (inflationData[firstItem] || []) : [];
            const data = [...raw].sort((a, b) => compareInflationDates(a.date, b.date, inflationCycle));
            if (!firstItem || data.length === 0) {
                hideInflationTooltip();
                hideCrosshair(inflationCrosshairX, inflationCrosshairY);
                return;
            }
            
            const rect = chartContainer.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const svgX = (x / rect.width) * 1200; // viewBox width
            
            const svgPadding = { left: 40, right: 20, top: 20, bottom: 30 };
            const svgChartWidth = 1200 - svgPadding.left - svgPadding.right;
            const svgChartHeight = 400 - svgPadding.top - svgPadding.bottom;
            const dataIndex = Math.round(((svgX - svgPadding.left) / svgChartWidth) * (data.length - 1));
            
            if (dataIndex >= 0 && dataIndex < data.length) {
                const dataPoint = data[dataIndex];
                const prevPoint = dataIndex > 0 ? data[dataIndex - 1] : null;
                
                // Update crosshair X position
                const crosshairXPos = svgPadding.left + (dataIndex / (data.length - 1 || 1)) * svgChartWidth;
                if (inflationCrosshairX) {
                    inflationCrosshairX.setAttribute('x1', crosshairXPos);
                    inflationCrosshairX.setAttribute('x2', crosshairXPos);
                    inflationCrosshairX.style.opacity = '1';
                }
                
                // Update crosshair Y position
                if (dataPoint && Number.isFinite(dataPoint.value) && inflationCrosshairY) {
                    const { min, max } = inflationYAxisRange;
                    const normY = (dataPoint.value - min) / (max - min || 1);
                    const crosshairYPos = svgPadding.top + (1 - normY) * svgChartHeight;
                    inflationCrosshairY.setAttribute('y1', crosshairYPos);
                    inflationCrosshairY.setAttribute('y2', crosshairYPos);
                    inflationCrosshairY.style.opacity = '1';
                }
                
                // 활성화된 국가들의 데이터도 찾기
                const countryDataPoints = {};
                activeInflationCountries.forEach(itemCode => {
                    const countryData = inflationCountryData[itemCode] || [];
                    const sortedCountryData = [...countryData].sort((a, b) => compareInflationDates(a.date, b.date, inflationCycle));
                    if (sortedCountryData.length > 0) {
                        // 가장 가까운 날짜 찾기
                        let closestPoint = sortedCountryData.find(d => d.date === dataPoint.date);
                        if (!closestPoint && sortedCountryData.length > 0) {
                            // 정확한 매칭이 없으면 가장 가까운 날짜 찾기
                            const dateIndex = sortedCountryData.findIndex(d => compareInflationDates(d.date, dataPoint.date, inflationCycle) >= 0);
                            if (dateIndex >= 0) {
                                closestPoint = sortedCountryData[dateIndex];
                            } else {
                                closestPoint = sortedCountryData[sortedCountryData.length - 1];
                            }
                        }
                        if (closestPoint) {
                            countryDataPoints[itemCode] = closestPoint;
                        }
                    }
                });
                
                showInflationTooltip(e, dataPoint, firstItem, prevPoint, countryDataPoints);
            } else {
                hideInflationTooltip();
                hideCrosshair(inflationCrosshairX, inflationCrosshairY);
            }
        });
    };
    
    inflationMouseLeaveHandler = () => {
        hideInflationTooltip();
        hideCrosshair(inflationCrosshairX, inflationCrosshairY);
    };
    
    chartContainer.addEventListener('mousemove', inflationMouseMoveHandler);
    chartContainer.addEventListener('mouseleave', inflationMouseLeaveHandler);
}

function showInflationTooltip(event, dataPoint, itemCode, prevPoint = null, countryDataPoints = {}) {
    const tooltip = document.getElementById('inflation-chart-tooltip');
    const tooltipDate = document.getElementById('inflation-tooltip-date');
    const tooltipContent = document.getElementById('inflation-tooltip-content');
    
    if (!tooltip || !tooltipDate || !tooltipContent) return;
    
    const formattedDate = formatInflationPeriodLabel(dataPoint.date, inflationCycle);
    tooltipDate.textContent = formattedDate;
    
    // Show value
    const itemNames = INFLATION_ITEM_NAMES;
    const colorMap = INFLATION_ITEM_COLORS;
    const valueText = Number(dataPoint.value).toLocaleString('ko-KR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    // "전기비" row removed as per user request
    
    // 활성화된 국가들의 지수 표시 (in English)
    let countryRows = '';
    Object.keys(countryDataPoints).forEach(itemCode => {
        const countryPoint = countryDataPoints[itemCode];
        const countryInfo = inflationCountryMapping[itemCode];
        const countryName = countryInfo ? getInflationCountryNameEnglish(countryInfo.name, itemCode) : itemCode;
        const countryColor = getInflationCountryColor(itemCode);
        
        // CSS 변수를 실제 색상으로 변환
        const tempEl = document.createElement('div');
        tempEl.style.color = countryColor;
        document.body.appendChild(tempEl);
        const computedColor = window.getComputedStyle(tempEl).color;
        document.body.removeChild(tempEl);
        
        const countryValueText = Number(countryPoint.value).toLocaleString('ko-KR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        countryRows += `
            <div class="chart-tooltip-item">
                <div class="chart-tooltip-currency">
                    <div class="chart-tooltip-dot" style="background: ${computedColor};"></div>
                    <span>${countryName}</span>
                </div>
                <span class="chart-tooltip-value">${countryValueText}</span>
            </div>
        `;
    });
    
    // Only show country rows (총지수 row removed as per user request)
    tooltipContent.innerHTML = countryRows || `
        <div class="chart-tooltip-item">
            <span class="chart-tooltip-value">${valueText}</span>
        </div>
    `;
    
    // Position tooltip
    tooltip.style.left = (event.clientX + 10) + 'px';
    tooltip.style.top = (event.clientY + 10) + 'px';
    tooltip.style.visibility = 'visible';
    tooltip.classList.add('visible');
}

function hideInflationTooltip() {
    const tooltip = document.getElementById('inflation-chart-tooltip');
    if (tooltip) {
        tooltip.classList.remove('visible');
        tooltip.style.visibility = 'hidden';
    }
    hideCrosshair(inflationCrosshairX, inflationCrosshairY);
}

// ============================================================
// CHART HEADER UPDATE
// ============================================================

function updateInflationChartHeader(stats, itemCode, countryCode = null) {
    const titleEl = document.getElementById('inflation-chart-main-title');
    const valueEl = document.getElementById('inflation-chart-main-value');
    const changeValueEl = document.getElementById('inflation-change-value');
    const changePercentEl = document.getElementById('inflation-change-percent');
    const statHighEl = document.getElementById('inflation-stat-high');
    const statLowEl = document.getElementById('inflation-stat-low');
    const statAverageEl = document.getElementById('inflation-stat-average');
    
    // Show country name in title if available
    let titleText = 'Consumer Price Index';
    if (countryCode && inflationCountryMapping[countryCode]) {
        const countryName = getInflationCountryNameEnglish(inflationCountryMapping[countryCode].name, countryCode);
        titleText = `${countryName} CPI`;
    }
    if (titleEl) titleEl.textContent = titleText;

    const has = stats && stats.hasData;
    if (!has) {
        if (valueEl) valueEl.textContent = '-';
        if (changeValueEl) changeValueEl.textContent = '-';
        if (changePercentEl) changePercentEl.textContent = '(-)';
        if (changeValueEl) changeValueEl.className = 'change-value';
        if (changePercentEl) changePercentEl.className = 'change-percent';
        if (statHighEl) statHighEl.textContent = '-';
        if (statLowEl) statLowEl.textContent = '-';
        if (statAverageEl) statAverageEl.textContent = '-';
        return;
    }

    const fmtIndex = (v) => Number(v).toLocaleString('ko-KR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (valueEl) valueEl.textContent = fmtIndex(stats.current);

    const change = Number(stats.change);
    const changePct = Number(stats.changePercent);
    const isUp = change > 0;
    const isDown = change < 0;

    if (changeValueEl && changePercentEl) {
        // 예시: -10 (-10%)
        changeValueEl.textContent = `${isUp ? '+' : ''}${change.toFixed(2)}`;
        changePercentEl.textContent = `(${isUp ? '+' : ''}${changePct.toFixed(2)}%)`;
        changeValueEl.className = `change-value ${isUp ? 'up' : (isDown ? 'down' : '')}`;
        changePercentEl.className = `change-percent ${isUp ? 'up' : (isDown ? 'down' : '')}`;
    }

    if (statHighEl) statHighEl.textContent = fmtIndex(stats.high);
    if (statLowEl) statLowEl.textContent = fmtIndex(stats.low);
    if (statAverageEl) statAverageEl.textContent = fmtIndex(stats.average);
}

// ============================================================
// GLOBAL EXPORTS
// ============================================================

// 전역 함수로 노출
window.initInflation = initInflation;
window.toggleInflationItem = toggleInflationItem;
window.toggleInflationCountry = toggleInflationCountry;
window.fetchInflationData = fetchInflationData;
window.updateInflationChart = updateInflationChart;

console.log('📊 Inflation module loaded');
