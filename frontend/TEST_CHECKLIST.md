# 🧪 프론트엔드 기능 테스트 체크리스트

> 파일 분리 작업 시 각 단계마다 이 체크리스트를 실행하여 기능 정상 동작을 확인하세요.

## 테스트 방법

1. 브라우저에서 `http://localhost:5000` 접속
2. 각 항목을 순서대로 테스트
3. 브라우저 개발자 도구(F12) 콘솔에서 에러 확인
4. 문제 발생 시 해당 모듈만 롤백

---

## 🔴 CRITICAL: 분리 전 반드시 테스트 (기준점 설정)

**분리 작업 시작 전에 현재 상태가 정상인지 확인하세요!**

```bash
# 1. 서버 실행
python server/main.py

# 2. 백엔드 API 테스트
python server/test_server.py

# 3. 프론트엔드 테스트
http://localhost:5000/test_frontend.html
```

---

## 📊 Economy 탭 테스트

### 1. 환율 (Exchange Rate) - `#economy-panel`
| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 차트 로드 | 페이지 로드 후 대기 | 환율 차트 표시 | |
| 기간 변경 | 1W, 1M, 3M, 1Y 버튼 클릭 | 차트 데이터 변경 | |
| 통화 토글 | USD, JPY, EUR 등 클릭 | 해당 통화 차트에 추가/제거 | |
| 날짜 직접 입력 | 날짜 선택 후 조회 | 해당 기간 데이터 로드 | |
| 툴팁 | 차트 위 마우스 오버 | 날짜, 환율 표시 | |
| 환율 계산기 | 금액 입력 | 변환 결과 표시 | |
| 헤더 통계 | - | 현재가, 변동률, 고저 표시 | |

### 2. 금리 (Interest Rates) - `#interest-rates-panel`
| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 차트 로드 | 사이드바에서 "Interest Rates" 클릭 | 금리 차트 표시 | |
| 국가 선택 | 국가 칩 클릭 | 해당 국가 금리 표시 | |
| 다중 국가 | 여러 국가 선택 | 여러 선 차트 표시 | |
| 기간 변경 | 기간 버튼 클릭 | 차트 데이터 변경 | |
| 툴팁 | 차트 위 마우스 오버 | 국가별 금리 표시 | |

### 3. 물가 (Inflation) - `#inflation-panel`
| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 차트 로드 | 사이드바에서 "Inflation" 클릭 | 물가 차트 표시 | |
| 항목 선택 | 총지수/신선식품 등 선택 | 해당 데이터 표시 | |
| 기간 변경 | 기간 버튼 클릭 | 차트 데이터 변경 | |
| 헤더 통계 | - | 현재 지수, 변동률 표시 | |

### 4. 주요 지표 (GDP) - `#gdp-panel`
| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 차트 로드 | 사이드바에서 "주요 지표" 클릭 | GDP 차트 표시 | |
| 서브메뉴 | GDP 호버 시 서브메뉴 표시 | 세부 지표 선택 가능 | |
| 통화 전환 | KRW/USD 버튼 클릭 | 통화 단위 변경 | |
| 기간 변경 | 연도 입력 | 해당 기간 데이터 로드 | |

### 5. 수출입 통계 (Trade) - `#trade-panel`
| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 차트 로드 | 사이드바에서 "수출입 통계" 클릭 | 무역 차트 표시 | |
| 바 차트 | 수출/수입 바 차트 표시 | 월별 데이터 표시 | |
| 성장률 선 | 성장률 라인 차트 | 전년 대비 성장률 | |
| 무역수지 | 무역수지 표시 | 흑자/적자 색상 구분 | |
| 지표 토글 | 수출/수입/무역수지 토글 | 표시/숨김 전환 | |
| 툴팁 | 차트 위 마우스 오버 | 상세 수치 표시 | |

### 6. 고용 통계 (Employment) - `#employment-panel`
| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 차트 로드 | 사이드바에서 "고용 통계" 클릭 | 고용 차트 표시 | |
| 실업률 | 실업률 데이터 표시 | 차트에 표시 | |

### 7. 경제 성장률 (Economy Growth Rate) - `#gdp-growth-panel`
| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 차트 로드 | 사이드바에서 "Economy Growth Rate" 클릭 | 성장률 차트 표시 | |

---

## 🚀 Logistics 탭 테스트 - `#logistics-panel`

| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 탭 전환 | "Logistics" 탭 클릭 | Logistics 패널 표시 | |
| SCFI/BDI | 지수 데이터 표시 | 현재값, 변동률 표시 | |

---

## 🌍 War Room 테스트 - `#war-room`

| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 지도 로드 | War Room 섹션 스크롤 | Google Maps 로드 | |
| 마커 표시 | 지도에 경고 마커 | 위험 지역 표시 | |
| 마커 클릭 | 마커 클릭 | 상세 정보 모달 표시 | |
| 필터링 | 심각도 필터 클릭 | 해당 심각도만 표시 | |
| 뷰 전환 | Map/Timeline/Country 탭 | 뷰 전환 | |
| 알림 목록 | 사이드바 목록 | 최신 알림 표시 | |

