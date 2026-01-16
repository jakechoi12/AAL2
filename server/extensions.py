"""
Flask Extensions
Flask 확장 모듈들의 초기화를 관리합니다.
"""

from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler

# ============================================================
# CORS Extension
# ============================================================
cors = CORS()

# ============================================================
# Background Scheduler
# ============================================================
scheduler = BackgroundScheduler(daemon=True)


def init_extensions(app):
    """
    Flask 앱에 확장 모듈들을 초기화합니다.
    
    Args:
        app: Flask application instance
    """
    # Initialize CORS
    cors.init_app(app)
    
    # Disable caching for development
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Add no-cache headers
    @app.after_request
    def add_no_cache_headers(response):
        """Add no-cache headers to all responses for development"""
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    return app

