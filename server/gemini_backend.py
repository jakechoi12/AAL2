"""
Gemini AI Backend - AI Assistant for AAL Platform
Google Gemini API를 사용한 AI 어시스턴트
"""

import os
import json
import logging
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

try:
    import google.generativeai as genai
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        logger.info("Gemini API configured successfully")
    else:
        GEMINI_AVAILABLE = False
        logger.warning("GEMINI_API_KEY not found in environment variables")
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai package not installed")

# ============================================================
# SYSTEM PROMPT - 플랫폼 기능 및 Quote Request 필드 정의
# ============================================================

SYSTEM_PROMPT = """당신은 AAL(Asia Logistics Link) 물류 플랫폼의 AI 어시스턴트입니다.
사용자가 물류 서비스를 쉽게 이용할 수 있도록 친절하게 안내해주세요.

## 플랫폼 주요 기능
1. **Quick Quote Request** - 운임 견적 조회
2. **Bidding** - 포워더 비딩 현황 확인
3. **Contract Management** - 계약 관리
4. **Market Data** - 시장 데이터 (BDI, SCFI 등)
5. **News Intelligence** - 물류 뉴스

## Quick Quote Request 필드 (운임 조회 시 필요)
사용자와 대화를 통해 아래 정보를 수집하세요:

1. **Trade Mode** (필수)
   - export: 수출
   - import: 수입
   - domestic: 국내

2. **Shipping Type** (필수)
   - ocean: 해상운송
   - air: 항공운송
   - truck: 내륙운송

3. **Load Type** (필수, Shipping Type에 따라 다름)
   - Ocean: FCL(Full Container Load), LCL(Less than Container Load)
   - Air: AIR
   - Truck: FTL(Full Truck Load), LTL(Less than Truck Load)

4. **POL (Port of Loading)** - 출발지 항구/도시 (필수)
   - 예: KRPUS (부산), KRINC (인천), KRSEL (서울)

5. **POD (Port of Discharging)** - 도착지 항구/도시 (필수)
   - 예: NLRTM (로테르담), CNSHA (상하이), USNYC (뉴욕)

6. **Container Type** (FCL인 경우 필수)
   - 20DC: 20ft Dry Container
   - 40DC: 40ft Dry Container
   - 40HC/4HDC: 40ft High Cube Container
   - 20RF: 20ft Reefer Container
   - 40RF: 40ft Reefer Container

7. **ETD** (Estimated Time of Departure) - 출발 예정일
   - 형식: YYYY-MM-DD

8. **Cargo Details** (선택)
   - 중량(kg), 부피(CBM), 수량

## 응답 규칙
1. 한국어로 친절하게 응답하세요
2. 필요한 정보를 하나씩 자연스럽게 물어보세요
3. 사용자가 잘못된 값을 입력하면 올바른 예시를 알려주세요
4. 모든 필수 정보가 수집되면 견적 조회가 가능하다고 안내하세요
5. 전문 용어는 쉽게 설명해주세요

## 데이터 추출 형식
모든 필수 정보가 수집되면, 응답 끝에 다음 JSON 형식으로 데이터를 추출하세요:
```json
{"quote_data": {"trade_mode": "export", "shipping_type": "ocean", "load_type": "FCL", "pol": "KRPUS", "pod": "NLRTM", "container_type": "4HDC", "etd": "2026-02-01"}}
```
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
# GEMINI API FUNCTIONS
# ============================================================

def get_gemini_model():
    """Gemini 모델 인스턴스 반환"""
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        return model
    except Exception as e:
        logger.error(f"Error creating Gemini model: {e}")
        return None


def chat_with_gemini(session_id: str, user_message: str) -> Dict[str, Any]:
    """
    Gemini와 대화
    
    Args:
        session_id: 세션 ID
        user_message: 사용자 메시지
    
    Returns:
        {
            "success": bool,
            "message": str,
            "quote_data": Optional[dict]  # 추출된 Quote 데이터
        }
    """
    if not GEMINI_AVAILABLE:
        return {
            "success": False,
            "message": "AI 서비스를 사용할 수 없습니다. GEMINI_API_KEY를 확인해주세요.",
            "quote_data": None
        }
    
    try:
        model = get_gemini_model()
        if not model:
            return {
                "success": False,
                "message": "AI 모델을 로드할 수 없습니다.",
                "quote_data": None
            }
        
        # 대화 이력 가져오기
        history = conversation_manager.get_history(session_id)
        
        # 채팅 시작
        chat = model.start_chat(history=history)
        
        # 메시지 전송
        response = chat.send_message(user_message)
        ai_message = response.text
        
        # 대화 이력 저장
        conversation_manager.add_message(session_id, "user", user_message)
        conversation_manager.add_message(session_id, "model", ai_message)
        
        # Quote 데이터 추출 시도
        quote_data = extract_quote_data(ai_message)
        
        return {
            "success": True,
            "message": ai_message,
            "quote_data": quote_data
        }
        
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return {
            "success": False,
            "message": f"AI 응답 중 오류가 발생했습니다: {str(e)}",
            "quote_data": None
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
        # JSON 블록 찾기
        import re
        json_match = re.search(r'\{"quote_data":\s*\{[^}]+\}\}', ai_message)
        
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            return data.get("quote_data")
        
        return None
        
    except Exception as e:
        logger.debug(f"Quote data extraction failed: {e}")
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
    print("=" * 50)
    print("Gemini Backend Test")
    print("=" * 50)
    print(f"Gemini Available: {GEMINI_AVAILABLE}")
    print(f"API Key: {'Set' if GEMINI_API_KEY else 'Not Set'}")
    
    if GEMINI_AVAILABLE:
        # 테스트 대화
        session_id = "test_session"
        
        test_messages = [
            "안녕하세요! 운임 조회하고 싶어요",
            "부산에서 로테르담으로 수출하려고 해요",
            "해상운송이요",
            "40피트 하이큐브 컨테이너 1개요",
            "다음달 초에 출발하면 좋겠어요"
        ]
        
        for msg in test_messages:
            print(f"\nUser: {msg}")
            result = chat_with_gemini(session_id, msg)
            print(f"AI: {result['message'][:200]}...")
            if result['quote_data']:
                print(f"Quote Data: {result['quote_data']}")
