"""
Database Models - Quote Request System
Reference Data (Master Tables) + Transaction Tables
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


# ==========================================
# ENUMS
# ==========================================

class TradeModeEnum(str, enum.Enum):
    export = "export"
    import_ = "import"
    domestic = "domestic"


class ShippingTypeEnum(str, enum.Enum):
    all = "all"
    ocean = "ocean"
    air = "air"
    truck = "truck"


class QuoteStatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    quoted = "quoted"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"


class BiddingStatusEnum(str, enum.Enum):
    open = "open"
    closed = "closed"
    awarded = "awarded"
    cancelled = "cancelled"
    expired = "expired"


class BidStatusEnum(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    awarded = "awarded"
    rejected = "rejected"


# ==========================================
# REFERENCE DATA (MASTER TABLES)
# ==========================================

class Port(Base):
    """
    POL/POD Reference Table
    Stores port and airport information for autocomplete
    """
    __tablename__ = "ports"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)  # e.g., KRPUS, USLAX
    name = Column(String(100), nullable=False)  # e.g., Busan Port
    name_ko = Column(String(100), nullable=True)  # Korean name
    country = Column(String(50), nullable=False)  # e.g., South Korea
    country_code = Column(String(2), nullable=False)  # e.g., KR
    port_type = Column(String(20), nullable=False)  # ocean, air, both
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Port {self.code}: {self.name}>"


class ContainerType(Base):
    """
    Container Types for FCL shipments
    Extended with ISO standards, dimensions, and weight specifications
    """
    __tablename__ = "container_types"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)  # e.g., 20DC, 40DC, 40HC
    name = Column(String(50), nullable=False)  # e.g., 20 Dry Container
    abbreviation = Column(String(20), nullable=True)  # 약어 표시용 (e.g., 20'GP, 40'HC)
    description = Column(String(200), nullable=True)
    
    # Size and Category
    size = Column(String(10), nullable=True)  # 20, 40, 4H (40HC)
    category = Column(String(10), nullable=True)  # FR, DC, OT, RF, TK
    size_teu = Column(DECIMAL(3, 1), nullable=True)  # TEU size (1.0, 2.0)
    
    # Standard Codes
    iso_standard = Column(String(20), nullable=True)  # ISO code: 22P1, 22G0, 42P1 etc
    customs_port_standard = Column(String(20), nullable=True)  # Customs/Port code: 22PC, 22GP etc
    china_send_standard = Column(String(20), nullable=True)  # China send code: 22PF, GP20 etc
    china_receive = Column(String(20), nullable=True)  # China receive code: 22PF, 22GP etc
    
    # Weight Specifications (kg)
    tare_weight = Column(DECIMAL(10, 2), nullable=True)  # Container self weight
    max_weight_kg = Column(Integer, nullable=True)  # Max cargo weight (max_payload)
    
    # Internal Dimensions (mm)
    length_mm = Column(Integer, nullable=True)  # Internal length
    width_mm = Column(Integer, nullable=True)  # Internal width
    height_mm = Column(Integer, nullable=True)  # Internal height
    
    # Volume
    max_cbm = Column(DECIMAL(5, 2), nullable=True)  # Max CBM
    cbm_limit = Column(Boolean, default=False)  # CBM limit flag (O=True, X=False)
    
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<ContainerType {self.code}: {self.name}>"


class TruckType(Base):
    """
    Truck Types for FTL shipments
    """
    __tablename__ = "truck_types"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)  # e.g., 5T_WING, 11T_WING
    name = Column(String(50), nullable=False)  # e.g., 5T Wing Body
    abbreviation = Column(String(20), nullable=True)  # 약어 표시용 (e.g., 5T 윙, 11T 냉동)
    description = Column(String(200), nullable=True)
    max_weight_kg = Column(Integer, nullable=True)
    max_cbm = Column(DECIMAL(5, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<TruckType {self.code}: {self.name}>"


class Incoterm(Base):
    """
    Incoterms Reference Table
    """
    __tablename__ = "incoterms"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), unique=True, nullable=False)  # e.g., EXW, FOB
    name = Column(String(50), nullable=False)  # e.g., Ex Works
    description = Column(String(500), nullable=True)
    description_ko = Column(String(500), nullable=True)
    seller_responsibility = Column(String(200), nullable=True)
    buyer_responsibility = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Incoterm {self.code}: {self.name}>"


class FreightCategory(Base):
    """
    Freight Category - 운임 대분류
    OCEAN, AIR, PORT CHARGES, LOCAL CHARGES 등
    """
    __tablename__ = "freight_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)  # e.g., OCEAN, AIR
    name_en = Column(String(100), nullable=False)  # e.g., Ocean Freight
    name_ko = Column(String(100), nullable=True)  # e.g., 해상운임
    shipping_types = Column(String(50), nullable=True)  # e.g., "ocean,air,truck"
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    freight_codes = relationship("FreightCode", back_populates="category")
    
    def __repr__(self):
        return f"<FreightCategory {self.code}: {self.name_en}>"


class FreightCode(Base):
    """
    Freight Code - 운임 코드 마스터
    FRT, BAF, THC, DOC 등 66개 운임 항목
    """
    __tablename__ = "freight_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)  # e.g., FRT, BAF
    category_id = Column(Integer, ForeignKey("freight_categories.id"), nullable=False)
    group_name = Column(String(50), nullable=True)  # e.g., FREIGHT, SURCHARGE, ETC
    name_en = Column(String(100), nullable=False)  # e.g., OCEAN FREIGHT
    name_ko = Column(String(100), nullable=True)  # e.g., 해상 운임
    vat_applicable = Column(Boolean, default=False)  # VAT 적용 여부
    default_currency = Column(String(3), default="USD")  # 기본 통화
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("FreightCategory", back_populates="freight_codes")
    allowed_units = relationship("FreightCodeUnit", back_populates="freight_code", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FreightCode {self.code}: {self.name_en}>"


class FreightUnit(Base):
    """
    Freight Unit - 운임 단위 마스터
    R/TON, CNTR, G.W, C.W, Day, B/L(AWB), Pallet, Box, Shipment 등
    """
    __tablename__ = "freight_units"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)  # e.g., R/TON, CNTR
    name_en = Column(String(50), nullable=True)  # e.g., Revenue Ton
    name_ko = Column(String(50), nullable=True)  # e.g., 운임톤
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    freight_code_units = relationship("FreightCodeUnit", back_populates="unit")
    
    def __repr__(self):
        return f"<FreightUnit {self.code}>"


class FreightCodeUnit(Base):
    """
    Freight Code - Unit 다대다 관계 테이블
    운임 코드별로 허용되는 단위 목록
    """
    __tablename__ = "freight_code_units"
    
    id = Column(Integer, primary_key=True, index=True)
    freight_code_id = Column(Integer, ForeignKey("freight_codes.id"), nullable=False)
    freight_unit_id = Column(Integer, ForeignKey("freight_units.id"), nullable=False)
    is_default = Column(Boolean, default=False)  # 기본 단위 여부
    
    # Relationships
    freight_code = relationship("FreightCode", back_populates="allowed_units")
    unit = relationship("FreightUnit", back_populates="freight_code_units")
    
    def __repr__(self):
        return f"<FreightCodeUnit code_id={self.freight_code_id} unit_id={self.freight_unit_id}>"


# ==========================================
# TRANSACTION TABLES
# ==========================================

class Customer(Base):
    """
    Customer Information
    """
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(50), nullable=False)
    job_title = Column(String(30), nullable=True)
    name = Column(String(30), nullable=False)
    email = Column(String(30), nullable=False, unique=True, index=True)
    phone = Column(String(30), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quote_requests = relationship("QuoteRequest", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer {self.company}: {self.name}>"


class QuoteRequest(Base):
    """
    Main Quote Request Table
    """
    __tablename__ = "quote_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_number = Column(String(20), unique=True, nullable=False, index=True)  # QR-20250130-001
    
    # Trade & Shipping
    trade_mode = Column(String(20), nullable=False)  # export, import, domestic
    shipping_type = Column(String(20), nullable=False)  # all, ocean, air, truck
    load_type = Column(String(20), nullable=False)  # FCL, LCL, Bulk, FTL, LTL, Air
    incoterms = Column(String(10), nullable=True)
    
    # Schedules
    pol = Column(String(50), nullable=False)
    pod = Column(String(50), nullable=False)
    etd = Column(DateTime, nullable=False)
    eta = Column(DateTime, nullable=True)
    
    # DG (Dangerous Goods)
    is_dg = Column(Boolean, default=False)
    dg_class = Column(String(1), nullable=True)
    dg_un = Column(String(4), nullable=True)
    
    # Additional Details
    export_cc = Column(Boolean, default=False)
    import_cc = Column(Boolean, default=False)
    shipping_insurance = Column(Boolean, default=False)
    pickup_required = Column(Boolean, default=False)
    pickup_address = Column(String(100), nullable=True)
    delivery_required = Column(Boolean, default=False)
    delivery_address = Column(String(100), nullable=True)
    invoice_value = Column(DECIMAL(15, 2), default=0)
    
    # Remark
    remark = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, processing, quoted, accepted, rejected, cancelled
    
    # Foreign Keys
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="quote_requests")
    cargo_details = relationship("CargoDetail", back_populates="quote_request", cascade="all, delete-orphan")
    bidding = relationship("Bidding", back_populates="quote_request", uselist=False)
    
    def __repr__(self):
        return f"<QuoteRequest {self.request_number}>"


class CargoDetail(Base):
    """
    Cargo Details - Multiple rows per quote request
    """
    __tablename__ = "cargo_details"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_request_id = Column(Integer, ForeignKey("quote_requests.id"), nullable=False)
    row_index = Column(Integer, nullable=False, default=0)
    
    # Container/Truck Type (FCL/FTL)
    container_type = Column(String(30), nullable=True)
    truck_type = Column(String(30), nullable=True)
    
    # Dimensions (LCL/Air)
    length = Column(Integer, nullable=True)  # CM
    width = Column(Integer, nullable=True)   # CM
    height = Column(Integer, nullable=True)  # CM
    
    # Quantities & Weights
    qty = Column(Integer, default=1)
    gross_weight = Column(DECIMAL(10, 2), nullable=True)  # KG
    cbm = Column(DECIMAL(10, 2), nullable=True)
    volume_weight = Column(Integer, nullable=True)  # Air only
    chargeable_weight = Column(Integer, nullable=True)  # Air only
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    quote_request = relationship("QuoteRequest", back_populates="cargo_details")
    
    def __repr__(self):
        return f"<CargoDetail #{self.row_index} for QR#{self.quote_request_id}>"


class Bidding(Base):
    """
    Bidding Management - RFQ sent to forwarders
    Bidding No Format: [Trade 2자리][Shipping 3자리][Sequence 5자리]
    Example: IMAIR00000, EXSEA00001
    """
    __tablename__ = "biddings"
    
    id = Column(Integer, primary_key=True, index=True)
    bidding_no = Column(String(10), unique=True, nullable=False, index=True)  # EXSEA00000
    quote_request_id = Column(Integer, ForeignKey("quote_requests.id"), nullable=False)
    pdf_path = Column(String(255), nullable=True)  # Path to generated PDF
    deadline = Column(DateTime, nullable=True)  # Quotation submission deadline
    status = Column(String(20), default="open")  # open, closed, awarded, cancelled, expired
    awarded_bid_id = Column(Integer, ForeignKey("bids.id"), nullable=True)  # 낙찰된 입찰 ID
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quote_request = relationship("QuoteRequest", back_populates="bidding")
    bids = relationship("Bid", back_populates="bidding", foreign_keys="Bid.bidding_id")
    awarded_bid = relationship("Bid", foreign_keys=[awarded_bid_id], post_update=True)
    
    def __repr__(self):
        return f"<Bidding {self.bidding_no}>"


class Forwarder(Base):
    """
    Forwarder Information - 포워더 정보
    """
    __tablename__ = "forwarders"
    
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(100), nullable=False)
    business_no = Column(String(20), nullable=True)  # 사업자등록번호
    name = Column(String(50), nullable=False)  # 담당자명
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=False)
    password_hash = Column(String(255), nullable=True)  # bcrypt 해시된 비밀번호
    is_verified = Column(Boolean, default=False)
    
    # Rating System (0.0 ~ 5.0, 0.5 단위)
    rating = Column(DECIMAL(2, 1), default=3.0)  # 평균 평점
    rating_count = Column(Integer, default=0)  # 평점 참여 수
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bids = relationship("Bid", back_populates="forwarder")
    
    def __repr__(self):
        return f"<Forwarder {self.company}: {self.name}>"


class Bid(Base):
    """
    Bid - 포워더의 입찰 정보
    """
    __tablename__ = "bids"
    
    id = Column(Integer, primary_key=True, index=True)
    bidding_id = Column(Integer, ForeignKey("biddings.id"), nullable=False)
    forwarder_id = Column(Integer, ForeignKey("forwarders.id"), nullable=False)
    
    # 입찰 금액 (KRW 기준)
    total_amount = Column(DECIMAL(15, 2), nullable=False)  # KRW 기준 총액
    total_amount_krw = Column(DECIMAL(15, 0), nullable=True)  # KRW 환산 금액
    freight_charge = Column(DECIMAL(15, 2), nullable=True)  # 운임
    local_charge = Column(DECIMAL(15, 2), nullable=True)  # 로컬비용
    other_charge = Column(DECIMAL(15, 2), nullable=True)  # 기타비용
    
    # 추가 정보
    validity_date = Column(DateTime, nullable=True)  # 견적 유효기간
    transit_time = Column(String(50), nullable=True)  # 예상 운송기간
    carrier = Column(String(100), nullable=True)  # 선사/항공사
    etd = Column(DateTime, nullable=True)  # 포워더 제안 ETD
    eta = Column(DateTime, nullable=True)  # 포워더 제안 ETA
    remark = Column(Text, nullable=True)  # 비고/조건
    
    # 상태
    status = Column(String(20), default="draft")  # draft, submitted, awarded, rejected
    submitted_at = Column(DateTime, nullable=True)  # 제출일시
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bidding = relationship("Bidding", back_populates="bids", foreign_keys=[bidding_id])
    forwarder = relationship("Forwarder", back_populates="bids")
    
    def __repr__(self):
        return f"<Bid #{self.id} for Bidding #{self.bidding_id} by Forwarder #{self.forwarder_id}>"


class Rating(Base):
    """
    Rating - 운송사 평점 시스템
    운송 완료 후 화주가 운송사에 평점을 부여
    """
    __tablename__ = "ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 관련 정보
    bidding_id = Column(Integer, ForeignKey("biddings.id"), nullable=False)
    forwarder_id = Column(Integer, ForeignKey("forwarders.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # 평점 (0.5 ~ 5.0, 0.5 단위)
    score = Column(DECIMAL(2, 1), nullable=False)  # 종합 평점
    
    # 세부 평점 (선택사항)
    price_score = Column(DECIMAL(2, 1), nullable=True)  # 가격 만족도
    service_score = Column(DECIMAL(2, 1), nullable=True)  # 서비스 품질
    punctuality_score = Column(DECIMAL(2, 1), nullable=True)  # 정시성
    communication_score = Column(DECIMAL(2, 1), nullable=True)  # 커뮤니케이션
    
    # 리뷰 내용
    comment = Column(Text, nullable=True)
    
    # 상태
    is_visible = Column(Boolean, default=True)  # 공개 여부
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Rating #{self.id} score={self.score} for Forwarder #{self.forwarder_id}>"


class Notification(Base):
    """
    Notification - 알림 시스템
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 수신자 정보 (forwarder 또는 customer)
    recipient_type = Column(String(20), nullable=False)  # forwarder, customer
    recipient_id = Column(Integer, nullable=False)
    
    # 알림 내용
    notification_type = Column(String(50), nullable=False)  # bid_awarded, bid_rejected, new_bidding, etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    
    # 관련 데이터
    related_type = Column(String(50), nullable=True)  # bidding, bid, quote_request
    related_id = Column(Integer, nullable=True)
    
    # 상태
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Notification #{self.id} to {self.recipient_type}#{self.recipient_id}>"


