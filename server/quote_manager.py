"""
Quote Backend Manager
Quote Backend (FastAPI) 서브프로세스 관리 모듈

기능:
- Quote Backend 서버 시작/종료
- Seed 데이터 초기화
- 상태 확인
"""

import os
import sys
import signal
import socket
import subprocess
import time
import logging

from config import BASE_DIR, QUOTE_BACKEND_DIR, QUOTE_BACKEND_PORT

logger = logging.getLogger(__name__)

# Global variable to store quote_backend process
_quote_backend_process = None


def is_port_in_use(port: int, host: str = 'localhost') -> bool:
    """포트가 사용 중인지 확인합니다."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    finally:
        sock.close()


def start_quote_backend() -> subprocess.Popen:
    """
    Quote Backend FastAPI 서버를 서브프로세스로 시작합니다.
    
    Returns:
        subprocess.Popen: 시작된 프로세스 객체 또는 None
    """
    global _quote_backend_process
    
    quote_backend_main = QUOTE_BACKEND_DIR / 'main.py'
    
    if not quote_backend_main.exists():
        logger.warning(f"quote_backend not found at {quote_backend_main}")
        return None
    
    try:
        # Check if port is already in use
        if is_port_in_use(QUOTE_BACKEND_PORT):
            logger.info(f"Quote Backend already running on port {QUOTE_BACKEND_PORT}")
            return None
        
        # Start quote_backend as subprocess
        logger.info(f"Starting Quote Backend on port {QUOTE_BACKEND_PORT}...")
        
        # Use the same Python interpreter
        python_exe = sys.executable
        
        # Log file for Quote Backend output
        log_file = QUOTE_BACKEND_DIR / 'server.log'
        
        # Start subprocess with proper flags for Windows
        if sys.platform == 'win32':
            # Open log file for writing
            log_handle = open(log_file, 'w')
            _quote_backend_process = subprocess.Popen(
                [python_exe, str(quote_backend_main)],
                cwd=str(QUOTE_BACKEND_DIR),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            log_handle = open(log_file, 'w')
            _quote_backend_process = subprocess.Popen(
                [python_exe, str(quote_backend_main)],
                cwd=str(QUOTE_BACKEND_DIR),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
        
        # Wait for the server to start (uvicorn needs a moment)
        max_wait = 10
        for i in range(max_wait):
            time.sleep(1)
            if is_port_in_use(QUOTE_BACKEND_PORT):
                logger.info(f"Quote Backend started successfully (PID: {_quote_backend_process.pid})")
                return _quote_backend_process
        
        # If we get here, server didn't start
        logger.warning(f"Quote Backend may not have started properly. Check {log_file}")
        return _quote_backend_process
        
    except Exception as e:
        logger.error(f"Failed to start Quote Backend: {e}")
        return None


def stop_quote_backend():
    """Quote Backend 서브프로세스를 종료합니다."""
    global _quote_backend_process
    
    if _quote_backend_process:
        try:
            logger.info("Stopping Quote Backend...")
            
            if sys.platform == 'win32':
                # Windows: terminate the process
                _quote_backend_process.terminate()
            else:
                # Unix: send SIGTERM to process group
                os.killpg(os.getpgid(_quote_backend_process.pid), signal.SIGTERM)
            
            _quote_backend_process.wait(timeout=5)
            logger.info("Quote Backend stopped successfully")
            
        except subprocess.TimeoutExpired:
            logger.warning("Quote Backend did not stop gracefully, forcing kill...")
            _quote_backend_process.kill()
        except Exception as e:
            logger.error(f"Error stopping Quote Backend: {e}")
        finally:
            _quote_backend_process = None


def run_quote_seed_if_needed():
    """데이터베이스가 비어있으면 seed_data.py를 실행합니다."""
    quote_db = QUOTE_BACKEND_DIR / 'quote.db'
    seed_script = QUOTE_BACKEND_DIR / 'seed_data.py'
    
    # If DB doesn't exist or is very small, run seed
    if not quote_db.exists() or quote_db.stat().st_size < 10000:
        if seed_script.exists():
            logger.info("Running quote_backend seed_data.py...")
            try:
                result = subprocess.run(
                    [sys.executable, str(seed_script)],
                    cwd=str(QUOTE_BACKEND_DIR),
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


def get_quote_backend_status() -> dict:
    """Quote Backend 상태를 반환합니다."""
    return {
        'running': is_port_in_use(QUOTE_BACKEND_PORT),
        'port': QUOTE_BACKEND_PORT,
        'process_alive': _quote_backend_process is not None and _quote_backend_process.poll() is None
    }

