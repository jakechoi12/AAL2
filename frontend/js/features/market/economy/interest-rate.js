/**
 * AAL Application - Interest Rate Module
 * 금리 관련 기능 모듈
 * 
 * 담당 패널: #interest-rate-panel
 * 주요 기능: 국내/국제 금리 차트, 국가별 금리 비교
 */

// ============================================================
// MODULE MARKER - 이 모듈이 로드되었음을 표시
// ============================================================
window.interestRateModuleLoaded = true;

// ============================================================
// 전역 변수 (금리 모듈 전용)
// ============================================================
// 단일 국가용 데이터 (하위 호환성)
let interestRateData = {};
let interestCycle = 'M'; // Current cycle (A, M, Q)
let interestYAxisRange = { min: 0, max: 0 };

// International Interest Rates Variables
let activeInterestCountries = [];
let interestCountryData = {};
let interestCountryMapping = {};
let interestCountryListLoaded = false;

// 이벤트 핸들러 저장 (cleanup용)
let interestMouseMoveHandler = null;
let interestMouseLeaveHandler = null;

// 국가 정보 매핑 (한국어명 → {englishName, color}) - 26개 국가 고유 색상
const interestCountryInfoMap = [
    { keywords: ['호주', 'aus', 'australia'], englishName: 'Australia', color: 'var(--c-interest-aus)' },
    { keywords: ['브라질', 'bra', 'brazil'], englishName: 'Brazil', color: 'var(--c-interest-bra)' },
    { keywords: ['캐나다', 'can', 'canada'], englishName: 'Canada', color: 'var(--c-interest-can)' },
    { keywords: ['스위스', 'che', 'switzerland'], englishName: 'Switzerland', color: 'var(--c-interest-che)' },
    { keywords: ['칠레', 'chl', 'chile'], englishName: 'Chile', color: 'var(--c-interest-chl)' },
    { keywords: ['중국', 'chn', 'china'], englishName: 'China', color: 'var(--c-interest-chn)' },
    { keywords: ['체코', 'cze', 'czech'], englishName: 'Czech Republic', color: 'var(--c-interest-cze)' },
    { keywords: ['덴마크', 'dnk', 'denmark'], englishName: 'Denmark', color: 'var(--c-interest-dnk)' },
    { keywords: ['영국', 'gbr', 'uk', 'united kingdom'], englishName: 'UK', color: 'var(--c-interest-gbr)' },
    { keywords: ['헝가리', 'hun', 'hungary'], englishName: 'Hungary', color: 'var(--c-interest-hun)' },
    { keywords: ['인도네시아', 'idn', 'indonesia'], englishName: 'Indonesia', color: 'var(--c-interest-idn)' },
    { keywords: ['이스라엘', 'isr', 'israel'], englishName: 'Israel', color: 'var(--c-interest-isr)' },
    { keywords: ['인도', 'ind', 'india'], englishName: 'India', color: 'var(--c-interest-ind)' },
    { keywords: ['아이슬란드', 'isl', 'iceland'], englishName: 'Iceland', color: 'var(--c-interest-isl)' },
    { keywords: ['일본', 'jpn', 'japan'], englishName: 'Japan', color: 'var(--c-interest-jpn)' },
    { keywords: ['한국', 'kor', 'korea'], englishName: 'Korea', color: 'var(--c-interest-kor)' },
    { keywords: ['멕시코', 'mex', 'mexico'], englishName: 'Mexico', color: 'var(--c-interest-mex)' },
    { keywords: ['노르웨이', 'nor', 'norway'], englishName: 'Norway', color: 'var(--c-interest-nor)' },
    { keywords: ['뉴질랜드', 'nzl', 'zealand'], englishName: 'New Zealand', color: 'var(--c-interest-nzl)' },
    { keywords: ['폴란드', 'pol', 'poland'], englishName: 'Poland', color: 'var(--c-interest-pol)' },
    { keywords: ['러시아', 'rus', 'russia'], englishName: 'Russia', color: 'var(--c-interest-rus)' },
    { keywords: ['스웨덴', 'swe', 'sweden'], englishName: 'Sweden', color: 'var(--c-interest-swe)' },
    { keywords: ['튀르키예', 'tur', 'turkey'], englishName: 'Turkey', color: 'var(--c-interest-tur)' },
    { keywords: ['미국', 'usa', 'us ', 'united states'], englishName: 'USA', color: 'var(--c-interest-usa)' },
    { keywords: ['유로', 'eur', 'eurozone', 'euro area'], englishName: 'Eurozone', color: 'var(--c-interest-eur)' },
    { keywords: ['남아프리카', 'zaf', 'south africa'], englishName: 'South Africa', color: 'var(--c-interest-zaf)' },
    { keywords: ['독일', 'deu', 'germany'], englishName: 'Germany', color: 'var(--c-interest-deu)' },
    { keywords: ['프랑스', 'fra', 'france'], englishName: 'France', color: 'var(--c-interest-fra)' },
    { keywords: ['이탈리아', 'ita', 'italy'], englishName: 'Italy', color: 'var(--c-interest-ita)' },
    { keywords: ['스페인', 'esp', 'spain'], englishName: 'Spain', color: 'var(--c-interest-esp)' }
];

// ============================================================
// INITIALIZATION
// ============================================================

function initInterestRates() {
    // Initialize date inputs for interest rates
    const startDateInput = document.getElementById('interest-start-date');
    const endDateInput = document.getElementById('interest-end-date');
    
    if (startDateInput && endDateInput) {
        const end = new Date();
        const start = new Date();
        // 월별 기본값: 현재 월을 포함해서 과거 12개월
        start.setMonth(end.getMonth() - 11); // 12개월 (현재월 포함)
        start.setDate(1); // 해당 월의 1일로 설정
        
        // YYYY-MM 형식으로 설정 (month input 타입)
        const startYear = start.getFullYear();
        const startMonth = String(start.getMonth() + 1).padStart(2, '0');
        const endYear = end.getFullYear();
        const endMonth = String(end.getMonth() + 1).padStart(2, '0');
        
        startDateInput.value = `${startYear}-${startMonth}`;
        endDateInput.value = `${endYear}-${endMonth}`;
        startDateInput.max = endDateInput.value;
        endDateInput.max = endDateInput.value;
        
        // Add event listeners for date inputs
        const handleDateInputChange = (inputEl) => {
            // Validate and format YYYY-MM input
            let value = inputEl.value.trim();
            // Allow partial input while typing
            if (value.match(/^\d{4}-\d{2}$/)) {
                // Valid format
                if (validateInterestDateRange()) {
                    if (activeInterestCountries.length > 0) {
                        fetchInterestRateDataMulti();
                    } else {
                        fetchInterestRateData();
                    }
                }
            }
        };
        
        startDateInput.addEventListener('change', () => handleDateInputChange(startDateInput));
        endDateInput.addEventListener('change', () => handleDateInputChange(endDateInput));
        
        // Add input formatting for text inputs
        const formatDateInput = (e) => {
            let value = e.target.value.replace(/[^\d-]/g, '');
            // Auto-add hyphen after year
            if (value.length === 4 && !value.includes('-')) {
                value = value + '-';
            }
            // Limit to 7 chars (YYYY-MM)
            if (value.length > 7) {
                value = value.substring(0, 7);
            }
            e.target.value = value;
        };
        
        startDateInput.addEventListener('input', formatDateInput);
        endDateInput.addEventListener('input', formatDateInput);
    }
    
    // Initialize cycle buttons (M, Q)
    // 기존 이벤트 리스너 제거 후 새로 추가 (중복 방지)
    document.querySelectorAll('.interest-cycle-btn').forEach(btn => {
        // 기존 클릭 이벤트 제거를 위해 클론 후 재추가
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);

        newBtn.addEventListener('click', function() {
            // 모든 버튼에서 active 제거
            document.querySelectorAll('.interest-cycle-btn').forEach(b => b.classList.remove('active'));
            // 클릭한 버튼에 active 추가
            this.classList.add('active');
            // interestCycle 변수 업데이트
            interestCycle = this.getAttribute('data-cycle');
            
            console.log('Cycle changed to:', interestCycle);
            
            // 데이터 재조회 (날짜는 변경하지 않음)
            if (activeInterestCountries.length > 0) {
                fetchInterestRateDataMulti();
            } else {
                fetchInterestRateData();
            }
        });
    });
    
    // Load country list and initialize chips
    fetchInterestCountryList().then(() => {
        // Initial data fetch (다중 국가)
        if (activeInterestCountries.length > 0) {
            fetchInterestRateDataMulti();
        } else {
            // 국가 리스트 로드 실패 시 기존 단일 국가 방식 사용
            fetchInterestRateData();
        }
    }).catch(err => {
        console.error('Failed to load country list, using single country mode:', err);
        fetchInterestRateData();
    });
    window.interestDataLoaded = true;
}

