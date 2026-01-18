## 📊 기존 코드베이스 분석 결과

### 🏗️ 기술 스택

| 영역                   | 기술                | 비고                   |
| ---------------------- | ------------------- | ---------------------- |
| **메인 서버**    | Flask (Python)      | Port 5000              |
| **견적 백엔드**  | FastAPI (Python)    | Port 8001              |
| **프론트엔드**   | Vanilla HTML/CSS/JS | 페이지 기반 (SPA 아님) |
| **데이터베이스** | SQLite + SQLAlchemy | 모듈별 분리 DB         |
| **AI**           | Gemini API          | `gemini_backend.py`  |

---

### 🧩 기존 모듈 & 재활용 가능 컴포넌트

#### 1. 🔐 인증 시스템 (`server/auth/`) ✅ **그대로 사용 가능**

- 회원가입/로그인/비밀번호 변경
- User 모델 (shipper/forwarder 타입)
- bcrypt 암호화

#### 2. 📦 물류 견적/비딩 시스템 (`quote_backend/`) ✅ **핵심 재활용**

매우 완성도 높은 시스템!

```
모델: Port, ContainerType, Incoterm, Customer, QuoteRequest, 
      Bidding, Bid, Contract, Shipment, Rating, Notification, Message
```

**주요 기능:**

- RFQ 생성 → 비딩 발행 → 견적 수신 → 낙찰 → 계약 → 배송추적
- PDF 생성, 이메일 알림
- 포워더 평점 시스템
- 분석 대시보드 (화주/포워더)

#### 3. 📰 뉴스 인텔리전스 (`server/news_intelligence/`) ✅ **연동**

- 다중 소스 수집 (Google, Naver, GDELT, RSS)
- AI 분석 (카테고리, 위기감지, 키워드)
- 워드클라우드, 지도 데이터

#### 4. 📑 리포트 인사이트 (`server/report/`) ✅ **연동**

- 리포트 CRUD, PDF 다운로드
- 관련 리포트 추천

#### 5. 📈 마켓 데이터 (`server/bok/`, `server/shipping_indices/`) ✅ **연동**

- 한국은행 API (환율, 금리, GDP 등)
- 해운 지수 (SCFI, CCFI, BDI)

---

### 🆕 B2B Commerce 프로토타입 - 신규 개발 필요 항목

| 구분                    | 내용                                                | 우선순위 |
| ----------------------- | --------------------------------------------------- | -------- |
| **기업 디렉토리** | Company 모델 확장 (Buyer/Seller), 프로필, 인증 배지 | 🔴 P0    |
| **상품 카탈로그** | Product, Category 모델 신규                         | 🔴 P0    |
| **상품 RFQ**      | 물류와 별도의 상품 RFQ 시스템                       | 🔴 P0    |
| **AI 에이전트**   | 대화형 RFQ 생성, 추천, 자동 초안                    | 🟡 P1    |
| **거래 관리**     | Transaction, Payment 프로세스                       | 🟡 P1    |

---

### 📁 기존 프론트엔드 페이지 현황

```
frontend/pages/
├── dashboard-shipper.html    # 화주 대시보드
├── dashboard-forwarder.html  # 포워더 대시보드
├── quotation.html            # 견적 요청
├── bidding-list.html         # 비딩 목록
├── shipper-bidding.html      # 화주 비딩 관리
├── contract-management.html  # 계약 관리
├── shipment-tracking.html    # 배송 추적
├── news-intelligence.html    # 뉴스 인텔리전스
├── market-data.html          # 마켓 데이터
├── report-insight.html       # 리포트 인사이트
├── company.html              # 회사 정보
└── mypage.html               # 마이페이지
```

---

## 🚀 프로토타입 개발 계획 제안

### Phase 1: 핵심 데이터 모델 & API (1주)

```
1. Company 모델 확장 (Buyer/Seller/Both 타입)
2. Product, Category 모델 생성
3. 상품 RFQ/Quotation 모델 생성
4. 기본 CRUD API 구현
```

### Phase 2: 핵심 UI 구현 (1주)

```
1. 기업 디렉토리 페이지
2. 상품 카탈로그 페이지
3. 상품 RFQ 작성/목록/상세 페이지
4. 견적 비교 페이지
```

### Phase 3: AI & 통합 (1주)

```
1. AI 에이전트 기본 기능 (RFQ 초안 생성)
2. 기존 물류 시스템 연동
3. 인텔리전스 피드 연동
4. 대시보드 통합
```
