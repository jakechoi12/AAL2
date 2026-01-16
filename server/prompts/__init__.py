"""
AAL AI Assistant - Dynamic Prompt System
상황별 프롬프트 분리 및 동적 로딩
"""

from .base import BASE_PROMPT
from .rate import RATE_PROMPT, RATE_TOOLS
from .quote import QUOTE_PROMPT, QUOTE_TOOLS
from .bidding import BIDDING_PROMPT, BIDDING_TOOLS
from .market import MARKET_PROMPT, MARKET_TOOLS
from .intent import classify_intent, get_dynamic_prompt, get_tools_for_intents

__all__ = [
    'BASE_PROMPT',
    'RATE_PROMPT', 'RATE_TOOLS',
    'QUOTE_PROMPT', 'QUOTE_TOOLS',
    'BIDDING_PROMPT', 'BIDDING_TOOLS',
    'MARKET_PROMPT', 'MARKET_TOOLS',
    'classify_intent',
    'get_dynamic_prompt',
    'get_tools_for_intents'
]
