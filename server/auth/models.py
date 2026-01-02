"""
User Authentication Models
사용자 인증을 위한 데이터베이스 모델 (암호화 저장 지원)
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import enum
import os

# Database Configuration
AUTH_DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')
AUTH_DATABASE_URL = f"sqlite:///{AUTH_DB_PATH}"

engine = create_engine(
    AUTH_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserType(str, enum.Enum):
    """사용자 유형"""
    shipper = "shipper"       # 화주
    forwarder = "forwarder"   # 포워더


class User(Base):
    """
    사용자 정보 테이블
    비밀번호는 bcrypt로 해시화하여 저장
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 사용자 유형
    user_type = Column(String(20), nullable=False)  # shipper, forwarder
    
    # 기본 정보
    company = Column(String(100), nullable=False)           # 회사명
    business_no = Column(String(20), nullable=True)         # 사업자등록번호
    name = Column(String(50), nullable=False)               # 담당자명
    email = Column(String(100), unique=True, nullable=False, index=True)  # 이메일 (고유)
    phone = Column(String(30), nullable=False)              # 연락처
    
    # 인증 정보 (암호화 저장)
    password_hash = Column(String(255), nullable=False)     # bcrypt 해시화된 비밀번호
    
    # 상태
    is_active = Column(Boolean, default=True)               # 활성 상태
    is_verified = Column(Boolean, default=False)            # 이메일 인증 여부
    
    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)         # 마지막 로그인 시간
    
    def __repr__(self):
        return f"<User {self.email} ({self.user_type})>"


def init_db():
    """데이터베이스 초기화 - 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    print(f"[OK] Auth database initialized: {AUTH_DB_PATH}")


def get_session():
    """데이터베이스 세션 반환"""
    return SessionLocal()


if __name__ == "__main__":
    init_db()
