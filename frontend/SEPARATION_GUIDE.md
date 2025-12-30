# 📁 파일 분리 가이드 및 테스트 전략

> 이 문서는 `ai_studio_code_F2.html` 파일을 모듈화하는 단계별 가이드입니다.
> 각 단계마다 테스트를 실행하여 기능 정상 동작을 확인하세요.

---

## 📊 현재 파일 구조 (10,462줄 - CSS 분리 후)

| 섹션 | 라인 범위 | 줄 수 | 설명 |
|------|----------|-------|------|
| **Head/Scripts** | 1 ~ 67 | ~67줄 | Google Maps API + CSS/JS 링크 |
| **HTML 마크업** | 68 ~ 1242 | ~1,175줄 | 페이지 구조 |
| **JavaScript** | 1243 ~ 10462 | ~9,219줄 | 모든 로직 (상수/유틸은 외부 파일로) |

---

## 🎯 목표

- 12,000줄 단일 파일 → 기능별 모듈로 분리
- 팀원 간 병렬 작업 가능
- Git 충돌 최소화

---

## 📋 분리 순서 (권장)

```
Phase 1: CSS 분리 (충돌 위험 낮음, 독립적) ✅ 완료
    ↓
Phase 2: 설정/유틸리티 JS 분리 (의존성 기반) ✅ 완료
    ↓
Phase 3: 기능 모듈 분리 (병렬 작업 가능)
    ↓
Phase 4: HTML 정리 및 통합
```

---

## ✅ Phase 1: CSS 분리 (완료)

### 생성된 파일 구조

```
frontend/css/
├── variables.css          # CSS 변수 (색상, 폰트 등)
├── base.css               # Reset, Typography, Layout, Animations
├── components/
│   ├── header.css         # 헤더, 네비게이션, 푸터
│   ├── buttons.css        # 버튼, 탭, 칩, 필터
│   ├── charts.css         # 차트, 툴팁, 그래프
│   ├── cards.css          # 카드, 테이블, 컨버터
│   └── modals.css         # 모달 다이얼로그
└── sections/
    ├── hero.css           # Hero 섹션
    ├── market.css         # Market 섹션, 사이드바
    ├── tools.css          # Smart Tools 섹션
    ├── war-room.css       # War Room 섹션
    └── news.css           # News 섹션
```

### 🧪 Phase 1 테스트

```bash
# 1. 서버 실행
python server/main.py

# 2. 브라우저에서 테스트
http://localhost:5000/test_frontend.html

# 3. "CSS 파일 테스트" 버튼 클릭하여 확인
```

---

## ✅ Phase 2: 핵심 JS 분리 (완료)

### 생성된 파일 구조

```
frontend/js/
├── config/
│   └── constants.js     # API 설정, 전역 상태, 통화 매핑
└── utils/
    └── helpers.js       # 날짜, 숫자 포맷팅, 애니메이션 유틸리티
```

### 2.1 설정 파일 (`js/config/constants.js`)

**포함된 내용:**
- `API_BASE` - API 엔드포인트 기본 URL
- `CURRENCY_MAPPING` - 통화 코드 매핑
- `AppState` - 전역 애플리케이션 상태
- 하위 호환성을 위한 `window` 객체 노출

### 2.2 유틸리티 함수 (`js/utils/helpers.js`)

**포함된 함수들:**
- 날짜 관련: `formatDateForAPI`, `formatInterestDateForAPI`, `toYYYYMMDD`, `parseYYYYMMDD`, `daysInMonth`, `makeDateSafe`, `weekdayKoShort`
- 숫자 포맷팅: `formatGDPNumber`, `formatGDPChange`, `formatGDPNumberWithEasyUnit`, `formatTradeNumberWithEasyUnit`
- 애니메이션: `animateValue`
- 물가 관련: `parseInflationDate`, `compareInflationDates`, `formatInflationPeriodLabel`, `getInflationMetricLabel`, `calculateInflationIndexStats`
- 기타: `buildYearLabel`, `escapeHtml`

### 🧪 Phase 2 테스트

```bash
# 터미널에서 파일 로드 확인
curl -s -o /dev/null -w "constants.js: HTTP %{http_code}\n" http://localhost:5000/js/config/constants.js
curl -s -o /dev/null -w "helpers.js: HTTP %{http_code}\n" http://localhost:5000/js/utils/helpers.js
```

