"""
Google News Collector

Collects logistics-related news from Google News RSS feeds.
Uses search-based RSS feeds to find relevant news.
"""

import feedparser
from typing import List, Dict, Any
from urllib.parse import quote_plus
from .base import BaseCollector
import logging

logger = logging.getLogger(__name__)


# Search queries for logistics news
GOOGLE_NEWS_QUERIES = [
    # Supply chain disruptions
    'supply chain disruption',
    'port strike',
    'shipping delay',
    'freight congestion',
    
    # Logistics news
    'logistics news',
    'freight rates',
    'container shipping',
    'air cargo',
    
    # Crisis events
    'port closure',
    'shipping crisis',
    'supply chain crisis',
    
    # Freight rates and costs
    'ocean freight rates',
    'air freight rates',
    'shipping costs increase',
    'logistics costs',
    
    # Major shipping routes and chokepoints
    'Suez Canal shipping',
    'Panama Canal transit',
    'Red Sea shipping',
    'Strait of Malacca',
    'Cape of Good Hope route',
    
    # Policy and regulations
    'shipping regulations',
    'trade policy',
    'customs regulations',
    'import tariffs',
    'export restrictions',
    'IMO regulations',
    
    # Major carriers
    'Maersk shipping',
    'MSC Mediterranean',
    'CMA CGM',
    'COSCO shipping',
    'Evergreen Marine',
    'Hapag-Lloyd',
    
    # Major ports
    'Port of Shanghai',
    'Port of Singapore',
    'Port of Rotterdam',
    'Port of Los Angeles',
    'Port of Busan',
    
    # Major airports (cargo)
    'Hong Kong airport cargo',
    'Memphis airport cargo',
    'Incheon airport cargo',
    
    # Trade and customs
    'global trade news',
    'customs clearance',
    'trade disruption',
    'export logistics',
    'import delays',
]


class GoogleNewsCollector(BaseCollector):
    """
    Collects news from Google News using RSS search feeds.
    
    Uses predefined logistics-related search queries to find relevant news.
    """
    
    GOOGLE_NEWS_RSS_BASE = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    
    def __init__(self, queries: List[str] = None, max_per_query: int = 10):
        """
        Initialize Google News collector.
        
        Args:
            queries: List of search queries (uses defaults if None)
            max_per_query: Maximum articles to collect per query
        """
        super().__init__(name='GoogleNewsCollector', news_type='GLOBAL')
        self.queries = queries or GOOGLE_NEWS_QUERIES
        self.max_per_query = max_per_query
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect news from Google News for all configured queries.
        
        Returns:
            List of news article dictionaries
        """
        all_articles = []
        seen_urls = set()
        
        for query in self.queries:
            try:
                articles = self._search_news(query)
                
                # Deduplicate within this collection run
                for article in articles:
                    if article['url'] not in seen_urls:
                        seen_urls.add(article['url'])
                        all_articles.append(article)
                        
                        if len([a for a in all_articles if a.get('_query') == query]) >= self.max_per_query:
                            break
                
            except Exception as e:
                self.logger.error(f"Error searching Google News for '{query}': {e}")
        
        # Remove query tracking field
        for article in all_articles:
            article.pop('_query', None)
        
        self.logger.info(f"Collected {len(all_articles)} articles from Google News")
        return all_articles
    
    def _search_news(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Google News for a specific query.
        
        Args:
            query: Search query string
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
        try:
            # Build RSS URL
            encoded_query = quote_plus(query)
            url = self.GOOGLE_NEWS_RSS_BASE.format(query=encoded_query)
            
            # Parse feed
            feed = feedparser.parse(url)
            
            if feed.bozo and not feed.entries:
                self.logger.warning(f"Feed parsing error for query '{query}': {feed.bozo_exception}")
                return []
            
            for entry in feed.entries[:self.max_per_query]:
                try:
                    article = self._parse_entry(entry, query)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Error parsing Google News entry: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch Google News for '{query}': {e}")
        
        return articles
    
    def _parse_entry(self, entry, query: str) -> Dict[str, Any]:
        """
        Parse a Google News RSS entry.
        
        Args:
            entry: feedparser entry object
            query: Original search query
            
        Returns:
            Article dictionary or None
        """
        # Get URL (Google News redirects, try to get original)
        url = getattr(entry, 'link', None)
        if not url:
            return None
        
        # Get title
        title = getattr(entry, 'title', None)
        if not title:
            return None
        title = self.clean_text(title)
        
        # Get summary/description
        summary = ''
        if hasattr(entry, 'summary'):
            summary = self.clean_text(entry.summary)
        elif hasattr(entry, 'description'):
            summary = self.clean_text(entry.description)
        
        summary = self.truncate_summary(summary, 500)
        
        # Parse published date
        published_at = None
        if hasattr(entry, 'published'):
            published_at = self.parse_datetime(entry.published)
        elif hasattr(entry, 'updated'):
            published_at = self.parse_datetime(entry.updated)
        
        # Extract source name from title (Google News format: "Title - Source")
        source_name = 'Google News'
        if ' - ' in title:
            parts = title.rsplit(' - ', 1)
            if len(parts) == 2:
                title = parts[0].strip()
                source_name = parts[1].strip()
        
        return {
            'title': title,
            'content_summary': summary,
            'source_name': source_name,
            'url': url,
            'published_at_utc': published_at,
            'news_type': 'GLOBAL',
            '_query': query,  # Temporary field for deduplication
        }

