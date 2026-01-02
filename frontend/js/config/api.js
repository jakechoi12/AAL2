/**
 * API Configuration
 * 백엔드 API 엔드포인트 설정
 */

// API Base URLs
const API_CONFIG = {
    // Main Flask Server
    MAIN_API_BASE: 'http://localhost:5000',
    
    // Quote Backend (FastAPI)
    QUOTE_API_BASE: 'http://localhost:8001',
    
    // Auth API
    AUTH_API_BASE: 'http://localhost:5000/api/auth',
    
    // Forwarder API  
    FORWARDER_API_BASE: 'http://localhost:8001/api/forwarder'
};

// Export for global use (if not using modules)
window.API_CONFIG = API_CONFIG;

// Convenience constants
const MAIN_API_BASE = API_CONFIG.MAIN_API_BASE;
const QUOTE_API_BASE = API_CONFIG.QUOTE_API_BASE;
