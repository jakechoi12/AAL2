"""
Intent 분류기 및 Dynamic Prompt 로더
사용자 메시지를 분석하여 필요한 프롬프트와 Tool을 선별
"""

import re
from typing import List, Set

from .base import BASE_PROMPT
from .rate import RATE_PROMPT, RATE_TOOLS
from .quote import QUOTE_PROMPT, QUOTE_TOOLS
from .bidding import BIDDING_PROMPT, BIDDING_TOOLS
from .market import MARKET_PROMPT, MARKET_TOOLS


# Intent 분류를 위한 키워드 정의
INTENT_KEYWORDS = {
    "rate": [
        "운임", "요금", "얼마", "피트", "컨테이너", "20dc", "40dc", "40hc",
        "해상", "항공", "육상", "fcl", "lcl",
        "부산", "인천", "로테르담", "상하이", "싱가포르", "LA",
        "선적", "화물", "배송비", "freight", "rate"
    ],
    "quote": [
        "견적", "요청", "신청", "문의", "quote",
        "etd", "eta", "출발", "도착", "예정",
        "고객", "회사", "담당자", "이메일", "전화",
        "수입", "수출", "import", "export",
        "incoterms", "fob", "cif", "exw", "dap",
        # 비딩 진행 관련 (대화형 견적 요청)
        "비딩 진행", "비딩 신청", "대화로", "직접 신청", "바로 신청",
        "비딩하고싶", "비딩할래", "비딩해줘", "진행하고싶"
    ],
    "bidding": [
        "비딩", "입찰", "낙찰", "마감", "bid",
        "포워더", "forwarder", "제출", "선정", "진행"
    ],
    "market": [
        "지수", "bdi", "scfi", "ccfi", "index",
        "뉴스", "news", "소식",
        "환율", "exchange", "달러", "유로", "엔",
        "경고", "alert", "공급망", "supply chain"
    ]
}


def classify_intent(message: str) -> List[str]:
    """
    사용자 메시지에서 intent를 분류합니다.
    
    Args:
        message: 사용자 메시지
        
    Returns:
        감지된 intent 목록 (항상 "base" 포함)
    """
    intents = ["base"]  # 기본 프롬프트는 항상 포함
    message_lower = message.lower()
    
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in message_lower:
                if intent not in intents:
                    intents.append(intent)
                break  # 하나라도 매칭되면 해당 intent 추가
    
    # 아무 intent도 감지되지 않으면 rate 추가 (기본 행동)
    # 단순 인사말 등은 base만으로 처리
    if len(intents) == 1:
        # 인사말 패턴 체크
        greeting_patterns = [
            r'^안녕', r'^hello', r'^hi\b', r'^뭐해', r'^ㅎㅇ',
            r'도움', r'할 수 있', r'뭘 해', r'무엇을'
        ]
        is_greeting = any(re.search(p, message_lower) for p in greeting_patterns)
        
        if not is_greeting:
            # 인사말이 아니면 운임 조회 관련으로 추정
            intents.append("rate")
    
    return intents


def get_dynamic_prompt(intents: List[str]) -> str:
    """
    감지된 intent에 따라 동적으로 System Prompt를 조합합니다.
    
    Args:
        intents: 감지된 intent 목록
        
    Returns:
        조합된 System Prompt
    """
    prompt_parts = [BASE_PROMPT]
    
    if "rate" in intents:
        prompt_parts.append(RATE_PROMPT)
    
    if "quote" in intents:
        prompt_parts.append(QUOTE_PROMPT)
    
    if "bidding" in intents:
        prompt_parts.append(BIDDING_PROMPT)
    
    if "market" in intents:
        prompt_parts.append(MARKET_PROMPT)
    
    return "\n\n".join(prompt_parts)


def get_tools_for_intents(intents: List[str]) -> Set[str]:
    """
    감지된 intent에 따라 필요한 Tool 목록을 반환합니다.
    
    Args:
        intents: 감지된 intent 목록
        
    Returns:
        필요한 Tool 이름 집합
    """
    tools = set()
    
    # 기본 Tool (항상 포함)
    base_tools = ["get_port_info", "navigate_to_page"]
    tools.update(base_tools)
    
    if "rate" in intents:
        tools.update(RATE_TOOLS)
    
    if "quote" in intents:
        tools.update(QUOTE_TOOLS)
    
    if "bidding" in intents:
        tools.update(BIDDING_TOOLS)
    
    if "market" in intents:
        tools.update(MARKET_TOOLS)
    
    return tools


def get_intent_description(intents: List[str]) -> str:
    """
    감지된 intent를 설명하는 문자열을 반환합니다.
    (디버깅/로깅용)
    """
    intent_names = {
        "base": "기본",
        "rate": "운임조회",
        "quote": "견적요청",
        "bidding": "비딩관리",
        "market": "시장정보"
    }
    
    return " + ".join(intent_names.get(i, i) for i in intents)
