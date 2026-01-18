"""
B2B Commerce Pydantic Schemas
API 요청/응답을 위한 스키마 정의
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# ==========================================
# ENUMS
# ==========================================

class CompanyTypeEnum(str, Enum):
    buyer = "buyer"
    seller = "seller"
    both = "both"


class VerificationStatusEnum(str, Enum):
    pending = "pending"
    verified = "verified"
    enterprise = "enterprise"
    rejected = "rejected"


class PriceTypeEnum(str, Enum):
    public = "public"
    range = "range"
    private = "private"


class StockStatusEnum(str, Enum):
    in_stock = "in_stock"
    limited = "limited"
    made_to_order = "made_to_order"


class RFQTypeEnum(str, Enum):
    buy = "buy"
    sell = "sell"


class RFQVisibilityEnum(str, Enum):
    public = "public"
    private = "private"
    invited = "invited"


class RFQStatusEnum(str, Enum):
    draft = "draft"
    open = "open"
    closed = "closed"
    cancelled = "cancelled"
    completed = "completed"


class QuotationStatusEnum(str, Enum):
    draft = "draft"
    submitted = "submitted"
    viewed = "viewed"
    negotiating = "negotiating"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"


class TransactionStatusEnum(str, Enum):
    confirmed = "confirmed"
    contract_pending = "contract_pending"
    payment_pending = "payment_pending"
    paid = "paid"
    shipping = "shipping"
    delivered = "delivered"
    completed = "completed"
    cancelled = "cancelled"
    disputed = "disputed"


# ==========================================
# COMPANY SCHEMAS
# ==========================================

class CompanyBase(BaseModel):
    company_name: str = Field(..., max_length=200)
    company_name_en: Optional[str] = Field(None, max_length=200)
    company_type: CompanyTypeEnum = CompanyTypeEnum.both
    business_number: Optional[str] = Field(None, max_length=50)
    country_code: str = Field("KR", max_length=3)
    region: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    industry_code: Optional[str] = Field(None, max_length=20)
    company_size: Optional[str] = Field("small", max_length=20)
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    export_ratio: Optional[float] = None
    founded_year: Optional[int] = None
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    preferred_incoterms: Optional[List[str]] = None
    preferred_payment: Optional[List[str]] = None
    min_order_value: Optional[float] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = Field(None, max_length=200)
    company_name_en: Optional[str] = Field(None, max_length=200)
    company_type: Optional[CompanyTypeEnum] = None
    business_number: Optional[str] = Field(None, max_length=50)
    country_code: Optional[str] = Field(None, max_length=3)
    region: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    industry_code: Optional[str] = Field(None, max_length=20)
    company_size: Optional[str] = Field(None, max_length=20)
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    export_ratio: Optional[float] = None
    founded_year: Optional[int] = None
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    preferred_incoterms: Optional[List[str]] = None
    preferred_payment: Optional[List[str]] = None
    min_order_value: Optional[float] = None


class CompanyResponse(CompanyBase):
    id: str
    verification_status: str = "pending"
    verification_date: Optional[datetime] = None
    trust_score: float = 3.0
    response_rate: float = 0.0
    avg_response_time: int = 0
    total_transactions: int = 0
    total_trade_volume: float = 0.0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyListItem(BaseModel):
    id: str
    company_name: str
    company_name_en: Optional[str] = None
    company_type: str
    country_code: str
    industry_code: Optional[str] = None
    verification_status: str
    trust_score: float
    total_transactions: int
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    companies: List[CompanyListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==========================================
# CERTIFICATION SCHEMAS
# ==========================================

class CertificationBase(BaseModel):
    cert_type: str = Field(..., max_length=50)
    cert_number: Optional[str] = Field(None, max_length=100)
    issuer: Optional[str] = Field(None, max_length=200)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    document_url: Optional[str] = Field(None, max_length=500)


class CertificationCreate(CertificationBase):
    company_id: str


class CertificationResponse(CertificationBase):
    id: str
    company_id: str
    verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# USER SCHEMAS
# ==========================================

class CommerceUserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., max_length=100)
    name_en: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    role: str = "both"
    language: str = "ko"
    timezone: str = "Asia/Seoul"


class CommerceUserCreate(CommerceUserBase):
    company_id: Optional[str] = None
    password: str = Field(..., min_length=8)


class CommerceUserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    name_en: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = None
    timezone: Optional[str] = None
    notification_email: Optional[bool] = None
    notification_push: Optional[bool] = None
    notification_sms: Optional[bool] = None


class CommerceUserResponse(CommerceUserBase):
    id: str
    company_id: Optional[str] = None
    email_verified: bool = False
    phone_verified: bool = False
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    notification_email: bool = True
    notification_push: bool = True
    notification_sms: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# CATEGORY SCHEMAS
# ==========================================

class CategoryBase(BaseModel):
    code: str = Field(..., max_length=20)
    name_ko: str = Field(..., max_length=100)
    name_en: Optional[str] = Field(None, max_length=100)
    level: int = 1
    path: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    icon_url: Optional[str] = Field(None, max_length=500)
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    parent_id: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: str
    parent_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryTreeItem(BaseModel):
    id: str
    code: str
    name_ko: str
    name_en: Optional[str] = None
    level: int
    children: List["CategoryTreeItem"] = []

    class Config:
        from_attributes = True


# ==========================================
# PRODUCT SCHEMAS
# ==========================================

class ProductBase(BaseModel):
    sku: Optional[str] = Field(None, max_length=50)
    name_ko: str = Field(..., max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    price_type: PriceTypeEnum = PriceTypeEnum.private
    price: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_currency: str = "USD"
    price_unit: Optional[str] = Field(None, max_length=20)
    moq: Optional[float] = None
    moq_unit: Optional[str] = Field(None, max_length=20)
    lead_time_min: Optional[int] = None
    lead_time_max: Optional[int] = None
    stock_status: StockStatusEnum = StockStatusEnum.in_stock
    origin_country: Optional[str] = Field(None, max_length=3)
    hs_code: Optional[str] = Field(None, max_length=20)
    certifications: Optional[List[str]] = None
    images: Optional[List[Dict[str, Any]]] = None
    documents: Optional[List[Dict[str, Any]]] = None


class ProductCreate(ProductBase):
    company_id: str
    category_id: Optional[str] = None


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, max_length=50)
    name_ko: Optional[str] = Field(None, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    category_id: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    price_type: Optional[PriceTypeEnum] = None
    price: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_currency: Optional[str] = None
    price_unit: Optional[str] = Field(None, max_length=20)
    moq: Optional[float] = None
    moq_unit: Optional[str] = Field(None, max_length=20)
    lead_time_min: Optional[int] = None
    lead_time_max: Optional[int] = None
    stock_status: Optional[StockStatusEnum] = None
    origin_country: Optional[str] = Field(None, max_length=3)
    hs_code: Optional[str] = Field(None, max_length=20)
    certifications: Optional[List[str]] = None
    images: Optional[List[Dict[str, Any]]] = None
    documents: Optional[List[Dict[str, Any]]] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: str
    company_id: str
    category_id: Optional[str] = None
    view_count: int = 0
    inquiry_count: int = 0
    is_featured: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    # Nested
    company: Optional[CompanyListItem] = None
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True


class ProductListItem(BaseModel):
    id: str
    company_id: str
    category_id: Optional[str] = None
    sku: Optional[str] = None
    name_ko: str
    name_en: Optional[str] = None
    price_type: str
    price: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_currency: str
    moq: Optional[float] = None
    origin_country: Optional[str] = None
    images: Optional[List[Dict[str, Any]]] = None
    view_count: int = 0
    is_featured: bool = False
    company_name: Optional[str] = None
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    products: List[ProductListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==========================================
# RFQ SCHEMAS
# ==========================================

class RFQItemBase(BaseModel):
    name: str = Field(..., max_length=200)
    specifications: Optional[Dict[str, Any]] = None
    quantity: float
    unit: str = "EA"
    target_price: Optional[float] = None
    target_currency: Optional[str] = None
    notes: Optional[str] = None


class RFQItemCreate(RFQItemBase):
    product_id: Optional[str] = None


class RFQItemResponse(RFQItemBase):
    id: str
    rfq_id: str
    product_id: Optional[str] = None
    item_number: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductRFQBase(BaseModel):
    rfq_type: RFQTypeEnum = RFQTypeEnum.buy
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    category_id: Optional[str] = None
    visibility: RFQVisibilityEnum = RFQVisibilityEnum.public
    target_countries: Optional[List[str]] = None
    incoterms: Optional[str] = Field(None, max_length=10)
    destination_port: Optional[str] = Field(None, max_length=100)
    origin_port: Optional[str] = Field(None, max_length=100)
    delivery_date: Optional[date] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    required_certs: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    auto_close: bool = True


class ProductRFQCreate(ProductRFQBase):
    company_id: str
    user_id: Optional[str] = None
    items: List[RFQItemCreate] = []
    invited_company_ids: Optional[List[str]] = None  # For private/invited RFQs


class ProductRFQUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    category_id: Optional[str] = None
    visibility: Optional[RFQVisibilityEnum] = None
    target_countries: Optional[List[str]] = None
    incoterms: Optional[str] = Field(None, max_length=10)
    destination_port: Optional[str] = Field(None, max_length=100)
    origin_port: Optional[str] = Field(None, max_length=100)
    delivery_date: Optional[date] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    required_certs: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    auto_close: Optional[bool] = None


class ProductRFQResponse(ProductRFQBase):
    id: str
    company_id: str
    user_id: Optional[str] = None
    rfq_number: str
    status: str
    view_count: int = 0
    quotation_count: int = 0
    ai_generated: bool = False
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    # Nested
    items: List[RFQItemResponse] = []
    company: Optional[CompanyListItem] = None
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True


class ProductRFQListItem(BaseModel):
    id: str
    rfq_number: str
    rfq_type: str
    title: str
    visibility: str
    status: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    company_id: str
    company_name: Optional[str] = None
    deadline: Optional[datetime] = None
    quotation_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ProductRFQListResponse(BaseModel):
    rfqs: List[ProductRFQListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==========================================
# QUOTATION SCHEMAS
# ==========================================

class QuotationItemBase(BaseModel):
    name: str = Field(..., max_length=200)
    specifications: Optional[Dict[str, Any]] = None
    quantity: float
    unit: str = "EA"
    unit_price: float
    moq: Optional[float] = None
    lead_time: Optional[int] = None
    notes: Optional[str] = None


class QuotationItemCreate(QuotationItemBase):
    rfq_item_id: Optional[str] = None
    product_id: Optional[str] = None


class QuotationItemResponse(QuotationItemBase):
    id: str
    quotation_id: str
    rfq_item_id: Optional[str] = None
    product_id: Optional[str] = None
    item_number: int
    amount: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProductQuotationBase(BaseModel):
    incoterms: Optional[str] = Field(None, max_length=10)
    payment_terms: Optional[str] = Field(None, max_length=100)
    delivery_date: Optional[date] = None
    lead_time: Optional[int] = None
    validity_days: int = 30
    valid_until: Optional[date] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class ProductQuotationCreate(ProductQuotationBase):
    rfq_id: str
    company_id: str
    user_id: Optional[str] = None
    items: List[QuotationItemCreate] = []


class ProductQuotationUpdate(BaseModel):
    incoterms: Optional[str] = Field(None, max_length=10)
    payment_terms: Optional[str] = Field(None, max_length=100)
    delivery_date: Optional[date] = None
    lead_time: Optional[int] = None
    validity_days: Optional[int] = None
    valid_until: Optional[date] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class ProductQuotationResponse(ProductQuotationBase):
    id: str
    rfq_id: str
    company_id: str
    user_id: Optional[str] = None
    quotation_number: str
    status: str
    total_amount: Optional[float] = None
    currency: str
    ai_generated: bool = False
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    # Nested
    items: List[QuotationItemResponse] = []
    company: Optional[CompanyListItem] = None

    class Config:
        from_attributes = True


class ProductQuotationListItem(BaseModel):
    id: str
    quotation_number: str
    rfq_id: str
    rfq_number: Optional[str] = None
    rfq_title: Optional[str] = None
    company_id: str
    company_name: Optional[str] = None
    status: str
    total_amount: Optional[float] = None
    currency: str
    valid_until: Optional[date] = None
    created_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductQuotationListResponse(BaseModel):
    quotations: List[ProductQuotationListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==========================================
# QUOTATION COMPARISON
# ==========================================

class QuotationComparisonItem(BaseModel):
    quotation_id: str
    quotation_number: str
    company_id: str
    company_name: str
    trust_score: float
    total_amount: float
    currency: str
    incoterms: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_date: Optional[date] = None
    lead_time: Optional[int] = None
    valid_until: Optional[date] = None
    item_count: int = 0
    # 비교 분석
    price_rank: int = 0
    price_diff_pct: float = 0.0  # 최저가 대비 %
    ai_score: Optional[float] = None
    ai_recommendation: Optional[str] = None


class QuotationComparisonResponse(BaseModel):
    rfq_id: str
    rfq_number: str
    rfq_title: str
    quotations: List[QuotationComparisonItem]
    total_quotations: int
    lowest_price: float
    highest_price: float
    avg_price: float


# ==========================================
# TRANSACTION SCHEMAS
# ==========================================

class ProductTransactionCreate(BaseModel):
    rfq_id: str
    quotation_id: str


class ProductTransactionResponse(BaseModel):
    id: str
    transaction_number: str
    rfq_id: str
    quotation_id: str
    buyer_company_id: str
    seller_company_id: str
    status: str
    total_amount: float
    currency: str
    incoterms: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_date: Optional[date] = None
    origin_country: Optional[str] = None
    origin_port: Optional[str] = None
    destination_country: Optional[str] = None
    destination_port: Optional[str] = None
    contract_signed: bool = False
    contract_signed_at: Optional[datetime] = None
    buyer_rating: Optional[float] = None
    seller_rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    # Nested
    buyer_company: Optional[CompanyListItem] = None
    seller_company: Optional[CompanyListItem] = None

    class Config:
        from_attributes = True


class ProductTransactionListItem(BaseModel):
    id: str
    transaction_number: str
    rfq_id: str
    rfq_number: Optional[str] = None
    buyer_company_id: str
    buyer_company_name: Optional[str] = None
    seller_company_id: str
    seller_company_name: Optional[str] = None
    status: str
    total_amount: float
    currency: str
    delivery_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProductTransactionListResponse(BaseModel):
    transactions: List[ProductTransactionListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class TransactionStatusUpdate(BaseModel):
    status: TransactionStatusEnum
    reason: Optional[str] = None


# ==========================================
# NOTIFICATION SCHEMAS
# ==========================================

class CommerceNotificationResponse(BaseModel):
    id: str
    user_id: str
    company_id: Optional[str] = None
    notification_type: str
    title: str
    message: Optional[str] = None
    related_type: Optional[str] = None
    related_id: Optional[str] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CommerceNotificationListResponse(BaseModel):
    notifications: List[CommerceNotificationResponse]
    total: int
    unread_count: int


# ==========================================
# MESSAGE SCHEMAS
# ==========================================

class CommerceMessageCreate(BaseModel):
    rfq_id: Optional[str] = None
    quotation_id: Optional[str] = None
    transaction_id: Optional[str] = None
    recipient_company_id: str
    content: str
    attachments: Optional[List[Dict[str, Any]]] = None


class CommerceMessageResponse(BaseModel):
    id: str
    rfq_id: Optional[str] = None
    quotation_id: Optional[str] = None
    transaction_id: Optional[str] = None
    sender_company_id: str
    sender_company_name: Optional[str] = None
    sender_user_id: str
    sender_user_name: Optional[str] = None
    recipient_company_id: str
    content: str
    attachments: Optional[List[Dict[str, Any]]] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CommerceMessageThreadResponse(BaseModel):
    messages: List[CommerceMessageResponse]
    total: int


# ==========================================
# DASHBOARD & ANALYTICS SCHEMAS
# ==========================================

class CompanyDashboardStats(BaseModel):
    total_rfqs: int = 0
    open_rfqs: int = 0
    total_quotations_sent: int = 0
    total_quotations_received: int = 0
    pending_quotations: int = 0
    active_transactions: int = 0
    completed_transactions: int = 0
    total_trade_volume: float = 0.0
    trust_score: float = 3.0
    response_rate: float = 0.0


class RFQStats(BaseModel):
    total: int = 0
    by_status: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    avg_quotations_per_rfq: float = 0.0
    avg_time_to_first_quotation: Optional[float] = None  # hours


# ==========================================
# AI SCHEMAS
# ==========================================

class AIRFQDraftRequest(BaseModel):
    prompt: str
    category_id: Optional[str] = None
    target_countries: Optional[List[str]] = None


class AIRFQDraftResponse(BaseModel):
    title: str
    description: str
    items: List[RFQItemCreate]
    suggested_incoterms: Optional[str] = None
    suggested_payment_terms: Optional[str] = None
    suggested_deadline_days: int = 14
    ai_notes: Optional[str] = None


class AIQuotationDraftRequest(BaseModel):
    rfq_id: str
    company_id: str


class AIQuotationDraftResponse(BaseModel):
    items: List[QuotationItemCreate]
    suggested_incoterms: Optional[str] = None
    suggested_payment_terms: Optional[str] = None
    suggested_lead_time: Optional[int] = None
    ai_notes: Optional[str] = None


class AICompanyMatchRequest(BaseModel):
    rfq_id: str
    limit: int = 10


class AICompanyMatchResponse(BaseModel):
    matches: List[Dict[str, Any]]
    total: int


# ==========================================
# COMMON RESPONSE SCHEMAS
# ==========================================

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