// ============================================================
// DATE VALIDATION
// ============================================================

function validateInterestDateRange() {
    const startDateInput = document.getElementById('interest-start-date');
    const endDateInput = document.getElementById('interest-end-date');
    
    if (!startDateInput || !endDateInput) return false;
    
    // Handle YYYY-MM format for text inputs
    const startValue = startDateInput.value.trim();
    const endValue = endDateInput.value.trim();
    
    if (!startValue.match(/^\d{4}-\d{2}$/) || !endValue.match(/^\d{4}-\d{2}$/)) {
        return false;
    }
    
    const startDate = new Date(startValue + '-01');
    const endDate = new Date(endValue + '-01');
    
    if (startDate > endDate) {
        alert('시작일은 종료일보다 앞서야 합니다.');
        return false;
    }
    
    return true;
}

// ============================================================
// DATA FETCHING - SINGLE COUNTRY (Legacy)
// ============================================================

async function fetchInterestRateData() {
    if (!validateInterestDateRange()) return;
    
    const startDateInputEl = document.getElementById('interest-start-date');
    const endDateInputEl = document.getElementById('interest-end-date');
    
    if (!startDateInputEl || !endDateInputEl) return;
    
    // 연도별(A)인 경우 년도 값을 날짜로 변환
    let startDate, endDate;
    if (interestCycle === 'A' && startDateInputEl.type === 'number') {
        // 년도만 선택한 경우, 해당 년도의 1월 1일 ~ 12월 31일로 변환
        const startYear = parseInt(startDateInputEl.value);
        const endYear = parseInt(endDateInputEl.value);
        startDate = `${startYear}0101`;
        endDate = `${endYear}1231`;
    } else {
        // YYYY-MM 형식을 YYYYMM01 형식으로 변환 (API는 YYYYMMDD 형식 기대)
        startDate = formatInterestDateForAPI(startDateInputEl.value);
        endDate = formatInterestDateForAPI(endDateInputEl.value);
    }
    
    const chartContainer = document.getElementById('interest-chart-container');
    if (chartContainer) {
        chartContainer.style.opacity = '0.5';
    }
    
    try {
        // 연도별(A)일 때는 일별(D) 데이터를 가져와서 연도별로 변환
        const apiCycle = interestCycle === 'A' ? 'D' : interestCycle;
        
        const url = `${API_BASE}/market/indices?type=interest&itemCode=BASE_RATE&startDate=${startDate}&endDate=${endDate}&cycle=${apiCycle}`;
        console.log('Fetching interest rate data from:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API response error:', {
                status: response.status,
                statusText: response.statusText,
                url: url,
                error: errorText
            });
            alert(`금리 데이터 조회 실패 (${response.status}): ${response.statusText}\nURL: ${url}`);
            return;
        }
        
        const json = await response.json();
        
        if (json.error) {
            console.error('Interest rate API error:', json.error);
            alert('금리 데이터 조회 중 오류가 발생했습니다: ' + json.error);
            return;
        }
        
        console.log('API response received:', {
            rowCount: json.StatisticSearch?.row?.length || 0,
            totalCount: json.StatisticSearch?.list_total_count || 0
        });
        
        // Process data
        processInterestRateData(json);
        
        // Fetch statistics (연도별일 때는 일별 데이터로 통계 계산)
        const statsCycle = interestCycle;
        const statsUrl = `${API_BASE}/market/indices/stats?type=interest&itemCode=BASE_RATE&startDate=${startDate}&endDate=${endDate}&cycle=${statsCycle}`;
        console.log('Fetching statistics from:', statsUrl);
        
        const statsResponse = await fetch(statsUrl);
        
        if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            if (!statsData.error) {
                updateInterestChartHeader(statsData);
            }
        } else {
            console.warn('Statistics API error:', statsResponse.status, statsResponse.statusText);
        }
        
    } catch (err) {
        console.error('Failed to fetch interest rate data:', err);
        console.error('Error details:', {
            message: err.message,
            stack: err.stack,
            name: err.name
        });
        alert('금리 데이터 조회 중 오류가 발생했습니다: ' + err.message);
    } finally {
        if (chartContainer) {
            chartContainer.style.opacity = '1';
        }
    }
}

// ============================================================
// DATA FETCHING - MULTI COUNTRY (International)
// ============================================================

async function fetchInterestCountryList() {
    if (interestCountryListLoaded && Object.keys(interestCountryMapping).length > 0) {
        return interestCountryMapping;
    }
    
    try {
        const url = `${API_BASE}/market/categories?category=interest-international`;
        const response = await fetch(url);
        
        if (response.ok) {
            const data = await response.json();
            if (data.items && Object.keys(data.items).length > 0) {
                interestCountryMapping = data.items;
                interestCountryListLoaded = true;
                
                // 기본으로 한국만 선택
                const itemCodes = Object.keys(interestCountryMapping);
                const defaultCodes = [];
                
                // 한국 찾기 (KOR, KOREA, 한국 등)
                const korCode = itemCodes.find(code => {
                    const name = interestCountryMapping[code].name;
                    return name.includes('한국') || name.includes('KOR') || code.includes('KOR');
                });
                if (korCode) defaultCodes.push(korCode);
                
                // 최소 1개는 선택
                if (defaultCodes.length === 0 && itemCodes.length > 0) {
                    defaultCodes.push(itemCodes[0]);
                }
                
                activeInterestCountries = defaultCodes;
                initInterestCountryChips();
                
                return interestCountryMapping;
            }
        }
        
        throw new Error('Failed to fetch country list from categories endpoint');
        
    } catch (err) {
        console.error('Failed to fetch interest country list:', err);
        throw err;
    }
}

function initInterestCountryChips() {
    const chipsContainer = document.getElementById('interest-country-chips');
    if (!chipsContainer) return;
    
    chipsContainer.innerHTML = '';
    
    const itemCodes = Object.keys(interestCountryMapping);
    if (itemCodes.length === 0) {
        chipsContainer.innerHTML = '<span style="color: var(--text-sub); font-size: 0.8rem;">국가 리스트 로딩 중...</span>';
        return;
    }
    
    itemCodes.forEach(itemCode => {
        const countryInfo = interestCountryMapping[itemCode];
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.setAttribute('data-item-code', itemCode);
        chip.setAttribute('title', countryInfo.name);
        
        const isActive = activeInterestCountries.includes(itemCode);
        if (isActive) {
            chip.classList.add('active');
        }
        
        // 국가별 그래프 색상 가져오기
        const countryColor = getInterestCountryColor(itemCode);
        
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
        // 국가 이름을 영어로 표시
        const englishName = getInterestCountryNameEnglish(countryInfo.name, itemCode);
        chip.appendChild(document.createTextNode(englishName));
        
        chip.addEventListener('click', () => toggleInterestCountry(itemCode));
        
        chipsContainer.appendChild(chip);
    });
}

