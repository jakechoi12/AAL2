"""
GDELT API Blueprint
글로벌 긴급 알림 API 라우트

Endpoints:
- /api/global-alerts - 글로벌 긴급 알림 조회
- /api/global-alerts/stats/by-country - 국가별 통계
- /api/global-alerts/stats/by-category - 카테고리별 통계
- /api/global-alerts/trends - 트렌드 분석
- /api/global-alerts/cache/clear - 캐시 초기화
"""

import logging
from flask import Blueprint, request, jsonify

import gdelt_backend

logger = logging.getLogger(__name__)

# Flask Blueprint
gdelt_bp = Blueprint('gdelt', __name__)


@gdelt_bp.route('/api/global-alerts', methods=['GET'])
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


@gdelt_bp.route('/api/global-alerts/stats/by-country', methods=['GET'])
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


@gdelt_bp.route('/api/global-alerts/stats/by-category', methods=['GET'])
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


@gdelt_bp.route('/api/global-alerts/trends', methods=['GET'])
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


@gdelt_bp.route('/api/global-alerts/cache/clear', methods=['POST'])
def clear_cache():
    """캐시를 초기화합니다."""
    try:
        gdelt_backend.clear_cache()
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

