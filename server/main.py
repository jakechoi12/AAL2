from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import logging
import bok_backend  # Import the BOK backend module
import gdelt_backend  # Import the GDELT backend module

# Load environment variables
load_dotenv()

# Determine base directory (parent of server directory)
BASE_DIR = Path(__file__).parent.parent

# Flask 앱 초기화
# static_folder를 설정하지 않아서 기본 라우트와 충돌하지 않도록 함
app = Flask(__name__)
CORS(app) # Enable CORS for all routes (for development)

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
    """
    threshold = request.args.get('threshold', -5.0, type=float)
    max_alerts = request.args.get('max_alerts', 1000, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        # 날짜 범위가 지정된 경우
        if start_date and end_date:
            result = gdelt_backend.get_alerts_by_date_range(
                start_date=start_date,
                end_date=end_date,
                goldstein_threshold=threshold,
                max_alerts=max_alerts
            )
        else:
            # 최신 데이터 가져오기
            result = gdelt_backend.get_critical_alerts(
                goldstein_threshold=threshold,
                max_alerts=max_alerts
            )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'alerts': [],
            'count': 0
        }), 500

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

# 서버 시작 시 즉시 한 번 실행 (초기 데이터 다운로드)
# 그리고 15분마다 실행
scheduler.add_job(
    func=update_gdelt_data_job,
    trigger=IntervalTrigger(minutes=15),
    id='gdelt_update_job',
    name='Update GDELT data every 15 minutes',
    replace_existing=True
)

# 스케줄러 시작
scheduler.start()

# 애플리케이션 종료 시 스케줄러 종료
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    print("="*50)
    print("Starting Flask Server on http://localhost:5000")
    print(f"BASE_DIR: {BASE_DIR.resolve()}")
    print(f"HTML file exists: {(BASE_DIR / 'frontend' / 'ai_studio_code_F2.html').exists()}")
    print("GDELT auto-update: Every 15 minutes")
    print("GDELT data path:", gdelt_backend.get_gdelt_base_path())
    print("="*50)
    
    # 서버 시작 시 즉시 GDELT 데이터 업데이트 시도
    try:
        update_gdelt_data_job()
    except Exception as e:
        logger.warning(f"Initial GDELT update failed: {e}")
    
    app.run(port=5000, debug=True)
