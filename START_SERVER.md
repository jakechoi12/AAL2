# AAL 서버 시작 가이드

## 통합 실행 (권장)

`server/main.py`를 실행하면 **두 서버가 자동으로 시작**됩니다:

| 서버 | 포트 | 용도 |
|------|------|------|
| Main Server (Flask) | 5000 | Market Data, News Intel, Auth, 프론트엔드 |
| Quote Backend (FastAPI) | 8001 | Quotation, POL/POD 자동완성, Bidding |

---

## 방법 1: 배치 파일 사용 (권장)

`server/start_server.bat` 파일을 더블클릭하여 실행하세요.

## 방법 2: 명령 프롬프트에서 실행

```bash
cd server
python main.py
```

## 방법 3: PowerShell에서 실행

```powershell
cd server
python main.py
```

---

## 서버 확인

서버가 시작되면 다음과 같이 표시됩니다:

```
============================================================
  AAL - All About Logistics Server
============================================================

  [Main Server]     http://localhost:5000  (Flask)
  [Quote Backend]   http://localhost:8001  (FastAPI)

  BASE_DIR: D:\Planning_data\AAL\AAL
  GDELT auto-update: Every 15 minutes
  News Intelligence: Every 1 hour

============================================================
```

---

## 브라우저에서 접속

1. 메인 페이지: `http://localhost:5000`
2. Quotation API 문서: `http://localhost:8001/docs`

---

## 자동 기능

서버 시작 시 자동으로 수행되는 작업:

1. **Quote Backend 자동 시작** - FastAPI 서버 (포트 8001)
2. **Seed Data 자동 초기화** - Port, Container Type 등 기초 데이터
3. **GDELT 데이터 업데이트** - 15분마다 자동 갱신
4. **뉴스 인텔리전스 수집** - 1시간마다 자동 수집

---

## 문제 해결

### 포트 5000 또는 8001이 이미 사용 중인 경우

기존 Python 프로세스를 종료하세요:

```bash
# Windows
taskkill /F /IM python.exe

# 또는 특정 포트 확인 후 종료
netstat -ano | findstr :5000
netstat -ano | findstr :8001
taskkill /F /PID [PID번호]
```

### POL/POD 자동완성이 안 되는 경우

Quote Backend가 정상 실행 중인지 확인:

```
http://localhost:8001/api/ports?search=busan
```

Seed 데이터가 없으면 수동으로 실행:

```bash
cd quote_backend
python seed_data.py
```

---

## 개별 서버 실행 (고급)

필요한 경우 서버를 개별적으로 실행할 수 있습니다:

```bash
# 터미널 1: Main Server
cd server
python main.py

# 터미널 2: Quote Backend (main.py가 자동 실행하지만, 수동 실행 시)
cd quote_backend
python main.py
```