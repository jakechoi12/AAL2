# AAL (All About Logistics) 프로젝트 분석 및 경쟁사 비교

> 작성일: 2026-01-09
> 버전: 1.0

---

## 1. 프로젝트 개요

### 1.1 서비스 정의

**AAL (All About Logistics)**은 물류/포워딩 업계 종사자들을 위한 **종합 시장 정보 및 운영 지원 B2B 플랫폼**입니다.

| 항목 | 내용 |
|------|------|
| 서비스명 | AAL (All About Logistics) |
| 타겟 사용자 | 화주(Shipper), 포워더(Forwarder) |
| 핵심 가치 | 시장 정보 + 거래 플랫폼 + 위기 관리의 통합 |
| 기술 스택 | Flask, FastAPI, Vanilla JS, SQLite |

### 1.2 핵심 기능 요약

| 카테고리 | 기능 |
|----------|------|
| 시장 데이터 | 환율, GDP, 물가, 금리, 무역수지 시각화 |
| 물류 지수 | KCCI, BDI, SCFI, CCFI 모니터링 |
| 견적 시스템 | 견적 요청, 입찰, 계약, 정산 관리 |
| 뉴스 인텔리전스 | AI 기반 물류 뉴스 수집/분석 |
| 글로벌 알림 | GDELT 기반 위기 상황 모니터링 |
| 대시보드 | 화주/포워더 맞춤형 성과 분석 |

---

## 2. 프로젝트 상세 구성

### 2.1 디렉토리 구조

```
AAL/
├── server/                    # Flask 메인 백엔드 (Port 5000)
│   ├── main.py               # Flask 애플리케이션
│   ├── bok_backend.py        # 한국은행 ECOS API 연동
│   ├── gdelt_backend.py      # GDELT 글로벌 이벤트 API
│   ├── auth/                 # 사용자 인증
│   ├── news_intelligence/    # AI 뉴스 분석
│   ├── shipping_indices/     # 해운 지수 (BDI, SCFI, CCFI)
│   ├── kcci/                 # 한국 컨테이너 운임지수
│   └── report/               # 리포트 생성
│
├── quote_backend/             # FastAPI 견적 백엔드 (Port 8001)
│   ├── main.py               # FastAPI 애플리케이션
│   ├── models.py             # SQLAlchemy 모델
│   ├── schemas.py            # Pydantic 스키마
│   ├── pdf_generator.py      # PDF 견적서 생성
│   └── email_service.py      # 이메일 서비스
│
├── frontend/                  # 프론트엔드
│   ├── ai_studio_code_F2.html # 메인 페이지
│   ├── pages/                # 21개 서브 페이지
│   ├── js/                   # JavaScript 모듈
│   └── css/                  # 스타일시트
│
├── docs/                      # 문서
│   ├── api/                  # API 문서
│   ├── gdelt/                # GDELT 관련 문서
│   └── product_planning/     # 제품 기획 문서
│
└── data/                      # 데이터 파일
    └── gdelt/                # GDELT 데이터
```

### 2.2 프론트엔드 페이지 구성

| 카테고리 | 페이지 | 파일명 |
|----------|--------|--------|
| **메인** | 대시보드 | `ai_studio_code_F2.html` |
| **시장 데이터** | 시장 데이터 | `market-data.html` |
| **견적** | 견적 조회 | `quotation.html` |
| | 견적 등록 | `quote-registration.html` |
| **입찰** | 입찰 목록 (포워더) | `bidding-list.html` |
| | 입찰 관리 (화주) | `shipper-bidding.html` |
| **계약/운송** | 계약 관리 | `contract-management.html` |
| | 운송 추적 | `shipment-tracking.html` |
| **분석** | 화주 분석 | `analytics-shipper.html` |
| | 포워더 분석 | `analytics-forwarder.html` |
| | 화주 대시보드 | `dashboard-shipper.html` |
| | 포워더 대시보드 | `dashboard-forwarder.html` |
| **뉴스/알림** | 뉴스 인텔리전스 | `news-intelligence.html` |
| | War Room | `war-room.html` |
| **리포트** | 리포트 상세 | `report-detail.html` |
| | 리포트 인사이트 | `report-insight.html` |
| **회원/정책** | 마이페이지 | `mypage.html` |
| | 개인정보처리방침 | `privacy.html` |
| | 이용약관 | `terms.html` |
| | 분쟁해결정책 | `dispute-policy.html` |
| **에러** | 404 에러 | `404.html` |
| | 500 에러 | `500.html` |

