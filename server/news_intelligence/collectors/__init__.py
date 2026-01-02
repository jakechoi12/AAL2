"""
News Collectors Module

Provides unified interface for collecting news from multiple sources:
- RSS feeds (international and Korean logistics news)
- GDELT (global event database)
- Google News (search-based)
- Naver News (Korean search-based)
"""

from .base import BaseCollector
from .rss_collector import RSSCollector
from .gdelt_collector import GDELTCollector
from .google_news_collector import GoogleNewsCollector
from .naver_news_collector import NaverNewsCollector
from .manager import NewsCollectorManager

__all__ = [
    'BaseCollector',
    'RSSCollector',
    'GDELTCollector',
    'GoogleNewsCollector',
    'NaverNewsCollector',
    'NewsCollectorManager'
]

