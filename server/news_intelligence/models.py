"""
Database Models for News Intelligence Service
- NewsArticle: Stores individual news items
- CollectionLog: Tracks collection job execution history
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    Float, JSON, Enum, Index, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum
import os

Base = declarative_base()


class NewsStatus(enum.Enum):
    """News article status"""
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class NewsType(enum.Enum):
    """News type classification"""
    KR = "KR"       # Korean news
    GLOBAL = "GLOBAL"  # Global/International news


class NewsCategory(enum.Enum):
    """News category for logistics domain"""
    CRISIS = "Crisis"       # Strikes, accidents, conflicts - Critical alerts
    OCEAN = "Ocean"         # Maritime/Shipping news
    AIR = "Air"             # Air cargo/aviation news
    INLAND = "Inland"       # Land transportation, warehousing
    ECONOMY = "Economy"     # Economy, freight rates, demand
    ETC = "ETC"             # Other/miscellaneous


class NewsArticle(Base):
    """
    News Article Model
    
    Stores collected news with AI-analyzed metadata.
    Primary deduplication is based on URL.
    """
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core content
    title = Column(String(500), nullable=False)
    content_summary = Column(Text, nullable=True)  # AI-generated or extracted summary
    source_name = Column(String(100), nullable=False)  # e.g., "FreightWaves", "물류신문"
    url = Column(String(1000), nullable=False, unique=True)  # Deduplication key
    
    # Time fields (all in UTC)
    published_at_utc = Column(DateTime, nullable=True)  # Original publish time
    collected_at_utc = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Classification
    news_type = Column(String(20), nullable=False)  # KR or GLOBAL
    category = Column(String(50), nullable=True)  # Crisis, Ocean, Air, etc.
    is_crisis = Column(Boolean, default=False)  # Quick flag for critical alerts
    
    # Geographic data (for map visualization)
    country_tags = Column(JSON, nullable=True)  # List of country codes, e.g., ["US", "KR", "DE"]
    
    # GDELT-specific metrics (optional, only for GDELT sources)
    goldstein_scale = Column(Float, nullable=True)  # -10 to +10
    avg_tone = Column(Float, nullable=True)  # Average sentiment tone
    num_mentions = Column(Integer, nullable=True)  # Number of mentions
    num_sources = Column(Integer, nullable=True)  # Number of sources
    num_articles = Column(Integer, nullable=True)  # Number of related articles
    
    # AI-extracted keywords for word cloud
    keywords = Column(JSON, nullable=True)  # List of keywords, e.g., ["strike", "port", "delay"]
    
    # Status management
    status = Column(String(20), default='ACTIVE')  # ACTIVE or ARCHIVED
    
    # Grouping for similar articles
    group_id = Column(String(100), nullable=True)  # For grouping duplicate/similar articles
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_news_status_published', 'status', 'published_at_utc'),
        Index('idx_news_status_collected', 'status', 'collected_at_utc'),
        Index('idx_news_type_category', 'news_type', 'category'),
        Index('idx_news_is_crisis', 'is_crisis'),
        Index('idx_news_url', 'url'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'id': self.id,
            'title': self.title,
            'content_summary': self.content_summary,
            'source_name': self.source_name,
            'url': self.url,
            'published_at_utc': self.published_at_utc.isoformat() if self.published_at_utc else None,
            'collected_at_utc': self.collected_at_utc.isoformat() if self.collected_at_utc else None,
            'news_type': self.news_type,
            'category': self.category or 'ETC',
            'is_crisis': self.is_crisis,
            'country_tags': self.country_tags or [],
            'goldstein_scale': self.goldstein_scale,
            'avg_tone': self.avg_tone,
            'num_mentions': self.num_mentions,
            'num_sources': self.num_sources,
            'num_articles': self.num_articles,
            'keywords': self.keywords or [],
            'status': self.status,
        }


class CollectionLog(Base):
    """
    Collection Job Log
    
    Tracks each news collection job execution for monitoring.
    """
    __tablename__ = 'collection_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Execution time
    executed_at_utc = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Results
    total_collected = Column(Integer, default=0)
    kr_news_count = Column(Integer, default=0)
    global_news_count = Column(Integer, default=0)
    new_articles_count = Column(Integer, default=0)  # Actually new (not duplicates)
    duplicate_count = Column(Integer, default=0)
    
    # Status
    is_success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Duration
    duration_seconds = Column(Float, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'executed_at_utc': self.executed_at_utc.isoformat() if self.executed_at_utc else None,
            'total_collected': self.total_collected,
            'kr_news_count': self.kr_news_count,
            'global_news_count': self.global_news_count,
            'new_articles_count': self.new_articles_count,
            'duplicate_count': self.duplicate_count,
            'is_success': self.is_success,
            'error_message': self.error_message,
            'duration_seconds': self.duration_seconds,
        }


# Database connection utilities
_cached_db_url = None

def get_database_url():
    """Get database URL from environment or use SQLite fallback"""
    global _cached_db_url
    
    if _cached_db_url is not None:
        return _cached_db_url
    
    # Try PostgreSQL first
    postgres_url = os.getenv('DATABASE_URL')
    if postgres_url and postgres_url.startswith('postgresql'):
        try:
            import psycopg2
            _cached_db_url = postgres_url
            return _cached_db_url
        except ImportError:
            pass  # psycopg2 not available, fallback to SQLite
    
    # Fallback to SQLite for development
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _cached_db_url = f"sqlite:///{os.path.join(base_dir, 'news_intelligence.db')}"
    return _cached_db_url


def init_database():
    """Initialize database and create tables"""
    engine = create_engine(get_database_url(), echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Get a new database session"""
    engine = create_engine(get_database_url(), echo=False)
    Session = sessionmaker(bind=engine)
    return Session()