### 2.3 JavaScript 모듈 구조

```
frontend/js/
├── main.js                    # 메인 진입점
├── config/
│   ├── api.js                # API 설정
│   └── constants.js          # 상수 정의
├── core/
│   ├── loading.js            # 로딩 UI
│   └── toast.js              # 토스트 알림
├── features/
│   ├── auth.js               # 인증
│   ├── analytics.js          # 분석
│   ├── dashboard.js          # 대시보드
│   ├── biddingList.js        # 입찰 목록
│   ├── contractManagement.js # 계약 관리
│   ├── shipmentTracking.js   # 운송 추적
│   ├── shipperBidding.js     # 화주 입찰
│   ├── quoteRegistration.js  # 견적 등록
│   ├── mypage.js             # 마이페이지
│   ├── onboarding.js         # 온보딩
│   ├── market/               # 시장 데이터
│   │   ├── economy/          # 경제 지표
│   │   └── logistics/        # 물류 지수
│   ├── headlines/
│   │   └── news.js           # 헤드라인 뉴스
│   ├── news-intelligence/
│   │   └── news-intelligence.js
│   ├── report-insight/
│   │   └── report-insight.js
│   ├── war-room/
│   │   └── global-alarm.js
│   └── tools/
│       └── tools.js          # 유틸리티 도구
└── utils/
    └── helpers.js            # 헬퍼 함수
```

### 2.4 데이터베이스 구성

| DB 파일 | 위치 | 용도 |
|---------|------|------|
| `quote.db` | `quote_backend/` | 견적, 입찰, 계약, 정산, 평점 |
| `news_intelligence.db` | `server/` | 뉴스 아티클, 수집 로그 |
| `shipping_indices.db` | `server/` | BDI, SCFI, CCFI 데이터 |
| `kcci.db` | `server/` | KCCI 운임지수 |
| `reports.db` | `server/` | 리포트 데이터 |
| `auth.db` | `server/auth/` | 사용자 인증 |

### 2.5 자동화 스케줄 작업

| 작업 | 주기 | 설명 |
|------|------|------|
| GDELT 업데이트 | 15분 | 글로벌 이벤트 데이터 수집 |
| 뉴스 수집 | 1시간 | RSS, GDELT, Google/Naver News |
| KCCI 수집 | 매주 월요일 14:30 KST | 한국 컨테이너 운임지수 |

---

## 3. 핵심 기능 상세

### 3.1 시장 데이터 (Market Data)

#### 데이터 소스
- **한국은행 ECOS API**: 환율, GDP, 물가, 금리 등

#### 지원 환율 (9개 통화)
| 통화 | 코드 | item_code |
|------|------|-----------|
| 미국 달러 | USD | 0000001 |
| 유로 | EUR | 0000003 |
| 일본 엔화 | JPY | 0000002 |
| 중국 위안화 | CNY | 0000053 |
| 영국 파운드 | GBP | 0000012 |
| 스위스 프랑 | CHF | 0000014 |
| 홍콩 달러 | HKD | 0000015 |
| 캐나다 달러 | CAD | 0000013 |
| 러시아 루블 | RUB | 0000043 |

#### 경제 지표
- GDP / GDP 성장률 / 1인당 GDP
- GNI (국민총소득)
- 소비자물가지수 (CPI)
- 기준금리
- 고용 지표
- 무역수지
- 글로벌 주가지수

### 3.2 물류 지수 (Shipping Indices)

| 지수 | 설명 | 업데이트 |
|------|------|----------|
| **KCCI** | Korea Container Cargo Index (한국 컨테이너 화물 지수) | 매주 월요일 |
| **BDI** | Baltic Dry Index (발틱 건화물 지수) | 엑셀 파일 |
| **SCFI** | Shanghai Container Freight Index (상하이 컨테이너 운임지수) | 엑셀 파일 |
| **CCFI** | China Container Freight Index (중국 컨테이너 운임지수) | 엑셀 파일 |

### 3.3 견적 시스템 (Quote Backend)

#### 주요 엔티티
```
Port              - 항구 마스터
ContainerType     - 컨테이너 타입 (20ft, 40ft 등)
TruckType         - 트럭 타입
Incoterm          - 인코텀즈 (FOB, CIF 등)
Customer          - 고객 (화주)
Forwarder         - 포워더
QuoteRequest      - 견적 요청
CargoDetail       - 화물 상세
Bidding           - 입찰 공고
Bid               - 입찰
Contract          - 계약
Shipment          - 선적
ShipmentTracking  - 운송 추적
Settlement        - 정산
Message           - 메시지
Rating            - 평점
FavoriteRoute     - 즐겨찾기 구간
BidTemplate       - 입찰 템플릿
```

