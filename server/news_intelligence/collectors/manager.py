"""
News Collector Manager

Coordinates all news collectors and manages the collection pipeline.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import time

from .rss_collector import RSSCollector
from .gdelt_collector import GDELTCollector
from .google_news_collector import GoogleNewsCollector
from .naver_news_collector import NaverNewsCollector
from ..models import NewsArticle, CollectionLog, get_session, init_database

logger = logging.getLogger(__name__)


class NewsCollectorManager:
    """
    Manages all news collectors and orchestrates collection jobs.
    
    Features:
    - Runs all collectors in sequence
    - Handles deduplication based on URL
    - Logs collection statistics
    - Manages database storage
    """
    
    def __init__(self, enable_gdelt: bool = True, enable_google: bool = True, enable_naver: bool = True):
        """
        Initialize collector manager.
        
        Args:
            enable_gdelt: Enable GDELT collector
            enable_google: Enable Google News collector
            enable_naver: Enable Naver News collector
        """
        self.collectors = []
        
        # RSS collectors (always enabled)
        self.collectors.append(RSSCollector(feed_type='global'))
        self.collectors.append(RSSCollector(feed_type='korean'))
        
        # Optional collectors
        if enable_gdelt:
            self.collectors.append(GDELTCollector())
        if enable_google:
            self.collectors.append(GoogleNewsCollector())
        if enable_naver:
            self.collectors.append(NaverNewsCollector())
        
        # Initialize database
        init_database()
        
        self.logger = logging.getLogger(__name__)
    
    def run_collection(self) -> Dict[str, Any]:
        """
        Run a complete collection job.
        
        Returns:
            Dictionary with collection results and statistics
        """
        start_time = time.time()
        
        result = {
            'success': True,
            'total_collected': 0,
            'new_articles': 0,
            'duplicates': 0,
            'kr_count': 0,
            'global_count': 0,
            'errors': [],
            'executed_at_utc': datetime.now(timezone.utc).isoformat(),
        }
        
        all_articles = []
        
        # Collect from all sources
        for collector in self.collectors:
            try:
                articles = collector.collect()
                all_articles.extend(articles)
                self.logger.info(f"Collected {len(articles)} from {collector.name}")
            except Exception as e:
                error_msg = f"Error in {collector.name}: {str(e)}"
                self.logger.error(error_msg)
                result['errors'].append(error_msg)
        
        result['total_collected'] = len(all_articles)
        
        # Store articles (with deduplication)
        try:
            stored_count, duplicate_count = self._store_articles(all_articles)
            result['new_articles'] = stored_count
            result['duplicates'] = duplicate_count
            
            # Count by type
            session = get_session()
            try:
                # Count articles stored in this run
                for article in all_articles:
                    if article.get('news_type') == 'KR':
                        result['kr_count'] += 1
                    else:
                        result['global_count'] += 1
            finally:
                session.close()
                
        except Exception as e:
            error_msg = f"Error storing articles: {str(e)}"
            self.logger.error(error_msg)
            result['errors'].append(error_msg)
            result['success'] = False
        
        # Archive old articles
        try:
            archived_count = self._archive_old_articles()
            result['archived'] = archived_count
        except Exception as e:
            self.logger.error(f"Error archiving old articles: {e}")
        
        # Calculate duration
        result['duration_seconds'] = round(time.time() - start_time, 2)
        
        # Log collection result
        try:
            self._log_collection(result)
        except Exception as e:
            self.logger.error(f"Error logging collection: {e}")
        
        return result
    
    def _store_articles(self, articles: List[Dict[str, Any]]) -> tuple:
        """
        Store articles in database with deduplication.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Tuple of (stored_count, duplicate_count)
        """
        session = get_session()
        stored_count = 0
        duplicate_count = 0
        
        try:
            for article_data in articles:
                url = article_data.get('url')
                if not url:
                    continue
                
                # Check for duplicate
                existing = session.query(NewsArticle).filter_by(url=url).first()
                if existing:
                    duplicate_count += 1
                    continue
                
                # Create new article
                article = NewsArticle(
                    title=article_data.get('title', ''),
                    content_summary=article_data.get('content_summary'),
                    source_name=article_data.get('source_name', 'Unknown'),
                    url=url,
                    published_at_utc=article_data.get('published_at_utc'),
                    collected_at_utc=datetime.now(timezone.utc),
                    news_type=article_data.get('news_type', 'GLOBAL'),
                    country_tags=article_data.get('country_tags'),
                    goldstein_scale=article_data.get('goldstein_scale'),
                    avg_tone=article_data.get('avg_tone'),
                    num_mentions=article_data.get('num_mentions'),
                    num_sources=article_data.get('num_sources'),
                    num_articles=article_data.get('num_articles'),
                    status='ACTIVE',
                )
                
                session.add(article)
                stored_count += 1
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
        
        return stored_count, duplicate_count
    
    def _archive_old_articles(self) -> int:
        """
        Archive articles older than 24 hours.
        
        Returns:
            Number of archived articles
        """
        session = get_session()
        archived_count = 0
        
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            # Find articles to archive (using published_at_utc or collected_at_utc)
            from sqlalchemy import or_, and_
            
            articles_to_archive = session.query(NewsArticle).filter(
                NewsArticle.status == 'ACTIVE',
                or_(
                    and_(
                        NewsArticle.published_at_utc.isnot(None),
                        NewsArticle.published_at_utc < cutoff_time
                    ),
                    and_(
                        NewsArticle.published_at_utc.is_(None),
                        NewsArticle.collected_at_utc < cutoff_time
                    )
                )
            ).all()
            
            for article in articles_to_archive:
                article.status = 'ARCHIVED'
                archived_count += 1
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error archiving articles: {e}")
        finally:
            session.close()
        
        return archived_count
    
    def _log_collection(self, result: Dict[str, Any]):
        """
        Log collection job result to database.
        
        Args:
            result: Collection result dictionary
        """
        session = get_session()
        
        try:
            log = CollectionLog(
                executed_at_utc=datetime.now(timezone.utc),
                total_collected=result.get('total_collected', 0),
                kr_news_count=result.get('kr_count', 0),
                global_news_count=result.get('global_count', 0),
                new_articles_count=result.get('new_articles', 0),
                duplicate_count=result.get('duplicates', 0),
                is_success=result.get('success', True),
                error_message='; '.join(result.get('errors', [])) if result.get('errors') else None,
                duration_seconds=result.get('duration_seconds'),
            )
            
            session.add(log)
            session.commit()
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error logging collection: {e}")
        finally:
            session.close()
    
    def get_last_collection_log(self) -> Optional[Dict[str, Any]]:
        """
        Get the last successful collection log.
        
        Returns:
            Collection log dictionary or None
        """
        session = get_session()
        
        try:
            log = session.query(CollectionLog).filter_by(
                is_success=True
            ).order_by(
                CollectionLog.executed_at_utc.desc()
            ).first()
            
            if log:
                return log.to_dict()
            return None
            
        finally:
            session.close()

