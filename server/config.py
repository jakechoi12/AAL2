"""
AAL Server Configuration
모든 설정값을 중앙에서 관리합니다.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================
# PATH CONFIGURATION
# ============================================================
# Base directory (parent of server directory)
BASE_DIR = Path(__file__).parent.parent
SERVER_DIR = Path(__file__).parent

# Frontend paths
FRONTEND_DIR = BASE_DIR / 'frontend'
FRONTEND_CSS_DIR = FRONTEND_DIR / 'css'
FRONTEND_JS_DIR = FRONTEND_DIR / 'js'
FRONTEND_PAGES_DIR = FRONTEND_DIR / 'pages'

# Quote backend paths
QUOTE_BACKEND_DIR = BASE_DIR / 'quote_backend'

# ============================================================
# API KEYS
# ============================================================
ECOS_API_KEY = os.getenv("ECOS_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ============================================================
# EXTERNAL API URLS
# ============================================================
ECOS_API_BASE_URL = "http://ecos.bok.or.kr/api"

# ============================================================
# SERVER CONFIGURATION
# ============================================================
FLASK_PORT = 5000
QUOTE_BACKEND_PORT = 8001
DEBUG_MODE = True

# Disable caching for development
SEND_FILE_MAX_AGE_DEFAULT = 0

# ============================================================
# SCHEDULER CONFIGURATION
# ============================================================
# GDELT: 15분마다
GDELT_UPDATE_INTERVAL_MINUTES = 15

# News Intelligence: 1시간마다
NEWS_INTELLIGENCE_INTERVAL_HOURS = 1

# KCCI: 매주 월요일 14:30 KST (05:30 UTC)
KCCI_COLLECTION_DAY = 'mon'
KCCI_COLLECTION_HOUR_UTC = 5
KCCI_COLLECTION_MINUTE = 30

# ============================================================
# LOGGING CONFIGURATION
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

