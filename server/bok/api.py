"""
BOK (Bank of Korea) API Blueprint
한국은행 경제통계시스템 API 라우트

Endpoints:
- /api/bok/stats - 통계 데이터 조회
- /api/bok/search-codes - 통계표 코드 검색
- /api/bok/item-list - 항목 목록 조회
- /api/bok/cache/stats - 캐시 통계
- /api/bok/cache/clear - 캐시 초기화
- /api/market/indices - 시장 지수 조회
- /api/market/indices/multi - 다중 시장 지수 조회
- /api/market/indices/stats - 시장 지수 통계
- /api/market/categories - 카테고리 정보
"""

import os
import logging
from flask import Blueprint, request, jsonify
import requests

import bok_backend
from config import ECOS_API_KEY, ECOS_API_BASE_URL

logger = logging.getLogger(__name__)

# Flask Blueprint
bok_bp = Blueprint('bok', __name__)


# ============================================================
# BOK Statistics API
# ============================================================

@bok_bp.route('/api/bok/stats', methods=['GET'])
def get_bok_stats():
    """BOK 통계 데이터 조회"""
    stat_code = request.args.get('statCode')
    item_code = request.args.get('itemCode')
    cycle = request.args.get('cycle', 'D')  # Default to Daily
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    
    if not all([stat_code, item_code, start_date, end_date]):
        return jsonify({"error": "Missing parameters: statCode, itemCode, startDate, endDate are required"}), 400

    result = bok_backend.get_bok_statistics(stat_code, item_code, cycle, start_date, end_date)
    
    if "error" in result:
        return jsonify(result), 500
        
    return jsonify(result)


@bok_bp.route('/api/bok/search-codes', methods=['GET'])
def search_statistical_codes():
    """
    통계표 코드를 검색합니다.
    
    파라미터:
    - statCode: 통계표 코드 (부분 검색 가능, 선택)
    - statName: 통계표명 (부분 검색 가능, 선택)
    - startIndex: 요청 시작 건수 (기본값: 1)
    - endIndex: 요청 종료 건수 (기본값: 100, 최대 1000)
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


@bok_bp.route('/api/bok/item-list', methods=['GET'])
def get_statistic_item_list():
    """
    특정 통계표의 항목 목록을 조회합니다.
    
    파라미터:
    - statCode: 통계표 코드 (필수)
    - startIndex: 요청 시작 건수 (기본값: 1)
    - endIndex: 요청 종료 건수 (기본값: 100, 최대 1000)
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


@bok_bp.route('/api/bok/cache/stats', methods=['GET'])
def get_bok_cache_stats():
    """BOK API 캐시 통계를 반환합니다."""
    try:
        stats = bok_backend.get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bok_bp.route('/api/bok/cache/clear', methods=['POST'])
def clear_bok_cache():
    """BOK API 캐시를 초기화합니다."""
    try:
        bok_backend.clear_api_cache()
        return jsonify({'message': 'BOK API cache cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing BOK cache: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================
# Market Indices API
# ============================================================

@bok_bp.route('/api/market/indices', methods=['GET'])
def get_market_indices():
    """시장 지수 조회"""
    category = request.args.get('type', 'exchange')  # default to exchange
    item_code = request.args.get('itemCode')  # Optional: specific item within category
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    cycle = request.args.get('cycle')  # Optional: override default cycle
    stat_code = request.args.get('statCode')  # Optional: for inflation category
    
    if not all([category, start_date, end_date]):
        return jsonify({"error": "Missing parameters: type, startDate, endDate"}), 400

    result = bok_backend.get_market_index(category, start_date, end_date, item_code=item_code, cycle=cycle, stat_code=stat_code)
    return jsonify(result)


@bok_bp.route('/api/market/indices/multi', methods=['GET'])
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


@bok_bp.route('/api/market/categories', methods=['GET'])
def get_market_categories():
    """
    Get information about available categories and their items.
    """
    category = request.args.get('category')
    result = bok_backend.get_category_info(category=category)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@bok_bp.route('/api/market/indices/stats', methods=['GET'])
def get_market_indices_stats():
    """
    시장 지수 데이터의 통계 정보를 반환합니다 (환율, 물가, GDP 등).
    """
    category = request.args.get('type', 'exchange')
    item_code = request.args.get('itemCode')
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


# ============================================================
# Legacy Exchange Rates API (keeping for backwards compatibility)
# ============================================================

@bok_bp.route('/api/exchange-rates', methods=['GET'])
def get_exchange_rates():
    """Legacy API for exchange rates"""
    item_code = request.args.get('itemCode')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    if not all([item_code, start_date, end_date]):
        return jsonify({"error": "Missing parameters"}), 400

    if not ECOS_API_KEY:
        return jsonify({"error": "Server configuration error: API Key missing"}), 500

    # Format: /StatisticSearch/KEY/json/kr/1/10/731Y001/D/START/END/ITEM
    url = f"{ECOS_API_BASE_URL}/StatisticSearch/{ECOS_API_KEY}/json/kr/1/10/731Y001/D/{start_date}/{end_date}/{item_code}"

    try:
        response = requests.get(url)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

