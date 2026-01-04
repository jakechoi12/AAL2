"""
Report & Insight - Data Models
SQLAlchemy models and Pydantic schemas for report management
MVP Version: No Auth, PDF stored in PostgreSQL bytea
"""

from datetime import date, datetime
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, Date, Boolean, DateTime, Integer, LargeBinary, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json
import os

Base = declarative_base()


# ============================================
# SQLAlchemy ORM Models
# ============================================

class ReportDB(Base):
    """SQLAlchemy model for reports table"""
    __tablename__ = "reports"
    
    id = Column(String(50), primary_key=True)
    title = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False)  # global_research, government, company
    organization = Column(String(200), nullable=False)
    published_date = Column(Date, nullable=False)
    summary = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array stored as text
    key_insights = Column(Text, nullable=True)  # JSON array stored as text
    canonical_url = Column(String(500), nullable=True)
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to files
    files = relationship("ReportFileDB", back_populates="report", cascade="all, delete-orphan")
    
    def get_tags(self) -> List[str]:
        """Parse tags from JSON string"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []
    
    def set_tags(self, tags: List[str]):
        """Convert tags list to JSON string"""
        self.tags = json.dumps(tags)
    
    def get_key_insights(self) -> List[str]:
        """Parse key_insights from JSON string"""
        if self.key_insights:
            try:
                return json.loads(self.key_insights)
            except:
                return []
        return []
    
    def set_key_insights(self, insights: List[str]):
        """Convert key_insights list to JSON string"""
        self.key_insights = json.dumps(insights)


class ReportFileDB(Base):
    """SQLAlchemy model for report files table - stores PDF binary"""
    __tablename__ = "report_files"
    
    id = Column(String(50), primary_key=True)
    report_id = Column(String(50), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(500), nullable=False)
    mime_type = Column(String(100), default="application/pdf")
    file_size = Column(Integer, nullable=False)
    sha256 = Column(String(64), unique=True, nullable=False)
    file_bytes = Column(LargeBinary, nullable=False)  # bytea for PDF storage
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to report
    report = relationship("ReportDB", back_populates="files")


# ============================================
# Pydantic Schemas for API
# ============================================

class ReportBase(BaseModel):
    """Base report schema"""
    title: str = Field(..., min_length=1, max_length=500)
    category: str = Field(..., pattern="^(global_research|government|company)$")
    organization: str = Field(..., min_length=1, max_length=200)
    published_date: date
    summary: Optional[str] = None
    tags: List[str] = []
    key_insights: List[str] = []
    canonical_url: Optional[str] = None
    is_featured: bool = False


class ReportCreate(ReportBase):
    """Schema for creating a report"""
    pass


class ReportUpdate(BaseModel):
    """Schema for updating a report"""
    title: Optional[str] = None
    category: Optional[str] = None
    organization: Optional[str] = None
    published_date: Optional[date] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    key_insights: Optional[List[str]] = None
    canonical_url: Optional[str] = None
    is_featured: Optional[bool] = None


class FileInfo(BaseModel):
    """Schema for file information"""
    file_name: str
    download_url: str


class ReportResponse(ReportBase):
    """Schema for report response"""
    id: str
    created_at: datetime
    updated_at: datetime
    file: Optional[FileInfo] = None
    
    class Config:
        from_attributes = True


class ReportListItem(BaseModel):
    """Schema for report list item (lighter than full response)"""
    id: str
    title: str
    category: str
    organization: str
    published_date: date
    summary: Optional[str] = None
    tags: List[str] = []
    has_pdf: bool = False


class ReportListResponse(BaseModel):
    """Schema for paginated report list"""
    reports: List[dict]  # Use dict for flexibility
    total: int
    page: int
    page_size: int
    total_pages: int


class CategoryCount(BaseModel):
    """Schema for category counts"""
    category: str
    count: int


class StatsResponse(BaseModel):
    """Schema for statistics response"""
    total_reports: int
    total_organizations: int
    this_month: int
    category_counts: List[CategoryCount]


class OrganizationFilter(BaseModel):
    """Schema for organization filter"""
    name: str
    count: int


class TagFilter(BaseModel):
    """Schema for tag filter"""
    name: str
    count: int


class FiltersResponse(BaseModel):
    """Schema for available filters"""
    organizations: List[OrganizationFilter]
    tags: List[TagFilter]


# ============================================
# Database Setup
# ============================================

# Get the server directory (parent of report folder)
SERVER_DIR = Path(__file__).parent.parent


def get_database_url():
    """Get database URL from environment variable or default to SQLite"""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        # Handle Heroku-style postgres:// URLs
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
        return db_url
    # Default to SQLite in server directory
    return f"sqlite:///{SERVER_DIR}/reports.db"


DATABASE_URL = get_database_url()

# Engine configuration based on database type
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL connection
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

