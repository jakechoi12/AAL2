/**
 * AAL Application - Utility Helper Functions
 * 이 파일은 전역 유틸리티 함수들을 정의합니다.
 */

// ============================================================
// DATE FORMATTING FUNCTIONS
// ============================================================

/**
 * YYYY-MM-DD 형식을 YYYYMMDD 형식으로 변환
 * @param {string} dateStr - YYYY-MM-DD 형식의 날짜 문자열
 * @returns {string} - YYYYMMDD 형식의 날짜 문자열
 */
function formatDateForAPI(dateStr) {
    return dateStr.replace(/-/g, '');
}

/**
 * Interest Rates 전용: YYYY-MM -> YYYYMM01 (백엔드는 YYYYMMDD 형식 기대)
 * @param {string} dateStr - YYYY-MM 형식의 날짜 문자열
 * @returns {string} - YYYYMM01 형식의 날짜 문자열
 */
function formatInterestDateForAPI(dateStr) {
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    if (parts.length === 2) {
        return `${parts[0]}${parts[1]}01`;
    }
    return dateStr.replace(/-/g, '');
}

/**
 * Date 객체를 YYYYMMDD 문자열로 변환
 * @param {Date} d - Date 객체
 * @returns {string} - YYYYMMDD 형식의 문자열
 */