# ==========================================
# CONTRACT & SHIPMENT MANAGEMENT
# ==========================================

class ContractStatusEnum(str, enum.Enum):
    pending = "pending"          # 계약 대기 (선정 후 초기 상태)
    confirmed = "confirmed"      # 양측 확정 완료
    active = "active"            # 배송 진행 중
    completed = "completed"      # 배송 완료
    cancelled = "cancelled"      # 취소됨


class ShipmentStatusEnum(str, enum.Enum):
    booked = "booked"                    # 계약 확정됨
    picked_up = "picked_up"              # 화물 픽업 완료
    in_transit = "in_transit"            # 운송 중
    arrived_port = "arrived_port"        # 목적지항 도착
    customs = "customs"                  # 통관 진행 중
    out_for_delivery = "out_for_delivery"  # 배송 출발
    delivered = "delivered"              # 배송 완료
    completed = "completed"              # 화주 확인 완료


class SettlementStatusEnum(str, enum.Enum):
    pending = "pending"          # 정산 대기
    requested = "requested"      # 정산 요청됨
    processing = "processing"    # 처리 중
    completed = "completed"      # 정산 완료
    disputed = "disputed"        # 분쟁 중


class Contract(Base):
    """
    Contract - 계약 관리
    운송사 선정 후 양측 확정 과정 관리
    """
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_no = Column(String(20), unique=True, nullable=False, index=True)  # CT-YYYYMMDD-XXX
    
    # 관련 정보
    bidding_id = Column(Integer, ForeignKey("biddings.id"), nullable=False)
    awarded_bid_id = Column(Integer, ForeignKey("bids.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    forwarder_id = Column(Integer, ForeignKey("forwarders.id"), nullable=False)
    
    # 계약 조건 (입찰 내용 스냅샷)
    total_amount_krw = Column(DECIMAL(15, 0), nullable=False)
    freight_charge = Column(DECIMAL(15, 2), nullable=True)
    local_charge = Column(DECIMAL(15, 2), nullable=True)
    other_charge = Column(DECIMAL(15, 2), nullable=True)
    transit_time = Column(String(50), nullable=True)
    carrier = Column(String(100), nullable=True)
    contract_terms = Column(Text, nullable=True)  # 추가 계약 조건
    
    # 확정 상태
    shipper_confirmed = Column(Boolean, default=False)
    shipper_confirmed_at = Column(DateTime, nullable=True)
    forwarder_confirmed = Column(Boolean, default=False)
    forwarder_confirmed_at = Column(DateTime, nullable=True)
    
    # 계약 상태
    status = Column(String(20), default="pending")  # pending, confirmed, active, completed, cancelled
    confirmed_at = Column(DateTime, nullable=True)  # 양측 모두 확정된 시간
    
    # 취소 정보
    cancelled_by = Column(String(20), nullable=True)  # shipper, forwarder
    cancelled_at = Column(DateTime, nullable=True)
    cancel_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bidding = relationship("Bidding", backref="contract")
    awarded_bid = relationship("Bid")
    customer = relationship("Customer")
    forwarder = relationship("Forwarder")
    shipment = relationship("Shipment", back_populates="contract", uselist=False)
    
    def __repr__(self):
        return f"<Contract {self.contract_no} status={self.status}>"


class Shipment(Base):
    """
    Shipment - 배송 추적 관리
    """
    __tablename__ = "shipments"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_no = Column(String(20), unique=True, nullable=False, index=True)  # SH-YYYYMMDD-XXX
    
    # 관련 정보
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    
    # 현재 상태
    current_status = Column(String(30), default="booked")
    current_location = Column(String(200), nullable=True)
    
    # 일정
    estimated_pickup = Column(DateTime, nullable=True)
    actual_pickup = Column(DateTime, nullable=True)
    estimated_delivery = Column(DateTime, nullable=True)
    actual_delivery = Column(DateTime, nullable=True)
    
    # B/L 또는 AWB 정보
    bl_no = Column(String(50), nullable=True)  # Bill of Lading / Airway Bill
    vessel_flight = Column(String(100), nullable=True)  # 선박명/항공편
    
    # 배송 완료 확인
    delivery_confirmed = Column(Boolean, default=False)
    delivery_confirmed_at = Column(DateTime, nullable=True)
    auto_confirmed = Column(Boolean, default=False)  # 자동 확인 여부
    
    # 알림 관련
    reminder_sent = Column(Boolean, default=False)  # 7일 알림 발송 여부
    reminder_sent_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    contract = relationship("Contract", back_populates="shipment")
    tracking_history = relationship("ShipmentTracking", back_populates="shipment", order_by="ShipmentTracking.created_at")
    
    def __repr__(self):
        return f"<Shipment {self.shipment_no} status={self.current_status}>"


class ShipmentTracking(Base):
    """
    ShipmentTracking - 배송 상태 이력
    """
    __tablename__ = "shipment_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    
    # 상태 정보
    status = Column(String(30), nullable=False)
    location = Column(String(200), nullable=True)
    remark = Column(Text, nullable=True)
    
    # 업데이트 정보
    updated_by_type = Column(String(20), nullable=False)  # forwarder, system
    updated_by_id = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    shipment = relationship("Shipment", back_populates="tracking_history")
    
    def __repr__(self):
        return f"<ShipmentTracking #{self.id} status={self.status}>"


class Settlement(Base):
    """
    Settlement - 정산 관리
    """
    __tablename__ = "settlements"
    
    id = Column(Integer, primary_key=True, index=True)
    settlement_no = Column(String(20), unique=True, nullable=False, index=True)  # ST-YYYYMMDD-XXX
    
    # 관련 정보
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    forwarder_id = Column(Integer, ForeignKey("forwarders.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # 금액 정보
    total_amount_krw = Column(DECIMAL(15, 0), nullable=False)
    service_fee = Column(DECIMAL(15, 0), default=0)  # 플랫폼 수수료
    net_amount = Column(DECIMAL(15, 0), nullable=False)  # 실 정산 금액
    
    # 정산 상태
    status = Column(String(20), default="pending")  # pending, requested, processing, completed, disputed, cancelled
    requested_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 결제 정보
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(100), nullable=True)
    
    # 비고
    remark = Column(Text, nullable=True)
    
    # 분쟁 관련 필드
    disputed_at = Column(DateTime, nullable=True)  # 분쟁 제기 일시
    dispute_reason = Column(Text, nullable=True)  # 분쟁 사유
    dispute_evidence = Column(Text, nullable=True)  # 증빙자료 링크/설명
    
    forwarder_response = Column(Text, nullable=True)  # 포워더 반박 의견
    forwarder_response_at = Column(DateTime, nullable=True)  # 포워더 응답 일시
    
    resolved_at = Column(DateTime, nullable=True)  # 해결 일시
    resolution_type = Column(String(30), nullable=True)  # agreement, mediation, cancel
    resolution_note = Column(Text, nullable=True)  # 해결 내용
    adjusted_amount = Column(DECIMAL(15, 0), nullable=True)  # 조정된 금액
    resolved_by = Column(Integer, nullable=True)  # 해결 처리자 (관리자 ID)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    contract = relationship("Contract")
    forwarder = relationship("Forwarder")
    customer = relationship("Customer")
    
    def __repr__(self):
        return f"<Settlement {self.settlement_no} status={self.status}>"


class Message(Base):
    """
    Message - 화주/포워더 간 메시지
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 관련 비딩 (대화 컨텍스트)
    bidding_id = Column(Integer, ForeignKey("biddings.id"), nullable=False)
    
    # 발신자
    sender_type = Column(String(20), nullable=False)  # shipper, forwarder
    sender_id = Column(Integer, nullable=False)
    
    # 수신자
    recipient_type = Column(String(20), nullable=False)  # shipper, forwarder
    recipient_id = Column(Integer, nullable=False)
    
    # 메시지 내용
    content = Column(Text, nullable=False)
    
    # 읽음 상태
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Message #{self.id} from {self.sender_type} to {self.recipient_type}>"


class FavoriteRoute(Base):
    """
    FavoriteRoute - 화주 즐겨찾기 구간
    """
    __tablename__ = "favorite_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # 구간 정보
    pol = Column(String(50), nullable=False)
    pod = Column(String(50), nullable=False)
    shipping_type = Column(String(20), nullable=True)  # ocean, air, truck
    
    # 별칭
    alias = Column(String(50), nullable=True)  # 예: "중국 상하이 정기편"
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    customer = relationship("Customer")
    
    def __repr__(self):
        return f"<FavoriteRoute {self.pol} → {self.pod}>"


class BidTemplate(Base):
    """
    BidTemplate - 포워더 입찰 템플릿
    """
    __tablename__ = "bid_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    forwarder_id = Column(Integer, ForeignKey("forwarders.id"), nullable=False)
    
    # 템플릿 정보
    name = Column(String(100), nullable=False)  # 템플릿 이름
    
    # 구간 조건
    pol = Column(String(50), nullable=True)
    pod = Column(String(50), nullable=True)
    shipping_type = Column(String(20), nullable=True)
    
    # 기본 견적
    base_freight = Column(DECIMAL(15, 2), nullable=True)
    base_local = Column(DECIMAL(15, 2), nullable=True)
    base_other = Column(DECIMAL(15, 2), nullable=True)
    transit_time = Column(String(50), nullable=True)
    carrier = Column(String(100), nullable=True)
    default_remark = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    forwarder = relationship("Forwarder")
    
    def __repr__(self):
        return f"<BidTemplate {self.name}>"


class BookmarkedBidding(Base):
    """
    BookmarkedBidding - 포워더 관심 비딩
    """
    __tablename__ = "bookmarked_biddings"
    
    id = Column(Integer, primary_key=True, index=True)
    forwarder_id = Column(Integer, ForeignKey("forwarders.id"), nullable=False)
    bidding_id = Column(Integer, ForeignKey("biddings.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    forwarder = relationship("Forwarder")
    bidding = relationship("Bidding")
    
    def __repr__(self):
        return f"<BookmarkedBidding forwarder={self.forwarder_id} bidding={self.bidding_id}>"


# ==========================================
# OCEAN FREIGHT RATE TABLES
# ==========================================

class OceanRateSheet(Base):
    """
    Ocean Rate Sheet - 해상 운임표 (POL-POD 조합별 헤더)
    Quick Quotation 기능을 위한 운임 데이터 관리
    """
    __tablename__ = "ocean_rate_sheets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # POL-POD (Foreign Key to ports)
    pol_id = Column(Integer, ForeignKey("ports.id"), nullable=False, index=True)
    pod_id = Column(Integer, ForeignKey("ports.id"), nullable=False, index=True)
    
    # Carrier (선사) - 기본값 HMM
    carrier = Column(String(100), default="HMM", nullable=False)
    
    # Validity Period (유효기간)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    remark = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    pol = relationship("Port", foreign_keys=[pol_id], lazy="joined")
    pod = relationship("Port", foreign_keys=[pod_id], lazy="joined")
    items = relationship("OceanRateItem", back_populates="sheet", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<OceanRateSheet {self.id}: POL{self.pol_id}->POD{self.pod_id}>"


class OceanRateItem(Base):
    """
    Ocean Rate Item - 해상 운임 항목 (컨테이너별, 비용항목별)
    rate가 NULL이면 Quick Quotation = N
    """
    __tablename__ = "ocean_rate_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Parent Sheet
    sheet_id = Column(Integer, ForeignKey("ocean_rate_sheets.id"), nullable=False, index=True)
    
    # Container Type
    container_type_id = Column(Integer, ForeignKey("container_types.id"), nullable=False, index=True)
    
    # Freight Code (OFR, THC, DOC 등) - 기존 freight_codes 테이블 참조
    freight_code_id = Column(Integer, ForeignKey("freight_codes.id"), nullable=False, index=True)
    
    # Freight Group (Ocean Freight, Origin Local Charges, etc.)
    freight_group = Column(String(50), nullable=False)
    
    # Unit & Currency
    unit = Column(String(10), nullable=False)  # Qty, BL
    currency = Column(String(3), nullable=False)  # USD, KRW, EUR
    
    # Rate (NULL이면 Quick Quotation = N)
    rate = Column(DECIMAL(15, 2), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sheet = relationship("OceanRateSheet", back_populates="items")
    container_type = relationship("ContainerType", lazy="joined")
    freight_code = relationship("FreightCode", lazy="joined")
    
    def __repr__(self):
        return f"<OceanRateItem {self.freight_code_id}: {self.rate} {self.currency}>"


# ==========================================
# TRUCKING RATE TABLE (내륙 운임)
# ==========================================

class TruckingRate(Base):
    """
    Trucking Rate - 내륙 운송 운임
    Pickup/Delivery 옵션 선택 시 운임 조회용
    """
    __tablename__ = "trucking_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 화물 종류 (일반화물 등)
    cargo_type = Column(String(20), default="일반화물", nullable=False)
    
    # 출발 터미널/항구 (Foreign Key to ports)
    origin_port_id = Column(Integer, ForeignKey("ports.id"), nullable=False, index=True)
    
    # 목적지 주소 (도/광역시 > 시/군/구 > 읍/면/동)
    dest_province = Column(String(50), nullable=False, index=True)  # 강원도
    dest_city = Column(String(50), nullable=False, index=True)      # 강릉시
    dest_district = Column(String(50), nullable=False)              # 강포동
    
    # 거리 (km)
    distance_km = Column(Integer, nullable=True)
    
    # 컨테이너별 운임 (KRW)
    rate_20ft = Column(DECIMAL(15, 0), nullable=True)
    rate_40ft = Column(DECIMAL(15, 0), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    origin_port = relationship("Port", lazy="joined")
    
    def __repr__(self):
        return f"<TruckingRate {self.origin_port_id}->{self.dest_province} {self.dest_city}: 20ft={self.rate_20ft}>"