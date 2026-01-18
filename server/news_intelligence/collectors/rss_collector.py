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
    # ===== 해외 물류/공급망 뉴스 =====
    'global_logistics': [
        {'name': 'The Loadstar', 'url': 'https://theloadstar.com/feed/', 'type': 'GLOBAL'},
        {'name': 'FreightWaves', 'url': 'https://www.freightwaves.com/feed', 'type': 'GLOBAL'},
        {'name': 'Supply Chain Dive', 'url': 'https://www.supplychaindive.com/feeds/news/', 'type': 'GLOBAL'},
        {'name': 'Splash247', 'url': 'https://splash247.com/feed/', 'type': 'GLOBAL'},
        {'name': 'Air Cargo Week', 'url': 'https://aircargoweek.com/feed/', 'type': 'GLOBAL'},
        {'name': 'Supply Chain 247', 'url': 'https://www.supplychain247.com/rss/all/feeds', 'type': 'GLOBAL'},
        {'name': 'Logistics Management', 'url': 'https://www.logisticsmgmt.com/rss/news', 'type': 'GLOBAL'},
        {'name': 'DC Velocity', 'url': 'https://www.dcvelocity.com/rss/news', 'type': 'GLOBAL'},
        {'name': 'American Shipper', 'url': 'https://www.freightwaves.com/american-shipper/feed', 'type': 'GLOBAL'},
        {'name': 'Supply Chain Brain', 'url': 'https://www.supplychainbrain.com/rss/articles', 'type': 'GLOBAL'},
        {'name': 'Material Handling & Logistics', 'url': 'https://www.mhlnews.com/rss', 'type': 'GLOBAL'},
        {'name': 'Global Trade Magazine', 'url': 'https://www.globaltrademag.com/feed/', 'type': 'GLOBAL'},
        {'name': 'Transport Topics', 'url': 'https://www.ttnews.com/rss/all', 'type': 'GLOBAL'},
        {'name': 'Seatrade Maritime', 'url': 'https://www.seatrade-maritime.com/rss.xml', 'type': 'GLOBAL'},
        {'name': 'Hellenic Shipping News', 'url': 'https://www.hellenicshippingnews.com/feed/', 'type': 'GLOBAL'},
        {'name': 'Port Technology', 'url': 'https://www.porttechnology.org/feed/', 'type': 'GLOBAL'},
        {'name': 'Container News', 'url': 'https://container-news.com/feed/', 'type': 'GLOBAL'},
    ],
    
    # ===== 해외 경제/금융 뉴스 =====
    'global_economy': [
        {'name': 'Reuters Business', 'url': 'https://feeds.reuters.com/reuters/businessNews', 'type': 'GLOBAL'},
        {'name': 'Reuters Markets', 'url': 'https://feeds.reuters.com/reuters/marketsNews', 'type': 'GLOBAL'},
        {'name': 'CNBC World', 'url': 'https://www.cnbc.com/id/100727362/device/rss/rss.html', 'type': 'GLOBAL'},
        {'name': 'CNBC Finance', 'url': 'https://www.cnbc.com/id/10000664/device/rss/rss.html', 'type': 'GLOBAL'},
        {'name': 'MarketWatch', 'url': 'https://feeds.marketwatch.com/marketwatch/topstories', 'type': 'GLOBAL'},
        {'name': 'Business Insider', 'url': 'https://www.businessinsider.com/rss', 'type': 'GLOBAL'},
        {'name': 'Forbes', 'url': 'https://www.forbes.com/business/feed/', 'type': 'GLOBAL'},
        {'name': 'Yahoo Finance', 'url': 'https://finance.yahoo.com/news/rssindex', 'type': 'GLOBAL'},
        {'name': 'Investing.com', 'url': 'https://www.investing.com/rss/news.rss', 'type': 'GLOBAL'},
        {'name': 'Seeking Alpha', 'url': 'https://seekingalpha.com/market_currents.xml', 'type': 'GLOBAL'},
    ],
    
    # ===== 해외 무역/관세 뉴스 =====
    'global_trade': [
        {'name': 'Trade.gov', 'url': 'https://www.trade.gov/rss/feed', 'type': 'GLOBAL'},
        {'name': 'WTO News', 'url': 'https://www.wto.org/english/news_e/news_rss_e.xml', 'type': 'GLOBAL'},
        {'name': 'Customs Today', 'url': 'https://customstoday.com/feed/', 'type': 'GLOBAL'},
    ],
    
    # ===== 국내 물류 뉴스 =====
    'korean_logistics': [
        {'name': '물류신문', 'url': 'https://www.klnews.co.kr/rss/allArticle.xml', 'type': 'KR'},
        {'name': '해운신문', 'url': 'https://www.maritimepress.co.kr/rss/allArticle.xml', 'type': 'KR'},
        {'name': '카고뉴스', 'url': 'https://www.cargonews.co.kr/rss/allArticle.xml', 'type': 'KR'},
        {'name': '코리아쉬핑가제트', 'url': 'https://www.ksg.co.kr/rss/allArticle.xml', 'type': 'KR'},
        {'name': '현대해양', 'url': 'https://www.hdhy.co.kr/rss/allArticle.xml', 'type': 'KR'},
        {'name': '월간 해양한국', 'url': 'https://www.monthlymaritimekorea.com/rss/allArticle.xml', 'type': 'KR'},
        {'name': '한국해사신문', 'url': 'https://www.haesanews.com/rss/allArticle.xml', 'type': 'KR'},
        {'name': '로지스틱스매거진', 'url': 'https://www.logisticsmagazine.co.kr/rss/allArticle.xml', 'type': 'KR'},
        {'name': 'SCM인사이트', 'url': 'https://www.scminsight.co.kr/rss/allArticle.xml', 'type': 'KR'},
    ],
    
    # ===== 국내 경제/금융 뉴스 =====
    'korean_economy': [
        {'name': '매일경제', 'url': 'https://www.mk.co.kr/rss/30000001/', 'type': 'KR'},
        {'name': '한국경제', 'url': 'https://www.hankyung.com/feed/all-news', 'type': 'KR'},
        {'name': '아시아경제', 'url': 'https://www.asiae.co.kr/rss/all.xml', 'type': 'KR'},
        {'name': '이데일리', 'url': 'https://www.edaily.co.kr/rss/all.xml', 'type': 'KR'},
        {'name': '머니투데이', 'url': 'https://news.mt.co.kr/rss/all.xml', 'type': 'KR'},
        {'name': '파이낸셜뉴스', 'url': 'https://www.fnnews.com/rss/all.xml', 'type': 'KR'},
        {'name': '서울경제', 'url': 'https://www.sedaily.com/rss/all.xml', 'type': 'KR'},
        {'name': '헤럴드경제', 'url': 'https://biz.heraldcorp.com/rss/all.xml', 'type': 'KR'},
        {'name': '뉴스핌', 'url': 'https://www.newspim.com/rss/all.xml', 'type': 'KR'},
        {'name': '이투데이', 'url': 'https://www.etoday.co.kr/rss/all.xml', 'type': 'KR'},
    ],
    
    # ===== 국내 무역/산업 뉴스 =====
    'korean_trade': [
        {'name': '한국무역신문', 'url': 'https://www.weeklytrade.co.kr/rss/allArticle.xml', 'type': 'KR'},
        {'name': '전자신문', 'url': 'https://www.etnews.com/rss/all.xml', 'type': 'KR'},
        {'name': '산업일보', 'url': 'https://www.kidd.co.kr/rss/allArticle.xml', 'type': 'KR'},
        {'name': '철강금속신문', 'url': 'https://www.snmnews.com/rss/allArticle.xml', 'type': 'KR'},
        {'name': '오토타임즈', 'url': 'https://www.autotimes.co.kr/rss/allArticle.xml', 'type': 'KR'},
        {'name': '반도체뉴스', 'url': 'https://www.snnews.co.kr/rss/allArticle.xml', 'type': 'KR'},
        {'name': '전기신문', 'url': 'https://www.electimes.com/rss/allArticle.xml', 'type': 'KR'},
    ],
}

# Legacy compatibility - combined feed groups
RSS_FEEDS['global'] = (
    RSS_FEEDS['global_logistics'] + 
    RSS_FEEDS['global_economy'] + 
    RSS_FEEDS['global_trade']
)
RSS_FEEDS['korean'] = (
    RSS_FEEDS['korean_logistics'] + 
    RSS_FEEDS['korean_economy'] + 
    RSS_FEEDS['korean_trade']
)


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

