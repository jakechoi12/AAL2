/**
 * AAL Application - Exchange Rate KRW Module
 * 대원화 환율 관련 기능 모듈
 * 
 * 담당 패널: #exchange-rate-krw-panel
 * 주요 기능: KRW 기준 환율 차트, 통화 비교
 * API: 731Y001 (대원화 환율)
 */

// ============================================================
// MODULE MARKER - 이 모듈이 로드되었음을 표시
// ============================================================
window.exchangeRateModuleLoaded = true;

// ============================================================
// 전역 변수 (constants.js에서 이미 정의된 것들은 재사용)
// ============================================================
// exchangeRates, activeCurrencies, chartData, previousRates, yAxisRange는 constants.js에서 정의됨

// 차트 관련 캐시 (인라인 스크립트와 공유를 위해 window 객체 사용)
if (typeof window.tooltipCache === 'undefined') {
    window.tooltipCache = { allDates: [], perCurrency: {} };
}
if (typeof window.currentRangeKey === 'undefined') {
    window.currentRangeKey = null; // '1W' | '1M' | '3M' | '1Y' | null
}

// ============================================================
// DATE INPUT FUNCTIONS
// ============================================================

/**
 * 날짜 입력 필드 초기화
 */
function initDateInputs() {
    // Exchange Rate 패널의 날짜 입력 필드만 선택
    const economyPanel = document.getElementById('exchange-rate-krw-panel');
    if (!economyPanel) return;
    
    const dateInputs = economyPanel.querySelectorAll('.date-input');
    if (dateInputs.length < 2) return;
    
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 90); // 기본값: 최근 3개월
    
    const startDateStr = start.toISOString().split('T')[0];
    const endDateStr = end.toISOString().split('T')[0];
    
    dateInputs[0].value = startDateStr;
    dateInputs[1].value = endDateStr;
    dateInputs[0].max = endDateStr;
    dateInputs[1].max = endDateStr;
}

/**
 * 날짜 범위 유효성 검사
 * @returns {boolean} 유효하면 true
 */
function validateDateRange() {
    // Exchange Rate 패널의 날짜 입력 필드만 확인
    const economyPanel = document.getElementById('exchange-rate-krw-panel');
    if (!economyPanel) return false;
    
    const dateInputs = economyPanel.querySelectorAll('.date-input');
    if (dateInputs.length < 2) return false;
    
    const startDate = new Date(dateInputs[0].value);
    const endDate = new Date(dateInputs[1].value);
    
    if (startDate > endDate) {
        alert('시작일은 종료일보다 앞서야 합니다.');
        return false;
    }
    
    return true;
}

/**
 * 날짜 범위 설정
 * @param {number} days - 기간 (일)
 * @param {string} periodKey - 기간 키 ('1W', '1M', '3M', '1Y')
 */
function setDateRange(days, periodKey = null) {
    // Exchange Rate 패널의 날짜 입력 필드만 선택
    const economyPanel = document.getElementById('exchange-rate-krw-panel');
    if (!economyPanel) return;
    
    const dateInputs = economyPanel.querySelectorAll('.date-input');
    if (dateInputs.length < 2) return;
    
    const end = new Date();
    let start;
    
    // 1Y의 경우: 현재 월 포함 12개월의 첫날을 시작일로 설정
    if (periodKey === '1Y') {
        // 현재 월에서 11개월 전의 1일
        start = new Date(end.getFullYear(), end.getMonth() - 11, 1);
    } else {
        start = new Date();
        start.setDate(start.getDate() - days);
    }
    
    const startDateStr = start.toISOString().split('T')[0];
    const endDateStr = end.toISOString().split('T')[0];
    
    dateInputs[0].value = startDateStr;
    dateInputs[1].value = endDateStr;
    
    // Period 버튼 활성화 상태 업데이트 (Exchange Rate 패널 내의 버튼만)
    economyPanel.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 데이터 재조회
    if (validateDateRange()) {
        fetchExchangeRateData();
    }
}

/**
 * 기간 버튼 클릭 핸들러
 * @param {string} period - 기간 ('1W', '1M', '3M', '1Y')
 */
function handlePeriodClick(period) {
    const days = {
        '1W': 7,
        '1M': 30,
        '3M': 90,
        '1Y': 365
    };
    
    if (days[period]) {
        setDateRange(days[period], period);
    }
}

// ============================================================
// API FUNCTIONS
// ============================================================

/**
 * 환율 데이터 조회
 */
async function fetchExchangeRateData() {
    if (!validateDateRange()) return;
    
    // Exchange Rate 패널의 날짜 입력 필드만 선택
    const economyPanel = document.getElementById('exchange-rate-krw-panel');
    if (!economyPanel) return;
    
    const dateInputs = economyPanel.querySelectorAll('.date-input');
    if (dateInputs.length < 2) return;
    
    const startDate = formatDateForAPI(dateInputs[0].value);
    const endDate = formatDateForAPI(dateInputs[1].value);
    
    // 활성화된 통화 중 BOK에서 지원하는 통화만 필터링
    const validCurrencies = activeCurrencies.filter(curr => CURRENCY_MAPPING[curr]);
    
    if (validCurrencies.length === 0) {
        console.warn('No valid currencies selected');
        return;
    }
    
    // 로딩 상태 표시
    const chartContainer = document.getElementById('chart-container');
    if (chartContainer) {
        chartContainer.style.opacity = '0.5';
    }
    
    try {
        // 각 통화별로 API 호출
        const fetchPromises = validCurrencies.map(async (currency) => {
            const itemCode = CURRENCY_MAPPING[currency];
            const url = `${API_BASE}/market/indices?type=exchange&itemCode=${itemCode}&startDate=${startDate}&endDate=${endDate}`;
            
            try {
                const response = await fetch(url);
                const json = await response.json();
                return { currency, data: json };
            } catch (err) {
                console.error(`Failed to fetch ${currency}:`, err);
                return { currency, data: { error: err.message } };
            }
        });
        
        const results = await Promise.all(fetchPromises);
        processExchangeRateData(results);
        
    } catch (err) {
        console.error('Failed to fetch exchange rate data:', err);
        alert('환율 데이터 조회 중 오류가 발생했습니다.');
    } finally {
        if (chartContainer) {
            chartContainer.style.opacity = '1';
        }
    }
}