```javascript
// 브라우저 콘솔에서 실행
console.log('=== Phase 2 테스트 ===');
console.log('API_BASE:', typeof API_BASE !== 'undefined' ? '✅' : '❌');
console.log('AppState:', typeof AppState !== 'undefined' ? '✅' : '❌');
console.log('formatDateForAPI:', typeof formatDateForAPI === 'function' ? '✅' : '❌');
console.log('animateValue:', typeof animateValue === 'function' ? '✅' : '❌');
```

---

## 🟡 Phase 3: 기능 모듈 분리 (병렬 작업 가능)

> ⚠️ 이 단계부터는 팀원들이 **병렬로 작업** 가능합니다.
> 각자 담당 모듈만 작업하면 충돌이 발생하지 않습니다.

### 현재 패널 구조

| 패널 ID | 기능 | 담당 모듈 파일 |
|---------|------|---------------|
| `#economy-panel` | 환율 차트 | `js/features/exchange-rate.js` |
| `#interest-rates-panel` | 금리 차트 | `js/features/interest-rate.js` |
| `#inflation-panel` | 물가 차트 | `js/features/inflation.js` |
| `#gdp-panel` | GDP 차트 | `js/features/gdp.js` |
| `#trade-panel` | 수출입 통계 | `js/features/trade.js` |
| `#employment-panel` | 고용 통계 | `js/features/employment.js` |
| `#gdp-growth-panel` | 경제 성장률 | `js/features/gdp-growth.js` |
| `#logistics-panel` | 물류 지수 | `js/features/logistics.js` |
| `#war-room` | War Room/지도 | `js/features/global-alarm.js` |

### 담당자 배정 예시

| 담당자 | 모듈 | 파일 |
|--------|------|------|
| A | 환율 | `js/features/exchange-rate.js` |
| B | 금리 | `js/features/interest-rate.js` |
| C | 물가 | `js/features/inflation.js` |
| D | GDP | `js/features/gdp.js` |
| E | 수출입 | `js/features/trade.js` |
| F | 고용 | `js/features/employment.js` |
| G | 경제 성장률 | `js/features/gdp-growth.js` |
| H | War Room | `js/features/global-alarm.js` |

### 3.1 환율 모듈 (exchange-rate.js)

**추출할 함수들:**
```
- fetchExchangeRateData()
- fetchExchangeRateStats()
- fetchAllCurrencyRates()
- processExchangeRateData()
- updateChart()
- toggleCurrency()
- updateCurrencyRatesTable()
- updateChartHeader()
- renderYAxisLabels()
- renderXAxisLabels()
- setupChartInteractivity()
- showTooltip()
- hideTooltip()
- rebuildTooltipCache()
- updateCalculator()
- calculate()
```

### 3.2 금리 모듈 (interest-rate.js)

**추출할 함수들:**
```
- initInterestRates()
- validateInterestDateRange()
- fetchInterestRateData()
- fetchInterestRateDataMulti()
- fetchInterestCountryList()
- processInterestRateData()
- processInterestRateDataMulti()
- initInterestCountryChips()
- toggleInterestCountry()
- updateInterestChart()
- updateInterestChartMulti()
- generateInterestSVGPath()
- generateInterestSVGPathMulti()
- renderInterestYAxisLabels()
- renderInterestXAxisLabels()
- renderInterestDataPoints()
- setupInterestChartInteractivity()
- showInterestTooltip()
- hideInterestTooltip()
- updateInterestChartHeader()
- getInterestCountryColor()
- findInterestCountryInfo()
- getInterestCountryNameEnglish()
```

### 3.3 물가 모듈 (inflation.js)

**추출할 함수들:**
```
- initInflation()
- validateInflationDateRange()
- toggleInflationItem()
- fetchInflationData()
- updateInflationChart()
- generateInflationSVGPath()
- renderInflationYAxisLabels()
- renderInflationXAxisLabels()
- renderInflationBarChart()
- renderInflationDataPoints()
- setupInflationChartInteractivity()
- showInflationTooltip()
- hideInflationTooltip()
- updateInflationChartHeader()
- parseInflationDate()
- compareInflationDates()
- formatInflationPeriodLabel()
- getInflationMetricLabel()
- calculateInflationIndexStats()
```

