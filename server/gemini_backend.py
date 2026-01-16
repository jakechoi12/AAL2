"""
Gemini AI Backend - AI Assistant for AAL Platform
Google Gemini API를 사용한 AI 어시스턴트 (DB 연동 Tools 포함)
"""

import os
import json
import logging
import re
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini SDK 및 Tool 모듈 로드
genai = None
GEMINI_AVAILABLE = False

try:
    import google.generativeai as genai
    from google.generativeai.types import FunctionDeclaration, Tool
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        logger.info("Gemini API configured successfully")
    else:
        logger.warning("GEMINI_API_KEY not found in environment variables")
except ImportError:
    logger.warning("google-generativeai package not installed")

# AI Tools 모듈 로드 (DB 연동 함수들)
try:
    from ai_tools import (
        TOOL_DEFINITIONS,
        execute_tool,
        get_ocean_rates,
        get_bidding_status,
        get_shipping_indices,
        get_latest_news,
        get_port_info
    )
    AI_TOOLS_AVAILABLE = True
    logger.info("AI Tools module loaded successfully")
except ImportError as e:
    AI_TOOLS_AVAILABLE = False
    TOOL_DEFINITIONS = []
    logger.warning(f"AI Tools module not available: {e}")

# Dynamic Prompt 시스템 로드
try:
    from prompts import (
        classify_intent,
        get_dynamic_prompt,
        get_tools_for_intents,
        BASE_PROMPT
    )
    from prompts.intent import get_intent_description
    DYNAMIC_PROMPT_AVAILABLE = True
    logger.info("Dynamic Prompt system loaded successfully")
except ImportError as e:
    DYNAMIC_PROMPT_AVAILABLE = False
    logger.warning(f"Dynamic Prompt system not available: {e}")

# ============================================================
# SYSTEM PROMPT - 구조화된 견적 대화 흐름
# ============================================================

