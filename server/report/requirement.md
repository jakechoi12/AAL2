# 실행방법

# JSON + PDF seed

python -m report.seed

# Legacy 샘플 데이터

python -m report.seed --legacy --force

# 데이터 삭제

python -m report.seed --clear

# 요구정의서

## 0. 목표

* 운영자가 직접 확보한 PDF 리포트를 **DB(Postgres)에 직접 적재**
* 사용자는
  * 리포트 리스트에서 검색/필터/정렬
  * 리포트 디테일에서 요약/인사이트 확인
  * PDF 다운로드
  * 연관 리포트 확인
* **로그인, 권한, 북마크, 공유 링크는 MVP에서 제외**

---

## 1. 기술 전제

* DB: **PostgreSQL**
* 파일 저장: **Postgres **`bytea`** 컬럼에 PDF 저장**
* 리포트 등록 방식: **seed 스크립트(JSON + PDF 파일)**
* 프론트: 이미 제공된 `report-insight.html`, `report-detail.html`
* API: REST (GET 위주)

---

## 2. 제외 범위 (명시)

❌ 로그인 / 회원가입 / 권한
❌ 북마크
❌ 공유 링크
❌ 운영자(Admin) 화면
❌ RSS / 크롤링
❌ PDF 미리보기
❌ 전문 검색(全文 검색)

---

## 3. 데이터 모델 (필수)

### 3.1 `sources` – 발행처

`<span data-testid="renderer-code-block-line-1" data-ds--code--row="" class=""><span class="">id uuid PK </span></span><span data-testid="renderer-code-block-line-2" data-ds--code--row="" class="">name text UNIQUE </span><span data-testid="renderer-code-block-line-3" data-ds--code--row="" class="">type text -- global_research | government | company </span><span data-testid="renderer-code-block-line-4" data-ds--code--row="" class=""></span>`

---

### 3.2 `tags`

`<span data-testid="renderer-code-block-line-1" data-ds--code--row="" class=""><span class="">id uuid PK </span></span><span data-testid="renderer-code-block-line-2" data-ds--code--row="" class="">name text UNIQUE </span><span data-testid="renderer-code-block-line-3" data-ds--code--row="" class=""></span>`

---

### 3.3 `reports`

`<span data-testid="renderer-code-block-line-1" data-ds--code--row="" class=""><span class="">id uuid PK </span></span><span data-testid="renderer-code-block-line-2" data-ds--code--row="" class="">title text </span><span data-testid="renderer-code-block-line-3" data-ds--code--row="" class="">source_id uuid FK -> sources.id </span><span data-testid="renderer-code-block-line-4" data-ds--code--row="" class="">category_key text -- global_research | government | company </span><span data-testid="renderer-code-block-line-5" data-ds--code--row="" class="">published_at date </span><span data-testid="renderer-code-block-line-6" data-ds--code--row="" class="">summary text </span><span data-testid="renderer-code-block-line-7" data-ds--code--row="" class="">key_insights jsonb -- string array </span><span data-testid="renderer-code-block-line-8" data-ds--code--row="" class="">canonical_url text NULL </span><span data-testid="renderer-code-block-line-9" data-ds--code--row="" class="">is_featured boolean DEFAULT false </span><span data-testid="renderer-code-block-line-10" data-ds--code--row="" class="">created_at timestamp </span><span data-testid="renderer-code-block-line-11" data-ds--code--row="" class=""></span>`

---

### 3.4 `report_tag_map`

`<span data-testid="renderer-code-block-line-1" data-ds--code--row="" class=""><span class="">report_id uuid FK </span></span><span data-testid="renderer-code-block-line-2" data-ds--code--row="" class="">tag_id uuid FK </span><span data-testid="renderer-code-block-line-3" data-ds--code--row="" class="">PRIMARY KEY (report_id, tag_id) </span><span data-testid="renderer-code-block-line-4" data-ds--code--row="" class=""></span>`

---

### 3.5 `report_files`

