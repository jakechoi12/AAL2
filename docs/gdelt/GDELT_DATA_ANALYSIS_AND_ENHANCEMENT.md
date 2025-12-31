# GDELT 데이터 분석 및 백엔드 고도화 방안

## 1. GDELT에서 추출 가능한 데이터 필드 분석

### 1.1 현재 JSON 파일에 포함된 필드들

`gdelt_raw_data_dump.json` 파일을 분석한 결과, 다음과 같은 데이터 필드들이 확인되었습니다:

#### 기본 이벤트 정보
- **event_date**: 이벤트 발생 날짜 (YYYYMMDD 형식)
- **event_code**: CAMEO 이벤트 코드 (예: "190", "100", "164")
- **category**: 이벤트 카테고리 (예: "Material Conflict", "Verbal Conflict")
- **quad_class**: QuadClass 분류 (1-4)

#### 행위자(Actor) 정보
- **actor1**: 주요 행위자 이름
- **actor1_country**: 행위자1의 국가 코드 (3자리 ISO 코드)
- **actor2**: 대상 행위자 이름
- **actor2_country**: 행위자2의 국가 코드

#### 위치 정보
- **lat/latitude**: 위도
- **lng/longitude**: 경도
- **location**: 위치 이름 (예: "Hyderabad, Andhra Pradesh, India")
- **country_code**: 국가 코드 (2자리 ISO 코드)

#### 분석 지표
- **goldstein_scale/scale**: Goldstein Scale 값 (-10.0 ~ +10.0)
- **avg_tone**: 평균 톤 값 (감정 분석 지표)
- **num_articles**: 관련 기사 수
- **num_mentions**: 언급 횟수
- **num_sources**: 출처 수

#### 출처 정보
- **source_url/url**: 원본 기사 URL
- **name**: 이벤트 이름 (actor1 - actor2 형식)

### 1.2 현재 백엔드에서 추출하지 않는 필드들

현재 `gdelt_backend.py`의 `_parse_csv_content()` 함수는 다음 필드만 추출하고 있습니다:
- actor1, actor2
- goldstein_scale
- lat, lng
- url
- event_date

**누락된 중요한 필드들:**
1. **actor1_country, actor2_country**: 국가 정보 분석에 필수
2. **avg_tone**: 감정 분석 지표
3. **category**: 이벤트 분류
4. **event_code**: CAMEO 이벤트 코드
5. **location**: 위치 이름 (지도 표시에 유용)
6. **country_code**: 국가 코드
7. **num_articles, num_mentions, num_sources**: 중요도 판단 지표
8. **quad_class**: 이벤트 분류

## 2. 백엔드 고도화 방안

### 2.1 데이터 필드 확장

#### 개선 사항
1. **추가 필드 추출**: 위에서 언급한 누락된 필드들을 모두 추출
2. **GDELT CSV 컬럼 매핑**: GDELT 2.0 Events CSV의 모든 컬럼 인덱스 정의

#### 필요한 컬럼 인덱스 (GDELT 2.0 Events CSV 기준)
```python
# 기본 정보
COL_SQLDATE = 1              # SQLDATE (YYYYMMDD)
COL_EVENT_CODE = 27          # EventCode (CAMEO 코드)
COL_QUAD_CLASS = 28          # QuadClass (1-4)
COL_GOLDSTEIN_SCALE = 30     # GoldsteinScale

# 행위자 정보
COL_ACTOR1NAME = 6           # Actor1Name
COL_ACTOR1COUNTRYCODE = 7    # Actor1CountryCode
COL_ACTOR2NAME = 16          # Actor2Name
COL_ACTOR2COUNTRYCODE = 17   # Actor2CountryCode

# 위치 정보
COL_ACTION_GEO_COUNTRYCODE = 51  # ActionGeo_CountryCode
COL_ACTION_GEO_ADM1CODE = 52     # ActionGeo_ADM1Code
COL_ACTION_GEO_LAT = 56          # ActionGeo_Lat
COL_ACTION_GEO_LONG = 57         # ActionGeo_Long
COL_ACTION_GEO_FULLNAME = 58     # ActionGeo_FullName

# 분석 지표
COL_AVG_TONE = 34           # AvgTone
COL_NUM_ARTICLES = 33       # NumArticles
COL_NUM_MENTIONS = 32       # NumMentions
COL_NUM_SOURCES = 31        # NumSources

# 출처
COL_SOURCEURL = 60          # SOURCEURL
```

