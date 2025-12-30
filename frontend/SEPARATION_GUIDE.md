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

### 📌 애플리케이션 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                        AAL Application                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              1️⃣ MARKET DATA (#market)                    │   │
│  │  ┌─────────────────────┐  ┌─────────────────────────┐   │   │
│  │  │   Economy Tab       │  │   Logistics Tab         │   │   │
│  │  │   (7개 지표)         │  │   (확장 예정)            │   │   │
│  │  │                     │  │                         │   │   │
│  │  │  • 환율             │  │  • 물류 지수             │   │   │
│  │  │  • 금리             │  │  • (운임지수 예정)       │   │   │
│  │  │  • 물가             │  │  • (컨테이너 예정)       │   │   │
│  │  │  • GDP              │  │  • (항만 예정)           │   │   │
│  │  │  • 수출입           │  │                         │   │   │
│  │  │  • 고용             │  │                         │   │   │
│  │  │  • 경제성장률        │  │                         │   │   │
│  │  └─────────────────────┘  └─────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              2️⃣ SMART TOOLS (#tools-apps)                │   │
│  │  • 환율 계산기, 단위 변환, 관세 계산 등                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              3️⃣ WAR ROOM (#war-room)                     │   │
│  │  • 글로벌 알림 지도, 리스크 모니터링                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              4️⃣ HEADLINES (#news)                        │   │
│  │  • 물류 뉴스, 실시간 업데이트                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 모듈 파일 구조

```
frontend/js/
├── config/
│   └── constants.js              # ✅ 완료
├── utils/
│   └── helpers.js                # ✅ 완료
└── features/
    ├── market/                   # 📊 Market Data 모듈
    │   ├── economy/              #    Economy 탭 (7개)
    │   │   ├── exchange-rate.js  #    환율
    │   │   ├── interest-rate.js  #    금리
    │   │   ├── inflation.js      #    물가
    │   │   ├── gdp.js            #    GDP
    │   │   ├── trade.js          #    수출입
    │   │   ├── employment.js     #    고용
    │   │   └── gdp-growth.js     #    경제성장률
    │   └── logistics/            #    Logistics 탭 (확장 예정)
    │       └── logistics.js      #    물류 지수
    ├── tools/                    # 🛠️ Smart Tools 모듈
    │   └── tools.js              #    계산기, 단위 변환 등
    ├── war-room/                 # 🌍 War Room 모듈
    │   └── global-alarm.js       #    글로벌 알림 지도
    └── headlines/                # 📰 Headlines 모듈
        └── news.js               #    뉴스 피드
```

### 섹션별 패널 구조

#### 1️⃣ Market Data - Economy (7개 지표)

| 패널 ID | 기능 | 모듈 파일 |
|---------|------|----------|
| `#economy-panel` | 환율 차트 | `js/features/market/economy/exchange-rate.js` |
| `#interest-rates-panel` | 금리 차트 | `js/features/market/economy/interest-rate.js` |
| `#inflation-panel` | 물가 차트 | `js/features/market/economy/inflation.js` |
| `#gdp-panel` | GDP 차트 | `js/features/market/economy/gdp.js` |
| `#trade-panel` | 수출입 통계 | `js/features/market/economy/trade.js` |
| `#employment-panel` | 고용 통계 | `js/features/market/economy/employment.js` |
| `#gdp-growth-panel` | 경제성장률 | `js/features/market/economy/gdp-growth.js` |

#### 1️⃣ Market Data - Logistics (확장 예정)

| 패널 ID | 기능 | 모듈 파일 |
|---------|------|----------|
| `#logistics-panel` | 물류 지수 | `js/features/market/logistics/logistics.js` |
| (예정) | 운임 지수 | `js/features/market/logistics/freight.js` |
| (예정) | 컨테이너 지수 | `js/features/market/logistics/container.js` |
| (예정) | 항만 통계 | `js/features/market/logistics/port.js` |

#### 2️⃣ Smart Tools

| 섹션 ID | 기능 | 모듈 파일 |
|---------|------|----------|
| `#tools-apps` | 환율 계산기, 단위 변환 등 | `js/features/tools/tools.js` |

#### 3️⃣ War Room

| 섹션 ID | 기능 | 모듈 파일 |
|---------|------|----------|
| `#war-room` | 글로벌 알림 지도 | `js/features/war-room/global-alarm.js` |

#### 4️⃣ Headlines

| 섹션 ID | 기능 | 모듈 파일 |
|---------|------|----------|
| `#news` | 물류 뉴스 피드 | `js/features/headlines/news.js` |

### 담당자 배정 예시

| 영역 | 담당자 | 모듈 | 파일 |
|------|--------|------|------|
| **Economy** | A | 환율 | `market/economy/exchange-rate.js` |
| **Economy** | B | 금리 | `market/economy/interest-rate.js` |
| **Economy** | C | 물가 | `market/economy/inflation.js` |
| **Economy** | D | GDP | `market/economy/gdp.js` |
| **Economy** | E | 수출입 | `market/economy/trade.js` |
| **Economy** | F | 고용 | `market/economy/employment.js` |
| **Economy** | G | 경제성장률 | `market/economy/gdp-growth.js` |
| **Logistics** | H | 물류 지수 | `market/logistics/logistics.js` |
| **Tools** | I | 계산기 등 | `tools/tools.js` |
| **War Room** | J | 글로벌 알림 | `war-room/global-alarm.js` |
| **Headlines** | K | 뉴스 | `headlines/news.js` |

---

### 📊 3.1 Market Data - Economy 모듈들

#### 3.1.1 환율 모듈 (`market/economy/exchange-rate.js`)

**추출할 함수들:**
```javascript
// API & 데이터
fetchExchangeRateData(), fetchExchangeRateStats(), fetchAllCurrencyRates()
processExchangeRateData()

// 차트 렌더링
updateChart(), renderYAxisLabels(), renderXAxisLabels()
generateSVGPath()

// UI 인터랙션
toggleCurrency(), setupChartInteractivity()
showTooltip(), hideTooltip(), rebuildTooltipCache()
updateChartHeader(), updateCurrencyRatesTable()

// 계산기
updateCalculator(), calculate()
```

#### 3.1.2 금리 모듈 (`market/economy/interest-rate.js`)

**추출할 함수들:**
```javascript
// 초기화 & API
initInterestRates(), validateInterestDateRange()
fetchInterestRateData(), fetchInterestRateDataMulti(), fetchInterestCountryList()
processInterestRateData(), processInterestRateDataMulti()

// 차트 렌더링
updateInterestChart(), updateInterestChartMulti()
generateInterestSVGPath(), generateInterestSVGPathMulti()
renderInterestYAxisLabels(), renderInterestXAxisLabels(), renderInterestDataPoints()

// UI 인터랙션
initInterestCountryChips(), toggleInterestCountry()
setupInterestChartInteractivity(), showInterestTooltip(), hideInterestTooltip()
updateInterestChartHeader()

// 유틸리티
getInterestCountryColor(), findInterestCountryInfo(), getInterestCountryNameEnglish()
```

#### 3.1.3 물가 모듈 (`market/economy/inflation.js`)

**추출할 함수들:**
```javascript
// 초기화 & API
initInflation(), validateInflationDateRange(), fetchInflationData()

// 차트 렌더링
updateInflationChart(), generateInflationSVGPath()
renderInflationYAxisLabels(), renderInflationXAxisLabels()
renderInflationBarChart(), renderInflationDataPoints()

// UI 인터랙션
toggleInflationItem(), initInflationCountryChips(), toggleInflationCountry()
setupInflationChartInteractivity(), showInflationTooltip(), hideInflationTooltip()
updateInflationChartHeader()
```

#### 3.1.4 GDP 모듈 (`market/economy/gdp.js`)

**추출할 함수들:**
```javascript
// 초기화 & API
initGDP(), validateGDPDateRange(), fetchGDPData(), fetchGDPDataForItem()
fetchGDPItemNames(), calculateGDPStatsFromSeries()

// 차트 렌더링
updateGDPChart(), generateGDPSVGPath()
renderGDPYAxisLabels(), renderGDPXAxisLabels(), renderGDPDataPoints()
renderGDPBarChart()

// UI 인터랙션
setGDPPeriod(), selectGDPFromSubmenu(), switchGDPCurrencyInPanel()
selectGDPIndicator(), switchGDPCurrency(), toggleGDPItem(), selectGDPItem()
updateGDPItemLabels(), setupGDPChartInteractivity(), updateGDPChartHeader()
updateGDPSubmenuPosition()
```

#### 3.1.5 수출입 모듈 (`market/economy/trade.js`)

**추출할 함수들:**
```javascript
// 초기화 & API
initTrade(), validateTradeDateRange(), fetchTradeData()
fetchTradeExchangeRates(), getExchangeRateForDate()

// 통계 계산
calculateTradeStats(), calculateTradeBalance()
calculateTradeGrowthRates(), calculateTradeYoYGrowthRates()
calculateDualYAxisRanges()

// 차트 렌더링
updateTradeChart(), generateTradeSVGPath(), generateTradeGrowthSVGPath()
renderTradeYAxisLabelsLeft(), renderTradeYAxisLabelsRight()
renderTradeBars(), renderTradeGrowthDataPoints()
renderTradeBalance(), renderTradeXAxisLabels(), renderTradeDataPoints()

// UI 인터랙션
toggleTradeIndicator(), setupTradeChartInteractivity()
showTradeTooltip(), hideTradeTooltip(), updateTradeChartHeader()
```

#### 3.1.6 고용 모듈 (`market/economy/employment.js`)

**추출할 함수들:**
```javascript
initEmployment(), fetchEmploymentData(), updateEmploymentChart()
// ... 고용 관련 함수들
```

#### 3.1.7 경제성장률 모듈 (`market/economy/gdp-growth.js`)

**추출할 함수들:**
```javascript
initGDPGrowth(), fetchGDPGrowthData(), updateGDPGrowthChart()
// ... 경제성장률 관련 함수들
```

---

### 🚛 3.2 Market Data - Logistics 모듈들

#### 3.2.1 물류 지수 모듈 (`market/logistics/logistics.js`)

**추출할 함수들:**
```javascript
initLogistics(), fetchLogisticsData(), updateLogisticsChart()
// ... 물류 지수 관련 함수들 (현재 기본 구조만 존재, 확장 예정)
```

> 📌 **확장 예정**: 운임 지수, 컨테이너 지수, 항만 통계 등 추가 모듈

---

### 🛠️ 3.3 Smart Tools 모듈

#### 3.3.1 도구 모듈 (`tools/tools.js`)

**추출할 함수들:**
```javascript
// 환율 계산기 (이미 exchange-rate.js와 공유)
updateCalculator(), calculate()

// 기타 도구들 (확장 예정)
// convertUnit(), calculateTariff(), ...
```

---

### 🌍 3.4 War Room 모듈

#### 3.4.1 글로벌 알림 모듈 (`war-room/global-alarm.js`)

**추출할 함수들:**
```javascript
// Google Maps 초기화
loadGoogleMapsAPI(), initGlobalAlarmMap(), checkAndInitMap()

// 데이터 & 마커
fetchAndApplyData(), updateMapMarkers()
getSeverityLevel(), getSeverityConfig(), getMarkerColor()

// UI 유틸리티
formatEventDate(), getCategoryIcon(), getCountryFlag(), getSeverityMeaning()
getEventDescription(), calculateConfidence(), getCleanActorName()

// 모달 & 필터
openAlertModal(), closeAlertModal(), filterBySeverity(), applyFilters()

// 뷰 전환
switchView(), updateTimelineView(), updateCountryDashboard(), updateAlertList()
```

---

### 📰 3.5 Headlines 모듈

#### 3.5.1 뉴스 모듈 (`headlines/news.js`)

**추출할 함수들:**
```javascript
fetchNews(), renderNewsCards(), updateNewsSection()
// ... 뉴스 관련 함수들
```

### 🧪 Phase 3 테스트 (모듈별)

각 모듈 분리 후 해당 기능만 집중 테스트:

```javascript
// ===== Market Data - Economy 테스트 =====

// 환율 모듈 테스트
console.log('=== 환율 모듈 테스트 ===');
console.log('fetchExchangeRateData:', typeof fetchExchangeRateData === 'function' ? '✅' : '❌');
console.log('updateChart:', typeof updateChart === 'function' ? '✅' : '❌');
toggleCurrency('JPY'); // JPY 추가되는지 확인

// 금리 모듈 테스트
console.log('=== 금리 모듈 테스트 ===');
switchProduct('interest-rates'); // 금리 패널 표시되는지 확인
console.log('initInterestRates:', typeof initInterestRates === 'function' ? '✅' : '❌');

// ===== Market Data - Logistics 테스트 =====

console.log('=== 물류 지수 모듈 테스트 ===');
switchTab('logistics'); // Logistics 탭 전환
console.log('#logistics-panel 표시:', document.getElementById('logistics-panel')?.style.display);

// ===== Smart Tools 테스트 =====

console.log('=== Smart Tools 테스트 ===');
// 환율 계산기 테스트 등

// ===== War Room 테스트 =====

console.log('=== War Room 테스트 ===');
console.log('initGlobalAlarmMap:', typeof initGlobalAlarmMap === 'function' ? '✅' : '❌');

// ===== Headlines 테스트 =====

console.log('=== Headlines 테스트 ===');
// 뉴스 로드 테스트
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

<!-- 3. Market Data - Economy 모듈 -->
<script src="js/features/market/economy/exchange-rate.js"></script>
<script src="js/features/market/economy/interest-rate.js"></script>
<script src="js/features/market/economy/inflation.js"></script>
<script src="js/features/market/economy/gdp.js"></script>
<script src="js/features/market/economy/trade.js"></script>
<script src="js/features/market/economy/employment.js"></script>
<script src="js/features/market/economy/gdp-growth.js"></script>

<!-- 4. Market Data - Logistics 모듈 -->
<script src="js/features/market/logistics/logistics.js"></script>

<!-- 5. Smart Tools 모듈 -->
<script src="js/features/tools/tools.js"></script>

<!-- 6. War Room 모듈 -->
<script src="js/features/war-room/global-alarm.js"></script>

<!-- 7. Headlines 모듈 -->
<script src="js/features/headlines/news.js"></script>

<!-- 8. 메인 진입점 (마지막) -->
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
feature/css-separation              # ✅ 완료
feature/js-config                   # ✅ 완료

# Market Data - Economy (7개)
feature/market-economy-exchange     # 환율
feature/market-economy-interest     # 금리
feature/market-economy-inflation    # 물가
feature/market-economy-gdp          # GDP
feature/market-economy-trade        # 수출입
feature/market-economy-employment   # 고용
feature/market-economy-growth       # 경제성장률

# Market Data - Logistics
feature/market-logistics            # 물류 지수

# 기타 섹션
feature/tools                       # Smart Tools
feature/war-room                    # War Room
feature/headlines                   # Headlines

# 통합 브랜치
develop
```

---

## 📊 진행 상태 추적

### 기반 작업 (Phase 1-2)

| Phase | 작업 | 상태 | 테스트 |
|-------|------|------|--------|
| 1 | CSS 분리 (12개 파일) | ✅ 완료 | ✅ |
| 2.1 | JS 설정 분리 (constants.js) | ✅ 완료 | ✅ |
| 2.2 | JS 유틸리티 분리 (helpers.js) | ✅ 완료 | ✅ |

### Market Data - Economy (Phase 3.1)

| 모듈 | 파일 | 담당자 | 상태 | 테스트 |
|------|------|--------|------|--------|
| 환율 | `market/economy/exchange-rate.js` | - | ✅ 완료 | ✅ |
| 금리 | `market/economy/interest-rate.js` | - | ✅ 완료 | ✅ |
| 물가 | `market/economy/inflation.js` | - | ✅ 완료 | ✅ |
| GDP | `market/economy/gdp.js` | - | ✅ 완료 | ✅ |
| 수출입 | `market/economy/trade.js` | - | ✅ 완료 | ✅ |
| 고용 | `market/economy/employment.js` | - | ✅ 완료 | ✅ |
| 경제성장률 | `market/economy/gdp-growth.js` | - | ✅ 완료 | ✅ |

### Market Data - Logistics (Phase 3.2)

| 모듈 | 파일 | 담당자 | 상태 | 테스트 |
|------|------|--------|------|--------|
| 물류 지수 | `market/logistics/logistics.js` | - | ✅ 완료 | ✅ |
| (예정) 운임 지수 | `market/logistics/freight.js` | | ⏳ 예정 | ⏳ |
| (예정) 컨테이너 | `market/logistics/container.js` | | ⏳ 예정 | ⏳ |
| (예정) 항만 | `market/logistics/port.js` | | ⏳ 예정 | ⏳ |

### 기타 섹션 (Phase 3.3-3.5)

| 섹션 | 모듈 | 파일 | 담당자 | 상태 | 테스트 |
|------|------|------|--------|------|--------|
| Smart Tools | 도구 | `tools/tools.js` | - | ✅ 완료 | ✅ |
| War Room | 글로벌 알림 | `war-room/global-alarm.js` | - | ✅ 완료 | ✅ |
| Headlines | 뉴스 | `headlines/news.js` | - | ✅ 완료 | ✅ |

### 최종 통합 (Phase 4)

| 작업 | 상태 |
|------|------|
| 메인 진입점 (main.js) | ✅ 완료 |
| HTML 스크립트 정리 | ✅ 완료 |
| 전체 테스트 | ✅ 완료 |

**상태 범례:** ⬜ 대기 | 🔄 진행중 | ✅ 완료 | ❌ 실패 | ⏳ 예정

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
2. **JS 모듈 테스트** - JS 모듈 파일 로드 확인
   - 현재: 2개 (constants.js, helpers.js)
   - Phase 3 완료 후: 13개 (+ 11개 feature 모듈)
3. **API 테스트** - 10개 API 엔드포인트 확인
4. **DOM 테스트** - 17개 DOM 요소 확인
5. **JS 함수 테스트** - 주요 함수 존재 확인

### 섹션별 테스트 체크포인트

| 섹션 | 테스트 항목 |
|------|------------|
| **Market - Economy** | 환율 차트, 금리 차트, 물가 차트, GDP 차트, 수출입 차트, 고용 차트, 경제성장률 차트 |
| **Market - Logistics** | 물류 지수 표시 |
| **Smart Tools** | 환율 계산기 동작 |
| **War Room** | 지도 로드, 알림 표시 |
| **Headlines** | 뉴스 카드 표시 |
