"""
Base Collector Abstract Class
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


# ===== 불필요한 기사 필터링 패턴 (v2.4) =====
# 물류/무역/경제와 무관한 기사를 자동으로 제거

IRRELEVANT_ARTICLE_PATTERNS = [
    # 결혼/혼인 관련
    r'\[화촉\]',
    r'결혼식',
    r'\bwedding\b',
    r'화촉을 밝히',
    r'약혼식',
    r'결혼을 발표',
    
    # 부동산 광고
    r'견본주택',
    r'분양\s*(일정|상담|문의|안내)',
    r'입주자\s*모집',
    r'리버블시티',
    r'자이\s*(아파트|타워)',
    r'아파트.*광고',
    r'모델하우스',
    r'청약\s*(일정|접수)',
    
    # 여권/비자 랭킹
    r'여권.*순위',
    r'여권.*\d+위',
    r'비자\s*면제.*국가',
    r'passport.*rank',
    r'passport.*power',
    r'henley.*passport',
    
    # 기타 광고/프로모션
    r'\[.*광고.*\]',
    r'\[.*프로모션.*\]',
    r'\[.*이벤트.*\]',
    r'\[.*협찬.*\]',
    r'\[AD\]',
    r'\[PR\]',
    r'\[스폰서\]',
    
    # 자격시험/교육 일정
    r'자격시험.*일정',
    r'특례교육.*일정',
    r'시험.*공고',
    r'합격자\s*발표',
    r'원서\s*접수',
    
    # 동정 기사
    r'\[동정\]',
    r'방문.*마치고.*귀국',
    r'출장.*귀국',
    r'예방.*했다',
    r'만찬.*참석',
    
    # 연예인/사건사고 (물류 무관)
    r'전신.*화상',
    r'휠체어.*귀국',
    r'응급\s*후송',
    r'사망\s*사고',
    
    # 스포츠/엔터테인먼트
    r'월드컵.*경기',
    r'올림픽.*경기',
    r'챔피언십.*결과',
    r'콘서트\s*일정',
    r'팬미팅',
    
    # 날씨 예보 (일반적인 것만)
    r'내일\s*날씨',
    r'주간\s*날씨',
    r'오늘의\s*운세',
]

# 컴파일된 패턴 (성능 최적화)
COMPILED_IRRELEVANT_PATTERNS = [re.compile(p, re.IGNORECASE) for p in IRRELEVANT_ARTICLE_PATTERNS]


class ArticleFilter:
    """
    불필요한 기사를 필터링하는 클래스 (v2.4)
    
    물류/무역/경제와 무관한 기사를 자동으로 제거합니다.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.filtered_count = 0
    
    def should_filter(self, title: str, summary: str = '') -> bool:
        """
        기사가 필터링 대상인지 확인합니다.
        
        Args:
            title: 기사 제목
            summary: 기사 요약
            
        Returns:
            True if article should be filtered out, False otherwise
        """
        text = f"{title} {summary}".strip()
        
        for pattern in COMPILED_IRRELEVANT_PATTERNS:
            if pattern.search(text):
                return True
        
        return False
    
    def filter_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        기사 목록에서 불필요한 기사를 제거합니다.
        
        Args:
            articles: 필터링할 기사 목록
            
        Returns:
            필터링된 기사 목록
        """
        filtered = []
        removed_count = 0
        
        for article in articles:
            title = article.get('title', '')
            summary = article.get('content_summary', '')
            
            if self.should_filter(title, summary):
                removed_count += 1
                self.logger.debug(f"Filtered out article: {title[:50]}...")
            else:
                filtered.append(article)
        
        if removed_count > 0:
            self.logger.info(f"Filtered out {removed_count} irrelevant articles")
        
        self.filtered_count += removed_count
        return filtered
    
    def get_filtered_count(self) -> int:
        """필터링된 기사 수 반환"""
        return self.filtered_count
    
    def reset_count(self):
        """필터링 카운트 초기화"""
        self.filtered_count = 0


# Global filter instance
article_filter = ArticleFilter()


class BaseCollector(ABC):
    """
    Abstract base class for all news collectors.
    
    All collectors must implement the collect() method which returns
    a list of news article dictionaries.
    """
    
    def __init__(self, name: str, news_type: str = 'GLOBAL'):
        """
        Initialize collector.
        
        Args:
            name: Collector name for logging
            news_type: 'KR' for Korean news, 'GLOBAL' for international
        """
        self.name = name
        self.news_type = news_type
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect news articles from the source.
        
        Returns:
            List of dictionaries with the following structure:
            {
                'title': str,
                'content_summary': str (optional),
                'source_name': str,
                'url': str (unique identifier),
                'published_at_utc': datetime (optional),
                'news_type': str ('KR' or 'GLOBAL'),
                'country_tags': List[str] (optional),
                # GDELT-specific (optional):
                'goldstein_scale': float,
                'avg_tone': float,
                'num_mentions': int,
                'num_sources': int,
                'num_articles': int,
            }
        """
        pass
    
    def parse_datetime(self, dt_str: str, formats: List[str] = None) -> Optional[datetime]:
        """
        Parse datetime string to UTC datetime object.
        
        Args:
            dt_str: Datetime string to parse
            formats: List of datetime formats to try
            
        Returns:
            datetime object in UTC or None if parsing fails
        """
        if not dt_str:
            return None
            
        if formats is None:
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',  # RFC 822
                '%a, %d %b %Y %H:%M:%S GMT',  # RFC 822 GMT
                '%Y-%m-%dT%H:%M:%S%z',  # ISO 8601
                '%Y-%m-%dT%H:%M:%SZ',   # ISO 8601 UTC
                '%Y-%m-%d %H:%M:%S',    # Common format
                '%Y-%m-%d',             # Date only
            ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(dt_str.strip(), fmt)
                # Convert to UTC if timezone-aware
                if dt.tzinfo is not None:
                    return dt.astimezone(timezone.utc).replace(tzinfo=None)
                # Assume UTC if no timezone
                return dt
            except (ValueError, AttributeError):
                continue
        
        self.logger.warning(f"Could not parse datetime: {dt_str}")
        return None
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def truncate_summary(self, text: str, max_length: int = 500) -> str:
        """
        Truncate text to maximum length while preserving word boundaries.
        
        Args:
            text: Text to truncate
            max_length: Maximum character length
            
        Returns:
            Truncated text
        """
        if not text or len(text) <= max_length:
            return text
        
        # Find last space before max_length
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated + '...'