#### 주요 기능
- 견적 요청 생성/조회/수정
- 포워더 입찰 등록/수정
- 낙찰 및 계약 체결
- 선적 상태 추적
- 정산 관리
- 화주-포워더 메시징
- 포워더 평점/리뷰
- PDF 견적서 자동 생성

### 3.4 뉴스 인텔리전스 (News Intelligence)

#### 데이터 소스
| 소스 | 유형 | 대상 |
|------|------|------|
| The Loadstar | RSS | 국제 |
| FreightWaves | RSS | 국제 |
| Supply Chain Dive | RSS | 국제 |
| Splash247 | RSS | 국제 |
| Air Cargo Week | RSS | 국제 |
| 물류신문 | RSS | 국내 |
| 해운신문 | RSS | 국내 |
| 카고뉴스 | RSS | 국내 |
| GDELT | API | 글로벌 이벤트 |
| Google News | Search | 키워드 검색 |
| Naver News | API | 국내 검색 |

#### AI 분석 최적화
| 방식 | 비용 | 속도 | 정확도 |
|------|------|------|--------|
| 규칙 기반 | 무료 | 빠름 | 85% |
| AI 배치 | 저비용 | 중간 | 95% |

- **비용 절감**: 87% (규칙 기반 우선 처리)
- **처리 시간**: 80% 단축

#### 카테고리 분류
| 카테고리 | 설명 |
|----------|------|
| Crisis | 파업, 사고, 재해, 분쟁 |
| Ocean | 해운, 항만, 컨테이너 |
| Air | 항공화물, 공항 |
| Inland | 트럭, 철도, 창고 |
| Economy | 운임, 수요, 무역정책 |
| ETC | 기타 |

### 3.5 글로벌 알림 (War Room)

#### GDELT 기반 기능
- 실시간 글로벌 이벤트 모니터링
- Goldstein Scale 기반 위기 평가
- 국가별/카테고리별 통계
- 트렌드 분석

#### 알림 임계값
- Goldstein Scale < -5.0: 위기 상황

---

## 4. 기술 스택

### 4.1 백엔드

| 구성요소 | 기술 | 포트 |
|----------|------|------|
| Main Backend | Flask (Python) | 5000 |
| Quote Backend | FastAPI (Python) | 8001 |
| Database | SQLite | - |
| Scheduler | APScheduler | - |
| PDF 생성 | ReportLab | - |

### 4.2 프론트엔드

| 구성요소 | 기술 |
|----------|------|
| HTML | HTML5 |
| CSS | CSS3 (CSS Variables) |
| JavaScript | Vanilla ES6+ |
| 차트 | Chart.js |

### 4.3 외부 API

| API | 용도 |
|-----|------|
| 한국은행 ECOS | 경제 통계 데이터 |
| GDELT | 글로벌 이벤트 |
| Google Maps | 지도 시각화 |
| OpenAI | 뉴스 분석 |

---

## 5. 경쟁사 분석

### 5.1 글로벌 경쟁사

#### Freightos
| 항목 | 내용 |
|------|------|
| 서비스 | 글로벌 운임 비교/예약 플랫폼 |
| 강점 | 실시간 운임 비교, 즉시 예약, 광범위한 커버리지 |
| 약점 | 유료 서비스, 주로 해외 시장 타겟 |
| 타겟 | 중대형 화주, 포워더 |

#### Xeneta
| 항목 | 내용 |
|------|------|
| 서비스 | 해상 운임 데이터 분석 플랫폼 |
| 강점 | 실시간 시장 운임 벤치마킹, 계약 운임 데이터 |
| 약점 | 고가의 엔터프라이즈 솔루션 |
| 타겟 | 대기업, 컨설팅 |

#### Container xChange
| 항목 | 내용 |
|------|------|
| 서비스 | 컨테이너 거래 플랫폼 |
| 강점 | 컨테이너 리스/트레이딩 전문 |
| 약점 | 컨테이너 거래에만 특화 |
| 타겟 | 선사, 리스 업체 |

#### MarineTraffic
| 항목 | 내용 |
|------|------|
| 서비스 | 선박 추적 서비스 |
| 강점 | 실시간 AIS 추적, 광범위한 선박 데이터 |
| 약점 | 선박 추적에만 특화 |
| 타겟 | 선사, 항만, 트레이더 |

