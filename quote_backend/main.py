"""
FastAPI Backend - Quote Request System
Main Application Entry Point
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import random
import string
import os

from database import get_db, engine
from models import Base, Port, ContainerType, TruckType, Incoterm, Customer, QuoteRequest, CargoDetail, Bidding, Forwarder, Bid
from schemas import (
    PortResponse, ContainerTypeResponse, TruckTypeResponse, IncotermResponse,
    QuoteRequestCreate, QuoteRequestResponse, QuoteSubmitResponse, APIResponse,
    BiddingResponse,
    # Forwarder schemas
    ForwarderCreate, ForwarderLogin, ForwarderResponse, ForwarderAuthResponse,
    # Bid schemas
    BidCreate, BidUpdate, BidResponse, BidWithForwarderResponse, BidSubmitResponse,
    # Bidding List schemas
    BiddingListItem, BiddingListResponse, BiddingStatsResponse, BiddingDetailResponse
)
from pdf_generator import RFQPDFGenerator
import hashlib
import secrets
import bcrypt


# ==========================================
# PASSWORD UTILITY FUNCTIONS
# ==========================================

def hash_password(password: str) -> str:
    """
    비밀번호를 bcrypt로 해시화
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    비밀번호 검증
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Quote Request API",
    description="API for handling international shipping quote requests",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def generate_request_number() -> str:
    """Generate unique request number: QR-YYYYMMDD-XXX"""
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.digits, k=3))
    return f"QR-{date_str}-{random_str}"


def parse_datetime(date_str: str) -> datetime:
    """Parse date string to datetime object"""
    if not date_str:
        return None
    
    # Try different formats
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Invalid date format: {date_str}")


def generate_bidding_no(trade_mode: str, shipping_type: str, db: Session) -> str:
    """
    Generate unique Bidding Number
    Format: [Trade Mode 2자리][Shipping Type 3자리][Sequence 5자리]
    
    Examples:
    - EXSEA00000 (Export + Ocean)
    - IMAIR00001 (Import + Air)
    - DOTRK00000 (Domestic + Truck)
    """
    # Trade Mode mapping (2 digits)
    trade_map = {
        "export": "EX",
        "import": "IM",
        "domestic": "DO"
    }
    
    # Shipping Type mapping (3 digits)
    ship_map = {
        "ocean": "SEA",
        "air": "AIR",
        "truck": "TRK",
        "all": "ALL"
    }
    
    prefix = trade_map.get(trade_mode, "XX") + ship_map.get(shipping_type, "XXX")
    
    # Find the last bidding number with this prefix
    last_bidding = db.query(Bidding).filter(
        Bidding.bidding_no.like(f"{prefix}%")
    ).order_by(Bidding.bidding_no.desc()).first()
    
    if last_bidding:
        # Extract sequence and increment
        last_seq = int(last_bidding.bidding_no[-5:])
        new_seq = str(last_seq + 1).zfill(5)
    else:
        new_seq = "00000"
    
    return f"{prefix}{new_seq}"


def calculate_deadline(etd: datetime, shipping_type: str) -> datetime:
    """
    Calculate quotation submission deadline based on shipping type
    
    Rules:
    - Ocean: ETD - 4 days
    - Air: ETD - 1 day
    - Truck/All: ETD - 1 day (default)
    
    Time is set to 18:00 KST
    """
    if shipping_type == "ocean":
        deadline = etd - timedelta(days=4)
    elif shipping_type == "air":
        deadline = etd - timedelta(days=1)
    else:
        deadline = etd - timedelta(days=1)  # Default for truck, all
    
    # Set time to 18:00
    deadline = deadline.replace(hour=18, minute=0, second=0, microsecond=0)
    
    return deadline


# ==========================================
# ROOT ENDPOINT
# ==========================================