`<span data-testid="renderer-code-block-line-1" data-ds--code--row="" class=""><span class="">id uuid PK </span></span><span data-testid="renderer-code-block-line-2" data-ds--code--row="" class="">report_id uuid FK </span><span data-testid="renderer-code-block-line-3" data-ds--code--row="" class="">file_name text </span><span data-testid="renderer-code-block-line-4" data-ds--code--row="" class="">mime_type text DEFAULT 'application/pdf' </span><span data-testid="renderer-code-block-line-5" data-ds--code--row="" class="">file_size int </span><span data-testid="renderer-code-block-line-6" data-ds--code--row="" class="">sha256 text UNIQUE </span><span data-testid="renderer-code-block-line-7" data-ds--code--row="" class="">file_bytes bytea -- PDF 바이너리 </span><span data-testid="renderer-code-block-line-8" data-ds--code--row="" class="">created_at timestamp </span><span data-testid="renderer-code-block-line-9" data-ds--code--row="" class=""></span>`

---

## 4. 리포트 등록 방식 (운영자 UI 없음)

### 4.1 입력 포맷

* `reports_seed.json`
* `seed_pdfs/` 폴더에 PDF 파일 저장

`<span data-testid="renderer-code-block-line-1" data-ds--code--row="" class=""><span class="">[ </span></span><span data-testid="renderer-code-block-line-2" data-ds--code--row="" class="">  { </span><span data-testid="renderer-code-block-line-3" data-ds--code--row="" class="">    "title": "Global Trade Outlook 2025", </span><span data-testid="renderer-code-block-line-4" data-ds--code--row="" class="">    "source": "OECD", </span><span data-testid="renderer-code-block-line-5" data-ds--code--row="" class="">    "category_key": "global_research", </span><span data-testid="renderer-code-block-line-6" data-ds--code--row="" class="">    "published_at": "2025-12-20", </span><span data-testid="renderer-code-block-line-7" data-ds--code--row="" class="">    "tags": ["Trade", "Macro"], </span><span data-testid="renderer-code-block-line-8" data-ds--code--row="" class="">    "summary": "요약 텍스트...", </span><span data-testid="renderer-code-block-line-9" data-ds--code--row="" class="">    "key_insights": [ </span><span data-testid="renderer-code-block-line-10" data-ds--code--row="" class="">      "글로벌 교역 성장 둔화", </span><span data-testid="renderer-code-block-line-11" data-ds--code--row="" class="">      "아시아 물동량 회복 신호" </span><span data-testid="renderer-code-block-line-12" data-ds--code--row="" class="">    ], </span><span data-testid="renderer-code-block-line-13" data-ds--code--row="" class="">    "canonical_url": "https://...", </span><span data-testid="renderer-code-block-line-14" data-ds--code--row="" class="">    "pdf_path": "./seed_pdfs/oecd_trade_outlook_2025.pdf", </span><span data-testid="renderer-code-block-line-15" data-ds--code--row="" class="">    "is_featured": true </span><span data-testid="renderer-code-block-line-16" data-ds--code--row="" class="">  } </span><span data-testid="renderer-code-block-line-17" data-ds--code--row="" class="">] </span><span data-testid="renderer-code-block-line-18" data-ds--code--row="" class=""></span>`

---

### 4.2 Seed 스크립트 요구사항

`scripts/seed-reports.ts`

* JSON 로드
* source upsert
* tag upsert
* report insert
* PDF 파일 읽기 → sha256 계산
* `report_files.file_bytes`에 저장
* tag 매핑 생성
* 중복 방지:
  * sha256 동일 시 skip 또는 reuse

---

## 5. API 요구사항

### 5.1 리포트 리스트

`GET /api/reports`

#### Query

* `q` (string, optional) – title + summary LIKE
* `category` (all / global_research / government / company)
* `source_ids` (comma separated)
* `tag_ids` (comma separated)
* `date_from`
* `date_to`
* `sort` (newest | oldest | title)
* `page`
* `page_size`

#### Response

