"""
Naver News Collector

Collects Korean logistics news from Naver News API.
Requires NAVER_CLIENT_ID and NAVER_CLIENT_SECRET environment variables.
"""

import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote_plus
from .base import BaseCollector
import logging
import re
from html import unescape

logger = logging.getLogger(__name__)


# Search queries for Korean logistics news
NAVER_NEWS_QUERIES = [
    # 기존 쿼리
    '물류 파업',
    '항만 혼잡',
    '해운 운임',
    '물류 지연',
    '항공 화물',
    '공급망 위기',
    '컨테이너 부족',
    '물류 뉴스',
    '물류센터',
    '택배 파업',
    
    # 운임 및 비용
    '해상 운임',
    '항공 운임',
    '물류비 상승',
    '운송 비용',
    '유류할증료',
    
    # 주요 항로 및 요충지
    '수에즈운하',
    '파나마운하',
    '홍해 항로',
    '말라카해협',
    '북극항로',
    
    # 정책 및 규제
    '해운 정책',
    '물류 규제',
    '통관 규제',
    '수출입 규제',
    '관세 정책',
    'IMO 규제',
    '탄소중립 해운',
    
    # 주요 선사
    '머스크',
    'HMM 실적',
    'SM상선',
    '고려해운',
    '흥아해운',
    '팬오션',
    
    # 주요 항만
    '부산항',
    '인천항',
    '광양항',
    '평택항',
    '울산항',
    '싱가포르항',
    '상하이항',
    
    # 주요 공항
    '인천공항 화물',
    '김해공항 화물',
    '화물터미널',
    
    # 무역 및 통관
    '무역 동향',
    '수출 물류',
    '수입 통관',
    '통관 지연',
    'FTA 활용',
    '원산지 증명',
]


class NaverNewsCollector(BaseCollector):
    """
    Collects Korean news from Naver News Search API.
    
    Uses predefined logistics-related search queries in Korean.
    Requires Naver API credentials in environment variables.
    """
    
    NAVER_API_URL = "https://openapi.naver.com/v1/search/news.json"
    
    def __init__(self, queries: List[str] = None, max_per_query: int = 10):
        """
        Initialize Naver News collector.
        
        Args:
            queries: List of search queries (uses defaults if None)
            max_per_query: Maximum articles to collect per query
        """
        super().__init__(name='NaverNewsCollector', news_type='KR')
        self.queries = queries or NAVER_NEWS_QUERIES
        self.max_per_query = max_per_query
        
        # Get API credentials from environment
        self.client_id = os.getenv('NAVER_CLIENT_ID')
        self.client_secret = os.getenv('NAVER_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            self.logger.warning("Naver API credentials not found. Set NAVER_CLIENT_ID and NAVER_CLIENT_SECRET.")
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect news from Naver News for all configured queries.
        
        Returns:
            List of news article dictionaries
        """
        if not self.client_id or not self.client_secret:
            self.logger.warning("Naver API credentials not configured, skipping collection")
            return []
        
        all_articles = []
        seen_urls = set()
        
        for query in self.queries:
            try:
                articles = self._search_news(query)
                
                # Deduplicate within this collection run
                for article in articles:
                    # Normalize URL for deduplication
                    normalized_url = self._normalize_url(article['url'])
                    if normalized_url not in seen_urls:
                        seen_urls.add(normalized_url)
                        all_articles.append(article)
                
            except Exception as e:
                self.logger.error(f"Error searching Naver News for '{query}': {e}")
        
        self.logger.info(f"Collected {len(all_articles)} articles from Naver News")
        return all_articles
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        # Remove tracking parameters
        if '?' in url:
            base_url = url.split('?')[0]
            return base_url
        return url
    
    def _search_news(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Naver News for a specific query.
        
        Args:
            query: Search query string (Korean)
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
        try:
            headers = {
                'X-Naver-Client-Id': self.client_id,
                'X-Naver-Client-Secret': self.client_secret,
            }
            
            params = {
                'query': query,
                'display': self.max_per_query,
                'start': 1,
                'sort': 'date',  # Sort by date
            }
            
            response = requests.get(
                self.NAVER_API_URL,
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"Naver API error: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            items = data.get('items', [])
            
            for item in items:
                try:
                    article = self._parse_item(item)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Error parsing Naver News item: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch Naver News for '{query}': {e}")
        
        return articles
    
    def _parse_item(self, item: Dict) -> Optional[Dict[str, Any]]:
        """
        Parse a Naver News API item.
        
        Args:
            item: Naver API response item
            
        Returns:
            Article dictionary or None
        """
        # Get URL
        url = item.get('link') or item.get('originallink')
        if not url:
            return None
        
        # Get and clean title (remove HTML tags)
        title = item.get('title', '')
        title = self._clean_html(title)
        if not title:
            return None
        
        # Get and clean description
        description = item.get('description', '')
        description = self._clean_html(description)
        description = self.truncate_summary(description, 500)
        
        # Parse published date (format: "Tue, 31 Dec 2024 10:00:00 +0900")
        published_at = None
        pub_date = item.get('pubDate')
        if pub_date:
            published_at = self.parse_datetime(pub_date)
        
        return {
            'title': title,
            'content_summary': description,
            'source_name': 'Naver News',
            'url': url,
            'published_at_utc': published_at,
            'news_type': 'KR',
        }
    
    def _clean_html(self, text: str) -> str:
        """
        Clean HTML tags and entities from text.
        
        Args:
            text: Raw HTML text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Unescape HTML entities
        text = unescape(text)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