### 3.4 GDP 모듈 (gdp.js)

**추출할 함수들:**
```
- initGDP()
- validateGDPDateRange()
- setGDPPeriod()
- selectGDPFromSubmenu()
- switchGDPCurrencyInPanel()
- selectGDPIndicator()
- switchGDPCurrency()
- toggleGDPItem()
- selectGDPItem()
- updateGDPItemLabels()
- fetchGDPItemNames()
- fetchGDPDataForItem()
- fetchGDPData()
- calculateGDPStatsFromSeries()
- updateGDPChart()
- generateGDPSVGPath()
- renderGDPYAxisLabels()
- renderGDPXAxisLabels()
- renderGDPDataPoints()
- setupGDPChartInteractivity()
- updateGDPChartHeader()
- renderGDPBarChart()
- updateGDPSubmenuPosition()
```

### 3.5 수출입 모듈 (trade.js)

**추출할 함수들:**
```
- initTrade()
- validateTradeDateRange()
- fetchTradeData()
- fetchTradeExchangeRates()
- getExchangeRateForDate()
- calculateTradeStats()
- calculateTradeBalance()
- calculateTradeGrowthRates()
- calculateTradeYoYGrowthRates()
- updateTradeChart()
- generateTradeSVGPath()
- calculateDualYAxisRanges()
- renderTradeYAxisLabelsLeft()
- renderTradeYAxisLabelsRight()
- renderTradeBars()
- generateTradeGrowthSVGPath()
- renderTradeGrowthDataPoints()
- renderTradeBalance()
- renderTradeXAxisLabels()
- renderTradeDataPoints()
- updateTradeChartHeader()
- setupTradeChartInteractivity()
- showTradeTooltip()
- hideTradeTooltip()
- toggleTradeIndicator()
```

### 3.6 War Room 모듈 (global-alarm.js)

**추출할 함수들:**
```
- loadGoogleMapsAPI()
- initGlobalAlarmMap()
- checkAndInitMap()
- fetchAndApplyData()
- updateMapMarkers()
- getSeverityLevel()
- getSeverityConfig()
- getMarkerColor()
- formatEventDate()
- getCategoryIcon()
- getCountryFlag()
- getSeverityMeaning()
- openAlertModal()
- closeAlertModal()
- filterBySeverity()
- applyFilters()
- switchView()
- updateTimelineView()
- updateCountryDashboard()
- updateAlertList()
- getEventDescription()
- calculateConfidence()
- getCleanActorName()
- escapeHtml()
```

### 🧪 Phase 3 테스트 (모듈별)

각 모듈 분리 후 해당 기능만 집중 테스트:

```javascript
// 환율 모듈 테스트
console.log('=== 환율 모듈 테스트 ===');
console.log('fetchExchangeRateData:', typeof fetchExchangeRateData === 'function' ? '✅' : '❌');
console.log('updateChart:', typeof updateChart === 'function' ? '✅' : '❌');
toggleCurrency('JPY'); // JPY 추가되는지 확인

// 금리 모듈 테스트
console.log('=== 금리 모듈 테스트 ===');
switchProduct('interest-rates'); // 금리 패널 표시되는지 확인
```

---

## 🟣 Phase 4: 최종 통합

### 4.1 메인 진입점 (main.js)

```javascript
// frontend/js/main.js

// 모듈 로드 확인
console.log('AAL App Initializing...');

// DOM 로드 완료 후 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 스크롤 애니메이션
    initScrollReveal();
    
    // 기본 차트 로드 (환율)
    initExchangeRate();
    
    // War Room 네비게이션 핸들러
    initWarRoomNavigation();
    
    // Google Maps 초기화 확인
    loadGoogleMapsAPI();
    
    console.log('AAL App Ready!');
});
```

### 4.2 HTML 스크립트 로드 순서

```html
<!-- index.html 하단 -->

<!-- 1. 설정 (가장 먼저) -->
<script src="js/config/constants.js"></script>

<!-- 2. 유틸리티 -->
<script src="js/utils/helpers.js"></script>

<!-- 3. 기능 모듈 (순서 무관) -->
<script src="js/features/exchange-rate.js"></script>
<script src="js/features/interest-rate.js"></script>
<script src="js/features/inflation.js"></script>
<script src="js/features/gdp.js"></script>
<script src="js/features/trade.js"></script>
<script src="js/features/employment.js"></script>
<script src="js/features/gdp-growth.js"></script>
<script src="js/features/global-alarm.js"></script>

<!-- 4. 메인 진입점 (마지막) -->
<script src="js/main.js"></script>
```

