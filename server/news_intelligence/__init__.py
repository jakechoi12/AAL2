# News Intelligence Module
# This module provides logistics news collection, analysis, and API services

from .models import NewsArticle, CollectionLog, Base
from .collectors import NewsCollectorManager
from .analyzer import NewsAnalyzer
from .api import news_bp

__all__ = [
    'NewsArticle',
    'CollectionLog', 
    'Base',
    'NewsCollectorManager',
    'NewsAnalyzer',
    'news_bp'
]

