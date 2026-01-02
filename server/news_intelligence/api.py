"""
News Intelligence API

Provides REST API endpoints for the News Intelligence service:
- /api/news-intelligence/articles - News article list with filters
- /api/news-intelligence/status - Collection status and summary
- /api/news-intelligence/map - Map data for crisis visualization
- /api/news-intelligence/wordcloud - Keyword data for word cloud
- /api/news-intelligence/categories - Category distribution
- /api/news-intelligence/critical-alerts - Crisis summary
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, or_, and_, desc, not_
import logging

from .models import NewsArticle, CollectionLog, get_session, init_database
from .analyzer import NewsAnalyzer

logger = logging.getLogger(__name__)

# Create Blueprint
news_bp = Blueprint('news_intelligence', __name__, url_prefix='/api/news-intelligence')

# Initialize database on import
init_database()


def is_gdelt_title_scraped_failed(title: str, source_name: str) -> bool:
    """
    Check if a GDELT article has failed title scraping.
    
    Failed GDELT articles have titles like:
    - "[GDELT] XXX: Material Conflict"
    - "[GDELT] XXX: Verbal Conflict"
    - "[GDELT] XXX: Material Cooperation"
    - "[GDELT] XXX: Verbal Cooperation"
    
    Returns True if the title scraping failed.
    """
    if source_name != 'GDELT':
        return False
    if not title:
        return True
    # Check for fallback title patterns
    failed_patterns = ['Conflict', 'Cooperation']
    return title.startswith('[GDELT]') and any(p in title for p in failed_patterns)


@news_bp.route('/articles', methods=['GET'])
def get_articles():
    """
    Get news articles with filtering and pagination.
    
    Query Parameters:
    - news_type: 'KR', 'GLOBAL', or 'all' (default: 'all')
    - category: Category filter (optional)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - is_crisis: Filter crisis articles only (optional, boolean)
    
    Returns:
    - articles: List of article objects
    - total: Total count matching filters
    - page: Current page
    - page_size: Items per page
    - total_pages: Total number of pages
    """
    # Parse parameters
    news_type = request.args.get('news_type', 'all')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)
    is_crisis = request.args.get('is_crisis')
    
    session = get_session()
    
    try:
        # Base query - only ACTIVE articles from last 24 hours
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        query = session.query(NewsArticle).filter(
            NewsArticle.status == 'ACTIVE',
            or_(
                and_(
                    NewsArticle.published_at_utc.isnot(None),
                    NewsArticle.published_at_utc >= cutoff_time
                ),
                and_(
                    NewsArticle.published_at_utc.is_(None),
                    NewsArticle.collected_at_utc >= cutoff_time
                )
            )
        )
        
        # Apply filters
        if news_type != 'all':
            query = query.filter(NewsArticle.news_type == news_type)
        
        if category:
            if category == 'ETC':
                # ETC includes both explicit 'ETC' and null categories
                query = query.filter(
                    or_(
                        NewsArticle.category == 'ETC',
                        NewsArticle.category.is_(None)
                    )
                )
            else:
                query = query.filter(NewsArticle.category == category)
        
        if is_crisis is not None:
            is_crisis_bool = is_crisis.lower() in ('true', '1', 'yes')
            query = query.filter(NewsArticle.is_crisis == is_crisis_bool)
        
        # Get all articles sorted by time
        all_articles = query.order_by(
            desc(func.coalesce(NewsArticle.published_at_utc, NewsArticle.collected_at_utc))
        ).all()
        
        # Filter out GDELT articles with failed title scraping (in Python for reliability)
        filtered_articles = [
            a for a in all_articles
            if not is_gdelt_title_scraped_failed(a.title, a.source_name)
        ]
        
        # Get total count after filtering
        total = len(filtered_articles)
        
        # Paginate
        offset = (page - 1) * page_size
        articles = filtered_articles[offset:offset + page_size]
        
        return jsonify({
            'articles': [a.to_dict() for a in articles],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
        })
        
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@news_bp.route('/status', methods=['GET'])
def get_status():
    """
    Get collection status and summary.
    
    Returns:
    - total_articles: Total articles in last 24 hours
    - kr_count: Korean news count
    - global_count: Global news count
    - last_updated_utc: Last successful collection time
    - categories: Category breakdown
    """
    session = get_session()
    
    try:
        # Get articles from last 24 hours
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        base_query = session.query(NewsArticle).filter(
            NewsArticle.status == 'ACTIVE',
            or_(
                and_(
                    NewsArticle.published_at_utc.isnot(None),
                    NewsArticle.published_at_utc >= cutoff_time
                ),
                and_(
                    NewsArticle.published_at_utc.is_(None),
                    NewsArticle.collected_at_utc >= cutoff_time
                )
            )
        )
        
        # Total count
        total = base_query.count()
        
        # Count by news type
        kr_count = base_query.filter(NewsArticle.news_type == 'KR').count()
        global_count = base_query.filter(NewsArticle.news_type == 'GLOBAL').count()
        
        # Count by category
        category_counts = session.query(
            NewsArticle.category,
            func.count(NewsArticle.id)
        ).filter(
            NewsArticle.status == 'ACTIVE',
            or_(
                and_(
                    NewsArticle.published_at_utc.isnot(None),
                    NewsArticle.published_at_utc >= cutoff_time
                ),
                and_(
                    NewsArticle.published_at_utc.is_(None),
                    NewsArticle.collected_at_utc >= cutoff_time
                )
            )
        ).group_by(NewsArticle.category).all()
        
        # Merge null categories into ETC
        categories = {}
        for cat, count in category_counts:
            cat_name = cat or 'ETC'
            categories[cat_name] = categories.get(cat_name, 0) + count
        
        # Crisis count
        crisis_count = base_query.filter(NewsArticle.is_crisis == True).count()
        
        # Get last collection log
        last_log = session.query(CollectionLog).filter_by(
            is_success=True
        ).order_by(desc(CollectionLog.executed_at_utc)).first()
        
        last_updated = last_log.executed_at_utc.isoformat() if last_log else None
        
        return jsonify({
            'total_articles': total,
            'kr_count': kr_count,
            'global_count': global_count,
            'crisis_count': crisis_count,
            'categories': categories,
            'last_updated_utc': last_updated,
            'current_time_utc': datetime.now(timezone.utc).isoformat(),
        })
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@news_bp.route('/map', methods=['GET'])
def get_map_data():
    """
    Get crisis data for map visualization.
    
    Returns country-level crisis scores for heatmap display.
    
    Returns:
    - countries: Dictionary of country_code -> crisis_count
    - total_crisis: Total crisis articles
    """
    session = get_session()
    
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Get crisis articles with country tags
        crisis_articles = session.query(NewsArticle).filter(
            NewsArticle.status == 'ACTIVE',
            NewsArticle.is_crisis == True,
            NewsArticle.country_tags.isnot(None),
            or_(
                and_(
                    NewsArticle.published_at_utc.isnot(None),
                    NewsArticle.published_at_utc >= cutoff_time
                ),
                and_(
                    NewsArticle.published_at_utc.is_(None),
                    NewsArticle.collected_at_utc >= cutoff_time
                )
            )
        ).all()
        
        # Count by country
        country_scores = {}
        for article in crisis_articles:
            if article.country_tags:
                for country in article.country_tags:
                    country_scores[country] = country_scores.get(country, 0) + 1
        
        return jsonify({
            'countries': country_scores,
            'total_crisis': len(crisis_articles),
        })
        
    except Exception as e:
        logger.error(f"Error getting map data: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@news_bp.route('/map/country/<country_code>', methods=['GET'])
def get_country_articles(country_code: str):
    """
    Get articles related to a specific country for map popup.
    
    Path Parameters:
    - country_code: ISO country code (e.g., US, CN, KR)
    
    Query Parameters:
    - limit: Maximum articles to return (default: 10)
    
    Returns:
    - articles: List of article summaries
    - total: Total count for this country
    """
    session = get_session()
    limit = min(int(request.args.get('limit', 10)), 20)
    
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Get all crisis articles within time range
        all_articles = session.query(NewsArticle).filter(
            NewsArticle.status == 'ACTIVE',
            NewsArticle.is_crisis == True,
            or_(
                and_(
                    NewsArticle.published_at_utc.isnot(None),
                    NewsArticle.published_at_utc >= cutoff_time
                ),
                and_(
                    NewsArticle.published_at_utc.is_(None),
                    NewsArticle.collected_at_utc >= cutoff_time
                )
            )
        ).order_by(desc(NewsArticle.collected_at_utc)).all()
        
        # Filter by country code in Python (DB-agnostic)
        filtered_articles = []
        for article in all_articles:
            if article.country_tags and country_code in article.country_tags:
                filtered_articles.append(article)
        
        total = len(filtered_articles)
        articles = filtered_articles[:limit]
        
        return jsonify({
            'country_code': country_code,
            'articles': [
                {
                    'id': a.id,
                    'title': a.title,
                    'source_name': a.source_name,
                    'category': a.category or 'ETC',
                    'url': a.url,
                    'published_at_utc': a.published_at_utc.isoformat() if a.published_at_utc else None,
                    'goldstein_scale': a.goldstein_scale,
                }
                for a in articles
            ],
            'total': total,
        })
        
    except Exception as e:
        logger.error(f"Error getting country articles for {country_code}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@news_bp.route('/wordcloud', methods=['GET'])
def get_wordcloud_data():
    """
    Get keyword data for word cloud visualization.
    
    Returns:
    - keywords: Dictionary of keyword -> frequency
    - total_articles: Number of articles analyzed
    """
    # Terms to exclude from word cloud (GDELT metrics, generic terms)
    EXCLUDED_TERMS = {
        'goldstein scale', 'goldstein', 'average tone', 'avg tone',
        'mentions', 'sources', 'articles', 'material conflict',
        'verbal conflict', 'material cooperation', 'verbal cooperation',
        'category', 'event', 'location', 'involves', 'unknown',
        'event category', 'num mentions', 'num sources', 'num articles',
    }
    
    session = get_session()
    
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Get articles with keywords
        articles = session.query(NewsArticle).filter(
            NewsArticle.status == 'ACTIVE',
            NewsArticle.keywords.isnot(None),
            or_(
                and_(
                    NewsArticle.published_at_utc.isnot(None),
                    NewsArticle.published_at_utc >= cutoff_time
                ),
                and_(
                    NewsArticle.published_at_utc.is_(None),
                    NewsArticle.collected_at_utc >= cutoff_time
                )
            )
        ).all()
        
        # Aggregate keywords
        keyword_freq = {}
        for article in articles:
            if article.keywords:
                for keyword in article.keywords:
                    keyword = keyword.lower().strip()
                    # Exclude GDELT metrics and generic terms
                    if keyword and len(keyword) > 2 and keyword not in EXCLUDED_TERMS:
                        keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Sort by frequency and take top 50
        sorted_keywords = dict(sorted(
            keyword_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:50])
        
        return jsonify({
            'keywords': sorted_keywords,
            'total_articles': len(articles),
        })
        
    except Exception as e:
        logger.error(f"Error getting wordcloud data: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@news_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    Get category distribution for chart visualization.
    
    Returns:
    - categories: List of {name, count, percentage}
    - total: Total article count
    """
    session = get_session()
    
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Count by category
        results = session.query(
            NewsArticle.category,
            func.count(NewsArticle.id)
        ).filter(
            NewsArticle.status == 'ACTIVE',
            or_(
                and_(
                    NewsArticle.published_at_utc.isnot(None),
                    NewsArticle.published_at_utc >= cutoff_time
                ),
                and_(
                    NewsArticle.published_at_utc.is_(None),
                    NewsArticle.collected_at_utc >= cutoff_time
                )
            )
        ).group_by(NewsArticle.category).all()
        
        total = sum(count for _, count in results)
        
        # Merge null categories into ETC
        category_dict = {}
        for cat, count in results:
            cat_name = cat or 'ETC'
            category_dict[cat_name] = category_dict.get(cat_name, 0) + count
        
        categories = []
        for cat_name, count in category_dict.items():
            categories.append({
                'name': cat_name,
                'count': count,
                'percentage': round(count / total * 100, 1) if total > 0 else 0
            })
        
        # Sort by count descending
        categories.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify({
            'categories': categories,
            'total': total,
        })
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@news_bp.route('/critical-alerts', methods=['GET'])
def get_critical_alerts():
    """
    Get critical alerts (crisis articles) with optional AI summary.
    
    Query Parameters:
    - limit: Maximum articles to return (default: 10)
    - include_summary: Include AI-generated summary (default: false)
    
    Returns:
    - alerts: List of crisis articles
    - count: Total crisis count
    - summary: AI-generated summary (if requested)
    """
    limit = request.args.get('limit', 10, type=int)
    include_summary = request.args.get('include_summary', 'false').lower() == 'true'
    
    session = get_session()
    
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Get crisis articles
        query = session.query(NewsArticle).filter(
            NewsArticle.status == 'ACTIVE',
            NewsArticle.is_crisis == True,
            or_(
                and_(
                    NewsArticle.published_at_utc.isnot(None),
                    NewsArticle.published_at_utc >= cutoff_time
                ),
                and_(
                    NewsArticle.published_at_utc.is_(None),
                    NewsArticle.collected_at_utc >= cutoff_time
                )
            )
        )
        
        # Sort by severity (Goldstein scale if available, then by time)
        query = query.order_by(
            NewsArticle.goldstein_scale.asc().nullslast(),
            desc(func.coalesce(NewsArticle.published_at_utc, NewsArticle.collected_at_utc))
        )
        
        total_count = query.count()
        alerts = query.limit(limit).all()
        
        result = {
            'alerts': [a.to_dict() for a in alerts],
            'count': total_count,
        }
        
        # Generate AI summary if requested
        if include_summary and alerts:
            try:
                analyzer = NewsAnalyzer()
                summary = analyzer.generate_crisis_summary([a.to_dict() for a in alerts])
                result['summary'] = summary
            except Exception as e:
                logger.error(f"Error generating summary: {e}")
                result['summary'] = None
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting critical alerts: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@news_bp.route('/collect', methods=['POST'])
def trigger_collection():
    """
    Manually trigger a news collection job.
    
    This endpoint is for testing/admin purposes.
    
    Returns:
    - Collection job result
    """
    from .collectors import NewsCollectorManager
    
    try:
        manager = NewsCollectorManager()
        result = manager.run_collection()
        
        # Run AI analysis on new articles
        if result.get('new_articles', 0) > 0:
            try:
                _analyze_unprocessed_articles()
            except Exception as e:
                logger.error(f"Error during analysis: {e}")
                result['analysis_error'] = str(e)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in collection: {e}")
        return jsonify({'error': str(e)}), 500


def _analyze_unprocessed_articles():
    """Analyze articles that haven't been processed by AI yet"""
    session = get_session()
    
    try:
        # Get articles without category
        articles = session.query(NewsArticle).filter(
            NewsArticle.category.is_(None)
        ).limit(50).all()
        
        if not articles:
            return
        
        analyzer = NewsAnalyzer()
        
        for article in articles:
            try:
                analysis = analyzer.analyze_article({
                    'title': article.title,
                    'content_summary': article.content_summary
                })
                
                article.category = analysis.get('category', 'ETC')
                article.country_tags = analysis.get('country_tags', [])
                article.keywords = analysis.get('keywords', [])
                article.is_crisis = analysis.get('is_crisis', False)
                
            except Exception as e:
                logger.warning(f"Error analyzing article {article.id}: {e}")
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