`<span data-testid="renderer-code-block-line-1" data-ds--code--row="" class=""><span class="">{ </span></span><span data-testid="renderer-code-block-line-2" data-ds--code--row="" class="">  "items": [ </span><span data-testid="renderer-code-block-line-3" data-ds--code--row="" class="">    { </span><span data-testid="renderer-code-block-line-4" data-ds--code--row="" class="">      "id": "uuid", </span><span data-testid="renderer-code-block-line-5" data-ds--code--row="" class="">      "title": "string", </span><span data-testid="renderer-code-block-line-6" data-ds--code--row="" class="">      "category_key": "government", </span><span data-testid="renderer-code-block-line-7" data-ds--code--row="" class="">      "published_at": "2025-12-29", </span><span data-testid="renderer-code-block-line-8" data-ds--code--row="" class="">      "source": { "name": "MOEF" }, </span><span data-testid="renderer-code-block-line-9" data-ds--code--row="" class="">      "tags": ["Trade"], </span><span data-testid="renderer-code-block-line-10" data-ds--code--row="" class="">      "summary": "..." </span><span data-testid="renderer-code-block-line-11" data-ds--code--row="" class="">    } </span><span data-testid="renderer-code-block-line-12" data-ds--code--row="" class="">  ], </span><span data-testid="renderer-code-block-line-13" data-ds--code--row="" class="">  "page": 1, </span><span data-testid="renderer-code-block-line-14" data-ds--code--row="" class="">  "page_size": 12, </span><span data-testid="renderer-code-block-line-15" data-ds--code--row="" class="">  "total": 42 </span><span data-testid="renderer-code-block-line-16" data-ds--code--row="" class="">} </span><span data-testid="renderer-code-block-line-17" data-ds--code--row="" class=""></span>`

---

### 5.2 필터/통계 정보

`GET /api/reports/filters?category=all`

`<span data-testid="renderer-code-block-line-1" data-ds--code--row="" class=""><span class="">{ </span></span><span data-testid="renderer-code-block-line-2" data-ds--code--row="" class="">  "stats": { </span><span data-testid="renderer-code-block-line-3" data-ds--code--row="" class="">    "total_reports": 42, </span><span data-testid="renderer-code-block-line-4" data-ds--code--row="" class="">    "total_orgs": 8, </span><span data-testid="renderer-code-block-line-5" data-ds--code--row="" class="">    "this_month": 5 </span><span data-testid="renderer-code-block-line-6" data-ds--code--row="" class="">  }, </span><span data-testid="renderer-code-block-line-7" data-ds--code--row="" class="">  "category_counts": { </span><span data-testid="renderer-code-block-line-8" data-ds--code--row="" class="">    "all": 42, </span><span data-testid="renderer-code-block-line-9" data-ds--code--row="" class="">    "global_research": 14, </span><span data-testid="renderer-code-block-line-10" data-ds--code--row="" class="">    "government": 18, </span><span data-testid="renderer-code-block-line-11" data-ds--code--row="" class="">    "company": 10 </span><span data-testid="renderer-code-block-line-12" data-ds--code--row="" class="">  }, </span><span data-testid="renderer-code-block-line-13" data-ds--code--row="" class="">  "sources": [ </span><span data-testid="renderer-code-block-line-14" data-ds--code--row="" class="">    { "id": "uuid", "name": "OECD", "count": 6 } </span><span data-testid="renderer-code-block-line-15" data-ds--code--row="" class="">  ], </span><span data-testid="renderer-code-block-line-16" data-ds--code--row="" class="">  "tags": [ </span><span data-testid="renderer-code-block-line-17" data-ds--code--row="" class="">    { "id": "uuid", "name": "Trade", "count": 12 } </span><span data-testid="renderer-code-block-line-18" data-ds--code--row="" class="">  ] </span><span data-testid="renderer-code-block-line-19" data-ds--code--row="" class="">} </span><span data-testid="renderer-code-block-line-20" data-ds--code--row="" class=""></span>`

---

### 5.3 리포트 디테일

`GET /api/reports/:id`

