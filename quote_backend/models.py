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
    status = Column(String(20), default="open")  # open, closed, awarded, cancelled
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quote_request = relationship("QuoteRequest", back_populates="bidding")
    
    def __repr__(self):
        return f"<Bidding {self.bidding_no}>"