### 5.2 국내 경쟁사

#### 트레드링스
| 항목 | 내용 |
|------|------|
| 서비스 | 수출입 물류 플랫폼 |
| 강점 | 포워딩 매칭, 운임 비교, 국내 시장 이해 |
| 약점 | 운임 데이터에 집중 |
| 타겟 | 중소 화주 |

#### 쉽다 (Shipda)
| 항목 | 내용 |
|------|------|
| 서비스 | 화물 운송 중개 플랫폼 |
| 강점 | 간편한 UI, 빠른 견적 |
| 약점 | 중소기업 타겟에 집중 |
| 타겟 | 스타트업, 중소 화주 |

#### 로지스팟
| 항목 | 내용 |
|------|------|
| 서비스 | B2B 물류 중개 플랫폼 |
| 강점 | 육상 물류 강점 |
| 약점 | 해상/항공 약함 |
| 타겟 | 내수 물류 기업 |

#### 포워딩닷컴
| 항목 | 내용 |
|------|------|
| 서비스 | 포워더 정보 플랫폼 |
| 강점 | 4,000개 포워더 빅데이터 |
| 약점 | 정보 제공에 집중, 거래 기능 미흡 |
| 타겟 | 화주 |

#### KL-Net (PLISM 3.0)
| 항목 | 내용 |
|------|------|
| 서비스 | 통합 물류 정보 시스템 |
| 강점 | 관세청 연동, 전자문서, 공신력 |
| 약점 | 복잡한 시스템, 사용성 |
| 타겟 | 관세사, 포워더 |

### 5.3 기능 비교 매트릭스

| 기능 | AAL | Freightos | Xeneta | 트레드링스 | KL-Net |
|------|:---:|:---------:|:------:|:---------:|:------:|
| 실시간 환율 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 물류 지수 (BDI/SCFI) | ✅ | ⚪ | ✅ | ⚪ | ❌ |
| 경제 지표 (GDP/물가) | ✅ | ❌ | ❌ | ❌ | ❌ |
| 견적 요청/입찰 | ✅ | ✅ | ❌ | ✅ | ⚪ |
| 글로벌 뉴스/알림 | ✅ | ❌ | ⚪ | ❌ | ❌ |
| AI 뉴스 분석 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 위기 상황 모니터링 | ✅ | ❌ | ⚪ | ❌ | ❌ |
| 화주/포워더 대시보드 | ✅ | ⚪ | ✅ | ⚪ | ⚪ |
| 운송 추적 | ✅ | ✅ | ❌ | ✅ | ✅ |
| 리포트/인사이트 | ✅ | ⚪ | ✅ | ❌ | ⚪ |
| 한국 시장 특화 | ✅ | ❌ | ❌ | ✅ | ✅ |

> ✅ = 지원 | ⚪ = 부분 지원 | ❌ = 미지원

---

## 6. AAL 경쟁력 분석

### 6.1 강점 (Strengths)

| 항목 | 설명 |
|------|------|
| **올인원 플랫폼** | 시장 데이터 + 견적 + 뉴스 + 분석을 한 곳에서 제공 |
| **AI 뉴스 인텔리전스** | 규칙 기반 + AI 하이브리드로 비용 최적화 (87% 절감) |
| **War Room** | GDELT 기반 실시간 글로벌 위기 모니터링 (경쟁사 없음) |
| **한국 시장 특화** | KCCI, 한국은행 ECOS 연동, 국내 뉴스 수집 |
| **화주/포워더 양면 서비스** | 양쪽 사용자 모두를 위한 맞춤형 대시보드 |
| **접근성** | 무료/오픈소스 지향으로 고가 서비스 대비 접근성 우수 |

### 6.2 약점 (Weaknesses)

| 항목 | 현재 상태 | 개선 방향 |
|------|----------|----------|
| 실시간 운임 데이터 | 지수만 제공 | 실제 운임 데이터 확보 필요 |
| 선박 추적 | 미지원 | AIS 연동 검토 |
| 모바일 | 웹만 지원 | 반응형 개선 또는 앱 개발 |
| 결제 자동화 | 기본 수준 | PG 연동 필요 |

### 6.3 기회 (Opportunities)

| 항목 | 설명 |
|------|------|
| B2B API 상품화 | 내부 API를 외부에 제공하여 수익화 |
| 데이터 판매 | 시장 데이터 리포트 구독 서비스 |
| 해외 진출 | 동남아 등 신흥 물류 시장 진출 |
| AI 고도화 | 운임 예측, 위험 분석 등 AI 기능 확대 |