`<span data-testid="renderer-code-block-line-1" data-ds--code--row="" class=""><span class="">{ </span></span><span data-testid="renderer-code-block-line-2" data-ds--code--row="" class="">  "id": "uuid", </span><span data-testid="renderer-code-block-line-3" data-ds--code--row="" class="">  "title": "string", </span><span data-testid="renderer-code-block-line-4" data-ds--code--row="" class="">  "category_key": "government", </span><span data-testid="renderer-code-block-line-5" data-ds--code--row="" class="">  "published_at": "2025-12-29", </span><span data-testid="renderer-code-block-line-6" data-ds--code--row="" class="">  "source": { "name": "MOEF" }, </span><span data-testid="renderer-code-block-line-7" data-ds--code--row="" class="">  "tags": ["Trade", "Policy"], </span><span data-testid="renderer-code-block-line-8" data-ds--code--row="" class="">  "summary": "string", </span><span data-testid="renderer-code-block-line-9" data-ds--code--row="" class="">  "key_insights": ["...", "..."], </span><span data-testid="renderer-code-block-line-10" data-ds--code--row="" class="">  "file": { </span><span data-testid="renderer-code-block-line-11" data-ds--code--row="" class="">    "file_name": "report.pdf", </span><span data-testid="renderer-code-block-line-12" data-ds--code--row="" class="">    "download_url": "/api/reports/:id/download" </span><span data-testid="renderer-code-block-line-13" data-ds--code--row="" class="">  }, </span><span data-testid="renderer-code-block-line-14" data-ds--code--row="" class="">  "related": [ </span><span data-testid="renderer-code-block-line-15" data-ds--code--row="" class="">    { </span><span data-testid="renderer-code-block-line-16" data-ds--code--row="" class="">      "id": "uuid", </span><span data-testid="renderer-code-block-line-17" data-ds--code--row="" class="">      "title": "Another Report", </span><span data-testid="renderer-code-block-line-18" data-ds--code--row="" class="">      "published_at": "2025-11-20", </span><span data-testid="renderer-code-block-line-19" data-ds--code--row="" class="">      "source": { "name": "KDI" } </span><span data-testid="renderer-code-block-line-20" data-ds--code--row="" class="">    } </span><span data-testid="renderer-code-block-line-21" data-ds--code--row="" class="">  ] </span><span data-testid="renderer-code-block-line-22" data-ds--code--row="" class="">} </span><span data-testid="renderer-code-block-line-23" data-ds--code--row="" class=""></span>`

---

### 5.4 PDF 다운로드

`GET /api/reports/:id/download`

* DB에서 `file_bytes` 조회
* Response header:
  * `Content-Type: application/pdf`
  * `Content-Disposition: attachment; filename="..."`

---

## 6. Related Reports 선정 로직 (MVP)

**목표:**
리포트 디테일 하단에 “맥락상 유사한 리포트” 최대 6개 표시

### 우선순위 규칙

1. 같은 `category_key`
2. 같은 `source_id`
3. tag 1개 이상 겹침
4. `published_at DESC`
5. 최대 6개
6. 자기 자신 제외

> 조건은 **동시에 만족할 필요 없음**
> 위 순서대로 채워서 6개가 될 때까지 선택

---

## 7. 프론트엔드 연동 규칙

### 7.1 리스트 화면

* 페이지 로드:
  * `/api/reports/filters`
  * `/api/reports`
* 검색/탭/필터/정렬 변경 시 `/api/reports` 재호출
* 카드 클릭 → `report-detail.html?id=<uuid>`

### 7.2 디테일 화면

* URL 파라미터 `id`
* `/api/reports/:id` 호출
* Download 버튼 → `/api/reports/:id/download`
* Related Reports 렌더

---

## 8. 개발 순서 (Cursor 지시용)

### Step 1

* DB 마이그레이션 작성 (bytea 포함)

### Step 2

* `seed-reports.ts` 구현

### Step 3

* 리포트 리스트 API
* 필터 API

### Step 4

* 디테일 API
* 다운로드 API
* Related Reports 로직

### Step 5

* 프론트 JS(`report-insight.js`) API 연결

---

## 최종 한 줄 지시

> **“Auth/운영자 UI 없이, Postgres bytea에 PDF를 저장하고 seed 스크립트로 리포트를 적재한 뒤, 리포트 리스트/디테일/다운로드/연관리포트만 구현한다.”**
>