### 2.2 기능 개선 사항

#### 1. 이벤트 카테고리 매핑
- **event_code**를 기반으로 카테고리 자동 분류
- CAMEO 이벤트 코드를 사람이 읽을 수 있는 카테고리로 변환

#### 2. 필터링 기능 강화
- **국가별 필터링**: country_code, actor1_country, actor2_country 기반
- **카테고리별 필터링**: category 기반
- **중요도 필터링**: num_articles, num_mentions 기반
- **톤 필터링**: avg_tone 기반

#### 3. 데이터 집계 및 통계
- 국가별 이벤트 수 집계
- 카테고리별 분포 통계
- 시간대별 트렌드 분석
- 평균 톤 및 Goldstein Scale 분포

#### 4. 위치 정보 개선
- **location** 필드 추가 (ActionGeo_FullName)
- 국가 코드 정규화 및 검증
- 좌표 유효성 검사 강화

#### 5. 성능 최적화
- 대용량 파일 처리 시 스트리밍 방식 개선
- 메모리 효율적인 파싱
- 병렬 처리 지원 (여러 파일 동시 처리)

#### 6. 에러 처리 개선
- 컬럼 수가 부족한 경우 더 상세한 로깅
- 데이터 타입 변환 실패 시 기본값 처리
- 부분 실패 시에도 가능한 데이터는 반환

### 2.3 API 확장 방안

#### 새로운 엔드포인트 제안
1. **국가별 통계**: `/api/global-alerts/stats/by-country`
2. **카테고리별 통계**: `/api/global-alerts/stats/by-category`
3. **시간대별 트렌드**: `/api/global-alerts/trends`
4. **특정 국가 필터링**: `/api/global-alerts?country=US`
5. **중요도 순 정렬**: `/api/global-alerts?sort_by=importance`

## 3. 구현 우선순위

### Phase 1: 필수 개선 (즉시 구현)
1. ✅ 누락된 필드 추출 추가
   - actor1_country, actor2_country
   - avg_tone
   - category (event_code 기반)
   - event_code
   - location
   - country_code
   - num_articles, num_mentions, num_sources
   - quad_class

2. ✅ 컬럼 인덱스 상수 정의
   - 모든 GDELT CSV 컬럼 인덱스를 상수로 정의

3. ✅ 에러 처리 개선
   - 필드가 없거나 유효하지 않은 경우 기본값 처리

### Phase 2: 기능 확장 (단기)
1. 국가별 필터링 기능
2. 카테고리별 필터링 기능
3. 중요도 기반 정렬
4. 위치 정보 개선 (location 필드 추가)

### Phase 3: 고급 기능 (중기)
1. 통계 및 집계 API
2. 트렌드 분석
3. 성능 최적화
4. 캐싱 메커니즘

## 4. 예상 효과

### 데이터 품질 향상
- 더 풍부한 메타데이터로 분석 정확도 향상
- 국가, 카테고리 정보로 필터링 및 그룹화 가능

### 사용자 경험 개선
- 위치 이름으로 지도 표시 개선
- 중요도 지표로 관련성 높은 이벤트 우선 표시
- 감정 분석 지표로 이벤트 톤 파악 가능

### 분석 기능 강화
- 국가별, 카테고리별 통계 분석 가능
- 시간대별 트렌드 분석 가능
- 다차원 필터링 및 검색 가능

## 5. 참고 자료

- GDELT 2.0 Events Data Format Codebook: https://blog.gdeltproject.org/gdelt-2-0-data-format-codebook/
- CAMEO Event Codes: https://parusanalytics.com/eventdata/cameo.dir/CAMEO.html
- QuadClass 설명: QuadClass는 이벤트의 네 가지 기본 분류를 나타냄 (1: Verbal Cooperation, 2: Material Cooperation, 3: Verbal Conflict, 4: Material Conflict)