### 6.4 위협 (Threats)

| 항목 | 설명 |
|------|------|
| 대기업 진출 | 네이버, 카카오 등 플랫폼 기업의 물류 진출 |
| 글로벌 경쟁사 | Freightos, Xeneta 등의 국내 시장 공략 |
| 데이터 확보 | 실시간 운임 데이터 확보 어려움 |

---

## 7. 시장 포지셔닝

```
                    시장 정보 중심
                         │
         Xeneta ─────────┼───────── AAL (목표)
                         │
     데이터 분석 ─────────┼───────── 거래 플랫폼
                         │
       KL-Net ───────────┼───────── Freightos
                         │
                    운영 효율 중심
```

### AAL의 포지션

**"시장 정보 + 거래 플랫폼의 통합 솔루션"**

- 기존 서비스들이 **시장 데이터(Xeneta)** 또는 **거래 플랫폼(Freightos)** 중 하나에 집중
- AAL은 **양쪽을 통합**하여 물류 전문가가 한 곳에서 모든 업무를 처리

---

## 8. 결론 및 권장사항

### 8.1 핵심 가치 제안

AAL은 물류 업계를 위한 **"올인원" B2B 정보 플랫폼**으로:

1. **시장 인텔리전스**: 환율, 물류 지수, AI 뉴스 분석
2. **거래 플랫폼**: 견적, 입찰, 계약, 정산
3. **위기 관리**: 글로벌 알림, War Room

이 세 가지를 통합한 점에서 기존 경쟁 서비스 대비 **차별화된 가치**를 제공합니다.

### 8.2 단기 개선 권장사항

| 우선순위 | 항목 | 기대 효과 |
|----------|------|----------|
| 1 | 모바일 반응형 개선 | 사용성 향상 |
| 2 | 실시간 운임 데이터 연동 | 핵심 가치 강화 |
| 3 | 선박 추적 기능 추가 | 경쟁력 확보 |
| 4 | 결제 시스템 연동 | 거래 완결성 |

### 8.3 중장기 발전 방향

| 기간 | 목표 |
|------|------|
| 6개월 | 실시간 운임 데이터 확보, 모바일 최적화 |
| 1년 | 선박 추적, AI 운임 예측 기능 |
| 2년 | 동남아 시장 진출, B2B API 상품화 |

---

## 부록

### A. API 엔드포인트 요약

#### Main Backend (Flask - Port 5000)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/bok/stats` | GET | 한국은행 통계 조회 |
| `/api/market/indices` | GET | 시장 지수 조회 |
| `/api/market/indices/multi` | GET | 다중 시장 지수 조회 |
| `/api/market/categories` | GET | 카테고리 정보 |
| `/api/global-alerts` | GET | GDELT 글로벌 알림 |
| `/api/news-intelligence/*` | GET/POST | 뉴스 인텔리전스 |
| `/api/shipping-indices/*` | GET | 해운 지수 |
| `/api/kcci/*` | GET | KCCI 지수 |
| `/api/reports/*` | GET/POST | 리포트 |
| `/api/auth/*` | POST | 인증 |

#### Quote Backend (FastAPI - Port 8001)

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/quotes/*` | CRUD | 견적 관리 |
| `/api/biddings/*` | CRUD | 입찰 관리 |
| `/api/contracts/*` | CRUD | 계약 관리 |
| `/api/shipments/*` | CRUD | 운송 관리 |
| `/api/settlements/*` | CRUD | 정산 관리 |
| `/api/forwarders/*` | CRUD | 포워더 관리 |
| `/api/analytics/*` | GET | 분석 데이터 |
| `/api/dashboard/*` | GET | 대시보드 데이터 |

### B. 환경 변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `ECOS_API_KEY` | Yes | 한국은행 ECOS API 키 |
| `GOOGLE_MAPS_API_KEY` | No | Google Maps API 키 |
| `OPENAI_API_KEY` | No | OpenAI API 키 (뉴스 분석) |
| `DATABASE_URL` | No | PostgreSQL URL (기본: SQLite) |

### C. 참고 문서

- [한국은행 ECOS API 가이드](http://ecos.bok.or.kr/api/)
- [GDELT Project](https://www.gdeltproject.org/)
- [통화 매핑 테이블](./currency/CURRENCY_MAPPING_TABLE.md)
- [대시보드 기획안](./DASHBOARD_PLAN.md)
- [뉴스 인텔리전스 API](./news/NEWS_INTELLIGENCE_API.md)

---

*문서 끝*
