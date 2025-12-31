"""
Report & Insight - Data Models
SQLAlchemy models and Pydantic schemas for report management
"""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, Date, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

Base = declarative_base()


# ============================================
# SQLAlchemy ORM Model
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
    pdf_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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


class BookmarkDB(Base):
    """SQLAlchemy model for bookmarks table"""
    __tablename__ = "bookmarks"
    
    id = Column(String(50), primary_key=True)
    report_id = Column(String(50), nullable=False)
    user_id = Column(String(50), default="default_user")  # Simplified for demo
    created_at = Column(DateTime, default=datetime.utcnow)


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
    pdf_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
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
    pdf_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_featured: Optional[bool] = None


class ReportResponse(ReportBase):
    """Schema for report response"""
    id: str
    created_at: datetime
    updated_at: datetime
    is_bookmarked: bool = False
    
    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for paginated report list"""
    reports: List[ReportResponse]
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


class BookmarkRequest(BaseModel):
    """Schema for bookmark request"""
    report_id: str


class BookmarkResponse(BaseModel):
    """Schema for bookmark response"""
    id: str
    report_id: str
    created_at: datetime


# ============================================
# Database Setup
# ============================================

DATABASE_URL = "sqlite:///./reports.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

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
