"""
Static File Routes Blueprint
정적 파일 서빙을 위한 라우트

Endpoints:
- / - 메인 페이지 (ai_studio_code_F2.html)
- /css/<path> - CSS 파일
- /js/<path> - JavaScript 파일
- /pages/<path> - HTML 페이지
- /api/config/google-maps-key - Google Maps API 키
- /api/news - 뉴스 Mock 데이터
- /api/logistics - 물류 지수 Mock 데이터
"""

import logging
from flask import Blueprint, send_from_directory, send_file, jsonify

from config import BASE_DIR, FRONTEND_DIR, GOOGLE_MAPS_API_KEY

logger = logging.getLogger(__name__)

# Flask Blueprint
static_bp = Blueprint('static', __name__)


# ============================================================
# Static File Routes
# ============================================================

@static_bp.route('/')
def serve_index():
    """frontend/ai_studio_code_F2.html을 메인 페이지로 서빙"""
    f2_file = FRONTEND_DIR / 'ai_studio_code_F2.html'
    if f2_file.exists():
        return send_file(str(f2_file))
    else:
        return "File not found: frontend/ai_studio_code_F2.html", 404


@static_bp.route('/css/<path:filename>')
def serve_css(filename):
    """CSS 파일 서빙"""
    return send_from_directory(str(FRONTEND_DIR / 'css'), filename)


@static_bp.route('/js/<path:filename>')
def serve_js(filename):
    """JavaScript 파일 서빙"""
    return send_from_directory(str(FRONTEND_DIR / 'js'), filename)


@static_bp.route('/pages/<path:filename>')
def serve_pages(filename):
    """Pages 폴더 파일 서빙 (quotation.html 등)"""
    return send_from_directory(str(FRONTEND_DIR / 'pages'), filename)


# ============================================================
# Config API Routes
# ============================================================

@static_bp.route('/api/config/google-maps-key', methods=['GET'])
def get_google_maps_key():
    """
    Google Maps API 키를 반환합니다.
    클라이언트에서 환경 변수로부터 안전하게 API 키를 가져올 수 있도록 합니다.
    """
    if not GOOGLE_MAPS_API_KEY:
        return jsonify({"error": "Google Maps API key is not configured"}), 500
    return jsonify({"apiKey": GOOGLE_MAPS_API_KEY})


# ============================================================
# Mock Data API Routes (News, Logistics)
# ============================================================

@static_bp.route('/api/news', methods=['GET'])
def get_news():
    """Mock Data for news"""
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


@static_bp.route('/api/logistics', methods=['GET'])
def get_logistics_indices():
    """Mock Data for Logistics Indices"""
    return jsonify({
        "SCFI": {"value": "2300.50", "change": "+12.5", "trend": "up"},
        "BDI": {"value": "1500.00", "change": "-5.0", "trend": "down"}
    })