@app.get("/")
def root():
    return {
        "message": "Quote Request API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ==========================================
# REFERENCE DATA ENDPOINTS
# ==========================================

@app.get("/api/ports", response_model=List[PortResponse], tags=["Reference Data"])
def get_ports(
    port_type: Optional[str] = None,
    country_code: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get list of ports/airports for POL/POD autocomplete
    
    - port_type: filter by 'ocean', 'air', or 'both'
    - country_code: filter by country (e.g., 'KR', 'CN', 'US')
    - search: search by name or code
    - limit: max number of results (default 50, max 200)
    """
    query = db.query(Port).filter(Port.is_active == True)
    
    if port_type:
        if port_type == "both":
            query = query.filter(Port.port_type.in_(["ocean", "air", "both"]))
        else:
            query = query.filter(Port.port_type.in_([port_type, "both"]))
    
    if country_code:
        query = query.filter(Port.country_code == country_code.upper())
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Port.name.ilike(search_term)) |
            (Port.name_ko.ilike(search_term)) |
            (Port.code.ilike(search_term))
        )
    
    # Apply limit (max 200)
    limit = min(limit, 200)
    return query.order_by(Port.country_code, Port.name).limit(limit).all()


@app.get("/api/container-types", response_model=List[ContainerTypeResponse], tags=["Reference Data"])
def get_container_types(db: Session = Depends(get_db)):
    """Get list of container types for FCL shipments"""
    return db.query(ContainerType).filter(
        ContainerType.is_active == True
    ).order_by(ContainerType.sort_order).all()


@app.get("/api/truck-types", response_model=List[TruckTypeResponse], tags=["Reference Data"])
def get_truck_types(db: Session = Depends(get_db)):
    """Get list of truck types for FTL shipments"""
    return db.query(TruckType).filter(
        TruckType.is_active == True
    ).order_by(TruckType.sort_order).all()


@app.get("/api/incoterms", response_model=List[IncotermResponse], tags=["Reference Data"])
def get_incoterms(db: Session = Depends(get_db)):
    """Get list of Incoterms"""
    return db.query(Incoterm).filter(
        Incoterm.is_active == True
    ).order_by(Incoterm.sort_order).all()


# ==========================================
# QUOTE REQUEST ENDPOINTS
# ==========================================

@app.post("/api/quote/request", response_model=QuoteSubmitResponse, tags=["Quote"])
def submit_quote_request(
    request_data: QuoteRequestCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a new quote request
    
    This endpoint receives the complete quote request form data and stores it in the database.
    """
    try:
        # Check if customer exists by email
        customer = db.query(Customer).filter(
            Customer.email == request_data.customer.email
        ).first()
        
        if not customer:
            # Create new customer
            customer = Customer(
                company=request_data.customer.company,
                job_title=request_data.customer.job_title,
                name=request_data.customer.name,
                email=request_data.customer.email,
                phone=request_data.customer.phone
            )
            db.add(customer)
            db.flush()  # Get customer ID
        else:
            # Update existing customer info
            customer.company = request_data.customer.company
            customer.job_title = request_data.customer.job_title
            customer.name = request_data.customer.name
            customer.phone = request_data.customer.phone
        
        # Generate request number
        request_number = generate_request_number()
        
        # Ensure unique request number
        while db.query(QuoteRequest).filter(QuoteRequest.request_number == request_number).first():
            request_number = generate_request_number()
        
        # Parse dates (both ETD and ETA are required)
        etd = parse_datetime(request_data.etd)
        eta = parse_datetime(request_data.eta)
        
        # Create quote request
        quote_request = QuoteRequest(
            request_number=request_number,
            trade_mode=request_data.trade_mode,
            shipping_type=request_data.shipping_type,
            load_type=request_data.load_type,
            incoterms=request_data.incoterms,
            pol=request_data.pol,
            pod=request_data.pod,
            etd=etd,
            eta=eta,
            is_dg=request_data.is_dg,
            dg_class=request_data.dg_class,
            dg_un=request_data.dg_un,
            export_cc=request_data.export_cc,
            import_cc=request_data.import_cc,
            shipping_insurance=request_data.shipping_insurance,
            pickup_required=request_data.pickup_required,
            pickup_address=request_data.pickup_address,
            delivery_required=request_data.delivery_required,
            delivery_address=request_data.delivery_address,
            invoice_value=request_data.invoice_value,
            remark=request_data.remark,
            status="pending",
            customer_id=customer.id
        )
        db.add(quote_request)
        db.flush()  # Get quote_request ID
        
        # Create cargo details
        for idx, cargo_data in enumerate(request_data.cargo):
            cargo = CargoDetail(
                quote_request_id=quote_request.id,
                row_index=idx,
                container_type=cargo_data.container_type,
                truck_type=cargo_data.truck_type,
                length=cargo_data.length,
                width=cargo_data.width,
                height=cargo_data.height,
                qty=cargo_data.qty,
                gross_weight=cargo_data.gross_weight,
                cbm=cargo_data.cbm,
                volume_weight=cargo_data.volume_weight,
                chargeable_weight=cargo_data.chargeable_weight
            )
            db.add(cargo)
        
        db.flush()  # Ensure cargo details are saved
        
        # ==========================================
        # BIDDING & PDF GENERATION
        # ==========================================
        
        # Generate Bidding No
        bidding_no = generate_bidding_no(request_data.trade_mode, request_data.shipping_type, db)
        
        # Calculate deadline (Ocean: ETD-4days, Air: ETD-1day)
        deadline = calculate_deadline(etd, request_data.shipping_type)
        
        # Generate PDF
        pdf_dir = Path(__file__).parent / "generated_pdfs"
        pdf_path = str(pdf_dir / f"RFQ_{bidding_no}.pdf")
        
        try:
            # Refresh quote_request to include relationships
            db.refresh(quote_request)
            
            pdf_generator = RFQPDFGenerator(bidding_no, quote_request, deadline)
            pdf_generator.generate(pdf_path)
        except Exception as pdf_error:
            # Log error but don't fail the request
            print(f"PDF generation error: {pdf_error}")
            pdf_path = None
        
        # Create Bidding record
        bidding = Bidding(
            bidding_no=bidding_no,
            quote_request_id=quote_request.id,
            pdf_path=pdf_path,
            deadline=deadline,
            status="open"
        )
        db.add(bidding)
        
        db.commit()
        
        return QuoteSubmitResponse(
            success=True,
            message="Quote request submitted successfully. RFQ generated.",
            request_number=request_number,
            quote_request_id=quote_request.id,
            bidding_no=bidding_no,
            pdf_url=f"/api/quote/rfq/{bidding_no}/pdf" if pdf_path else None,
            deadline=deadline.strftime("%Y-%m-%d %H:%M") if deadline else None
        )
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.put("/api/quote/update/{bidding_no}", response_model=QuoteSubmitResponse, tags=["Quote"])
def update_quote_request(
    bidding_no: str,
    request_data: QuoteRequestCreate,
    db: Session = Depends(get_db)
):
    """
    Update an existing quote request by bidding number
    
    This endpoint updates the quote request associated with the given bidding number
    and regenerates the PDF.
    """
    try:
        # Find the bidding record
        bidding = db.query(Bidding).filter(Bidding.bidding_no == bidding_no).first()
        
        if not bidding:
            raise HTTPException(status_code=404, detail=f"Bidding number {bidding_no} not found")
        
        # Get the associated quote request
        quote_request = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
        
        if not quote_request:
            raise HTTPException(status_code=404, detail="Quote request not found")
        
        # Update customer info
        customer = quote_request.customer
        customer.company = request_data.customer.company
        customer.job_title = request_data.customer.job_title
        customer.name = request_data.customer.name
        customer.phone = request_data.customer.phone
        
        # Parse dates
        etd = parse_datetime(request_data.etd)
        eta = parse_datetime(request_data.eta)
        
        # Update quote request fields
        quote_request.trade_mode = request_data.trade_mode
        quote_request.shipping_type = request_data.shipping_type
        quote_request.load_type = request_data.load_type
        quote_request.incoterms = request_data.incoterms
        quote_request.pol = request_data.pol
        quote_request.pod = request_data.pod
        quote_request.etd = etd
        quote_request.eta = eta
        quote_request.is_dg = request_data.is_dg
        quote_request.dg_class = request_data.dg_class
        quote_request.dg_un = request_data.dg_un
        quote_request.export_cc = request_data.export_cc
        quote_request.import_cc = request_data.import_cc
        quote_request.shipping_insurance = request_data.shipping_insurance
        quote_request.pickup_required = request_data.pickup_required
        quote_request.pickup_address = request_data.pickup_address
        quote_request.delivery_required = request_data.delivery_required
        quote_request.delivery_address = request_data.delivery_address
        quote_request.invoice_value = request_data.invoice_value
        quote_request.remark = request_data.remark
        quote_request.updated_at = datetime.now()
        
        # Delete old cargo details and create new ones
        db.query(CargoDetail).filter(CargoDetail.quote_request_id == quote_request.id).delete()
        
        for idx, cargo_data in enumerate(request_data.cargo):
            cargo = CargoDetail(
                quote_request_id=quote_request.id,
                row_index=idx,
                container_type=cargo_data.container_type,
                truck_type=cargo_data.truck_type,
                length=cargo_data.length,
                width=cargo_data.width,
                height=cargo_data.height,
                qty=cargo_data.qty,
                gross_weight=cargo_data.gross_weight,
                cbm=cargo_data.cbm,
                volume_weight=cargo_data.volume_weight,
                chargeable_weight=cargo_data.chargeable_weight
            )
            db.add(cargo)
        
        db.flush()
        
        # Recalculate deadline
        deadline = calculate_deadline(etd, request_data.shipping_type)
        bidding.deadline = deadline
        bidding.updated_at = datetime.now()
        
        # Regenerate PDF
        pdf_dir = Path(__file__).parent / "generated_pdfs"
        pdf_path = str(pdf_dir / f"RFQ_{bidding_no}.pdf")
        
        try:
            db.refresh(quote_request)
            pdf_generator = RFQPDFGenerator(bidding_no, quote_request, deadline)
            pdf_generator.generate(pdf_path)
            bidding.pdf_path = pdf_path
        except Exception as pdf_error:
            print(f"PDF regeneration error: {pdf_error}")
        
        db.commit()
        
        return QuoteSubmitResponse(
            success=True,
            message="Quote request updated successfully. RFQ regenerated.",
            request_number=quote_request.request_number,
            quote_request_id=quote_request.id,
            bidding_no=bidding_no,
            pdf_url=f"/api/quote/rfq/{bidding_no}/pdf" if bidding.pdf_path else None,
            deadline=deadline.strftime("%Y-%m-%d %H:%M") if deadline else None
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/quote/requests", tags=["Quote"])
def get_quote_requests(
    status: Optional[str] = None,
    trade_mode: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get list of quote requests with filters
    """
    query = db.query(QuoteRequest).join(Customer)
    
    if status:
        query = query.filter(QuoteRequest.status == status)
    
    if trade_mode:
        query = query.filter(QuoteRequest.trade_mode == trade_mode)
    
    total = query.count()
    requests = query.order_by(QuoteRequest.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [
            {
                "id": r.id,
                "request_number": r.request_number,
                "trade_mode": r.trade_mode,
                "shipping_type": r.shipping_type,
                "load_type": r.load_type,
                "pol": r.pol,
                "pod": r.pod,
                "etd": r.etd.isoformat() if r.etd else None,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "customer_company": r.customer.company,
                "customer_name": r.customer.name
            }
            for r in requests
        ]
    }


@app.get("/api/quote/request/{request_id}", response_model=QuoteRequestResponse, tags=["Quote"])
def get_quote_request(request_id: int, db: Session = Depends(get_db)):
    """
    Get detailed quote request by ID
    """
    quote_request = db.query(QuoteRequest).filter(QuoteRequest.id == request_id).first()
    
    if not quote_request:
        raise HTTPException(status_code=404, detail="Quote request not found")
    
    return quote_request


@app.patch("/api/quote/request/{request_id}/status", tags=["Quote"])
def update_quote_status(
    request_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """
    Update quote request status
    
    Valid statuses: pending, processing, quoted, accepted, rejected, cancelled
    """
    valid_statuses = ["pending", "processing", "quoted", "accepted", "rejected", "cancelled"]
    
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    quote_request = db.query(QuoteRequest).filter(QuoteRequest.id == request_id).first()
    
    if not quote_request:
        raise HTTPException(status_code=404, detail="Quote request not found")
    
    quote_request.status = status
    db.commit()
    
    return APIResponse(
        success=True,
        message=f"Status updated to '{status}'",
        data={"request_id": request_id, "new_status": status}
    )


# ==========================================
# BIDDING & PDF ENDPOINTS
# ==========================================

@app.get("/api/quote/rfq/{bidding_no}/pdf", tags=["Bidding"])
def download_rfq_pdf(bidding_no: str, db: Session = Depends(get_db)):
    """
    Download RFQ PDF by Bidding Number
    """
    bidding = db.query(Bidding).filter(Bidding.bidding_no == bidding_no).first()
    
    if not bidding:
        raise HTTPException(status_code=404, detail="Bidding not found")
    
    if not bidding.pdf_path or not os.path.exists(bidding.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(
        path=bidding.pdf_path,
        media_type="application/pdf",
        filename=f"RFQ_{bidding_no}.pdf"
    )


@app.get("/api/quote/bidding/{bidding_no}", response_model=BiddingResponse, tags=["Bidding"])
def get_bidding(bidding_no: str, db: Session = Depends(get_db)):
    """
    Get bidding details by Bidding Number
    """
    bidding = db.query(Bidding).filter(Bidding.bidding_no == bidding_no).first()
    
    if not bidding:
        raise HTTPException(status_code=404, detail="Bidding not found")
    
    return bidding


@app.get("/api/quote/biddings", tags=["Bidding"])
def get_biddings(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get list of biddings with filters
    """
    query = db.query(Bidding)
    
    if status:
        query = query.filter(Bidding.status == status)
    
    total = query.count()
    biddings = query.order_by(Bidding.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [
            {
                "id": b.id,
                "bidding_no": b.bidding_no,
                "quote_request_id": b.quote_request_id,
                "deadline": b.deadline.isoformat() if b.deadline else None,
                "status": b.status,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "has_pdf": bool(b.pdf_path and os.path.exists(b.pdf_path))
            }
            for b in biddings
        ]
    }


# ==========================================
# FORWARDER AUTH ENDPOINTS
# ==========================================

def generate_simple_token(email: str) -> str:
    """Generate a simple token for forwarder authentication"""
    random_part = secrets.token_hex(16)
    hash_input = f"{email}:{random_part}:{datetime.now().isoformat()}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:32]


def get_forwarder_from_token(token: str, db: Session) -> Optional[Forwarder]:
    """
    간단한 토큰 검증 (실제 프로덕션에서는 JWT 등 사용 권장)
    현재는 헤더에서 forwarder_id를 직접 받는 방식으로 간소화
    """
    # 이 구현에서는 X-Forwarder-ID 헤더를 사용
    return None


@app.post("/api/forwarder/register", response_model=ForwarderAuthResponse, tags=["Forwarder"])
def register_forwarder(
    forwarder_data: ForwarderCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new forwarder
    
    이메일 + 비밀번호 인증 방식
    """
    try:
        # Check if email already exists
        existing = db.query(Forwarder).filter(Forwarder.email == forwarder_data.email).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
        
        # Hash password
        password_hashed = hash_password(forwarder_data.password)
        
        # Create new forwarder
        forwarder = Forwarder(
            company=forwarder_data.company,
            business_no=forwarder_data.business_no,
            name=forwarder_data.name,
            email=forwarder_data.email,
            phone=forwarder_data.phone,
            password_hash=password_hashed,
            is_verified=True
        )
        db.add(forwarder)
        db.commit()
        db.refresh(forwarder)
        
        # Generate token
        token = generate_simple_token(forwarder.email)
        
        return ForwarderAuthResponse(
            success=True,
            message="회원가입이 완료되었습니다.",
            forwarder=ForwarderResponse.model_validate(forwarder),
            token=token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"등록 실패: {str(e)}")


@app.post("/api/forwarder/login", response_model=ForwarderAuthResponse, tags=["Forwarder"])
def login_forwarder(
    login_data: ForwarderLogin,
    db: Session = Depends(get_db)
):
    """
    Login forwarder by email and password
    
    이메일 + 비밀번호 인증 방식
    """
    forwarder = db.query(Forwarder).filter(Forwarder.email == login_data.email).first()
    
    if not forwarder:
        raise HTTPException(status_code=404, detail="등록되지 않은 이메일입니다. 회원가입을 해주세요.")
    
    # 기존에 password_hash가 없는 사용자 처리 (하위 호환)
    if not forwarder.password_hash:
        raise HTTPException(status_code=400, detail="비밀번호가 설정되지 않았습니다. 다시 등록해주세요.")
    
    # Verify password
    if not verify_password(login_data.password, forwarder.password_hash):
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
    
    # Generate token
    token = generate_simple_token(forwarder.email)
    
    return ForwarderAuthResponse(
        success=True,
        message="로그인 성공",
        forwarder=ForwarderResponse.model_validate(forwarder),
        token=token
    )


@app.get("/api/forwarder/profile/{forwarder_id}", response_model=ForwarderResponse, tags=["Forwarder"])
def get_forwarder_profile(
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """Get forwarder profile by ID"""
    forwarder = db.query(Forwarder).filter(Forwarder.id == forwarder_id).first()
    
    if not forwarder:
        raise HTTPException(status_code=404, detail="Forwarder not found")
    
    return forwarder


# ==========================================
# BIDDING LIST ENDPOINTS (for Forwarders)
# ==========================================

@app.get("/api/bidding/stats", response_model=BiddingStatsResponse, tags=["Bidding List"])
def get_bidding_stats(db: Session = Depends(get_db)):
    """
    Get bidding statistics for dashboard
    
    - total_count: 전체 Bidding 건수
    - open_count: 진행중인 입찰 건수
    - closing_soon_count: 24시간 이내 마감 예정 건수
    - awarded_count: 낙찰 완료 건수
    - failed_count: 유찰 건수 (closed + cancelled + expired)
    """
    now = datetime.now()
    tomorrow = now + timedelta(hours=24)
    
    total_count = db.query(Bidding).count()
    
    open_count = db.query(Bidding).filter(Bidding.status == "open").count()
    
    closing_soon_count = db.query(Bidding).filter(
        Bidding.status == "open",
        Bidding.deadline <= tomorrow,
        Bidding.deadline > now
    ).count()
    
    awarded_count = db.query(Bidding).filter(Bidding.status == "awarded").count()
    
    failed_count = db.query(Bidding).filter(
        Bidding.status.in_(["closed", "cancelled", "expired"])
    ).count()
    
    return BiddingStatsResponse(
        total_count=total_count,
        open_count=open_count,
        closing_soon_count=closing_soon_count,
        awarded_count=awarded_count,
        failed_count=failed_count
    )


@app.get("/api/bidding/list", response_model=BiddingListResponse, tags=["Bidding List"])
def get_bidding_list(
    status: Optional[str] = None,
    shipping_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    forwarder_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get paginated list of biddings for forwarders
    
    - status: filter by bidding status (open, closed, awarded, cancelled, expired)
    - shipping_type: filter by shipping type (ocean, air, truck)
    - search: search by bidding_no
    - page: page number (1-based)
    - limit: items per page
    - forwarder_id: optional, to check if forwarder has already bid
    """
    # Base query with join to get quote request and customer info
    query = db.query(Bidding).join(
        QuoteRequest, Bidding.quote_request_id == QuoteRequest.id
    ).join(
        Customer, QuoteRequest.customer_id == Customer.id
    )
    
    # Apply filters
    if status:
        query = query.filter(Bidding.status == status)
    
    if shipping_type:
        query = query.filter(QuoteRequest.shipping_type == shipping_type)
    
    if search:
        query = query.filter(Bidding.bidding_no.ilike(f"%{search}%"))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    biddings = query.order_by(Bidding.created_at.desc()).offset(offset).limit(limit).all()
    
    # Build response
    items = []
    for b in biddings:
        qr = b.quote_request
        
        # Count bids for this bidding
        bid_count = db.query(Bid).filter(
            Bid.bidding_id == b.id,
            Bid.status == "submitted"
        ).count()
        
        # Check if forwarder has already bid
        my_bid_status = None
        if forwarder_id:
            my_bid = db.query(Bid).filter(
                Bid.bidding_id == b.id,
                Bid.forwarder_id == forwarder_id
            ).first()
            if my_bid:
                my_bid_status = my_bid.status
        
        items.append(BiddingListItem(
            id=b.id,
            bidding_no=b.bidding_no,
            customer_company=qr.customer.company,
            pol=qr.pol,
            pod=qr.pod,
            shipping_type=qr.shipping_type,
            load_type=qr.load_type,
            etd=qr.etd,
            deadline=b.deadline,
            status=b.status,
            bid_count=bid_count,
            my_bid_status=my_bid_status
        ))
    
    return BiddingListResponse(
        total=total,
        page=page,
        limit=limit,
        data=items
    )


@app.get("/api/bidding/{bidding_no}/detail", response_model=BiddingDetailResponse, tags=["Bidding List"])
def get_bidding_detail(
    bidding_no: str,
    forwarder_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get detailed bidding information including quote request details
    
    - forwarder_id: optional, to include forwarder's own bid
    """
    bidding = db.query(Bidding).filter(Bidding.bidding_no == bidding_no).first()
    
    if not bidding:
        raise HTTPException(status_code=404, detail="Bidding not found")
    
    qr = bidding.quote_request
    customer = qr.customer
    
    # Count bids
    bid_count = db.query(Bid).filter(
        Bid.bidding_id == bidding.id,
        Bid.status == "submitted"
    ).count()
    
    # Get forwarder's bid if forwarder_id provided
    my_bid = None
    if forwarder_id:
        bid = db.query(Bid).filter(
            Bid.bidding_id == bidding.id,
            Bid.forwarder_id == forwarder_id
        ).first()
        if bid:
            my_bid = BidResponse.model_validate(bid)
    
    return BiddingDetailResponse(
        id=bidding.id,
        bidding_no=bidding.bidding_no,
        status=bidding.status,
        deadline=bidding.deadline,
        created_at=bidding.created_at,
        pdf_url=f"/api/quote/rfq/{bidding_no}/pdf" if bidding.pdf_path else None,
        customer_company=customer.company,
        customer_name=customer.name,
        trade_mode=qr.trade_mode,
        shipping_type=qr.shipping_type,
        load_type=qr.load_type,
        incoterms=qr.incoterms,
        pol=qr.pol,
        pod=qr.pod,
        etd=qr.etd,
        eta=qr.eta,
        is_dg=qr.is_dg,
        remark=qr.remark,
        bid_count=bid_count,
        my_bid=my_bid
    )


# ==========================================
# BID ENDPOINTS (for Forwarders)
# ==========================================

@app.post("/api/bid/submit", response_model=BidSubmitResponse, tags=["Bid"])
def submit_bid(
    bid_data: BidCreate,
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """
    Submit a new bid for a bidding
    
    - forwarder_id: 포워더 ID (헤더 또는 쿼리로 전달)
    - 마감 전까지만 제출 가능
    - 동일 포워더가 동일 비딩에 중복 제출 불가 (수정은 PUT 사용)
    """
    try:
        # Verify forwarder exists
        forwarder = db.query(Forwarder).filter(Forwarder.id == forwarder_id).first()
        if not forwarder:
            raise HTTPException(status_code=404, detail="Forwarder not found")
        
        # Verify bidding exists and is open
        bidding = db.query(Bidding).filter(Bidding.id == bid_data.bidding_id).first()
        if not bidding:
            raise HTTPException(status_code=404, detail="Bidding not found")
        
        if bidding.status != "open":
            raise HTTPException(status_code=400, detail="Bidding is not open for bids")
        
        # Check deadline
        if bidding.deadline and datetime.now() > bidding.deadline:
            raise HTTPException(status_code=400, detail="Bidding deadline has passed")
        
        # Check for existing bid
        existing_bid = db.query(Bid).filter(
            Bid.bidding_id == bid_data.bidding_id,
            Bid.forwarder_id == forwarder_id
        ).first()
        
        if existing_bid:
            raise HTTPException(
                status_code=400, 
                detail="You have already submitted a bid. Use PUT /api/bid/{bid_id} to update."
            )
        
        # Parse validity date
        validity_date = None
        if bid_data.validity_date:
            validity_date = parse_datetime(bid_data.validity_date)
        
        # Create bid
        bid = Bid(
            bidding_id=bid_data.bidding_id,
            forwarder_id=forwarder_id,
            total_amount=bid_data.total_amount,
            freight_charge=bid_data.freight_charge,
            local_charge=bid_data.local_charge,
            other_charge=bid_data.other_charge,
            validity_date=validity_date,
            transit_time=bid_data.transit_time,
            remark=bid_data.remark,
            status="submitted",
            submitted_at=datetime.now()
        )
        db.add(bid)
        db.commit()
        db.refresh(bid)
        
        return BidSubmitResponse(
            success=True,
            message="Bid submitted successfully",
            bid=BidResponse.model_validate(bid)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit bid: {str(e)}")


@app.put("/api/bid/{bid_id}", response_model=BidSubmitResponse, tags=["Bid"])
def update_bid(
    bid_id: int,
    bid_data: BidUpdate,
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """
    Update an existing bid
    
    - 본인의 입찰만 수정 가능
    - 마감 전까지만 수정 가능
    - 낙찰/거절된 입찰은 수정 불가
    """
    try:
        # Get bid
        bid = db.query(Bid).filter(Bid.id == bid_id).first()
        if not bid:
            raise HTTPException(status_code=404, detail="Bid not found")
        
        # Verify ownership
        if bid.forwarder_id != forwarder_id:
            raise HTTPException(status_code=403, detail="You can only update your own bids")
        
        # Check bid status
        if bid.status in ["awarded", "rejected"]:
            raise HTTPException(status_code=400, detail=f"Cannot update bid with status '{bid.status}'")
        
        # Check bidding deadline
        bidding = db.query(Bidding).filter(Bidding.id == bid.bidding_id).first()
        if bidding.deadline and datetime.now() > bidding.deadline:
            raise HTTPException(status_code=400, detail="Bidding deadline has passed")
        
        if bidding.status != "open":
            raise HTTPException(status_code=400, detail="Bidding is no longer open")
        
        # Update bid
        bid.total_amount = bid_data.total_amount
        bid.freight_charge = bid_data.freight_charge
        bid.local_charge = bid_data.local_charge
        bid.other_charge = bid_data.other_charge
        if bid_data.validity_date:
            bid.validity_date = parse_datetime(bid_data.validity_date)
        bid.transit_time = bid_data.transit_time
        bid.remark = bid_data.remark
        bid.updated_at = datetime.now()
        
        db.commit()
        db.refresh(bid)
        
        return BidSubmitResponse(
            success=True,
            message="Bid updated successfully",
            bid=BidResponse.model_validate(bid)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update bid: {str(e)}")


@app.get("/api/bid/my-bids", tags=["Bid"])
def get_my_bids(
    forwarder_id: int,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get list of forwarder's own bids
    
    - status: filter by bid status (draft, submitted, awarded, rejected)
    """
    query = db.query(Bid).filter(Bid.forwarder_id == forwarder_id)
    
    if status:
        query = query.filter(Bid.status == status)
    
    total = query.count()
    offset = (page - 1) * limit
    bids = query.order_by(Bid.created_at.desc()).offset(offset).limit(limit).all()
    
    # Build response with bidding info
    result = []
    for bid in bids:
        bidding = db.query(Bidding).filter(Bidding.id == bid.bidding_id).first()
        qr = bidding.quote_request if bidding else None
        
        result.append({
            "id": bid.id,
            "bidding_id": bid.bidding_id,
            "bidding_no": bidding.bidding_no if bidding else None,
            "pol": qr.pol if qr else None,
            "pod": qr.pod if qr else None,
            "shipping_type": qr.shipping_type if qr else None,
            "total_amount": float(bid.total_amount),
            "status": bid.status,
            "bidding_status": bidding.status if bidding else None,
            "deadline": bidding.deadline.isoformat() if bidding and bidding.deadline else None,
            "submitted_at": bid.submitted_at.isoformat() if bid.submitted_at else None,
            "created_at": bid.created_at.isoformat() if bid.created_at else None
        })
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": result
    }


@app.get("/api/bidding/{bidding_no}/bids", tags=["Bid"])
def get_bidding_bids(
    bidding_no: str,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all bids for a specific bidding (화주용)
    
    - 봉인 입찰: 마감 후에만 조회 가능
    - customer_id로 본인 확인 (간소화된 인증)
    """
    bidding = db.query(Bidding).filter(Bidding.bidding_no == bidding_no).first()
    
    if not bidding:
        raise HTTPException(status_code=404, detail="Bidding not found")
    
    # 봉인 입찰: 마감 전에는 조회 불가 (화주도)
    # 단, 마감이 지났거나 awarded 상태면 조회 가능
    if bidding.status == "open" and bidding.deadline and datetime.now() < bidding.deadline:
        raise HTTPException(
            status_code=403, 
            detail="Bids are sealed until deadline. Please wait until the deadline passes."
        )
    
    # Get all submitted bids with forwarder info
    bids = db.query(Bid).filter(
        Bid.bidding_id == bidding.id,
        Bid.status.in_(["submitted", "awarded", "rejected"])
    ).order_by(Bid.total_amount.asc()).all()
    
    result = []
    for bid in bids:
        forwarder = db.query(Forwarder).filter(Forwarder.id == bid.forwarder_id).first()
        result.append({
            "id": bid.id,
            "forwarder_id": bid.forwarder_id,
            "forwarder_company": forwarder.company if forwarder else None,
            "forwarder_name": forwarder.name if forwarder else None,
            "forwarder_phone": forwarder.phone if forwarder else None,
            "total_amount": float(bid.total_amount),
            "freight_charge": float(bid.freight_charge) if bid.freight_charge else None,
            "local_charge": float(bid.local_charge) if bid.local_charge else None,
            "other_charge": float(bid.other_charge) if bid.other_charge else None,
            "transit_time": bid.transit_time,
            "validity_date": bid.validity_date.isoformat() if bid.validity_date else None,
            "remark": bid.remark,
            "status": bid.status,
            "submitted_at": bid.submitted_at.isoformat() if bid.submitted_at else None
        })
    
    return {
        "bidding_no": bidding_no,
        "bidding_status": bidding.status,
        "total_bids": len(result),
        "bids": result
    }


# ==========================================
# AWARD ENDPOINTS (for Shippers)
# ==========================================

@app.post("/api/bidding/{bidding_no}/award", response_model=APIResponse, tags=["Award"])
def award_bid(
    bidding_no: str,
    bid_id: int,
    db: Session = Depends(get_db)
):
    """
    Award a bid to a forwarder (화주용)
    
    - bidding_no: Bidding 번호
    - bid_id: 낙찰할 Bid ID
    """
    try:
        # Get bidding
        bidding = db.query(Bidding).filter(Bidding.bidding_no == bidding_no).first()
        if not bidding:
            raise HTTPException(status_code=404, detail="Bidding not found")
        
        if bidding.status == "awarded":
            raise HTTPException(status_code=400, detail="Bidding has already been awarded")
        
        if bidding.status not in ["open", "closed"]:
            raise HTTPException(status_code=400, detail=f"Cannot award bidding with status '{bidding.status}'")
        
        # Get the bid to award
        bid = db.query(Bid).filter(
            Bid.id == bid_id,
            Bid.bidding_id == bidding.id
        ).first()
        
        if not bid:
            raise HTTPException(status_code=404, detail="Bid not found for this bidding")
        
        if bid.status != "submitted":
            raise HTTPException(status_code=400, detail=f"Cannot award bid with status '{bid.status}'")
        
        # Award the bid
        bid.status = "awarded"
        bid.updated_at = datetime.now()
        
        # Update bidding status
        bidding.status = "awarded"
        bidding.awarded_bid_id = bid.id
        bidding.updated_at = datetime.now()
        
        # Reject all other bids
        other_bids = db.query(Bid).filter(
            Bid.bidding_id == bidding.id,
            Bid.id != bid.id,
            Bid.status == "submitted"
        ).all()
        
        for other_bid in other_bids:
            other_bid.status = "rejected"
            other_bid.updated_at = datetime.now()
        
        db.commit()
        
        # Get forwarder info for response
        forwarder = db.query(Forwarder).filter(Forwarder.id == bid.forwarder_id).first()
        
        return APIResponse(
            success=True,
            message=f"Bid awarded successfully to {forwarder.company if forwarder else 'forwarder'}",
            data={
                "bidding_no": bidding_no,
                "awarded_bid_id": bid.id,
                "forwarder_id": bid.forwarder_id,
                "forwarder_company": forwarder.company if forwarder else None,
                "total_amount": float(bid.total_amount)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to award bid: {str(e)}")


@app.post("/api/bidding/{bidding_no}/close", response_model=APIResponse, tags=["Award"])
def close_bidding(
    bidding_no: str,
    db: Session = Depends(get_db)
):
    """
    Close a bidding without awarding (유찰 처리)
    """
    bidding = db.query(Bidding).filter(Bidding.bidding_no == bidding_no).first()
    
    if not bidding:
        raise HTTPException(status_code=404, detail="Bidding not found")
    
    if bidding.status != "open":
        raise HTTPException(status_code=400, detail=f"Cannot close bidding with status '{bidding.status}'")
    
    bidding.status = "closed"
    bidding.updated_at = datetime.now()
    
    # Reject all submitted bids
    bids = db.query(Bid).filter(
        Bid.bidding_id == bidding.id,
        Bid.status == "submitted"
    ).all()
    
    for bid in bids:
        bid.status = "rejected"
        bid.updated_at = datetime.now()
    
    db.commit()
    
    return APIResponse(
        success=True,
        message="Bidding closed successfully",
        data={"bidding_no": bidding_no, "status": "closed", "rejected_bids": len(bids)}
    )


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":
    import uvicorn
    # reload=False for subprocess compatibility
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)