---

## 🔧 Smart Tools 테스트 - `#tools-apps`

| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 카드 표시 | Tools 섹션 확인 | CBM, 관세, HS Code 카드 | |
| 호버 효과 | 카드 위 마우스 오버 | 애니메이션 효과 | |

---

## 📰 News 섹션 테스트 - `#news`

| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 뉴스 목록 | News 섹션 확인 | 뉴스 항목 표시 | |
| 날짜/태그 | 각 뉴스 항목 확인 | 날짜, 태그 정상 표시 | |

---

## 🎨 공통 UI 테스트

| 항목 | 테스트 방법 | 예상 결과 | ✅/❌ |
|------|------------|----------|------|
| 헤더 고정 | 스크롤 | 헤더가 상단에 고정 | |
| 네비게이션 | 메뉴 클릭 | 해당 섹션으로 스크롤 | |
| 스크롤 애니메이션 | 섹션 스크롤 | fade-up 애니메이션 | |
| 반응형 | 창 크기 조절 | 레이아웃 적응 | |
| 다크 테마 | 전체 페이지 | 다크 모드 스타일 | |

---

## 🔍 콘솔 에러 체크

**테스트 완료 후 반드시 확인:**

```javascript
// 브라우저 콘솔(F12)에서 실행
// 에러가 없어야 함

// 1. 에러 확인 (빨간색 메시지가 없어야 함)
// 2. 경고 확인 (주요 기능 관련 경고 없어야 함)

// 주요 전역 변수 확인
console.log('=== 전역 변수 상태 ===');
console.log('exchangeRates:', typeof exchangeRates !== 'undefined' ? '✅' : '❌');
console.log('activeCurrencies:', typeof activeCurrencies !== 'undefined' ? '✅' : '❌');
console.log('chartData:', typeof chartData !== 'undefined' ? '✅' : '❌');
console.log('API_BASE:', typeof API_BASE !== 'undefined' ? '✅' : '❌');

// 주요 함수 확인
console.log('=== 주요 함수 상태 ===');
console.log('switchTab:', typeof switchTab === 'function' ? '✅' : '❌');
console.log('switchProduct:', typeof switchProduct === 'function' ? '✅' : '❌');
console.log('toggleCurrency:', typeof toggleCurrency === 'function' ? '✅' : '❌');
console.log('initInterestRates:', typeof initInterestRates === 'function' ? '✅' : '❌');
console.log('initInflation:', typeof initInflation === 'function' ? '✅' : '❌');
console.log('initGDP:', typeof initGDP === 'function' ? '✅' : '❌');
console.log('initTrade:', typeof initTrade === 'function' ? '✅' : '❌');
console.log('loadGoogleMapsAPI:', typeof loadGoogleMapsAPI === 'function' ? '✅' : '❌');
```

---

## 📝 테스트 결과 기록 템플릿

```
테스트 일시: ____년 __월 __일 __:__
테스트 단계: [ ] CSS 분리 / [ ] config.js / [ ] utils.js / [ ] 기능모듈
담당자: ________

| 모듈 | 결과 | 비고 |
|------|------|------|
| 환율 | ✅/❌ | |
| 금리 | ✅/❌ | |
| 물가 | ✅/❌ | |
| GDP | ✅/❌ | |
| 수출입 | ✅/❌ | |
| 고용 | ✅/❌ | |
| 경제 성장률 | ✅/❌ | |
| Logistics | ✅/❌ | |
| War Room | ✅/❌ | |
| Tools | ✅/❌ | |
| News | ✅/❌ | |
| UI/애니메이션 | ✅/❌ | |

발견된 문제:
1. 
2. 

조치 사항:
1. 
2. 
```

---

## 🚨 문제 발생 시 롤백 방법

```bash
# Git으로 관리 시
git checkout -- frontend/ai_studio_code_F2.html
git checkout -- frontend/js/
git checkout -- frontend/css/

# 또는 특정 커밋으로 복구
git revert HEAD
```

---

## 🎨 CSS 파일 로드 확인

분리된 CSS 파일들이 모두 로드되는지 확인:

| CSS 파일 | 상태 |
|----------|------|
| `css/variables.css` | |
| `css/base.css` | |
| `css/components/header.css` | |
| `css/components/buttons.css` | |
| `css/components/charts.css` | |
| `css/components/cards.css` | |
| `css/components/modals.css` | |
| `css/sections/hero.css` | |
| `css/sections/market.css` | |
| `css/sections/tools.css` | |
| `css/sections/war-room.css` | |
| `css/sections/news.css` | |

**확인 방법:**
```bash
# 브라우저에서 테스트 페이지 열기
http://localhost:5000/test_frontend.html

# "CSS 파일 테스트" 버튼 클릭
```