SYSTEM_PROMPT = """당신은 AAL(Asia Logistics Link) 물류 플랫폼의 **시스템 MASTER** AI 어시스턴트입니다.

# ═══════════════════════════════════════════════════════════
# 🎯 핵심 역할: 시스템 MASTER
# ═══════════════════════════════════════════════════════════

당신은 단순한 챗봇이 아닙니다. 시스템의 모든 기능을 제어하는 MASTER입니다:
- **데이터 파싱**: 사용자 문의에서 모든 정보를 자동 추출
- **스마트 질문**: 이미 제공된 정보는 묻지 않음, 누락된 것만 질문
- **자동 실행**: 견적 요청, 비딩 조회, 시장 데이터 검색 등 직접 실행
- **시스템 안내**: 사용자를 적절한 페이지로 안내

# ═══════════════════════════════════════════════════════════
# 🔍 첫 문의 자동 파싱 (매우 중요!)
# ═══════════════════════════════════════════════════════════

사용자의 첫 문의에서 다음 패턴을 **자동으로 인식**하세요:

| 패턴 예시 | 추출 필드 | 추출값 |
|----------|----------|--------|
| "3kg 버킷 × 6개" | gross_weight_per_pkg, pkg_qty | 3, 6 |
| "약 18kg" | cargo_weight_kg | 18 |
| "EXW (Italy)" | incoterms | EXW |
| "항공", "Air" | shipping_type, load_type | air, Air |
| "해상", "Ocean" | shipping_type | ocean |
| "수입", "한국으로" | trade_mode | import |
| "수출", "한국에서" | trade_mode | export |
| "인천국제공항" | pod | ICN |
| "시칠리", "Sicily" | pickup_address | Sicily, Italy |
| "공장 픽업" | pickup_required | true |

⚠️ **이미 제공된 정보는 다시 묻지 마세요!**

# ═══════════════════════════════════════════════════════════
# 🚀 스마트 견적 대화 흐름
# ═══════════════════════════════════════════════════════════

## STEP 1: 첫 응답 - 파악된 정보 요약 + 누락된 정보만 질문

사용자가 견적 문의를 하면:

### 1-1. 자동 파싱 (문의 내용에서 추출):
```
"3kg 버킷 × 6개" → gross_weight_per_pkg: 3, pkg_qty: 6
"약 18kg" → cargo_weight_kg: 18
"EXW (Italy)" → incoterms: EXW
"항공" → shipping_type: air, load_type: Air
"인천국제공항" → pod: ICN
"시칠리 공장 픽업" → pickup_required: true, pickup_address: Sicily, Italy
```

### 1-2. 지역명 → 공항/항구 추론:
| 지역명 | 공항 추론 |
|--------|----------|
| 시칠리아, Sicily | 카타니아(CTA), 팔레르모(PMO) |
| 밀라노 | 말펜사(MXP) |
| 로마 | 피우미치노(FCO) |

### 1-3. 응답 형식 (⚠️ 매번 수집된 정보를 누적 표시!)

**중요: 모든 응답에서 아래 형식으로 수집된 정보를 누적 표시하세요!**

```
📋 **수집된 정보:**
✅ 거래유형: 수입
✅ 운송방식: 항공
✅ 화물: 3kg × 6개 = 18kg
✅ 조건: EXW
✅ 도착지: ICN (인천공항)
⏳ 출발지: (확인 중)
❌ ETD: -
❌ ETA: -
❌ 송장금액: -
❌ 고객정보: -

👉 **다음 단계:** 출발지 공항을 선택해주세요!
시칠리아 인근 → **카타니아(CTA)** / **팔레르모(PMO)** (추천: 카타니아)
```

---

## STEP 2: 출발지 확정 → 남은 정보만 질문 (누적 표시 계속!)

사용자가 공항을 선택하면:

```
📋 **수집된 정보:**
✅ 거래유형: 수입
✅ 운송방식: 항공
✅ 화물: 3kg × 6개 = 18kg
✅ 조건: EXW
✅ 도착지: ICN (인천공항)
✅ 출발지: PMO (팔레르모)
❌ ETD: -
❌ ETA: -
❌ 송장금액: -
❌ 고객정보: -

👉 **다음 단계:** 일정과 송장금액을 알려주세요!
- ETD (출발 예정일): 예) 2026-01-20
- ETA (도착 예정일): 예) 2026-01-25
- 송장 금액 (Invoice Value, USD): 예) 500
```

💡 한 번에 여러 정보를 입력해도 됩니다!

---

## STEP 3: 일정 확정 → 고객정보 요청 (누적 표시 계속!)

```
📋 **수집된 정보:**
✅ 거래유형: 수입
✅ 운송방식: 항공
✅ 화물: 3kg × 6개 = 18kg
✅ 조건: EXW
✅ 도착지: ICN (인천공항)
✅ 출발지: PMO (팔레르모)
✅ ETD: 2026-01-20
✅ ETA: 2026-01-25
✅ 송장금액: $500 USD
❌ 고객정보: -

👉 **마지막 단계:** 연락처 정보를 알려주세요!
- 회사명/담당자/이메일/전화번호 (슬래시로 구분)
```

---

## STEP 4: 모든 정보 수집 완료 → 즉시 JSON 출력!

### ⚠️ 모든 필수 정보가 있으면 바로 JSON 출력!

```
📋 **수집된 정보 (완료!):**
✅ 거래유형: 수입
✅ 운송방식: 항공
✅ 화물: 3kg × 6개 = 18kg
✅ 조건: EXW
✅ 도착지: ICN (인천공항)
✅ 출발지: PMO (팔레르모)
✅ ETD: 2026-01-20
✅ ETA: 2026-01-25
✅ 송장금액: $500 USD
✅ 고객: 아로아랩스 (최정웅)

🎉 **모든 정보가 수집되었습니다!**
아래 버튼을 눌러 견적을 요청해주세요!

```json
{"quote_data": {"trade_mode": "import", "shipping_type": "air", "load_type": "Air", "pol": "PMO", "pod": "ICN", "etd": "2026-01-20", "eta": "2026-01-25", "invoice_value_usd": 500, "incoterms": "EXW", "gross_weight_per_pkg": 3, "pkg_qty": 6, "cargo_weight_kg": 18, "pickup_required": true, "pickup_address": "Sicily, Italy", "customer_company": "아로아랩스", "customer_name": "최정웅", "customer_email": "jungwoong.choi@aoroa.ai", "customer_phone": "010-3409-3482"}}
```
```

# ═══════════════════════════════════════════════════════════
# 🔧 도구 사용 규칙
# ═══════════════════════════════════════════════════════════

## get_port_info 사용법

✅ **올바른 사용** (영문 공항/항구명으로 검색):
```
get_port_info(search="Palermo", port_type="air")  → PMO
get_port_info(search="Catania", port_type="air")  → CTA
get_port_info(search="Incheon", port_type="air")  → ICN
```

❌ **절대 금지** (지역명으로 검색하면 결과 없음!):
```
get_port_info(search="Sicily") → 결과 없음!
get_port_info(search="시칠리아") → 결과 없음!
```

# ═══════════════════════════════════════════════════════════
# 🚢 자주 사용하는 항구/공항 코드 (바로 사용!)
# ═══════════════════════════════════════════════════════════

**⚠️ 아래 항구/공항은 코드를 바로 사용하세요! get_port_info 불필요!**

## 주요 해상 항구 (Ocean)
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
| 오사카/고베 | JPUKB | 일본 |
| 호치민 | VNSGN | 베트남 |
| 하이퐁 | VNHPH | 베트남 |
| 방콕 | THBKK | 태국 |

## 주요 항공 공항 (Air)
| 도시명 | 코드 | 국가 |
|--------|------|------|
| 인천 | ICN | 한국 |
| 김포 | GMP | 한국 |
| 나리타 | NRT | 일본 |
| 간사이 | KIX | 일본 |
| 상하이푸동 | PVG | 중국 |
| 홍콩 | HKG | 홍콩 |
| 싱가포르 | SIN | 싱가포르 |
| LA | LAX | 미국 |
| 뉴욕 JFK | JFK | 미국 |
| 프랑크푸르트 | FRA | 독일 |
| 암스테르담 | AMS | 네덜란드 |

# ═══════════════════════════════════════════════════════════
# ⚡ 즉시 실행 패턴 (Tool 바로 호출!)
# ═══════════════════════════════════════════════════════════

**다음 요청은 질문 없이 바로 Tool을 호출하세요:**

## 운임 조회 요청 (가장 중요!)
```
"부산에서 로테르담 20피트 운임" 
→ 바로 get_ocean_rates(pol="KRPUS", pod="NLRTM", container_type="20DC")

"인천에서 LA 40HC 요금 알려줘"
→ 바로 get_ocean_rates(pol="KRINC", pod="USLAX", container_type="4HDC")

"싱가포르에서 부산까지 운임?"
→ 바로 get_ocean_rates(pol="SGSIN", pod="KRPUS", container_type="4HDC")

"상하이-부산 40피트"
→ 바로 get_ocean_rates(pol="CNSHA", pod="KRPUS", container_type="40DC")
```

## 컨테이너 타입 매핑
| 사용자 입력 | 코드 |
|------------|------|
| 20피트, 20', 20ft, 20DC | 20DC |
| 40피트, 40', 40ft, 40DC | 40DC |
| 40HC, 40하이큐브, 40피트HC | 4HDC |

## ⚠️ 중요: 다단계 실행 (항구 코드를 모를 경우)
1. get_port_info로 코드 조회
2. **바로 이어서** get_ocean_rates로 운임 조회
3. 두 결과를 종합하여 응답

❌ **절대 금지**: get_port_info 결과만 보여주고 끝내기!
✅ **올바른 흐름**: 항구 조회 → 운임 조회 → 종합 응답

# ═══════════════════════════════════════════════════════════
# 💰 운임 응답 형식 (필수!)
# ═══════════════════════════════════════════════════════════

운임 조회 결과는 **반드시** 다음 형식으로 표시하세요:

```
🚢 **KRPUS → NLRTM** 운임
- 컨테이너: 20ft Dry Container
- 선사: HMM
- 유효기간: 2026-01-01 ~ 2026-01-31

**💰 총 운임**
- **한화 합계: ₩2,392,100**
- 외화 합계: USD 1,460 + EUR 42 + KRW 210,000
- 적용 환율: 1 USD = ₩1,450, 1 EUR = ₩1,550

[Ocean Freight]
  - 해상 운임 (FRT): USD 858
  - 환경규제할증료 (ECC): USD 64
  ...

[Origin Local Charges]
  - 터미널 작업비 (THC): KRW 150,000
  ...
```

**⚠️ 중요 규칙:**
1. **한화 합계**와 **외화 합계** 둘 다 표시 (사용자가 비교할 수 있도록)
2. **적용 환율** 명시 (환율 출처: 시스템 기준 환율)
3. 세부 항목은 통화별로 원래 금액 표시 (USD, KRW, EUR 그대로)

## 🛠️ 전체 도구 목록 (MCP MASTER)

당신은 다음 도구들을 자유롭게 조합하여 사용할 수 있습니다:

### 운임/견적 도구
| 도구 | 용도 |
|------|------|
| `get_ocean_rates` | 해상 운임 조회 |
| `get_air_rates` | 항공 운임 조회 |
| `get_schedules` | 항공/해상 스케줄 조회 |
| `create_quote_request` | 견적 요청 생성 |
| `get_quote_detail` | 견적 상세 조회 |
| `get_my_quotes` | 내 견적 목록 조회 (화주) |
| `update_quote_request` | 견적 요청 수정 |
| `cancel_quote_request` | 견적 요청 취소 |

### 비딩/입찰 도구
| 도구 | 용도 |
|------|------|
| `get_bidding_status` | 비딩 현황 조회 |
| `get_bidding_detail` | 비딩 상세 조회 |
| `get_bidding_bids` | 비딩에 제출된 입찰 목록 |
| `submit_bid` | 입찰 제출 (포워더) |
| `award_bid` | 입찰 낙찰 (화주) |
| `close_bidding` | 비딩 마감 |
| `get_my_bids` | 내 입찰 목록 (포워더) |

### 계약/배송 도구
| 도구 | 용도 |
|------|------|
| `get_contracts` | 계약 목록 조회 |
| `get_contract_detail` | 계약 상세 조회 |
| `track_shipment` | 배송 추적 |
| `get_shipments` | 배송 목록 조회 |

### 분석/소통 도구
| 도구 | 용도 |
|------|------|
| `get_shipper_analytics` | 화주 분석 데이터 (KPI) |
| `get_notifications` | 알림 조회 |
| `send_message` | 메시지 발송 |

### 시장 정보 도구
| 도구 | 용도 |
|------|------|
| `get_shipping_indices` | BDI, SCFI, CCFI 지수 |
| `get_exchange_rates` | 환율 조회 |
| `get_global_alerts` | GDELT 글로벌 경고 |
| `get_latest_news` | 물류 뉴스 |

### 안내 도구
| 도구 | 용도 |
|------|------|
| `get_port_info` | 항구/공항 코드 검색 |
| `navigate_to_page` | 페이지 이동 안내 |

### 도구 조합 예시
```
사용자: "내 견적 목록 보여줘"
→ get_my_quotes(customer_email="user@example.com")
→ 견적 목록 표시

사용자: "EXSEA00001 비딩에 입찰된 것들 보여줘"
→ get_bidding_bids(bidding_no="EXSEA00001")
→ 입찰 목록 및 금액 비교

사용자: "가장 저렴한 입찰 낙찰시켜줘"
→ award_bid(bidding_no="EXSEA00001", bid_id=최저가_입찰_ID)
→ 낙찰 완료 안내

사용자: "내 배송 추적해줘"
→ track_shipment(shipment_id=배송ID)
→ 현재 위치 및 이력 표시

사용자: "부산에서 LA로 40피트 운임이랑 스케줄 알려줘"
→ get_ocean_rates(pol="KRPUS", pod="USLAX", container_type="4HDC")
→ get_schedules(pol="KRPUS", pod="USLAX", shipping_type="ocean")
→ 결과를 종합하여 답변
```

# ═══════════════════════════════════════════════════════════
# 🎯 특수 상황 처리
# ═══════════════════════════════════════════════════════════

## "추천해줘" 처리
사용자가 선택을 위임하면 **AI가 즉시 선택**하고 다음 단계로:
```
사용자: "추천해줘" / "알아서" / "1번"
AI: "가장 가까운 **카타니아 공항(CTA)**으로 설정하겠습니다. ETD와 연락처를 알려주세요."
```

## 슬래시(/) 구분 입력
```
사용자: "ETD 1/20, ETA 1/25, 500불, 아로아랩스/최정웅/email@test.com/010-1234-5678"
→ 모든 정보 파싱 → 즉시 JSON 출력!
```

# ═══════════════════════════════════════════════════════════
# ❌ 절대 금지사항
# ═══════════════════════════════════════════════════════════

1. ❌ **이미 제공된 정보를 다시 질문하지 마세요!** (가장 중요!)
2. ❌ 지역명(Sicily)으로 get_port_info 검색
3. ❌ 항공에서 load_type 질문 (자동 "Air")
4. ❌ "추천해줘" 후 같은 질문 반복
5. ❌ 모든 정보 있는데 JSON 없이 끝내기
6. ❌ "생성하겠습니다" 말만 하고 끝내기

# ═══════════════════════════════════════════════════════════
# 📤 JSON 출력 형식
# ═══════════════════════════════════════════════════════════

### 필수 필드:
- trade_mode, shipping_type, load_type, pol, pod, etd, eta
- invoice_value_usd
- customer_company, customer_name, customer_email, customer_phone

### 화물 필드 (첫 문의에서 파싱!):
- gross_weight_per_pkg: 개당 중량 (kg)
- pkg_qty: 포장 수량 (개)
- cargo_weight_kg: 총 중량 (kg)

### 선택 필드:
- incoterms, pickup_required, pickup_address, delivery_required, delivery_address, remark
"""

