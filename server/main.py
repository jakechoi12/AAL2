from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import requests
import os
import sys
import subprocess
import signal
from dotenv import load_dotenv
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

# Load environment variables FIRST before importing modules that need DATABASE_URL
load_dotenv()

import atexit
import logging
import bok_backend  # Import the BOK backend module
import gdelt_backend  # Import the GDELT backend module
from report.api import report_bp  # Import the Report backend module
from news_intelligence.api import news_bp  # Import the News Intelligence module
from auth.auth_backend import auth_bp  # Import the Auth module
from auth.models import init_db as init_auth_db  # Initialize auth database
from kcci.api import kcci_bp  # Import the KCCI module
# Import Shipping Indices module with detailed error handling
print("=" * 60)
print("Importing Shipping Indices module...")
try:
    from shipping_indices.api import shipping_bp  # Import the Shipping Indices module
    print("[OK] Shipping Indices module imported successfully")
    print(f"   Blueprint name: {shipping_bp.name}")
    print(f"   URL prefix: {shipping_bp.url_prefix}")
except ImportError as e:
    print(f"[ERROR] ImportError: Failed to import shipping_indices module")
    print(f"   Error: {e}")
    print("   This is usually due to missing dependencies.")
    print("   Please install: pip install pandas xlrd")
    import traceback
    traceback.print_exc()
    # Create empty Blueprint so server can continue running
    from flask import Blueprint
    shipping_bp = Blueprint('shipping_indices', __name__, url_prefix='/api/shipping-indices')
    print("   [WARN] Created empty Blueprint (no routes will work)")
except Exception as e:
    print(f"[ERROR] Unexpected error importing shipping_indices module: {e}")
    import traceback
    traceback.print_exc()
    from flask import Blueprint
    shipping_bp = Blueprint('shipping_indices', __name__, url_prefix='/api/shipping-indices')
    print("   [WARN] Created empty Blueprint (no routes will work)")
print("=" * 60)
print()

# Global variable to store quote_backend process
quote_backend_process = None

# Determine base directory (parent of server directory)
BASE_DIR = Path(__file__).parent.parent

# Flask 앱 초기화
# static_folder를 설정하지 않아서 기본 라우트와 충돌하지 않도록 함
app = Flask(__name__)
CORS(app) # Enable CORS for all routes (for development)

# Register Blueprints
try:
    app.register_blueprint(report_bp)
    app.register_blueprint(news_bp)  # News Intelligence API
    app.register_blueprint(kcci_bp)  # KCCI (Korea Container Freight Index) API
    app.register_blueprint(shipping_bp)  # Shipping Indices (BDI, SCFI, CCFI) API
    app.register_blueprint(auth_bp)  # User Authentication API
    print("[OK] All blueprints registered successfully")
except Exception as e:
    print(f"[ERROR] Error registering blueprints: {e}")
    import traceback
    traceback.print_exc()

# Initialize Auth Database
init_auth_db()