function toggleInterestCountry(itemCode) {
    const index = activeInterestCountries.indexOf(itemCode);
    
    // 토글: 있으면 제거, 없으면 추가
    if (index === -1) {
        activeInterestCountries.push(itemCode);
    } else {
        activeInterestCountries.splice(index, 1);
    }
    
    // UI 업데이트
    const chip = document.querySelector(`#interest-country-chips [data-item-code="${itemCode}"]`);
    if (chip) {
        const chipDot = chip.querySelector('.chip-dot');
        const isActive = activeInterestCountries.includes(itemCode);
        
        if (isActive) {
            chip.classList.add('active');
            // active 상태일 때만 색상 적용
            const countryColor = getInterestCountryColor(itemCode);
            if (chipDot) {
                chipDot.style.background = countryColor;
            }
            // chip의 배경색과 테두리 색상도 설정
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
            chip.classList.remove('active');
            // 비활성화 시 색상 제거
            if (chipDot) {
                chipDot.style.background = 'currentColor';
            }
            // chip 스타일 초기화
            chip.style.borderColor = '';
            chip.style.color = '';
            chip.style.background = '';
        }
    }
    
    // 데이터 재조회 (또는 그래프 업데이트)
    if (activeInterestCountries.length === 0) {
        // 모든 국가가 해제되면 그래프 비우기
        updateInterestChartMulti();
    } else if (validateInterestDateRange()) {
        fetchInterestRateDataMulti();
    }
}

