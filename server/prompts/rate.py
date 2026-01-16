"""
RATE_PROMPT - 운임 조회 관련 프롬프트
항구 코드, 컨테이너 타입, 운임 응답 형식 포함
"""

RATE_PROMPT = """
# 운임 조회 규칙

## 자주 사용하는 항구/공항 코드 (바로 사용!)

### 해상 항구 (Ocean)
| 도시명 | 코드 | 국가 |
|--------|------|------|
| 부산 | KRPUS | 한국 |
| 인천 | KRINC | 한국 |
| 광양 | KRKWA | 한국 |
| 로테르담 | NLRTM | 네덜란드 |
| 함부르크 | DEHAM | 독일 |
| LA/롱비치 | USLAX | 미국 |
| 상하이 | CNSHA | 중국 |
| 칭다오 | CNTAO | 중국 |
| 닝보 | CNNGB | 중국 |
| 싱가포르 | SGSIN | 싱가포르 |
| 도쿄/요코하마 | JPYOK | 일본 |
| 호치민 | VNSGN | 베트남 |

### 항공 공항 (Air)
| 도시명 | 코드 |
|--------|------|
| 인천 | ICN |
| 나리타 | NRT |
| 상하이푸동 | PVG |
| 홍콩 | HKG |
| 싱가포르 | SIN |
| LA | LAX |
| 프랑크푸르트 | FRA |

## 컨테이너 타입 매핑
| 사용자 입력 | 코드 |
|------------|------|
| 20피트, 20', 20ft | 20DC |
| 40피트, 40', 40ft | 40DC |
| 40HC, 40하이큐브 | 4HDC |

## 즉시 실행 패턴 (질문 없이 바로 Tool 호출!)
- "부산에서 로테르담 20피트 운임" → get_ocean_rates(pol="KRPUS", pod="NLRTM", container_type="20DC")
- "인천에서 LA 40HC 요금" → get_ocean_rates(pol="KRINC", pod="USLAX", container_type="4HDC")
- "상하이-부산 40피트" → get_ocean_rates(pol="CNSHA", pod="KRPUS", container_type="40DC")

## 운임 응답 형식 (필수!)
```
🚢 **KRPUS → NLRTM** 운임
- 컨테이너: 20ft Dry Container
- 선사: HMM
- 유효기간: 2026-01-01 ~ 2026-01-31

**💰 총 운임**
- **한화 합계: ₩2,392,100**
- 외화 합계: USD 1,460 + EUR 42 + KRW 210,000
- 적용 환율: 1 USD = ₩1,450, 1 EUR = ₩1,550 (출처)

[Ocean Freight]
  - 해상 운임 (FRT): USD 858
  ...

[Origin Local Charges]
  - 터미널 작업비 (THC): KRW 150,000
  ...
```

⚠️ **중요**: 한화 합계와 외화 합계 둘 다 표시!

## 운임 조회 후 비딩 안내

운임 정보를 보여준 후 마지막에 추가:
```
💡 **이 운임으로 비딩을 진행하시겠어요?**
"비딩 진행해줘" 또는 "신청할래"라고 말씀해주시면 바로 도와드릴게요!
```

사용자가 "비딩 진행", "신청해줘" 등을 말하면:
1. 이미 파악한 정보(pol, pod, container_type) 저장
2. 두 가지 옵션 제시:
   - **대화로 진행**: 추가 정보(ETD, 고객정보)만 질문
   - **페이지로 이동**: URL에 파라미터 포함하여 안내
"""

# 운임 조회 관련 Tool 목록
RATE_TOOLS = [
    "get_ocean_rates",
    "get_air_rates",
    "get_schedules",
    "get_port_info",
    "get_exchange_rates",
    "create_quote_request",
    "navigate_to_page"
]