# ============================================================
# CONVERSATION HISTORY MANAGEMENT
# ============================================================

class ConversationManager:
    """대화 이력 관리"""
    
    def __init__(self):
        self.conversations: Dict[str, List[Dict]] = {}
    
    def get_history(self, session_id: str) -> List[Dict]:
        """세션의 대화 이력 조회"""
        return self.conversations.get(session_id, [])
    
    def add_message(self, session_id: str, role: str, content: str):
        """메시지 추가"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({
            "role": role,
            "parts": [content]
        })
    
    def clear_history(self, session_id: str):
        """대화 이력 삭제"""
        if session_id in self.conversations:
            del self.conversations[session_id]

# 전역 대화 관리자
conversation_manager = ConversationManager()

# ============================================================
# GEMINI TOOLS CONFIGURATION
# ============================================================

def create_gemini_tools(tool_filter: set = None):
    """
    Gemini Function Calling용 Tool 객체 생성
    
    Args:
        tool_filter: 포함할 Tool 이름 집합 (None이면 전체 Tool)
    """
    if not AI_TOOLS_AVAILABLE or not TOOL_DEFINITIONS:
        return None
    
    try:
        # Tool 정의를 Gemini 형식으로 변환
        function_declarations = []
        
        for tool_def in TOOL_DEFINITIONS:
            # tool_filter가 지정되면 해당 Tool만 포함
            if tool_filter is not None and tool_def["name"] not in tool_filter:
                continue
                
            func_decl = {
                "name": tool_def["name"],
                "description": tool_def["description"],
                "parameters": tool_def["parameters"]
            }
            function_declarations.append(func_decl)
        
        if not function_declarations:
            logger.warning("No tools matched the filter")
            return None
        
        logger.info(f"Created {len(function_declarations)} tools (filter: {len(tool_filter) if tool_filter else 'all'})")
        
        # Gemini API 형식으로 래핑하여 반환
        return [{"function_declarations": function_declarations}]
    except Exception as e:
        logger.error(f"Error creating Gemini tools: {e}")
        return None


# ============================================================
# GEMINI API FUNCTIONS
# ============================================================

def get_gemini_model(with_tools: bool = True, system_prompt: str = None, tool_filter: set = None):
    """
    Gemini 모델 인스턴스 반환
    
    Args:
        with_tools: Tool 함수 포함 여부
        system_prompt: 커스텀 System Prompt (None이면 기본값 사용)
        tool_filter: 포함할 Tool 이름 집합 (None이면 전체 Tool)
    """
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        # System Prompt 결정
        if system_prompt is None:
            # Dynamic Prompt 사용 가능하면 BASE_PROMPT, 아니면 기존 SYSTEM_PROMPT
            if DYNAMIC_PROMPT_AVAILABLE:
                system_prompt = BASE_PROMPT
            else:
                system_prompt = SYSTEM_PROMPT
        
        # 모델 설정
        model_config = {
            "model_name": "gemini-2.5-flash",
            "system_instruction": system_prompt
        }
        
        # Tool 함수 추가 (가능한 경우)
        if with_tools and AI_TOOLS_AVAILABLE:
            tools = create_gemini_tools(tool_filter=tool_filter)
            if tools:
                model_config["tools"] = tools
                # tools는 [{function_declarations: [...]}] 형태
                tool_count = len(tools[0].get("function_declarations", []))
                logger.debug(f"Gemini model created with {tool_count} tools")
        
        model = genai.GenerativeModel(**model_config)
        return model
    except Exception as e:
        logger.error(f"Error creating Gemini model: {e}")
        return None


def safe_get_response_text(response) -> str:
    """
    Gemini 응답에서 텍스트를 안전하게 추출
    function_call만 있는 경우에도 오류 없이 처리
    
    Args:
        response: Gemini API 응답 객체
        
    Returns:
        추출된 텍스트 (텍스트가 없으면 빈 문자열)
    """
    try:
        # 먼저 텍스트 파트가 있는지 확인
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                return part.text
        # 텍스트가 없으면 빈 문자열
        return ""
    except (IndexError, AttributeError):
        # 구조가 예상과 다른 경우 직접 .text 시도
        try:
            return response.text
        except Exception:
            return ""
    except Exception as e:
        logger.warning(f"Error extracting response text: {e}")
        return ""


def process_tool_calls(response) -> tuple:
    """
    Gemini 응답에서 Tool 호출 처리 (타임아웃 적용)
    
    Returns:
        (tool_results: list, has_tool_calls: bool)
    """
    tool_results = []
    has_tool_calls = False
    TOOL_TIMEOUT = 15  # 각 Tool 실행 타임아웃 (초)
    
    try:
        # response.candidates[0].content.parts에서 function_call 확인
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                has_tool_calls = True
                func_call = part.function_call
                tool_name = func_call.name
                
                # 파라미터 추출
                params = {}
                if func_call.args:
                    for key, value in func_call.args.items():
                        params[key] = value
                
                logger.info(f"Executing tool: {tool_name} with params: {params}")
                
                # Tool 실행 (타임아웃 적용)
                try:
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(execute_tool, tool_name, params)
                        result = future.result(timeout=TOOL_TIMEOUT)
                except FuturesTimeoutError:
                    logger.error(f"Tool timeout: {tool_name}")
                    result = {
                        "success": False,
                        "message": f"도구 실행 시간 초과 ({tool_name}). 잠시 후 다시 시도해주세요."
                    }
                except Exception as tool_error:
                    logger.error(f"Tool execution error: {tool_name} - {tool_error}")
                    result = {
                        "success": False,
                        "message": f"도구 실행 오류: {str(tool_error)}"
                    }
                
                tool_results.append({
                    "name": tool_name,
                    "params": params,
                    "result": result
                })
                
    except Exception as e:
        logger.error(f"Error processing tool calls: {e}")
    
    return tool_results, has_tool_calls


def format_tool_results_for_response(tool_results: list) -> str:
    """Tool 실행 결과를 사용자 친화적 텍스트로 포맷"""
    formatted = []
    
    for tr in tool_results:
        result = tr["result"]
        tool_name = tr["name"]
        
        if not result.get("success", False):
            formatted.append(f"⚠️ {result.get('message', '조회 실패')}")
            continue
        
        # Tool별 포맷팅
        if tool_name == "get_ocean_rates":
            route = result.get("route", {})
            total = result.get("total", {})
            container = result.get("container", {})
            
            # route 형식에 따라 처리 (문자열 또는 딕셔너리)
            pol_code = route.get("pol") if isinstance(route.get("pol"), str) else route.get("pol", {}).get("code", "")
            pod_code = route.get("pod") if isinstance(route.get("pod"), str) else route.get("pod", {}).get("code", "")
            
            text = f"🚢 **{pol_code} → {pod_code}** 운임\n"
            text += f"- 컨테이너: {container.get('name', '') or container.get('code', '')}\n"
            text += f"- 선사: {result.get('carrier', 'HMM')}\n"
            text += f"- 유효기간: {result.get('validity', {}).get('from', '')} ~ {result.get('validity', {}).get('to', '')}\n"
            
            # 총액 (KRW + USD 이중 표시)
            total_krw = total.get("total_krw_converted", 0)
            total_usd = total.get("usd", 0)
            total_eur = total.get("eur", 0)
            local_krw = total.get("krw", 0)
            
            text += f"\n**💰 총 운임**\n"
            if total_krw:
                text += f"- **한화 합계: ₩{total_krw:,.0f}**\n"
            
            # 외화 합계 표시
            foreign_parts = []
            if total_usd:
                foreign_parts.append(f"USD {total_usd:,.0f}")
            if total_eur:
                foreign_parts.append(f"EUR {total_eur:,.0f}")
            if local_krw:
                foreign_parts.append(f"KRW {local_krw:,.0f}")
            
            if foreign_parts:
                text += f"- 외화 합계: {' + '.join(foreign_parts)}\n"
            
            # 환율 정보 및 출처 표시
            exchange_rates = result.get("exchange_rates_used", {})
            exchange_rate_source = result.get("exchange_rate_source", "")
            if exchange_rates:
                text += f"- 적용 환율: "
                rate_strs = [f"1 {curr} = ₩{rate:,.0f}" for curr, rate in exchange_rates.items()]
                text += ", ".join(rate_strs)
                if exchange_rate_source:
                    text += f" ({exchange_rate_source})"
                text += "\n"
            
            # 상세 항목
            rates = result.get("rates", {})
            for group, items in rates.items():
                text += f"\n[{group}]\n"
                for item in items[:5]:  # 최대 5개만 표시
                    text += f"  - {item['name']}: {item['currency']} {item['rate']:,.0f}\n"
            
            if result.get("note"):
                text += f"\n💡 {result['note']}"
            
            formatted.append(text)
            
        elif tool_name == "get_bidding_status":
            biddings = result.get("biddings", [])
            stats = result.get("statistics", {})
            
            text = f"📋 **비딩 현황** (진행중: {stats.get('open', 0)}건)\n\n"
            for b in biddings[:5]:
                status_icon = {"진행중": "🟢", "마감": "🔴", "낙찰완료": "✅"}.get(b["status"], "⚪")
                text += f"{status_icon} **{b['bidding_no']}** - {b['route']}\n"
                text += f"   {b['shipping_type']} | {b['load_type']} | ETD: {b.get('etd', '-')}\n"
                text += f"   입찰: {b['bid_count']}건 | 마감: {b.get('deadline', '-')}\n\n"
            
            formatted.append(text)
            
        elif tool_name == "get_shipping_indices":
            indices = result.get("indices", {})
            
            text = "📊 **해운 시장 지수**\n\n"
            for idx_name, data in indices.items():
                if "latest" in data:
                    latest = data["latest"]
                    trend_icon = "📈" if latest["trend"] == "상승" else ("📉" if latest["trend"] == "하락" else "➡️")
                    text += f"**{idx_name}** ({data.get('description', '')[:20]})\n"
                    text += f"  {trend_icon} **{latest['value']:,.1f}** ({latest['change_rate']}) - {latest['date']}\n\n"
                else:
                    text += f"**{idx_name}**: {data.get('message', '데이터 없음')}\n\n"
            
            formatted.append(text)
            
        elif tool_name == "get_latest_news":
            articles = result.get("articles", [])
            
            text = "📰 **최신 물류 뉴스**\n\n"
            for i, a in enumerate(articles[:5], 1):
                crisis_badge = "🚨 " if a.get("is_crisis") else ""
                text += f"{i}. {crisis_badge}**{a['title'][:50]}{'...' if len(a['title']) > 50 else ''}**\n"
                text += f"   [{a['category']}] {a['source']} | {a['published_at'][:10]}\n"
                if a.get('summary'):
                    text += f"   {a['summary'][:80]}...\n"
                text += "\n"
            
            formatted.append(text)
            
        elif tool_name == "get_port_info":
            ports = result.get("ports", [])
            
            text = "🌍 **항구 정보**\n\n"
            for p in ports[:10]:
                text += f"- **{p['code']}**: {p['name']} ({p['country']}) - {p['type']}\n"
            
            formatted.append(text)
        
        elif tool_name == "create_quote_request":
            # 견적 요청 생성 결과
            if result.get("success"):
                summary = result.get("summary", {})
                text = "✅ **견적 요청이 성공적으로 생성되었습니다!**\n\n"
                text += f"📋 **요청번호**: `{result.get('request_number', '-')}`\n"
                text += f"📦 **비딩번호**: `{result.get('bidding_no', '-')}`\n"
                text += f"⏰ **입찰 마감일**: {result.get('deadline', '-')}\n\n"
                text += f"**운송 정보**\n"
                text += f"- 경로: {summary.get('route', '-')}\n"
                text += f"- 운송유형: {summary.get('shipping_type', '-')}\n"
                text += f"- 적재유형: {summary.get('load_type', '-')}\n"
                text += f"- 출발예정일: {summary.get('etd', '-')}\n"
                text += f"- 고객사: {summary.get('customer', '-')}\n\n"
                text += "📧 포워더들에게 RFQ가 발송되었습니다. 곧 견적을 받아보실 수 있습니다!"
            else:
                text = f"❌ **견적 요청 생성 실패**\n\n{result.get('message', '알 수 없는 오류')}"
            
            formatted.append(text)
        
        # ══════════════════════════════════════════════════════
        # NEW MCP TOOLS 포맷팅
        # ══════════════════════════════════════════════════════
        
        elif tool_name == "get_air_rates":
            charges = result.get("charges", {})
            text = f"✈️ **{result.get('route', '')}** 항공 운임\n\n"
            text += f"- 화물중량: {result.get('weight_kg', 0)}kg\n"
            text += f"- Chargeable Weight: {result.get('chargeable_weight_kg', 0)}kg\n"
            text += f"- 예상 Transit: {result.get('transit_days', '-')}\n\n"
            text += f"**운임 내역**\n"
            text += f"- 기본운임: ${charges.get('freight', 0):,.2f}\n"
            text += f"- 유류할증료: ${charges.get('fuel_surcharge', 0):,.2f}\n"
            text += f"- 보안료: ${charges.get('security_fee', 0):,.2f}\n"
            text += f"- AWB발급료: ${charges.get('awb_fee', 0):,.2f}\n"
            text += f"- **총계: ${charges.get('total', 0):,.2f}**\n"
            if result.get("note"):
                text += f"\n💡 {result['note']}"
            formatted.append(text)
        
        elif tool_name == "get_schedules":
            schedules = result.get("schedules", [])
            ship_type = result.get("shipping_type", "")
            icon = "✈️" if "항공" in ship_type else "🚢"
            
            text = f"{icon} **{result.get('route', '')}** 스케줄 ({ship_type})\n\n"
            for i, s in enumerate(schedules[:5], 1):
                if "flight_no" in s:  # 항공
                    text += f"{i}. **{s['carrier']} {s['flight_no']}**\n"
                    text += f"   {s['departure']} {s.get('departure_time', '')} → {s['arrival']}\n"
                    text += f"   {s['stops']} | {s.get('available', '')}\n\n"
                else:  # 해상
                    text += f"{i}. **{s['carrier']}** - {s.get('vessel', '')}\n"
                    text += f"   {s['departure']} → {s['arrival']} ({s['transit_days']}일)\n"
                    text += f"   {s.get('transhipment', '')} | {s.get('available', '')}\n\n"
            formatted.append(text)
        
        elif tool_name == "get_quote_detail":
            quote = result.get("quote", {})
            bidding = result.get("bidding", {})
            customer = result.get("customer", {})
            
            text = f"📄 **견적 상세** - {bidding.get('bidding_no', quote.get('request_number', '-'))}\n\n"
            text += f"**운송 정보**\n"
            text += f"- 경로: {quote.get('route', '-')}\n"
            text += f"- 운송유형: {quote.get('shipping_type', '-')} / {quote.get('load_type', '-')}\n"
            text += f"- ETD: {quote.get('etd', '-')} → ETA: {quote.get('eta', '-')}\n"
            text += f"- 인코텀즈: {quote.get('incoterms', '-')}\n\n"
            text += f"**비딩 현황**\n"
            text += f"- 상태: {bidding.get('status', '-')}\n"
            text += f"- 마감일: {bidding.get('deadline', '-')}\n\n"
            text += f"**고객**: {customer.get('company', '-')} ({customer.get('name', '-')})"
            formatted.append(text)
        
        elif tool_name == "get_exchange_rates":
            rates = result.get("rates", {})
            base = result.get("base_currency", "USD")
            source = result.get("source", "")
            
            text = f"💱 **환율 정보** (기준: {base})\n\n"
            for target, data in rates.items():
                text += f"- {base}/{target}: **{data['rate']:,.2f}**\n"
            if source:
                text += f"\n📊 출처: {source}"
            if result.get("note"):
                text += f"\n💡 {result['note']}"
            formatted.append(text)
        
        elif tool_name == "get_global_alerts":
            alerts = result.get("alerts", [])
            
            text = "🚨 **글로벌 물류 경고**\n\n"
            for a in alerts[:5]:
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(a.get("severity", ""), "⚪")
                text += f"{severity_icon} **{a.get('title', '-')}**\n"
                text += f"   [{a.get('category', '-')}] {a.get('region', '-')} | {a.get('date', '-')}\n"
                if a.get("impact"):
                    text += f"   영향: {a['impact']}\n"
                text += "\n"
            formatted.append(text)
        
        elif tool_name == "navigate_to_page":
            text = f"🔗 **{result.get('title', '')}** 페이지로 이동합니다.\n\n"
            text += f"{result.get('description', '')}\n"
            text += f"URL: `{result.get('url', '')}`"
            formatted.append(text)
        
        # ══════════════════════════════════════════════════════
        # NEW TOOLS 포맷팅 (Phase 0~3)
        # ══════════════════════════════════════════════════════
        
        elif tool_name == "get_my_quotes":
            quotes = result.get("quotes", [])
            text = f"📋 **내 견적 요청 목록** ({result.get('count', 0)}건)\n\n"
            for q in quotes[:10]:
                status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "cancelled": "❌"}.get(q.get("status"), "📄")
                text += f"{status_icon} **{q.get('request_number', q.get('bidding_no', '-'))}**\n"
                text += f"   {q.get('pol', '-')} → {q.get('pod', '-')} | {q.get('shipping_type', '-')}\n"
                text += f"   ETD: {q.get('etd', '-')} | 상태: {q.get('status', '-')}\n\n"
            formatted.append(text)
        
        elif tool_name == "update_quote_request":
            text = f"✏️ **견적 수정 완료**\n\n"
            text += f"- 비딩번호: {result.get('bidding_no', '-')}\n"
            text += f"- 수정된 항목: {', '.join(result.get('updated_fields', []))}"
            formatted.append(text)
        
        elif tool_name == "cancel_quote_request":
            text = f"🗑️ **견적 취소 완료**\n\n{result.get('message', '')}"
            formatted.append(text)
        
        elif tool_name == "submit_bid":
            text = f"📤 **입찰 제출 완료**\n\n"
            text += f"- 비딩 ID: {result.get('bidding_id', '-')}\n"
            text += f"- 입찰 ID: {result.get('bid_id', '-')}\n"
            text += f"- 제안 금액: **${result.get('total_amount', 0):,.2f}**"
            formatted.append(text)
        
        elif tool_name == "award_bid":
            text = f"🏆 **낙찰 완료**\n\n"
            text += f"- 비딩번호: {result.get('bidding_no', '-')}\n"
            text += f"- 낙찰 포워더: **{result.get('forwarder_company', '-')}**\n"
            text += f"- 낙찰 금액: **${result.get('total_amount', 0):,.2f}**"
            formatted.append(text)
        
        elif tool_name == "get_bidding_detail":
            bidding = result.get("bidding", {})
            text = f"📋 **비딩 상세** - {bidding.get('bidding_no', '-')}\n\n"
            text += f"- 상태: {bidding.get('status', '-')}\n"
            text += f"- 경로: {bidding.get('pol', '-')} → {bidding.get('pod', '-')}\n"
            text += f"- 운송유형: {bidding.get('shipping_type', '-')}\n"
            text += f"- 마감일: {bidding.get('deadline', '-')}\n"
            text += f"- 입찰 수: {bidding.get('bid_count', 0)}건"
            formatted.append(text)
        
        elif tool_name == "get_bidding_bids":
            bids = result.get("bids", [])
            text = f"📊 **입찰 목록** - {result.get('bidding_no', '')} ({result.get('count', 0)}건)\n\n"
            for i, b in enumerate(bids[:10], 1):
                status_icon = {"submitted": "📤", "awarded": "🏆", "rejected": "❌"}.get(b.get("status"), "📋")
                text += f"{i}. {status_icon} **{b.get('forwarder_company', b.get('forwarder_name', '-'))}**\n"
                text += f"   💰 **${b.get('total_amount', 0):,.2f}** | ⏱️ {b.get('transit_time', '-')}\n"
                if b.get('rating'):
                    text += f"   ⭐ {b.get('rating', '-')} | "
                text += f"   제출: {str(b.get('submitted_at', '-'))[:16]}\n\n"
            formatted.append(text)
        
        elif tool_name == "close_bidding":
            text = f"🔒 **비딩 마감**\n\n{result.get('message', '')}"
            formatted.append(text)
        
        elif tool_name == "get_my_bids":
            bids = result.get("bids", [])
            text = f"📋 **내 입찰 목록** ({result.get('count', 0)}건)\n\n"
            for b in bids[:10]:
                status_icon = {"submitted": "📤", "awarded": "🏆", "rejected": "❌"}.get(b.get("status"), "📋")
                text += f"{status_icon} **{b.get('bidding_no', '-')}** - ${b.get('total_amount', 0):,.2f}\n"
                text += f"   {b.get('route', '-')} | 상태: {b.get('status', '-')}\n\n"
            formatted.append(text)
        
        elif tool_name == "get_contracts":
            contracts = result.get("contracts", [])
            text = f"📝 **계약 목록** ({result.get('count', 0)}건)\n\n"
            for c in contracts[:10]:
                status_icon = {"pending": "⏳", "confirmed": "✅", "in_progress": "🚚", "completed": "✔️", "cancelled": "❌"}.get(c.get("status"), "📝")
                text += f"{status_icon} **{c.get('contract_no', '-')}**\n"
                text += f"   {c.get('route', '-')} | {c.get('forwarder_company', '-')}\n"
                text += f"   금액: ${c.get('total_amount', 0):,.2f}\n\n"
            formatted.append(text)
        
        elif tool_name == "get_contract_detail":
            contract = result.get("contract", {})
            text = f"📝 **계약 상세** - {contract.get('contract_no', '-')}\n\n"
            text += f"- 상태: {contract.get('status', '-')}\n"
            text += f"- 경로: {contract.get('pol', '-')} → {contract.get('pod', '-')}\n"
            text += f"- 포워더: {contract.get('forwarder_company', '-')}\n"
            text += f"- 금액: **${contract.get('total_amount', 0):,.2f}**\n"
            text += f"- ETD: {contract.get('etd', '-')} | ETA: {contract.get('eta', '-')}"
            formatted.append(text)
        
        elif tool_name == "track_shipment":
            shipment = result.get("shipment", {})
            status_icon = {"pending": "⏳", "picked_up": "📦", "in_transit": "🚚", "delivered": "✅"}.get(shipment.get("current_status"), "📍")
            text = f"🚚 **배송 추적** - {shipment.get('shipment_no', '-')}\n\n"
            text += f"**현재 상태**: {status_icon} {shipment.get('current_status', '-')}\n"
            text += f"**현재 위치**: {shipment.get('current_location', '-')}\n\n"
            text += f"- 경로: {shipment.get('pol', '-')} → {shipment.get('pod', '-')}\n"
            text += f"- B/L No: {shipment.get('bl_no', '-')}\n"
            text += f"- 선박/항공: {shipment.get('vessel_flight', '-')}\n"
            text += f"- 예상 도착: {shipment.get('estimated_delivery', '-')}\n\n"
            
            history = shipment.get("tracking_history", [])
            if history:
                text += "**추적 이력**\n"
                for h in history[:5]:
                    text += f"- {h.get('created_at', '-')[:16]} | {h.get('status', '-')} @ {h.get('location', '-')}\n"
            formatted.append(text)
        
        elif tool_name == "get_shipments":
            shipments = result.get("shipments", [])
            text = f"📦 **배송 목록** ({result.get('count', 0)}건)\n\n"
            for s in shipments[:10]:
                status_icon = {"pending": "⏳", "picked_up": "📦", "in_transit": "🚚", "delivered": "✅"}.get(s.get("current_status"), "📍")
                text += f"{status_icon} **{s.get('shipment_no', '-')}**\n"
                text += f"   {s.get('pol', '-')} → {s.get('pod', '-')} | {s.get('current_status', '-')}\n\n"
            formatted.append(text)
        
        elif tool_name == "get_shipper_analytics":
            analytics = result.get("analytics", {})
            text = f"📊 **화주 분석 데이터**\n\n"
            text += f"- 총 요청 건수: **{analytics.get('total_requests', 0)}건**\n"
            text += f"- 평균 입찰 수: **{analytics.get('avg_bids_per_request', 0):.1f}건/요청**\n"
            text += f"- 낙찰률: **{analytics.get('award_rate', 0):.1f}%**\n"
            text += f"- 총 운송비: **₩{analytics.get('total_cost_krw', 0):,.0f}**\n"
            text += f"- 평균 절감률: **{analytics.get('avg_saving_rate', 0):.1f}%**"
            formatted.append(text)
        
        elif tool_name == "get_notifications":
            notifications = result.get("notifications", [])
            text = f"🔔 **알림** ({result.get('count', 0)}건, 읽지 않음: {result.get('unread_count', 0)}건)\n\n"
            for n in notifications[:10]:
                read_icon = "📩" if not n.get("is_read") else "📬"
                text += f"{read_icon} **{n.get('title', '-')}**\n"
                text += f"   {n.get('message', '-')[:50]}...\n"
                text += f"   {n.get('created_at', '-')[:16]}\n\n"
            formatted.append(text)
        
        elif tool_name == "send_message":
            text = f"💬 **메시지 발송 완료**\n\n{result.get('message', '')}"
            formatted.append(text)
        
        else:
            # 기본 포맷
            formatted.append(f"✅ {tool_name} 조회 완료\n{json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
    
    return "\n".join(formatted)


def chat_with_gemini(session_id: str, user_message: str) -> Dict[str, Any]:
    """
    Gemini와 대화 (Dynamic Prompt + Tool 함수 호출 포함)
    
    Args:
        session_id: 세션 ID
        user_message: 사용자 메시지
    
    Returns:
        {
            "success": bool,
            "message": str,
            "quote_data": Optional[dict],
            "tool_used": Optional[list]  # 사용된 Tool 목록
        }
    """
    if not GEMINI_AVAILABLE:
        return {
            "success": False,
            "message": "AI 서비스를 사용할 수 없습니다. GEMINI_API_KEY를 확인해주세요.",
            "quote_data": None,
            "tool_used": None
        }
    
    try:
        # Dynamic Prompt 시스템 사용
        if DYNAMIC_PROMPT_AVAILABLE:
            # Intent 분류
            intents = classify_intent(user_message)
            intent_desc = get_intent_description(intents)
            logger.info(f"[Intent] Classified: {intent_desc} for message: {user_message[:50]}...")
            
            # 동적 프롬프트 생성
            dynamic_prompt = get_dynamic_prompt(intents)
            logger.info(f"[Prompt] Generated dynamic prompt ({len(dynamic_prompt)} chars)")
            
            # 필요한 Tool 선별
            tool_filter = get_tools_for_intents(intents)
            logger.info(f"[Tools] Selected {len(tool_filter)} tools: {sorted(tool_filter)}")
            
            # 모델 생성 (동적 프롬프트 + 선별된 Tool)
            model = get_gemini_model(
                with_tools=AI_TOOLS_AVAILABLE,
                system_prompt=dynamic_prompt,
                tool_filter=tool_filter
            )
        else:
            # 기존 방식 (전체 프롬프트 + 전체 Tool)
            logger.info("[Prompt] Using legacy full prompt")
            model = get_gemini_model(with_tools=AI_TOOLS_AVAILABLE)
        
        if not model:
            return {
                "success": False,
                "message": "AI 모델을 로드할 수 없습니다.",
                "quote_data": None,
                "tool_used": None
            }
        
        # 대화 이력 가져오기
        history = conversation_manager.get_history(session_id)
        
        # 채팅 시작
        chat = model.start_chat(history=history)
        
        # 첫 번째 메시지 전송
        logger.info(f"[DEBUG] Sending message to Gemini: {user_message[:100]}...")
        response = chat.send_message(user_message)
        
        # 응답 디버그 로그
        logger.info(f"[DEBUG] Gemini response received")
        try:
            response_text = safe_get_response_text(response)
            logger.info(f"[DEBUG] Response text (first 200 chars): {response_text[:200] if response_text else 'EMPTY'}")
            
            # Tool 호출 여부 확인
            has_function_call = False
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_call = True
                        logger.info(f"[DEBUG] Function call detected: {part.function_call.name}")
            logger.info(f"[DEBUG] Has function call: {has_function_call}")
        except Exception as debug_err:
            logger.warning(f"[DEBUG] Error in debug logging: {debug_err}")
        
        # Tool 호출 처리
        tool_results, has_tool_calls = process_tool_calls(response)
        tools_used = []
        logger.info(f"[DEBUG] Tool results count: {len(tool_results)}, has_tool_calls: {has_tool_calls}")
        
        if has_tool_calls and tool_results:
            # Tool 결과를 Gemini에 전달하여 최종 응답 생성
            tools_used = [tr["name"] for tr in tool_results]
            
            # Tool 결과를 포맷하여 컨텍스트에 추가
            tool_context = format_tool_results_for_response(tool_results)
            
            # Tool 결과와 함께 후속 응답 요청
            follow_up = f"""위 도구 조회 결과를 바탕으로 사용자에게 친절하게 설명해주세요.