function toYYYYMMDD(d) {
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${yyyy}${mm}${dd}`;
}

/**
 * YYYYMMDD 문자열을 Date 객체로 변환
 * @param {string} dateStr - YYYYMMDD 형식의 문자열
 * @returns {Date|null} - Date 객체 또는 null
 */
function parseYYYYMMDD(dateStr) {
    if (!dateStr || dateStr.length !== 8) return null;
    const year = parseInt(dateStr.substring(0, 4), 10);
    const month = parseInt(dateStr.substring(4, 6), 10) - 1;
    const day = parseInt(dateStr.substring(6, 8), 10);
    return new Date(year, month, day);
}

/**
 * 특정 연월의 일수 반환
 * @param {number} year - 연도
 * @param {number} monthIndex - 월 인덱스 (0-11)
 * @returns {number} - 해당 월의 일수
 */
function daysInMonth(year, monthIndex) {
    return new Date(year, monthIndex + 1, 0).getDate();
}

/**
 * 날짜를 안전하게 생성 (해당 월의 마지막 일 초과 방지)
 * @param {number} year - 연도
 * @param {number} monthIndex - 월 인덱스 (0-11)
 * @param {number} dayOfMonth - 일
 * @returns {Date} - Date 객체
 */
function makeDateSafe(year, monthIndex, dayOfMonth) {
    const maxDay = daysInMonth(year, monthIndex);
    return new Date(year, monthIndex, Math.min(dayOfMonth, maxDay));
}

/**
 * 요일을 한국어 약어로 변환
 * @param {Date} dateObj - Date 객체
 * @returns {string} - 요일 약어 (일, 월, 화, 수, 목, 금, 토)
 */
function weekdayKoShort(dateObj) {
    const days = ['일', '월', '화', '수', '목', '금', '토'];
    return days[dateObj.getDay()];
}

// ============================================================
// NUMBER FORMATTING FUNCTIONS
// ============================================================

/**
 * GDP 숫자 포맷팅 (한국어 로케일)
 * @param {number} n - 숫자
 * @param {number} maxFrac - 최대 소수점 자릿수 (기본값: 1)
 * @returns {string} - 포맷된 문자열
 */
function formatGDPNumber(n, maxFrac = 1) {
    if (!Number.isFinite(n)) return '-';
    return n.toLocaleString('ko-KR', { maximumFractionDigits: maxFrac });
}

/**
 * GDP 변화량 포맷팅 (부호 포함)
 * @param {number} n - 숫자
 * @param {number} maxFrac - 최대 소수점 자릿수 (기본값: 1)
 * @returns {string} - 포맷된 문자열 (양수일 경우 + 접두사)
 */
function formatGDPChange(n, maxFrac = 1) {
    if (!Number.isFinite(n)) return '-';
    const sign = n > 0 ? '+' : (n < 0 ? '' : '');
    return `${sign}${n.toLocaleString('ko-KR', { maximumFractionDigits: maxFrac })}`;
}

/**
 * GDP 숫자에 쉬운 단위를 괄호로 추가하는 함수
 * @param {number} value - 원본 값
 * @param {string} itemCode - 항목 코드 (10101, 1010101, 10102, 1010201, 10106, 1010601, 10107, 1010701)
 * @returns {string} - "2,556,857.4 (2556조)" 형식의 문자열
 */
function formatGDPNumberWithEasyUnit(value, itemCode) {
    if (!Number.isFinite(value)) return formatGDPNumber(value, 1);
    
    const formattedValue = formatGDPNumber(value, 1);
    let easyUnit = '';
    
    // 국내총생산 / 국민총소득 (KRW): 십억원 → 조원
    if (itemCode === '10101' || itemCode === '10102') {
        const joValue = value / 1000;
        if (joValue >= 0.01) {
            easyUnit = `(${joValue.toFixed(joValue >= 1 ? 0 : 1)}조)`;
        }
    }
    // 국내총생산 / 국민총소득 (USD): 억달러 → 조달러
    else if (itemCode === '1010101' || itemCode === '1010201') {
        const joValue = value / 10000;
        if (joValue >= 0.01) {
            easyUnit = `(${joValue.toFixed(joValue >= 1 ? 0 : 2)}조)`;
        }
    }
    // 1인당 국민총소득 / 1인당 국내총생산 (KRW): 만원 → 억원/천만원
    else if (itemCode === '10106' || itemCode === '10107') {
        if (value >= 10000) {
            const eokValue = value / 10000;
            easyUnit = `(${eokValue.toFixed(1)}억)`;
        } else if (value >= 1000) {
            const cheonValue = value / 1000;
            easyUnit = `(${cheonValue.toFixed(1)}천만)`;
        }
    }
    // 1인당 국민총소득 / 1인당 국내총생산 (USD): 달러 → 만달러/천달러
    else if (itemCode === '1010601' || itemCode === '1010701') {
        if (value >= 10000) {
            const manValue = value / 10000;
            easyUnit = `(${manValue.toFixed(1)}만)`;
        } else if (value >= 1000) {
            const cheonValue = value / 1000;
            easyUnit = `(${cheonValue.toFixed(1)}천)`;
        }
    }
    
    return easyUnit ? `${formattedValue} ${easyUnit}` : formattedValue;
}

/**
 * 수출입 통계 숫자에 쉬운 단위를 괄호로 추가하는 함수
 * @param {number} value - 원본 값 (USD: 백만달러 단위, KRW: 억원 단위)
 * @param {string} currency - 통화 ('USD' 또는 'KRW')
 * @returns {object} - { formatted: "55,878", easyUnit: "(559억)" } 형식의 객체
 */
function formatTradeNumberWithEasyUnit(value, currency = 'USD') {
    if (!Number.isFinite(value)) {
        return { formatted: value.toFixed(0), easyUnit: '' };
    }
    
    const formattedValue = Number(value).toLocaleString('ko-KR', { 
        maximumFractionDigits: 0 
    });
    
    let easyUnit = '';
    
    if (currency === 'USD') {
        const eokValue = value / 100;
        if (eokValue >= 0.1) {
            easyUnit = `(${eokValue.toFixed(eokValue >= 1 ? 0 : 1)}억)`;
        }
    } else if (currency === 'KRW') {
        const joValue = value / 10000;
        if (joValue >= 0.01) {
            easyUnit = `(${joValue.toFixed(joValue >= 1 ? 0 : 1)}조)`;
        }
    }
    
    return { formatted: formattedValue, easyUnit: easyUnit };
}

// ============================================================
// ANIMATION FUNCTIONS
// ============================================================

/**
 * 숫자 값을 부드럽게 애니메이션하는 함수
 * @param {HTMLElement} element - 애니메이션할 DOM 요소
 * @param {number} start - 시작 값
 * @param {number} end - 종료 값
 * @param {number} duration - 애니메이션 지속 시간 (ms)
 */
function animateValue(element, start, end, duration) {
    if (!element || isNaN(start) || isNaN(end)) return;
    
    const startTime = performance.now();
    const difference = end - start;
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (ease-out)
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const current = start + (difference * easeProgress);
        
        element.textContent = current.toLocaleString('ko-KR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// ============================================================
// INFLATION DATE FUNCTIONS
// ============================================================

/**
 * 물가 날짜 문자열 파싱
 * @param {string} dateStr - 날짜 문자열
 * @param {string} cycle - 주기 ('M': 월별, 'Q': 분기별)
 * @returns {Date|null} - Date 객체 또는 null
 */
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

/**
 * 물가 날짜 비교
 * @param {string} a - 첫 번째 날짜 문자열
 * @param {string} b - 두 번째 날짜 문자열
 * @param {string} cycle - 주기 ('M': 월별, 'Q': 분기별)
 * @returns {number} - 비교 결과 (-1, 0, 1)
 */
function compareInflationDates(a, b, cycle) {
    const da = parseInflationDate(a, cycle);
    const db = parseInflationDate(b, cycle);
    if (!da || !db) return String(a).localeCompare(String(b));
    return da.getTime() - db.getTime();
}

/**
 * 물가 기간 라벨 포맷팅
 * @param {string} dateStr - 날짜 문자열
 * @param {string} cycle - 주기 ('M': 월별, 'Q': 분기별)
 * @returns {string} - 포맷된 라벨
 */
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

/**
 * 물가 메트릭 라벨 가져오기
 * @param {string} cycle - 주기 ('M': 월별, 'Q': 분기별)
 * @returns {string} - 라벨
 */
function getInflationMetricLabel(cycle) {
    return cycle === 'Q' ? '전기비' : '전월비';
}

/**
 * 물가 지수 통계 계산
 * @param {Array} rawSeries - 원시 데이터 시리즈
 * @param {string} cycle - 주기
 * @returns {object} - 통계 객체
 */
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
    const changePercent = prev == null || prev === 0 ? 0 : (change / prev) * 100;
    const high = Math.max(...values);
    const low = Math.min(...values);
    const average = values.reduce((a, b) => a + b, 0) / values.length;
    return { current, change, changePercent, high, low, average, hasData: true };
}

// ============================================================
// GDP UTILITY FUNCTIONS
// ============================================================

/**
 * 연도 라벨 생성
 * @param {number} year - 연도
 * @returns {string} - 연도 문자열
 */
function buildYearLabel(year) {
    return String(year);
}

// ============================================================
// HTML ESCAPE FUNCTION
// ============================================================

/**
 * HTML 특수 문자 이스케이프
 * @param {string} text - 이스케이프할 텍스트
 * @returns {string} - 이스케이프된 텍스트
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
// INTEREST RATE DATE FUNCTIONS (공유 함수)
// ============================================================

/**
 * 금리 날짜 문자열 파싱
 * @param {string} dateStr - 날짜 문자열
 * @param {string} cycle - 주기 ('M': 월별, 'Q': 분기별, 'A': 연도별)
 * @returns {Date|null} - Date 객체 또는 null
 */
function parseInterestDate(dateStr, cycle) {
    if (!dateStr) return null;
    
    if (cycle === 'M') {
        // 월별: YYYYMM -> 해당 월의 첫째 날로 변환
        if (dateStr.length === 6) {
            const year = parseInt(dateStr.substring(0, 4), 10);
            const month = parseInt(dateStr.substring(4, 6), 10) - 1;
            return new Date(year, month, 1);
        }
    } else if (cycle === 'Q') {
        // 분기별: YYYYQn (예: 2024Q1) -> 해당 분기 첫째 날로 변환
        const match = dateStr.match(/^(\d{4})Q([1-4])$/);
        if (match) {
            const year = parseInt(match[1], 10);
            const quarter = parseInt(match[2], 10);
            const month = (quarter - 1) * 3; // Q1=0, Q2=3, Q3=6, Q4=9
            return new Date(year, month, 1);
        }
    } else if (cycle === 'A') {
        // 연도별: YYYY -> 해당 연도의 1월 1일로 변환
        if (dateStr.length === 4) {
            const year = parseInt(dateStr, 10);
            return new Date(year, 0, 1);
        }
    }
    
    return null;
}

/**
 * 금리 날짜 포맷팅
 * @param {Date} dateObj - Date 객체
 * @param {string} cycle - 주기 ('M': 월별, 'Q': 분기별, 'A': 연도별)
 * @returns {string} - 포맷된 문자열
 */
function formatInterestDate(dateObj, cycle) {
    if (!dateObj) return '';
    
    if (cycle === 'M') {
        // 월별: YYYY/MM
        return `${dateObj.getFullYear()}/${String(dateObj.getMonth() + 1).padStart(2, '0')}`;
    } else if (cycle === 'Q') {
        // 분기별: YYYY Qn
        const quarter = Math.floor(dateObj.getMonth() / 3) + 1;
        return `${dateObj.getFullYear()} Q${quarter}`;
    } else if (cycle === 'A') {
        // 연도별: YYYY
        return String(dateObj.getFullYear());
    }
    
    return '';
}

/**
 * 금리 날짜 비교
 * @param {string} a - 첫 번째 날짜 문자열
 * @param {string} b - 두 번째 날짜 문자열
 * @param {string} cycle - 주기
 * @returns {number} - 비교 결과
 */
function compareInterestDates(a, b, cycle) {
    const dateA = parseInterestDate(a, cycle);
    const dateB = parseInterestDate(b, cycle);
    
    if (!dateA || !dateB) {
        // 파싱 실패 시 문자열 비교
        return a.localeCompare(b);
    }
    
    return dateA.getTime() - dateB.getTime();
}

// ============================================================
// CHART UTILITY FUNCTIONS (공유 함수)
// ============================================================

/**
 * SVG viewBox 크기 가져오기
 * @param {SVGElement} svgEl - SVG 요소
 * @returns {object} - { width, height }
 */
function getSvgViewBoxSize(svgEl) {
    try {
        const vb = (svgEl && svgEl.getAttribute) ? svgEl.getAttribute('viewBox') : null;
        if (vb) {
            const parts = vb.trim().split(/\s+/).map(Number);
            if (parts.length === 4 && parts.every(n => Number.isFinite(n))) {
                return { width: parts[2], height: parts[3] };
            }
        }
    } catch (e) {
        // ignore
    }
    return { width: 800, height: 300 };
}

/**
 * 주말/공휴일 등 빠진 날짜를 이전 영업일 데이터로 채우기
 * @param {Array} data - {date, value} 배열 (date는 YYYYMMDD 형식)
 * @param {string} startDateStr - 시작일 (YYYYMMDD 또는 YYYY-MM-DD)
 * @param {string} endDateStr - 종료일 (YYYYMMDD 또는 YYYY-MM-DD)
 * @returns {Array} - 모든 날짜가 채워진 {date, value} 배열
 */
function fillMissingDates(data, startDateStr, endDateStr) {
    if (!data || data.length === 0) return [];
    
    // 날짜 형식 정규화
    const normalizeDate = (str) => str.includes('-') ? str.replace(/-/g, '') : str;
    const start = normalizeDate(startDateStr);
    const end = normalizeDate(endDateStr);
    
    // 기존 데이터를 맵으로 변환
    const dataMap = {};
    data.forEach(item => {
        dataMap[item.date] = item.value;
    });
    
    // 시작일과 종료일 파싱
    const startObj = parseYYYYMMDD(start);
    const endObj = parseYYYYMMDD(end);
    
    if (!startObj || !endObj) return data;
    
    const result = [];
    let lastValue = null;
    
    // 시작일 이전의 첫 번째 데이터 값 찾기 (없는 경우 대비)
    const sortedDates = Object.keys(dataMap).sort();
    if (sortedDates.length > 0) {
        lastValue = dataMap[sortedDates[0]];
    }
    
    // 시작일부터 종료일까지 모든 날짜 순회
    const current = new Date(startObj);
    while (current <= endObj) {
        const dateStr = toYYYYMMDD(current);
        
        if (dataMap[dateStr] !== undefined) {
            // 실제 데이터가 있는 경우
            lastValue = dataMap[dateStr];
            result.push({ date: dateStr, value: lastValue, isActual: true });
        } else if (lastValue !== null) {
            // 데이터가 없는 경우 (주말/공휴일) - 이전 값 사용
            result.push({ date: dateStr, value: lastValue, isActual: false });
        }
        
        // 다음 날로 이동
        current.setDate(current.getDate() + 1);
    }
    
    return result;
}

/**
 * 정렬된 날짜 배열에서 가장 가까운 날짜 찾기 (이진 탐색)
 * @param {Array} sortedDates - 정렬된 날짜 배열 (YYYYMMDD 형식)
 * @param {string} targetDateStr - 찾을 날짜 (YYYYMMDD 형식)
 * @returns {string|null} - 가장 가까운 날짜 또는 null
 */
function findClosestDate(sortedDates, targetDateStr) {
    if (!sortedDates || sortedDates.length === 0) return null;
    const target = parseInt(targetDateStr, 10);
    let lo = 0;
    let hi = sortedDates.length - 1;

    while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        const midVal = parseInt(sortedDates[mid], 10);
        if (midVal === target) return sortedDates[mid];
        if (midVal < target) lo = mid + 1;
        else hi = mid - 1;
    }

    // lo는 삽입 위치. hi는 lo-1
    const candA = sortedDates[Math.max(0, hi)];
    const candB = sortedDates[Math.min(sortedDates.length - 1, lo)];
    if (!candA) return candB || null;
    if (!candB) return candA || null;

    const diffA = Math.abs(parseInt(candA, 10) - target);
    const diffB = Math.abs(parseInt(candB, 10) - target);
    return diffA <= diffB ? candA : candB;
}

/**
 * 타겟 배열 중복 제거 및 정렬
 * @param {Array} targets - { idx, label } 객체 배열
 * @returns {Array} - 중복 제거 및 정렬된 배열
 */
function dedupeAndSortTargets(targets) {
    const map = new Map();
    for (const t of targets) {
        if (t && Number.isFinite(t.idx)) map.set(t.idx, t); // idx 기준 중복 제거
    }
    return Array.from(map.values()).sort((a, b) => a.idx - b.idx);
}

/**
 * X축 타겟 위치 계산
 * 기간에 따라 다른 라벨 표시:
 * - 1W: 모든 일자 표시 (MM.DD)
 * - 1M: 1일, 15일, 마지막날 표시
 * - 3M: 각 월 표시
 * - 1Y: 각 월 표시 (12개월)
 * - 1Y 초과: 연도와 홀수 월만 표시
 * - 2Y 초과: 연도만 표시
 * 
 * @param {string} rangeKey - 기간 키 ('1W', '1M', '3M', '1Y' 또는 null)
 * @param {Array} dates - 날짜 배열 (YYYYMMDD 형식)
 * @param {string} endDateOverride - 종료일 오버라이드 (YYYY-MM-DD 또는 YYYYMMDD)
 * @returns {Array} - { idx, label } 객체 배열
 */
function buildXAxisTargets(rangeKey, dates, endDateOverride = null) {
    if (!dates || dates.length === 0) return [];
    
    // 시작일과 종료일 계산
    const startDateStr = dates[0];
    const startObj = parseYYYYMMDD(startDateStr);
    
    let endDateStr, endObj;
    if (endDateOverride) {
        if (endDateOverride.includes('-')) {
            endDateStr = endDateOverride.replace(/-/g, '');
        } else {
            endDateStr = endDateOverride;
        }
        endObj = parseYYYYMMDD(endDateStr);
    } else {
        endDateStr = dates[dates.length - 1];
        endObj = parseYYYYMMDD(endDateStr);
    }
    
    if (!endObj || !startObj) return [];

    // 실제 조회 기간 계산 (일 단위)
    const diffMs = endObj.getTime() - startObj.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    const indexMap = {};
    for (let i = 0; i < dates.length; i++) indexMap[dates[i]] = i;

    const targets = []; // { idx, label }
    
    // 날짜 포맷 함수들
    const formatMD = (dObj) => {
        const month = String(dObj.getMonth() + 1).padStart(2, '0');
        const day = String(dObj.getDate()).padStart(2, '0');
        return `${month}.${day}`;
    };
    
    const formatYM = (dObj) => {
        const year = String(dObj.getFullYear()).slice(-2);
        const month = String(dObj.getMonth() + 1).padStart(2, '0');
        return `${year}.${month}`;
    };
    
    const formatYear = (dObj) => {
        return String(dObj.getFullYear());
    };

    const snap = (targetStr) => {
        const closest = findClosestDate(dates, targetStr);
        if (!closest) return null;
        const idx = indexMap[closest];
        if (idx == null) return null;
        return { closest, idx };
    };
    
    // 정확한 날짜가 있으면 해당 인덱스 반환, 없으면 null
    const exactMatch = (targetStr) => {
        const idx = indexMap[targetStr];
        if (idx == null) return null;
        return { closest: targetStr, idx };
    };

    // 1W: 모든 일자 표시 (중복 없이)
    if (rangeKey === '1W' || diffDays <= 7) {
        // 이미 표시한 날짜 추적 (중복 방지)
        const shownDates = new Set();
        
        for (let i = 0; i < dates.length; i++) {
            const dateStr = dates[i];
            // 이미 같은 날짜가 표시되었으면 스킵
            if (shownDates.has(dateStr)) continue;
            shownDates.add(dateStr);
            
            const dObj = parseYYYYMMDD(dateStr);
            if (!dObj) continue;
            targets.push({ idx: i, label: formatMD(dObj) });
        }
        return dedupeAndSortTargets(targets);
    }

    // 1M: 1일, 15일, 마지막날 표시
    if (rangeKey === '1M' || (diffDays > 7 && diffDays <= 31)) {
        // 각 월의 1일, 15일, 마지막날 찾기
        const monthData = {}; // { 'YYYY-MM': { first: idx, fifteenth: idx, last: idx } }
        
        for (let i = 0; i < dates.length; i++) {
            const dObj = parseYYYYMMDD(dates[i]);
            if (!dObj) continue;
            
            const yearMonth = `${dObj.getFullYear()}-${String(dObj.getMonth() + 1).padStart(2, '0')}`;
            const day = dObj.getDate();
            
            if (!monthData[yearMonth]) {
                monthData[yearMonth] = { first: null, fifteenth: null, last: null };
            }
            
            // 1일 (또는 1일에 가장 가까운 날)
            if (day === 1) {
                monthData[yearMonth].first = { idx: i, date: dates[i] };
            } else if (!monthData[yearMonth].first && day <= 5) {
                monthData[yearMonth].first = { idx: i, date: dates[i] };
            }
            
            // 15일 (또는 15일에 가장 가까운 날)
            if (day === 15) {
                monthData[yearMonth].fifteenth = { idx: i, date: dates[i] };
            } else if (!monthData[yearMonth].fifteenth && day >= 13 && day <= 17) {
                monthData[yearMonth].fifteenth = { idx: i, date: dates[i] };
            }
            
            // 마지막날 (항상 최신 인덱스로 업데이트)
            monthData[yearMonth].last = { idx: i, date: dates[i] };
        }
        
        // 정렬된 월별로 타겟 추가
        const sortedMonths = Object.keys(monthData).sort();
        for (const ym of sortedMonths) {
            const data = monthData[ym];
            
            // 1일 추가
            if (data.first) {
                const dObj = parseYYYYMMDD(data.first.date);
                if (dObj) targets.push({ idx: data.first.idx, label: formatMD(dObj) });
            }
            
            // 15일 추가
            if (data.fifteenth) {
                const dObj = parseYYYYMMDD(data.fifteenth.date);
                if (dObj) targets.push({ idx: data.fifteenth.idx, label: formatMD(dObj) });
            }
            
            // 마지막날 추가
            if (data.last) {
                const dObj = parseYYYYMMDD(data.last.date);
                if (dObj) targets.push({ idx: data.last.idx, label: formatMD(dObj) });
            }
        }
        
        return dedupeAndSortTargets(targets);
    }

    // 3M: 각 월 표시
    if (rangeKey === '3M' || (diffDays > 31 && diffDays <= 93)) {
        // 각 월의 첫 번째 데이터 포인트 찾기
        const monthStarts = {};
        
        for (let i = 0; i < dates.length; i++) {
            const dObj = parseYYYYMMDD(dates[i]);
            if (!dObj) continue;
            const yearMonth = `${dObj.getFullYear()}-${String(dObj.getMonth()).padStart(2, '0')}`;
            // 같은 월의 첫 번째 인덱스만 저장
            if (!monthStarts[yearMonth]) {
                monthStarts[yearMonth] = { idx: i, date: dates[i] };
            }
        }
        
        // 월별 첫 번째 날짜들을 정렬하여 추가
        const sortedMonths = Object.keys(monthStarts).sort();
        for (const ym of sortedMonths) {
            const { idx, date } = monthStarts[ym];
            const dObj = parseYYYYMMDD(date);
            if (dObj) {
                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                targets.push({ idx, label: monthNames[dObj.getMonth()] });
            }
        }
        
        return dedupeAndSortTargets(targets);
    }

    // 1Y: 각 월 표시 (현재 월 포함 12개월)
    if (rangeKey === '1Y' || (diffDays > 93 && diffDays <= 365)) {
        // 각 월의 첫 번째 데이터 포인트 찾기
        const monthStarts = {};
        
        for (let i = 0; i < dates.length; i++) {
            const dObj = parseYYYYMMDD(dates[i]);
            if (!dObj) continue;
            const yearMonth = `${dObj.getFullYear()}-${String(dObj.getMonth()).padStart(2, '0')}`;
            // 같은 월의 첫 번째 인덱스만 저장
            if (!monthStarts[yearMonth]) {
                monthStarts[yearMonth] = { idx: i, date: dates[i] };
            }
        }
        
        // 월별 첫 번째 날짜들을 정렬하여 추가
        const sortedMonths = Object.keys(monthStarts).sort();
        for (const ym of sortedMonths) {
            const { idx, date } = monthStarts[ym];
            const dObj = parseYYYYMMDD(date);
            if (dObj) {
                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                targets.push({ idx, label: monthNames[dObj.getMonth()] });
            }
        }
        
        return dedupeAndSortTargets(targets);
    }

    // 1Y 초과 ~ 2Y 이하: 연도와 홀수 월만 표시
    if (diffDays > 365 && diffDays <= 730) {
        const monthStarts = {};
        
        for (let i = 0; i < dates.length; i++) {
            const dObj = parseYYYYMMDD(dates[i]);
            if (!dObj) continue;
            const month = dObj.getMonth() + 1; // 1-12
            // 홀수 월만 (1, 3, 5, 7, 9, 11)
            if (month % 2 === 1) {
                const yearMonth = `${dObj.getFullYear()}-${String(dObj.getMonth()).padStart(2, '0')}`;
                if (!monthStarts[yearMonth]) {
                    monthStarts[yearMonth] = { idx: i, date: dates[i] };
                }
            }
        }
        
        const sortedMonths = Object.keys(monthStarts).sort();
        for (const ym of sortedMonths) {
            const { idx, date } = monthStarts[ym];
            const dObj = parseYYYYMMDD(date);
            if (dObj) {
                targets.push({ idx, label: formatYM(dObj) });
            }
        }
        
        return dedupeAndSortTargets(targets);
    }

    // 2Y 초과: 연도만 표시
    if (diffDays > 730) {
        const yearStarts = {};
        
        for (let i = 0; i < dates.length; i++) {
            const dObj = parseYYYYMMDD(dates[i]);
            if (!dObj) continue;
            const year = dObj.getFullYear();
            // 각 연도의 첫 번째 데이터만 저장
            if (!yearStarts[year]) {
                yearStarts[year] = { idx: i, date: dates[i] };
            }
        }
        
        const sortedYears = Object.keys(yearStarts).sort();
        for (const year of sortedYears) {
            const { idx, date } = yearStarts[year];
            const dObj = parseYYYYMMDD(date);
            if (dObj) {
                targets.push({ idx, label: formatYear(dObj) });
            }
        }
        
        return dedupeAndSortTargets(targets);
    }

    return [];
}

// Expose to window for backwards compatibility
window.formatDateForAPI = formatDateForAPI;
window.formatInterestDateForAPI = formatInterestDateForAPI;
window.toYYYYMMDD = toYYYYMMDD;
window.parseYYYYMMDD = parseYYYYMMDD;
window.daysInMonth = daysInMonth;
window.makeDateSafe = makeDateSafe;
window.weekdayKoShort = weekdayKoShort;
window.formatGDPNumber = formatGDPNumber;
window.formatGDPChange = formatGDPChange;
window.formatGDPNumberWithEasyUnit = formatGDPNumberWithEasyUnit;
window.formatTradeNumberWithEasyUnit = formatTradeNumberWithEasyUnit;
window.animateValue = animateValue;
window.parseInflationDate = parseInflationDate;
window.compareInflationDates = compareInflationDates;
window.formatInflationPeriodLabel = formatInflationPeriodLabel;
window.getInflationMetricLabel = getInflationMetricLabel;
window.calculateInflationIndexStats = calculateInflationIndexStats;
window.buildYearLabel = buildYearLabel;
window.escapeHtml = escapeHtml;

// New shared functions
window.parseInterestDate = parseInterestDate;
window.formatInterestDate = formatInterestDate;
window.compareInterestDates = compareInterestDates;
window.getSvgViewBoxSize = getSvgViewBoxSize;
window.fillMissingDates = fillMissingDates;
window.findClosestDate = findClosestDate;
window.dedupeAndSortTargets = dedupeAndSortTargets;
window.buildXAxisTargets = buildXAxisTargets;

console.log('✅ AAL Helpers loaded');

