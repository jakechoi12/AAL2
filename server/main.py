"""
AAL - All About Logistics Server
메인 Flask 애플리케이션 엔트리포인트

이 파일은 앱 팩토리 패턴을 사용하여 Flask 앱을 초기화하고
모든 Blueprint를 등록합니다.
"""

import atexit
import logging
from flask import Flask
from dotenv import load_dotenv

# Load environment variables FIRST before importing modules that need them
load_dotenv()

# Import configuration
from config import BASE_DIR, FLASK_PORT, QUOTE_BACKEND_PORT, DEBUG_MODE

# Import extensions
from extensions import init_extensions

# Import scheduler
from scheduler import (
    init_scheduler,
    run_initial_jobs,
    start_news_collection_after_server_ready,
    shutdown_scheduler
)

# Import quote backend manager
from quote_manager import (
    start_quote_backend,
    stop_quote_backend,
    run_quote_seed_if_needed
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """
    Flask 앱 팩토리
    
    Returns:
        Flask: 초기화된 Flask 앱 인스턴스
    """
    app = Flask(__name__)
    
    # Initialize extensions (CORS, etc.)
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    return app


def register_blueprints(app: Flask):
    """
    모든 Blueprint를 Flask 앱에 등록합니다.
    
    Args:
        app: Flask application instance
    """
    # === External Module Blueprints ===
    from report.api import report_bp
    from news_intelligence.api import news_bp
    from kcci.api import kcci_bp
    from auth.auth_backend import auth_bp
    
    # Shipping Indices Blueprint (with error handling)
    try:
        from shipping_indices.api import shipping_bp
        print("[OK] Shipping Indices module imported successfully")
    except ImportError as e:
        print(f"[ERROR] ImportError: Failed to import shipping_indices module")
        print(f"   Error: {e}")
        print("   Please install: pip install pandas xlrd")
        from flask import Blueprint
        shipping_bp = Blueprint('shipping_indices', __name__, url_prefix='/api/shipping-indices')
    
    # === Internal Module Blueprints ===
    from bok.api import bok_bp
    from ai.api import ai_bp
    from gdelt.api import gdelt_bp
    from static_routes import static_bp
    
    # Register all blueprints
    try:
        app.register_blueprint(report_bp)
        app.register_blueprint(news_bp)
        app.register_blueprint(kcci_bp)
        app.register_blueprint(shipping_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(bok_bp)
        app.register_blueprint(ai_bp)
        app.register_blueprint(gdelt_bp)
        app.register_blueprint(static_bp)
        print("[OK] All blueprints registered successfully")
    except Exception as e:
        print(f"[ERROR] Error registering blueprints: {e}")
        import traceback
        traceback.print_exc()
    
    # Initialize Auth Database
    from auth.models import init_db as init_auth_db
    init_auth_db()


def cleanup():
    """애플리케이션 종료 시 정리 작업"""
    shutdown_scheduler()
    stop_quote_backend()


# Create the Flask application
app = create_app()

# Register cleanup on exit
atexit.register(cleanup)


if __name__ == '__main__':
    print("=" * 60)
    print("  AAL - All About Logistics Server")
    print("=" * 60)
    print()
    
    # Initialize seed data if needed
    run_quote_seed_if_needed()
    
    # Start Quote Backend (FastAPI on port 8001)
    start_quote_backend()
    
    # Initialize and start scheduler
    init_scheduler()
    
    print()
    print(f"  [Main Server]     http://localhost:{FLASK_PORT}  (Flask)")
    print(f"  [Quote Backend]   http://localhost:{QUOTE_BACKEND_PORT}  (FastAPI)")
    print()
    print(f"  BASE_DIR: {BASE_DIR.resolve()}")
    print(f"  GDELT auto-update: Every 15 minutes")
    print(f"  News Intelligence: Every 1 hour")
    print(f"  KCCI: Every Monday at 14:30 KST (05:30 UTC)")
    print()
    print("=" * 60)

    # 등록된 라우트 출력 (디버깅용)
    print("\nRegistered Shipping Indices Routes:")
    shipping_routes = [rule for rule in app.url_map.iter_rules() if rule.endpoint.startswith('shipping_indices')]
    if shipping_routes:
        for rule in shipping_routes:
            print(f"  [OK] {rule.rule} -> {rule.endpoint}")
    else:
        print("  [X] No shipping_indices routes found!")
    print()
    
    # Run initial jobs (GDELT update)
    run_initial_jobs()
    
    # Start news collection after server is ready
    start_news_collection_after_server_ready(FLASK_PORT)
    
    # Start Flask server (use_reloader=False to prevent double subprocess)
    app.run(port=FLASK_PORT, debug=DEBUG_MODE, use_reloader=False)