async function fetchInterestRateDataMulti() {
    if (!validateInterestDateRange()) return;
    
    const startDateInputEl = document.getElementById('interest-start-date');
    const endDateInputEl = document.getElementById('interest-end-date');
    
    if (!startDateInputEl || !endDateInputEl) return;
    
    if (activeInterestCountries.length === 0) {
        // 모든 국가가 해제되면 그래프 비우기
        updateInterestChartMulti();
        return;
    }
    
    const startDate = formatInterestDateForAPI(startDateInputEl.value);
    const endDate = formatInterestDateForAPI(endDateInputEl.value);
    // 백엔드에는 항상 월별(M)로 요청하고, 프론트엔드에서 분기별로 그룹화
    const cycle = 'M'; // 항상 월별 데이터를 받아서 프론트엔드에서 처리
    
    const chartContainer = document.getElementById('interest-chart-container');
    if (chartContainer) {
        chartContainer.style.opacity = '0.5';
    }
    
    try {
        // 각 국가별로 API 호출
        const fetchPromises = activeInterestCountries.map(async (itemCode) => {
            const url = `${API_BASE}/market/indices?type=interest-international&itemCode=${itemCode}&startDate=${startDate}&endDate=${endDate}&cycle=${cycle}`;
            
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
        processInterestRateDataMulti(results);
        
    } catch (err) {
        console.error('Failed to fetch interest rate data:', err);
        alert('금리 데이터 조회 중 오류가 발생했습니다: ' + err.message);
    } finally {
        if (chartContainer) {
            chartContainer.style.opacity = '1';
        }
    }
}

// ============================================================
// DATA PROCESSING
// ============================================================

function processInterestRateDataMulti(results) {
    interestCountryData = {};
    
    // 선택한 기간 가져오기
    const startDateInputEl = document.getElementById('interest-start-date');
    const endDateInputEl = document.getElementById('interest-end-date');
    const startDateStr = startDateInputEl ? formatInterestDateForAPI(startDateInputEl.value) : '';
    const endDateStr = endDateInputEl ? formatInterestDateForAPI(endDateInputEl.value) : '';
    
    // 월별 데이터를 분기별로 그룹화하는 함수
    function groupMonthlyToQuarterly(monthlyData) {
        const quarterlyMap = new Map();
        
        monthlyData.forEach(item => {
            if (item.date && item.date.length === 6) {
                // YYYYMM 형식
                const year = item.date.substring(0, 4);
                const month = parseInt(item.date.substring(4, 6), 10);
                let quarter;
                
                if (month >= 1 && month <= 3) quarter = 1;
                else if (month >= 4 && month <= 6) quarter = 2;
                else if (month >= 7 && month <= 9) quarter = 3;
                else if (month >= 10 && month <= 12) quarter = 4;
                else return; // 유효하지 않은 월
                
                const quarterKey = `${year}Q${quarter}`;
                
                if (!quarterlyMap.has(quarterKey)) {
                    quarterlyMap.set(quarterKey, []);
                }
                quarterlyMap.get(quarterKey).push(item.value);
            }
        });
        
        // 각 분기의 평균값 계산
        const quarterlyData = [];
        quarterlyMap.forEach((values, quarterKey) => {
            const avgValue = values.reduce((sum, v) => sum + v, 0) / values.length;
            quarterlyData.push({
                date: quarterKey,
                value: avgValue
            });
        });
        
        return quarterlyData;
    }
    
    results.forEach(({ itemCode, data }) => {
        if (data.error || !data.StatisticSearch) {
            console.error(`Error processing ${itemCode}:`, data.error || 'Invalid data format');
            return;
        }
        
        const rows = data.StatisticSearch.row || [];
        let values = rows.map(row => ({
            date: row.TIME,
            value: parseFloat(row.DATA_VALUE)
        })).filter(item => !isNaN(item.value) && item.value > 0);
        
        // 분기별 선택 시 월별 데이터를 분기별로 그룹화
        if (interestCycle === 'Q') {
            // 먼저 월별 데이터를 분기별로 그룹화
            values = groupMonthlyToQuarterly(values);
        }
        
        // 선택한 기간의 데이터만 필터링
        if (startDateStr && endDateStr) {
            // startDateStr과 endDateStr은 YYYYMM01 형식이므로 YYYYMM만 추출
            const startMonth = startDateStr.substring(0, 6); // YYYYMM
            const endMonth = endDateStr.substring(0, 6); // YYYYMM
            
            values = values.filter(item => {
                if (!item.date) return false;
                
                let itemDateStr = item.date;
                
                // YYYYQn 형식을 YYYYMM으로 변환하여 비교
                if (itemDateStr.includes('Q')) {
                    const year = itemDateStr.substring(0, 4);
                    const quarter = parseInt(itemDateStr.substring(5), 10);
                    const month = (quarter - 1) * 3 + 1; // 분기의 첫 번째 월
                    itemDateStr = `${year}${String(month).padStart(2, '0')}`;
                } else if (itemDateStr.length === 8) {
                    // YYYYMMDD 형식인 경우 YYYYMM만 추출
                    itemDateStr = itemDateStr.substring(0, 6);
                }
                
                // YYYYMM 형식으로 비교
                return itemDateStr >= startMonth && itemDateStr <= endMonth;
            });
        }
        
        // 날짜 정렬 (YYYYMM 또는 YYYYQn 형식 지원)
        values.sort((a, b) => {
            return compareInterestDates(a.date, b.date, interestCycle || 'M');
        });
        
        interestCountryData[itemCode] = values;
    });
    
    console.log('Processed interest rate data (multi):', {
        countries: Object.keys(interestCountryData),
        cycle: interestCycle,
        dateRange: { start: startDateStr, end: endDateStr },
        dataCounts: Object.fromEntries(
            Object.entries(interestCountryData).map(([code, data]) => [code, data.length])
        )
    });
    
    updateInterestChartMulti();
}

function processInterestRateData(data) {
    if (!data || !data.StatisticSearch) {
        console.error('Invalid interest rate data format');
        return;
    }
    
    const rows = data.StatisticSearch.row || [];
    let values = rows.map(row => ({
        date: row.TIME,
        value: parseFloat(row.DATA_VALUE)
    })).filter(item => !isNaN(item.value) && item.value > 0);
    
    // 주기에 따라 날짜 정렬
    values.sort((a, b) => compareInterestDates(a.date, b.date, interestCycle));
    
    interestRateData = values;
    
    // 디버깅: 처리된 데이터 확인
    console.log('Processed interest rate data:', {
        cycle: interestCycle,
        count: values.length,
        dates: values.map(v => v.date),
        dateRange: values.length > 0 ? {
            start: values[0].date,
            end: values[values.length - 1].date
        } : null
    });
    
    updateInterestChart();
}

// 주기별 데이터 개수 계산 함수
function getInterestDataUnitCount(data, cycle) {
    if (!data || data.length === 0) return 0;
    
    if (cycle === 'M') {
        // 월별: 고유한 월 개수 계산
        const uniqueMonths = new Set();
        data.forEach(item => {
            if (item.date && item.date.length === 6) {
                uniqueMonths.add(item.date); // YYYYMM 형식
            }
        });
        return uniqueMonths.size;
    } else if (cycle === 'Q') {
        // 분기별: 고유한 분기 개수 계산
        const uniqueQuarters = new Set();
        data.forEach(item => {
            if (item.date && item.date.includes('Q')) {
                uniqueQuarters.add(item.date); // YYYYQn 형식
            }
        });
        return uniqueQuarters.size;
    } else if (cycle === 'A') {
        // 연도별: 고유한 연도 개수 계산
        const uniqueYears = new Set();
        data.forEach(item => {
            if (item.date && item.date.length === 4) {
                uniqueYears.add(item.date); // YYYY 형식
            }
        });
        return uniqueYears.size;
    }
    
    return data.length;
}

// ============================================================
// COUNTRY INFO HELPERS
// ============================================================

// itemCode에서 국가 코드 추출 (예: "AUS_IR" -> "aus", "0000001" -> null)
function extractCountryCodeFromItemCode(itemCode) {
    if (!itemCode) return null;
    const code = itemCode.toLowerCase();
    // 패턴: XXX_IR, XXX_RATE 등에서 국가코드 추출
    const match = code.match(/^([a-z]{2,3})_/);
    if (match) return match[1];
    // 국가코드가 직접 포함된 경우 (예: 'KOR', 'USA')
    const countryPattern = code.match(/^([a-z]{2,3})$/);
    if (countryPattern) return countryPattern[1];
    return null;
}

// 국가 정보 찾기 (한국어명 또는 itemCode 기반)
function findInterestCountryInfo(koreanNameOrItemCode, itemCode = null) {
    if (!koreanNameOrItemCode && !itemCode) return null;
    
    // 1. itemCode에서 국가 코드 추출하여 매칭 시도
    const countryCode = extractCountryCodeFromItemCode(itemCode) || extractCountryCodeFromItemCode(koreanNameOrItemCode);
    if (countryCode) {
        for (const info of interestCountryInfoMap) {
            if (info.keywords.some(keyword => keyword.toLowerCase() === countryCode)) {
                return info;
            }
        }
    }
    
    // 2. 이름 기반 매칭
    const name = (koreanNameOrItemCode || '').toLowerCase();
    for (const info of interestCountryInfoMap) {
        if (info.keywords.some(keyword => name.includes(keyword.toLowerCase()))) {
            return info;
        }
    }
    
    return null;
}

// 국가 이름을 영어로 변환하는 함수
function getInterestCountryNameEnglish(koreanName, itemCode = null) {
    const info = findInterestCountryInfo(koreanName, itemCode);
    return info ? info.englishName : koreanName;
}

// 국가별 색상 매핑 (item_code → CSS 변수)
function getInterestCountryColor(itemCode) {
    const countryInfo = interestCountryMapping[itemCode];
    
    // 1. itemCode로 직접 국가 코드 추출하여 색상 찾기
    const info = findInterestCountryInfo(countryInfo?.name, itemCode);
    if (info) {
        return info.color;
    }
    
    // 2. 매핑되지 않은 경우 기본 색상 (item_code 기반 해시)
    const colors = [
        'var(--c-interest-kor)', 'var(--c-interest-usa)', 'var(--c-interest-jpn)',
        'var(--c-interest-chn)', 'var(--c-interest-gbr)', 'var(--c-interest-deu)',
        'var(--c-interest-fra)', 'var(--c-interest-ita)', 'var(--c-interest-esp)',
        'var(--c-interest-can)', 'var(--c-interest-aus)', 'var(--c-interest-nzl)'
    ];
    let hash = 0;
    for (let i = 0; i < itemCode.length; i++) {
        hash = ((hash << 5) - hash) + itemCode.charCodeAt(i);
        hash = hash & hash;
    }
    return colors[Math.abs(hash) % colors.length];
}

// ============================================================
// CHART RENDERING - MULTI COUNTRY
// ============================================================

function updateInterestChartMulti() {
    const svg = document.getElementById('interest-chart-svg');
    const pointsGroup = document.getElementById('interest-data-points');
    
    if (!svg || !pointsGroup) return;
    
    // 모든 국가 path 정리
    Object.keys(interestCountryMapping).forEach(itemCode => {
        let path = document.getElementById(`path-interest-${itemCode}`);
        if (!path) {
            // path 요소 생성
            path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.id = `path-interest-${itemCode}`;
            path.classList.add('chart-path');
            path.setAttribute('stroke', getInterestCountryColor(itemCode));
            path.setAttribute('stroke-width', '2.5');
            path.setAttribute('fill', 'none');
            svg.insertBefore(path, pointsGroup);
        }
        path.setAttribute('d', '');
        path.classList.remove('visible');
    });
    
    // 활성화된 국가가 없으면 그래프 비우기
    if (activeInterestCountries.length === 0) {
        renderInterestYAxisLabelsMulti([]);
        renderInterestXAxisLabelsMulti([]);
        pointsGroup.innerHTML = '';
        return;
    }
    
    // 모든 국가 데이터 병합하여 공통 날짜 목록 생성
    const allDates = new Set();
    Object.values(interestCountryData).forEach(data => {
        data.forEach(item => allDates.add(item.date));
    });
    const sortedDates = Array.from(allDates).sort((a, b) => {
        return compareInterestDates(a, b, interestCycle || 'M');
    });
    
    if (sortedDates.length === 0) {
        renderInterestYAxisLabelsMulti([]);
        renderInterestXAxisLabelsMulti([]);
        return;
    }
    
    // Y축 범위 계산 (모든 국가 데이터 기반)
    const allValues = [];
    Object.values(interestCountryData).forEach(data => {
        data.forEach(item => allValues.push(item.value));
    });
    
    if (allValues.length === 0) {
        renderInterestYAxisLabelsMulti([]);
        renderInterestXAxisLabelsMulti(sortedDates);
        return;
    }
    
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const range = maxValue - minValue || 1;
    const paddingPercent = range < 10 ? 0.05 : 0.03;
    interestYAxisRange = {
        min: Math.max(0, minValue - range * paddingPercent),
        max: maxValue + range * paddingPercent
    };
    
    // Y축 라벨 렌더링
    renderInterestYAxisLabelsMulti(sortedDates);
    
    // 각 국가별 path 렌더링
    activeInterestCountries.forEach(itemCode => {
        const data = interestCountryData[itemCode];
        if (!data || data.length === 0) return;
        
        let path = document.getElementById(`path-interest-${itemCode}`);
        if (!path) {
            path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.id = `path-interest-${itemCode}`;
            path.classList.add('chart-path');
            path.setAttribute('stroke', getInterestCountryColor(itemCode));
            path.setAttribute('stroke-width', '2.5');
            path.setAttribute('fill', 'none');
            svg.insertBefore(path, pointsGroup);
        }
        
        // 데이터를 공통 날짜 기준으로 정렬
        const sortedData = sortedDates.map(date => {
            const found = data.find(item => item.date === date);
            return found || { date, value: null };
        }).filter(item => item.value !== null);
        
        if (sortedData.length > 0) {
            const pathData = generateInterestSVGPathMulti(sortedData);
            path.setAttribute('d', pathData);
            path.classList.add('visible');
        }
    });
    
    // 데이터 포인트 렌더링
    renderInterestDataPointsMulti(sortedDates);
    
    // X축 라벨 렌더링
    renderInterestXAxisLabelsMulti(sortedDates);
    
    // 인터랙티브 기능 설정
    setupInterestChartInteractivityMulti();
    
    // 통계 헤더 업데이트
    updateInterestChartHeaderMulti();
}

function generateInterestSVGPathMulti(data) {
    if (!data || data.length === 0) return '';
    
    const svg = document.getElementById('interest-chart-svg');
    if (!svg) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const minValue = interestYAxisRange.min;
    const maxValue = interestYAxisRange.max;
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

function renderInterestYAxisLabelsMulti(sortedDates) {
    const yAxisGroup = document.getElementById('interest-y-axis-labels');
    if (!yAxisGroup) return;
    
    yAxisGroup.innerHTML = '';
    
    const minValue = interestYAxisRange.min;
    const maxValue = interestYAxisRange.max;
    const steps = 5;
    
    for (let i = 0; i <= steps; i++) {
        const value = maxValue - (i / steps) * (maxValue - minValue);
        const y = 20 + (i / steps) * 330; // 350 - 20 = 330 (차트 높이)
        
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', '30');
        label.setAttribute('y', y);
        label.setAttribute('class', 'chart-yaxis-label');
        label.setAttribute('text-anchor', 'end');
        label.setAttribute('dominant-baseline', 'middle');
        label.textContent = value.toFixed(2) + '%';
        
        yAxisGroup.appendChild(label);
    }
}

function renderInterestXAxisLabelsMulti(sortedDates) {
    const xAxisGroup = document.getElementById('interest-x-axis-labels');
    if (!xAxisGroup || !sortedDates || sortedDates.length === 0) return;
    
    xAxisGroup.innerHTML = '';
    
    const svg = document.getElementById('interest-chart-svg');
    if (!svg) return;
    
    const { width } = getSvgViewBoxSize(svg);
    const padding = { left: 40, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    
    // 기간 계산 (월 단위)
    const totalMonths = sortedDates.length;
    
    // 기간별 라벨 표시 규칙:
    // 1Y 이내 (≤12개월): YY.MM 모든 월 표시
    // 1Y~2Y (13~24개월): YY.MM 홀수 월만 표시
    // 2Y 초과 (>24개월): YYYY 연도만 표시
    
    const targets = [];
    
    if (totalMonths <= 12) {
        // 1Y 이내: 모든 월 표시 (YY.MM)
        sortedDates.forEach((date, index) => {
            targets.push({ index, date });
        });
    } else if (totalMonths <= 24) {
        // 1Y~2Y: 홀수 월만 표시 (YY.MM)
        sortedDates.forEach((date, index) => {
            if (date.length === 6) {
                const month = parseInt(date.substring(4, 6), 10);
                // 홀수 월만 (1, 3, 5, 7, 9, 11)
                if (month % 2 === 1) {
                    targets.push({ index, date });
                }
            }
        });
        // 첫 번째와 마지막 추가 (중복 방지)
        if (targets.length === 0 || targets[0].index !== 0) {
            targets.unshift({ index: 0, date: sortedDates[0] });
        }
        if (targets[targets.length - 1].index !== sortedDates.length - 1) {
            targets.push({ index: sortedDates.length - 1, date: sortedDates[sortedDates.length - 1] });
        }
    } else {
        // 2Y 초과: 연도만 표시 (YYYY)
        const seenYears = new Set();
        sortedDates.forEach((date, index) => {
            if (date.length >= 4) {
                const year = date.substring(0, 4);
                if (!seenYears.has(year)) {
                    seenYears.add(year);
                    targets.push({ index, date, isYear: true });
                }
            }
        });
    }
    
    // 라벨 렌더링
    targets.forEach(({ index, date, isYear }) => {
        const x = padding.left + (index / (sortedDates.length - 1 || 1)) * chartWidth;
        const y = 370;
        
        let labelText = '';
        if (isYear) {
            // 연도만 표시
            labelText = date.substring(0, 4);
        } else if (date.length === 6 && !date.includes('Q')) {
            // YYYYMM 형식 -> YY.MM
            const year = date.substring(2, 4);
            const month = date.substring(4, 6);
            labelText = `${year}.${month}`;
        } else {
            labelText = date;
        }
        
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', x);
        label.setAttribute('y', y);
        label.setAttribute('class', 'chart-xaxis-label');
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('dominant-baseline', 'middle');
        label.textContent = labelText;
        
        xAxisGroup.appendChild(label);
    });
}

function renderInterestDataPointsMulti(sortedDates) {
    // Data points (circles) are removed as per user request - showing only lines
    const pointsGroup = document.getElementById('interest-data-points');
    if (pointsGroup) {
        pointsGroup.innerHTML = '';
    }
}

let interestCrosshairX = null;
let interestCrosshairY = null;

function setupInterestChartInteractivityMulti() {
    const chartContainer = document.getElementById('interest-chart-container');
    const svg = document.getElementById('interest-chart-svg');
    if (!chartContainer || !svg) return;
    
    // 툴팁을 body로 이동 (exchange rate 스타일)
    const tooltip = document.getElementById('interest-chart-tooltip');
    if (tooltip) {
        if (tooltip.parentElement !== document.body) {
            document.body.appendChild(tooltip);
        }
    }
    
    // Create crosshair elements
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    const crosshairs = createCrosshairElements(svg, padding, chartWidth, chartHeight);
    interestCrosshairX = crosshairs.crosshairX;
    interestCrosshairY = crosshairs.crosshairY;
    
    // 기존 이벤트 리스너 제거
    if (interestMouseMoveHandler) {
        chartContainer.removeEventListener('mousemove', interestMouseMoveHandler);
    }
    if (interestMouseLeaveHandler) {
        chartContainer.removeEventListener('mouseleave', interestMouseLeaveHandler);
    }
    
    let rafId = null;
    
    interestMouseMoveHandler = (event) => {
        if (rafId) return;
        
        rafId = requestAnimationFrame(() => {
            rafId = null;
            showInterestTooltipMulti(event);
        });
    };
    
    interestMouseLeaveHandler = () => {
        if (rafId) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
        hideInterestTooltip();
        hideCrosshair(interestCrosshairX, interestCrosshairY);
    };
    
    chartContainer.addEventListener('mousemove', interestMouseMoveHandler);
    chartContainer.addEventListener('mouseleave', interestMouseLeaveHandler);
}

function showInterestTooltipMulti(event) {
    const tooltip = document.getElementById('interest-chart-tooltip');
    if (!tooltip) return;
    
    const svg = document.getElementById('interest-chart-svg');
    if (!svg) return;
    
    const svgRect = svg.getBoundingClientRect();
    const { width: vbWidth, height: vbHeight } = getSvgViewBoxSize(svg);
    const chartPadding = { left: 40, right: 20, top: 20, bottom: 30 };
    const chartWidth = vbWidth - chartPadding.left - chartPadding.right;
    const chartHeight = vbHeight - chartPadding.top - chartPadding.bottom;
    
    // 픽셀 좌표를 viewBox 좌표로 변환
    const pixelX = event.clientX - svgRect.left;
    const scaleX = vbWidth / svgRect.width;
    const viewBoxX = pixelX * scaleX;
    
    // viewBox 좌표에서 차트 영역 내 비율 계산
    const chartRelativeX = viewBoxX - chartPadding.left;
    const ratio = Math.max(0, Math.min(1, chartRelativeX / chartWidth));
    
    // 모든 국가 데이터 병합하여 공통 날짜 목록 생성
    const allDates = new Set();
    Object.values(interestCountryData).forEach(data => {
        data.forEach(item => allDates.add(item.date));
    });
    const sortedDates = Array.from(allDates).sort((a, b) => {
        return compareInterestDates(a, b, interestCycle || 'M');
    });
    
    if (sortedDates.length === 0) {
        hideCrosshair(interestCrosshairX, interestCrosshairY);
        return;
    }
    
    // 비율로 날짜 인덱스 찾기
    const dateIndex = Math.round(ratio * (sortedDates.length - 1));
    const dateIndexClamped = Math.max(0, Math.min(sortedDates.length - 1, dateIndex));
    const date = sortedDates[dateIndexClamped];
    
    // Update crosshair X position
    const crosshairXPos = chartPadding.left + (dateIndexClamped / (sortedDates.length - 1 || 1)) * chartWidth;
    if (interestCrosshairX) {
        interestCrosshairX.setAttribute('x1', crosshairXPos);
        interestCrosshairX.setAttribute('x2', crosshairXPos);
        interestCrosshairX.style.opacity = '1';
    }
    
    // Calculate average Y for crosshair
    let sumY = 0, countY = 0;
    activeInterestCountries.forEach(itemCode => {
        const data = interestCountryData[itemCode];
        if (data) {
            const item = data.find(d => d.date === date);
            if (item && Number.isFinite(item.value)) { sumY += item.value; countY++; }
        }
    });
    
    if (countY > 0 && interestCrosshairY) {
        const avgVal = sumY / countY;
        const { min, max } = interestYAxisRange;
        const normY = (avgVal - min) / (max - min || 1);
        const crosshairYPos = chartPadding.top + (1 - normY) * chartHeight;
        interestCrosshairY.setAttribute('y1', crosshairYPos);
        interestCrosshairY.setAttribute('y2', crosshairYPos);
        interestCrosshairY.style.opacity = '1';
    }
    
    // 날짜 포맷팅 (X축과 동일한 형식: YY.MM)
    let dateLabel = date;
    if (date.length === 6 && !date.includes('Q')) {
        // YYYYMM 형식 -> YY.MM
        const year = date.substring(2, 4);
        const month = date.substring(4, 6);
        dateLabel = `${year}.${month}`;
    } else if (date.includes('Q')) {
        // YYYYQn 형식 (예: 2024Q1 -> 24Q1)
        const year = date.substring(0, 4);
        const quarter = date.substring(5);
        dateLabel = `${year.substring(2)}Q${quarter}`;
    }
    
    // Exchange rate 스타일의 툴팁 생성
    let content = '';
    activeInterestCountries.forEach(itemCode => {
        const data = interestCountryData[itemCode];
        if (!data) return;
        
        // 정확한 날짜 매칭 시도
        let item = data.find(d => d.date === date);
        
        // 정확한 매칭이 없으면 가장 가까운 날짜 찾기
        if (!item && sortedDates.length > 0) {
            const currentIndex = sortedDates.indexOf(date);
            if (currentIndex > 0) {
                const prevDate = sortedDates[currentIndex - 1];
                item = data.find(d => d.date === prevDate);
            }
            if (!item && currentIndex < sortedDates.length - 1) {
                const nextDate = sortedDates[currentIndex + 1];
                item = data.find(d => d.date === nextDate);
            }
        }
        
        if (!item) return;
        
        const countryInfo = interestCountryMapping[itemCode];
        const countryName = countryInfo ? getInterestCountryNameEnglish(countryInfo.name, itemCode) : itemCode;
        const color = getInterestCountryColor(itemCode);
        
        // CSS 변수를 실제 색상으로 변환
        const tempEl = document.createElement('div');
        tempEl.style.color = color;
        document.body.appendChild(tempEl);
        const computedColor = window.getComputedStyle(tempEl).color;
        document.body.removeChild(tempEl);
        
        content += `
            <div class="chart-tooltip-item">
                <div class="chart-tooltip-currency">
                    <div class="chart-tooltip-dot" style="background: ${computedColor}"></div>
                    <span>${countryName}</span>
                </div>
                <span class="chart-tooltip-value">${item.value.toFixed(2)}%</span>
            </div>
        `;
    });
    
    if (!content) {
        hideInterestTooltip();
        return;
    }
    
    const tooltipContentEl = document.getElementById('interest-tooltip-content');
    if (tooltipContentEl) {
        tooltipContentEl.innerHTML = content;
    }
    
    const tooltipDateEl = document.getElementById('interest-tooltip-date');
    if (tooltipDateEl) {
        tooltipDateEl.textContent = dateLabel;
    }
    
    // 툴팁을 먼저 표시해서 크기를 측정 (exchange rate 스타일)
    tooltip.style.visibility = 'hidden';
    tooltip.classList.add('visible');
    
    const tooltipRect = tooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const tooltipPadding = 15;
    
    // 기본 위치 (마우스 오른쪽 아래)
    let left = event.clientX + tooltipPadding;
    let top = event.clientY + tooltipPadding;
    
    // 우측 경계 체크 및 조정
    if (left + tooltipRect.width > viewportWidth - tooltipPadding) {
        left = event.clientX - tooltipRect.width - tooltipPadding;
    }
    
    // 좌측 경계 체크 및 조정
    if (left < tooltipPadding) {
        if (event.clientX + tooltipRect.width + tooltipPadding <= viewportWidth - tooltipPadding) {
            left = event.clientX + tooltipPadding;
        } else {
            left = tooltipPadding;
        }
    }
    
    // 하단 경계 체크 및 조정
    if (top + tooltipRect.height > viewportHeight - tooltipPadding) {
        top = event.clientY - tooltipRect.height - tooltipPadding;
    }
    
    // 상단 경계 체크 및 조정
    if (top < tooltipPadding) {
        if (event.clientY + tooltipRect.height + tooltipPadding <= viewportHeight - tooltipPadding) {
            top = event.clientY + tooltipPadding;
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
    
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    tooltip.style.visibility = 'visible';
}

function updateInterestChartHeaderMulti() {
    if (activeInterestCountries.length === 0) return;
    
    // 첫 번째 국가의 데이터만 사용 (대표 기준금리)
    const firstCountryCode = activeInterestCountries[0];
    const firstCountryData = interestCountryData[firstCountryCode];
    
    if (!firstCountryData || firstCountryData.length === 0) return;
    
    // 첫 번째 국가의 현재 선택된 기간의 값들만 사용
    const values = firstCountryData.map(item => item.value);
    const high = Math.max(...values);
    const low = Math.min(...values);
    const average = values.reduce((sum, v) => sum + v, 0) / values.length;
    
    // 첫 번째 국가의 최신값
    const current = firstCountryData[firstCountryData.length - 1].value;
    const previous = firstCountryData.length > 1
        ? firstCountryData[firstCountryData.length - 2].value
        : current;
    
    const change = current - previous;
    const changePercent = previous !== 0 ? (change / previous) * 100 : 0;
    
    // 헤더 업데이트
    const countryInfo = interestCountryMapping[firstCountryCode];
    const countryName = countryInfo ? getInterestCountryNameEnglish(countryInfo.name, firstCountryCode) : firstCountryCode;
    
    const titleEl = document.getElementById('interest-chart-main-title');
    if (titleEl) titleEl.textContent = countryName + ' Interest Rate';
    
    const valueEl = document.getElementById('interest-chart-main-value');
    if (valueEl) valueEl.textContent = current.toFixed(2) + '%';
    
    // 변화율 표시 숨김
    const changeContainer = document.getElementById('interest-chart-change');
    if (changeContainer) {
        changeContainer.style.display = 'none';
    }
    const changeValueEl = document.getElementById('interest-change-value');
    const changePercentEl = document.getElementById('interest-change-percent');
    if (changeValueEl && changePercentEl) {
        changeValueEl.textContent = '';
        changePercentEl.textContent = '';
    }
    
    // 통계 업데이트 (첫 번째 국가의 현재 선택된 기간만)
    const highEl = document.getElementById('interest-stat-high');
    const lowEl = document.getElementById('interest-stat-low');
    const avgEl = document.getElementById('interest-stat-average');
    
    if (highEl) highEl.textContent = high.toFixed(2) + '%';
    if (lowEl) lowEl.textContent = low.toFixed(2) + '%';
    if (avgEl) avgEl.textContent = average.toFixed(2) + '%';
}

// ============================================================
// CHART RENDERING - SINGLE COUNTRY (Legacy)
// ============================================================

function updateInterestChart() {
    const path = document.getElementById('path-interest');
    const barGroup = document.getElementById('interest-bar-chart');
    const pointsGroup = document.getElementById('interest-data-points');
    
    if (!path || !barGroup || !pointsGroup) return;
    
    if (!interestRateData || interestRateData.length === 0) {
        path.setAttribute('d', '');
        path.classList.remove('visible');
        barGroup.innerHTML = '';
        pointsGroup.innerHTML = '';
        return;
    }
    
    // 주기별 데이터 개수 계산
    const unitCount = getInterestDataUnitCount(interestRateData, interestCycle);
    const isSingleUnit = unitCount <= 1;
    
    // Update Y-axis labels
    renderInterestYAxisLabels();
    
    if (isSingleUnit) {
        // 1개 단위 이하: 막대 그래프
        path.setAttribute('d', '');
        path.classList.remove('visible');
        pointsGroup.innerHTML = '';
        renderInterestBarChart();
    } else {
        // 2개 단위 이상: 꺾은선 그래프 + 포인트
        barGroup.innerHTML = '';
        const pathData = generateInterestSVGPath(interestRateData);
        path.setAttribute('d', pathData);
        path.classList.add('visible');
        renderInterestDataPoints();
    }
    
    // Update X-axis labels
    renderInterestXAxisLabels(isSingleUnit);
    
    // Setup interactivity
    setupInterestChartInteractivity();
}

function setupInterestChartInteractivity() {
    const chartContainer = document.getElementById('interest-chart-container');
    const svg = document.getElementById('interest-chart-svg');
    
    if (!chartContainer || !svg) return;
    
    // Ensure tooltip is in body
    const tooltip = document.getElementById('interest-chart-tooltip');
    if (tooltip && tooltip.parentElement !== document.body) {
        document.body.appendChild(tooltip);
    }
    
    // Remove existing listeners if they exist
    if (interestMouseMoveHandler) {
        chartContainer.removeEventListener('mousemove', interestMouseMoveHandler);
    }
    if (interestMouseLeaveHandler) {
        chartContainer.removeEventListener('mouseleave', interestMouseLeaveHandler);
    }
    
    // Add new listeners
    let rafId = null;
    
    interestMouseMoveHandler = (e) => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
            rafId = null;
            
            if (!interestRateData || interestRateData.length === 0) {
                hideInterestTooltip();
                return;
            }
            
            const svgEl = document.getElementById('interest-chart-svg');
            if (!svgEl) {
                hideInterestTooltip();
                return;
            }
            
            const svgRect = svgEl.getBoundingClientRect();
            const { width: vbWidth } = getSvgViewBoxSize(svgEl);
            
            // 픽셀 좌표를 viewBox 좌표로 변환
            const pixelX = e.clientX - svgRect.left;
            const scaleX = vbWidth / svgRect.width;
            const viewBoxX = pixelX * scaleX;
            
            const padding = { left: 40, right: 20 };
            const chartWidth = vbWidth - padding.left - padding.right;
            
            // viewBox 좌표에서 차트 영역 내 비율 계산
            const chartRelativeX = viewBoxX - padding.left;
            const ratio = Math.max(0, Math.min(1, chartRelativeX / chartWidth));
            const dataIndex = Math.round(ratio * (interestRateData.length - 1));
            
            if (dataIndex >= 0 && dataIndex < interestRateData.length) {
                const dataPoint = interestRateData[dataIndex];
                showInterestTooltip(e, dataPoint);
            } else {
                hideInterestTooltip();
            }
        });
    };
    
    interestMouseLeaveHandler = () => {
        hideInterestTooltip();
    };
    
    chartContainer.addEventListener('mousemove', interestMouseMoveHandler);
    chartContainer.addEventListener('mouseleave', interestMouseLeaveHandler);
}

function showInterestTooltip(event, dataPoint) {
    const tooltip = document.getElementById('interest-chart-tooltip');
    const tooltipDate = document.getElementById('interest-tooltip-date');
    const tooltipContent = document.getElementById('interest-tooltip-content');
    
    if (!tooltip || !tooltipDate || !tooltipContent || !dataPoint) return;
    
    // 날짜 포맷 (X축과 동일한 형식: YY.MM)
    let formattedDate = dataPoint.date;
    
    if (interestCycle === 'M' && dataPoint.date.length === 6) {
        // 월별: YY.MM 형식
        const year = dataPoint.date.substring(2, 4);
        const month = dataPoint.date.substring(4, 6);
        formattedDate = `${year}.${month}`;
    } else if (interestCycle === 'Q' && dataPoint.date.includes('Q')) {
        // 분기별: YYQn 형식 (예: 24Q1, 24Q2)
        const match = dataPoint.date.match(/^(\d{4})Q([1-4])$/);
        if (match) {
            const year = match[1].substring(2, 4);
            const quarter = match[2];
            formattedDate = `${year}Q${quarter}`;
        }
    }
    
    tooltipDate.textContent = formattedDate;
    
    // Show value
    tooltipContent.innerHTML = `
        <div class="chart-tooltip-item">
            <div class="chart-tooltip-currency">
                <div class="chart-tooltip-dot" style="background: var(--accent-color);"></div>
                <span>기준금리</span>
            </div>
            <span class="chart-tooltip-value">${dataPoint.value.toFixed(2)}%</span>
        </div>
    `;
    
    // Position tooltip
    tooltip.style.left = (event.clientX + 10) + 'px';
    tooltip.style.top = (event.clientY + 10) + 'px';
    tooltip.style.visibility = 'visible';
    tooltip.classList.add('visible');
}

function hideInterestTooltip() {
    const tooltip = document.getElementById('interest-chart-tooltip');
    if (tooltip) {
        tooltip.classList.remove('visible');
        tooltip.style.visibility = 'hidden';
    }
    hideCrosshair(interestCrosshairX, interestCrosshairY);
}

function generateInterestSVGPath(data) {
    if (!data || data.length === 0) return '';
    
    const svg = document.getElementById('interest-chart-svg');
    if (!svg) return '';
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // Use Y-axis range
    const minValue = interestYAxisRange.min;
    const maxValue = interestYAxisRange.max;
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

// 막대 그래프 렌더링 함수 (1개 단위일 때)
function renderInterestBarChart() {
    const barGroup = document.getElementById('interest-bar-chart');
    if (!barGroup || !interestRateData || interestRateData.length === 0) return;
    
    barGroup.innerHTML = '';
    
    const svg = document.getElementById('interest-chart-svg');
    if (!svg) return;
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // 중앙에 막대 표시
    const centerX = padding.left + chartWidth / 2;
    const barWidth = Math.min(60, chartWidth * 0.3);
    
    // 첫 번째 데이터 포인트 사용 (1개 단위이므로)
    const dataPoint = interestRateData[0];
    const minValue = interestYAxisRange.min;
    const maxValue = interestYAxisRange.max;
    const valueRange = maxValue - minValue || 1;
    const normalizedValue = (dataPoint.value - minValue) / valueRange;
    const barHeight = normalizedValue * chartHeight;
    const barY = padding.top + (1 - normalizedValue) * chartHeight;
    
    // 막대 그리기
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('x', String(centerX - barWidth / 2));
    rect.setAttribute('y', String(barY));
    rect.setAttribute('width', String(barWidth));
    rect.setAttribute('height', String(barHeight));
    rect.setAttribute('fill', 'var(--accent-color)');
    rect.setAttribute('rx', '4');
    barGroup.appendChild(rect);
}

// 데이터 포인트 렌더링 함수 (꺾은선 그래프용)
// Data points (circles) are removed as per user request - showing only lines
function renderInterestDataPoints() {
    const pointsGroup = document.getElementById('interest-data-points');
    if (pointsGroup) {
        pointsGroup.innerHTML = '';
    }
}

function renderInterestYAxisLabels() {
    const svg = document.getElementById('interest-chart-svg');
    const g = document.getElementById('interest-y-axis-labels');
    if (!svg || !g) return;
    
    g.innerHTML = '';
    
    if (!interestRateData || interestRateData.length === 0) return;
    
    // Calculate min/max values
    const values = interestRateData.map(d => d.value);
    let minValue = Math.min(...values);
    let maxValue = Math.max(...values);
    
    // 단일 값인 경우 막대그래프를 위해 Y축을 0.5 단위로 나눔
    const isSingleValue = minValue === maxValue;
    const isSingleUnit = getInterestDataUnitCount(interestRateData, interestCycle) <= 1;
    
    if (isSingleValue && isSingleUnit) {
        // 막대그래프를 위해 Y축을 0.5 단위로 설정
        const centerValue = minValue;
        // 0.5 단위로 Y축 범위 설정 (예: 2.5면 0.0 ~ 3.0)
        interestYAxisRange.min = Math.max(0, Math.floor(centerValue * 2) / 2 - 0.5);
        interestYAxisRange.max = Math.ceil(centerValue * 2) / 2 + 0.5;
        
        // 최소값이 0보다 작으면 0으로 설정
        if (interestYAxisRange.min < 0) {
            interestYAxisRange.min = 0;
        }
    } else {
        // Calculate range with padding
        const range = maxValue - minValue;
        let paddingPercent = 0.01;
        if (range > 1) {
            paddingPercent = 0.003;
        } else if (range > 0.1) {
            paddingPercent = 0.005;
        }
        
        const padding = range * paddingPercent;
        const calculatedMin = minValue - padding;
        const calculatedMax = maxValue + padding;
        
        const minValueRatio = minValue / (maxValue || 1);
        if (calculatedMin < 0 || (minValueRatio < 0.05 && minValue < range * 0.1)) {
            interestYAxisRange.min = 0;
            interestYAxisRange.max = maxValue + padding + Math.abs(Math.min(0, calculatedMin));
        } else {
            interestYAxisRange.min = calculatedMin;
            interestYAxisRange.max = calculatedMax;
        }
    }
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding_axis = { top: 20, bottom: 30, left: 40, right: 20 };
    const chartHeight = height - padding_axis.top - padding_axis.bottom;
    
    const numLabels = 6;
    const step = (interestYAxisRange.max - interestYAxisRange.min) / (numLabels - 1);
    
    for (let i = 0; i < numLabels; i++) {
        const value = interestYAxisRange.max - (step * i);
        const y = padding_axis.top + (i / (numLabels - 1)) * chartHeight;
        
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', String(padding_axis.left - 10));
        label.setAttribute('y', String(y));
        label.setAttribute('class', 'chart-yaxis-label');
        label.textContent = value.toLocaleString('ko-KR', {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
        });
        g.appendChild(label);
    }
}

function renderInterestXAxisLabels(isSingleUnit = false) {
    const svg = document.getElementById('interest-chart-svg');
    const g = document.getElementById('interest-x-axis-labels');
    if (!svg || !g) return;
    
    g.innerHTML = '';
    
    if (!interestRateData || interestRateData.length === 0) return;
    
    const { width, height } = getSvgViewBoxSize(svg);
    const padding = { left: 40, right: 20, top: 20, bottom: 30 };
    const chartWidth = width - padding.left - padding.right;
    const y = height - padding.bottom + 15;
    
    if (isSingleUnit) {
        // 1개 단위: 중앙에 레이블 표시 (YY.MM 형식)
        const centerX = padding.left + chartWidth / 2;
        const dataPoint = interestRateData[0];
        let label = '';
        
        if (dataPoint.date.length === 6) {
            // 월별: YY.MM 형식
            const year = dataPoint.date.substring(2, 4);
            const month = dataPoint.date.substring(4, 6);
            label = `${year}.${month}`;
        } else {
            label = dataPoint.date;
        }
        
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', String(centerX));
        t.setAttribute('y', String(y));
        t.setAttribute('text-anchor', 'middle');
        t.setAttribute('dominant-baseline', 'middle');
        t.setAttribute('class', 'chart-xaxis-label');
        t.textContent = label;
        g.appendChild(t);
    } else {
        // 2개 이상: 기존 로직 사용
        const dates = interestRateData.map(d => d.date);
        const rangeKey = getInterestRangeKey();
        const targets = buildInterestXAxisTargets(rangeKey, dates);
        const n = dates.length;
        
        for (const tInfo of targets) {
            const i = tInfo.idx;
            let x = padding.left + (i / (n - 1 || 1)) * chartWidth;
            
            // 마지막 레이블인 경우 오른쪽 여백 고려 (텍스트가 잘리지 않도록)
            if (i === n - 1 && n > 1) {
                // 텍스트 너비를 고려하여 위치 조정 (대략 40px 여유)
                x = Math.min(x, width - padding.right - 20);
            }
            
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
}

function getInterestRangeKey() {
    // Map cycle to range key for X-axis formatting
    const cycleMap = {
        'A': '1Y',
        'M': '3M',
        'Q': '1Y'
    };
    return cycleMap[interestCycle] || '3M';
}

function buildInterestXAxisTargets(rangeKey, dates) {
    const n = dates.length;
    if (n === 0) return [];
    
    const targets = [];
    
    // 기간별 라벨 표시 규칙:
    // 1Y 이내 (≤12개월): YY.MM 모든 월 표시
    // 1Y~2Y (13~24개월): YY.MM 홀수 월만 표시
    // 2Y 초과 (>24개월): YYYY 연도만 표시
    
    if (n <= 12) {
        // 1Y 이내: 모든 월 표시
        for (let i = 0; i < n; i++) {
            const dateStr = dates[i];
            let label = dateStr;
            
            if (dateStr.length === 6) {
                const year = dateStr.substring(2, 4);
                const month = dateStr.substring(4, 6);
                label = `${year}.${month}`;
            }
            
            targets.push({ idx: i, label: label });
        }
    } else if (n <= 24) {
        // 1Y~2Y: 홀수 월만 표시
        for (let i = 0; i < n; i++) {
            const dateStr = dates[i];
            if (dateStr.length === 6) {
                const month = parseInt(dateStr.substring(4, 6), 10);
                // 홀수 월만 (1, 3, 5, 7, 9, 11) 또는 첫/마지막
                if (month % 2 === 1 || i === 0 || i === n - 1) {
                    const year = dateStr.substring(2, 4);
                    const monthStr = dateStr.substring(4, 6);
                    targets.push({ idx: i, label: `${year}.${monthStr}` });
                }
            }
        }
    } else {
        // 2Y 초과: 연도만 표시
        const seenYears = new Set();
        for (let i = 0; i < n; i++) {
            const dateStr = dates[i];
            if (dateStr.length >= 4) {
                const year = dateStr.substring(0, 4);
                if (!seenYears.has(year)) {
                    seenYears.add(year);
                    targets.push({ idx: i, label: year });
                }
            }
        }
    }
    
    return targets;
}

function updateInterestChartHeader(stats) {
    if (!stats || stats.error) {
        document.getElementById('interest-chart-main-title').textContent = '기준금리';
        document.getElementById('interest-chart-main-value').textContent = '-';
        document.getElementById('interest-change-value').textContent = '-';
        document.getElementById('interest-change-percent').textContent = '(-)';
        document.getElementById('interest-stat-high').textContent = '-';
        document.getElementById('interest-stat-low').textContent = '-';
        document.getElementById('interest-stat-average').textContent = '-';
        return;
    }
    
    // Update current value
    const currentValueEl = document.getElementById('interest-chart-main-value');
    const targetValue = stats.current;
    const currentValue = parseFloat(currentValueEl.textContent.replace(/,/g, '')) || 0;
    if (currentValue !== targetValue) {
        animateValue(currentValueEl, currentValue, targetValue, 800);
    } else {
        currentValueEl.textContent = targetValue.toLocaleString('ko-KR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    
    // Update change
    const change = stats.change;
    const changePercent = stats.changePercent;
    const isUp = change >= 0;
    
    const changeValueEl = document.getElementById('interest-change-value');
    const changePercentEl = document.getElementById('interest-change-percent');
    
    changeValueEl.textContent = `${isUp ? '+' : ''}${change.toFixed(2)}`;
    changePercentEl.textContent = `(${isUp ? '+' : ''}${changePercent.toFixed(2)}%)`;
    
    changeValueEl.className = `change-value ${isUp ? 'up' : 'down'}`;
    changePercentEl.className = `change-percent ${isUp ? 'up' : 'down'}`;
    
    // Update statistics
    const statHighEl = document.getElementById('interest-stat-high');
    const statLowEl = document.getElementById('interest-stat-low');
    const statAverageEl = document.getElementById('interest-stat-average');
    
    const currentHigh = parseFloat(statHighEl.textContent.replace(/,/g, '')) || 0;
    const currentLow = parseFloat(statLowEl.textContent.replace(/,/g, '')) || 0;
    const currentAverage = parseFloat(statAverageEl.textContent.replace(/,/g, '')) || 0;
    
    if (currentHigh !== stats.high) {
        animateValue(statHighEl, currentHigh, stats.high, 800);
    } else {
        statHighEl.textContent = stats.high.toLocaleString('ko-KR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    
    if (currentLow !== stats.low) {
        animateValue(statLowEl, currentLow, stats.low, 800);
    } else {
        statLowEl.textContent = stats.low.toLocaleString('ko-KR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    
    if (currentAverage !== stats.average) {
        animateValue(statAverageEl, currentAverage, stats.average, 800);
    } else {
        statAverageEl.textContent = stats.average.toLocaleString('ko-KR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
}

// ============================================================
// GLOBAL EXPORTS
// ============================================================

// 전역 함수로 노출
window.initInterestRates = initInterestRates;
window.toggleInterestCountry = toggleInterestCountry;
window.fetchInterestRateData = fetchInterestRateData;
window.fetchInterestRateDataMulti = fetchInterestRateDataMulti;
window.updateInterestChart = updateInterestChart;
window.updateInterestChartMulti = updateInterestChartMulti;

console.log('📊 Interest Rate module loaded');
