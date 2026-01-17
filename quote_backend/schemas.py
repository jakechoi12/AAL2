"""
Pydantic Schemas - Request/Response Models for API
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ==========================================
# REFERENCE DATA SCHEMAS
# ==========================================

class PortBase(BaseModel):
    code: str
    name: str
    name_ko: Optional[str] = None
    country: str
    country_code: str
    port_type: str
    is_active: bool = True


class PortResponse(PortBase):
    id: int
    
    class Config:
        from_attributes = True


class ContainerTypeBase(BaseModel):
    code: str
    name: str
    abbreviation: Optional[str] = None  # 약어 표시용 (e.g., 20'GP, 40'HC)
    description: Optional[str] = None
    
    # Size and Category
    size: Optional[str] = None  # 20, 40, 4H
    category: Optional[str] = None  # FR, DC, OT, RF, TK
    size_teu: Optional[float] = None
    
    # Standard Codes
    iso_standard: Optional[str] = None
    customs_port_standard: Optional[str] = None
    china_send_standard: Optional[str] = None
    china_receive: Optional[str] = None
    
    # Weight Specifications (kg)
    tare_weight: Optional[float] = None
    max_weight_kg: Optional[int] = None  # max_payload
    
    # Internal Dimensions (mm)
    length_mm: Optional[int] = None
    width_mm: Optional[int] = None
    height_mm: Optional[int] = None
    
    # Volume
    max_cbm: Optional[float] = None
    cbm_limit: Optional[bool] = False
    
    is_active: bool = True
    sort_order: int = 0


class ContainerTypeResponse(ContainerTypeBase):
    id: int
    
    class Config:
        from_attributes = True


class TruckTypeBase(BaseModel):
    code: str
    name: str
    abbreviation: Optional[str] = None  # 약어 표시용 (e.g., 5T윙, 11T냉동)
    description: Optional[str] = None
    max_weight_kg: Optional[int] = None
    max_cbm: Optional[float] = None
    is_active: bool = True
    sort_order: int = 0


class TruckTypeResponse(TruckTypeBase):
    id: int
    
    class Config:
        from_attributes = True


class IncotermBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    description_ko: Optional[str] = None
    seller_responsibility: Optional[str] = None
    buyer_responsibility: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class IncotermResponse(IncotermBase):
    id: int
    
    class Config:
        from_attributes = True


# ==========================================
# FREIGHT CODE SCHEMAS
# ==========================================

class FreightUnitResponse(BaseModel):
    """운임 단위 응답"""
    id: int
    code: str
    name_en: Optional[str] = None
    name_ko: Optional[str] = None
    sort_order: int = 0
    
    class Config:
        from_attributes = True


class FreightCodeResponse(BaseModel):
    """운임 코드 응답 (단위 포함)"""
    id: int
    code: str
    group_name: Optional[str] = None
    name_en: str
    name_ko: Optional[str] = None
    vat_applicable: bool = False
    default_currency: str = "USD"
    is_active: bool = True
    sort_order: int = 0
    units: List[str] = []  # 허용 단위 코드 목록
    
    class Config:
        from_attributes = True


class FreightCategoryResponse(BaseModel):
    """운임 카테고리 응답"""
    id: int
    code: str
    name_en: str
    name_ko: Optional[str] = None
    shipping_types: Optional[str] = None
    sort_order: int = 0
    
    class Config:
        from_attributes = True


class FreightCategoryWithCodesResponse(BaseModel):
    """운임 카테고리 + 소속 코드 목록"""
    id: int
    code: str
    name_en: str
    name_ko: Optional[str] = None
    shipping_types: Optional[str] = None
    sort_order: int = 0
    codes: List[FreightCodeResponse] = []
    
    class Config:
        from_attributes = True


class FreightCodesListResponse(BaseModel):
    """운임 코드 전체 목록 응답 (카테고리별 그룹핑)"""
    categories: List[FreightCategoryWithCodesResponse]
    units: List[FreightUnitResponse]


# ==========================================
# CUSTOMER SCHEMAS
# ==========================================

class CustomerBase(BaseModel):
    company: str = Field(..., max_length=50)
    job_title: Optional[str] = Field(None, max_length=30)
    name: str = Field(..., max_length=30)
    email: str = Field(..., max_length=30)
    phone: str = Field(..., max_length=30)


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# CARGO DETAIL SCHEMAS
# ==========================================

class CargoDetailBase(BaseModel):
    row_index: int = 0
    container_type: Optional[str] = None
    truck_type: Optional[str] = None
    length: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    qty: int = 1
    gross_weight: Optional[float] = None
    cbm: Optional[float] = None
    volume_weight: Optional[int] = None
    chargeable_weight: Optional[int] = None


class CargoDetailCreate(CargoDetailBase):
    pass


class CargoDetailResponse(CargoDetailBase):
    id: int
    quote_request_id: int
    
    class Config:
        from_attributes = True


# ==========================================
# QUOTE REQUEST SCHEMAS
# ==========================================

class QuoteRequestBase(BaseModel):
    # Trade & Shipping
    trade_mode: str = Field(..., description="export, import, domestic")
    shipping_type: str = Field(..., description="all, ocean, air, truck")
    load_type: str = Field(..., description="FCL, LCL, Bulk, FTL, LTL, Air")
    incoterms: Optional[str] = Field(None, description="EXW, FOB, CFR, CIF, DAP, DDP")
    
    # Schedules
    pol: str = Field(..., max_length=50)
    pod: str = Field(..., max_length=50)
    etd: str = Field(..., description="YYYY-MM-DD or YYYY-MM-DD HH:MM")
    eta: str = Field(..., description="YYYY-MM-DD or YYYY-MM-DD HH:MM")  # Required
    
    # DG
    is_dg: bool = False
    dg_class: Optional[str] = Field(None, max_length=1)
    dg_un: Optional[str] = Field(None, max_length=4)
    
    # Additional Details
    export_cc: bool = False
    import_cc: bool = False
    shipping_insurance: bool = False
    pickup_required: bool = False
    pickup_address: Optional[str] = Field(None, max_length=100)
    delivery_required: bool = False
    delivery_address: Optional[str] = Field(None, max_length=100)
    invoice_value: float = Field(..., description="Invoice value in USD")  # Required
    
    # Remark
    remark: Optional[str] = None


class QuoteRequestCreate(QuoteRequestBase):
    cargo: List[CargoDetailCreate]
    customer: CustomerCreate


class QuoteRequestResponse(QuoteRequestBase):
    id: int
    request_number: str
    status: str
    customer_id: int
    created_at: datetime
    updated_at: datetime
    cargo_details: List[CargoDetailResponse]
    customer: CustomerResponse
    
    class Config:
        from_attributes = True


class QuoteRequestListResponse(BaseModel):
    id: int
    request_number: str
    trade_mode: str
    shipping_type: str
    load_type: str
    pol: str
    pod: str
    etd: datetime
    status: str
    created_at: datetime
    customer_company: str
    customer_name: str
    
    class Config:
        from_attributes = True


# ==========================================
# API RESPONSE SCHEMAS
# ==========================================

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class QuoteSubmitResponse(BaseModel):
    success: bool
    message: str
    request_number: str
    quote_request_id: int
    bidding_no: Optional[str] = None
    pdf_url: Optional[str] = None
    deadline: Optional[str] = None


# ==========================================
# BIDDING SCHEMAS
# ==========================================

class BiddingResponse(BaseModel):
    id: int
    bidding_no: str
    quote_request_id: int
    pdf_path: Optional[str] = None
    deadline: Optional[datetime] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# FORWARDER SCHEMAS
# ==========================================

class ForwarderBase(BaseModel):
    company: str = Field(..., max_length=100)
    business_no: Optional[str] = Field(None, max_length=20)
    name: str = Field(..., max_length=50)
    email: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=30)


class ForwarderCreate(ForwarderBase):
    password: str = Field(..., min_length=6, max_length=100, description="비밀번호 (최소 6자)")


class ForwarderLogin(BaseModel):
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=1, max_length=100, description="비밀번호")


class ForwarderResponse(ForwarderBase):
    id: int
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ForwarderAuthResponse(BaseModel):
    success: bool
    message: str
    forwarder: Optional[ForwarderResponse] = None
    token: Optional[str] = None


# ==========================================
# BID SCHEMAS
# ==========================================

class BidBase(BaseModel):
    total_amount: float = Field(..., description="Total bid amount")
    total_amount_krw: Optional[float] = Field(None, description="Total bid amount in KRW")
    freight_charge: Optional[float] = Field(None, description="Freight charge")
    local_charge: Optional[float] = Field(None, description="Local charges")
    other_charge: Optional[float] = Field(None, description="Other charges")
    validity_date: Optional[str] = Field(None, description="Quote validity date YYYY-MM-DD")
    transit_time: Optional[str] = Field(None, max_length=50, description="Expected transit time")
    carrier: Optional[str] = Field(None, max_length=100, description="Carrier/Airline name")
    etd: Optional[str] = Field(None, description="Proposed ETD YYYY-MM-DD HH:MM")
    eta: Optional[str] = Field(None, description="Proposed ETA YYYY-MM-DD HH:MM")
    remark: Optional[str] = Field(None, description="Additional remarks/conditions")


class BidCreate(BidBase):
    bidding_id: int


class BidUpdate(BidBase):
    pass


class BidResponse(BaseModel):
    id: int
    bidding_id: int
    forwarder_id: int
    total_amount: float
    freight_charge: Optional[float] = None
    local_charge: Optional[float] = None
    other_charge: Optional[float] = None
    validity_date: Optional[datetime] = None  # DateTime from DB
    transit_time: Optional[str] = None
    remark: Optional[str] = None
    status: str
    submitted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BidWithForwarderResponse(BidResponse):
    forwarder: ForwarderResponse
    
    class Config:
        from_attributes = True


class BidSubmitResponse(BaseModel):
    success: bool
    message: str
    bid: Optional[BidResponse] = None


# ==========================================
# BIDDING LIST SCHEMAS
# ==========================================

class BiddingListItem(BaseModel):
    id: int
    bidding_no: str
    customer_company: str
    pol: str
    pod: str
    pol_name: Optional[str] = None  # 항구 이름 (e.g., "BUSAN, KOREA")
    pod_name: Optional[str] = None  # 항구 이름 (e.g., "ROTTERDAM, NETHERLANDS")
    shipping_type: str
    load_type: str
    cargo_summary: Optional[str] = None  # 물량 요약 (e.g., "20'GP × 3", "32.5 CBM", "1,500 KGS")
    etd: datetime
    deadline: Optional[datetime] = None
    status: str
    bid_count: int = 0
    avg_bid_price: Optional[float] = None  # 평균 입찰가
    my_bid_status: Optional[str] = None  # 포워더 본인의 입찰 상태
    
    class Config:
        from_attributes = True


class BiddingListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[BiddingListItem]


class BiddingStatsResponse(BaseModel):
    total_count: int  # 전체 Bidding 건수
    open_count: int
    closing_soon_count: int  # 24시간 이내 마감
    awarded_count: int
    failed_count: int  # closed + cancelled + expired


class BiddingDetailResponse(BaseModel):
    id: int
    bidding_no: str
    status: str
    deadline: Optional[datetime] = None
    created_at: datetime
    pdf_url: Optional[str] = None
    
    # Quote Request 정보
    customer_company: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    trade_mode: str
    shipping_type: str
    load_type: str
    incoterms: Optional[str] = None
    pol: str
    pod: str
    etd: datetime
    eta: Optional[datetime] = None
    is_dg: bool
    dg_class: Optional[str] = None
    dg_un: Optional[str] = None
    remark: Optional[str] = None
    
    # Cargo Details (화물 정보) - 합계
    container_type: Optional[str] = None
    container_qty: int = 0
    total_qty: int = 0
    total_weight: float = 0
    total_cbm: float = 0
    invoice_value: float = 0
    
    # Cargo Details (개별 화물 리스트)
    cargo_details: List[CargoDetailResponse] = []
    
    # Additional Details (부가 정보)
    export_cc: bool = False
    import_cc: bool = False
    shipping_insurance: bool = False
    pickup_required: bool = False
    pickup_address: Optional[str] = None
    delivery_required: bool = False
    delivery_address: Optional[str] = None
    
    # 입찰 정보
    bid_count: int = 0
    my_bid: Optional[BidResponse] = None
    
    class Config:
        from_attributes = True


# ==========================================
# SHIPPER BIDDING MANAGEMENT SCHEMAS
# ==========================================

class ShipperBidItem(BaseModel):
    """화주용 입찰 항목 (익명화된 운송사 정보 포함)"""
    id: int
    rank: int  # 입찰가 기준 순위
    company_masked: str  # 익명화된 회사명 (예: 삼****)
    rating: float = 3.0  # 평점 (0.0 ~ 5.0)
    rating_count: int = 0  # 평점 참여 수
    total_amount_krw: float  # KRW 기준 입찰가
    total_amount: float  # 원래 통화 기준 입찰가
    freight_charge: Optional[float] = None  # 운임
    local_charge: Optional[float] = None  # 로컬비
    other_charge: Optional[float] = None  # 기타비용
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    transit_time: Optional[str] = None
    carrier: Optional[str] = None
    validity_date: Optional[datetime] = None
    remark: Optional[str] = None
    status: str
    submitted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ShipperBiddingListItem(BaseModel):
    """화주용 비딩 목록 항목"""
    id: int
    bidding_no: str
    pol: str
    pod: str
    shipping_type: str
    load_type: str
    etd: datetime
    eta: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: str
    bid_count: int = 0
    min_bid_price_krw: Optional[float] = None  # 최저 입찰가 (KRW)
    avg_bid_price_krw: Optional[float] = None  # 평균 입찰가 (KRW)
    awarded_forwarder: Optional[str] = None  # 낙찰된 운송사 (익명화)
    created_at: datetime
    
    class Config:
        from_attributes = True


class ShipperBiddingListResponse(BaseModel):
    """화주용 비딩 목록 응답"""
    total: int
    page: int
    limit: int
    data: List[ShipperBiddingListItem]


class ShipperBiddingStatsResponse(BaseModel):
    """화주용 비딩 통계"""
    total_count: int
    open_count: int
    closing_soon_count: int
    awarded_count: int
    failed_count: int


class ShipperBiddingBidsResponse(BaseModel):
    """특정 비딩의 입찰 목록 응답"""
    bidding_no: str
    bidding_status: str
    pol: str
    pod: str
    shipping_type: str
    etd: datetime
    deadline: Optional[datetime] = None
    bid_count: int
    bids: List[ShipperBidItem]


class AwardBidRequest(BaseModel):
    """운송사 선정 요청"""
    pass  # bid_id는 URL 파라미터로 전달


class AwardBidResponse(BaseModel):
    """운송사 선정 응답"""
    success: bool
    message: str
    bidding_no: str
    awarded_bid_id: int
    notification_sent: bool = False


# ==========================================
# NOTIFICATION SCHEMAS
# ==========================================

class NotificationResponse(BaseModel):
    """알림 응답"""
    id: int
    notification_type: str
    title: str
    message: Optional[str] = None
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """알림 목록 응답"""
    total: int
    unread_count: int
    data: List[NotificationResponse]


class MarkNotificationReadRequest(BaseModel):
    """알림 읽음 처리 요청"""
    notification_ids: List[int]


# ==========================================
# RATING SCHEMAS
# ==========================================

class RatingCreate(BaseModel):
    """평점 생성 요청"""
    bidding_id: int
    forwarder_id: int
    score: float = Field(..., ge=0.5, le=5.0, description="종합 평점 (0.5 ~ 5.0)")
    price_score: Optional[float] = Field(None, ge=0.5, le=5.0)
    service_score: Optional[float] = Field(None, ge=0.5, le=5.0)
    punctuality_score: Optional[float] = Field(None, ge=0.5, le=5.0)
    communication_score: Optional[float] = Field(None, ge=0.5, le=5.0)
    comment: Optional[str] = Field(None, max_length=500)


class RatingResponse(BaseModel):
    """평점 응답"""
    id: int
    bidding_id: int
    forwarder_id: int
    customer_id: int
    score: float
    price_score: Optional[float] = None
    service_score: Optional[float] = None
    punctuality_score: Optional[float] = None
    communication_score: Optional[float] = None
    comment: Optional[str] = None
    is_visible: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


class ForwarderRatingStats(BaseModel):
    """운송사 평점 통계"""
    forwarder_id: int
    company: str
    average_score: float
    total_ratings: int
    score_distribution: dict  # {5.0: 10, 4.5: 5, ...}
    avg_price_score: Optional[float] = None
    avg_service_score: Optional[float] = None
    avg_punctuality_score: Optional[float] = None
    avg_communication_score: Optional[float] = None


class SubmitRatingResponse(BaseModel):
    """평점 제출 응답"""
    success: bool
    message: str
    rating: Optional[RatingResponse] = None


# ==========================================
# ANALYTICS SCHEMAS
# ==========================================

class AnalyticsPeriod(BaseModel):
    """분석 기간"""
    from_date: str
    to_date: str


class ComparisonData(BaseModel):
    """비교 데이터 (전기 대비)"""
    requests_change: Optional[float] = None  # 요청 건수 변화율 (%)
    cost_change: Optional[float] = None  # 비용 변화율 (%)
    award_rate_change: Optional[float] = None  # 낙찰률 변화


# --- 화주용 분석 스키마 ---

class ShipperAnalyticsSummary(BaseModel):
    """화주용 분석 요약"""
    period: AnalyticsPeriod
    total_requests: int  # 총 요청 건수
    total_biddings: int  # 비딩 진행 건수
    avg_bids_per_request: float  # 요청당 평균 입찰 수
    award_rate: float  # 낙찰률 (%)
    total_cost_krw: float  # 총 운송비 (KRW)
    avg_saving_rate: float  # 평균 절감률 (%)
    comparison: Optional[ComparisonData] = None


class MonthlyTrendItem(BaseModel):
    """월별 추이 항목"""
    month: str  # YYYY-MM
    request_count: int
    bid_count: int
    awarded_count: int
    total_cost_krw: float
    avg_bid_price_krw: float


class ShipperMonthlyTrendResponse(BaseModel):
    """화주용 월별 추이"""
    period: AnalyticsPeriod
    data: List[MonthlyTrendItem]


class CostByTypeItem(BaseModel):
    """운송타입별 비용 항목"""
    shipping_type: str  # ocean, air, truck
    count: int
    total_cost_krw: float
    percentage: float


class ShipperCostByTypeResponse(BaseModel):
    """화주용 운송타입별 비용"""
    period: AnalyticsPeriod
    data: List[CostByTypeItem]


class RouteStatItem(BaseModel):
    """구간별 통계 항목"""
    pol: str
    pod: str
    count: int
    avg_bid_price_krw: float
    min_bid_price_krw: float
    max_bid_price_krw: float


class ShipperRouteStatsResponse(BaseModel):
    """화주용 구간별 통계"""
    period: AnalyticsPeriod
    data: List[RouteStatItem]


class ForwarderRankingItem(BaseModel):
    """운송사 순위 항목"""
    rank: int
    forwarder_id: int
    company_masked: str  # 익명화된 회사명
    awarded_count: int
    total_amount_krw: float
    avg_rating: float
    rating_count: int


class ShipperForwarderRankingResponse(BaseModel):
    """화주용 운송사 순위"""
    period: AnalyticsPeriod
    data: List[ForwarderRankingItem]


# --- 운송사용 분석 스키마 ---

class ForwarderAnalyticsSummary(BaseModel):
    """운송사용 분석 요약"""
    period: AnalyticsPeriod
    total_bids: int  # 총 입찰 건수
    awarded_count: int  # 낙찰 건수
    rejected_count: int  # 탈락 건수
    award_rate: float  # 낙찰률 (%)
    avg_rank: float  # 평균 순위
    total_revenue_krw: float  # 총 수주액 (KRW)
    avg_rating: float  # 평균 평점
    comparison: Optional[ComparisonData] = None


class ForwarderMonthlyTrendItem(BaseModel):
    """운송사 월별 추이 항목"""
    month: str  # YYYY-MM
    bid_count: int
    awarded_count: int
    rejected_count: int
    revenue_krw: float
    avg_rank: float


class ForwarderMonthlyTrendResponse(BaseModel):
    """운송사용 월별 추이"""
    period: AnalyticsPeriod
    data: List[ForwarderMonthlyTrendItem]


class BidStatsByTypeItem(BaseModel):
    """운송타입별 입찰 통계"""
    shipping_type: str
    bid_count: int
    awarded_count: int
    award_rate: float
    total_revenue_krw: float


class ForwarderBidStatsResponse(BaseModel):
    """운송사용 입찰 통계"""
    period: AnalyticsPeriod
    data: List[BidStatsByTypeItem]


class CompetitivenessData(BaseModel):
    """경쟁력 분석 데이터"""
    my_avg_bid_krw: float  # 내 평균 입찰가
    market_avg_bid_krw: float  # 시장 평균 입찰가
    winning_avg_bid_krw: float  # 낙찰 평균가
    price_competitiveness: float  # 가격 경쟁력 (%)
    win_rate_vs_market: float  # 시장 대비 낙찰률


class ForwarderCompetitivenessResponse(BaseModel):
    """운송사용 경쟁력 분석"""
    period: AnalyticsPeriod
    data: CompetitivenessData


class RatingTrendItem(BaseModel):
    """평점 추이 항목"""
    month: str
    avg_score: float
    rating_count: int
    avg_price_score: Optional[float] = None
    avg_service_score: Optional[float] = None
    avg_punctuality_score: Optional[float] = None
    avg_communication_score: Optional[float] = None


class ForwarderRatingTrendResponse(BaseModel):
    """운송사용 평점 추이"""
    period: AnalyticsPeriod
    current_rating: float
    total_ratings: int
    data: List[RatingTrendItem]


# ==========================================
# CONTRACT SCHEMAS
# ==========================================

class ContractCreate(BaseModel):
    """계약 생성 (운송사 선정 시 자동 생성)"""
    bidding_id: int
    awarded_bid_id: int


class ContractConfirmRequest(BaseModel):
    """계약 확정 요청"""
    user_type: str  # shipper, forwarder
    user_id: int


class ContractCancelRequest(BaseModel):
    """계약 취소 요청"""
    user_type: str  # shipper, forwarder
    user_id: int
    reason: Optional[str] = None


class ContractResponse(BaseModel):
    """계약 응답"""
    id: int
    contract_no: str
    bidding_id: int
    awarded_bid_id: int
    customer_id: int
    forwarder_id: int
    
    # 계약 금액
    total_amount_krw: float
    freight_charge: Optional[float] = None
    local_charge: Optional[float] = None
    other_charge: Optional[float] = None
    transit_time: Optional[str] = None
    carrier: Optional[str] = None
    contract_terms: Optional[str] = None
    
    # 확정 상태
    shipper_confirmed: bool
    shipper_confirmed_at: Optional[datetime] = None
    forwarder_confirmed: bool
    forwarder_confirmed_at: Optional[datetime] = None
    
    # 계약 상태
    status: str
    confirmed_at: Optional[datetime] = None
    
    # 취소 정보
    cancelled_by: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ContractDetailResponse(ContractResponse):
    """계약 상세 응답 (관련 정보 포함)"""
    bidding_no: Optional[str] = None
    pol: Optional[str] = None
    pod: Optional[str] = None
    shipping_type: Optional[str] = None
    customer_company: Optional[str] = None
    forwarder_company: Optional[str] = None
    shipment: Optional["ShipmentResponse"] = None


class ContractListItem(BaseModel):
    """계약 목록 항목"""
    id: int
    contract_no: str
    bidding_no: str
    pol: str
    pod: str
    shipping_type: str
    total_amount_krw: float
    status: str
    shipper_confirmed: bool
    forwarder_confirmed: bool
    created_at: datetime


class ContractListResponse(BaseModel):
    """계약 목록 응답"""
    total: int
    page: int
    limit: int
    data: List[ContractListItem]


# ==========================================
# SHIPMENT SCHEMAS
# ==========================================

class ShipmentStatusUpdate(BaseModel):
    """배송 상태 업데이트"""
    status: str  # picked_up, in_transit, arrived_port, customs, out_for_delivery, delivered
    location: Optional[str] = None
    remark: Optional[str] = None
    forwarder_id: int


class ShipmentDeliveryConfirm(BaseModel):
    """배송 완료 확인 (화주)"""
    customer_id: int


class ShipmentTrackingItem(BaseModel):
    """배송 추적 이력 항목"""
    id: int
    status: str
    location: Optional[str] = None
    remark: Optional[str] = None
    updated_by_type: str
    created_at: datetime


class ShipmentResponse(BaseModel):
    """배송 응답"""
    id: int
    shipment_no: str
    contract_id: int
    
    current_status: str
    current_location: Optional[str] = None
    
    estimated_pickup: Optional[datetime] = None
    actual_pickup: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    
    bl_no: Optional[str] = None
    vessel_flight: Optional[str] = None
    
    delivery_confirmed: bool
    delivery_confirmed_at: Optional[datetime] = None
    auto_confirmed: bool
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ShipmentDetailResponse(ShipmentResponse):
    """배송 상세 응답 (추적 이력 포함)"""
    tracking_history: List[ShipmentTrackingItem] = []
    contract_no: Optional[str] = None
    bidding_no: Optional[str] = None
    pol: Optional[str] = None
    pod: Optional[str] = None


class ShipmentListItem(BaseModel):
    """배송 목록 항목"""
    id: int
    shipment_no: str
    contract_no: str
    bidding_no: str
    pol: str
    pod: str
    current_status: str
    estimated_delivery: Optional[datetime] = None
    delivery_confirmed: bool


class ShipmentListResponse(BaseModel):
    """배송 목록 응답"""
    total: int
    page: int
    limit: int
    data: List[ShipmentListItem]


# ==========================================
# SETTLEMENT SCHEMAS
# ==========================================

class SettlementRequest(BaseModel):
    """정산 요청"""
    contract_id: int
    forwarder_id: int


class SettlementResponse(BaseModel):
    """정산 응답"""
    id: int
    settlement_no: str
    contract_id: int
    forwarder_id: int
    customer_id: int
    
    total_amount_krw: float
    service_fee: float
    net_amount: float
    
    status: str
    requested_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    remark: Optional[str] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class SettlementListItem(BaseModel):
    """정산 목록 항목"""
    id: int
    settlement_no: str
    contract_no: str
    bidding_no: str
    total_amount_krw: float
    net_amount: float
    status: str
    requested_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SettlementListResponse(BaseModel):
    """정산 목록 응답"""
    total: int
    page: int
    limit: int
    data: List[SettlementListItem]


class SettlementSummary(BaseModel):
    """정산 요약 (대시보드용)"""
    total_completed: float
    total_pending: float
    count_completed: int
    count_pending: int


# ==========================================
# SETTLEMENT DISPUTE SCHEMAS
# ==========================================

class DisputeRequest(BaseModel):
    """분쟁 제기 요청"""
    customer_id: int
    reason: str
    evidence: Optional[str] = None


class DisputeResponse(BaseModel):
    """분쟁 응답 요청"""
    forwarder_id: int
    response: str
    proposed_amount: Optional[float] = None


class DisputeResolveRequest(BaseModel):
    """분쟁 해결 요청"""
    resolution_type: str  # agreement, mediation, cancel
    resolution_note: str
    final_amount: Optional[float] = None
    resolved_by: Optional[int] = None


class DisputeDetailResponse(BaseModel):
    """분쟁 상세 응답"""
    settlement_id: int
    settlement_no: str
    status: str
    
    customer_id: int
    customer_name: Optional[str] = None
    forwarder_id: int
    forwarder_name: Optional[str] = None
    
    original_amount_krw: float
    service_fee: float
    adjusted_amount_krw: Optional[float] = None
    final_net_amount: float
    
    disputed_at: Optional[datetime] = None
    dispute_reason: Optional[str] = None
    dispute_evidence: Optional[str] = None
    
    forwarder_response: Optional[str] = None
    forwarder_response_at: Optional[datetime] = None
    
    resolved_at: Optional[datetime] = None
    resolution_type: Optional[str] = None
    resolution_note: Optional[str] = None
    resolved_by: Optional[int] = None
    
    days_since_dispute: Optional[int] = None
    auto_resolve_in_days: Optional[int] = None


class DisputeListItem(BaseModel):
    """분쟁 목록 항목"""
    settlement_id: int
    settlement_no: str
    status: str
    customer_name: Optional[str] = None
    forwarder_name: Optional[str] = None
    original_amount_krw: float
    dispute_reason: Optional[str] = None
    disputed_at: Optional[datetime] = None
    has_response: bool
    resolved_at: Optional[datetime] = None
    resolution_type: Optional[str] = None


class DisputeListResponse(BaseModel):
    """분쟁 목록 응답"""
    total: int
    page: int
    limit: int
    total_pages: int
    disputes: List[DisputeListItem]


# ==========================================
# MESSAGE SCHEMAS
# ==========================================

class MessageCreate(BaseModel):
    """메시지 생성"""
    bidding_id: int
    sender_type: str  # shipper, forwarder
    sender_id: int
    recipient_type: str  # shipper, forwarder
    recipient_id: int
    content: str


class MessageResponse(BaseModel):
    """메시지 응답"""
    id: int
    bidding_id: int
    sender_type: str
    sender_id: int
    recipient_type: str
    recipient_id: int
    content: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    
    # 추가 정보
    sender_name: Optional[str] = None
    sender_company: Optional[str] = None
    
    class Config:
        from_attributes = True


class MessageThreadResponse(BaseModel):
    """메시지 스레드 응답"""
    bidding_id: int
    bidding_no: str
    pol: str
    pod: str
    messages: List[MessageResponse]
    unread_count: int


class UnreadMessagesResponse(BaseModel):
    """읽지 않은 메시지 응답"""
    total_unread: int
    threads: List[MessageThreadResponse]


# ==========================================
# FAVORITE ROUTE SCHEMAS
# ==========================================

class FavoriteRouteCreate(BaseModel):
    """즐겨찾기 구간 생성"""
    customer_id: int
    pol: str
    pod: str
    shipping_type: Optional[str] = None
    alias: Optional[str] = None


class FavoriteRouteResponse(BaseModel):
    """즐겨찾기 구간 응답"""
    id: int
    customer_id: int
    pol: str
    pod: str
    shipping_type: Optional[str] = None
    alias: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteRouteListResponse(BaseModel):
    """즐겨찾기 구간 목록"""
    data: List[FavoriteRouteResponse]


# ==========================================
# BID TEMPLATE SCHEMAS
# ==========================================

class BidTemplateCreate(BaseModel):
    """입찰 템플릿 생성"""
    forwarder_id: int
    name: str
    pol: Optional[str] = None
    pod: Optional[str] = None
    shipping_type: Optional[str] = None
    base_freight: Optional[float] = None
    base_local: Optional[float] = None
    base_other: Optional[float] = None
    transit_time: Optional[str] = None
    carrier: Optional[str] = None
    default_remark: Optional[str] = None


class BidTemplateResponse(BaseModel):
    """입찰 템플릿 응답"""
    id: int
    forwarder_id: int
    name: str
    pol: Optional[str] = None
    pod: Optional[str] = None
    shipping_type: Optional[str] = None
    base_freight: Optional[float] = None
    base_local: Optional[float] = None
    base_other: Optional[float] = None
    transit_time: Optional[str] = None
    carrier: Optional[str] = None
    default_remark: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BidTemplateListResponse(BaseModel):
    """입찰 템플릿 목록"""
    data: List[BidTemplateResponse]


# ==========================================
# BOOKMARKED BIDDING SCHEMAS
# ==========================================

class BookmarkBiddingRequest(BaseModel):
    """비딩 북마크 요청"""
    forwarder_id: int
    bidding_id: int


class BookmarkedBiddingResponse(BaseModel):
    """북마크된 비딩 응답"""
    id: int
    forwarder_id: int
    bidding_id: int
    bidding_no: str
    pol: str
    pod: str
    shipping_type: str
    deadline: Optional[datetime] = None
    status: str
    created_at: datetime


class BookmarkedBiddingListResponse(BaseModel):
    """북마크된 비딩 목록"""
    data: List[BookmarkedBiddingResponse]


# ==========================================
# QUOTE REQUEST UPDATE SCHEMAS
# ==========================================

class QuoteRequestUpdate(BaseModel):
    """운송 요청 수정"""
    trade_mode: Optional[str] = None
    shipping_type: Optional[str] = None
    load_type: Optional[str] = None
    incoterms: Optional[str] = None
    pol: Optional[str] = None
    pod: Optional[str] = None
    etd: Optional[str] = None
    is_dg: Optional[bool] = None
    dg_class: Optional[str] = None
    dg_un: Optional[str] = None
    pickup_required: Optional[bool] = None
    pickup_address: Optional[str] = None
    delivery_required: Optional[bool] = None
    delivery_address: Optional[str] = None
    remark: Optional[str] = None


class QuoteRequestCopyRequest(BaseModel):
    """운송 요청 복사"""
    customer_id: int
    new_etd: Optional[str] = None


# ==========================================
# RECOMMENDATION SCHEMAS
# ==========================================

class RecommendedForwarder(BaseModel):
    """추천 포워더"""
    forwarder_id: int
    company_masked: str
    rating: float
    rating_count: int
    awarded_count: int  # 해당 구간 낙찰 횟수
    avg_price_krw: float  # 평균 입찰가
    reason: str  # 추천 사유


class ForwarderRecommendationResponse(BaseModel):
    """포워더 추천 응답"""
    pol: str
    pod: str
    shipping_type: Optional[str] = None
    recommendations: List[RecommendedForwarder]


class RecommendedBidding(BaseModel):
    """추천 비딩"""
    bidding_id: int
    bidding_no: str
    pol: str
    pod: str
    shipping_type: str
    deadline: Optional[datetime] = None
    avg_bid_price_krw: Optional[float] = None
    bid_count: int
    reason: str  # 추천 사유


class BiddingRecommendationResponse(BaseModel):
    """비딩 추천 응답"""
    forwarder_id: int
    recommendations: List[RecommendedBidding]


class PriceGuideResponse(BaseModel):
    """구간별 가격 가이드"""
    pol: str
    pod: str
    shipping_type: Optional[str] = None
    sample_count: int
    avg_price_krw: float
    min_price_krw: float
    max_price_krw: float
    median_price_krw: float


# ==========================================
# QUICK QUOTATION / FREIGHT ESTIMATE SCHEMAS
# ==========================================

class FreightRateItem(BaseModel):
    """개별 운임 항목"""
    code: str
    name: str
    name_ko: Optional[str] = None
    rate: Optional[float] = None
    currency: str
    unit: str


class FreightGroupBreakdown(BaseModel):
    """운임 그룹별 breakdown"""
    group_name: str
    items: List[FreightRateItem]
    subtotal_usd: float = 0
    subtotal_krw: float = 0
    subtotal_eur: float = 0


class QuickQuotationResponse(BaseModel):
    """Quick Quotation 응답 (운임 자동완성)"""
    quick_quotation: bool
    message: Optional[str] = None
    guide: Optional[str] = None
    
    # Quick Quotation = Y인 경우
    carrier: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    container_type: Optional[str] = None
    container_name: Optional[str] = None
    
    # 운임 breakdown
    ocean_freight: Optional[FreightGroupBreakdown] = None
    origin_local: Optional[FreightGroupBreakdown] = None
    
    # 합계
    total_usd: float = 0
    total_krw: float = 0
    total_eur: float = 0
    
    note: Optional[str] = None
    
    # KRW 환산 총액
    total_krw_converted: float = 0
    exchange_rates_used: Optional[dict] = None
    
    # Quick Quotation = N인 경우 - 유효한 운임 데이터 기간 안내
    available_from: Optional[str] = None
    available_to: Optional[str] = None