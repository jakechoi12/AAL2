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
    # ===== 기본 물류 =====
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
  
    # ===== 운임 및 비용 =====
    '해상 운임',
    '항공 운임',
    '물류비 상승',
    '운송 비용',
    '유류할증료',
    '컨테이너 운임',
    'SCFI 운임지수',
    'BDI 지수',
  
    # ===== 주요 항로 및 요충지 =====
    '수에즈운하',
    '파나마운하',
    '홍해 항로',
    '말라카해협',
    '북극항로',
    '바브엘만데브 해협',
    '호르무즈 해협',
    '대만해협 물류',
    '남중국해 항로',
    '보스포루스 해협',
    '지브롤터 해협',
    '희망봉 우회',
    '아덴만 항로',
  
    # ===== 정책 및 규제 =====
    '해운 정책',
    '물류 규제',
    '통관 규제',
    '수출입 규제',
    '관세 정책',
    'IMO 규제',
    '탄소중립 해운',
    'EU ETS 해운',
    'EU CBAM',
  
    # ===== 주요 선사 (글로벌) =====
    '머스크',
    'MSC 해운',
    'CMA CGM',
    '코스코 해운',
    '에버그린 해운',
    '하파그로이드',
    'ONE 해운',
    '양밍해운',
    'ZIM 해운',
    '완하이 해운',
  
    # ===== 주요 선사 (한국) =====
    'HMM 실적',
    'SM상선',
    '고려해운',
    '흥아해운',
    '팬오션',
    '장금상선',
    '대한해운',
    '천경해운',
    '시노코르',
    '남성해운',
  
    # ===== 주요 항만 (아시아) =====
    '부산항',
    '인천항',
    '광양항',
    '평택항',
    '울산항',
    '싱가포르항',
    '상하이항',
    '닝보항',
    '선전항',
    '광저우항',
    '홍콩항',
    '칭다오항',
    '톈진항',
    '가오슝항',
    '도쿄항',
    '요코하마항',
    '호치민항',
    '하이퐁항',
    '방콕항',
    '자카르타항',
    '콜롬보항',
    '뭄바이항',
  
    # ===== 주요 항만 (유럽) =====
    '로테르담항',
    '앤트워프항',
    '함부르크항',
    '브레머하펜항',
    '발렌시아항',
    '바르셀로나항',
    '피레우스항',
    '르아브르항',
    '펠릭스토항',
  
    # ===== 주요 항만 (미주) =====
    'LA항',
    '롱비치항',
    '뉴욕항',
    '사바나항',
    '휴스턴항',
    '시애틀항',
    '밴쿠버항',
    '산토스항',
    '콜론항',
    '만사니요항',
  
    # ===== 주요 항만 (중동/아프리카) =====
    '두바이항',
    '제벨알리항',
    '살랄라항',
    '제다항',
    '포트사이드항',
    '탕헤르항',
    '더반항',
  
    # ===== 주요 공항 (글로벌 화물) =====
    '인천공항 화물',
    '김해공항 화물',
    '화물터미널',
    '홍콩공항 화물',
    '상하이푸동 화물',
    '싱가포르창이 화물',
    '두바이공항 화물',
    '앵커리지 화물',
    '멤피스공항 페덱스',
    '루이빌공항 UPS',
    '프랑크푸르트 화물',
    '파리CDG 화물',
    '암스테르담 화물',
    '나리타공항 화물',
    '타이베이 화물',
    '광저우바이윈 화물',
  
    # ===== 무역 및 통관 =====
    '무역 동향',
    '수출 물류',
    '수입 통관',
    '통관 지연',
    'FTA 활용',
    '원산지 증명',
    '수출입 통계',
    '무역수지',
  
    # ===== 최신 이슈 =====
    '반도체 물류',
    '배터리 공급망',
    '전기차 물류',
    '친환경 선박',
    '자율운항 선박',
    '암모니아 선박',
    '메탄올 선박',
    'LNG 추진선',
    '탈탄소 해운',
    '콜드체인',
    '의약품 물류',
  
    # ===== 지정학 (글로벌) =====
    '중국 수출 규제',
    '미중 무역',
    '러시아 제재 물류',
    '북한 해운',
    '우크라이나 전쟁 물류',
    '대만 해협 위기',
    '이란 제재',
    '후티 반군 공격',
    '예멘 사태 해운',
    '이스라엘 가자 물류',
    '중동 위기 해운',
    '남중국해 분쟁',
    '인도태평양 공급망',
    '미국 관세',
    '트럼프 관세',
    'EU 제재',
  
    # ===== 디지털 물류 =====
    '스마트 물류',
    '물류 자동화',
    'AI 물류',
    '물류 로봇',
    '디지털 포워딩',
    '블록체인 물류',
    '디지털 트윈 물류',
  
    # ===== 풀필먼트 =====
    '풀필먼트 센터',
    '당일배송',
    '새벽배송',
    '라스트마일',
    '쿠팡 물류',
    'CJ대한통운',
    '롯데글로벌로지스',
    '한진',
    '로젠',
  
    # ===== 주요 제조업체 =====
    '삼성전자 물류',
    'SK하이닉스 공급망',
    '현대차 물류',
    '기아 공급망',
    'LG에너지솔루션',
    '삼성SDI',
    'SK온',
    'CATL 배터리',
    'TSMC 공급망',
    '테슬라 물류',
    '애플 공급망',
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

