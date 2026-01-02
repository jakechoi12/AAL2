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
    total_amount: float = Field(..., description="Total bid amount in USD")
    freight_charge: Optional[float] = Field(None, description="Freight charge")
    local_charge: Optional[float] = Field(None, description="Local charges")
    other_charge: Optional[float] = Field(None, description="Other charges")
    validity_date: Optional[str] = Field(None, description="Quote validity date YYYY-MM-DD")
    transit_time: Optional[str] = Field(None, max_length=50, description="Expected transit time")
    remark: Optional[str] = Field(None, description="Additional remarks/conditions")


class BidCreate(BidBase):
    bidding_id: int


class BidUpdate(BidBase):
    pass


class BidResponse(BidBase):
    id: int
    bidding_id: int
    forwarder_id: int
    status: str
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
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
    shipping_type: str
    load_type: str
    etd: datetime
    deadline: Optional[datetime] = None
    status: str
    bid_count: int = 0
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
    trade_mode: str
    shipping_type: str
    load_type: str
    incoterms: Optional[str] = None
    pol: str
    pod: str
    etd: datetime
    eta: Optional[datetime] = None
    is_dg: bool
    remark: Optional[str] = None
    
    # 입찰 정보
    bid_count: int = 0
    my_bid: Optional[BidResponse] = None
    
    class Config:
        from_attributes = True