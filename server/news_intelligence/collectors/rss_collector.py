"""
RSS Feed Collector

Collects news from logistics RSS feeds:
- International: FreightWaves, The Loadstar, Supply Chain Dive, etc.
- Korean: 물류신문, 해운신문, 카고뉴스
"""

import feedparser
from typing import List, Dict, Any
from datetime import datetime, timezone
from .base import BaseCollector
import logging

logger = logging.getLogger(__name__)


# RSS Feed configurations
RSS_FEEDS = {
    # International logistics news
    'global': [
        {
            'name': 'The Loadstar',
            'url': 'https://theloadstar.com/feed/',
            'type': 'GLOBAL'
        },
        {
            'name': 'FreightWaves',
            'url': 'https://www.freightwaves.com/feed',
            'type': 'GLOBAL'
        },
        {
            'name': 'Supply Chain Dive',
            'url': 'https://www.supplychaindive.com/feeds/news/',
            'type': 'GLOBAL'
        },
        {
            'name': 'Splash247',
            'url': 'https://splash247.com/feed/',
            'type': 'GLOBAL'
        },
        {
            'name': 'Air Cargo Week',
            'url': 'https://aircargoweek.com/feed/',
            'type': 'GLOBAL'
        },
        {
            'name': 'Supply Chain 247',
            'url': 'https://www.supplychain247.com/rss/all/feeds',
            'type': 'GLOBAL'
        },
    ],
    # Korean logistics news
    'korean': [
        {
            'name': '물류신문',
            'url': 'https://www.klnews.co.kr/rss/allArticle.xml',
            'type': 'KR'
        },
        {
            'name': '해운신문',
            'url': 'https://www.maritimepress.co.kr/rss/allArticle.xml',
            'type': 'KR'
        },
        {
            'name': '카고뉴스',
            'url': 'https://www.cargonews.co.kr/rss/allArticle.xml',
            'type': 'KR'
        },
    ]
}


class RSSCollector(BaseCollector):
    """
    Collects news from RSS feeds.
    
    Supports both international and Korean logistics news sources.
    """
    
    def __init__(self, feed_type: str = 'all'):
        """
        Initialize RSS collector.
        
        Args:
            feed_type: 'global', 'korean', or 'all' (default)
        """
        super().__init__(name='RSSCollector')
        self.feed_type = feed_type
        self.feeds = self._get_feeds()
    
    def _get_feeds(self) -> List[Dict[str, str]]:
        """Get feed configurations based on feed_type"""
        if self.feed_type == 'global':
            return RSS_FEEDS['global']
        elif self.feed_type == 'korean':
            return RSS_FEEDS['korean']
        else:  # all
            return RSS_FEEDS['global'] + RSS_FEEDS['korean']
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect news from all configured RSS feeds.
        
        Returns:
            List of news article dictionaries
        """
        all_articles = []
        
        for feed_config in self.feeds:
            try:
                articles = self._collect_from_feed(feed_config)
                all_articles.extend(articles)
                self.logger.info(f"Collected {len(articles)} articles from {feed_config['name']}")
            except Exception as e:
                self.logger.error(f"Error collecting from {feed_config['name']}: {e}")
        
        return all_articles
    
    def _collect_from_feed(self, feed_config: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Collect articles from a single RSS feed.
        
        Args:
            feed_config: Feed configuration dictionary
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
        try:
            # Parse the feed
            feed = feedparser.parse(feed_config['url'])
            
            if feed.bozo and not feed.entries:
                self.logger.warning(f"Feed parsing error for {feed_config['name']}: {feed.bozo_exception}")
                return []
            
            for entry in feed.entries:
                try:
                    article = self._parse_entry(entry, feed_config)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Error parsing entry from {feed_config['name']}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch feed {feed_config['url']}: {e}")
        
        return articles
    
    def _parse_entry(self, entry, feed_config: Dict[str, str]) -> Dict[str, Any]:
        """
        Parse a single RSS entry into article dictionary.
        
        Args:
            entry: feedparser entry object
            feed_config: Feed configuration
            
        Returns:
            Article dictionary or None
        """
        # Get URL (required)
        url = getattr(entry, 'link', None)
        if not url:
            return None
        
        # Get title (required)
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
        
        return {
            'title': title,
            'content_summary': summary,
            'source_name': feed_config['name'],
            'url': url,
            'published_at_utc': published_at,
            'news_type': feed_config['type'],
        }


def get_rss_feeds_info() -> Dict[str, List[Dict]]:
    """Get information about configured RSS feeds"""
    return RSS_FEEDS

