"""
Base Collector Abstract Class
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


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

