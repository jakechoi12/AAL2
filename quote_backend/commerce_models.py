"""
B2B Commerce Models
상품 거래 플랫폼을 위한 데이터 모델

기존 물류 견적 시스템(models.py)과 별도로 관리
상품 RFQ, 기업 디렉토리, 거래 관리 모델 정의
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, Enum, DECIMAL, JSON, Date, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
import uuid


# ==========================================
# ENUMS
# ==========================================

class CompanyTypeEnum(str, enum.Enum):
    """기업 유형"""
    buyer = "buyer"
    seller = "seller"
    both = "both"


class CompanySizeEnum(str, enum.Enum):
    """기업 규모"""
    startup = "startup"
    small = "small"
    medium = "medium"
    large = "large"


class VerificationStatusEnum(str, enum.Enum):
    """기업 인증 상태"""
    pending = "pending"
    verified = "verified"
    enterprise = "enterprise"
    rejected = "rejected"


class UserRoleEnum(str, enum.Enum):
    """사용자 역할"""
    buyer = "buyer"
    seller = "seller"
    both = "both"
    operator = "operator"
    admin = "admin"


class PriceTypeEnum(str, enum.Enum):
    """가격 유형"""
    public = "public"       # 공개 가격
    range = "range"         # 범위 표시
    private = "private"     # 문의 필요


class StockStatusEnum(str, enum.Enum):
    """재고 상태"""
    in_stock = "in_stock"
    limited = "limited"
    made_to_order = "made_to_order"


class RFQTypeEnum(str, enum.Enum):
    """RFQ 유형"""
    buy = "buy"     # 구매 RFQ
    sell = "sell"   # 판매 RFQ


class RFQVisibilityEnum(str, enum.Enum):
    """RFQ 공개 범위"""
    public = "public"       # 전체 공개
    private = "private"     # 비공개 (초대만)
    invited = "invited"     # 초대 + 일부 공개


class RFQStatusEnum(str, enum.Enum):
    """RFQ 상태"""
    draft = "draft"
    open = "open"
    closed = "closed"
    cancelled = "cancelled"
    completed = "completed"


class QuotationStatusEnum(str, enum.Enum):
    """견적 상태"""
    draft = "draft"
    submitted = "submitted"
    viewed = "viewed"
    negotiating = "negotiating"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"


class TransactionStatusEnum(str, enum.Enum):
    """거래 상태"""
    confirmed = "confirmed"
    contract_pending = "contract_pending"
    payment_pending = "payment_pending"
    paid = "paid"
    shipping = "shipping"
    delivered = "delivered"
    completed = "completed"
    cancelled = "cancelled"
    disputed = "disputed"


class InvitationStatusEnum(str, enum.Enum):
    """초대 상태"""
    pending = "pending"
    viewed = "viewed"
    responded = "responded"
    declined = "declined"


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def generate_uuid():
    """UUID 생성"""
    return str(uuid.uuid4())


# ==========================================
# COMPANY & USER MODELS
# ==========================================

class Company(Base):
    """
    기업 정보
    바이어/셀러 모두 포함하는 기업 프로필
    """
    __tablename__ = "companies"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # 기본 정보
    company_name = Column(String(200), nullable=False)
    company_name_en = Column(String(200), nullable=True)
    company_type = Column(String(20), nullable=False, default="both")  # buyer/seller/both
    business_number = Column(String(50), nullable=True)  # 사업자등록번호
    
    # 위치 정보
    country_code = Column(String(3), nullable=False, default="KR")  # ISO 3166-1
    region = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    
    # 산업/규모 정보
    industry_code = Column(String(20), nullable=True)  # 산업분류코드
    company_size = Column(String(20), nullable=True, default="small")
    employee_count = Column(Integer, nullable=True)
    annual_revenue = Column(DECIMAL(20, 2), nullable=True)  # USD
    export_ratio = Column(DECIMAL(5, 2), nullable=True)  # %
    founded_year = Column(Integer, nullable=True)
    
    # 프로필
    website = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    # 인증 상태
    verification_status = Column(String(20), default="pending")
    verification_date = Column(DateTime, nullable=True)
    verified_by = Column(String(36), nullable=True)
    
    # 통계/신뢰도
    trust_score = Column(DECIMAL(3, 2), default=3.00)  # 0.00~5.00
    response_rate = Column(DECIMAL(5, 2), default=0.00)  # %
    avg_response_time = Column(Integer, default=0)  # 시간
    total_transactions = Column(Integer, default=0)
    total_trade_volume = Column(DECIMAL(20, 2), default=0.00)  # USD
    
    # 거래 조건 선호
    preferred_incoterms = Column(JSON, nullable=True)  # ["FOB", "CIF"]
    preferred_payment = Column(JSON, nullable=True)    # ["T/T", "L/C"]
    min_order_value = Column(DECIMAL(15, 2), nullable=True)
    
    # 상태
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("CommerceUser", back_populates="company")
    products = relationship("Product", back_populates="company")
    rfqs = relationship("ProductRFQ", back_populates="company", foreign_keys="ProductRFQ.company_id")
    quotations = relationship("ProductQuotation", back_populates="company", foreign_keys="ProductQuotation.company_id")
    certifications = relationship("CompanyCertification", back_populates="company")
    
    # Indexes
    __table_args__ = (
        Index('idx_company_country', 'country_code'),
        Index('idx_company_industry', 'industry_code'),
        Index('idx_company_type', 'company_type', 'verification_status'),
        Index('idx_company_trust', 'trust_score'),
    )
    
    def __repr__(self):
        return f"<Company {self.company_name}>"


class CompanyCertification(Base):
    """
    기업 인증 정보
    ISO, IATF 등 보유 인증 관리
    """
    __tablename__ = "company_certifications"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    
    cert_type = Column(String(50), nullable=False)  # ISO9001, IATF16949 등
    cert_number = Column(String(100), nullable=True)
    issuer = Column(String(200), nullable=True)  # 발급기관
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    document_url = Column(String(500), nullable=True)
    
    verified = Column(Boolean, default=False)  # 플랫폼 검증 여부
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="certifications")
    
    def __repr__(self):
        return f"<CompanyCertification {self.cert_type}>"


class CommerceUser(Base):
    """
    B2B Commerce 사용자
    기업 소속 담당자 계정
    """
    __tablename__ = "commerce_users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    
    # 로그인 정보
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    
    # 프로필
    name = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    role = Column(String(20), default="both")  # buyer/seller/both/operator/admin
    
    # 설정
    language = Column(String(5), default="ko")
    timezone = Column(String(50), default="Asia/Seoul")
    profile_image_url = Column(String(500), nullable=True)
    
    # 인증
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    
    # 알림 설정
    notification_email = Column(Boolean, default=True)
    notification_push = Column(Boolean, default=True)
    notification_sms = Column(Boolean, default=False)
    
    # 상태
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="users")
    
    __table_args__ = (
        Index('idx_commerce_user_company', 'company_id'),
        Index('idx_commerce_user_role', 'role'),
    )
    
    def __repr__(self):
        return f"<CommerceUser {self.email}>"


# ==========================================
# CATEGORY & PRODUCT MODELS
# ==========================================

class Category(Base):
    """
    상품 카테고리
    계층 구조 지원 (대분류 > 중분류 > 소분류)
    """
    __tablename__ = "categories"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    parent_id = Column(String(36), ForeignKey("categories.id"), nullable=True)
    
    code = Column(String(20), unique=True, nullable=False)
    name_ko = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=True)
    level = Column(Integer, default=1)  # 1=대분류, 2=중분류, 3=소분류
    path = Column(String(500), nullable=True)  # /전자/소재/필름
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Self-referential relationship
    children = relationship("Category", backref="parent", remote_side=[id])
    
    # Other relationships
    products = relationship("Product", back_populates="category")
    rfqs = relationship("ProductRFQ", back_populates="category")
    
    __table_args__ = (
        Index('idx_category_parent', 'parent_id'),
        Index('idx_category_level', 'level', 'sort_order'),
    )
    
    def __repr__(self):
        return f"<Category {self.code}: {self.name_ko}>"


class Product(Base):
    """
    상품 정보
    셀러가 등록하는 상품 카탈로그
    """
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True)
    
    # 기본 정보
    sku = Column(String(50), nullable=True)  # 상품코드
    name_ko = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    specifications = Column(JSON, nullable=True)  # {"weight": "100g", "size": "10x10cm"}
    
    # 가격 정보
    price_type = Column(String(20), default="private")  # public/range/private
    price = Column(DECIMAL(15, 2), nullable=True)
    price_min = Column(DECIMAL(15, 2), nullable=True)
    price_max = Column(DECIMAL(15, 2), nullable=True)
    price_currency = Column(String(3), default="USD")
    price_unit = Column(String(20), nullable=True)  # per kg, per piece
    
    # 주문 조건
    moq = Column(DECIMAL(15, 2), nullable=True)  # 최소주문수량
    moq_unit = Column(String(20), nullable=True)
    lead_time_min = Column(Integer, nullable=True)  # 일
    lead_time_max = Column(Integer, nullable=True)
    stock_status = Column(String(20), default="in_stock")  # in_stock/limited/made_to_order
    
    # 원산지/규격
    origin_country = Column(String(3), nullable=True)
    hs_code = Column(String(20), nullable=True)
    certifications = Column(JSON, nullable=True)  # ["ISO9001", "CE"]
    
    # 미디어
    images = Column(JSON, nullable=True)  # [{"url": "...", "is_primary": true}]
    documents = Column(JSON, nullable=True)  # [{"type": "TDS", "url": "..."}]
    
    # 통계
    view_count = Column(Integer, default=0)
    inquiry_count = Column(Integer, default=0)
    
    # 상태
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="products")
    category = relationship("Category", back_populates="products")
    rfq_items = relationship("ProductRFQItem", back_populates="product")
    
    __table_args__ = (
        Index('idx_product_company', 'company_id', 'is_active'),
        Index('idx_product_category', 'category_id', 'is_active'),
        Index('idx_product_price', 'price_type', 'price'),
    )
    
    def __repr__(self):
        return f"<Product {self.name_ko}>"


# ==========================================
# RFQ MODELS
# ==========================================

class ProductRFQ(Base):
    """
    상품 RFQ (견적요청)
    바이어의 구매 요청 또는 셀러의 판매 제안
    """
    __tablename__ = "product_rfqs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("commerce_users.id"), nullable=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True)
    
    # 기본 정보
    rfq_number = Column(String(20), unique=True, nullable=False, index=True)
    rfq_type = Column(String(10), default="buy")  # buy/sell
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    
    # 공개/상태
    visibility = Column(String(20), default="public")  # public/private/invited
    status = Column(String(20), default="draft")  # draft/open/closed/cancelled/completed
    
    # 거래 조건
    target_countries = Column(JSON, nullable=True)  # ["US", "CN", "DE"]
    incoterms = Column(String(10), nullable=True)
    destination_port = Column(String(100), nullable=True)
    origin_port = Column(String(100), nullable=True)
    
    # 일정/결제
    delivery_date = Column(Date, nullable=True)
    payment_terms = Column(String(100), nullable=True)
    required_certs = Column(JSON, nullable=True)  # ["ISO9001", "CE"]
    
    # 마감
    deadline = Column(DateTime, nullable=True)
    auto_close = Column(Boolean, default=True)
    
    # 통계
    view_count = Column(Integer, default=0)
    quotation_count = Column(Integer, default=0)
    
    # AI 관련
    ai_generated = Column(Boolean, default=False)
    ai_prompt = Column(Text, nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="rfqs", foreign_keys=[company_id])
    user = relationship("CommerceUser")
    category = relationship("Category", back_populates="rfqs")
    items = relationship("ProductRFQItem", back_populates="rfq", cascade="all, delete-orphan")
    invitations = relationship("ProductRFQInvitation", back_populates="rfq", cascade="all, delete-orphan")
    quotations = relationship("ProductQuotation", back_populates="rfq")
    
    __table_args__ = (
        Index('idx_rfq_company', 'company_id', 'status'),
        Index('idx_rfq_category', 'category_id', 'status', 'visibility'),
        Index('idx_rfq_status', 'status', 'deadline'),
        Index('idx_rfq_type', 'rfq_type', 'visibility', 'status'),
    )
    
    def __repr__(self):
        return f"<ProductRFQ {self.rfq_number}>"


class ProductRFQItem(Base):
    """
    RFQ 품목
    RFQ에 포함된 개별 품목
    """
    __tablename__ = "product_rfq_items"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    rfq_id = Column(String(36), ForeignKey("product_rfqs.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    
    item_number = Column(Integer, default=1)
    name = Column(String(200), nullable=False)
    specifications = Column(JSON, nullable=True)
    quantity = Column(DECIMAL(15, 2), nullable=False)
    unit = Column(String(20), default="EA")  # kg, piece, set
    target_price = Column(DECIMAL(15, 2), nullable=True)
    target_currency = Column(String(3), nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    rfq = relationship("ProductRFQ", back_populates="items")
    product = relationship("Product", back_populates="rfq_items")
    quotation_items = relationship("ProductQuotationItem", back_populates="rfq_item")
    
    __table_args__ = (
        Index('idx_rfq_item_rfq', 'rfq_id', 'item_number'),
    )
    
    def __repr__(self):
        return f"<ProductRFQItem {self.name}>"


class ProductRFQInvitation(Base):
    """
    RFQ 초대
    PRIVATE/INVITED RFQ의 초대 관리
    """
    __tablename__ = "product_rfq_invitations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    rfq_id = Column(String(36), ForeignKey("product_rfqs.id"), nullable=False)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    
    status = Column(String(20), default="pending")  # pending/viewed/responded/declined
    invited_at = Column(DateTime, server_default=func.now())
    viewed_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    
    # Relationships
    rfq = relationship("ProductRFQ", back_populates="invitations")
    company = relationship("Company")
    
    __table_args__ = (
        Index('idx_invitation_rfq', 'rfq_id', 'status'),
        Index('idx_invitation_company', 'company_id', 'status'),
    )
    
    def __repr__(self):
        return f"<ProductRFQInvitation rfq={self.rfq_id}>"


# ==========================================
# QUOTATION MODELS
# ==========================================

class ProductQuotation(Base):
    """
    상품 견적
    RFQ에 대한 응답 견적
    """
    __tablename__ = "product_quotations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    rfq_id = Column(String(36), ForeignKey("product_rfqs.id"), nullable=False)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("commerce_users.id"), nullable=True)
    
    # 기본 정보
    quotation_number = Column(String(20), unique=True, nullable=False, index=True)
    status = Column(String(20), default="draft")
    
    # 가격
    total_amount = Column(DECIMAL(20, 2), nullable=True)
    currency = Column(String(3), default="USD")
    
    # 거래 조건
    incoterms = Column(String(10), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    
    # 납기
    delivery_date = Column(Date, nullable=True)
    lead_time = Column(Integer, nullable=True)  # 일
    validity_days = Column(Integer, default=30)
    valid_until = Column(Date, nullable=True)
    
    # 부가 정보
    notes = Column(Text, nullable=True)
    terms_conditions = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)
    
    # AI 관련
    ai_generated = Column(Boolean, default=False)
    ai_recommendation = Column(JSON, nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    submitted_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    
    # Relationships
    rfq = relationship("ProductRFQ", back_populates="quotations")
    company = relationship("Company", back_populates="quotations", foreign_keys=[company_id])
    user = relationship("CommerceUser")
    items = relationship("ProductQuotationItem", back_populates="quotation", cascade="all, delete-orphan")
    revisions = relationship("ProductQuotationRevision", back_populates="quotation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_quotation_rfq', 'rfq_id', 'status'),
        Index('idx_quotation_company', 'company_id', 'status'),
        Index('idx_quotation_price', 'total_amount', 'currency'),
    )
    
    def __repr__(self):
        return f"<ProductQuotation {self.quotation_number}>"


class ProductQuotationItem(Base):
    """
    견적 품목
    견적에 포함된 개별 품목
    """
    __tablename__ = "product_quotation_items"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    quotation_id = Column(String(36), ForeignKey("product_quotations.id"), nullable=False)
    rfq_item_id = Column(String(36), ForeignKey("product_rfq_items.id"), nullable=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    
    item_number = Column(Integer, default=1)
    name = Column(String(200), nullable=False)
    specifications = Column(JSON, nullable=True)
    quantity = Column(DECIMAL(15, 2), nullable=False)
    unit = Column(String(20), default="EA")
    unit_price = Column(DECIMAL(15, 2), nullable=False)
    amount = Column(DECIMAL(20, 2), nullable=True)  # quantity × unit_price
    moq = Column(DECIMAL(15, 2), nullable=True)
    lead_time = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    quotation = relationship("ProductQuotation", back_populates="items")
    rfq_item = relationship("ProductRFQItem", back_populates="quotation_items")
    product = relationship("Product")
    
    __table_args__ = (
        Index('idx_quotation_item_quotation', 'quotation_id', 'item_number'),
    )
    
    def __repr__(self):
        return f"<ProductQuotationItem {self.name}>"


class ProductQuotationRevision(Base):
    """
    견적 수정 이력
    협상 과정에서의 가격/조건 변경 기록
    """
    __tablename__ = "product_quotation_revisions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    quotation_id = Column(String(36), ForeignKey("product_quotations.id"), nullable=False)
    
    revision_number = Column(Integer, default=1)
    changed_by = Column(String(36), nullable=True)  # user_id
    change_type = Column(String(50), nullable=True)  # price/quantity/terms
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    quotation = relationship("ProductQuotation", back_populates="revisions")
    
    __table_args__ = (
        Index('idx_revision_quotation', 'quotation_id', 'revision_number'),
    )
    
    def __repr__(self):
        return f"<ProductQuotationRevision {self.revision_number}>"


# ==========================================
# TRANSACTION MODELS
# ==========================================

class ProductTransaction(Base):
    """
    상품 거래
    견적 수락 후 생성되는 거래 정보
    """
    __tablename__ = "product_transactions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    rfq_id = Column(String(36), ForeignKey("product_rfqs.id"), nullable=False)
    quotation_id = Column(String(36), ForeignKey("product_quotations.id"), nullable=False)
    buyer_company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    seller_company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    
    # 기본 정보
    transaction_number = Column(String(20), unique=True, nullable=False, index=True)
    status = Column(String(30), default="confirmed")
    
    # 금액
    total_amount = Column(DECIMAL(20, 2), nullable=False)
    currency = Column(String(3), default="USD")
    
    # 거래 조건
    incoterms = Column(String(10), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    delivery_date = Column(Date, nullable=True)
    
    # 배송 정보
    origin_country = Column(String(3), nullable=True)
    origin_port = Column(String(100), nullable=True)
    destination_country = Column(String(3), nullable=True)
    destination_port = Column(String(100), nullable=True)
    
    # 계약
    contract_signed = Column(Boolean, default=False)
    contract_signed_at = Column(DateTime, nullable=True)
    
    # 평가
    buyer_rating = Column(DECIMAL(2, 1), nullable=True)  # 1.0~5.0
    seller_rating = Column(DECIMAL(2, 1), nullable=True)
    buyer_review = Column(Text, nullable=True)
    seller_review = Column(Text, nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    rfq = relationship("ProductRFQ")
    quotation = relationship("ProductQuotation")
    buyer_company = relationship("Company", foreign_keys=[buyer_company_id])
    seller_company = relationship("Company", foreign_keys=[seller_company_id])
    items = relationship("ProductTransactionItem", back_populates="transaction", cascade="all, delete-orphan")
    status_logs = relationship("ProductTransactionStatusLog", back_populates="transaction", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_transaction_buyer', 'buyer_company_id', 'status'),
        Index('idx_transaction_seller', 'seller_company_id', 'status'),
        Index('idx_transaction_status', 'status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ProductTransaction {self.transaction_number}>"


class ProductTransactionItem(Base):
    """
    거래 품목
    확정된 거래의 품목 정보
    """
    __tablename__ = "product_transaction_items"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(String(36), ForeignKey("product_transactions.id"), nullable=False)
    quotation_item_id = Column(String(36), ForeignKey("product_quotation_items.id"), nullable=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    
    item_number = Column(Integer, default=1)
    name = Column(String(200), nullable=False)
    specifications = Column(JSON, nullable=True)
    quantity = Column(DECIMAL(15, 2), nullable=False)
    unit = Column(String(20), default="EA")
    unit_price = Column(DECIMAL(15, 2), nullable=False)
    amount = Column(DECIMAL(20, 2), nullable=True)
    hs_code = Column(String(20), nullable=True)
    origin_country = Column(String(3), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    transaction = relationship("ProductTransaction", back_populates="items")
    quotation_item = relationship("ProductQuotationItem")
    product = relationship("Product")
    
    __table_args__ = (
        Index('idx_transaction_item', 'transaction_id', 'item_number'),
    )
    
    def __repr__(self):
        return f"<ProductTransactionItem {self.name}>"


class ProductTransactionStatusLog(Base):
    """
    거래 상태 변경 이력
    """
    __tablename__ = "product_transaction_status_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(String(36), ForeignKey("product_transactions.id"), nullable=False)
    
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    changed_by = Column(String(36), nullable=True)  # user_id
    change_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    transaction = relationship("ProductTransaction", back_populates="status_logs")
    
    __table_args__ = (
        Index('idx_status_log_transaction', 'transaction_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ProductTransactionStatusLog {self.from_status}->{self.to_status}>"


# ==========================================
# NOTIFICATION & MESSAGE MODELS (Commerce-specific)
# ==========================================

class CommerceNotification(Base):
    """
    B2B Commerce 알림
    """
    __tablename__ = "commerce_notifications"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # 수신자
    user_id = Column(String(36), ForeignKey("commerce_users.id"), nullable=False)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    
    # 알림 내용
    notification_type = Column(String(50), nullable=False)  # new_rfq, quotation_received, etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    
    # 관련 엔티티
    related_type = Column(String(50), nullable=True)  # rfq, quotation, transaction
    related_id = Column(String(36), nullable=True)
    
    # 상태
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("CommerceUser")
    company = relationship("Company")
    
    __table_args__ = (
        Index('idx_notification_user', 'user_id', 'is_read'),
        Index('idx_notification_company', 'company_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<CommerceNotification {self.notification_type}>"


class CommerceMessage(Base):
    """
    B2B Commerce 메시지
    RFQ/견적 관련 대화
    """
    __tablename__ = "commerce_messages"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # 대화 컨텍스트
    rfq_id = Column(String(36), ForeignKey("product_rfqs.id"), nullable=True)
    quotation_id = Column(String(36), ForeignKey("product_quotations.id"), nullable=True)
    transaction_id = Column(String(36), ForeignKey("product_transactions.id"), nullable=True)
    
    # 발신/수신
    sender_company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    sender_user_id = Column(String(36), ForeignKey("commerce_users.id"), nullable=False)
    recipient_company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    
    # 메시지
    content = Column(Text, nullable=False)
    attachments = Column(JSON, nullable=True)
    
    # 상태
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    rfq = relationship("ProductRFQ")
    quotation = relationship("ProductQuotation")
    transaction = relationship("ProductTransaction")
    sender_company = relationship("Company", foreign_keys=[sender_company_id])
    sender_user = relationship("CommerceUser")
    recipient_company = relationship("Company", foreign_keys=[recipient_company_id])
    
    __table_args__ = (
        Index('idx_message_rfq', 'rfq_id', 'created_at'),
        Index('idx_message_sender', 'sender_company_id'),
        Index('idx_message_recipient', 'recipient_company_id', 'is_read'),
    )
    
    def __repr__(self):
        return f"<CommerceMessage {self.id}>"