[조회 결과]
{tool_context}

사용자의 원래 질문: {user_message}

자연스럽게 답변해주세요. 도구를 사용했다는 것은 언급하지 마세요."""

            # Function calling 응답 처리
            try:
                # Gemini에 function 결과 전달
                from google.generativeai.types import content_types
                
                function_responses = []
                for tr in tool_results:
                    function_responses.append({
                        "name": tr["name"],
                        "response": tr["result"]
                    })
                
                # function_response 형식으로 전달
                final_response = chat.send_message(
                    content_types.to_content({
                        "parts": [{"function_response": fr} for fr in function_responses]
                    })
                )
                ai_message = safe_get_response_text(final_response)
                
                # 텍스트가 비어있으면 Tool 결과 직접 사용
                if not ai_message.strip():
                    ai_message = tool_context
                
            except Exception as e:
                logger.warning(f"Function response failed, using fallback: {e}")
                # 폴백: 직접 컨텍스트로 전달
                final_response = chat.send_message(follow_up)
                ai_message = safe_get_response_text(final_response)
                
                if not ai_message.strip():
                    ai_message = tool_context
        else:
            # Tool 호출 없음 - 일반 응답
            ai_message = safe_get_response_text(response)
        
        # 대화 이력 저장
        conversation_manager.add_message(session_id, "user", user_message)
        conversation_manager.add_message(session_id, "model", ai_message)
        
        # Quote 데이터 추출 시도
        quote_data = extract_quote_data(ai_message)
        
        # 폴백: AI가 JSON을 출력하지 않았으면 대화 내용에서 추출
        if quote_data is None:
            conversation_history = conversation_manager.get_history(session_id)
            quote_data = extract_quote_from_conversation(conversation_history, ai_message)
            if quote_data:
                logger.info("Quote data extracted via fallback mechanism")
        
        return {
            "success": True,
            "message": ai_message,
            "quote_data": quote_data,
            "tool_used": tools_used if tools_used else None
        }
        
    except Exception as e:
        logger.error(f"Gemini API error: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"AI 응답 중 오류가 발생했습니다: {str(e)}",
            "quote_data": None,
            "tool_used": None
        }


def extract_quote_data(ai_message: str) -> Optional[Dict]:
    """
    AI 응답에서 Quote 데이터 추출
    
    Args:
        ai_message: AI 응답 텍스트
    
    Returns:
        추출된 Quote 데이터 또는 None
    """
    try:
        import re
        
        # 방법 1: {quote_data: {...}} 또는 {"quote_data": {...}} 형식 찾기
        # 중첩 객체를 처리하기 위해 brace 카운팅 사용
        patterns = [
            r'\{[\s]*["\']?quote_data["\']?\s*:\s*\{',  # {quote_data: { 또는 {"quote_data": {
        ]
        
        for pattern in patterns:
            match = re.search(pattern, ai_message)
            if match:
                start_idx = match.start()
                # Brace 카운팅으로 전체 JSON 추출
                brace_count = 0
                in_string = False
                escape_next = False
                
                for i, char in enumerate(ai_message[start_idx:]):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_str = ai_message[start_idx:start_idx + i + 1]
                                try:
                                    # JSON 키에 따옴표가 없는 경우 처리
                                    json_str_fixed = re.sub(r'(\{|\,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
                                    data = json.loads(json_str_fixed)
                                    return data.get("quote_data")
                                except json.JSONDecodeError:
                                    # 원본으로 시도
                                    try:
                                        data = json.loads(json_str)
                                        return data.get("quote_data")
                                    except:
                                        pass
                                break
        
        # 방법 2: 코드 블록 내 JSON 찾기
        code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', ai_message)
        if code_block_match:
            json_str = code_block_match.group(1)
            try:
                json_str_fixed = re.sub(r'(\{|\,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
                data = json.loads(json_str_fixed)
                if "quote_data" in data:
                    return data.get("quote_data")
                # quote_data 래퍼 없이 직접 데이터인 경우
                if "trade_mode" in data or "shipping_type" in data:
                    return data
            except:
                pass
        
        return None
        
    except Exception as e:
        logger.debug(f"Quote data extraction failed: {e}")
        return None


def extract_quote_from_conversation(conversation_history: List[Dict], ai_message: str) -> Optional[Dict]:
    """
    대화 내용 전체를 분석하여 Quote 데이터 추출 (폴백 메커니즘)
    
    AI가 JSON을 출력하지 않았을 때 대화 내용에서 정보를 추출합니다.
    
    Args:
        conversation_history: 전체 대화 이력
        ai_message: 마지막 AI 응답
        
    Returns:
        추출된 Quote 데이터 또는 None
    """
    import re
    
    # "모든 정보가 확인되었습니다" 또는 유사 문구가 있는지 확인
    completion_phrases = [
        "모든 정보가 확인",
        "모든 정보가 수집",  # 추가
        "정보가 모두 수집",
        "견적 요청을 생성",
        "견적을 생성",
        "요청을 진행",
        "모든 필수 정보",
        "수집된 정보 (완료",  # 추가: ✅ 수집된 정보 (완료!):
    ]
    
    is_complete = any(phrase in ai_message for phrase in completion_phrases)
    
    if not is_complete:
        return None
    
    # 대화 내용 전체를 하나의 텍스트로 합침
    full_text = ai_message
    for msg in conversation_history:
        # Gemini 형식: {"role": "...", "parts": ["..."]}
        parts = msg.get("parts", [])
        if parts:
            full_text += "\n" + parts[0]
        # 일반 형식: {"role": "...", "content": "..."}
        elif msg.get("content"):
            full_text += "\n" + msg.get("content", "")
    
    full_text_lower = full_text.lower()
    
    quote_data = {}
    
    # trade_mode 추출
    if "수입" in full_text or "import" in full_text_lower:
        quote_data["trade_mode"] = "import"
    elif "수출" in full_text or "export" in full_text_lower:
        quote_data["trade_mode"] = "export"
    elif "국내" in full_text or "domestic" in full_text_lower:
        quote_data["trade_mode"] = "domestic"
    
    # shipping_type 추출
    if "항공" in full_text or "air" in full_text_lower:
        quote_data["shipping_type"] = "air"
        quote_data["load_type"] = "Air"
    elif "해상" in full_text or "ocean" in full_text_lower or "선박" in full_text:
        quote_data["shipping_type"] = "ocean"
    elif "육상" in full_text or "truck" in full_text_lower or "트럭" in full_text:
        quote_data["shipping_type"] = "truck"
    
    # POL 추출 (공항/항구 코드)
    pol_patterns = [
        r'출발지[:\s]*([A-Z]{3})',
        r'출발[:\s]*[가-힣]*\(([A-Z]{3})\)',
        r'카타니아[^)]*\(([A-Z]{3})\)',
        r'팔레르모[^)]*\(([A-Z]{3})\)',
        r'CTA|PMO|FCO|MXP'  # 이탈리아 공항 코드
    ]
    for pattern in pol_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            code = match.group(1) if match.lastindex else match.group(0)
            quote_data["pol"] = code.upper()
            break
    
    # POD 추출
    pod_patterns = [
        r'도착지[:\s]*([A-Z]{3,5})',
        r'도착[:\s]*[가-힣]*\(([A-Z]{3,5})\)',
        r'인천[^)]*\(([A-Z]{3,5})\)',
        r'ICN|KRICN'  # 인천공항 코드
    ]
    for pattern in pod_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            code = match.group(1) if match.lastindex else match.group(0)
            quote_data["pod"] = code.upper()
            break
    
    # 인천공항 기본값
    if "pod" not in quote_data and ("인천" in full_text or "한국" in full_text):
        quote_data["pod"] = "ICN"
    
    # ETD/ETA 추출 (YYYY-MM-DD 형식)
    # ETD 패턴: "ETD: 2026-01-20" 또는 "출발 예정일: 2026-01-20"
    etd_match = re.search(r'(?:ETD|출발)[:\s]*(\d{4}-\d{2}-\d{2})', full_text, re.IGNORECASE)
    if etd_match:
        quote_data["etd"] = etd_match.group(1)
    else:
        # 일반적인 날짜 패턴 (첫 번째 날짜를 ETD로)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', full_text)
        if date_match:
            quote_data["etd"] = date_match.group(1)
    
    # ETA 패턴: "ETA: 2026-01-25" 또는 "도착 예정일: 2026-01-25"
    eta_match = re.search(r'(?:ETA|도착)[:\s]*(\d{4}-\d{2}-\d{2})', full_text, re.IGNORECASE)
    if eta_match:
        quote_data["eta"] = eta_match.group(1)
    
    # Invoice Value 추출 (USD 금액)
    # 패턴: "송장 금액: $500" 또는 "500 USD" 또는 "invoice: 500"
    invoice_match = re.search(r'(?:송장|invoice|금액)[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|달러)?', full_text, re.IGNORECASE)
    if invoice_match:
        amount_str = invoice_match.group(1).replace(',', '')
        quote_data["invoice_value_usd"] = float(amount_str)
    else:
        # 간단한 패턴: "$500" 또는 "500 USD"
        invoice_match2 = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)|(\d+(?:,\d{3})*(?:\.\d{2})?)\s*USD', full_text, re.IGNORECASE)
        if invoice_match2:
            amount_str = (invoice_match2.group(1) or invoice_match2.group(2)).replace(',', '')
            quote_data["invoice_value_usd"] = float(amount_str)
    
    # 고객 정보 추출 (슬래시로 구분된 형식: 회사명/이름/이메일/전화)
    customer_match = re.search(r'([가-힣\w]+)/([가-힣\w]+)/([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/(\d{2,3}-\d{3,4}-\d{4})', full_text)
    if customer_match:
        quote_data["customer_company"] = customer_match.group(1)
        quote_data["customer_name"] = customer_match.group(2)
        quote_data["customer_email"] = customer_match.group(3)
        quote_data["customer_phone"] = customer_match.group(4)
    
    # 인코텀즈 추출
    incoterms_match = re.search(r'\b(EXW|FOB|CFR|CIF|DAP|DDP|FCA|CPT|CIP|DAT|DAU)\b', full_text, re.IGNORECASE)
    if incoterms_match:
        quote_data["incoterms"] = incoterms_match.group(1).upper()
    
    # ═══════════════════════════════════════════════════════════
    # 화물 정보 파싱 (패키지당 중량 × 수량)
    # ═══════════════════════════════════════════════════════════
    
    # 패턴 1: "포장: 3kg 버킷 × 6개" (가장 명확한 패턴 - 우선순위 높음)
    # Unicode × (U+00D7)와 일반 x/X/* 모두 매칭
    pkg_pattern1 = re.search(r'포장[:\s]*(\d+(?:\.\d+)?)\s*kg[^\d]+(\d+)\s*개', full_text)
    if pkg_pattern1:
        quote_data["gross_weight_per_pkg"] = float(pkg_pattern1.group(1))
        quote_data["pkg_qty"] = int(pkg_pattern1.group(2))
        quote_data["cargo_weight_kg"] = quote_data["gross_weight_per_pkg"] * quote_data["pkg_qty"]
        logger.info(f"Pattern1 (포장) matched: {quote_data['gross_weight_per_pkg']}kg × {quote_data['pkg_qty']}개 = {quote_data['cargo_weight_kg']}kg")
    
    # 패턴 2: "3kg 버킷 × 6개" 또는 "3kg x 6개" (일반 패턴)
    # [^\d]+ = 숫자가 아닌 문자들 (×, x, 버킷, 공백 등 모두 포함)
    if "gross_weight_per_pkg" not in quote_data:
        pkg_pattern2 = re.search(r'(\d+(?:\.\d+)?)\s*kg[^\d]+(\d+)\s*개', full_text)
        if pkg_pattern2:
            quote_data["gross_weight_per_pkg"] = float(pkg_pattern2.group(1))
            quote_data["pkg_qty"] = int(pkg_pattern2.group(2))
            quote_data["cargo_weight_kg"] = quote_data["gross_weight_per_pkg"] * quote_data["pkg_qty"]
            logger.info(f"Pattern2 matched: {quote_data['gross_weight_per_pkg']}kg × {quote_data['pkg_qty']}개 = {quote_data['cargo_weight_kg']}kg")
    
    # 패턴 3: "버킷 6개 × 3kg" 또는 "6개 × 3kg" (역순 패턴)
    if "gross_weight_per_pkg" not in quote_data:
        pkg_pattern3 = re.search(r'(\d+)\s*개[^\d]+(\d+(?:\.\d+)?)\s*kg', full_text)
        if pkg_pattern3:
            quote_data["pkg_qty"] = int(pkg_pattern3.group(1))
            quote_data["gross_weight_per_pkg"] = float(pkg_pattern3.group(2))
            quote_data["cargo_weight_kg"] = quote_data["gross_weight_per_pkg"] * quote_data["pkg_qty"]
            logger.info(f"Pattern3 (역순) matched: {quote_data['pkg_qty']}개 × {quote_data['gross_weight_per_pkg']}kg")
    
    # 패턴 4: "수량: 약 18kg" + "6개" 분리된 경우
    if "gross_weight_per_pkg" not in quote_data:
        # 총 중량 추출
        weight_match = re.search(r'(?:약|총|수량)[:\s]*(\d+(?:\.\d+)?)\s*kg', full_text, re.IGNORECASE)
        # 개수 추출
        qty_match = re.search(r'(\d+)\s*개', full_text)
        if weight_match and qty_match:
            total_weight = float(weight_match.group(1))
            qty = int(qty_match.group(1))
            quote_data["cargo_weight_kg"] = total_weight
            quote_data["pkg_qty"] = qty
            quote_data["gross_weight_per_pkg"] = total_weight / qty if qty > 0 else total_weight
            logger.info(f"Pattern4 matched: 총 {total_weight}kg, {qty}개, 개당 {quote_data['gross_weight_per_pkg']}kg")
    
    # 패턴 5: 총 중량만 있는 경우 (약 18kg 등)
    if "cargo_weight_kg" not in quote_data:
        weight_match = re.search(r'(?:약|총)?[\s]*(\d+(?:\.\d+)?)\s*kg', full_text, re.IGNORECASE)
        if weight_match:
            quote_data["cargo_weight_kg"] = float(weight_match.group(1))
            logger.info(f"Pattern5 matched: 총 중량 {quote_data['cargo_weight_kg']}kg")
    
    # 픽업 정보
    if "픽업" in full_text or "EXW" in full_text.upper():
        quote_data["pickup_required"] = True
        # 픽업 주소 추출 시도
        if "시칠리" in full_text or "sicily" in full_text_lower:
            quote_data["pickup_address"] = "Sicily, Italy"
    
    # load_type 자동 설정 (shipping_type 기반)
    if quote_data.get("shipping_type") == "air" and "load_type" not in quote_data:
        quote_data["load_type"] = "Air"
    elif quote_data.get("shipping_type") == "ocean" and "load_type" not in quote_data:
        # 해상은 FCL/LCL 선택 필요하지만 기본값 설정
        quote_data["load_type"] = "LCL"
    elif quote_data.get("shipping_type") == "truck" and "load_type" not in quote_data:
        quote_data["load_type"] = "FTL"
    
    # 필수 필드 체크 (eta, invoice_value_usd 추가)
    required_fields = ["trade_mode", "shipping_type", "pol", "pod", "etd", "eta", "invoice_value_usd",
                      "customer_company", "customer_name", "customer_email", "customer_phone"]
    
    if all(field in quote_data for field in required_fields):
        logger.info(f"Quote data extracted from conversation: {quote_data}")
        return quote_data
    
    # 일부 필드만 있어도 반환 (프론트엔드에서 처리)
    if len(quote_data) >= 5:
        logger.info(f"Partial quote data extracted: {quote_data}")
        return quote_data
    
    return None


def get_quick_suggestions() -> List[Dict[str, str]]:
    """빠른 제안 버튼 목록"""
    return [
        {"id": "quote", "label": "운임 조회", "prompt": "운임을 조회하고 싶어요"},
        {"id": "bidding", "label": "비딩 현황", "prompt": "현재 진행 중인 비딩 현황을 알려주세요"},
        {"id": "market", "label": "시장 동향", "prompt": "최근 해운 시장 동향이 어떤가요?"},
        {"id": "help", "label": "도움말", "prompt": "이 플랫폼에서 무엇을 할 수 있나요?"}
    ]


def clear_conversation(session_id: str) -> bool:
    """대화 이력 삭제"""
    try:
        conversation_manager.clear_history(session_id)
        return True
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        return False


# ============================================================
# TEST FUNCTION
# ============================================================

if __name__ == "__main__":
    # 테스트
    print("=" * 60)
    print("Gemini Backend Test (with DB Tools)")
    print("=" * 60)
    print(f"Gemini Available: {GEMINI_AVAILABLE}")
    print(f"AI Tools Available: {AI_TOOLS_AVAILABLE}")
    print(f"API Key: {'Set' if GEMINI_API_KEY else 'Not Set'}")
    
    # AI Tools 단독 테스트
    if AI_TOOLS_AVAILABLE:
        print("\n--- AI Tools Direct Test ---")
        
        # 운임 조회 테스트
        print("\n[1] Ocean Rates Test (KRPUS → NLRTM)")
        from ai_tools import get_ocean_rates
        result = get_ocean_rates("KRPUS", "NLRTM", "4HDC")
        print(f"Success: {result.get('success')}")
        if result.get('success'):
            print(f"Total: {result.get('total', {}).get('summary', 'N/A')}")
        else:
            print(f"Message: {result.get('message')}")
        
        # 비딩 현황 테스트
        print("\n[2] Bidding Status Test")
        from ai_tools import get_bidding_status
        result = get_bidding_status("open", 3)
        print(f"Success: {result.get('success')}, Count: {result.get('count', 0)}")
        
        # 해운 지수 테스트
        print("\n[3] Shipping Indices Test (BDI)")
        from ai_tools import get_shipping_indices
        result = get_shipping_indices("BDI", 3)
        print(f"Success: {result.get('success')}")
        if result.get('indices', {}).get('BDI', {}).get('latest'):
            print(f"BDI: {result['indices']['BDI']['latest']['value']}")
        
        # 뉴스 테스트
        print("\n[4] Latest News Test")
        from ai_tools import get_latest_news
        result = get_latest_news(limit=2)
        print(f"Success: {result.get('success')}, Count: {result.get('count', 0)}")
    
    # Gemini 대화 테스트
    if GEMINI_AVAILABLE:
        print("\n--- Gemini Chat Test ---")
        session_id = "test_session"
        
        test_messages = [
            "안녕하세요! 부산에서 로테르담까지 40HC 운임이 얼마인가요?",
            "현재 BDI 지수가 어떻게 되나요?",
            "진행 중인 비딩이 있나요?"
        ]
        
        for msg in test_messages:
            print(f"\n{'='*40}")
            print(f"User: {msg}")
            result = chat_with_gemini(session_id, msg)
            print(f"AI: {result['message'][:300]}...")
            if result.get('tool_used'):
                print(f"[Tools Used: {result['tool_used']}]")
            if result.get('quote_data'):
                print(f"[Quote Data: {result['quote_data']}]")
