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
    # ===== Supply chain disruptions =====
    'supply chain disruption',
    'port strike',
    'shipping delay',
    'freight congestion',
  
    # ===== Logistics news =====
    'logistics news',
    'freight rates',
    'container shipping',
    'air cargo',
  
    # ===== Crisis events =====
    'port closure',
    'shipping crisis',
    'supply chain crisis',
  
    # ===== Freight rates and costs =====
    'ocean freight rates',
    'air freight rates',
    'shipping costs increase',
    'logistics costs',
  
    # ===== Major shipping routes and chokepoints =====
    'Suez Canal shipping',
    'Panama Canal transit',
    'Red Sea shipping',
    'Strait of Malacca',
    'Cape of Good Hope route',
    'Bab el-Mandeb strait',
    'Strait of Hormuz shipping',
    'Bosphorus strait shipping',
    'Gibraltar strait shipping',
    'Northern Sea Route',
  
    # ===== Policy and regulations =====
    'shipping regulations',
    'trade policy',
    'customs regulations',
    'import tariffs',
    'export restrictions',
    'IMO regulations',
  
    # ===== Major carriers (Ocean) =====
    'Maersk shipping',
    'MSC Mediterranean',
    'CMA CGM',
    'COSCO shipping',
    'Evergreen Marine',
    'Hapag-Lloyd',
    'ONE Ocean Network Express',
    'Yang Ming shipping',
    'HMM Hyundai Merchant',
    'ZIM shipping',
    'PIL Pacific International Lines',
    'Wan Hai Lines',
  
    # ===== Major carriers (Air) =====
    'FedEx cargo',
    'UPS air freight',
    'DHL Express',
    'Cargolux',
    'Korean Air Cargo',
    'Cathay Pacific Cargo',
    'Emirates SkyCargo',
    'Qatar Airways Cargo',
    'Singapore Airlines Cargo',
    'Lufthansa Cargo',
  
    # ===== Major ports (Asia) =====
    'Port of Shanghai',
    'Port of Singapore',
    'Port of Busan',
    'Port of Ningbo',
    'Port of Shenzhen',
    'Port of Guangzhou',
    'Port of Hong Kong',
    'Port of Qingdao',
    'Port of Tianjin',
    'Port of Kaohsiung',
    'Port of Tanjung Pelepas',
    'Port of Laem Chabang',
    'Port of Ho Chi Minh',
    'Port of Mumbai',
    'Port of Colombo',
  
    # ===== Major ports (Europe) =====
    'Port of Rotterdam',
    'Port of Antwerp',
    'Port of Hamburg',
    'Port of Bremerhaven',
    'Port of Valencia',
    'Port of Barcelona',
    'Port of Piraeus',
    'Port of Felixstowe',
    'Port of Le Havre',
    'Port of Genoa',
  
    # ===== Major ports (Americas) =====
    'Port of Los Angeles',
    'Port of Long Beach',
    'Port of New York',
    'Port of Savannah',
    'Port of Houston',
    'Port of Seattle',
    'Port of Oakland',
    'Port of Vancouver',
    'Port of Santos',
    'Port of Colon Panama',
    'Port of Manzanillo',
  
    # ===== Major ports (Middle East/Africa) =====
    'Port of Jebel Ali',
    'Port of Salalah',
    'Port of Jeddah',
    'Port of Port Said',
    'Port of Durban',
    'Port of Tangier Med',
  
    # ===== Major airports (cargo) =====
    'Hong Kong airport cargo',
    'Memphis airport cargo',
    'Incheon airport cargo',
    'Shanghai Pudong cargo',
    'Anchorage airport cargo',
    'Dubai airport cargo',
    'Louisville airport UPS',
    'Singapore Changi cargo',
    'Tokyo Narita cargo',
    'Frankfurt airport cargo',
    'Paris CDG cargo',
    'Amsterdam Schiphol cargo',
    'London Heathrow cargo',
    'Los Angeles LAX cargo',
    'Miami airport cargo',
    'Taipei Taoyuan cargo',
    'Guangzhou Baiyun cargo',
  
    # ===== Trade and customs =====
    'global trade news',
    'customs clearance',
    'trade disruption',
    'export logistics',
    'import delays',
  
    # ===== Geopolitical risks =====
    'geopolitical risk supply chain',
    'Ukraine war logistics',
    'Taiwan strait shipping',
    'Middle East shipping disruption',
    'sanctions shipping',
    'Russia sanctions logistics',
    'China Taiwan conflict shipping',
    'South China Sea shipping',
    'Iran sanctions shipping',
    'North Korea shipping ban',
    'Houthi attacks shipping',
    'Yemen crisis shipping',
    'Israel Gaza shipping',
    'US China trade war',
    'EU sanctions Russia',
  
    # ===== Latest trends =====
    'nearshoring supply chain',
    'reshoring manufacturing',
    'EV battery supply chain',
    'semiconductor logistics',
    'green shipping',
    'decarbonization shipping',
    'alternative fuels shipping',
    'ammonia fuel shipping',
    'methanol fuel shipping',
    'LNG powered ships',
    'digital supply chain',
    'blockchain logistics',
    'AI logistics',
    'autonomous shipping',
    'drone delivery',
    'cold chain logistics',
    'pharmaceutical logistics',
  
    # ===== Major manufacturers (Semiconductor) =====
    'TSMC supply chain',
    'Samsung semiconductor',
    'Intel chip supply',
    'SK Hynix logistics',
    'Micron supply chain',
    'NVIDIA chip shortage',
    'AMD supply chain',
    'Qualcomm logistics',
    'ASML supply chain',
  
    # ===== Major manufacturers (Automotive) =====
    'Tesla supply chain',
    'Toyota logistics',
    'Volkswagen supply chain',
    'BYD supply chain',
    'Hyundai logistics',
    'Ford supply chain',
    'GM supply chain',
    'BMW logistics',
    'Mercedes supply chain',
  
    # ===== Major manufacturers (EV Battery) =====
    'CATL supply chain',
    'LG Energy Solution',
    'Samsung SDI logistics',
    'Panasonic battery supply',
    'SK On supply chain',
    'BYD battery logistics',
  
    # ===== Major manufacturers (Electronics) =====
    'Apple supply chain',
    'Foxconn logistics',
    'Samsung Electronics supply',
    'Huawei supply chain',
    'Sony logistics',
    'LG Electronics supply',
  
    # ===== Climate/Weather =====
    'weather shipping disruption',
    'drought Panama Canal',
    'hurricane port closure',
    'typhoon shipping delay',
    'flooding port disruption',
    'extreme weather logistics',
  
    # ===== Labor issues =====
    'dockworkers strike',
    'truckers strike',
    'warehouse workers strike',
    'labor shortage logistics',
    'port workers union',
    'ILA strike',
    'ILWU strike',
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