# Disable caching for development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_no_cache_headers(response):
    """Add no-cache headers to all responses for development"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ECOS_API_KEY = os.getenv("ECOS_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
API_BASE_URL = "http://ecos.bok.or.kr/api"

# API Routes (must be defined before static file routes)

@app.route('/api/bok/stats', methods=['GET'])
def get_bok_stats():
    stat_code = request.args.get('statCode')
    item_code = request.args.get('itemCode')
    cycle = request.args.get('cycle', 'D') # Default to Daily
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    
    if not all([stat_code, item_code, start_date, end_date]):
        return jsonify({"error": "Missing parameters: statCode, itemCode, startDate, endDate are required"}), 400

    result = bok_backend.get_bok_statistics(stat_code, item_code, cycle, start_date, end_date)
    
    if "error" in result:
        return jsonify(result), 500
        
    return jsonify(result)


@app.route('/api/market/indices', methods=['GET'])
def get_market_indices():
    category = request.args.get('type', 'exchange') # default to exchange
    item_code = request.args.get('itemCode')  # Optional: specific item within category
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    cycle = request.args.get('cycle')  # Optional: override default cycle
    stat_code = request.args.get('statCode')  # Optional: for inflation category
    
    if not all([category, start_date, end_date]):
         return jsonify({"error": "Missing parameters: type, startDate, endDate"}), 400

    result = bok_backend.get_market_index(category, start_date, end_date, item_code=item_code, cycle=cycle, stat_code=stat_code)
    return jsonify(result)

@app.route('/api/market/indices/multi', methods=['GET'])
def get_market_indices_multi():
    """
    Fetch multiple items for a category at once.
    """
    category = request.args.get('type', 'exchange')
    item_codes = request.args.getlist('itemCode')  # Multiple item codes
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    cycle = request.args.get('cycle')
    
    if not all([category, start_date, end_date]):
         return jsonify({"error": "Missing parameters: type, startDate, endDate"}), 400
    
    # If no item codes specified, fetch all
    if not item_codes:
        item_codes = None
    
    result = bok_backend.get_market_index_multi(category, start_date, end_date, item_codes=item_codes, cycle=cycle)
    return jsonify(result)

@app.route('/api/market/categories', methods=['GET'])
def get_market_categories():
    """
    Get information about available categories and their items.
    """
    category = request.args.get('category')
    result = bok_backend.get_category_info(category=category)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/api/bok/search-codes', methods=['GET'])
def search_statistical_codes():
    """
    통계표 코드를 검색합니다.
    
    파라미터:
    - statCode: 통계표 코드 (부분 검색 가능, 선택)
    - statName: 통계표명 (부분 검색 가능, 선택)
    - startIndex: 요청 시작 건수 (기본값: 1)
    - endIndex: 요청 종료 건수 (기본값: 100, 최대 1000)
    
    예시:
    - GET /api/bok/search-codes?statCode=901Y
    - GET /api/bok/search-codes?statName=소비자물가지수
    - GET /api/bok/search-codes?statCode=404Y&statName=물가
    """
    stat_code = request.args.get('statCode')
    stat_name = request.args.get('statName')
    start_index = request.args.get('startIndex', 1, type=int)
    end_index = request.args.get('endIndex', 100, type=int)
    
    result = bok_backend.search_statistical_codes(
        stat_code=stat_code,
        stat_name=stat_name,
        start_index=start_index,
        end_index=end_index
    )
    
    if "error" in result:
        return jsonify(result), 500
    
    return jsonify(result)

@app.route('/api/bok/item-list', methods=['GET'])
def get_statistic_item_list():
    """
    특정 통계표의 항목 목록을 조회합니다.
    
    파라미터:
    - statCode: 통계표 코드 (필수)
    - startIndex: 요청 시작 건수 (기본값: 1)
    - endIndex: 요청 종료 건수 (기본값: 100, 최대 1000)
    
    예시:
    - GET /api/bok/item-list?statCode=901Y009
    """
    stat_code = request.args.get('statCode')
    start_index = request.args.get('startIndex', 1, type=int)
    end_index = request.args.get('endIndex', 100, type=int)
    
    if not stat_code:
        return jsonify({"error": "Missing parameter: statCode is required"}), 400
    
    result = bok_backend.get_statistic_item_list(
        stat_code=stat_code,
        start_index=start_index,
        end_index=end_index
    )
    
    if "error" in result:
        return jsonify(result), 500
    
    return jsonify(result)


@app.route('/api/bok/cache/stats', methods=['GET'])
def get_bok_cache_stats():
    """
    BOK API 캐시 통계를 반환합니다.
    
    Returns:
    - total: 전체 캐시 항목 수
    - active: 유효한 캐시 항목 수
    - expired: 만료된 캐시 항목 수
    """
    try:
        stats = bok_backend.get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/bok/cache/clear', methods=['POST'])
def clear_bok_cache():
    """
    BOK API 캐시를 초기화합니다.
    """
    try:
        bok_backend.clear_api_cache()
        return jsonify({'message': 'BOK API cache cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing BOK cache: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/indices/stats', methods=['GET'])
def get_market_indices_stats():
    """
    시장 지수 데이터의 통계 정보를 반환합니다 (환율, 물가, GDP 등).
    - 고점 (high)
    - 저점 (low)
    - 평균 (average)
    - 현재값 (current)
    - 변동률 (change, changePercent)
    """
    category = request.args.get('type', 'exchange')
    item_code = request.args.get('itemCode')  # 항목 코드 (예: USD, CPI_TOTAL, GDP_TOTAL)
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    cycle = request.args.get('cycle')
    
    if not all([category, start_date, end_date]):
        return jsonify({"error": "Missing parameters: type, startDate, endDate are required"}), 400
    
    # 시장 지수 데이터 조회
    result = bok_backend.get_market_index(category, start_date, end_date, item_code=item_code, cycle=cycle)
    
    if "error" in result:
        # 날짜 범위 오류 등은 400으로 반환 (클라이언트 오류)
        error_msg = result.get("error", "Unknown error")
        if "Date range" in error_msg or "date" in error_msg.lower():
            return jsonify(result), 400
        return jsonify(result), 500
    
    # 통계 정보 계산
    # GDP는 QoQ(직전 분기 대비)로 계산 (나머지는 기존 range-start 대비 유지)
    if category == 'gdp':
        stats = bok_backend.calculate_statistics_previous_period(result, currency_code=item_code)
    else:
        stats = bok_backend.calculate_statistics(result, currency_code=item_code)
    
    if "error" in stats:
        return jsonify(stats), 500
    
    return jsonify(stats)

@app.route('/api/global-alerts', methods=['GET'])
def get_global_alerts():
    """
    GDELT 기반 글로벌 긴급 알림을 반환합니다.
    
    Parameters:
    - threshold: GoldsteinScale 임계값 (기본값: -5.0)
    - max_alerts: 최대 알림 수 (기본값: 1000)
    - start_date: 시작 날짜 (YYYY-MM-DD, 선택사항)
    - end_date: 종료 날짜 (YYYY-MM-DD, 선택사항)
    - country: 국가 코드 필터 (예: US, KR)
    - category: 카테고리 필터 (예: Material Conflict)
    - min_articles: 최소 기사 수 필터
    - sort_by: 정렬 기준 (importance, date, tone, scale)
    """
    threshold = request.args.get('threshold', -5.0, type=float)
    max_alerts = request.args.get('max_alerts', 1000, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    country = request.args.get('country')
    category = request.args.get('category')
    min_articles = request.args.get('min_articles', type=int)
    sort_by = request.args.get('sort_by', 'date')
    
    try:
        # 날짜 범위가 지정된 경우
        if start_date and end_date:
            result = gdelt_backend.get_alerts_by_date_range(
                start_date=start_date,
                end_date=end_date,
                goldstein_threshold=threshold,
                max_alerts=max_alerts,
                country=country,
                category=category,
                min_articles=min_articles,
                sort_by=sort_by
            )
        else:
            # 최신 데이터 가져오기 (캐싱 사용)
            result = gdelt_backend.get_cached_alerts(
                goldstein_threshold=threshold,
                max_alerts=max_alerts,
                country=country,
                category=category,
                min_articles=min_articles,
                sort_by=sort_by
            )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in get_global_alerts: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'alerts': [],
            'count': 0
        }), 500


@app.route('/api/global-alerts/stats/by-country', methods=['GET'])
def get_stats_by_country():
    """
    국가별 통계를 반환합니다.
    
    Parameters:
    - threshold: GoldsteinScale 임계값 (기본값: -5.0)
    """
    threshold = request.args.get('threshold', -5.0, type=float)
    
    try:
        result = gdelt_backend.get_stats_by_country(goldstein_threshold=threshold)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_stats_by_country: {e}", exc_info=True)
        return jsonify({'error': str(e), 'stats': {}}), 500


@app.route('/api/global-alerts/stats/by-category', methods=['GET'])
def get_stats_by_category():
    """
    카테고리별 통계를 반환합니다.
    
    Parameters:
    - threshold: GoldsteinScale 임계값 (기본값: -5.0)
    """
    threshold = request.args.get('threshold', -5.0, type=float)
    
    try:
        result = gdelt_backend.get_stats_by_category(goldstein_threshold=threshold)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_stats_by_category: {e}", exc_info=True)
        return jsonify({'error': str(e), 'stats': {}}), 500


@app.route('/api/global-alerts/trends', methods=['GET'])
def get_trends():
    """
    시간대별 트렌드를 분석합니다.
    
    Parameters:
    - start_date: 시작 날짜 (YYYY-MM-DD, 필수)
    - end_date: 종료 날짜 (YYYY-MM-DD, 필수)
    - threshold: GoldsteinScale 임계값 (기본값: -5.0)
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    threshold = request.args.get('threshold', -5.0, type=float)
    
    if not start_date or not end_date:
        return jsonify({
            'error': 'start_date and end_date are required (YYYY-MM-DD format)',
            'trends': {}
        }), 400
    
    try:
        result = gdelt_backend.get_trends(
            start_date=start_date,
            end_date=end_date,
            goldstein_threshold=threshold
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_trends: {e}", exc_info=True)
        return jsonify({'error': str(e), 'trends': {}}), 500


@app.route('/api/global-alerts/cache/clear', methods=['POST'])
def clear_cache():
    """
    캐시를 초기화합니다.
    """
    try:
        gdelt_backend.clear_cache()
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/news', methods=['GET'])
def get_news():
    # Mock Data for now as per plan
    news_data = [
        {
            "date": "2024.05.20",
            "title": "파나마 운하 통행량 제한 완화 발표",
            "summary": "우기 시작으로 수위가 상승함에 따라 일일 통행 선박 수를 단계적으로 늘릴 예정입니다.",
            "tag": "Shipping"
        },
        {
            "date": "2024.05.19",
            "title": "항공 화물 수요, 3개월 연속 상승세",
            "summary": "중국발 이커머스 물량 급증으로 인해 아시아-북미 항공 화물 스페이스 부족 현상이 심화되고 있습니다.",
            "tag": "Air Cargo"
        },
        {
            "date": "2024.05.18",
            "title": "K-물류 플랫폼, 동남아 시장 진출 가속화",
            "summary": "국내 주요 물류 스타트업들이 베트남과 인도네시아 현지 물류 센터를 확보하며 시장 공략에 나섰습니다.",
            "tag": "Business"
        }
    ]
    return jsonify(news_data)

@app.route('/api/logistics', methods=['GET'])
def get_logistics_indices():
    # Mock Data for Logistics Indices
    # In real world, this might come from another API
    return jsonify({
        "SCFI": {"value": "2300.50", "change": "+12.5", "trend": "up"},
        "BDI": {"value": "1500.00", "change": "-5.0", "trend": "down"}
    })

@app.route('/api/config/google-maps-key', methods=['GET'])
def get_google_maps_key():
    """
    Google Maps API 키를 반환합니다.
    클라이언트에서 환경 변수로부터 안전하게 API 키를 가져올 수 있도록 합니다.
    """
    if not GOOGLE_MAPS_API_KEY:
        return jsonify({"error": "Google Maps API key is not configured"}), 500
    return jsonify({"apiKey": GOOGLE_MAPS_API_KEY})


# API Proxy Endpoint (Legacy - keeping for now, but BOK logic is preferred via bok_backend)
@app.route('/api/exchange-rates', methods=['GET'])
def get_exchange_rates():
    item_code = request.args.get('itemCode')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    if not all([item_code, start_date, end_date]):
        return jsonify({"error": "Missing parameters"}), 400

    if not ECOS_API_KEY:
        return jsonify({"error": "Server configuration error: API Key missing"}), 500

    # Format: /StatisticSearch/KEY/json/kr/1/10/731Y001/D/START/END/ITEM
    url = f"{API_BASE_URL}/StatisticSearch/{ECOS_API_KEY}/json/kr/1/10/731Y001/D/{start_date}/{end_date}/{item_code}"

    try:
        response = requests.get(url)
        # Pass the raw JSON from ECOS back to frontend
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Static File Routes (must be defined after API routes)
@app.route('/')
def serve_index():
    # frontend/ai_studio_code_F2.html을 메인 페이지로 서빙
    f2_file = BASE_DIR / 'frontend' / 'ai_studio_code_F2.html'
    if f2_file.exists():
        return send_file(str(f2_file))
    else:
        return "File not found: frontend/ai_studio_code_F2.html", 404

@app.route('/test_frontend.html')
def serve_test_page():
    """프론트엔드 테스트 페이지 서빙"""
    test_file = BASE_DIR / 'frontend' / 'test_frontend.html'
    if test_file.exists():
        return send_file(str(test_file))
    else:
        return "File not found: frontend/test_frontend.html", 404

@app.route('/css/<path:filename>')
def serve_css(filename):
    """CSS 파일 서빙"""
    return send_from_directory(str(BASE_DIR / 'frontend' / 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """JavaScript 파일 서빙"""
    return send_from_directory(str(BASE_DIR / 'frontend' / 'js'), filename)

@app.route('/pages/<path:filename>')
def serve_pages(filename):
    """Pages 폴더 파일 서빙 (quotation.html 등)"""
    return send_from_directory(str(BASE_DIR / 'frontend' / 'pages'), filename)


# GDELT 데이터 자동 업데이트 스케줄러
scheduler = BackgroundScheduler(daemon=True)


def update_gdelt_data_job():
    """15분마다 실행되는 GDELT 데이터 업데이트 작업"""
    try:
        logger.info("Starting GDELT data update...")
        result = gdelt_backend.update_gdelt_data()
        if result.get('error'):
            logger.error(f"GDELT update error: {result['error']}")
        else:
            if result.get('downloaded'):
                logger.info(f"GDELT file downloaded: {result.get('file_path')}")
            if result.get('cleaned_dirs', 0) > 0:
                logger.info(f"Cleaned up {result['cleaned_dirs']} old directories")
    except Exception as e:
        logger.error(f"Error in GDELT update job: {e}", exc_info=True)


def update_news_intelligence_job():
    """1시간마다 실행되는 뉴스 인텔리전스 수집 작업"""
    try:
        logger.info("Starting News Intelligence collection...")
        from news_intelligence.collectors import NewsCollectorManager
        from news_intelligence.models import NewsArticle, get_session
        
        # Run collection (fast, no blocking)
        manager = NewsCollectorManager()
        result = manager.run_collection()
        
        new_count = result.get('new_articles', 0)
        logger.info(f"News collection completed: {new_count} new articles")
        
        # Start background analysis if new articles found
        if new_count > 0:
            import threading
            analysis_thread = threading.Thread(
                target=_background_analysis_job,
                name="NewsAnalysisThread",
                daemon=True
            )
            analysis_thread.start()
            logger.info("Background analysis started")
            
    except Exception as e:
        logger.error(f"Error in News Intelligence job: {e}", exc_info=True)


def update_kcci_job():
    """매주 월요일 14:30에 실행되는 KCCI 수집 작업"""
    try:
        logger.info("Starting KCCI data collection...")
        from kcci.collector import collect_kcci_and_save
        
        result = collect_kcci_and_save()
        
        if result.get('success'):
            logger.info(f"KCCI collection completed: week_date={result.get('week_date')}, "
                       f"comprehensive={result.get('comprehensive', {}).get('current_index')}")
        else:
            logger.error(f"KCCI collection failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error in KCCI collection job: {e}", exc_info=True)

def _background_analysis_job():
    """
    백그라운드에서 실행되는 뉴스 분석 작업
    
    최적화 전략:
    1. 규칙 기반 우선 처리 (빠름, API 비용 없음)
    2. 불확실한 기사만 AI 배치 처리
    3. 서버 성능에 영향 없도록 비동기 처리
    """
    try:
        from news_intelligence.analyzer import NewsAnalyzer
        from news_intelligence.models import NewsArticle, get_session
        import time
        
        logger.info("Background analysis job started")
        start_time = time.time()
        
        session = get_session()
        try:
            # Get unprocessed articles
            articles = session.query(NewsArticle).filter(
                NewsArticle.category.is_(None)
            ).limit(100).all()  # Process up to 100 articles per run
            
            if not articles:
                logger.info("No articles to analyze")
                return
            
            logger.info(f"Analyzing {len(articles)} articles (optimized batch mode)...")
            
            # Initialize analyzer
            analyzer = NewsAnalyzer()
            analyzer.reset_stats()
            
            # Prepare articles for batch analysis
            article_dicts = [
                {
                    'id': a.id,
                    'title': a.title,
                    'content_summary': a.content_summary
                }
                for a in articles
            ]
            
            # Run optimized batch analysis (rule-based first + AI for uncertain)
            analyzed = analyzer.analyze_batch(article_dicts)
            
            # Update database
            for article_data in analyzed:
                article = next((a for a in articles if a.id == article_data['id']), None)
                if article:
                    article.category = article_data.get('category', 'ETC')
                    article.country_tags = article_data.get('country_tags', [])
                    article.keywords = article_data.get('keywords', [])
                    article.is_crisis = article_data.get('is_crisis', False)
            
            session.commit()
            
            # Log statistics
            elapsed = time.time() - start_time
            stats = analyzer.get_stats()
            logger.info(
                f"Analysis completed in {elapsed:.1f}s: "
                f"{stats['total_analyzed']} articles, "
                f"Rule-based: {stats['rule_based_count']} ({stats['ai_reduction_percent']}% AI saved), "
                f"AI batches: {stats['batch_count']}"
            )
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error in background analysis job: {e}", exc_info=True)


# 서버 시작 시 즉시 한 번 실행 (초기 데이터 다운로드)
# 그리고 15분마다 실행
scheduler.add_job(
    func=update_gdelt_data_job,
    trigger=IntervalTrigger(minutes=15),
    id='gdelt_update_job',
    name='Update GDELT data every 15 minutes',
    replace_existing=True
)

# News Intelligence: 1시간마다 실행
scheduler.add_job(
    func=update_news_intelligence_job,
    trigger=IntervalTrigger(hours=1),
    id='news_intelligence_job',
    name='Collect news every 1 hour',
    replace_existing=True
)

# KCCI: 매주 월요일 14:30 KST (05:30 UTC)에 실행
scheduler.add_job(
    func=update_kcci_job,
    trigger=CronTrigger(day_of_week='mon', hour=5, minute=30),  # UTC 기준
    id='kcci_collection_job',
    name='Collect KCCI data every Monday at 14:30 KST',
    replace_existing=True
)

# 스케줄러 시작
scheduler.start()


# ==========================================
# QUOTE BACKEND MANAGEMENT
# ==========================================

def start_quote_backend():
    """
    Start quote_backend FastAPI server as a subprocess
    """
    global quote_backend_process
    
    quote_backend_dir = BASE_DIR / 'quote_backend'
    quote_backend_main = quote_backend_dir / 'main.py'
    
    if not quote_backend_main.exists():
        logger.warning(f"quote_backend not found at {quote_backend_main}")
        return None
    
    try:
        # Check if port 8001 is already in use
        import socket
        import time
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8001))
        sock.close()
        
        if result == 0:
            logger.info("Quote Backend already running on port 8001")
            return None
        
        # Start quote_backend as subprocess
        logger.info("Starting Quote Backend on port 8001...")
        
        # Use the same Python interpreter
        python_exe = sys.executable
        
        # Log file for Quote Backend output
        log_file = BASE_DIR / 'quote_backend' / 'server.log'
        
        # Start subprocess with proper flags for Windows
        if sys.platform == 'win32':
            # Open log file for writing
            log_handle = open(log_file, 'w')
            quote_backend_process = subprocess.Popen(
                [python_exe, str(quote_backend_main)],
                cwd=str(quote_backend_dir),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            log_handle = open(log_file, 'w')
            quote_backend_process = subprocess.Popen(
                [python_exe, str(quote_backend_main)],
                cwd=str(quote_backend_dir),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
        
        # Wait for the server to start (uvicorn needs a moment)
        max_wait = 10
        for i in range(max_wait):
            time.sleep(1)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8001))
            sock.close()
            
            if result == 0:
                logger.info(f"Quote Backend started successfully (PID: {quote_backend_process.pid})")
                return quote_backend_process
        
        # If we get here, server didn't start
        logger.warning(f"Quote Backend may not have started properly. Check {log_file}")
        return quote_backend_process
        
    except Exception as e:
        logger.error(f"Failed to start Quote Backend: {e}")
        return None


def stop_quote_backend():
    """
    Stop the quote_backend subprocess
    """
    global quote_backend_process
    
    if quote_backend_process:
        try:
            logger.info("Stopping Quote Backend...")
            
            if sys.platform == 'win32':
                # Windows: terminate the process
                quote_backend_process.terminate()
            else:
                # Unix: send SIGTERM to process group
                os.killpg(os.getpgid(quote_backend_process.pid), signal.SIGTERM)
            
            quote_backend_process.wait(timeout=5)
            logger.info("Quote Backend stopped successfully")
            
        except subprocess.TimeoutExpired:
            logger.warning("Quote Backend did not stop gracefully, forcing kill...")
            quote_backend_process.kill()
        except Exception as e:
            logger.error(f"Error stopping Quote Backend: {e}")
        finally:
            quote_backend_process = None


def run_quote_seed_if_needed():
    """
    Run seed_data.py if the database is empty
    """
    quote_backend_dir = BASE_DIR / 'quote_backend'
    quote_db = quote_backend_dir / 'quote.db'
    seed_script = quote_backend_dir / 'seed_data.py'
    
    # If DB doesn't exist or is very small, run seed
    if not quote_db.exists() or quote_db.stat().st_size < 10000:
        if seed_script.exists():
            logger.info("Running quote_backend seed_data.py...")
            try:
                result = subprocess.run(
                    [sys.executable, str(seed_script)],
                    cwd=str(quote_backend_dir),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    logger.info("Quote Backend seed data initialized successfully")
                else:
                    logger.warning(f"Seed data warning: {result.stderr}")
            except Exception as e:
                logger.warning(f"Failed to run seed_data.py: {e}")


# 애플리케이션 종료 시 정리
def cleanup():
    """Cleanup on application exit"""
    scheduler.shutdown()
    stop_quote_backend()

atexit.register(cleanup)


if __name__ == '__main__':
    print("="*60)
    print("  AAL - All About Logistics Server")
    print("="*60)
    print()
    
    # Initialize seed data if needed
    run_quote_seed_if_needed()
    
    # Start Quote Backend (FastAPI on port 8001)
    start_quote_backend()
    
    print()
    print("  [Main Server]     http://localhost:5000  (Flask)")
    print("  [Quote Backend]   http://localhost:8001  (FastAPI)")
    print()
    print(f"  BASE_DIR: {BASE_DIR.resolve()}")
    print(f"  GDELT auto-update: Every 15 minutes")
    print(f"  News Intelligence: Every 1 hour")
    print(f"  KCCI: Every Monday at 14:30 KST (05:30 UTC)")
    print()
    print("="*60)

    # 등록된 라우트 출력 (디버깅용)
    print("\nRegistered Shipping Indices Routes:")
    shipping_routes = [rule for rule in app.url_map.iter_rules() if rule.endpoint.startswith('shipping_indices')]
    if shipping_routes:
        for rule in shipping_routes:
            print(f"  [OK] {rule.rule} -> {rule.endpoint}")
    else:
        print("  [X] No shipping_indices routes found!")
    print()
    
    # 서버 시작 시 즉시 GDELT 데이터 업데이트 시도
    try:
        update_gdelt_data_job()
    except Exception as e:
        logger.warning(f"Initial GDELT update failed: {e}")
    
    # 서버가 시작된 후 뉴스 수집을 시작하기 위한 함수
    def start_news_collection_after_server_start():
        """서버가 시작된 후 뉴스 수집 시작"""
        import threading
        import time
        import socket
        
        # 서버가 포트 5000에서 리스닝할 때까지 대기
        logger.info("Waiting for server to be ready on localhost:5000...")
        max_wait = 30  # 최대 30초 대기
        wait_time = 0
        server_ready = False
        
        while wait_time < max_wait:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', 5000))
                sock.close()
                if result == 0:
                    server_ready = True
                    logger.info("[OK] Server is ready on localhost:5000")
                    break
            except Exception:
                pass
            time.sleep(0.5)
            wait_time += 0.5
        
        if server_ready:
            # 서버가 완전히 초기화될 때까지 약간의 추가 대기
            time.sleep(1)
            try:
                logger.info("Starting News Intelligence collection after server startup...")
                update_news_intelligence_job()
            except Exception as e:
                logger.warning(f"Initial News Intelligence collection failed: {e}")
        else:
            logger.warning("[WARN] Server may not be ready, skipping initial news collection")
    
    # 서버 시작 후 뉴스 수집을 시작하는 스레드 시작
    import threading
    news_thread = threading.Thread(target=start_news_collection_after_server_start, daemon=True)
    news_thread.start()
    
    # Start Flask server (use_reloader=False to prevent double subprocess)
    app.run(port=5000, debug=True, use_reloader=False)
