"""
Background Scheduler Jobs
백그라운드 작업 스케줄러 설정 및 작업 정의

Jobs:
- GDELT 데이터 업데이트 (15분마다)
- News Intelligence 수집 (1시간마다)
- KCCI 수집 (매주 월요일 14:30 KST)
"""

import logging
import threading
import time

from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from extensions import scheduler
from config import (
    GDELT_UPDATE_INTERVAL_MINUTES,
    NEWS_INTELLIGENCE_INTERVAL_HOURS,
    KCCI_COLLECTION_DAY,
    KCCI_COLLECTION_HOUR_UTC,
    KCCI_COLLECTION_MINUTE
)

logger = logging.getLogger(__name__)


# ============================================================
# GDELT Update Job
# ============================================================

def update_gdelt_data_job():
    """15분마다 실행되는 GDELT 데이터 업데이트 작업"""
    try:
        import gdelt_backend
        
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


# ============================================================
# News Intelligence Job
# ============================================================

def update_news_intelligence_job():
    """1시간마다 실행되는 뉴스 인텔리전스 수집 작업"""
    try:
        logger.info("Starting News Intelligence collection...")
        from news_intelligence.collectors import NewsCollectorManager
        
        # Run collection (fast, no blocking)
        manager = NewsCollectorManager()
        result = manager.run_collection()
        
        new_count = result.get('new_articles', 0)
        logger.info(f"News collection completed: {new_count} new articles")
        
        # Start background analysis if new articles found
        if new_count > 0:
            analysis_thread = threading.Thread(
                target=_background_analysis_job,
                name="NewsAnalysisThread",
                daemon=True
            )
            analysis_thread.start()
            logger.info("Background analysis started")
            
    except Exception as e:
        logger.error(f"Error in News Intelligence job: {e}", exc_info=True)


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


# ============================================================
# KCCI Collection Job
# ============================================================

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


# ============================================================
# Scheduler Initialization
# ============================================================

def init_scheduler():
    """스케줄러를 초기화하고 작업을 등록합니다."""
    
    # GDELT: 15분마다 실행
    scheduler.add_job(
        func=update_gdelt_data_job,
        trigger=IntervalTrigger(minutes=GDELT_UPDATE_INTERVAL_MINUTES),
        id='gdelt_update_job',
        name='Update GDELT data every 15 minutes',
        replace_existing=True
    )
    
    # News Intelligence: 1시간마다 실행
    scheduler.add_job(
        func=update_news_intelligence_job,
        trigger=IntervalTrigger(hours=NEWS_INTELLIGENCE_INTERVAL_HOURS),
        id='news_intelligence_job',
        name='Collect news every 1 hour',
        replace_existing=True
    )
    
    # KCCI: 매주 월요일 14:30 KST (05:30 UTC)에 실행
    scheduler.add_job(
        func=update_kcci_job,
        trigger=CronTrigger(
            day_of_week=KCCI_COLLECTION_DAY, 
            hour=KCCI_COLLECTION_HOUR_UTC, 
            minute=KCCI_COLLECTION_MINUTE
        ),
        id='kcci_collection_job',
        name='Collect KCCI data every Monday at 14:30 KST',
        replace_existing=True
    )
    
    # 스케줄러 시작
    scheduler.start()
    
    logger.info("Scheduler initialized with jobs: GDELT (15min), News (1hr), KCCI (Mon 14:30 KST)")


def run_initial_jobs():
    """서버 시작 시 초기 작업을 실행합니다."""
    
    # 서버 시작 시 즉시 GDELT 데이터 업데이트 시도
    try:
        update_gdelt_data_job()
    except Exception as e:
        logger.warning(f"Initial GDELT update failed: {e}")


def start_news_collection_after_server_ready(port: int = 5000):
    """서버가 준비된 후 뉴스 수집을 시작합니다."""
    import socket
    
    def _wait_and_collect():
        # 서버가 포트에서 리스닝할 때까지 대기
        logger.info(f"Waiting for server to be ready on localhost:{port}...")
        max_wait = 30  # 최대 30초 대기
        wait_time = 0
        server_ready = False
        
        while wait_time < max_wait:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    server_ready = True
                    logger.info(f"[OK] Server is ready on localhost:{port}")
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
    news_thread = threading.Thread(target=_wait_and_collect, daemon=True)
    news_thread.start()


def shutdown_scheduler():
    """스케줄러를 종료합니다."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown complete")

