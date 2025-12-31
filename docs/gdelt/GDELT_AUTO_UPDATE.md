# GDELT 자동 업데이트 가이드

## 개요

GDELT 데이터는 15분마다 자동으로 다운로드되며, UTC 기준 오늘과 어제 데이터만 유지하고 나머지는 자동으로 삭제됩니다.

## 데이터 저장 위치

### 기본 경로
- **프로젝트 내부**: `{프로젝트_루트}/data/gdelt/`
- **구조**:
  ```
  data/gdelt/
  └── default/
      └── events/
          ├── 20251229/  (오늘)
          │   └── 20251229120000.export.CSV.zip
          └── 20251228/  (어제)
              └── 20251228120000.export.CSV.zip
  ```

### 환경 변수로 경로 변경
`.env` 파일에 `GDELT_BASE_PATH`를 설정하면 다른 경로를 사용할 수 있습니다:

```env
# 예시: D 드라이브 사용
GDELT_BASE_PATH=D:\GDELT DB

# 예시: C 드라이브 사용
GDELT_BASE_PATH=C:\MyData\GDELT

# 예시: 상대 경로 (프로젝트 기준)
GDELT_BASE_PATH=./custom_gdelt_data
```

## 자동 업데이트 동작

1. **서버 시작 시**: 즉시 최신 GDELT 데이터를 다운로드 시도
2. **15분마다**: 자동으로 최신 파일 확인 및 다운로드
3. **데이터 정리**: 매 업데이트마다 UTC 기준 오늘과 어제 데이터만 유지

## 수동 업데이트

API를 통해 수동으로 업데이트할 수 있습니다:

```python
import gdelt_backend

# 데이터 업데이트 (다운로드 + 정리)
result = gdelt_backend.update_gdelt_data()
print(result)
```

## 데이터 정리 규칙

- **유지 기간**: UTC 기준 오늘 + 어제 (총 2일)
- **삭제 대상**: 2일 이전의 모든 날짜 디렉토리
- **예시**:
  - 오늘이 2025-12-29 (UTC)인 경우
  - 유지: `20251229/`, `20251228/`
  - 삭제: `20251227/` 이전의 모든 디렉토리

## 주의사항

1. **디스크 공간**: GDELT 파일은 크므로 (수백 MB ~ 수 GB), 디스크 공간을 확인하세요.
2. **네트워크**: 다운로드 시 인터넷 연결이 필요합니다.
3. **첫 실행**: 서버 시작 시 첫 다운로드가 실패할 수 있습니다 (GDELT 서버 응답 지연 등). 이는 정상이며 다음 주기(15분 후)에 재시도됩니다.

## 문제 해결

### 다운로드 실패
- 인터넷 연결 확인
- GDELT 서버 상태 확인: http://data.gdeltproject.org/gdeltv2/
- 로그 확인: 서버 콘솔에서 에러 메시지 확인

### 디스크 공간 부족
- 오래된 데이터가 자동으로 삭제되지만, 수동으로 정리할 수도 있습니다:
  ```python
  import gdelt_backend
  deleted_count = gdelt_backend.cleanup_old_gdelt_data()
  ```

### 경로 문제
- `.env` 파일의 `GDELT_BASE_PATH`가 올바른지 확인
- 경로에 쓰기 권한이 있는지 확인

