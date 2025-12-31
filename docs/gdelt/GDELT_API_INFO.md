# GDELT Global Alerts API

## 개요
GDELT (Global Database of Events, Language, and Tone) 데이터를 기반으로 전 세계 긴급 이벤트를 제공하는 API입니다.

## 엔드포인트

### GET /api/global-alerts

긴급 알림 데이터를 가져옵니다.

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `threshold` | float | 아니오 | -5.0 | GoldsteinScale 임계값 (이하 값만 반환) |
| `max_alerts` | int | 아니오 | 1000 | 최대 반환할 알림 수 |
| `start_date` | string | 아니오 | - | 시작 날짜 (YYYY-MM-DD) |
| `end_date` | string | 아니오 | - | 종료 날짜 (YYYY-MM-DD) |

#### GoldsteinScale 설명
- 범위: -10.0 ~ +10.0
- 음수: 부정적 이벤트 (갈등, 폭력, 위협 등)
- 양수: 긍정적 이벤트 (협력, 지원, 외교 등)
- -10.0: 가장 심각한 부정적 이벤트 (전쟁, 대량 살상 등)
- -5.0: 중간 수준의 부정적 이벤트 (시위, 소규모 충돌 등)

#### 예시 요청

```bash
# 최신 긴급 알림 조회 (threshold -5.0 이하)
curl "http://localhost:5000/api/global-alerts?threshold=-5.0&max_alerts=1000"

# 특정 날짜 범위의 알림 조회
curl "http://localhost:5000/api/global-alerts?start_date=2025-12-20&end_date=2025-12-29&threshold=-7.0&max_alerts=500"

# 매우 심각한 이벤트만 조회
curl "http://localhost:5000/api/global-alerts?threshold=-8.0&max_alerts=100"
```

#### 응답 형식

```json
{
  "alerts": [
    {
      "name": "Actor1Name - Actor2Name",
      "actor1": "Actor1Name",
      "actor2": "Actor2Name",
      "scale": -6.5,
      "goldstein_scale": -6.5,
      "lat": 37.5665,
      "lng": 126.9780,
      "latitude": 37.5665,
      "longitude": 126.9780,
      "url": "https://example.com/news-article",
      "source_url": "https://example.com/news-article",
      "event_date": "20251229"
    }
  ],
  "count": 150,
  "last_updated": "2025-12-29T15:30:45.123456",
  "file_path": "D:\\GDELT DB\\default\\events\\20251229\\20251229123000.export.CSV",
  "threshold": -5.0
}
```

#### 오류 응답

```json
{
  "error": "No GDELT data file found",
  "alerts": [],
  "count": 0,
  "last_updated": null
}
```

## 데이터 필드 설명

### Alert 객체

| 필드 | 타입 | 설명 |
|------|------|------|
| `name` | string | 이벤트 이름 (행위자1 - 행위자2) |
| `actor1` | string | 주요 행위자 (국가, 조직, 인물 등) |
| `actor2` | string | 대상 행위자 |
| `scale` | float | GoldsteinScale 값 (프론트엔드용) |
| `goldstein_scale` | float | GoldsteinScale 값 (하위 호환) |
| `lat` | float | 위도 (프론트엔드용) |
| `lng` | float | 경도 (프론트엔드용) |
| `latitude` | float | 위도 (하위 호환) |
| `longitude` | float | 경도 (하위 호환) |
| `url` | string | 출처 URL (프론트엔드용) |
| `source_url` | string | 출처 URL (하위 호환) |
| `event_date` | string | 이벤트 날짜 (YYYYMMDD) |

## 데이터 경로 설정

### 환경 변수

```bash
# .env 파일에 추가
GDELT_BASE_PATH=D:\GDELT DB
```

### 디렉토리 구조

```
{GDELT_BASE_PATH}/
└── default/
    └── events/
        ├── 20251227/
        │   ├── 20251227120000.export.CSV
        │   └── 20251227123000.export.CSV.zip
        ├── 20251228/
        └── 20251229/
```

## 프론트엔드 통합

프론트엔드에서 다음과 같이 사용:

```javascript
async function fetchGlobalAlerts() {
    const response = await fetch('/api/global-alerts?threshold=-5.0&max_alerts=1000');
    const data = await response.json();
    
    if (data.error) {
        console.error('Error:', data.error);
        return;
    }
    
    // 지도에 마커 표시
    data.alerts.forEach(alert => {
        if (alert.lat && alert.lng) {
            // Google Maps 마커 생성
            const marker = new google.maps.Marker({
                position: { lat: alert.lat, lng: alert.lng },
                title: alert.name,
                // ...
            });
        }
    });
}
```

## 주의사항

1. **GDELT 데이터 필수**: API가 작동하려면 GDELT 데이터 파일이 지정된 경로에 있어야 합니다.
2. **파일 크기**: GDELT CSV 파일은 매우 클 수 있으므로 `max_alerts` 파라미터로 제한하세요.
3. **실시간 데이터**: GDELT는 15분마다 업데이트되므로, 최신 데이터를 위해 주기적으로 다운로드가 필요합니다.
4. **좌표 검증**: 모든 이벤트가 유효한 좌표를 가지는 것은 아닙니다. 프론트엔드에서 검증이 필요합니다.

## 문제 해결

### "No GDELT data file found" 오류
- GDELT_BASE_PATH 환경 변수가 올바른지 확인
- 디렉토리 구조가 올바른지 확인: `{BASE_PATH}/default/events/{YYYYMMDD}/`
- CSV 파일이 실제로 존재하는지 확인

### "Invalid coordinates" 경고
- GDELT 데이터에 일부 이벤트는 위치 정보가 없거나 잘못되어 있을 수 있음
- 프론트엔드에서 자동으로 필터링됨

### 성능 문제
- `max_alerts` 값을 줄이세요 (예: 100-500)
- `threshold` 값을 낮춰서 더 심각한 이벤트만 필터링하세요 (예: -7.0, -8.0)

