"""
Database Configuration - Quote Request System
SQLite for local development, can be switched to MySQL/PostgreSQL for production
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Database URL - Use SQLite with absolute path for reliability
# Get the directory where this file is located
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "quote.db"

# Force SQLite for local development (ignore DATABASE_URL env var if it's PostgreSQL)
env_db_url = os.getenv("DATABASE_URL", "")
if env_db_url.startswith("postgresql") or env_db_url.startswith("mysql"):
    # Use SQLite instead for local development
    DATABASE_URL = f"sqlite:///{DB_PATH}"
else:
    DATABASE_URL = env_db_url if env_db_url else f"sqlite:///{DB_PATH}"

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}  # SQLite specific
    )
else:
    engine = create_engine(DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI - yields database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    from models import Base  # Import here to avoid circular imports
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")


if __name__ == "__main__":
    init_db()

