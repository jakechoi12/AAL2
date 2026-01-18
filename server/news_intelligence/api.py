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
    Get keyword data for word cloud visualization (v2.4 개선).
    
    Features:
    - bigram/trigram 추출 (2-3단어 구문)
    - 강화된 STOP_WORDS 필터링
    - 조사/관사 필터링
    - 키워드 100개로 확장
    
    Returns:
    - keywords: List of {text, count, size}
    - total_articles: Number of articles analyzed
    """
    import re
    from collections import Counter
    
    # ===== 일반 단어 블랙리스트 (v2.4) =====
    STOP_WORDS = {
        'freight', 'logistics', 'shipping', 'port', 'container', 'cargo',
        'trade', 'import', 'export', 'supply chain', 'supplychain',
        '물류', '해운', '항만', '컨테이너', '수출', '수입', '무역', '화물', '운송', '공급망',
        'news', 'article', 'report', 'update', 'breaking', 'said', 'according',
        # 웹사이트/RSS 관련 불필요한 문구
        'appeared first', 'the post', 'first on', 'read more', 'click here',
        'on freightwaves', 'freightwaves', 'on air', 'cargo week', 'trade magazine',
        'source: bloomberg', 'journal of', 'yahoo finance', 'tradingview',
        # 일반적인 영어 구문
        'a new', 'of long', 'is expected', 'will be', 'has been', 'have been',
        'continued to', 'according to', 'more than', 'as well', 'such as',
        'this week', 'last year', 'last week', 'this year', 'next year',
        'from the', 'with the', 'from a', 'with a', 'that could', 'to be',
        'the new', 'the first', 'the us', 'the global', 'the maritime',
        'and the', 'as the', 'after the', 'across the', 'state of',
        'return to', 'service to', 'performance in', 'tonnes of',
        'a record', 'to red', 'time to', 'court to', 'and supply', 'to cut',
        'the u.s', 'the future', 'billion in', 'the suez',
        'expected to', 'set to', 'more the', 'the latest', 'the middle',
        'returns to', 'two years', 'market is', 'to return', 'to supply',
        'to close', 'the red', 'position in', 'teu in', 'in november',
        'through the', 'all markets', 'and passenger', 'record year',
        '2025 the', '2025 as', 'and jade', 'dragon and',
        # 한국어 일반 단어
        '지난', '오늘', '내일', '올해', '작년', '이번', '다음', '밝혔다', '전했다',
        '등 다양한', '다양한 산업', '수 있도록', '수 있다는', '이에 따라', '참석한 가운데',
        '전년 대비', '포함)은', '이코노미', '클래스', '밝혔다. 이번', '오는 2월',
        '받을 수 있다', '지난해 11월', '전년동기 대비', '포토]',
        # GDELT 관련
        'goldstein scale', 'goldstein', 'average tone', 'avg tone',
        'mentions', 'sources', 'articles', 'material conflict',
        'verbal conflict', 'material cooperation', 'verbal cooperation',
        'category', 'event', 'location', 'involves', 'unknown',
    }
    
    # 조사/관사 블랙리스트
    PREPOSITIONS = {
        'in', 'on', 'at', 'to', 'for', 'of', 'the', 'a', 'an', 'and', 'or', 'but',
        'in the', 'to the', 'for the', 'of the', 'on the', 'at the', 'by the',
        'in 2024', 'in 2025', 'in 2026', 'for 2026', 'in december', 'in january',
        'first on', 'the post', 'post appeared', 'on global',
        'port of', 'with the', 'from the', 'that the',
        # 날짜 패턴 (한국어)
        '지난 15일', '지난 14일', '지난 16일', '오는 15일', '오는 16일',
        '16일 밝혔다', '16일 오전', '지난해 12월', '16일 서울',
    }
    
    # 불필요한 패턴
    IRRELEVANT_PATTERNS = {
        '마줄스', '니콜라이스', '마줄스 남자농구', '남자농구 국가대표', '감독 취임',
        '취임 기자회견', '서울 광화문', '광화문 프레스', '프레스센타에서', '열렸다.',
        '만원', '68만', '54만', '56만', '△뉴욕', '△샌프란시스코', '△호놀룰루',
    }
    
    # 가격 패턴
    PRICE_PATTERN = re.compile(r'(\d+만\d*원?|△\w+|\d{2,}만|\d+원)')
    
    session = get_session()
    
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Get all ACTIVE articles (not just those with keywords)
        articles = session.query(NewsArticle).filter(
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
        ).all()
        
        keyword_counts = Counter()
        
        for article in articles:
            # 기존 키워드에서 일반 단어 제외
            if article.keywords:
                for kw in article.keywords:
                    kw_lower = kw.lower()
                    if kw_lower not in STOP_WORDS and len(kw) > 2:
                        if len(kw.split()) >= 2:  # 2단어 이상만
                            keyword_counts[kw_lower] += 1
            
            # 제목과 요약에서 bigram/trigram 추출
            title = article.title or ''
            summary = article.content_summary or ''
            text = f"{title} {summary}"
            
            # 단어 토큰화
            words = re.findall(r'\b[\w가-힣]+\b', text.lower())
            
            # 2단어 구문 (bigram)
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i+1]}"
                # 필터링 조건
                if bigram in PREPOSITIONS or bigram in STOP_WORDS:
                    continue
                if any(w in STOP_WORDS or w in PREPOSITIONS for w in bigram.split()):
                    continue
                if len(bigram) > 4:
                    keyword_counts[bigram] += 1
            
            # 3단어 구문 (trigram)
            for i in range(len(words) - 2):
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                if any(p in trigram for p in PREPOSITIONS):
                    continue
                if trigram in STOP_WORDS:
                    continue
                if len(trigram) > 6:
                    keyword_counts[trigram] += 1
        
        # 불필요한 패턴 필터링
        filtered_counts = Counter()
        for word, count in keyword_counts.items():
            # 불필요한 패턴 체크
            if any(pattern in word for pattern in IRRELEVANT_PATTERNS):
                continue
            # 가격 패턴 체크
            if PRICE_PATTERN.search(word):
                continue
            # 특수문자만 있는 경우 제외
            if re.match(r'^[\W\d]+$', word):
                continue
            # 최소 2회 이상 등장
            if count >= 2:
                filtered_counts[word] = count
        
        # 중복 제거: 짧은 구문이 긴 구문에 포함되면 제거
        final_counts = Counter()
        sorted_keywords = sorted(filtered_counts.keys(), key=lambda x: len(x), reverse=True)
        
        for word in sorted_keywords:
            is_subset = False
            for existing in final_counts:
                if word in existing and word != existing:
                    is_subset = True
                    break
            if not is_subset:
                final_counts[word] = filtered_counts[word]
        
        # 워드클라우드 형식으로 변환 (100개)
        wordcloud_list = [
            {'text': word, 'count': count, 'size': min(count * 10, 100)}
            for word, count in final_counts.most_common(100)
        ]
        
        return jsonify({
            'keywords': wordcloud_list,
            'total_articles': len(articles),
            'total_keywords': len(final_counts),
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