### 🧪 Phase 4 최종 테스트

```bash
# 전체 테스트 실행
http://localhost:5000/test_frontend.html

# 수동 테스트 체크리스트 실행
frontend/TEST_CHECKLIST.md 참조
```

---

## ⚠️ 주의사항

### 1. 전역 변수 처리

분리 전:
```javascript
let exchangeRates = {};
```

분리 후:
```javascript
// config/constants.js에서 정의
window.exchangeRates = {};

// 각 모듈에서 사용
// exchangeRates 변수 그대로 사용 가능 (window 객체의 속성)
```

### 2. 함수 간 의존성

만약 함수 A가 함수 B를 호출한다면:
- B가 정의된 파일이 A보다 먼저 로드되어야 함
- 또는 둘 다 같은 파일에 유지

### 3. DOM 요소 참조

```javascript
// ❌ 잘못된 방법 (스크립트 로드 시점에 DOM이 없을 수 있음)
const chart = document.getElementById('fx-chart');

// ✅ 올바른 방법
function updateChart() {
    const chart = document.getElementById('fx-chart');
    if (!chart) return;
    // ...
}
```

### 4. Git 브랜치 전략

```bash
# 메인 브랜치
main

# 기능별 브랜치 (병렬 작업)
feature/css-separation       # 담당: A ✅ 완료
feature/js-config           # 담당: B
feature/exchange-rate       # 담당: C
feature/interest-rate       # 담당: D
feature/inflation          # 담당: E
feature/gdp                # 담당: F
feature/trade              # 담당: G
feature/employment         # 담당: H
feature/gdp-growth         # 담당: I
feature/global-alarm       # 담당: J

# 통합 브랜치
develop
```

---

## 📊 진행 상태 추적

| Phase | 작업 | 담당자 | 상태 | 테스트 |
|-------|------|--------|------|--------|
| 1.1 | CSS 변수 분리 | - | ✅ 완료 | ✅ |
| 1.2 | CSS 기본 스타일 분리 | - | ✅ 완료 | ✅ |
| 1.3 | CSS 컴포넌트 분리 | - | ✅ 완료 | ✅ |
| 1.4 | CSS 섹션 분리 | - | ✅ 완료 | ✅ |
| 2.1 | JS 설정 분리 | - | ✅ 완료 | ✅ |
| 2.2 | JS 유틸리티 분리 | - | ✅ 완료 | ✅ |
| 3.1 | 환율 모듈 | | ⬜ 대기 | ⬜ |
| 3.2 | 금리 모듈 | | ⬜ 대기 | ⬜ |
| 3.3 | 물가 모듈 | | ⬜ 대기 | ⬜ |
| 3.4 | GDP 모듈 | | ⬜ 대기 | ⬜ |
| 3.5 | 수출입 모듈 | | ⬜ 대기 | ⬜ |
| 3.6 | 고용 모듈 | | ⬜ 대기 | ⬜ |
| 3.7 | 경제 성장률 모듈 | | ⬜ 대기 | ⬜ |
| 3.8 | War Room 모듈 | | ⬜ 대기 | ⬜ |
| 4 | 최종 통합 | | ⬜ 대기 | ⬜ |

상태: ⬜ 대기 | 🔄 진행중 | ✅ 완료 | ❌ 실패

---

## 🧪 테스트 실행 방법

### 자동화 테스트

```bash
# 서버 실행
python server/main.py

# 브라우저에서 테스트 페이지 열기
http://localhost:5000/test_frontend.html

# "전체 테스트 실행" 버튼 클릭
```

### 테스트 항목

1. **CSS 파일 테스트** - 12개 CSS 파일 로드 확인
2. **JS 모듈 테스트** - 2개 JS 모듈 파일 로드 확인
3. **API 테스트** - 10개 API 엔드포인트 확인
4. **DOM 테스트** - 17개 DOM 요소 확인
5. **JS 함수 테스트** - 13개 함수 존재 확인