/**
 * 환율 통계 조회
 * @param {string} currency - 통화 코드
 * @param {string} startDate - 시작일 (YYYYMMDD)
 * @param {string} endDate - 종료일 (YYYYMMDD)
 * @returns {Promise<object|null>} - 통계 데이터 또는 null
 */
async function fetchExchangeRateStats(currency, startDate, endDate) {
    try {
        const itemCode = CURRENCY_MAPPING[currency];
        if (!itemCode) return null;
        
        // itemCode를 사용해야 함 (CURRENCY_MAPPING에서 가져온 ECOS 항목 코드)
        const url = `${API_BASE}/market/indices/stats?type=exchange&itemCode=${itemCode}&startDate=${startDate}&endDate=${endDate}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.error) {
            console.error(`Stats error for ${currency}:`, data.error);
            return null;
        }
        
        return data;
    } catch (err) {
        console.error(`Failed to fetch stats for ${currency}:`, err);
        return null;
    }
}

/**
 * 모든 통화의 현재 환율 가져오기 (주요 통화별 현재 환율 테이블용)
 */
async function fetchAllCurrencyRates() {
    const allCurrencies = ['USD', 'EUR', 'JPY', 'CNY', 'GBP', 'CHF', 'HKD', 'CAD', 'RUB'];
    
    // 오늘 날짜로 설정 (최신 환율)
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0].replace(/-/g, '');
    
    try {
        // 각 통화별로 최신 환율 가져오기
        const fetchPromises = allCurrencies.map(async (currency) => {
            const itemCode = CURRENCY_MAPPING[currency];
            if (!itemCode) return { currency, data: null };
            
            // 최근 7일 데이터를 가져와서 가장 최신 값 사용
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - 7);
            const startDateStr = startDate.toISOString().split('T')[0].replace(/-/g, '');
            
            const url = `${API_BASE}/market/indices?type=exchange&itemCode=${itemCode}&startDate=${startDateStr}&endDate=${todayStr}`;
            
            try {
                const response = await fetch(url);
                const json = await response.json();
                return { currency, data: json };
            } catch (err) {
                console.error(`Failed to fetch ${currency}:`, err);
                return { currency, data: null };
            }
        });
        
        const results = await Promise.all(fetchPromises);
        
        // 결과 처리: 각 통화의 최신 환율과 전일 환율을 저장
        results.forEach(({ currency, data }) => {
            if (data && !data.error && data.StatisticSearch && data.StatisticSearch.row) {
                const rows = data.StatisticSearch.row;
                if (rows.length > 0) {
                    // 날짜순으로 정렬 (오래된 것부터)
                    const sortedRows = [...rows].sort((a, b) => {
                        const dateA = parseInt(a.TIME || '0', 10);
                        const dateB = parseInt(b.TIME || '0', 10);
                        return dateA - dateB;
                    });
                    
                    // 가장 최신 데이터 (마지막 항목) = 오늘
                    const latest = sortedRows[sortedRows.length - 1];
                    if (latest && latest.DATA_VALUE) {
                        const currentValue = parseFloat(latest.DATA_VALUE);
                        if (!isNaN(currentValue)) {
                            exchangeRates[currency] = currentValue;
                            
                            // 전일 데이터 찾기
                            if (sortedRows.length >= 2) {
                                const previous = sortedRows[sortedRows.length - 2];
                                if (previous && previous.DATA_VALUE) {
                                    const previousValue = parseFloat(previous.DATA_VALUE);
                                    if (!isNaN(previousValue)) {
                                        previousRates[currency] = previousValue;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        });
        
        // 테이블 업데이트
        updateCurrencyRatesTable();
        
    } catch (err) {
        console.error('Failed to fetch all currency rates:', err);
    }
}

// ============================================================
// DATA PROCESSING FUNCTIONS
// ============================================================

/**
 * 환율 데이터 처리
 * @param {Array} results - API 응답 결과 배열
 */
function processExchangeRateData(results) {
    // chartData 초기화
    chartData = {};
    
    // 조회 기간 가져오기
    const economyPanel = document.getElementById('exchange-rate-krw-panel');
    let startDateStr = '';
    let endDateStr = '';
    
    if (economyPanel) {
        const dateInputs = economyPanel.querySelectorAll('.date-input');
        if (dateInputs.length >= 2) {
            startDateStr = dateInputs[0].value; // YYYY-MM-DD
            endDateStr = dateInputs[1].value;   // YYYY-MM-DD
        }
    }
    
    results.forEach(result => {
        const { currency, data } = result;
        
        if (data.error) {
            console.error(`Error for ${currency}:`, data.error);
            return;
        }
        
        if (data.StatisticSearch && data.StatisticSearch.row) {
            const rows = data.StatisticSearch.row;
            
            // 날짜별 환율 데이터 정리
            const rawValues = rows.map(row => ({
                date: row.TIME, // YYYYMMDD 형식
                value: parseFloat(row.DATA_VALUE)
            }));
            
            // 주말/공휴일 등 빠진 날짜를 이전 영업일 데이터로 채우기
            let values = rawValues;
            if (startDateStr && endDateStr && typeof fillMissingDates === 'function') {
                values = fillMissingDates(rawValues, startDateStr, endDateStr);
            }
            
            chartData[currency] = values;
            
            // 최신 환율 저장 (계산기용) - 실제 데이터만 사용
            const actualValues = values.filter(v => v.isActual !== false);
            if (actualValues.length > 0) {
                const latest = actualValues[actualValues.length - 1];
                const previous = actualValues.length > 1 ? actualValues[actualValues.length - 2] : null;
                
                // 전일 환율 저장
                if (previous) {
                    previousRates[currency] = previous.value;
                }
                
                exchangeRates[currency] = latest.value;
            }
        }
    });
    
    // 툴팁/인터랙션 + X축 라벨 렌더링을 위한 캐시 재구축
    rebuildTooltipCache();
    
    // 차트 업데이트 (여기서 X축 라벨도 함께 렌더링됨)
    updateChart();
    
    // 계산기 업데이트
    updateCalculator();
    
    // 환율 테이블 업데이트
    updateCurrencyRatesTable();

    // 차트 인터랙티브 기능 설정
    setupChartInteractivity();
    
    // 첫 번째 활성 통화의 통계 정보 표시
    if (activeCurrencies.length > 0) {
        const primaryCurrency = activeCurrencies[0];
        if (economyPanel) {
            const dateInputs = economyPanel.querySelectorAll('.date-input');
            if (dateInputs.length >= 2) {
                const startDate = formatDateForAPI(dateInputs[0].value);
                const endDate = formatDateForAPI(dateInputs[1].value);
                fetchExchangeRateStats(primaryCurrency, startDate, endDate)
                    .then(stats => {
                        if (stats) {
                            updateChartHeader(primaryCurrency, stats);
                        }
                    });
            }
        }
    }
}

/**
 * 툴팁 캐시 재구축
 */
function rebuildTooltipCache() {
    const perCurrency = {};
    const allDatesSet = new Set();

    Object.keys(chartData || {}).forEach(curr => {
        const arr = chartData[curr] || [];
        if (!Array.isArray(arr) || arr.length === 0) return;

        const map = {};
        const dates = new Array(arr.length);
        for (let i = 0; i < arr.length; i++) {
            const item = arr[i];
            map[item.date] = item;
            dates[i] = item.date;
            allDatesSet.add(item.date);
        }
        dates.sort(); // YYYYMMDD 문자열 정렬 == 날짜 오름차순
        perCurrency[curr] = { map, dates };
    });

    window.tooltipCache = {
        allDates: Array.from(allDatesSet).sort(),
        perCurrency
    };
}

// ============================================================
// CHART RENDERING FUNCTIONS
// ============================================================

/**
 * SVG 경로 데이터 생성
 * @param {string} currency - 통화 코드
 * @param {Array} data - 차트 데이터
 * @returns {string} - SVG 경로 문자열
 */
function generateSVGPath(currency, data) {
    if (!data || data.length === 0) return '';
    
    const svg = document.querySelector('.chart-svg');
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // Y축 레이블에서 계산된 범위 사용
    const minValue = yAxisRange.min;
    const maxValue = yAxisRange.max;
    const valueRange = maxValue - minValue || 1;
    
    // Path 데이터 생성
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

/**
 * 입력된 날짜 범위에서 기간 키 추론
 * 커스텀 범위의 경우 null을 반환하여 buildXAxisTargets가 실제 기간에 따라 처리하도록 함
 * @returns {string|null} - 기간 키 ('1W', '1M', '3M', '1Y') 또는 null
 */
function inferRangeKeyFromInputs() {
    const economyPanel = document.getElementById('exchange-rate-krw-panel');
    if (!economyPanel) return null;
    
    const inputs = economyPanel.querySelectorAll('.date-input');
    if (!inputs || inputs.length < 2) return null;
    const a = new Date(inputs[0].value);
    const b = new Date(inputs[1].value);
    if (isNaN(a.getTime()) || isNaN(b.getTime())) return null;
    const diffDays = Math.abs(Math.round((b.getTime() - a.getTime()) / (1000 * 60 * 60 * 24)));
    
    // 정확한 기간 버튼에 매칭되는 경우만 키 반환
    // 그 외에는 null을 반환하여 buildXAxisTargets가 diffDays 기준으로 처리
    if (diffDays <= 7) return '1W';
    if (diffDays > 7 && diffDays <= 31) return '1M';
    if (diffDays > 31 && diffDays <= 93) return '3M';
    if (diffDays > 93 && diffDays <= 365) return '1Y';
    
    // 1년 초과는 null 반환 (buildXAxisTargets가 자동으로 처리)
    return null;
}

/**
 * 활성 기간 키 가져오기
 * @returns {string|null} - 기간 키 또는 null (커스텀 범위)
 */
function getActiveRangeKey() {
    if (window.currentRangeKey === '1W' || window.currentRangeKey === '1M' || 
        window.currentRangeKey === '3M' || window.currentRangeKey === '1Y') {
        return window.currentRangeKey;
    }
    const economyPanel = document.getElementById('exchange-rate-krw-panel');
    const btn = economyPanel ? economyPanel.querySelector('.period-btn.active') : null;
    const key = btn ? btn.textContent.trim() : null;
    if (key === '1W' || key === '1M' || key === '3M' || key === '1Y') return key;
    
    // 커스텀 범위의 경우 inferRangeKeyFromInputs가 null을 반환할 수 있음
    return inferRangeKeyFromInputs();
}

/**
 * Y축 라벨 렌더링
 */
function renderYAxisLabels() {
    const svg = document.querySelector('.chart-svg');
    const g = document.getElementById('y-axis-labels');
    if (!svg || !g) return;

    // 기존 라벨 제거
    g.innerHTML = '';

    // 모든 활성 통화의 데이터에서 최소/최대값 계산
    let minValue = Infinity;
    let maxValue = -Infinity;

    activeCurrencies.forEach(currency => {
        const data = chartData[currency];
        if (data && data.length > 0) {
            const values = data.map(d => d.value);
            const dataMin = Math.min(...values);
            const dataMax = Math.max(...values);
            minValue = Math.min(minValue, dataMin);
            maxValue = Math.max(maxValue, dataMax);
        }
    });

    if (minValue === Infinity || maxValue === Infinity) {
        yAxisRange.min = 0;
        yAxisRange.max = 0;
        return;
    }

    // 값 범위 계산
    const range = maxValue - minValue;
    
    // 동적 여백 조정
    let paddingPercent = 0.01; // 기본 1%
    if (range > 1000) {
        paddingPercent = 0.003; // 0.3%
    } else if (range > 100) {
        paddingPercent = 0.005; // 0.5%
    }
    
    const padding = range * paddingPercent;
    
    const calculatedMin = minValue - padding;
    const calculatedMax = maxValue + padding;
    
    // 실제 Y축 범위 저장
    const minValueRatio = minValue / (maxValue || 1);
    if (calculatedMin < 0 || (minValueRatio < 0.05 && minValue < range * 0.1)) {
        yAxisRange.min = 0;
        yAxisRange.max = maxValue + padding + Math.abs(Math.min(0, calculatedMin));
    } else {
        yAxisRange.min = calculatedMin;
        yAxisRange.max = calculatedMax;
    }
    
    // Y축 레이블 렌더링
    const { width, height } = getSvgViewBoxSize(svg);
    const padding_axis = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartHeight = height - padding_axis.top - padding_axis.bottom;

    // 6개의 레이블 생성
    const numLabels = 6;
    const step = (yAxisRange.max - yAxisRange.min) / (numLabels - 1);

    for (let i = 0; i < numLabels; i++) {
        const value = yAxisRange.max - (step * i);
        const y = padding_axis.top + (i / (numLabels - 1)) * chartHeight;

        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', String(padding_axis.left - 10));
        label.setAttribute('y', String(y));
        label.setAttribute('class', 'chart-yaxis-label');
        label.textContent = value.toLocaleString('ko-KR', { 
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2 
        });
        g.appendChild(label);
    }
}

/**
 * X축 라벨 렌더링
 */
function renderXAxisLabels() {
    const svg = document.querySelector('.chart-svg');
    const g = document.getElementById('x-axis-labels');
    if (!svg || !g) return;

    // 기존 라벨 제거
    g.innerHTML = '';

    const tooltipCache = window.tooltipCache;
    const dates = (tooltipCache && tooltipCache.allDates) ? tooltipCache.allDates : [];
    if (!dates || dates.length === 0) return;

    const rangeKey = getActiveRangeKey();
    
    // 날짜 입력 필드에서 종료일(오늘) 가져오기
    const dateInputs = document.querySelectorAll('.date-input');
    let endDateOverride = null;
    if (dateInputs.length >= 2 && dateInputs[1].value) {
        endDateOverride = dateInputs[1].value; // YYYY-MM-DD 형식
    }
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { left: 40, right: 20, top: 20, bottom: 30 };
    const chartWidth = width - padding.left - padding.right;

    // 하단 라벨 y 위치 (viewBox 기준)
    const y = height - padding.bottom + 15;

    const targets = buildXAxisTargets(rangeKey, dates, endDateOverride);
    const n = dates.length;

    // 렌더링
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

/**
 * 차트 업데이트
 */
function updateChart() {
    // 모든 통화 path 초기화
    const allCurrencies = ['USD', 'EUR', 'JPY', 'CNY', 'GBP', 'CHF', 'HKD', 'CAD', 'RUB'];
    allCurrencies.forEach(curr => {
        const path = document.getElementById(`path-${curr}`);
        if (path) {
            path.setAttribute('d', '');
            path.classList.remove('visible');
        }
    });
    
    // Y축 라벨을 먼저 렌더링하여 범위 계산
    renderYAxisLabels();
    
    // 활성화된 통화만 표시 (Y축 범위가 계산된 후)
    activeCurrencies.forEach(currency => {
        if (!CURRENCY_MAPPING[currency]) return;
        
        const path = document.getElementById(`path-${currency}`);
        if (!path) return;
        
        const data = chartData[currency];
        if (data && data.length > 0) {
            const pathData = generateSVGPath(currency, data);
            path.setAttribute('d', pathData);
            path.classList.add('visible');
        }
    });
    
    // X축 라벨 렌더링 (기간별 대표 기준점만 표시)
    renderXAxisLabels();
}

/**
 * 통화 토글
 * @param {string} curr - 통화 코드
 */
function toggleCurrency(curr) {
    const btn = document.querySelector(`.chip[data-curr="${curr}"]`);
    if (!btn) return;
    
    btn.classList.toggle('active');
    const isActive = btn.classList.contains('active');
    
    // activeCurrencies 목록 업데이트
    if (isActive) {
        if (!activeCurrencies.includes(curr)) {
            activeCurrencies.push(curr);
        }
    } else {
        activeCurrencies = activeCurrencies.filter(c => c !== curr);
    }
    
    // 통화가 하나만 선택되었을 때 환율 계산기 자동 업데이트
    if (activeCurrencies.length === 1) {
        const selectedCurrency = activeCurrencies[0];
        const currSelect = document.getElementById('curr-from');
        if (currSelect && currSelect.value !== selectedCurrency) {
            currSelect.value = selectedCurrency;
            calculate(); // 계산기 업데이트
        }
    }
    
    // 데이터가 없으면 API 호출
    if (isActive && (!chartData[curr] || chartData[curr].length === 0)) {
        fetchExchangeRateData();
    } else {
        // 데이터가 있으면 즉시 차트 업데이트
        updateChart();
        
        // 활성 통화가 있으면 첫 번째 통화의 통계 정보 업데이트
        if (activeCurrencies.length > 0) {
            const primaryCurrency = activeCurrencies[0];
            const economyPanel = document.getElementById('exchange-rate-krw-panel');
            if (economyPanel) {
                const dateInputs = economyPanel.querySelectorAll('.date-input');
                if (dateInputs.length >= 2) {
                    const startDate = formatDateForAPI(dateInputs[0].value);
                    const endDate = formatDateForAPI(dateInputs[1].value);
                    fetchExchangeRateStats(primaryCurrency, startDate, endDate)
                        .then(stats => {
                            if (stats) {
                                updateChartHeader(primaryCurrency, stats);
                            }
                        });
                }
            }
        }
    }
}

// ============================================================
// TOOLTIP & INTERACTIVITY FUNCTIONS
// ============================================================

/**
 * 날짜 포맷 함수
 * @param {string} dateStr - YYYYMMDD 형식의 날짜 문자열
 * @returns {string} - YYYY-MM-DD 형식의 날짜 문자열
 */
function formatDate(dateStr) {
    if (dateStr && dateStr.length === 8) {
        return `${dateStr.substring(0,4)}-${dateStr.substring(4,6)}-${dateStr.substring(6,8)}`;
    }
    return dateStr;
}

/**
 * 마우스 X 좌표에서 날짜 찾기
 * @param {number} mouseX - 마우스 X 좌표
 * @param {DOMRect} chartRect - 차트 영역 rect
 * @returns {string|null} - 날짜 문자열 또는 null
 */
function getDateFromMouseX(mouseX, chartRect) {
    const svg = document.querySelector('.chart-svg');
    if (!svg) return null;
    
    const svgRect = svg.getBoundingClientRect();
    const { width: vbW } = getSvgViewBoxSize(svg);
    const padding = { left: 40, right: 20 };
    // viewBox padding을 실제 픽셀 폭으로 환산
    const padLeftPx = (padding.left / vbW) * svgRect.width;
    const padRightPx = (padding.right / vbW) * svgRect.width;
    const chartWidthPx = Math.max(1, svgRect.width - padLeftPx - padRightPx);
    
    // 마우스 X 좌표를 SVG 좌표계로 변환
    const relativeX = mouseX - svgRect.left - padLeftPx;
    const ratio = Math.max(0, Math.min(1, relativeX / chartWidthPx));
    
    // 캐시된 전체 날짜 사용
    const tooltipCache = window.tooltipCache;
    const allDates = (tooltipCache && tooltipCache.allDates) ? tooltipCache.allDates : [];
    
    if (allDates.length === 0) return null;
    
    const index = Math.floor(ratio * (allDates.length - 1));
    return allDates[index];
}

/**
 * 툴팁 표시
 * @param {Event} event - 마우스 이벤트
 * @param {string} date - 날짜 문자열
 */
function showTooltip(event, date) {
    const tooltip = document.getElementById('chart-tooltip');
    const tooltipDate = document.getElementById('tooltip-date');
    const tooltipContent = document.getElementById('tooltip-content');
    
    if (!tooltip || !tooltipDate || !tooltipContent || !date || !chartData) return;
    
    // 날짜 표시
    const formattedDate = formatDate(date);
    const dateObj = parseYYYYMMDD(date);
    
    // 주말/공휴일 여부 확인 (첫 번째 활성 통화의 데이터로 확인)
    let isNonTrading = false;
    if (activeCurrencies.length > 0) {
        const firstCurrency = activeCurrencies[0];
        const data = chartData[firstCurrency];
        if (data) {
            const item = data.find(d => d.date === date);
            if (item && item.isActual === false) {
                isNonTrading = true;
            }
        }
    }
    
    // 날짜 표시 (주말/공휴일인 경우 표시)
    let dateLabel = dateObj ? `${formattedDate} (${weekdayKoShort(dateObj)})` : formattedDate;
    if (isNonTrading) {
        dateLabel += ' <span style="color: var(--text-sub); font-size: 0.75rem;">휴장일</span>';
    }
    tooltipDate.innerHTML = dateLabel;
    
    // 활성화된 통화들의 환율 표시
    const tooltipCache = window.tooltipCache;
    let content = '';
    activeCurrencies.forEach(currency => {
        const c = tooltipCache && tooltipCache.perCurrency ? tooltipCache.perCurrency[currency] : null;
        if (c && c.dates && c.dates.length > 0) {
            // exact -> closest (O(1) map + O(log n) 이진탐색)
            let item = c.map[date];
            if (!item) {
                const closest = findClosestDate(c.dates, date);
                item = closest ? c.map[closest] : null;
            }
            
            if (item) {
                const color = getComputedStyle(document.documentElement)
                    .getPropertyValue(`--c-${currency.toLowerCase()}`).trim();
                
                // 휴장일인 경우 전일 종가 표시
                const noteText = item.isActual === false ? ' <span style="color: var(--text-sub); font-size: 0.7rem;">(전일)</span>' : '';
                
                content += `
                    <div class="chart-tooltip-item">
                        <div class="chart-tooltip-currency">
                            <div class="chart-tooltip-dot" style="background: ${color}"></div>
                            <span>${currency}</span>
                        </div>
                        <span class="chart-tooltip-value">${parseFloat(item.value).toLocaleString('ko-KR')} 원${noteText}</span>
                    </div>
                `;
            }
        }
    });
    
    if (!content) {
        hideTooltip();
        return;
    }
    
    tooltipContent.innerHTML = content;
    
    // 툴팁을 먼저 표시해서 크기를 측정
    tooltip.style.visibility = 'hidden';
    tooltip.classList.add('visible');
    
    const tooltipRect = tooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const tooltipPadding = 10;
    
    // 기본 위치 (마우스 오른쪽 아래)
    let left = event.clientX + 15;
    let top = event.clientY + 15;
    
    // 우측 경계 체크 및 조정
    if (left + tooltipRect.width > viewportWidth - tooltipPadding) {
        left = event.clientX - tooltipRect.width - 15;
    }
    
    // 좌측 경계 체크 및 조정
    if (left < tooltipPadding) {
        if (event.clientX + tooltipRect.width + 15 <= viewportWidth - tooltipPadding) {
            left = event.clientX + 15;
        } else {
            left = tooltipPadding;
        }
    }
    
    // 하단 경계 체크 및 조정
    if (top + tooltipRect.height > viewportHeight - tooltipPadding) {
        top = event.clientY - tooltipRect.height - 15;
    }
    
    // 상단 경계 체크 및 조정
    if (top < tooltipPadding) {
        if (event.clientY + tooltipRect.height + 15 <= viewportHeight - tooltipPadding) {
            top = event.clientY + 15;
        } else {
            top = tooltipPadding;
        }
    }
    
    // 최종 검증 및 강제 조정
    if (left < tooltipPadding) left = tooltipPadding;
    if (left + tooltipRect.width > viewportWidth - tooltipPadding) {
        left = viewportWidth - tooltipPadding - tooltipRect.width;
    }
    if (top < tooltipPadding) top = tooltipPadding;
    if (top + tooltipRect.height > viewportHeight - tooltipPadding) {
        top = viewportHeight - tooltipPadding - tooltipRect.height;
    }
    
    // fixed + transform으로 이동
    tooltip.style.transform = `translate3d(${left}px, ${top}px, 0)`;
    tooltip.style.visibility = 'visible';
}

/**
 * 툴팁 숨기기
 */
function hideTooltip() {
    const tooltip = document.getElementById('chart-tooltip');
    if (tooltip) {
        tooltip.classList.remove('visible');
        tooltip.style.visibility = 'hidden';
    }
}

/**
 * 툴팁을 body로 이동 (Portal)
 */
function ensureTooltipInBody() {
    const tooltip = document.getElementById('chart-tooltip');
    if (!tooltip) return;
    if (tooltip.parentElement !== document.body) {
        document.body.appendChild(tooltip);
    }
}

let exchangeRateCrosshairX = null;
let exchangeRateCrosshairY = null;

/**
 * 차트 인터랙티브 기능 설정
 */
function setupChartInteractivity() {
    // 이미 설정되어 있으면 스킵
    if (chartInteractivitySetup) return;
    
    const chartContainer = document.getElementById('chart-container');
    const svg = document.querySelector('.chart-svg');
    
    if (!chartContainer || !svg) return;

    // Portal 보장
    ensureTooltipInBody();
    
    // Create crosshair elements
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 60, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const crosshairs = createCrosshairElements(svg, padding, chartWidth, chartHeight);
    exchangeRateCrosshairX = crosshairs.crosshairX;
    exchangeRateCrosshairY = crosshairs.crosshairY;
    
    // mousemove rAF 스로틀링
    let rafId = null;
    let lastPoint = null;
    const handleMove = () => {
        rafId = null;
        if (!lastPoint) return;

        const tooltipCache = window.tooltipCache;
        if (!tooltipCache || !tooltipCache.allDates || tooltipCache.allDates.length === 0) {
            hideTooltip();
            hideCrosshair(exchangeRateCrosshairX, exchangeRateCrosshairY);
            return;
        }

        const fakeEvent = { clientX: lastPoint.x, clientY: lastPoint.y };
        const date = getDateFromMouseX(lastPoint.x, chartContainer.getBoundingClientRect());
        if (date) {
            showTooltip(fakeEvent, date);
            // Update crosshair X position
            const allDates = tooltipCache.allDates;
            const dateIdx = allDates.indexOf(date);
            if (dateIdx >= 0) {
                const crosshairXPos = padding.left + (dateIdx / (allDates.length - 1 || 1)) * chartWidth;
                if (exchangeRateCrosshairX) {
                    exchangeRateCrosshairX.setAttribute('x1', crosshairXPos);
                    exchangeRateCrosshairX.setAttribute('x2', crosshairXPos);
                    exchangeRateCrosshairX.style.opacity = '1';
                }
                
                // Calculate average Y for crosshair
                let sumY = 0, countY = 0;
                activeCurrencies.forEach(currency => {
                    const currData = chartData[currency];
                    if (currData) {
                        const item = currData.find(d => d.date === date);
                        if (item && Number.isFinite(item.value)) { sumY += item.value; countY++; }
                    }
                });
                
                if (countY > 0 && exchangeRateCrosshairY) {
                    const avgVal = sumY / countY;
                    const { min, max } = yAxisRange;
                    const normY = (avgVal - min) / (max - min || 1);
                    const crosshairYPos = padding.top + (1 - normY) * chartHeight;
                    exchangeRateCrosshairY.setAttribute('y1', crosshairYPos);
                    exchangeRateCrosshairY.setAttribute('y2', crosshairYPos);
                    exchangeRateCrosshairY.style.opacity = '1';
                }
            }
        } else {
            hideTooltip();
            hideCrosshair(exchangeRateCrosshairX, exchangeRateCrosshairY);
        }
    };

    chartContainer.addEventListener('mousemove', (event) => {
        lastPoint = { x: event.clientX, y: event.clientY };
        if (rafId) return;
        rafId = requestAnimationFrame(handleMove);
    });
    
    // 마우스가 차트 영역을 벗어날 때
    chartContainer.addEventListener('mouseleave', () => {
        hideTooltip();
        hideCrosshair(exchangeRateCrosshairX, exchangeRateCrosshairY);
    });

    // 스크롤/리사이즈 시 툴팁 숨김
    window.addEventListener('scroll', () => {
        hideTooltip();
        hideCrosshair(exchangeRateCrosshairX, exchangeRateCrosshairY);
    }, true);
    window.addEventListener('resize', () => {
        hideTooltip();
        hideCrosshair(exchangeRateCrosshairX, exchangeRateCrosshairY);
    });
    
    chartInteractivitySetup = true;
}

// ============================================================
// TABLE & CALCULATOR FUNCTIONS
// ============================================================

/**
 * 통화 환율 테이블 업데이트
 */
function updateCurrencyRatesTable() {
    const grid = document.getElementById('currency-rates-grid');
    if (!grid) return;
    
    const currencies = ['USD', 'EUR', 'JPY', 'CNY', 'GBP', 'CHF', 'HKD', 'CAD', 'RUB'];
    
    grid.innerHTML = currencies.map(currency => {
        const currentRate = exchangeRates[currency];
        const previousRate = previousRates[currency];
        
        if (!currentRate) {
            return `
                <div class="currency-rate-item">
                    <div class="currency-rate-header">
                        <span class="currency-code">${currency}</span>
                    </div>
                    <div class="currency-value">-</div>
                    <div class="currency-change">
                        <span style="color: var(--text-sub);">데이터 없음</span>
                    </div>
                </div>
            `;
        }
        
        // 전일 대비 계산
        let change = 0;
        let changePercent = 0;
        let isUp = false;
        
        if (previousRate && !isNaN(previousRate) && previousRate > 0) {
            change = currentRate - previousRate;
            changePercent = (change / previousRate) * 100;
            isUp = change > 0;
        }
        
        const changeClass = change === 0 ? '' : (isUp ? 'up' : 'down');
        const changeIcon = change === 0 ? '' : (isUp ? '▲' : '▼');
        const changeSign = change === 0 ? '' : (isUp ? '+' : '');
        
        let changeText = '';
        if (previousRate && !isNaN(previousRate) && previousRate > 0) {
            changeText = `
                <span class="currency-change-icon">${changeIcon}</span>
                <span class="currency-change-value">
                    ${changeSign}${Math.abs(change).toFixed(2)}
                </span>
                <span class="currency-change-percent">
                    (${changeSign}${Math.abs(changePercent).toFixed(2)}%)
                </span>
            `;
        } else {
            changeText = '<span style="color: var(--text-sub);">-</span>';
        }
        
        return `
            <div class="currency-rate-item">
                <div class="currency-rate-header">
                    <span class="currency-code">${currency}</span>
                </div>
                <div class="currency-value">${currentRate.toLocaleString('ko-KR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                <div class="currency-change ${changeClass}">
                    ${changeText}
                </div>
            </div>
        `;
    }).join('');
}

/**
 * 계산기 업데이트
 */
function updateCalculator() {
    const amountFrom = document.getElementById('amount-from');
    const amountTo = document.getElementById('amount-to');
    const currSelect = document.getElementById('curr-from');
    
    if (amountFrom && amountTo && currSelect) {
        calculate();
    }
}

/**
 * 환율 계산
 */
function calculate() {
    const amountFrom = document.getElementById('amount-from');
    const amountTo = document.getElementById('amount-to');
    const currSelect = document.getElementById('curr-from');
    
    if (!amountFrom || !amountTo || !currSelect) return;
    
    const val = parseFloat(amountFrom.value) || 0;
    const curr = currSelect.value;
    
    // exchangeRates에서 환율 가져오기
    const rate = exchangeRates[curr];
    
    if (rate && !isNaN(val)) {
        amountTo.value = (val * rate).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    } else {
        amountTo.value = '-';
    }
}

/**
 * 차트 헤더 업데이트
 * @param {string} currency - 통화 코드
 * @param {object} stats - 통계 데이터
 */
function updateChartHeader(currency, stats) {
    const titleEl = document.getElementById('chart-main-title');
    const valueEl = document.getElementById('chart-main-value');
    const changeValueEl = document.getElementById('change-value');
    const changePercentEl = document.getElementById('change-percent');
    const statHighEl = document.getElementById('stat-high');
    const statLowEl = document.getElementById('stat-low');
    const statAverageEl = document.getElementById('stat-average');
    
    // 타이틀 업데이트
    if (titleEl) {
        titleEl.textContent = `${currency}/KRW`;
    }
    
    // 에러 또는 데이터 없음 처리
    if (!stats || stats.error) {
        if (valueEl) valueEl.textContent = '-';
        if (changeValueEl) changeValueEl.textContent = '-';
        if (changePercentEl) changePercentEl.textContent = '(-)';
        if (statHighEl) statHighEl.textContent = '-';
        if (statLowEl) statLowEl.textContent = '-';
        if (statAverageEl) statAverageEl.textContent = '-';
        return;
    }
    
    // 현재 값 업데이트 (애니메이션 적용)
    if (valueEl && stats.current != null) {
        const targetValue = stats.current;
        const currentValue = parseFloat(valueEl.textContent.replace(/,/g, '')) || 0;
        if (currentValue !== targetValue && typeof animateValue === 'function') {
            animateValue(valueEl, currentValue, targetValue, 800);
        } else {
            valueEl.textContent = targetValue.toLocaleString('ko-KR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    }
    
    // 변동 정보 업데이트
    const change = stats.change || 0;
    const changePercent = stats.changePercent || 0;
    const isUp = change >= 0;
    
    if (changeValueEl) {
        changeValueEl.textContent = `${isUp ? '+' : ''}${change.toFixed(2)}`;
        changeValueEl.className = `change-value ${isUp ? 'up' : 'down'}`;
    }
    
    if (changePercentEl) {
        changePercentEl.textContent = `(${isUp ? '+' : ''}${changePercent.toFixed(2)}%)`;
        changePercentEl.className = `change-percent ${isUp ? 'up' : 'down'}`;
    }
    
    // 통계 정보 업데이트 (애니메이션 적용)
    if (statHighEl && stats.high != null) {
        const targetHigh = stats.high;
        const currentHigh = parseFloat(statHighEl.textContent.replace(/,/g, '')) || 0;
        if (currentHigh !== targetHigh && typeof animateValue === 'function') {
            animateValue(statHighEl, currentHigh, targetHigh, 600);
        } else {
            statHighEl.textContent = targetHigh.toLocaleString('ko-KR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    }
    
    if (statLowEl && stats.low != null) {
        const targetLow = stats.low;
        const currentLow = parseFloat(statLowEl.textContent.replace(/,/g, '')) || 0;
        if (currentLow !== targetLow && typeof animateValue === 'function') {
            animateValue(statLowEl, currentLow, targetLow, 600);
        } else {
            statLowEl.textContent = targetLow.toLocaleString('ko-KR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    }
    
    if (statAverageEl && stats.average != null) {
        const targetAvg = stats.average;
        const currentAvg = parseFloat(statAverageEl.textContent.replace(/,/g, '')) || 0;
        if (currentAvg !== targetAvg && typeof animateValue === 'function') {
            animateValue(statAverageEl, currentAvg, targetAvg, 600);
        } else {
            statAverageEl.textContent = targetAvg.toLocaleString('ko-KR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    }
}

// ============================================================
// INITIALIZATION
// ============================================================

/**
 * 환율 모듈 초기화
 */
function initExchangeRate() {
    // 날짜 입력 초기화
    initDateInputs();
    
    // 현재 period 상태 초기화
    const economyPanel = document.getElementById('exchange-rate-krw-panel');
    const activeBtn = economyPanel ? economyPanel.querySelector('.period-btn.active') : null;
    const initialKey = activeBtn ? activeBtn.textContent.trim() : null;
    window.currentRangeKey = (initialKey === '1W' || initialKey === '1M' || initialKey === '3M' || initialKey === '1Y') ? initialKey : null;
    
    // Period 버튼 클릭 이벤트
    if (economyPanel) {
        economyPanel.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                economyPanel.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                const period = e.target.textContent.trim();
                window.currentRangeKey = period;
                handlePeriodClick(period);
            });
        });
        
        // 날짜 입력 변경 이벤트
        economyPanel.querySelectorAll('.date-input').forEach(input => {
            input.addEventListener('change', () => {
                if (validateDateRange()) {
                    economyPanel.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                    window.currentRangeKey = null;
                    fetchExchangeRateData();
                }
            });
        });
    }
    
    // 초기 통화 선택 상태 확인 및 설정 (USD만 선택)
    document.querySelectorAll('.chip').forEach(chip => {
        const curr = chip.getAttribute('data-curr');
        if (curr === 'USD') {
            chip.classList.add('active');
            if (!activeCurrencies.includes('USD')) {
                activeCurrencies.push('USD');
            }
        } else {
            chip.classList.remove('active');
            activeCurrencies = activeCurrencies.filter(c => c !== curr);
        }
    });
    
    // activeCurrencies가 비어있으면 USD로 초기화
    if (activeCurrencies.length === 0) {
        activeCurrencies = ['USD'];
    }
    
    // 초기 계산기 설정 (USD 기준)
    const currSelect = document.getElementById('curr-from');
    if (currSelect) {
        currSelect.value = 'USD';
    }
    
    // 계산기 이벤트 설정
    const amountFrom = document.getElementById('amount-from');
    if (amountFrom) {
        amountFrom.addEventListener('input', calculate);
        if (currSelect) {
            currSelect.addEventListener('change', calculate);
        }
    }
    
    // 초기 데이터 로드
    if (validateDateRange()) {
        fetchExchangeRateData();
    }
    
    // 모든 통화의 현재 환율 가져오기
    fetchAllCurrencyRates();
    
    // 주기적으로 모든 통화 환율 업데이트 (5분마다)
    setInterval(() => {
        fetchAllCurrencyRates();
    }, 5 * 60 * 1000);
    
    // 초기 테이블 렌더링
    updateCurrencyRatesTable();
    
    console.log('✅ Exchange Rate module initialized');
}

// ============================================================
// EXPOSE TO WINDOW
// ============================================================
window.initDateInputs = initDateInputs;
window.validateDateRange = validateDateRange;
window.setDateRange = setDateRange;
window.handlePeriodClick = handlePeriodClick;
window.fetchExchangeRateData = fetchExchangeRateData;
window.fetchExchangeRateStats = fetchExchangeRateStats;
window.fetchAllCurrencyRates = fetchAllCurrencyRates;
window.processExchangeRateData = processExchangeRateData;
window.rebuildTooltipCache = rebuildTooltipCache;
window.generateSVGPath = generateSVGPath;
window.inferRangeKeyFromInputs = inferRangeKeyFromInputs;
window.getActiveRangeKey = getActiveRangeKey;
window.renderYAxisLabels = renderYAxisLabels;
window.renderXAxisLabels = renderXAxisLabels;
window.updateChart = updateChart;
window.toggleCurrency = toggleCurrency;
window.formatDate = formatDate;
window.getDateFromMouseX = getDateFromMouseX;
window.showTooltip = showTooltip;
window.hideTooltip = hideTooltip;
window.ensureTooltipInBody = ensureTooltipInBody;
window.setupChartInteractivity = setupChartInteractivity;
window.updateCurrencyRatesTable = updateCurrencyRatesTable;
window.updateCalculator = updateCalculator;
window.calculate = calculate;
window.initExchangeRate = initExchangeRate;

console.log('📈 Exchange Rate module loaded');
