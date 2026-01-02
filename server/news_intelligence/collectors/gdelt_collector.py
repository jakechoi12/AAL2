"""
GDELT Collector

Collects logistics-related events from GDELT (Global Database of Events, Language, and Tone).
Uses existing GDELT data infrastructure from gdelt_backend.
"""

import os
import sys
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
from .base import BaseCollector
import logging

logger = logging.getLogger(__name__)

# Simple cache for fetched titles (to avoid re-fetching)
_title_cache: Dict[str, str] = {}

# Add parent directory for gdelt_backend import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class GDELTCollector(BaseCollector):
    """
    Collects logistics-relevant events from GDELT data.
    
    Focuses on events with negative Goldstein scores that may
    indicate supply chain disruptions (conflicts, strikes, etc.)
    """
    
    # CAMEO event codes related to logistics/supply chain
    LOGISTICS_RELATED_CODES = {
        # Protests and strikes
        '140': 'Engage in political dissidence',
        '1411': 'Demonstrate or rally',
        '1412': 'Strike or boycott',
        '1413': 'Obstruct passage',
        '1414': 'Riot',
        # Economic actions
        '0231': 'Appeal for economic aid',
        '0311': 'Express intent to cooperate economically',
        '061': 'Provide economic support',
        # Sanctions and restrictions
        '163': 'Impose embargo, boycott, or sanctions',
        # Military/security (affects shipping lanes)
        '190': 'Use conventional military force',
        '193': 'Fight with artillery and tanks',
        '195': 'Employ aerial weapons',
    }
    
    # Goldstein scale threshold for crisis detection
    CRISIS_THRESHOLD = -4.0
    
    def __init__(self, goldstein_threshold: float = -4.0, max_events: int = 100):
        """
        Initialize GDELT collector.
        
        Args:
            goldstein_threshold: Minimum Goldstein score to consider as crisis
            max_events: Maximum number of events to collect
        """
        super().__init__(name='GDELTCollector', news_type='GLOBAL')
        self.goldstein_threshold = goldstein_threshold
        self.max_events = max_events
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect crisis events from GDELT data.
        
        Returns:
            List of event dictionaries formatted as news articles
        """
        try:
            import gdelt_backend
            
            # Get cached alerts from gdelt_backend
            result = gdelt_backend.get_cached_alerts(
                goldstein_threshold=self.goldstein_threshold,
                max_alerts=self.max_events,
                sort_by='severity'
            )
            
            if 'error' in result:
                self.logger.error(f"GDELT error: {result['error']}")
                return []
            
            alerts = result.get('alerts', [])
            articles = []
            
            # First pass: convert alerts to articles with basic info
            for alert in alerts:
                try:
                    article = self._convert_alert_to_article(alert)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Error converting GDELT alert: {e}")
            
            # Second pass: fetch titles from URLs in parallel (limited to avoid overload)
            self._fetch_titles_parallel(articles, max_workers=10)
            
            self.logger.info(f"Collected {len(articles)} events from GDELT")
            return articles
            
        except ImportError:
            self.logger.error("gdelt_backend module not available")
            return []
        except Exception as e:
            self.logger.error(f"Error collecting from GDELT: {e}")
            return []
    
    def _fetch_title_from_url(self, url: str) -> Optional[str]:
        """
        Fetch the title from a URL by scraping the HTML.
        
        Args:
            url: The URL to fetch
            
        Returns:
            The title or None if failed
        """
        global _title_cache
        
        # Check cache first
        if url in _title_cache:
            return _title_cache[url]
        
        # Skip non-http URLs
        if not url or not url.startswith('http'):
            return None
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
            response.raise_for_status()
            
            # Try to find title in HTML
            html = response.text[:10000]  # Only check first 10KB
            
            # Try <title> tag first
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                # Clean up common suffixes
                title = re.sub(r'\s*[\|\-–—]\s*[^|\-–—]+$', '', title)
                title = title.strip()
                if title and len(title) > 5:
                    _title_cache[url] = title
                    return title
            
            # Try og:title meta tag
            og_title_match = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if og_title_match:
                title = og_title_match.group(1).strip()
                if title and len(title) > 5:
                    _title_cache[url] = title
                    return title
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to fetch title from {url}: {e}")
            return None
    
    def _fetch_titles_parallel(self, articles: List[Dict[str, Any]], max_workers: int = 10):
        """
        Fetch titles for articles in parallel.
        
        Args:
            articles: List of article dictionaries
            max_workers: Maximum number of parallel workers
        """
        # All GDELT articles need title fetching
        needs_fetch = [
            (i, a) for i, a in enumerate(articles)
            if a.get('url') and a.get('url').startswith('http')
        ]
        
        if not needs_fetch:
            return
        
        self.logger.info(f"Fetching titles for {len(needs_fetch)} GDELT articles...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit fetch tasks
            future_to_idx = {
                executor.submit(self._fetch_title_from_url, a['url']): i
                for i, a in needs_fetch
            }
            
            # Process completed futures
            fetched_count = 0
            for future in as_completed(future_to_idx, timeout=30):
                idx = future_to_idx[future]
                try:
                    title = future.result()
                    if title:
                        articles[idx]['title'] = title
                        articles[idx]['title_scraped'] = True  # Mark as successfully scraped
                        fetched_count += 1
                    else:
                        articles[idx]['title_scraped'] = False  # Mark as failed
                except Exception as e:
                    self.logger.debug(f"Error fetching title: {e}")
                    articles[idx]['title_scraped'] = False  # Mark as failed
        
        self.logger.info(f"Fetched {fetched_count} titles from URLs")
    
    def _convert_alert_to_article(self, alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert GDELT alert to news article format.
        
        Args:
            alert: GDELT alert dictionary
            
        Returns:
            Article dictionary or None
        """
        # Generate unique URL for GDELT event
        event_id = alert.get('id') or f"gdelt-{alert.get('event_date', '')}-{alert.get('event_code', '')}"
        source_url = alert.get('source_url') or alert.get('url')
        
        if not source_url:
            source_url = f"https://gdeltproject.org/events/{event_id}"
        
        # Build title from actors and category (using correct field names from gdelt_backend)
        actor1 = alert.get('actor1', '') or ''
        actor2 = alert.get('actor2', '') or ''
        category = alert.get('category', 'Event')
        location = alert.get('location', '')
        
        # Create a more descriptive title
        if actor1 and actor2:
            title = f"[GDELT] {actor1} → {actor2}: {category}"
        elif actor1:
            title = f"[GDELT] {actor1}: {category}"
        elif location:
            title = f"[GDELT] {location}: {category}"
        else:
            title = f"[GDELT] {category}"
        
        # Build summary (more descriptive, without metric labels that would be extracted as keywords)
        goldstein = alert.get('goldstein_scale') or alert.get('scale') or 0
        avg_tone = alert.get('avg_tone') or 0
        
        summary_parts = []
        if location:
            summary_parts.append(f"Event in {location}.")
        summary_parts.append(f"Event category: {category}.")
        if actor1 and actor2:
            summary_parts.append(f"Involves {actor1} and {actor2}.")
        elif actor1:
            summary_parts.append(f"Involves {actor1}.")
        
        summary = ' '.join(summary_parts)
        
        # Parse date
        published_at = None
        date_str = alert.get('event_date') or alert.get('date')
        if date_str:
            try:
                if len(str(date_str)) == 8:  # YYYYMMDD format
                    published_at = datetime.strptime(str(date_str), '%Y%m%d')
                else:
                    published_at = self.parse_datetime(str(date_str))
            except:
                pass
        
        # Extract country codes (using correct field names from gdelt_backend)
        country_tags = []
        if alert.get('actor1_country'):
            country_tags.append(alert['actor1_country'])
        if alert.get('actor2_country') and alert['actor2_country'] not in country_tags:
            country_tags.append(alert['actor2_country'])
        if alert.get('country_code') and alert['country_code'] not in country_tags:
            country_tags.append(alert['country_code'])
        
        return {
            'title': title,
            'content_summary': summary,
            'source_name': 'GDELT',
            'url': source_url,
            'published_at_utc': published_at,
            'news_type': 'GLOBAL',
            'country_tags': country_tags,
            # GDELT-specific metrics
            'goldstein_scale': goldstein,
            'avg_tone': avg_tone,
            'num_mentions': alert.get('num_mentions'),
            'num_sources': alert.get('num_sources'),
            'num_articles': alert.get('num_articles'),
        }

