"""
FastAPI Backend - Quote Request System
Main Application Entry Point
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import random
import string
import os
import requests
from functools import lru_cache

# 한국은행 API 환율 조회 함수
BOK_API_BASE = "http://localhost:5000"  # Flask server (bok_backend)

@lru_cache(maxsize=10)
def get_bok_exchange_rate(currency: str, cache_key: str = None) -> float:
    """
    한국은행 API를 통해 환율 조회 (최근 7일 평균)
    cache_key: 캐싱을 위한 날짜 키 (예: "2026-01-13")
    
    Returns: KRW 환율 (1 currency = X KRW)
    """
    default_rates = {"USD": 1450.0, "EUR": 1550.0, "JPY": 9.5, "CNY": 200.0}
    
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        
        # 한국은행 API 호출 (Flask 서버 경유)
        response = requests.get(
            f"{BOK_API_BASE}/api/market/indices",
            params={
                "type": "exchange",
                "itemCode": currency.upper(),
                "startDate": start_date,
                "endDate": end_date,
                "cycle": "D"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # BOK API 응답 형식: {"StatisticSearch": {"row": [...]}}
            stat_search = data.get("StatisticSearch", {})
            rows = stat_search.get("row", [])
            
            if rows and len(rows) > 0:
                # 최신 환율 반환 (row의 마지막 항목)
                latest = rows[-1]
                rate = float(latest.get("DATA_VALUE", 0))
                if rate > 0:
                    print(f"[Exchange Rate] {currency}: {rate} KRW (from BOK API)")
                    return rate
            
            # 기존 형식 호환성: data 배열 체크
            if data.get("data") and len(data["data"]) > 0:
                latest = data["data"][-1]
                rate = float(latest.get("DATA_VALUE", 0))
                if rate > 0:
                    print(f"[Exchange Rate] {currency}: {rate} KRW (from data array)")
                    return rate
        
        # 실패 시 기본값 반환
        print(f"[Exchange Rate] {currency}: Using default {default_rates.get(currency.upper())} (API failed or no data)")
        return default_rates.get(currency.upper(), 1.0)
        
    except Exception as e:
        print(f"[Exchange Rate] Error fetching rate for {currency}: {e}")
        # 기본값 반환
        return default_rates.get(currency.upper(), 1.0)

from database import get_db, engine
from models import (
    Base, Port, ContainerType, TruckType, Incoterm, Customer, QuoteRequest, 
    CargoDetail, Bidding, Forwarder, Bid, Notification, Rating,
    # Freight Master tables
    FreightCategory, FreightCode, FreightUnit, FreightCodeUnit,
    # Contract & Shipment
    Contract, Shipment, ShipmentTracking, Settlement, Message,
    FavoriteRoute, BidTemplate, BookmarkedBidding,
    # Ocean & Trucking Rates
    OceanRateSheet, OceanRateItem, TruckingRate
)
from schemas import (
    PortResponse, ContainerTypeResponse, TruckTypeResponse, IncotermResponse,
    QuoteRequestCreate, QuoteRequestResponse, QuoteSubmitResponse, APIResponse,
    BiddingResponse, CargoDetailResponse,
    # Forwarder schemas
    ForwarderCreate, ForwarderLogin, ForwarderResponse, ForwarderAuthResponse,
    # Bid schemas
    BidCreate, BidUpdate, BidResponse, BidWithForwarderResponse, BidSubmitResponse,
    # Bidding List schemas
    BiddingListItem, BiddingListResponse, BiddingStatsResponse, BiddingDetailResponse,
    # Freight Code schemas
    FreightUnitResponse, FreightCodeResponse, FreightCategoryResponse,
    FreightCategoryWithCodesResponse, FreightCodesListResponse,
    # Shipper Bidding Management schemas
    ShipperBidItem, ShipperBiddingListItem, ShipperBiddingListResponse,
    ShipperBiddingStatsResponse, ShipperBiddingBidsResponse, AwardBidResponse,
    # Notification schemas
    NotificationResponse, NotificationListResponse, MarkNotificationReadRequest,
    # Rating schemas
    RatingCreate, RatingResponse, ForwarderRatingStats, SubmitRatingResponse,
    # Analytics schemas
    AnalyticsPeriod, ShipperAnalyticsSummary, ShipperMonthlyTrendResponse,
    MonthlyTrendItem, ShipperCostByTypeResponse, CostByTypeItem,
    ShipperRouteStatsResponse, RouteStatItem, ShipperForwarderRankingResponse,
    ForwarderRankingItem, ForwarderAnalyticsSummary, ForwarderMonthlyTrendResponse,
    ForwarderMonthlyTrendItem, ForwarderBidStatsResponse, BidStatsByTypeItem,
    ForwarderCompetitivenessResponse, CompetitivenessData,
    ForwarderRatingTrendResponse, RatingTrendItem, ComparisonData,
    # Contract & Shipment schemas
    ContractConfirmRequest, ContractCancelRequest, ContractResponse, 
    ContractDetailResponse, ContractListItem, ContractListResponse,
    ShipmentStatusUpdate, ShipmentDeliveryConfirm, ShipmentTrackingItem,
    ShipmentResponse, ShipmentDetailResponse, ShipmentListItem, ShipmentListResponse,
    SettlementRequest, SettlementResponse, SettlementListItem, SettlementListResponse, SettlementSummary,
    MessageCreate, MessageResponse, MessageThreadResponse, UnreadMessagesResponse,
    FavoriteRouteCreate, FavoriteRouteResponse, FavoriteRouteListResponse,
    BidTemplateCreate, BidTemplateResponse, BidTemplateListResponse,
    BookmarkBiddingRequest, BookmarkedBiddingResponse, BookmarkedBiddingListResponse,
    QuoteRequestUpdate, QuoteRequestCopyRequest,
    RecommendedForwarder, ForwarderRecommendationResponse,
    RecommendedBidding, BiddingRecommendationResponse, PriceGuideResponse,
    # Forwarder Profile schemas
    ForwarderProfileResponse, ForwarderTopRoute, ForwarderShippingModeStats, ForwarderReviewItem
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

# Import and create tables for commerce models FIRST
# (before Base.metadata.create_all to ensure all tables are created)
from commerce_models import (
    Company, CompanyCertification, CommerceUser, Category, Product,
    ProductRFQ, ProductRFQItem, ProductRFQInvitation,
    ProductQuotation, ProductQuotationItem, ProductQuotationRevision,
    ProductTransaction, ProductTransactionItem, ProductTransactionStatusLog,
    CommerceNotification, CommerceMessage
)

# Import commerce router
from commerce_api import router as commerce_router

# Create tables for ALL models (quote_backend + commerce)
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AAL Quote & Commerce API",
    description="API for international shipping quotes and B2B commerce",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Commerce Router
app.include_router(commerce_router)


# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def normalize_container_type(value: str) -> str:
    """
    비표준 컨테이너 타입 값을 표준 abbreviation으로 변환
    다양한 입력 형식을 일관된 형식으로 정규화
    """
    if not value:
        return value
    
    # 대문자 변환 및 특수문자 제거
    normalized = value.upper().replace("'", "").replace("'", "").replace(" ", "").replace("FT", "")
    
    # 표준 매핑 테이블
    mapping = {
        # 20ft Dry Container
        "20GP": "20'GP",
        "20DC": "20'GP",
        "20DRY": "20'GP",
        "20DRYCONTAINER": "20'GP",
        "20STDRY": "20'GP",
        "20STANDARD": "20'GP",
        "22GP": "20'GP",
        "22G0": "20'GP",
        # 40ft Dry Container
        "40GP": "40'GP",
        "40DC": "40'GP",
        "40DRY": "40'GP",
        "40DRYCONTAINER": "40'GP",
        "40STDRY": "40'GP",
        "40STANDARD": "40'GP",
        "42GP": "40'GP",
        "42G0": "40'GP",
        # 40ft High Cube
        "40HC": "40'HC",
        "40HQ": "40'HC",
        "40HIGHCUBE": "40'HC",
        "40HIGH": "40'HC",
        "4HDC": "40'HC",
        "45G0": "40'HC",
        "45GP": "40'HC",
        # 20ft Reefer
        "20RF": "20'RF",
        "20REEFER": "20'RF",
        "22R0": "20'RF",
        # 40ft Reefer
        "40RF": "40'RF",
        "40REEFER": "40'RF",
        "42R0": "40'RF",
        # 40ft Reefer High Cube
        "40RH": "40'RH",
        "40REEFERHC": "40'RH",
        "45R0": "40'RH",
        # 20ft Open Top
        "20OT": "20'OT",
        "20OPENTOP": "20'OT",
        "22U0": "20'OT",
        # 40ft Open Top
        "40OT": "40'OT",
        "40OPENTOP": "40'OT",
        "42U0": "40'OT",
        # 20ft Flat Rack
        "20FR": "20'FR",
        "20FLATRACK": "20'FR",
        "22P1": "20'FR",
        # 40ft Flat Rack
        "40FR": "40'FR",
        "40FLATRACK": "40'FR",
        "42P1": "40'FR",
        # 20ft Tank
        "20TK": "20'TK",
        "20TANK": "20'TK",
        "22K0": "20'TK",
    }
    
    return mapping.get(normalized, value)


def find_container_type(db: Session, ct_value: str):
    """
    다양한 방식으로 컨테이너 타입 검색 (code, abbreviation, name)
    """
    if not ct_value:
        return None
    
    # 1. 먼저 code로 정확히 검색
    container = db.query(ContainerType).filter(
        ContainerType.code == ct_value
    ).first()
    if container:
        return container
    
    # 2. abbreviation으로 검색
    container = db.query(ContainerType).filter(
        ContainerType.abbreviation == ct_value
    ).first()
    if container:
        return container
    
    # 3. name으로 검색 (대소문자 무시)
    container = db.query(ContainerType).filter(
        func.lower(ContainerType.name) == ct_value.lower()
    ).first()
    if container:
        return container
    
    # 4. 정규화된 값으로 다시 검색
    normalized = normalize_container_type(ct_value)
    if normalized != ct_value:
        # abbreviation으로 검색 (정규화 후)
        container = db.query(ContainerType).filter(
            ContainerType.abbreviation == normalized
        ).first()
        if container:
            return container
    
    return None


def generate_cargo_summary(
    shipping_type: str, 
    load_type: str, 
    cargo_details: list, 
    db: Session
) -> Optional[str]:
    """
    Generate cargo summary string based on shipping type and load type.
    
    Examples:
    - FCL (Ocean): "20'GP × 3" or "20'GP × 2, 40'HC × 1"
    - LCL (Ocean): "32.5 CBM"
    - AIR: "1,500 KGS"
    - TRUCK (FTL): "5T윙 × 2"
    """
    if not cargo_details:
        return None
    
    try:
        # FCL - Container based
        if shipping_type == "ocean" and load_type == "FCL":
            # Group by container type (정규화된 값 기준)
            container_counts = {}
            for cargo in cargo_details:
                ct_value = cargo.container_type
                if ct_value:
                    qty = cargo.qty or 1
                    # 정규화된 키 사용
                    normalized_key = normalize_container_type(ct_value)
                    if normalized_key not in container_counts:
                        container_counts[normalized_key] = {"qty": 0, "original": ct_value}
                    container_counts[normalized_key]["qty"] += qty
            
            # Get abbreviations from database
            summaries = []
            for normalized_key, data in container_counts.items():
                # 다양한 방식으로 컨테이너 타입 검색
                container = find_container_type(db, data["original"])
                
                if container and container.abbreviation:
                    abbr = container.abbreviation
                else:
                    # 정규화된 값 사용 (fallback)
                    abbr = normalized_key
                summaries.append(f"{abbr} × {data['qty']}")
            
            return ", ".join(summaries) if summaries else None
        
        # LCL - CBM based
        elif shipping_type == "ocean" and load_type == "LCL":
            total_cbm = sum(
                float(cargo.cbm or 0) * (cargo.qty or 1) 
                for cargo in cargo_details
            )
            if total_cbm > 0:
                return f"{total_cbm:,.1f} CBM"
            return None
        
        # AIR - Chargeable Weight based
        elif shipping_type == "air":
            total_cw = sum(
                int(cargo.chargeable_weight or 0) * (cargo.qty or 1) 
                for cargo in cargo_details
            )
            if total_cw > 0:
                return f"{total_cw:,} KGS"
            return None
        
        # TRUCK - FTL (Truck based)
        elif shipping_type == "truck" and load_type == "FTL":
            # Group by truck type
            truck_counts = {}
            for cargo in cargo_details:
                tt_value = cargo.truck_type
                if tt_value:
                    qty = cargo.qty or 1
                    if tt_value not in truck_counts:
                        truck_counts[tt_value] = {"qty": 0}
                    truck_counts[tt_value]["qty"] += qty
            
            # Get abbreviations from database
            summaries = []
            for tt_value, data in truck_counts.items():
                # 다양한 방식으로 트럭 타입 검색
                truck = db.query(TruckType).filter(
                    (TruckType.code == tt_value) |
                    (TruckType.abbreviation == tt_value) |
                    (func.lower(TruckType.name) == tt_value.lower())
                ).first()
                
                if truck and truck.abbreviation:
                    abbr = truck.abbreviation
                else:
                    abbr = tt_value  # fallback to original value
                summaries.append(f"{abbr} × {data['qty']}")
            
            return ", ".join(summaries) if summaries else None
        
        # TRUCK - LTL (CBM or weight based)
        elif shipping_type == "truck" and load_type == "LTL":
            total_cbm = sum(
                float(cargo.cbm or 0) * (cargo.qty or 1) 
                for cargo in cargo_details
            )
            if total_cbm > 0:
                return f"{total_cbm:,.1f} CBM"
            return None
        
        return None
        
    except Exception as e:
        print(f"Error generating cargo summary: {e}")
        return None


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
def get_forwarder_profile_basic(
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """Get forwarder basic profile by ID"""
    forwarder = db.query(Forwarder).filter(Forwarder.id == forwarder_id).first()
    
    if not forwarder:
        raise HTTPException(status_code=404, detail="Forwarder not found")
    
    return forwarder


# ==========================================
# FORWARDER PROFILE ENDPOINT
# ==========================================

@app.get("/api/forwarders/{forwarder_id}/profile", response_model=ForwarderProfileResponse, tags=["Forwarder Profile"])
def get_forwarder_profile(
    forwarder_id: int,
    limit_reviews: int = 10,
    db: Session = Depends(get_db)
):
    """
    포워더 프로필 상세 조회
    
    - 포워더 기본 정보 및 평점
    - 주요 운송 루트 (Top 5)
    - 운송 모드별 통계
    - 최근 리뷰 목록
    """
    # 포워더 조회
    forwarder = db.query(Forwarder).filter(Forwarder.id == forwarder_id).first()
    if not forwarder:
        raise HTTPException(status_code=404, detail="Forwarder not found")
    
    # 모든 입찰 조회 (submitted 또는 awarded)
    bids = db.query(Bid).filter(
        Bid.forwarder_id == forwarder_id,
        Bid.status.in_(["submitted", "awarded"])
    ).all()
    
    total_bids = len(bids)
    total_awarded = sum(1 for b in bids if b.status == "awarded")
    award_rate = (total_awarded / total_bids * 100) if total_bids > 0 else 0.0
    
    # 주요 루트 계산 (입찰 이력 기반)
    route_counts = {}
    for bid in bids:
        bidding = db.query(Bidding).filter(Bidding.id == bid.bidding_id).first()
        if bidding:
            quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
            if quote_req:
                route_key = (quote_req.pol, quote_req.pod)
                if route_key not in route_counts:
                    route_counts[route_key] = {"count": 0, "awarded": 0}
                route_counts[route_key]["count"] += 1
                if bid.status == "awarded":
                    route_counts[route_key]["awarded"] += 1
    
    # Top 5 루트 정렬
    top_routes = []
    sorted_routes = sorted(route_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:5]
    for (pol, pod), data in sorted_routes:
        top_routes.append(ForwarderTopRoute(
            pol=pol,
            pod=pod,
            count=data["count"],
            awarded_count=data["awarded"]
        ))
    
    # 운송 모드별 통계
    shipping_mode_counts = {}
    for bid in bids:
        bidding = db.query(Bidding).filter(Bidding.id == bid.bidding_id).first()
        if bidding:
            quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
            if quote_req:
                mode = quote_req.shipping_type
                if mode not in shipping_mode_counts:
                    shipping_mode_counts[mode] = {"count": 0, "awarded": 0}
                shipping_mode_counts[mode]["count"] += 1
                if bid.status == "awarded":
                    shipping_mode_counts[mode]["awarded"] += 1
    
    shipping_mode_stats = []
    for mode, data in shipping_mode_counts.items():
        percentage = (data["count"] / total_bids * 100) if total_bids > 0 else 0.0
        shipping_mode_stats.append(ForwarderShippingModeStats(
            shipping_type=mode,
            count=data["count"],
            percentage=round(percentage, 1),
            awarded_count=data["awarded"]
        ))
    
    # 정렬: count 기준 내림차순
    shipping_mode_stats.sort(key=lambda x: x.count, reverse=True)
    
    # 평점 조회 및 분석
    ratings = db.query(Rating).filter(
        Rating.forwarder_id == forwarder_id,
        Rating.is_visible == True
    ).all()
    
    score_distribution = {}
    price_scores = []
    service_scores = []
    punctuality_scores = []
    communication_scores = []
    
    for r in ratings:
        score_key = str(float(r.score))
        score_distribution[score_key] = score_distribution.get(score_key, 0) + 1
        if r.price_score:
            price_scores.append(float(r.price_score))
        if r.service_score:
            service_scores.append(float(r.service_score))
        if r.punctuality_score:
            punctuality_scores.append(float(r.punctuality_score))
        if r.communication_score:
            communication_scores.append(float(r.communication_score))
    
    # 리뷰 목록 조회 (최신순)
    reviews_query = db.query(Rating).filter(
        Rating.forwarder_id == forwarder_id,
        Rating.is_visible == True
    ).order_by(Rating.created_at.desc()).limit(limit_reviews).all()
    
    reviews = []
    for r in reviews_query:
        # 비딩 정보 조회
        bidding = db.query(Bidding).filter(Bidding.id == r.bidding_id).first()
        quote_req = None
        if bidding:
            quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
        
        # 화주 정보 조회
        customer = db.query(Customer).filter(Customer.id == r.customer_id).first()
        customer_company_masked = mask_company_name(customer.company) if customer else "***"
        
        reviews.append(ForwarderReviewItem(
            id=r.id,
            score=float(r.score),
            price_score=float(r.price_score) if r.price_score else None,
            service_score=float(r.service_score) if r.service_score else None,
            punctuality_score=float(r.punctuality_score) if r.punctuality_score else None,
            communication_score=float(r.communication_score) if r.communication_score else None,
            comment=r.comment,
            bidding_no=bidding.bidding_no if bidding else "",
            pol=quote_req.pol if quote_req else "",
            pod=quote_req.pod if quote_req else "",
            shipping_type=quote_req.shipping_type if quote_req else "",
            created_at=r.created_at,
            customer_company_masked=customer_company_masked
        ))
    
    return ForwarderProfileResponse(
        forwarder_id=forwarder.id,
        company=forwarder.company,
        company_masked=mask_company_name(forwarder.company),
        rating=float(forwarder.rating) if forwarder.rating else 3.0,
        rating_count=forwarder.rating_count or 0,
        avg_price_score=sum(price_scores) / len(price_scores) if price_scores else None,
        avg_service_score=sum(service_scores) / len(service_scores) if service_scores else None,
        avg_punctuality_score=sum(punctuality_scores) / len(punctuality_scores) if punctuality_scores else None,
        avg_communication_score=sum(communication_scores) / len(communication_scores) if communication_scores else None,
        score_distribution=score_distribution,
        total_bids=total_bids,
        total_awarded=total_awarded,
        award_rate=round(award_rate, 1),
        top_routes=top_routes,
        shipping_mode_stats=shipping_mode_stats,
        reviews=reviews,
        member_since=forwarder.created_at
    )


# ==========================================
# BIDDING LIST ENDPOINTS (for Forwarders)
# ==========================================

@app.get("/api/bidding/stats", response_model=BiddingStatsResponse, tags=["Bidding List"])
def get_bidding_stats(db: Session = Depends(get_db)):
    """
    Get bidding statistics for dashboard
    
    - total_count: 전체 Bidding 건수
    - open_count: 진행중인 입찰 건수 (마감일이 지나지 않은 것만)
    - closing_soon_count: 24시간 이내 마감 예정 건수
    - awarded_count: 낙찰 완료 건수
    - failed_count: 유찰/마감 건수 (closed + cancelled + expired + 마감일 지난 open)
    """
    now = datetime.now()
    tomorrow = now + timedelta(hours=24)
    
    total_count = db.query(Bidding).count()
    
    # open_count: status가 'open'이고 마감일이 아직 지나지 않은 것
    open_count = db.query(Bidding).filter(
        Bidding.status == "open",
        or_(
            Bidding.deadline == None,
            Bidding.deadline > now
        )
    ).count()
    
    # closing_soon_count: status가 'open'이고 24시간 이내 마감 예정
    closing_soon_count = db.query(Bidding).filter(
        Bidding.status == "open",
        Bidding.deadline <= tomorrow,
        Bidding.deadline > now
    ).count()
    
    awarded_count = db.query(Bidding).filter(Bidding.status == "awarded").count()
    
    # failed_count: closed, cancelled, expired 상태 + 마감일이 지난 open 상태
    explicitly_failed = db.query(Bidding).filter(
        Bidding.status.in_(["closed", "cancelled", "expired"])
    ).count()
    
    # 마감일이 지났지만 아직 status가 'open'인 것들도 마감으로 카운트
    expired_but_open = db.query(Bidding).filter(
        Bidding.status == "open",
        Bidding.deadline != None,
        Bidding.deadline <= now
    ).count()
    
    failed_count = explicitly_failed + expired_but_open
    
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
    now = datetime.now()
    deadline_24h = now + timedelta(hours=24)
    
    if status:
        if status == "expired":
            # expired (마감): explicitly expired OR (open AND deadline passed)
            query = query.filter(
                or_(
                    Bidding.status == "expired",
                    and_(
                        Bidding.status == "open",
                        Bidding.deadline != None,
                        Bidding.deadline <= now
                    )
                )
            )
        elif status == "open":
            # open (진행중): status is open AND deadline NOT passed
            query = query.filter(
                Bidding.status == "open",
                or_(
                    Bidding.deadline == None,
                    Bidding.deadline > now
                )
            )
        elif status == "closing_soon":
            # closing_soon (마감예정): open AND deadline within 24 hours
            query = query.filter(
                Bidding.status == "open",
                Bidding.deadline != None,
                Bidding.deadline > now,
                Bidding.deadline <= deadline_24h
            )
        elif status == "failed":
            # failed (유찰): closed OR cancelled
            query = query.filter(
                or_(
                    Bidding.status == "closed",
                    Bidding.status == "cancelled"
                )
            )
        else:
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
        
        # Calculate average bid price
        avg_bid_price = None
        if bid_count > 0:
            from sqlalchemy import func
            avg_result = db.query(func.avg(Bid.total_amount)).filter(
                Bid.bidding_id == b.id,
                Bid.status == "submitted",
                Bid.total_amount.isnot(None)
            ).scalar()
            avg_bid_price = round(float(avg_result), 2) if avg_result else None
        
        # Check if forwarder has already bid
        my_bid_status = None
        if forwarder_id:
            my_bid = db.query(Bid).filter(
                Bid.bidding_id == b.id,
                Bid.forwarder_id == forwarder_id
            ).first()
            if my_bid:
                my_bid_status = my_bid.status
        
        # Determine effective status (expired if deadline passed and still open)
        effective_status = b.status
        now = datetime.now()
        if b.status == "open" and b.deadline and b.deadline <= now:
            effective_status = "expired"
        
        # Generate cargo summary
        cargo_summary = generate_cargo_summary(
            qr.shipping_type,
            qr.load_type,
            qr.cargo_details,
            db
        )
        
        # Get port names for POL/POD
        pol_port = db.query(Port).filter(Port.code == qr.pol).first()
        pod_port = db.query(Port).filter(Port.code == qr.pod).first()
        
        pol_name = f"{pol_port.name}, {pol_port.country}".upper() if pol_port else None
        pod_name = f"{pod_port.name}, {pod_port.country}".upper() if pod_port else None
        
        items.append(BiddingListItem(
            id=b.id,
            bidding_no=b.bidding_no,
            customer_company=qr.customer.company,
            pol=qr.pol,
            pod=qr.pod,
            pol_name=pol_name,
            pod_name=pod_name,
            shipping_type=qr.shipping_type,
            load_type=qr.load_type,
            cargo_summary=cargo_summary,
            etd=qr.etd,
            deadline=b.deadline,
            status=effective_status,
            bid_count=bid_count,
            avg_bid_price=avg_bid_price,
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
    
    # Calculate cargo totals from cargo_details
    cargo_details = qr.cargo_details
    container_type = None
    container_qty = 0
    total_qty = 0
    total_weight = 0.0
    total_cbm = 0.0
    
    if cargo_details:
        for cd in cargo_details:
            if cd.container_type and not container_type:
                container_type = cd.container_type
            total_qty += cd.qty or 0
            container_qty += cd.qty or 0
            total_weight += float(cd.gross_weight or 0)
            total_cbm += float(cd.cbm or 0)
    
    # Build cargo details response list
    cargo_details_list = []
    if cargo_details:
        for cd in cargo_details:
            cargo_details_list.append(CargoDetailResponse(
                id=cd.id,
                quote_request_id=cd.quote_request_id,
                row_index=cd.row_index,
                container_type=cd.container_type,
                truck_type=cd.truck_type,
                length=cd.length,
                width=cd.width,
                height=cd.height,
                qty=cd.qty or 1,
                gross_weight=float(cd.gross_weight) if cd.gross_weight else None,
                cbm=float(cd.cbm) if cd.cbm else None,
                volume_weight=cd.volume_weight,
                chargeable_weight=cd.chargeable_weight
            ))
    
    # Get POL/POD codes for Quick Quotation
    # qr.pol/pod가 코드일 수도 있고, 이름일 수도 있으므로 두 경우 모두 처리
    pol_code = None
    pod_code = None
    
    # 먼저 코드로 검색 시도
    pol_port = db.query(Port).filter(Port.code == qr.pol).first()
    if pol_port:
        pol_code = pol_port.code
    else:
        # 이름으로 검색 시도 (name 또는 name_ko에서 검색)
        pol_port = db.query(Port).filter(
            (Port.name.ilike(f"%{qr.pol}%")) | (Port.name_ko.ilike(f"%{qr.pol}%"))
        ).first()
        if pol_port:
            pol_code = pol_port.code
    
    pod_port = db.query(Port).filter(Port.code == qr.pod).first()
    if pod_port:
        pod_code = pod_port.code
    else:
        pod_port = db.query(Port).filter(
            (Port.name.ilike(f"%{qr.pod}%")) | (Port.name_ko.ilike(f"%{qr.pod}%"))
        ).first()
        if pod_port:
            pod_code = pod_port.code
    
    return BiddingDetailResponse(
        id=bidding.id,
        bidding_no=bidding.bidding_no,
        status=bidding.status,
        deadline=bidding.deadline,
        created_at=bidding.created_at,
        pdf_url=f"/api/quote/rfq/{bidding_no}/pdf" if bidding.pdf_path else None,
        customer_company=customer.company,
        customer_name=customer.name,
        customer_email=customer.email,
        customer_phone=customer.phone,
        trade_mode=qr.trade_mode,
        shipping_type=qr.shipping_type,
        load_type=qr.load_type,
        incoterms=qr.incoterms,
        pol=qr.pol,
        pod=qr.pod,
        pol_code=pol_code,
        pod_code=pod_code,
        etd=qr.etd,
        eta=qr.eta,
        is_dg=qr.is_dg,
        dg_class=qr.dg_class,
        dg_un=qr.dg_un,
        remark=qr.remark,
        # Cargo Details (합계)
        container_type=container_type,
        container_qty=container_qty,
        total_qty=total_qty,
        total_weight=total_weight,
        total_cbm=total_cbm,
        invoice_value=float(qr.invoice_value or 0),
        # Cargo Details (개별 리스트)
        cargo_details=cargo_details_list,
        # Additional Details
        export_cc=qr.export_cc or False,
        import_cc=qr.import_cc or False,
        shipping_insurance=qr.shipping_insurance or False,
        pickup_required=qr.pickup_required or False,
        pickup_address=qr.pickup_address,
        delivery_required=qr.delivery_required or False,
        delivery_address=qr.delivery_address,
        # Bid Info
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
# FREIGHT CODE API
# ==========================================

@app.get("/api/freight-codes", response_model=FreightCodesListResponse, tags=["Freight Codes"])
def get_freight_codes(
    shipping_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    운임 코드 목록 조회 (카테고리별 그룹핑)
    
    - shipping_type: ocean, air, truck 중 하나 (없으면 전체)
    """
    # 카테고리 조회 (shipping_type 필터링)
    categories_query = db.query(FreightCategory).filter(FreightCategory.is_active == True)
    
    if shipping_type:
        # shipping_types 컬럼에 해당 타입이 포함된 카테고리만
        categories_query = categories_query.filter(
            FreightCategory.shipping_types.contains(shipping_type)
        )
    
    categories = categories_query.order_by(FreightCategory.sort_order).all()
    
    # 단위 목록 조회
    units = db.query(FreightUnit).filter(
        FreightUnit.is_active == True
    ).order_by(FreightUnit.sort_order).all()
    
    result_categories = []
    
    for cat in categories:
        # 각 카테고리별 운임 코드 조회
        codes = db.query(FreightCode).filter(
            FreightCode.category_id == cat.id,
            FreightCode.is_active == True
        ).order_by(FreightCode.sort_order).all()
        
        codes_response = []
        for code in codes:
            # 각 코드별 허용 단위 조회
            code_units = db.query(FreightUnit.code).join(
                FreightCodeUnit, FreightCodeUnit.freight_unit_id == FreightUnit.id
            ).filter(
                FreightCodeUnit.freight_code_id == code.id
            ).all()
            
            codes_response.append(FreightCodeResponse(
                id=code.id,
                code=code.code,
                group_name=code.group_name,
                name_en=code.name_en,
                name_ko=code.name_ko,
                vat_applicable=code.vat_applicable,
                default_currency=code.default_currency,
                is_active=code.is_active,
                sort_order=code.sort_order,
                units=[u[0] for u in code_units]
            ))
        
        result_categories.append(FreightCategoryWithCodesResponse(
            id=cat.id,
            code=cat.code,
            name_en=cat.name_en,
            name_ko=cat.name_ko,
            shipping_types=cat.shipping_types,
            sort_order=cat.sort_order,
            codes=codes_response
        ))
    
    units_response = [FreightUnitResponse(
        id=u.id,
        code=u.code,
        name_en=u.name_en,
        name_ko=u.name_ko,
        sort_order=u.sort_order
    ) for u in units]
    
    return FreightCodesListResponse(
        categories=result_categories,
        units=units_response
    )


@app.get("/api/freight-codes/{code}", response_model=FreightCodeResponse, tags=["Freight Codes"])
def get_freight_code_detail(
    code: str,
    db: Session = Depends(get_db)
):
    """
    특정 운임 코드 상세 조회
    """
    freight_code = db.query(FreightCode).filter(
        FreightCode.code == code.upper(),
        FreightCode.is_active == True
    ).first()
    
    if not freight_code:
        raise HTTPException(status_code=404, detail=f"Freight code '{code}' not found")
    
    # 허용 단위 조회
    code_units = db.query(FreightUnit.code).join(
        FreightCodeUnit, FreightCodeUnit.freight_unit_id == FreightUnit.id
    ).filter(
        FreightCodeUnit.freight_code_id == freight_code.id
    ).all()
    
    return FreightCodeResponse(
        id=freight_code.id,
        code=freight_code.code,
        group_name=freight_code.group_name,
        name_en=freight_code.name_en,
        name_ko=freight_code.name_ko,
        vat_applicable=freight_code.vat_applicable,
        default_currency=freight_code.default_currency,
        is_active=freight_code.is_active,
        sort_order=freight_code.sort_order,
        units=[u[0] for u in code_units]
    )


@app.get("/api/freight-units", response_model=List[FreightUnitResponse], tags=["Freight Codes"])
def get_freight_units(db: Session = Depends(get_db)):
    """
    운임 단위 목록 조회
    """
    units = db.query(FreightUnit).filter(
        FreightUnit.is_active == True
    ).order_by(FreightUnit.sort_order).all()
    
    return [FreightUnitResponse(
        id=u.id,
        code=u.code,
        name_en=u.name_en,
        name_ko=u.name_ko,
        sort_order=u.sort_order
    ) for u in units]


@app.get("/api/freight-categories", response_model=List[FreightCategoryResponse], tags=["Freight Codes"])
def get_freight_categories(
    shipping_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    운임 카테고리 목록 조회
    
    - shipping_type: ocean, air, truck 중 하나 (없으면 전체)
    """
    query = db.query(FreightCategory).filter(FreightCategory.is_active == True)
    
    if shipping_type:
        query = query.filter(FreightCategory.shipping_types.contains(shipping_type))
    
    categories = query.order_by(FreightCategory.sort_order).all()
    
    return [FreightCategoryResponse(
        id=c.id,
        code=c.code,
        name_en=c.name_en,
        name_ko=c.name_ko,
        shipping_types=c.shipping_types,
        sort_order=c.sort_order
    ) for c in categories]


# ==========================================
# QUICK QUOTATION - FREIGHT ESTIMATE API
# ==========================================

from models import OceanRateSheet, OceanRateItem
from schemas import QuickQuotationResponse, FreightRateItem, FreightGroupBreakdown, DefaultChargeItem


def get_default_charges(db: Session, container_type_code: str) -> List[DefaultChargeItem]:
    """
    기본 비용 조회 (DOC, SEAL/CSL, THC)
    경로 운임이 없을 때 사용
    """
    default_charges = []
    
    # Get container type
    ct = db.query(ContainerType).filter(ContainerType.code == container_type_code.upper()).first()
    
    # 컨테이너 사이즈에 따른 THC 요금 결정
    thc_rate = 150000  # 기본값 (20ft)
    if container_type_code.upper().startswith('4'):
        thc_rate = 210000  # 40ft
    elif container_type_code.upper().startswith('45'):
        thc_rate = 250000  # 45ft
    
    # DOC (서류 발급 비용) - 50,000 KRW, BL 단위
    doc_code = db.query(FreightCode).filter(FreightCode.code == "DOC").first()
    if doc_code:
        default_charges.append(DefaultChargeItem(
            code="DOC",
            name="DOCUMENT FEE",
            name_ko="서류 발급 비용",
            rate=50000,
            currency="KRW",
            unit="BL"
        ))
    
    # CSL (컨테이너 씰 비용) - 5,000 KRW, Qty 단위
    csl_code = db.query(FreightCode).filter(FreightCode.code == "CSL").first()
    if csl_code:
        default_charges.append(DefaultChargeItem(
            code="CSL",
            name="CONTAINER SEAL CHARGE",
            name_ko="컨테이너 씰 비용",
            rate=5000,
            currency="KRW",
            unit="Qty"
        ))
    else:
        # CSL이 없으면 SEAL로 시도
        seal_code = db.query(FreightCode).filter(FreightCode.code == "SEAL").first()
        if seal_code:
            default_charges.append(DefaultChargeItem(
                code="SEAL",
                name="SEAL FEE",
                name_ko="씰 비용",
                rate=5000,
                currency="KRW",
                unit="Qty"
            ))
    
    # THC (터미널 작업비) - 컨테이너 사이즈별 차등
    thc_code = db.query(FreightCode).filter(FreightCode.code == "THC").first()
    if thc_code:
        default_charges.append(DefaultChargeItem(
            code="THC",
            name="TERMINAL HANDLING CHARGE",
            name_ko="터미널 작업비",
            rate=thc_rate,
            currency="KRW",
            unit="Qty"
        ))
    
    return default_charges


@app.get("/api/freight/estimate", response_model=QuickQuotationResponse, tags=["Quick Quotation"])
def get_freight_estimate(
    pol: str,
    pod: str,
    container_type: str,
    etd: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Quick Quotation - 운임 자동완성 API
    
    - pol: 출발항 코드 (e.g., KRPUS)
    - pod: 도착항 코드 (e.g., NLRTM)
    - container_type: 컨테이너 타입 코드 (e.g., 20DC, 40DC, 4HDC)
    - etd: 출발예정일 (YYYY-MM-DD) - 유효기간 체크용 (선택)
    
    Returns:
    - quick_quotation: true/false
    - 운임 breakdown (quick_quotation=true인 경우)
    """
    
    # Get ports
    pol_port = db.query(Port).filter(Port.code == pol.upper()).first()
    pod_port = db.query(Port).filter(Port.code == pod.upper()).first()
    
    if not pol_port:
        return QuickQuotationResponse(
            quick_quotation=False,
            message=f"출발항 '{pol}'을 찾을 수 없습니다.",
            guide="올바른 항구 코드를 입력해 주세요."
        )
    
    if not pod_port:
        return QuickQuotationResponse(
            quick_quotation=False,
            message=f"도착항 '{pod}'을 찾을 수 없습니다.",
            guide="올바른 항구 코드를 입력해 주세요."
        )
    
    # Get container type
    ct = db.query(ContainerType).filter(ContainerType.code == container_type.upper()).first()
    if not ct:
        return QuickQuotationResponse(
            quick_quotation=False,
            message=f"컨테이너 타입 '{container_type}'을 찾을 수 없습니다.",
            guide="올바른 컨테이너 타입을 선택해 주세요."
        )
    
    # Determine check date
    if etd:
        try:
            check_date = datetime.strptime(etd, "%Y-%m-%d")
        except ValueError:
            check_date = datetime.now()
    else:
        check_date = datetime.now()
    
    # Find valid rate sheet
    sheet = db.query(OceanRateSheet).filter(
        OceanRateSheet.pol_id == pol_port.id,
        OceanRateSheet.pod_id == pod_port.id,
        OceanRateSheet.is_active == True,
        OceanRateSheet.valid_from <= check_date,
        OceanRateSheet.valid_to >= check_date
    ).first()
    
    if not sheet:
        # 해당 구간의 다른 유효한 운임이 있는지 확인
        available_sheet = db.query(OceanRateSheet).filter(
            OceanRateSheet.pol_id == pol_port.id,
            OceanRateSheet.pod_id == pod_port.id,
            OceanRateSheet.is_active == True
        ).order_by(OceanRateSheet.valid_from.desc()).first()
        
        # 기본 비용 조회 (DOC, SEAL, THC)
        default_charges = get_default_charges(db, container_type)
        
        if available_sheet:
            # 운임 데이터는 있지만 요청한 날짜가 유효 기간 외
            return QuickQuotationResponse(
                quick_quotation=False,
                message=f"요청하신 날짜({etd or '미지정'})에 운임 데이터가 없습니다.",
                guide=f"현재 운임 데이터: {available_sheet.valid_from.strftime('%Y-%m-%d')} ~ {available_sheet.valid_to.strftime('%Y-%m-%d')}",
                available_from=available_sheet.valid_from.strftime('%Y-%m-%d'),
                available_to=available_sheet.valid_to.strftime('%Y-%m-%d'),
                container_type=ct.code,
                container_name=ct.name,
                default_charges=default_charges
            )
        else:
            # 해당 구간에 운임 데이터가 전혀 없음
            return QuickQuotationResponse(
                quick_quotation=False,
                message="해당 구간은 실시간 견적을 제공하지 않습니다.",
                guide="기본 비용(DOC, 씰, THC)만 자동완성됩니다. 운임은 직접 입력해 주세요.",
                container_type=ct.code,
                container_name=ct.name,
                default_charges=default_charges
            )
    
    # Get rate items for this container type
    items = db.query(OceanRateItem).filter(
        OceanRateItem.sheet_id == sheet.id,
        OceanRateItem.container_type_id == ct.id,
        OceanRateItem.is_active == True
    ).all()
    
    if not items:
        # 기본 비용 조회 (DOC, SEAL, THC)
        default_charges = get_default_charges(db, container_type)
        return QuickQuotationResponse(
            quick_quotation=False,
            message="해당 컨테이너 타입의 운임 정보가 없습니다.",
            guide="기본 비용(DOC, 씰, THC)만 자동완성됩니다. 운임은 직접 입력해 주세요.",
            container_type=ct.code,
            container_name=ct.name,
            default_charges=default_charges
        )
    
    # Check if Ocean Freight (FRT) rate exists
    frt_code = db.query(FreightCode).filter(FreightCode.code == "FRT").first()
    frt_item = next((i for i in items if i.freight_code_id == frt_code.id), None) if frt_code else None
    
    if not frt_item or frt_item.rate is None:
        # 기본 비용 조회 (DOC, SEAL, THC)
        default_charges = get_default_charges(db, container_type)
        return QuickQuotationResponse(
            quick_quotation=False,
            message="해당 컨테이너 타입의 기본 운임이 등록되지 않았습니다.",
            guide="기본 비용(DOC, 씰, THC)만 자동완성됩니다. 운임은 직접 입력해 주세요.",
            container_type=ct.code,
            container_name=ct.name,
            default_charges=default_charges
        )
    
    # Build breakdown
    ocean_freight_items = []
    origin_local_items = []
    
    total_usd = 0.0
    total_krw = 0.0
    total_eur = 0.0
    
    ocean_usd = 0.0
    local_usd = 0.0
    local_krw = 0.0
    local_eur = 0.0
    
    for item in items:
        fc = item.freight_code
        rate_item = FreightRateItem(
            code=fc.code,
            name=fc.name_en,
            name_ko=fc.name_ko,
            rate=float(item.rate) if item.rate else None,
            currency=item.currency,
            unit=item.unit
        )
        
        if item.freight_group == "Ocean Freight":
            ocean_freight_items.append(rate_item)
            if item.rate:
                if item.currency == "USD":
                    ocean_usd += float(item.rate)
                    total_usd += float(item.rate)
        else:
            origin_local_items.append(rate_item)
            if item.rate:
                if item.currency == "USD":
                    local_usd += float(item.rate)
                    total_usd += float(item.rate)
                elif item.currency == "KRW":
                    local_krw += float(item.rate)
                    total_krw += float(item.rate)
                elif item.currency == "EUR":
                    local_eur += float(item.rate)
                    total_eur += float(item.rate)
    
    ocean_breakdown = FreightGroupBreakdown(
        group_name="Ocean Freight",
        items=ocean_freight_items,
        subtotal_usd=ocean_usd
    )
    
    local_breakdown = FreightGroupBreakdown(
        group_name="Origin Local Charges",
        items=origin_local_items,
        subtotal_usd=local_usd,
        subtotal_krw=local_krw,
        subtotal_eur=local_eur
    )
    
    # 환율 조회 및 KRW 환산 (한국은행 API 활용)
    exchange_rates_used = {}
    total_krw_converted = total_krw  # 이미 KRW인 금액은 그대로
    cache_key = datetime.now().strftime("%Y-%m-%d")  # 일별 캐싱
    
    # USD 환산
    if total_usd > 0:
        usd_rate = get_bok_exchange_rate("USD", cache_key)
        exchange_rates_used["USD"] = usd_rate
        total_krw_converted += total_usd * usd_rate
    
    # EUR 환산
    if total_eur > 0:
        eur_rate = get_bok_exchange_rate("EUR", cache_key)
        exchange_rates_used["EUR"] = eur_rate
        total_krw_converted += total_eur * eur_rate
    
    return QuickQuotationResponse(
        quick_quotation=True,
        carrier=sheet.carrier,
        valid_from=sheet.valid_from.strftime("%Y-%m-%d"),
        valid_to=sheet.valid_to.strftime("%Y-%m-%d"),
        container_type=ct.code,
        container_name=ct.name,
        ocean_freight=ocean_breakdown,
        origin_local=local_breakdown,
        total_usd=total_usd,
        total_krw=total_krw,
        total_eur=total_eur,
        total_krw_converted=total_krw_converted,
        exchange_rates_used=exchange_rates_used if exchange_rates_used else None,
        note="해당 견적은 예상 견적입니다. 실제 금액은 비딩 결과에 따라 달라질 수 있습니다."
    )


@app.get("/api/freight/routes", tags=["Quick Quotation"])
def get_available_routes(db: Session = Depends(get_db)):
    """
    Quick Quotation 가능한 구간 목록 조회
    """
    today = datetime.now()
    
    sheets = db.query(OceanRateSheet).filter(
        OceanRateSheet.is_active == True,
        OceanRateSheet.valid_from <= today,
        OceanRateSheet.valid_to >= today
    ).all()
    
    routes = []
    for sheet in sheets:
        routes.append({
            "pol_code": sheet.pol.code,
            "pol_name": sheet.pol.name,
            "pod_code": sheet.pod.code,
            "pod_name": sheet.pod.name,
            "carrier": sheet.carrier,
            "valid_from": sheet.valid_from.strftime("%Y-%m-%d"),
            "valid_to": sheet.valid_to.strftime("%Y-%m-%d")
        })
    
    return {
        "count": len(routes),
        "routes": routes
    }


# ==========================================
# TRUCKING RATE API
# ==========================================

@app.get("/api/trucking/rate", tags=["Trucking"])
def get_trucking_rate(
    origin_port: str,
    address: str,
    container_type: str,
    db: Session = Depends(get_db)
):
    """
    Trucking Rate 조회 API
    
    - origin_port: 출발항 코드 (e.g., KRPUS)
    - address: 목적지 주소 (검색용)
    - container_type: 컨테이너 타입 코드 (e.g., 20DC, 40DC)
    
    Returns:
    - rate: 운임 (KRW), null if not found
    """
    
    # Get port
    port = db.query(Port).filter(Port.code == origin_port.upper()).first()
    if not port:
        return {"rate": None, "message": f"출발항 '{origin_port}'을 찾을 수 없습니다."}
    
    # Parse container type for rate column selection
    is_40ft = container_type.upper().startswith('4')
    
    # Search trucking rate by address (partial match)
    # 주소에서 도/시/구 정보 추출 시도
    query = db.query(TruckingRate).filter(
        TruckingRate.origin_port_id == port.id,
        TruckingRate.is_active == True
    )
    
    # 주소 검색 (도/시/구/동 중 하나라도 매칭)
    address_parts = address.replace(',', ' ').split()
    
    if address_parts:
        # OR 조건으로 주소 부분 매칭
        rate = None
        for part in address_parts:
            part = part.strip()
            if len(part) < 2:
                continue
            
            rate = query.filter(
                or_(
                    TruckingRate.dest_province.contains(part),
                    TruckingRate.dest_city.contains(part),
                    TruckingRate.dest_district.contains(part)
                )
            ).first()
            
            if rate:
                break
        
        if rate:
            rate_value = float(rate.rate_40ft) if is_40ft else float(rate.rate_20ft)
            return {
                "rate": rate_value,
                "currency": "KRW",
                "origin": f"{port.code} - {port.name}",
                "destination": f"{rate.dest_province} {rate.dest_city} {rate.dest_district}",
                "distance_km": rate.distance_km,
                "container_type": "40ft" if is_40ft else "20ft"
            }
    
    return {
        "rate": None,
        "message": f"'{address}' 지역의 운임 정보를 찾을 수 없습니다."
    }


@app.get("/api/trucking/locations", tags=["Trucking"])
def get_trucking_locations(
    origin_port: str,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Trucking 가능 지역 목록 조회
    
    - origin_port: 출발항 코드
    - search: 검색어 (선택)
    """
    port = db.query(Port).filter(Port.code == origin_port.upper()).first()
    if not port:
        return {"locations": [], "message": f"출발항 '{origin_port}'을 찾을 수 없습니다."}
    
    query = db.query(TruckingRate).filter(
        TruckingRate.origin_port_id == port.id,
        TruckingRate.is_active == True
    )
    
    if search:
        query = query.filter(
            or_(
                TruckingRate.dest_province.contains(search),
                TruckingRate.dest_city.contains(search),
                TruckingRate.dest_district.contains(search)
            )
        )
    
    rates = query.limit(50).all()
    
    locations = []
    for rate in rates:
        locations.append({
            "province": rate.dest_province,
            "city": rate.dest_city,
            "district": rate.dest_district,
            "full_address": f"{rate.dest_province} {rate.dest_city} {rate.dest_district}",
            "distance_km": rate.distance_km,
            "rate_20ft": float(rate.rate_20ft) if rate.rate_20ft else None,
            "rate_40ft": float(rate.rate_40ft) if rate.rate_40ft else None
        })
    
    return {
        "count": len(locations),
        "locations": locations
    }


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
# SHIPPER BIDDING MANAGEMENT ENDPOINTS
# ==========================================

# KRW 환율 (실제 서비스에서는 실시간 환율 API 연동 필요)
EXCHANGE_RATES = {
    'USD': 1350,  # 1 USD = 1350 KRW
    'EUR': 1450,
    'JPY': 9,
    'CNY': 185,
    'KRW': 1
}


def convert_to_krw(amount: float, currency: str = 'USD') -> float:
    """금액을 KRW로 변환"""
    rate = EXCHANGE_RATES.get(currency.upper(), 1350)
    return amount * rate


def mask_company_name(company_name: str) -> str:
    """회사명 익명화: 첫 글자만 표시하고 나머지는 ****"""
    if not company_name:
        return "****"
    return company_name[0] + "****"


@app.get("/api/shipper/biddings/stats", response_model=ShipperBiddingStatsResponse, tags=["Shipper Bidding"])
def get_shipper_bidding_stats(
    customer_id: Optional[int] = None,
    customer_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    화주의 비딩 통계 조회
    - customer_id 또는 customer_email 중 하나 필수
    """
    # customer_email이 있으면 해당 Customer의 ID 조회
    if customer_email and not customer_id:
        customer = db.query(Customer).filter(Customer.email == customer_email).first()
        if customer:
            customer_id = customer.id
        else:
            # 해당 이메일의 고객이 없으면 빈 통계 반환
            return ShipperBiddingStatsResponse(
                total_count=0,
                open_count=0,
                closing_soon_count=0,
                awarded_count=0,
                failed_count=0
            )
    
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id 또는 customer_email이 필요합니다.")
    
    # 해당 고객의 Quote Request ID 목록 조회
    quote_ids = db.query(QuoteRequest.id).filter(
        QuoteRequest.customer_id == customer_id
    ).subquery()
    
    # 기본 쿼리
    base_query = db.query(Bidding).filter(Bidding.quote_request_id.in_(quote_ids))
    
    total_count = base_query.count()
    open_count = base_query.filter(Bidding.status == "open").count()
    
    # 24시간 이내 마감 예정
    now = datetime.now()
    closing_soon_deadline = now + timedelta(hours=24)
    closing_soon_count = base_query.filter(
        Bidding.status == "open",
        Bidding.deadline != None,
        Bidding.deadline <= closing_soon_deadline,
        Bidding.deadline > now
    ).count()
    
    awarded_count = base_query.filter(Bidding.status == "awarded").count()
    failed_count = base_query.filter(
        Bidding.status.in_(["closed", "cancelled", "expired"])
    ).count()
    
    return ShipperBiddingStatsResponse(
        total_count=total_count,
        open_count=open_count,
        closing_soon_count=closing_soon_count,
        awarded_count=awarded_count,
        failed_count=failed_count
    )


@app.get("/api/shipper/biddings", response_model=ShipperBiddingListResponse, tags=["Shipper Bidding"])
def get_shipper_bidding_list(
    customer_id: Optional[int] = None,
    customer_email: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    shipping_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    화주의 비딩 목록 조회
    
    - customer_id 또는 customer_email 중 하나 필수
    - status: open, closing_soon, awarded, expired, closed
    - shipping_type: ocean, air, truck
    - search: Bidding No 검색
    """
    # customer_email이 있으면 해당 Customer의 ID 조회
    if customer_email and not customer_id:
        customer = db.query(Customer).filter(Customer.email == customer_email).first()
        if customer:
            customer_id = customer.id
        else:
            # 해당 이메일의 고객이 없으면 빈 목록 반환
            return ShipperBiddingListResponse(data=[], total=0, page=page, limit=limit)
    
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id 또는 customer_email이 필요합니다.")
    
    # 해당 고객의 Quote Request와 Bidding 조인
    query = db.query(Bidding, QuoteRequest).join(
        QuoteRequest, Bidding.quote_request_id == QuoteRequest.id
    ).filter(
        QuoteRequest.customer_id == customer_id
    )
    
    # 상태 필터
    now = datetime.now()
    if status == "open":
        query = query.filter(Bidding.status == "open")
    elif status == "closing_soon":
        closing_deadline = now + timedelta(hours=24)
        query = query.filter(
            Bidding.status == "open",
            Bidding.deadline != None,
            Bidding.deadline <= closing_deadline,
            Bidding.deadline > now
        )
    elif status == "awarded":
        query = query.filter(Bidding.status == "awarded")
    elif status == "expired":
        query = query.filter(Bidding.status.in_(["expired", "closed", "cancelled"]))
    
    # 운송 타입 필터
    if shipping_type:
        query = query.filter(QuoteRequest.shipping_type == shipping_type)
    
    # 검색
    if search:
        query = query.filter(Bidding.bidding_no.ilike(f"%{search}%"))
    
    # 전체 건수
    total = query.count()
    
    # 페이지네이션
    offset = (page - 1) * limit
    results = query.order_by(Bidding.created_at.desc()).offset(offset).limit(limit).all()
    
    # 응답 데이터 구성
    data = []
    for bidding, quote_req in results:
        # 입찰 수 및 통계 조회
        bids = db.query(Bid).filter(
            Bid.bidding_id == bidding.id,
            Bid.status == "submitted"
        ).all()
        
        bid_count = len(bids)
        min_bid_krw = None
        avg_bid_krw = None
        
        if bids:
            # KRW 환산 금액으로 계산
            krw_amounts = []
            for bid in bids:
                if bid.total_amount_krw:
                    krw_amounts.append(float(bid.total_amount_krw))
                else:
                    krw_amounts.append(convert_to_krw(float(bid.total_amount)))
            
            min_bid_krw = min(krw_amounts)
            avg_bid_krw = sum(krw_amounts) / len(krw_amounts)
        
        # 낙찰 운송사 (익명화)
        awarded_forwarder = None
        if bidding.awarded_bid_id:
            awarded_bid = db.query(Bid).filter(Bid.id == bidding.awarded_bid_id).first()
            if awarded_bid:
                forwarder = db.query(Forwarder).filter(Forwarder.id == awarded_bid.forwarder_id).first()
                if forwarder:
                    awarded_forwarder = mask_company_name(forwarder.company)
        
        data.append(ShipperBiddingListItem(
            id=bidding.id,
            bidding_no=bidding.bidding_no,
            pol=quote_req.pol,
            pod=quote_req.pod,
            shipping_type=quote_req.shipping_type,
            load_type=quote_req.load_type,
            etd=quote_req.etd,
            eta=quote_req.eta,
            deadline=bidding.deadline,
            status=bidding.status,
            bid_count=bid_count,
            min_bid_price_krw=min_bid_krw,
            avg_bid_price_krw=avg_bid_krw,
            awarded_forwarder=awarded_forwarder,
            created_at=bidding.created_at
        ))
    
    return ShipperBiddingListResponse(
        total=total,
        page=page,
        limit=limit,
        data=data
    )


@app.get("/api/shipper/bidding/{bidding_no}/bids", response_model=ShipperBiddingBidsResponse, tags=["Shipper Bidding"])
def get_shipper_bidding_bids(
    bidding_no: str,
    customer_id: Optional[int] = None,
    customer_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    특정 비딩의 입찰 목록 조회 (화주용, 익명화)
    
    - customer_id 또는 customer_email 중 하나 필수
    - 업체명은 첫 글자만 표시 (예: 삼****)
    - 입찰가 순서로 rank 부여
    - 평점 포함
    """
    # customer_email이 있으면 해당 Customer의 ID 조회
    if customer_email and not customer_id:
        customer = db.query(Customer).filter(Customer.email == customer_email).first()
        if customer:
            customer_id = customer.id
        else:
            raise HTTPException(status_code=403, detail="Access denied - customer not found")
    
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id 또는 customer_email이 필요합니다.")
    
    # 비딩 조회 및 권한 확인
    bidding = db.query(Bidding).filter(Bidding.bidding_no == bidding_no).first()
    if not bidding:
        raise HTTPException(status_code=404, detail="Bidding not found")
    
    quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
    if not quote_req or quote_req.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 제출된 입찰 목록 조회 (총액 순서)
    bids = db.query(Bid, Forwarder).join(
        Forwarder, Bid.forwarder_id == Forwarder.id
    ).filter(
        Bid.bidding_id == bidding.id,
        Bid.status == "submitted"
    ).all()
    
    # KRW 환산 및 정렬
    bid_data = []
    for bid, forwarder in bids:
        krw_amount = float(bid.total_amount_krw) if bid.total_amount_krw else convert_to_krw(float(bid.total_amount))
        bid_data.append({
            'bid': bid,
            'forwarder': forwarder,
            'krw_amount': krw_amount
        })
    
    # KRW 기준 오름차순 정렬
    bid_data.sort(key=lambda x: x['krw_amount'])
    
    # 응답 데이터 구성
    bid_items = []
    for rank, item in enumerate(bid_data, 1):
        bid = item['bid']
        forwarder = item['forwarder']
        
        bid_items.append(ShipperBidItem(
            id=bid.id,
            forwarder_id=forwarder.id,
            rank=rank,
            company_masked=mask_company_name(forwarder.company),
            rating=float(forwarder.rating) if forwarder.rating else 3.0,
            rating_count=forwarder.rating_count or 0,
            total_amount_krw=item['krw_amount'],
            total_amount=float(bid.total_amount),
            freight_charge=float(bid.freight_charge) if bid.freight_charge else None,
            local_charge=float(bid.local_charge) if bid.local_charge else None,
            other_charge=float(bid.other_charge) if bid.other_charge else None,
            etd=bid.etd,
            eta=bid.eta,
            transit_time=bid.transit_time,
            carrier=bid.carrier,
            validity_date=bid.validity_date,
            remark=bid.remark,
            status=bid.status,
            submitted_at=bid.submitted_at
        ))
    
    return ShipperBiddingBidsResponse(
        bidding_no=bidding.bidding_no,
        bidding_status=bidding.status,
        pol=quote_req.pol,
        pod=quote_req.pod,
        shipping_type=quote_req.shipping_type,
        etd=quote_req.etd,
        deadline=bidding.deadline,
        bid_count=len(bid_items),
        bids=bid_items
    )


@app.post("/api/shipper/bidding/{bidding_no}/award/{bid_id}", response_model=AwardBidResponse, tags=["Shipper Bidding"])
def award_bid(
    bidding_no: str,
    bid_id: int,
    customer_id: Optional[int] = None,
    customer_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    운송사 선정 (낙찰)
    
    - customer_id 또는 customer_email 중 하나 필수
    - 해당 비딩의 상태를 'awarded'로 변경
    - 선정된 입찰의 상태를 'awarded'로 변경
    - 나머지 입찰은 'rejected'로 변경
    - 선정된 운송사에 알림 발송
    """
    # customer_email이 있으면 해당 Customer의 ID 조회
    if customer_email and not customer_id:
        customer = db.query(Customer).filter(Customer.email == customer_email).first()
        if customer:
            customer_id = customer.id
        else:
            raise HTTPException(status_code=403, detail="Access denied - customer not found")
    
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id 또는 customer_email이 필요합니다.")
    
    # 비딩 조회 및 권한 확인
    bidding = db.query(Bidding).filter(Bidding.bidding_no == bidding_no).first()
    if not bidding:
        raise HTTPException(status_code=404, detail="Bidding not found")
    
    quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
    if not quote_req or quote_req.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if bidding.status != "open":
        raise HTTPException(status_code=400, detail="Bidding is not open")
    
    # 선정할 입찰 조회
    awarded_bid = db.query(Bid).filter(
        Bid.id == bid_id,
        Bid.bidding_id == bidding.id,
        Bid.status == "submitted"
    ).first()
    
    if not awarded_bid:
        raise HTTPException(status_code=404, detail="Bid not found or not submitted")
    
    try:
        # 1. 비딩 상태 변경
        bidding.status = "awarded"
        bidding.awarded_bid_id = bid_id
        bidding.updated_at = datetime.now()
        
        # 2. 선정된 입찰 상태 변경
        awarded_bid.status = "awarded"
        awarded_bid.updated_at = datetime.now()
        
        # 3. 나머지 입찰 rejected 처리
        db.query(Bid).filter(
            Bid.bidding_id == bidding.id,
            Bid.id != bid_id,
            Bid.status == "submitted"
        ).update({"status": "rejected", "updated_at": datetime.now()})
        
        # 4. 선정 알림 생성
        notification = Notification(
            recipient_type="forwarder",
            recipient_id=awarded_bid.forwarder_id,
            notification_type="bid_awarded",
            title=f"축하합니다! {bidding_no} 건에 선정되었습니다.",
            message=f"{quote_req.pol} → {quote_req.pod} 운송 건에 대해 귀사가 운송사로 선정되었습니다. 고객사에서 곧 연락드릴 예정입니다.",
            related_type="bidding",
            related_id=bidding.id
        )
        db.add(notification)
        
        # 5. 탈락 알림 생성 (다른 입찰자들에게)
        rejected_bids = db.query(Bid).filter(
            Bid.bidding_id == bidding.id,
            Bid.id != bid_id,
            Bid.status == "rejected"
        ).all()
        
        for rejected_bid in rejected_bids:
            reject_notification = Notification(
                recipient_type="forwarder",
                recipient_id=rejected_bid.forwarder_id,
                notification_type="bid_rejected",
                title=f"{bidding_no} 건 입찰 결과 안내",
                message=f"{quote_req.pol} → {quote_req.pod} 운송 건에 대해 아쉽게도 다른 운송사가 선정되었습니다. 다음 기회에 좋은 결과 있기를 바랍니다.",
                related_type="bidding",
                related_id=bidding.id
            )
            db.add(reject_notification)
        
        db.commit()
        
        return AwardBidResponse(
            success=True,
            message="운송사가 선정되었습니다.",
            bidding_no=bidding_no,
            awarded_bid_id=bid_id,
            notification_sent=True
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to award bid: {str(e)}")


# ==========================================
# NOTIFICATION ENDPOINTS
# ==========================================

@app.get("/api/notifications", response_model=NotificationListResponse, tags=["Notifications"])
def get_notifications(
    recipient_type: str,
    recipient_id: int,
    limit: int = 20,
    include_read: bool = False,
    db: Session = Depends(get_db)
):
    """
    알림 목록 조회
    
    - recipient_type: forwarder, customer
    - recipient_id: 수신자 ID
    - include_read: 읽은 알림도 포함할지 여부
    """
    query = db.query(Notification).filter(
        Notification.recipient_type == recipient_type,
        Notification.recipient_id == recipient_id
    )
    
    if not include_read:
        query = query.filter(Notification.is_read == False)
    
    total = query.count()
    unread_count = db.query(Notification).filter(
        Notification.recipient_type == recipient_type,
        Notification.recipient_id == recipient_id,
        Notification.is_read == False
    ).count()
    
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    return NotificationListResponse(
        total=total,
        unread_count=unread_count,
        data=[NotificationResponse(
            id=n.id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            related_type=n.related_type,
            related_id=n.related_id,
            is_read=n.is_read,
            read_at=n.read_at,
            created_at=n.created_at
        ) for n in notifications]
    )


@app.post("/api/notifications/mark-read", tags=["Notifications"])
def mark_notifications_read(
    request: MarkNotificationReadRequest,
    db: Session = Depends(get_db)
):
    """
    알림 읽음 처리
    """
    try:
        db.query(Notification).filter(
            Notification.id.in_(request.notification_ids)
        ).update({
            "is_read": True,
            "read_at": datetime.now()
        }, synchronize_session=False)
        
        db.commit()
        
        return {"success": True, "message": f"{len(request.notification_ids)}개 알림을 읽음 처리했습니다."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# RATING ENDPOINTS
# ==========================================

@app.post("/api/ratings", response_model=SubmitRatingResponse, tags=["Ratings"])
def submit_rating(
    rating_data: RatingCreate,
    customer_id: int,
    db: Session = Depends(get_db)
):
    """
    운송사 평점 등록
    
    운송 완료 후 화주가 운송사에 평점을 부여합니다.
    - score: 종합 평점 (0.5 ~ 5.0, 0.5 단위)
    - 세부 평점: 가격, 서비스, 정시성, 커뮤니케이션 (선택)
    """
    # 비딩 조회 및 권한 확인
    bidding = db.query(Bidding).filter(Bidding.id == rating_data.bidding_id).first()
    if not bidding:
        raise HTTPException(status_code=404, detail="Bidding not found")
    
    quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
    if not quote_req or quote_req.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 낙찰된 비딩인지 확인
    if bidding.status != "awarded":
        raise HTTPException(status_code=400, detail="Rating can only be submitted for awarded biddings")
    
    # 해당 운송사가 낙찰된 운송사인지 확인
    awarded_bid = db.query(Bid).filter(Bid.id == bidding.awarded_bid_id).first()
    if not awarded_bid or awarded_bid.forwarder_id != rating_data.forwarder_id:
        raise HTTPException(status_code=400, detail="Invalid forwarder for this bidding")
    
    # 이미 평점을 부여했는지 확인
    existing_rating = db.query(Rating).filter(
        Rating.bidding_id == rating_data.bidding_id,
        Rating.customer_id == customer_id
    ).first()
    
    if existing_rating:
        raise HTTPException(status_code=400, detail="Rating already submitted for this bidding")
    
    try:
        # 0.5 단위로 반올림
        score = round(rating_data.score * 2) / 2
        
        # 평점 생성
        rating = Rating(
            bidding_id=rating_data.bidding_id,
            forwarder_id=rating_data.forwarder_id,
            customer_id=customer_id,
            score=score,
            price_score=round(rating_data.price_score * 2) / 2 if rating_data.price_score else None,
            service_score=round(rating_data.service_score * 2) / 2 if rating_data.service_score else None,
            punctuality_score=round(rating_data.punctuality_score * 2) / 2 if rating_data.punctuality_score else None,
            communication_score=round(rating_data.communication_score * 2) / 2 if rating_data.communication_score else None,
            comment=rating_data.comment
        )
        db.add(rating)
        
        # 운송사 평균 평점 업데이트
        forwarder = db.query(Forwarder).filter(Forwarder.id == rating_data.forwarder_id).first()
        if forwarder:
            # 모든 평점의 평균 계산
            all_ratings = db.query(Rating).filter(
                Rating.forwarder_id == rating_data.forwarder_id,
                Rating.is_visible == True
            ).all()
            
            total_score = sum(float(r.score) for r in all_ratings) + score
            total_count = len(all_ratings) + 1
            
            forwarder.rating = round((total_score / total_count) * 2) / 2
            forwarder.rating_count = total_count
        
        db.commit()
        db.refresh(rating)
        
        return SubmitRatingResponse(
            success=True,
            message="평점이 등록되었습니다.",
            rating=RatingResponse(
                id=rating.id,
                bidding_id=rating.bidding_id,
                forwarder_id=rating.forwarder_id,
                customer_id=rating.customer_id,
                score=float(rating.score),
                price_score=float(rating.price_score) if rating.price_score else None,
                service_score=float(rating.service_score) if rating.service_score else None,
                punctuality_score=float(rating.punctuality_score) if rating.punctuality_score else None,
                communication_score=float(rating.communication_score) if rating.communication_score else None,
                comment=rating.comment,
                is_visible=rating.is_visible,
                created_at=rating.created_at
            )
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit rating: {str(e)}")


@app.get("/api/ratings/forwarder/{forwarder_id}", response_model=ForwarderRatingStats, tags=["Ratings"])
def get_forwarder_rating_stats(
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """
    운송사 평점 통계 조회
    """
    forwarder = db.query(Forwarder).filter(Forwarder.id == forwarder_id).first()
    if not forwarder:
        raise HTTPException(status_code=404, detail="Forwarder not found")
    
    # 모든 평점 조회
    ratings = db.query(Rating).filter(
        Rating.forwarder_id == forwarder_id,
        Rating.is_visible == True
    ).all()
    
    if not ratings:
        return ForwarderRatingStats(
            forwarder_id=forwarder_id,
            company=forwarder.company,
            average_score=float(forwarder.rating) if forwarder.rating else 3.0,
            total_ratings=0,
            score_distribution={}
        )
    
    # 점수 분포 계산
    distribution = {}
    for r in ratings:
        score_key = str(float(r.score))
        distribution[score_key] = distribution.get(score_key, 0) + 1
    
    # 세부 평점 평균 계산
    price_scores = [float(r.price_score) for r in ratings if r.price_score]
    service_scores = [float(r.service_score) for r in ratings if r.service_score]
    punctuality_scores = [float(r.punctuality_score) for r in ratings if r.punctuality_score]
    communication_scores = [float(r.communication_score) for r in ratings if r.communication_score]
    
    return ForwarderRatingStats(
        forwarder_id=forwarder_id,
        company=forwarder.company,
        average_score=float(forwarder.rating) if forwarder.rating else 3.0,
        total_ratings=len(ratings),
        score_distribution=distribution,
        avg_price_score=sum(price_scores) / len(price_scores) if price_scores else None,
        avg_service_score=sum(service_scores) / len(service_scores) if service_scores else None,
        avg_punctuality_score=sum(punctuality_scores) / len(punctuality_scores) if punctuality_scores else None,
        avg_communication_score=sum(communication_scores) / len(communication_scores) if communication_scores else None
    )


@app.get("/api/ratings/bidding/{bidding_id}", response_model=Optional[RatingResponse], tags=["Ratings"])
def get_bidding_rating(
    bidding_id: int,
    customer_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 비딩에 대한 평점 조회
    """
    rating = db.query(Rating).filter(
        Rating.bidding_id == bidding_id,
        Rating.customer_id == customer_id
    ).first()
    
    if not rating:
        return None
    
    return RatingResponse(
        id=rating.id,
        bidding_id=rating.bidding_id,
        forwarder_id=rating.forwarder_id,
        customer_id=rating.customer_id,
        score=float(rating.score),
        price_score=float(rating.price_score) if rating.price_score else None,
        service_score=float(rating.service_score) if rating.service_score else None,
        punctuality_score=float(rating.punctuality_score) if rating.punctuality_score else None,
        communication_score=float(rating.communication_score) if rating.communication_score else None,
        comment=rating.comment,
        is_visible=rating.is_visible,
        created_at=rating.created_at
    )


# ==========================================
# FORWARDER PROFILE ENDPOINT
# ==========================================

@app.get("/api/forwarders/{forwarder_id}/profile", response_model=ForwarderProfileResponse, tags=["Forwarder Profile"])
def get_forwarder_profile(
    forwarder_id: int,
    limit_reviews: int = 10,
    db: Session = Depends(get_db)
):
    """
    포워더 프로필 상세 조회
    
    - 포워더 기본 정보 및 평점
    - 주요 운송 루트 (Top 5)
    - 운송 모드별 통계
    - 최근 리뷰 목록
    """
    # 포워더 조회
    forwarder = db.query(Forwarder).filter(Forwarder.id == forwarder_id).first()
    if not forwarder:
        raise HTTPException(status_code=404, detail="Forwarder not found")
    
    # 모든 입찰 조회 (submitted 또는 awarded)
    bids = db.query(Bid).filter(
        Bid.forwarder_id == forwarder_id,
        Bid.status.in_(["submitted", "awarded"])
    ).all()
    
    total_bids = len(bids)
    total_awarded = sum(1 for b in bids if b.status == "awarded")
    award_rate = (total_awarded / total_bids * 100) if total_bids > 0 else 0.0
    
    # 주요 루트 계산 (입찰 이력 기반)
    route_counts = {}
    for bid in bids:
        bidding = db.query(Bidding).filter(Bidding.id == bid.bidding_id).first()
        if bidding:
            quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
            if quote_req:
                route_key = (quote_req.pol, quote_req.pod)
                if route_key not in route_counts:
                    route_counts[route_key] = {"count": 0, "awarded": 0}
                route_counts[route_key]["count"] += 1
                if bid.status == "awarded":
                    route_counts[route_key]["awarded"] += 1
    
    # Top 5 루트 정렬
    top_routes = []
    sorted_routes = sorted(route_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:5]
    for (pol, pod), data in sorted_routes:
        top_routes.append(ForwarderTopRoute(
            pol=pol,
            pod=pod,
            count=data["count"],
            awarded_count=data["awarded"]
        ))
    
    # 운송 모드별 통계
    shipping_mode_counts = {}
    for bid in bids:
        bidding = db.query(Bidding).filter(Bidding.id == bid.bidding_id).first()
        if bidding:
            quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
            if quote_req:
                mode = quote_req.shipping_type
                if mode not in shipping_mode_counts:
                    shipping_mode_counts[mode] = {"count": 0, "awarded": 0}
                shipping_mode_counts[mode]["count"] += 1
                if bid.status == "awarded":
                    shipping_mode_counts[mode]["awarded"] += 1
    
    shipping_mode_stats = []
    for mode, data in shipping_mode_counts.items():
        percentage = (data["count"] / total_bids * 100) if total_bids > 0 else 0.0
        shipping_mode_stats.append(ForwarderShippingModeStats(
            shipping_type=mode,
            count=data["count"],
            percentage=round(percentage, 1),
            awarded_count=data["awarded"]
        ))
    
    # 정렬: count 기준 내림차순
    shipping_mode_stats.sort(key=lambda x: x.count, reverse=True)
    
    # 평점 조회 및 분석
    ratings = db.query(Rating).filter(
        Rating.forwarder_id == forwarder_id,
        Rating.is_visible == True
    ).all()
    
    score_distribution = {}
    price_scores = []
    service_scores = []
    punctuality_scores = []
    communication_scores = []
    
    for r in ratings:
        score_key = str(float(r.score))
        score_distribution[score_key] = score_distribution.get(score_key, 0) + 1
        if r.price_score:
            price_scores.append(float(r.price_score))
        if r.service_score:
            service_scores.append(float(r.service_score))
        if r.punctuality_score:
            punctuality_scores.append(float(r.punctuality_score))
        if r.communication_score:
            communication_scores.append(float(r.communication_score))
    
    # 리뷰 목록 조회 (최신순)
    reviews_query = db.query(Rating).filter(
        Rating.forwarder_id == forwarder_id,
        Rating.is_visible == True
    ).order_by(Rating.created_at.desc()).limit(limit_reviews).all()
    
    reviews = []
    for r in reviews_query:
        # 비딩 정보 조회
        bidding = db.query(Bidding).filter(Bidding.id == r.bidding_id).first()
        quote_req = None
        if bidding:
            quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
        
        # 화주 정보 조회
        customer = db.query(Customer).filter(Customer.id == r.customer_id).first()
        customer_company_masked = mask_company_name(customer.company) if customer else "***"
        
        reviews.append(ForwarderReviewItem(
            id=r.id,
            score=float(r.score),
            price_score=float(r.price_score) if r.price_score else None,
            service_score=float(r.service_score) if r.service_score else None,
            punctuality_score=float(r.punctuality_score) if r.punctuality_score else None,
            communication_score=float(r.communication_score) if r.communication_score else None,
            comment=r.comment,
            bidding_no=bidding.bidding_no if bidding else "",
            pol=quote_req.pol if quote_req else "",
            pod=quote_req.pod if quote_req else "",
            shipping_type=quote_req.shipping_type if quote_req else "",
            created_at=r.created_at,
            customer_company_masked=customer_company_masked
        ))
    
    return ForwarderProfileResponse(
        forwarder_id=forwarder.id,
        company=forwarder.company,
        company_masked=mask_company_name(forwarder.company),
        rating=float(forwarder.rating) if forwarder.rating else 3.0,
        rating_count=forwarder.rating_count or 0,
        avg_price_score=sum(price_scores) / len(price_scores) if price_scores else None,
        avg_service_score=sum(service_scores) / len(service_scores) if service_scores else None,
        avg_punctuality_score=sum(punctuality_scores) / len(punctuality_scores) if punctuality_scores else None,
        avg_communication_score=sum(communication_scores) / len(communication_scores) if communication_scores else None,
        score_distribution=score_distribution,
        total_bids=total_bids,
        total_awarded=total_awarded,
        award_rate=round(award_rate, 1),
        top_routes=top_routes,
        shipping_mode_stats=shipping_mode_stats,
        reviews=reviews,
        member_since=forwarder.created_at
    )


# ==========================================
# ANALYTICS ENDPOINTS - SHIPPER
# ==========================================

def parse_date_range(from_date: Optional[str], to_date: Optional[str]):
    """날짜 범위 파싱 (기본: 최근 12개월)"""
    if to_date:
        end_date = datetime.strptime(to_date, "%Y-%m-%d")
    else:
        end_date = datetime.now()
    
    if from_date:
        start_date = datetime.strptime(from_date, "%Y-%m-%d")
    else:
        start_date = end_date - timedelta(days=365)
    
    return start_date, end_date


@app.get("/api/analytics/shipper/summary", response_model=ShipperAnalyticsSummary, tags=["Analytics - Shipper"])
def get_shipper_analytics_summary(
    customer_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    화주용 분석 요약 KPI
    
    - total_requests: 총 요청 건수
    - avg_bids_per_request: 요청당 평균 입찰 수
    - award_rate: 낙찰률 (%)
    - total_cost_krw: 총 운송비 (KRW)
    - avg_saving_rate: 평균 절감률 (%)
    """
    start_date, end_date = parse_date_range(from_date, to_date)
    
    # 해당 기간의 Quote Request 조회
    quote_requests = db.query(QuoteRequest).filter(
        QuoteRequest.customer_id == customer_id,
        QuoteRequest.created_at >= start_date,
        QuoteRequest.created_at <= end_date
    ).all()
    
    total_requests = len(quote_requests)
    quote_ids = [q.id for q in quote_requests]
    
    # 비딩 조회
    biddings = db.query(Bidding).filter(
        Bidding.quote_request_id.in_(quote_ids)
    ).all() if quote_ids else []
    
    total_biddings = len(biddings)
    bidding_ids = [b.id for b in biddings]
    
    # 입찰 통계
    if bidding_ids:
        bids = db.query(Bid).filter(
            Bid.bidding_id.in_(bidding_ids),
            Bid.status == "submitted"
        ).all()
        
        awarded_bids = [b for b in bids if b.status == "awarded"]
        total_bids = len(bids)
        awarded_count = len([b for b in biddings if b.status == "awarded"])
        
        # 평균 입찰 수
        avg_bids = total_bids / total_biddings if total_biddings > 0 else 0
        
        # 낙찰률
        award_rate = (awarded_count / total_biddings * 100) if total_biddings > 0 else 0
        
        # 총 비용 및 절감률 계산
        total_cost_krw = 0
        saving_rates = []
        
        for bidding in biddings:
            if bidding.status == "awarded" and bidding.awarded_bid_id:
                awarded_bid = db.query(Bid).filter(Bid.id == bidding.awarded_bid_id).first()
                if awarded_bid:
                    bid_amount = float(awarded_bid.total_amount_krw) if awarded_bid.total_amount_krw else convert_to_krw(float(awarded_bid.total_amount))
                    total_cost_krw += bid_amount
                    
                    # 최고가 대비 절감률 계산
                    all_bids = db.query(Bid).filter(
                        Bid.bidding_id == bidding.id,
                        Bid.status.in_(["submitted", "awarded", "rejected"])
                    ).all()
                    
                    if all_bids:
                        max_bid = max(float(b.total_amount_krw) if b.total_amount_krw else convert_to_krw(float(b.total_amount)) for b in all_bids)
                        if max_bid > 0:
                            saving = (max_bid - bid_amount) / max_bid * 100
                            saving_rates.append(saving)
        
        avg_saving_rate = sum(saving_rates) / len(saving_rates) if saving_rates else 0
    else:
        avg_bids = 0
        award_rate = 0
        total_cost_krw = 0
        avg_saving_rate = 0
    
    return ShipperAnalyticsSummary(
        period=AnalyticsPeriod(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        ),
        total_requests=total_requests,
        total_biddings=total_biddings,
        avg_bids_per_request=round(avg_bids, 1),
        award_rate=round(award_rate, 1),
        total_cost_krw=round(total_cost_krw, 0),
        avg_saving_rate=round(avg_saving_rate, 1)
    )


@app.get("/api/analytics/shipper/monthly-trend", response_model=ShipperMonthlyTrendResponse, tags=["Analytics - Shipper"])
def get_shipper_monthly_trend(
    customer_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    화주용 월별 추이 데이터
    """
    start_date, end_date = parse_date_range(from_date, to_date)
    
    # 월별 데이터 집계
    monthly_data = {}
    
    # Quote Request와 Bidding 조인 쿼리
    results = db.query(
        QuoteRequest, Bidding
    ).join(
        Bidding, Bidding.quote_request_id == QuoteRequest.id
    ).filter(
        QuoteRequest.customer_id == customer_id,
        QuoteRequest.created_at >= start_date,
        QuoteRequest.created_at <= end_date
    ).all()
    
    for quote_req, bidding in results:
        month_key = quote_req.created_at.strftime("%Y-%m")
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                "request_count": 0,
                "bid_count": 0,
                "awarded_count": 0,
                "total_cost_krw": 0,
                "bid_prices": []
            }
        
        monthly_data[month_key]["request_count"] += 1
        
        # 입찰 수 집계
        bids = db.query(Bid).filter(
            Bid.bidding_id == bidding.id,
            Bid.status.in_(["submitted", "awarded", "rejected"])
        ).all()
        
        monthly_data[month_key]["bid_count"] += len(bids)
        
        if bidding.status == "awarded":
            monthly_data[month_key]["awarded_count"] += 1
            
            if bidding.awarded_bid_id:
                awarded_bid = db.query(Bid).filter(Bid.id == bidding.awarded_bid_id).first()
                if awarded_bid:
                    bid_amount = float(awarded_bid.total_amount_krw) if awarded_bid.total_amount_krw else convert_to_krw(float(awarded_bid.total_amount))
                    monthly_data[month_key]["total_cost_krw"] += bid_amount
                    monthly_data[month_key]["bid_prices"].append(bid_amount)
    
    # 응답 데이터 구성
    trend_items = []
    for month in sorted(monthly_data.keys()):
        data = monthly_data[month]
        avg_price = sum(data["bid_prices"]) / len(data["bid_prices"]) if data["bid_prices"] else 0
        
        trend_items.append(MonthlyTrendItem(
            month=month,
            request_count=data["request_count"],
            bid_count=data["bid_count"],
            awarded_count=data["awarded_count"],
            total_cost_krw=round(data["total_cost_krw"], 0),
            avg_bid_price_krw=round(avg_price, 0)
        ))
    
    return ShipperMonthlyTrendResponse(
        period=AnalyticsPeriod(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        ),
        data=trend_items
    )


@app.get("/api/analytics/shipper/cost-by-type", response_model=ShipperCostByTypeResponse, tags=["Analytics - Shipper"])
def get_shipper_cost_by_type(
    customer_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    화주용 운송타입별 비용 분석
    """
    start_date, end_date = parse_date_range(from_date, to_date)
    
    # 운송타입별 집계
    type_data = {}
    
    results = db.query(
        QuoteRequest, Bidding
    ).join(
        Bidding, Bidding.quote_request_id == QuoteRequest.id
    ).filter(
        QuoteRequest.customer_id == customer_id,
        QuoteRequest.created_at >= start_date,
        QuoteRequest.created_at <= end_date,
        Bidding.status == "awarded"
    ).all()
    
    total_cost = 0
    
    for quote_req, bidding in results:
        ship_type = quote_req.shipping_type
        
        if ship_type not in type_data:
            type_data[ship_type] = {"count": 0, "total_cost_krw": 0}
        
        type_data[ship_type]["count"] += 1
        
        if bidding.awarded_bid_id:
            awarded_bid = db.query(Bid).filter(Bid.id == bidding.awarded_bid_id).first()
            if awarded_bid:
                bid_amount = float(awarded_bid.total_amount_krw) if awarded_bid.total_amount_krw else convert_to_krw(float(awarded_bid.total_amount))
                type_data[ship_type]["total_cost_krw"] += bid_amount
                total_cost += bid_amount
    
    # 응답 데이터 구성
    cost_items = []
    for ship_type, data in type_data.items():
        percentage = (data["total_cost_krw"] / total_cost * 100) if total_cost > 0 else 0
        cost_items.append(CostByTypeItem(
            shipping_type=ship_type,
            count=data["count"],
            total_cost_krw=round(data["total_cost_krw"], 0),
            percentage=round(percentage, 1)
        ))
    
    # 비용 순으로 정렬
    cost_items.sort(key=lambda x: x.total_cost_krw, reverse=True)
    
    return ShipperCostByTypeResponse(
        period=AnalyticsPeriod(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        ),
        data=cost_items
    )


@app.get("/api/analytics/shipper/route-stats", response_model=ShipperRouteStatsResponse, tags=["Analytics - Shipper"])
def get_shipper_route_stats(
    customer_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    화주용 구간별 통계 (자주 이용하는 구간)
    """
    start_date, end_date = parse_date_range(from_date, to_date)
    
    # 구간별 집계
    route_data = {}
    
    results = db.query(
        QuoteRequest, Bidding
    ).join(
        Bidding, Bidding.quote_request_id == QuoteRequest.id
    ).filter(
        QuoteRequest.customer_id == customer_id,
        QuoteRequest.created_at >= start_date,
        QuoteRequest.created_at <= end_date
    ).all()
    
    for quote_req, bidding in results:
        route_key = f"{quote_req.pol}|{quote_req.pod}"
        
        if route_key not in route_data:
            route_data[route_key] = {
                "pol": quote_req.pol,
                "pod": quote_req.pod,
                "count": 0,
                "bid_prices": []
            }
        
        route_data[route_key]["count"] += 1
        
        # 입찰가 수집
        bids = db.query(Bid).filter(
            Bid.bidding_id == bidding.id,
            Bid.status.in_(["submitted", "awarded", "rejected"])
        ).all()
        
        for bid in bids:
            bid_amount = float(bid.total_amount_krw) if bid.total_amount_krw else convert_to_krw(float(bid.total_amount))
            route_data[route_key]["bid_prices"].append(bid_amount)
    
    # 응답 데이터 구성
    route_items = []
    for route_key, data in route_data.items():
        if data["bid_prices"]:
            route_items.append(RouteStatItem(
                pol=data["pol"],
                pod=data["pod"],
                count=data["count"],
                avg_bid_price_krw=round(sum(data["bid_prices"]) / len(data["bid_prices"]), 0),
                min_bid_price_krw=round(min(data["bid_prices"]), 0),
                max_bid_price_krw=round(max(data["bid_prices"]), 0)
            ))
    
    # 이용 횟수 순으로 정렬
    route_items.sort(key=lambda x: x.count, reverse=True)
    
    return ShipperRouteStatsResponse(
        period=AnalyticsPeriod(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        ),
        data=route_items[:limit]
    )


@app.get("/api/analytics/shipper/forwarder-ranking", response_model=ShipperForwarderRankingResponse, tags=["Analytics - Shipper"])
def get_shipper_forwarder_ranking(
    customer_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    화주용 운송사 순위 (선정 횟수 기준)
    """
    start_date, end_date = parse_date_range(from_date, to_date)
    
    # 운송사별 집계
    forwarder_data = {}
    
    # 해당 기간의 낙찰된 비딩 조회
    results = db.query(
        QuoteRequest, Bidding, Bid, Forwarder
    ).join(
        Bidding, Bidding.quote_request_id == QuoteRequest.id
    ).join(
        Bid, Bid.id == Bidding.awarded_bid_id
    ).join(
        Forwarder, Forwarder.id == Bid.forwarder_id
    ).filter(
        QuoteRequest.customer_id == customer_id,
        QuoteRequest.created_at >= start_date,
        QuoteRequest.created_at <= end_date,
        Bidding.status == "awarded"
    ).all()
    
    for quote_req, bidding, bid, forwarder in results:
        fwd_id = forwarder.id
        
        if fwd_id not in forwarder_data:
            forwarder_data[fwd_id] = {
                "forwarder": forwarder,
                "awarded_count": 0,
                "total_amount_krw": 0
            }
        
        forwarder_data[fwd_id]["awarded_count"] += 1
        bid_amount = float(bid.total_amount_krw) if bid.total_amount_krw else convert_to_krw(float(bid.total_amount))
        forwarder_data[fwd_id]["total_amount_krw"] += bid_amount
    
    # 응답 데이터 구성
    ranking_items = []
    for fwd_id, data in forwarder_data.items():
        forwarder = data["forwarder"]
        ranking_items.append({
            "forwarder_id": fwd_id,
            "company_masked": mask_company_name(forwarder.company),
            "awarded_count": data["awarded_count"],
            "total_amount_krw": data["total_amount_krw"],
            "avg_rating": float(forwarder.rating) if forwarder.rating else 3.0,
            "rating_count": forwarder.rating_count or 0
        })
    
    # 선정 횟수 순으로 정렬
    ranking_items.sort(key=lambda x: x["awarded_count"], reverse=True)
    
    # 순위 부여
    final_items = []
    for rank, item in enumerate(ranking_items[:limit], 1):
        final_items.append(ForwarderRankingItem(
            rank=rank,
            forwarder_id=item["forwarder_id"],
            company_masked=item["company_masked"],
            awarded_count=item["awarded_count"],
            total_amount_krw=round(item["total_amount_krw"], 0),
            avg_rating=item["avg_rating"],
            rating_count=item["rating_count"]
        ))
    
    return ShipperForwarderRankingResponse(
        period=AnalyticsPeriod(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        ),
        data=final_items
    )


# ==========================================
# ANALYTICS ENDPOINTS - FORWARDER
# ==========================================

@app.get("/api/analytics/forwarder/summary", response_model=ForwarderAnalyticsSummary, tags=["Analytics - Forwarder"])
def get_forwarder_analytics_summary(
    forwarder_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    운송사용 분석 요약 KPI
    """
    start_date, end_date = parse_date_range(from_date, to_date)
    
    # 해당 기간의 입찰 조회
    bids = db.query(Bid).filter(
        Bid.forwarder_id == forwarder_id,
        Bid.created_at >= start_date,
        Bid.created_at <= end_date,
        Bid.status.in_(["submitted", "awarded", "rejected"])
    ).all()
    
    total_bids = len(bids)
    awarded_bids = [b for b in bids if b.status == "awarded"]
    rejected_bids = [b for b in bids if b.status == "rejected"]
    
    awarded_count = len(awarded_bids)
    rejected_count = len(rejected_bids)
    award_rate = (awarded_count / total_bids * 100) if total_bids > 0 else 0
    
    # 총 수주액
    total_revenue = sum(
        float(b.total_amount_krw) if b.total_amount_krw else convert_to_krw(float(b.total_amount))
        for b in awarded_bids
    )
    
    # 평균 순위 계산
    ranks = []
    for bid in bids:
        # 해당 비딩의 모든 입찰 조회
        all_bids = db.query(Bid).filter(
            Bid.bidding_id == bid.bidding_id,
            Bid.status.in_(["submitted", "awarded", "rejected"])
        ).all()
        
        # 입찰가 순으로 정렬하여 순위 계산
        sorted_bids = sorted(all_bids, key=lambda x: float(x.total_amount_krw) if x.total_amount_krw else convert_to_krw(float(x.total_amount)))
        for rank, b in enumerate(sorted_bids, 1):
            if b.id == bid.id:
                ranks.append(rank)
                break
    
    avg_rank = sum(ranks) / len(ranks) if ranks else 0
    
    # 평균 평점
    forwarder = db.query(Forwarder).filter(Forwarder.id == forwarder_id).first()
    avg_rating = float(forwarder.rating) if forwarder and forwarder.rating else 3.0
    
    return ForwarderAnalyticsSummary(
        period=AnalyticsPeriod(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        ),
        total_bids=total_bids,
        awarded_count=awarded_count,
        rejected_count=rejected_count,
        award_rate=round(award_rate, 1),
        avg_rank=round(avg_rank, 1),
        total_revenue_krw=round(total_revenue, 0),
        avg_rating=avg_rating
    )


@app.get("/api/analytics/forwarder/monthly-trend", response_model=ForwarderMonthlyTrendResponse, tags=["Analytics - Forwarder"])
def get_forwarder_monthly_trend(
    forwarder_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    운송사용 월별 추이 데이터
    """
    start_date, end_date = parse_date_range(from_date, to_date)
    
    # 월별 데이터 집계
    monthly_data = {}
    
    bids = db.query(Bid).filter(
        Bid.forwarder_id == forwarder_id,
        Bid.created_at >= start_date,
        Bid.created_at <= end_date,
        Bid.status.in_(["submitted", "awarded", "rejected"])
    ).all()
    
    for bid in bids:
        month_key = bid.created_at.strftime("%Y-%m")
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                "bid_count": 0,
                "awarded_count": 0,
                "rejected_count": 0,
                "revenue_krw": 0,
                "ranks": []
            }
        
        monthly_data[month_key]["bid_count"] += 1
        
        if bid.status == "awarded":
            monthly_data[month_key]["awarded_count"] += 1
            bid_amount = float(bid.total_amount_krw) if bid.total_amount_krw else convert_to_krw(float(bid.total_amount))
            monthly_data[month_key]["revenue_krw"] += bid_amount
        elif bid.status == "rejected":
            monthly_data[month_key]["rejected_count"] += 1
        
        # 순위 계산
        all_bids = db.query(Bid).filter(
            Bid.bidding_id == bid.bidding_id,
            Bid.status.in_(["submitted", "awarded", "rejected"])
        ).all()
        
        sorted_bids = sorted(all_bids, key=lambda x: float(x.total_amount_krw) if x.total_amount_krw else convert_to_krw(float(x.total_amount)))
        for rank, b in enumerate(sorted_bids, 1):
            if b.id == bid.id:
                monthly_data[month_key]["ranks"].append(rank)
                break
    
    # 응답 데이터 구성
    trend_items = []
    for month in sorted(monthly_data.keys()):
        data = monthly_data[month]
        avg_rank = sum(data["ranks"]) / len(data["ranks"]) if data["ranks"] else 0
        
        trend_items.append(ForwarderMonthlyTrendItem(
            month=month,
            bid_count=data["bid_count"],
            awarded_count=data["awarded_count"],
            rejected_count=data["rejected_count"],
            revenue_krw=round(data["revenue_krw"], 0),
            avg_rank=round(avg_rank, 1)
        ))
    
    return ForwarderMonthlyTrendResponse(
        period=AnalyticsPeriod(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        ),
        data=trend_items
    )


@app.get("/api/analytics/forwarder/bid-stats", response_model=ForwarderBidStatsResponse, tags=["Analytics - Forwarder"])
def get_forwarder_bid_stats(
    forwarder_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    운송사용 운송타입별 입찰 통계
    """
    start_date, end_date = parse_date_range(from_date, to_date)
    
    # 운송타입별 집계
    type_data = {}
    
    bids = db.query(Bid, Bidding, QuoteRequest).join(
        Bidding, Bid.bidding_id == Bidding.id
    ).join(
        QuoteRequest, Bidding.quote_request_id == QuoteRequest.id
    ).filter(
        Bid.forwarder_id == forwarder_id,
        Bid.created_at >= start_date,
        Bid.created_at <= end_date,
        Bid.status.in_(["submitted", "awarded", "rejected"])
    ).all()
    
    for bid, bidding, quote_req in bids:
        ship_type = quote_req.shipping_type
        
        if ship_type not in type_data:
            type_data[ship_type] = {
                "bid_count": 0,
                "awarded_count": 0,
                "total_revenue_krw": 0
            }
        
        type_data[ship_type]["bid_count"] += 1
        
        if bid.status == "awarded":
            type_data[ship_type]["awarded_count"] += 1
            bid_amount = float(bid.total_amount_krw) if bid.total_amount_krw else convert_to_krw(float(bid.total_amount))
            type_data[ship_type]["total_revenue_krw"] += bid_amount
    
    # 응답 데이터 구성
    stat_items = []
    for ship_type, data in type_data.items():
        award_rate = (data["awarded_count"] / data["bid_count"] * 100) if data["bid_count"] > 0 else 0
        stat_items.append(BidStatsByTypeItem(
            shipping_type=ship_type,
            bid_count=data["bid_count"],
            awarded_count=data["awarded_count"],
            award_rate=round(award_rate, 1),
            total_revenue_krw=round(data["total_revenue_krw"], 0)
        ))
    
    return ForwarderBidStatsResponse(
        period=AnalyticsPeriod(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        ),
        data=stat_items
    )


@app.get("/api/analytics/forwarder/competitiveness", response_model=ForwarderCompetitivenessResponse, tags=["Analytics - Forwarder"])
def get_forwarder_competitiveness(
    forwarder_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    운송사용 경쟁력 분석
    """
    start_date, end_date = parse_date_range(from_date, to_date)
    
    # 내 입찰 조회
    my_bids = db.query(Bid).filter(
        Bid.forwarder_id == forwarder_id,
        Bid.created_at >= start_date,
        Bid.created_at <= end_date,
        Bid.status.in_(["submitted", "awarded", "rejected"])
    ).all()
    
    my_bid_amounts = []
    market_bid_amounts = []
    winning_bid_amounts = []
    my_bidding_ids = set()
    
    for bid in my_bids:
        bid_amount = float(bid.total_amount_krw) if bid.total_amount_krw else convert_to_krw(float(bid.total_amount))
        my_bid_amounts.append(bid_amount)
        my_bidding_ids.add(bid.bidding_id)
    
    # 같은 비딩의 모든 입찰 조회 (시장 평균)
    for bidding_id in my_bidding_ids:
        all_bids = db.query(Bid).filter(
            Bid.bidding_id == bidding_id,
            Bid.status.in_(["submitted", "awarded", "rejected"])
        ).all()
        
        for bid in all_bids:
            bid_amount = float(bid.total_amount_krw) if bid.total_amount_krw else convert_to_krw(float(bid.total_amount))
            market_bid_amounts.append(bid_amount)
            
            if bid.status == "awarded":
                winning_bid_amounts.append(bid_amount)
    
    my_avg = sum(my_bid_amounts) / len(my_bid_amounts) if my_bid_amounts else 0
    market_avg = sum(market_bid_amounts) / len(market_bid_amounts) if market_bid_amounts else 0
    winning_avg = sum(winning_bid_amounts) / len(winning_bid_amounts) if winning_bid_amounts else 0
    
    # 가격 경쟁력 (시장 평균 대비 내 평균이 얼마나 낮은지)
    price_competitiveness = ((market_avg - my_avg) / market_avg * 100) if market_avg > 0 else 0
    
    # 시장 대비 낙찰률
    my_awarded = len([b for b in my_bids if b.status == "awarded"])
    my_award_rate = (my_awarded / len(my_bids) * 100) if my_bids else 0
    
    # 시장 전체 낙찰률 계산
    total_biddings = len(my_bidding_ids)
    market_award_rate = (total_biddings / len(market_bid_amounts) * 100) if market_bid_amounts else 0
    
    win_rate_vs_market = my_award_rate - market_award_rate
    
    return ForwarderCompetitivenessResponse(
        period=AnalyticsPeriod(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        ),
        data=CompetitivenessData(
            my_avg_bid_krw=round(my_avg, 0),
            market_avg_bid_krw=round(market_avg, 0),
            winning_avg_bid_krw=round(winning_avg, 0),
            price_competitiveness=round(price_competitiveness, 1),
            win_rate_vs_market=round(win_rate_vs_market, 1)
        )
    )


@app.get("/api/analytics/forwarder/rating-trend", response_model=ForwarderRatingTrendResponse, tags=["Analytics - Forwarder"])
def get_forwarder_rating_trend(
    forwarder_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    운송사용 평점 추이
    """
    start_date, end_date = parse_date_range(from_date, to_date)
    
    # 운송사 정보
    forwarder = db.query(Forwarder).filter(Forwarder.id == forwarder_id).first()
    if not forwarder:
        raise HTTPException(status_code=404, detail="Forwarder not found")
    
    # 해당 기간의 평점 조회
    ratings = db.query(Rating).filter(
        Rating.forwarder_id == forwarder_id,
        Rating.created_at >= start_date,
        Rating.created_at <= end_date,
        Rating.is_visible == True
    ).all()
    
    # 월별 집계
    monthly_data = {}
    
    for rating in ratings:
        month_key = rating.created_at.strftime("%Y-%m")
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                "scores": [],
                "price_scores": [],
                "service_scores": [],
                "punctuality_scores": [],
                "communication_scores": []
            }
        
        monthly_data[month_key]["scores"].append(float(rating.score))
        
        if rating.price_score:
            monthly_data[month_key]["price_scores"].append(float(rating.price_score))
        if rating.service_score:
            monthly_data[month_key]["service_scores"].append(float(rating.service_score))
        if rating.punctuality_score:
            monthly_data[month_key]["punctuality_scores"].append(float(rating.punctuality_score))
        if rating.communication_score:
            monthly_data[month_key]["communication_scores"].append(float(rating.communication_score))
    
    # 응답 데이터 구성
    trend_items = []
    for month in sorted(monthly_data.keys()):
        data = monthly_data[month]
        
        trend_items.append(RatingTrendItem(
            month=month,
            avg_score=round(sum(data["scores"]) / len(data["scores"]), 1) if data["scores"] else 0,
            rating_count=len(data["scores"]),
            avg_price_score=round(sum(data["price_scores"]) / len(data["price_scores"]), 1) if data["price_scores"] else None,
            avg_service_score=round(sum(data["service_scores"]) / len(data["service_scores"]), 1) if data["service_scores"] else None,
            avg_punctuality_score=round(sum(data["punctuality_scores"]) / len(data["punctuality_scores"]), 1) if data["punctuality_scores"] else None,
            avg_communication_score=round(sum(data["communication_scores"]) / len(data["communication_scores"]), 1) if data["communication_scores"] else None
        ))
    
    return ForwarderRatingTrendResponse(
        period=AnalyticsPeriod(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        ),
        current_rating=float(forwarder.rating) if forwarder.rating else 3.0,
        total_ratings=forwarder.rating_count or 0,
        data=trend_items
    )


# ==========================================
# CONTRACT ENDPOINTS
# ==========================================

def generate_contract_no(db: Session) -> str:
    """Generate unique Contract Number: CT-YYYYMMDD-XXX"""
    date_str = datetime.now().strftime("%Y%m%d")
    
    # Get max sequence for today
    today_contracts = db.query(Contract).filter(
        Contract.contract_no.like(f"CT-{date_str}-%")
    ).count()
    
    seq = str(today_contracts + 1).zfill(3)
    return f"CT-{date_str}-{seq}"


@app.get("/api/contract/{contract_id}", response_model=ContractDetailResponse, tags=["Contract"])
def get_contract_detail(
    contract_id: int,
    db: Session = Depends(get_db)
):
    """계약 상세 조회"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    bidding = db.query(Bidding).filter(Bidding.id == contract.bidding_id).first()
    quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first() if bidding else None
    customer = db.query(Customer).filter(Customer.id == contract.customer_id).first()
    forwarder = db.query(Forwarder).filter(Forwarder.id == contract.forwarder_id).first()
    
    # Get shipment if exists
    shipment = db.query(Shipment).filter(Shipment.contract_id == contract.id).first()
    shipment_data = None
    if shipment:
        shipment_data = ShipmentResponse(
            id=shipment.id,
            shipment_no=shipment.shipment_no,
            contract_id=shipment.contract_id,
            current_status=shipment.current_status,
            current_location=shipment.current_location,
            estimated_pickup=shipment.estimated_pickup,
            actual_pickup=shipment.actual_pickup,
            estimated_delivery=shipment.estimated_delivery,
            actual_delivery=shipment.actual_delivery,
            bl_no=shipment.bl_no,
            vessel_flight=shipment.vessel_flight,
            delivery_confirmed=shipment.delivery_confirmed,
            delivery_confirmed_at=shipment.delivery_confirmed_at,
            auto_confirmed=shipment.auto_confirmed,
            created_at=shipment.created_at,
            updated_at=shipment.updated_at
        )
    
    return ContractDetailResponse(
        id=contract.id,
        contract_no=contract.contract_no,
        bidding_id=contract.bidding_id,
        awarded_bid_id=contract.awarded_bid_id,
        customer_id=contract.customer_id,
        forwarder_id=contract.forwarder_id,
        total_amount_krw=float(contract.total_amount_krw),
        freight_charge=float(contract.freight_charge) if contract.freight_charge else None,
        local_charge=float(contract.local_charge) if contract.local_charge else None,
        other_charge=float(contract.other_charge) if contract.other_charge else None,
        transit_time=contract.transit_time,
        carrier=contract.carrier,
        contract_terms=contract.contract_terms,
        shipper_confirmed=contract.shipper_confirmed,
        shipper_confirmed_at=contract.shipper_confirmed_at,
        forwarder_confirmed=contract.forwarder_confirmed,
        forwarder_confirmed_at=contract.forwarder_confirmed_at,
        status=contract.status,
        confirmed_at=contract.confirmed_at,
        cancelled_by=contract.cancelled_by,
        cancelled_at=contract.cancelled_at,
        cancel_reason=contract.cancel_reason,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        bidding_no=bidding.bidding_no if bidding else None,
        pol=quote_req.pol if quote_req else None,
        pod=quote_req.pod if quote_req else None,
        shipping_type=quote_req.shipping_type if quote_req else None,
        customer_company=customer.company if customer else None,
        forwarder_company=forwarder.company if forwarder else None,
        shipment=shipment_data
    )


@app.get("/api/contracts", response_model=ContractListResponse, tags=["Contract"])
def get_contract_list(
    user_type: str,  # shipper, forwarder
    user_id: int,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """계약 목록 조회"""
    query = db.query(Contract)
    
    if user_type == "shipper":
        query = query.filter(Contract.customer_id == user_id)
    else:
        query = query.filter(Contract.forwarder_id == user_id)
    
    if status:
        query = query.filter(Contract.status == status)
    
    total = query.count()
    contracts = query.order_by(Contract.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    items = []
    for contract in contracts:
        bidding = db.query(Bidding).filter(Bidding.id == contract.bidding_id).first()
        quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first() if bidding else None
        
        items.append(ContractListItem(
            id=contract.id,
            contract_no=contract.contract_no,
            bidding_no=bidding.bidding_no if bidding else "",
            pol=quote_req.pol if quote_req else "",
            pod=quote_req.pod if quote_req else "",
            shipping_type=quote_req.shipping_type if quote_req else "",
            total_amount_krw=float(contract.total_amount_krw),
            status=contract.status,
            shipper_confirmed=contract.shipper_confirmed,
            forwarder_confirmed=contract.forwarder_confirmed,
            created_at=contract.created_at
        ))
    
    return ContractListResponse(
        total=total,
        page=page,
        limit=limit,
        data=items
    )


@app.post("/api/contract/{contract_id}/confirm", tags=["Contract"])
def confirm_contract(
    contract_id: int,
    request: ContractConfirmRequest,
    db: Session = Depends(get_db)
):
    """계약 확정 (화주/포워더 각각 확정)"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract.status == "cancelled":
        raise HTTPException(status_code=400, detail="Contract is cancelled")
    
    if contract.status == "confirmed":
        raise HTTPException(status_code=400, detail="Contract is already confirmed")
    
    now = datetime.now()
    
    if request.user_type == "shipper":
        if contract.customer_id != request.user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        contract.shipper_confirmed = True
        contract.shipper_confirmed_at = now
    elif request.user_type == "forwarder":
        if contract.forwarder_id != request.user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        contract.forwarder_confirmed = True
        contract.forwarder_confirmed_at = now
    else:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    # Check if both confirmed
    if contract.shipper_confirmed and contract.forwarder_confirmed:
        contract.status = "confirmed"
        contract.confirmed_at = now
        
        # Create shipment automatically
        shipment = Shipment(
            shipment_no=f"SH-{datetime.now().strftime('%Y%m%d')}-{str(contract.id).zfill(3)}",
            contract_id=contract.id,
            current_status="booked"
        )
        db.add(shipment)
        
        # Add initial tracking
        tracking = ShipmentTracking(
            shipment_id=shipment.id,
            status="booked",
            remark="계약 확정됨",
            updated_by_type="system"
        )
        db.add(tracking)
        
        # Send notifications
        notification_shipper = Notification(
            recipient_type="customer",
            recipient_id=contract.customer_id,
            notification_type="contract_confirmed",
            title="계약이 확정되었습니다",
            message=f"계약번호 {contract.contract_no}의 계약이 양측 확정되었습니다.",
            related_type="contract",
            related_id=contract.id
        )
        notification_forwarder = Notification(
            recipient_type="forwarder",
            recipient_id=contract.forwarder_id,
            notification_type="contract_confirmed",
            title="계약이 확정되었습니다",
            message=f"계약번호 {contract.contract_no}의 계약이 양측 확정되었습니다.",
            related_type="contract",
            related_id=contract.id
        )
        db.add(notification_shipper)
        db.add(notification_forwarder)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Contract confirmed successfully",
        "contract_no": contract.contract_no,
        "status": contract.status,
        "shipper_confirmed": contract.shipper_confirmed,
        "forwarder_confirmed": contract.forwarder_confirmed
    }


@app.post("/api/contract/{contract_id}/cancel", tags=["Contract"])
def cancel_contract(
    contract_id: int,
    request: ContractCancelRequest,
    db: Session = Depends(get_db)
):
    """계약 취소"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract.status in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Contract cannot be cancelled (status: {contract.status})")
    
    # Verify user
    if request.user_type == "shipper" and contract.customer_id != request.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if request.user_type == "forwarder" and contract.forwarder_id != request.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    contract.status = "cancelled"
    contract.cancelled_by = request.user_type
    contract.cancelled_at = datetime.now()
    contract.cancel_reason = request.reason
    
    # Notify the other party
    if request.user_type == "shipper":
        notification = Notification(
            recipient_type="forwarder",
            recipient_id=contract.forwarder_id,
            notification_type="contract_cancelled",
            title="계약이 취소되었습니다",
            message=f"계약번호 {contract.contract_no}이 화주에 의해 취소되었습니다. 사유: {request.reason or '미기재'}",
            related_type="contract",
            related_id=contract.id
        )
    else:
        notification = Notification(
            recipient_type="customer",
            recipient_id=contract.customer_id,
            notification_type="contract_cancelled",
            title="계약이 취소되었습니다",
            message=f"계약번호 {contract.contract_no}이 운송사에 의해 취소되었습니다. 사유: {request.reason or '미기재'}",
            related_type="contract",
            related_id=contract.id
        )
    db.add(notification)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Contract cancelled",
        "contract_no": contract.contract_no
    }


# ==========================================
# SHIPMENT ENDPOINTS
# ==========================================

@app.get("/api/shipment/{shipment_id}", response_model=ShipmentDetailResponse, tags=["Shipment"])
def get_shipment_detail(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    """배송 상세 조회"""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    contract = db.query(Contract).filter(Contract.id == shipment.contract_id).first()
    bidding = db.query(Bidding).filter(Bidding.id == contract.bidding_id).first() if contract else None
    quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first() if bidding else None
    
    tracking_history = db.query(ShipmentTracking).filter(
        ShipmentTracking.shipment_id == shipment.id
    ).order_by(ShipmentTracking.created_at.desc()).all()
    
    tracking_items = [
        ShipmentTrackingItem(
            id=t.id,
            status=t.status,
            location=t.location,
            remark=t.remark,
            updated_by_type=t.updated_by_type,
            created_at=t.created_at
        ) for t in tracking_history
    ]
    
    return ShipmentDetailResponse(
        id=shipment.id,
        shipment_no=shipment.shipment_no,
        contract_id=shipment.contract_id,
        current_status=shipment.current_status,
        current_location=shipment.current_location,
        estimated_pickup=shipment.estimated_pickup,
        actual_pickup=shipment.actual_pickup,
        estimated_delivery=shipment.estimated_delivery,
        actual_delivery=shipment.actual_delivery,
        bl_no=shipment.bl_no,
        vessel_flight=shipment.vessel_flight,
        delivery_confirmed=shipment.delivery_confirmed,
        delivery_confirmed_at=shipment.delivery_confirmed_at,
        auto_confirmed=shipment.auto_confirmed,
        created_at=shipment.created_at,
        updated_at=shipment.updated_at,
        tracking_history=tracking_items,
        contract_no=contract.contract_no if contract else None,
        bidding_no=bidding.bidding_no if bidding else None,
        pol=quote_req.pol if quote_req else None,
        pod=quote_req.pod if quote_req else None
    )


@app.get("/api/shipments", response_model=ShipmentListResponse, tags=["Shipment"])
def get_shipment_list(
    user_type: str,
    user_id: int,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """배송 목록 조회"""
    query = db.query(Shipment).join(Contract)
    
    if user_type == "shipper":
        query = query.filter(Contract.customer_id == user_id)
    else:
        query = query.filter(Contract.forwarder_id == user_id)
    
    if status:
        query = query.filter(Shipment.current_status == status)
    
    total = query.count()
    shipments = query.order_by(Shipment.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    items = []
    for shipment in shipments:
        contract = db.query(Contract).filter(Contract.id == shipment.contract_id).first()
        bidding = db.query(Bidding).filter(Bidding.id == contract.bidding_id).first() if contract else None
        quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first() if bidding else None
        
        items.append(ShipmentListItem(
            id=shipment.id,
            shipment_no=shipment.shipment_no,
            contract_no=contract.contract_no if contract else "",
            bidding_no=bidding.bidding_no if bidding else "",
            pol=quote_req.pol if quote_req else "",
            pod=quote_req.pod if quote_req else "",
            current_status=shipment.current_status,
            estimated_delivery=shipment.estimated_delivery,
            delivery_confirmed=shipment.delivery_confirmed
        ))
    
    return ShipmentListResponse(
        total=total,
        page=page,
        limit=limit,
        data=items
    )


@app.post("/api/shipment/{shipment_id}/status", tags=["Shipment"])
def update_shipment_status(
    shipment_id: int,
    request: ShipmentStatusUpdate,
    db: Session = Depends(get_db)
):
    """배송 상태 업데이트 (포워더)"""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    contract = db.query(Contract).filter(Contract.id == shipment.contract_id).first()
    if contract.forwarder_id != request.forwarder_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update shipment
    shipment.current_status = request.status
    if request.location:
        shipment.current_location = request.location
    
    # Handle specific statuses
    if request.status == "picked_up":
        shipment.actual_pickup = datetime.now()
    elif request.status == "delivered":
        shipment.actual_delivery = datetime.now()
        contract.status = "active"  # 배송 완료 상태로 변경
    
    # Add tracking history
    tracking = ShipmentTracking(
        shipment_id=shipment.id,
        status=request.status,
        location=request.location,
        remark=request.remark,
        updated_by_type="forwarder",
        updated_by_id=request.forwarder_id
    )
    db.add(tracking)
    
    # Notify shipper
    status_labels = {
        "picked_up": "화물 픽업 완료",
        "in_transit": "운송 중",
        "arrived_port": "목적지항 도착",
        "customs": "통관 진행 중",
        "out_for_delivery": "배송 출발",
        "delivered": "배송 완료"
    }
    
    notification = Notification(
        recipient_type="customer",
        recipient_id=contract.customer_id,
        notification_type="shipment_status_update",
        title=f"배송 상태 업데이트: {status_labels.get(request.status, request.status)}",
        message=f"배송번호 {shipment.shipment_no}의 상태가 업데이트되었습니다.",
        related_type="shipment",
        related_id=shipment.id
    )
    db.add(notification)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Shipment status updated",
        "shipment_no": shipment.shipment_no,
        "status": shipment.current_status
    }


@app.post("/api/shipment/{shipment_id}/confirm-delivery", tags=["Shipment"])
def confirm_delivery(
    shipment_id: int,
    request: ShipmentDeliveryConfirm,
    db: Session = Depends(get_db)
):
    """배송 완료 확인 (화주)"""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    contract = db.query(Contract).filter(Contract.id == shipment.contract_id).first()
    if contract.customer_id != request.customer_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if shipment.current_status != "delivered":
        raise HTTPException(status_code=400, detail="Shipment is not in delivered status")
    
    # Confirm delivery
    shipment.current_status = "completed"
    shipment.delivery_confirmed = True
    shipment.delivery_confirmed_at = datetime.now()
    
    # Update contract status
    contract.status = "completed"
    
    # Add tracking
    tracking = ShipmentTracking(
        shipment_id=shipment.id,
        status="completed",
        remark="화주 배송 완료 확인",
        updated_by_type="system"
    )
    db.add(tracking)
    
    # Create settlement
    settlement = Settlement(
        settlement_no=f"ST-{datetime.now().strftime('%Y%m%d')}-{str(contract.id).zfill(3)}",
        contract_id=contract.id,
        forwarder_id=contract.forwarder_id,
        customer_id=contract.customer_id,
        total_amount_krw=contract.total_amount_krw,
        service_fee=0,
        net_amount=contract.total_amount_krw,
        status="pending"
    )
    db.add(settlement)
    
    # Notify forwarder
    notification = Notification(
        recipient_type="forwarder",
        recipient_id=contract.forwarder_id,
        notification_type="delivery_confirmed",
        title="배송 완료가 확인되었습니다",
        message=f"배송번호 {shipment.shipment_no}의 배송 완료가 화주에 의해 확인되었습니다. 정산을 진행해주세요.",
        related_type="shipment",
        related_id=shipment.id
    )
    db.add(notification)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Delivery confirmed",
        "shipment_no": shipment.shipment_no
    }


# ==========================================
# SETTLEMENT ENDPOINTS
# ==========================================

@app.post("/api/settlement/request", tags=["Settlement"])
def request_settlement(
    request: SettlementRequest,
    db: Session = Depends(get_db)
):
    """정산 요청"""
    settlement = db.query(Settlement).filter(
        Settlement.contract_id == request.contract_id,
        Settlement.forwarder_id == request.forwarder_id
    ).first()
    
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    if settlement.status != "pending":
        raise HTTPException(status_code=400, detail=f"Settlement status is {settlement.status}")
    
    settlement.status = "requested"
    settlement.requested_at = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "message": "Settlement requested",
        "settlement_no": settlement.settlement_no
    }


@app.get("/api/settlements", response_model=SettlementListResponse, tags=["Settlement"])
def get_settlement_list(
    user_type: str,
    user_id: int,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """정산 목록 조회"""
    query = db.query(Settlement)
    
    if user_type == "shipper":
        query = query.filter(Settlement.customer_id == user_id)
    else:
        query = query.filter(Settlement.forwarder_id == user_id)
    
    if status:
        query = query.filter(Settlement.status == status)
    
    total = query.count()
    settlements = query.order_by(Settlement.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    items = []
    for settlement in settlements:
        contract = db.query(Contract).filter(Contract.id == settlement.contract_id).first()
        bidding = db.query(Bidding).filter(Bidding.id == contract.bidding_id).first() if contract else None
        
        items.append(SettlementListItem(
            id=settlement.id,
            settlement_no=settlement.settlement_no,
            contract_no=contract.contract_no if contract else "",
            bidding_no=bidding.bidding_no if bidding else "",
            total_amount_krw=float(settlement.total_amount_krw),
            net_amount=float(settlement.net_amount),
            status=settlement.status,
            requested_at=settlement.requested_at,
            completed_at=settlement.completed_at
        ))
    
    return SettlementListResponse(
        total=total,
        page=page,
        limit=limit,
        data=items
    )


@app.get("/api/settlements/summary", response_model=SettlementSummary, tags=["Settlement"])
def get_settlement_summary(
    user_type: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """정산 요약 (대시보드용)"""
    query = db.query(Settlement)
    
    if user_type == "shipper":
        query = query.filter(Settlement.customer_id == user_id)
    else:
        query = query.filter(Settlement.forwarder_id == user_id)
    
    completed = query.filter(Settlement.status == "completed").all()
    pending = query.filter(Settlement.status.in_(["pending", "requested", "processing"])).all()
    
    return SettlementSummary(
        total_completed=sum(float(s.net_amount) for s in completed),
        total_pending=sum(float(s.net_amount) for s in pending),
        count_completed=len(completed),
        count_pending=len(pending)
    )


# ==========================================
# MESSAGE ENDPOINTS
# ==========================================

@app.post("/api/messages", response_model=MessageResponse, tags=["Message"])
def send_message(
    request: MessageCreate,
    db: Session = Depends(get_db)
):
    """메시지 전송"""
    # Verify bidding exists
    bidding = db.query(Bidding).filter(Bidding.id == request.bidding_id).first()
    if not bidding:
        raise HTTPException(status_code=404, detail="Bidding not found")
    
    message = Message(
        bidding_id=request.bidding_id,
        sender_type=request.sender_type,
        sender_id=request.sender_id,
        recipient_type=request.recipient_type,
        recipient_id=request.recipient_id,
        content=request.content
    )
    db.add(message)
    
    # Send notification
    notification = Notification(
        recipient_type=request.recipient_type,
        recipient_id=request.recipient_id,
        notification_type="new_message",
        title="새 메시지가 도착했습니다",
        message=request.content[:100] + "..." if len(request.content) > 100 else request.content,
        related_type="message",
        related_id=message.id
    )
    db.add(notification)
    
    db.commit()
    db.refresh(message)
    
    # Get sender info
    sender_name = None
    sender_company = None
    if request.sender_type == "shipper":
        customer = db.query(Customer).filter(Customer.id == request.sender_id).first()
        if customer:
            sender_name = customer.name
            sender_company = customer.company
    else:
        forwarder = db.query(Forwarder).filter(Forwarder.id == request.sender_id).first()
        if forwarder:
            sender_name = forwarder.name
            sender_company = forwarder.company
    
    return MessageResponse(
        id=message.id,
        bidding_id=message.bidding_id,
        sender_type=message.sender_type,
        sender_id=message.sender_id,
        recipient_type=message.recipient_type,
        recipient_id=message.recipient_id,
        content=message.content,
        is_read=message.is_read,
        read_at=message.read_at,
        created_at=message.created_at,
        sender_name=sender_name,
        sender_company=sender_company
    )


@app.get("/api/messages/thread/{bidding_id}", response_model=MessageThreadResponse, tags=["Message"])
def get_message_thread(
    bidding_id: int,
    user_type: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """비딩별 메시지 스레드 조회"""
    bidding = db.query(Bidding).filter(Bidding.id == bidding_id).first()
    if not bidding:
        raise HTTPException(status_code=404, detail="Bidding not found")
    
    quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
    
    messages = db.query(Message).filter(
        Message.bidding_id == bidding_id,
        or_(
            and_(Message.sender_type == user_type, Message.sender_id == user_id),
            and_(Message.recipient_type == user_type, Message.recipient_id == user_id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    message_items = []
    unread_count = 0
    
    for msg in messages:
        # Get sender info
        sender_name = None
        sender_company = None
        if msg.sender_type == "shipper":
            customer = db.query(Customer).filter(Customer.id == msg.sender_id).first()
            if customer:
                sender_name = customer.name
                sender_company = customer.company
        else:
            forwarder = db.query(Forwarder).filter(Forwarder.id == msg.sender_id).first()
            if forwarder:
                sender_name = forwarder.name
                sender_company = forwarder.company
        
        message_items.append(MessageResponse(
            id=msg.id,
            bidding_id=msg.bidding_id,
            sender_type=msg.sender_type,
            sender_id=msg.sender_id,
            recipient_type=msg.recipient_type,
            recipient_id=msg.recipient_id,
            content=msg.content,
            is_read=msg.is_read,
            read_at=msg.read_at,
            created_at=msg.created_at,
            sender_name=sender_name,
            sender_company=sender_company
        ))
        
        if not msg.is_read and msg.recipient_type == user_type and msg.recipient_id == user_id:
            unread_count += 1
    
    return MessageThreadResponse(
        bidding_id=bidding_id,
        bidding_no=bidding.bidding_no,
        pol=quote_req.pol if quote_req else "",
        pod=quote_req.pod if quote_req else "",
        messages=message_items,
        unread_count=unread_count
    )


@app.get("/api/messages/unread", response_model=UnreadMessagesResponse, tags=["Message"])
def get_unread_messages(
    user_type: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """읽지 않은 메시지 조회"""
    unread_messages = db.query(Message).filter(
        Message.recipient_type == user_type,
        Message.recipient_id == user_id,
        Message.is_read == False
    ).all()
    
    # Group by bidding
    threads_dict = {}
    for msg in unread_messages:
        if msg.bidding_id not in threads_dict:
            bidding = db.query(Bidding).filter(Bidding.id == msg.bidding_id).first()
            quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first() if bidding else None
            
            threads_dict[msg.bidding_id] = {
                "bidding_id": msg.bidding_id,
                "bidding_no": bidding.bidding_no if bidding else "",
                "pol": quote_req.pol if quote_req else "",
                "pod": quote_req.pod if quote_req else "",
                "messages": [],
                "unread_count": 0
            }
        
        threads_dict[msg.bidding_id]["messages"].append(msg)
        threads_dict[msg.bidding_id]["unread_count"] += 1
    
    threads = []
    for bidding_id, thread_data in threads_dict.items():
        message_items = []
        for msg in thread_data["messages"]:
            message_items.append(MessageResponse(
                id=msg.id,
                bidding_id=msg.bidding_id,
                sender_type=msg.sender_type,
                sender_id=msg.sender_id,
                recipient_type=msg.recipient_type,
                recipient_id=msg.recipient_id,
                content=msg.content,
                is_read=msg.is_read,
                read_at=msg.read_at,
                created_at=msg.created_at
            ))
        
        threads.append(MessageThreadResponse(
            bidding_id=thread_data["bidding_id"],
            bidding_no=thread_data["bidding_no"],
            pol=thread_data["pol"],
            pod=thread_data["pod"],
            messages=message_items,
            unread_count=thread_data["unread_count"]
        ))
    
    return UnreadMessagesResponse(
        total_unread=len(unread_messages),
        threads=threads
    )


@app.put("/api/messages/{message_id}/read", tags=["Message"])
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db)
):
    """메시지 읽음 처리"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.is_read = True
    message.read_at = datetime.now()
    db.commit()
    
    return {"success": True, "message": "Message marked as read"}


# ==========================================
# FAVORITE ROUTES ENDPOINTS
# ==========================================

@app.get("/api/shipper/favorite-routes", response_model=FavoriteRouteListResponse, tags=["Shipper"])
def get_favorite_routes(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """즐겨찾기 구간 목록 조회"""
    routes = db.query(FavoriteRoute).filter(
        FavoriteRoute.customer_id == customer_id
    ).order_by(FavoriteRoute.created_at.desc()).all()
    
    return FavoriteRouteListResponse(
        data=[FavoriteRouteResponse(
            id=r.id,
            customer_id=r.customer_id,
            pol=r.pol,
            pod=r.pod,
            shipping_type=r.shipping_type,
            alias=r.alias,
            created_at=r.created_at
        ) for r in routes]
    )


@app.post("/api/shipper/favorite-routes", response_model=FavoriteRouteResponse, tags=["Shipper"])
def add_favorite_route(
    request: FavoriteRouteCreate,
    db: Session = Depends(get_db)
):
    """즐겨찾기 구간 추가"""
    # Check duplicate
    existing = db.query(FavoriteRoute).filter(
        FavoriteRoute.customer_id == request.customer_id,
        FavoriteRoute.pol == request.pol,
        FavoriteRoute.pod == request.pod
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Route already in favorites")
    
    route = FavoriteRoute(
        customer_id=request.customer_id,
        pol=request.pol,
        pod=request.pod,
        shipping_type=request.shipping_type,
        alias=request.alias
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    
    return FavoriteRouteResponse(
        id=route.id,
        customer_id=route.customer_id,
        pol=route.pol,
        pod=route.pod,
        shipping_type=route.shipping_type,
        alias=route.alias,
        created_at=route.created_at
    )


@app.delete("/api/shipper/favorite-routes/{route_id}", tags=["Shipper"])
def delete_favorite_route(
    route_id: int,
    customer_id: int,
    db: Session = Depends(get_db)
):
    """즐겨찾기 구간 삭제"""
    route = db.query(FavoriteRoute).filter(
        FavoriteRoute.id == route_id,
        FavoriteRoute.customer_id == customer_id
    ).first()
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    db.delete(route)
    db.commit()
    
    return {"success": True, "message": "Route deleted"}


# ==========================================
# BID TEMPLATES ENDPOINTS
# ==========================================

@app.get("/api/forwarder/bid-templates", response_model=BidTemplateListResponse, tags=["Forwarder"])
def get_bid_templates(
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """입찰 템플릿 목록 조회"""
    templates = db.query(BidTemplate).filter(
        BidTemplate.forwarder_id == forwarder_id
    ).order_by(BidTemplate.created_at.desc()).all()
    
    return BidTemplateListResponse(
        data=[BidTemplateResponse(
            id=t.id,
            forwarder_id=t.forwarder_id,
            name=t.name,
            pol=t.pol,
            pod=t.pod,
            shipping_type=t.shipping_type,
            base_freight=float(t.base_freight) if t.base_freight else None,
            base_local=float(t.base_local) if t.base_local else None,
            base_other=float(t.base_other) if t.base_other else None,
            transit_time=t.transit_time,
            carrier=t.carrier,
            default_remark=t.default_remark,
            created_at=t.created_at,
            updated_at=t.updated_at
        ) for t in templates]
    )


@app.post("/api/forwarder/bid-templates", response_model=BidTemplateResponse, tags=["Forwarder"])
def create_bid_template(
    request: BidTemplateCreate,
    db: Session = Depends(get_db)
):
    """입찰 템플릿 생성"""
    template = BidTemplate(
        forwarder_id=request.forwarder_id,
        name=request.name,
        pol=request.pol,
        pod=request.pod,
        shipping_type=request.shipping_type,
        base_freight=request.base_freight,
        base_local=request.base_local,
        base_other=request.base_other,
        transit_time=request.transit_time,
        carrier=request.carrier,
        default_remark=request.default_remark
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return BidTemplateResponse(
        id=template.id,
        forwarder_id=template.forwarder_id,
        name=template.name,
        pol=template.pol,
        pod=template.pod,
        shipping_type=template.shipping_type,
        base_freight=float(template.base_freight) if template.base_freight else None,
        base_local=float(template.base_local) if template.base_local else None,
        base_other=float(template.base_other) if template.base_other else None,
        transit_time=template.transit_time,
        carrier=template.carrier,
        default_remark=template.default_remark,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@app.delete("/api/forwarder/bid-templates/{template_id}", tags=["Forwarder"])
def delete_bid_template(
    template_id: int,
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """입찰 템플릿 삭제"""
    template = db.query(BidTemplate).filter(
        BidTemplate.id == template_id,
        BidTemplate.forwarder_id == forwarder_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    
    return {"success": True, "message": "Template deleted"}


# ==========================================
# BOOKMARK ENDPOINTS
# ==========================================

@app.get("/api/forwarder/bookmarked", response_model=BookmarkedBiddingListResponse, tags=["Forwarder"])
def get_bookmarked_biddings(
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """북마크된 비딩 목록 조회"""
    bookmarks = db.query(BookmarkedBidding).filter(
        BookmarkedBidding.forwarder_id == forwarder_id
    ).order_by(BookmarkedBidding.created_at.desc()).all()
    
    items = []
    for b in bookmarks:
        bidding = db.query(Bidding).filter(Bidding.id == b.bidding_id).first()
        if bidding:
            quote_req = db.query(QuoteRequest).filter(QuoteRequest.id == bidding.quote_request_id).first()
            items.append(BookmarkedBiddingResponse(
                id=b.id,
                forwarder_id=b.forwarder_id,
                bidding_id=b.bidding_id,
                bidding_no=bidding.bidding_no,
                pol=quote_req.pol if quote_req else "",
                pod=quote_req.pod if quote_req else "",
                shipping_type=quote_req.shipping_type if quote_req else "",
                deadline=bidding.deadline,
                status=bidding.status,
                created_at=b.created_at
            ))
    
    return BookmarkedBiddingListResponse(data=items)


@app.post("/api/forwarder/bookmark/{bidding_id}", tags=["Forwarder"])
def bookmark_bidding(
    bidding_id: int,
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """비딩 북마크"""
    # Check if already bookmarked
    existing = db.query(BookmarkedBidding).filter(
        BookmarkedBidding.forwarder_id == forwarder_id,
        BookmarkedBidding.bidding_id == bidding_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already bookmarked")
    
    bookmark = BookmarkedBidding(
        forwarder_id=forwarder_id,
        bidding_id=bidding_id
    )
    db.add(bookmark)
    db.commit()
    
    return {"success": True, "message": "Bidding bookmarked"}


@app.delete("/api/forwarder/bookmark/{bidding_id}", tags=["Forwarder"])
def remove_bookmark(
    bidding_id: int,
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """북마크 삭제"""
    bookmark = db.query(BookmarkedBidding).filter(
        BookmarkedBidding.forwarder_id == forwarder_id,
        BookmarkedBidding.bidding_id == bidding_id
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    db.delete(bookmark)
    db.commit()
    
    return {"success": True, "message": "Bookmark removed"}


# ==========================================
# QUOTE REQUEST UPDATE ENDPOINTS
# ==========================================

@app.put("/api/quote-request/{request_id}", tags=["Quote Request"])
def update_quote_request(
    request_id: int,
    request: QuoteRequestUpdate,
    customer_id: int,
    db: Session = Depends(get_db)
):
    """운송 요청 수정"""
    quote_req = db.query(QuoteRequest).filter(
        QuoteRequest.id == request_id,
        QuoteRequest.customer_id == customer_id
    ).first()
    
    if not quote_req:
        raise HTTPException(status_code=404, detail="Quote request not found")
    
    # Check if bidding exists and has bids
    bidding = db.query(Bidding).filter(Bidding.quote_request_id == request_id).first()
    if bidding:
        bids = db.query(Bid).filter(Bid.bidding_id == bidding.id, Bid.status == "submitted").count()
        if bids > 0:
            raise HTTPException(status_code=400, detail="Cannot modify request with submitted bids")
    
    # Update fields
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            if key == "etd":
                setattr(quote_req, key, parse_datetime(value))
            else:
                setattr(quote_req, key, value)
    
    db.commit()
    
    return {"success": True, "message": "Quote request updated", "request_number": quote_req.request_number}


@app.delete("/api/quote-request/{request_id}", tags=["Quote Request"])
def cancel_quote_request(
    request_id: int,
    customer_id: int,
    db: Session = Depends(get_db)
):
    """운송 요청 취소"""
    quote_req = db.query(QuoteRequest).filter(
        QuoteRequest.id == request_id,
        QuoteRequest.customer_id == customer_id
    ).first()
    
    if not quote_req:
        raise HTTPException(status_code=404, detail="Quote request not found")
    
    if quote_req.status in ["accepted", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel request with status: {quote_req.status}")
    
    quote_req.status = "cancelled"
    
    # Cancel bidding if exists
    bidding = db.query(Bidding).filter(Bidding.quote_request_id == request_id).first()
    if bidding:
        bidding.status = "cancelled"
    
    db.commit()
    
    return {"success": True, "message": "Quote request cancelled", "request_number": quote_req.request_number}


@app.post("/api/quote-request/{request_id}/copy", tags=["Quote Request"])
def copy_quote_request(
    request_id: int,
    request: QuoteRequestCopyRequest,
    db: Session = Depends(get_db)
):
    """운송 요청 복사 (재요청)"""
    original = db.query(QuoteRequest).filter(QuoteRequest.id == request_id).first()
    
    if not original:
        raise HTTPException(status_code=404, detail="Quote request not found")
    
    # Copy cargo details
    cargo_details = db.query(CargoDetail).filter(CargoDetail.quote_request_id == request_id).all()
    
    # Create new request
    new_etd = parse_datetime(request.new_etd) if request.new_etd else original.etd
    
    new_request = QuoteRequest(
        request_number=generate_request_number(),
        trade_mode=original.trade_mode,
        shipping_type=original.shipping_type,
        load_type=original.load_type,
        incoterms=original.incoterms,
        pol=original.pol,
        pod=original.pod,
        etd=new_etd,
        is_dg=original.is_dg,
        dg_class=original.dg_class,
        dg_un=original.dg_un,
        pickup_required=original.pickup_required,
        pickup_address=original.pickup_address,
        delivery_required=original.delivery_required,
        delivery_address=original.delivery_address,
        remark=original.remark,
        customer_id=request.customer_id,
        status="pending"
    )
    db.add(new_request)
    db.flush()
    
    # Copy cargo details
    for cargo in cargo_details:
        new_cargo = CargoDetail(
            quote_request_id=new_request.id,
            row_index=cargo.row_index,
            container_type=cargo.container_type,
            truck_type=cargo.truck_type,
            length=cargo.length,
            width=cargo.width,
            height=cargo.height,
            qty=cargo.qty,
            gross_weight=cargo.gross_weight,
            cbm=cargo.cbm,
            volume_weight=cargo.volume_weight,
            chargeable_weight=cargo.chargeable_weight
        )
        db.add(new_cargo)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Quote request copied",
        "new_request_number": new_request.request_number,
        "new_request_id": new_request.id
    }


# ==========================================
# BID WITHDRAW/RESUBMIT ENDPOINTS
# ==========================================

@app.delete("/api/bid/{bid_id}", tags=["Bid"])
def withdraw_bid(
    bid_id: int,
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """입찰 철회"""
    bid = db.query(Bid).filter(
        Bid.id == bid_id,
        Bid.forwarder_id == forwarder_id
    ).first()
    
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    if bid.status == "awarded":
        raise HTTPException(status_code=400, detail="Cannot withdraw awarded bid")
    
    bidding = db.query(Bidding).filter(Bidding.id == bid.bidding_id).first()
    if bidding and bidding.status != "open":
        raise HTTPException(status_code=400, detail="Bidding is not open")
    
    bid.status = "draft"
    bid.submitted_at = None
    
    db.commit()
    
    return {"success": True, "message": "Bid withdrawn"}


@app.post("/api/bid/{bid_id}/resubmit", tags=["Bid"])
def resubmit_bid(
    bid_id: int,
    forwarder_id: int,
    db: Session = Depends(get_db)
):
    """입찰 재제출"""
    bid = db.query(Bid).filter(
        Bid.id == bid_id,
        Bid.forwarder_id == forwarder_id
    ).first()
    
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    if bid.status not in ["draft", "rejected"]:
        raise HTTPException(status_code=400, detail=f"Cannot resubmit bid with status: {bid.status}")
    
    bidding = db.query(Bidding).filter(Bidding.id == bid.bidding_id).first()
    if bidding and bidding.status != "open":
        raise HTTPException(status_code=400, detail="Bidding is not open")
    
    bid.status = "submitted"
    bid.submitted_at = datetime.now()
    
    db.commit()
    
    return {"success": True, "message": "Bid resubmitted"}


# ==========================================
# RECOMMENDATION ENDPOINTS
# ==========================================

@app.get("/api/recommend/forwarders", response_model=ForwarderRecommendationResponse, tags=["Recommendation"])
def recommend_forwarders(
    customer_id: int,
    pol: str,
    pod: str,
    shipping_type: Optional[str] = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """포워더 추천 (화주용)"""
    # Find forwarders who have been awarded for similar routes
    query = db.query(
        Forwarder, Bid, Bidding, QuoteRequest
    ).join(
        Bid, Bid.forwarder_id == Forwarder.id
    ).join(
        Bidding, Bid.bidding_id == Bidding.id
    ).join(
        QuoteRequest, Bidding.quote_request_id == QuoteRequest.id
    ).filter(
        QuoteRequest.pol == pol,
        QuoteRequest.pod == pod,
        Bid.status == "awarded"
    )
    
    if shipping_type:
        query = query.filter(QuoteRequest.shipping_type == shipping_type)
    
    results = query.all()
    
    # Aggregate by forwarder
    forwarder_stats = {}
    for forwarder, bid, bidding, quote_req in results:
        if forwarder.id not in forwarder_stats:
            forwarder_stats[forwarder.id] = {
                "forwarder": forwarder,
                "awarded_count": 0,
                "total_price": 0
            }
        forwarder_stats[forwarder.id]["awarded_count"] += 1
        bid_amount = float(bid.total_amount_krw) if bid.total_amount_krw else convert_to_krw(float(bid.total_amount))
        forwarder_stats[forwarder.id]["total_price"] += bid_amount
    
    # Sort by awarded count
    sorted_forwarders = sorted(
        forwarder_stats.values(),
        key=lambda x: (x["awarded_count"], float(x["forwarder"].rating or 3.0)),
        reverse=True
    )[:limit]
    
    recommendations = []
    for stats in sorted_forwarders:
        f = stats["forwarder"]
        avg_price = stats["total_price"] / stats["awarded_count"] if stats["awarded_count"] > 0 else 0
        recommendations.append(RecommendedForwarder(
            forwarder_id=f.id,
            company_masked=mask_company_name(f.company),
            rating=float(f.rating) if f.rating else 3.0,
            rating_count=f.rating_count or 0,
            awarded_count=stats["awarded_count"],
            avg_price_krw=round(avg_price, 0),
            reason=f"해당 구간 {stats['awarded_count']}회 낙찰 경험"
        ))
    
    return ForwarderRecommendationResponse(
        pol=pol,
        pod=pod,
        shipping_type=shipping_type,
        recommendations=recommendations
    )


@app.get("/api/recommend/biddings", response_model=BiddingRecommendationResponse, tags=["Recommendation"])
def recommend_biddings(
    forwarder_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """비딩 추천 (포워더용)"""
    # Find routes where forwarder has been awarded before
    awarded_routes = db.query(QuoteRequest.pol, QuoteRequest.pod, QuoteRequest.shipping_type).join(
        Bidding, Bidding.quote_request_id == QuoteRequest.id
    ).join(
        Bid, Bid.bidding_id == Bidding.id
    ).filter(
        Bid.forwarder_id == forwarder_id,
        Bid.status == "awarded"
    ).distinct().all()
    
    route_set = set((r.pol, r.pod, r.shipping_type) for r in awarded_routes)
    
    # Find open biddings matching these routes
    open_biddings = db.query(Bidding, QuoteRequest).join(
        QuoteRequest, Bidding.quote_request_id == QuoteRequest.id
    ).filter(
        Bidding.status == "open"
    ).all()
    
    recommendations = []
    for bidding, quote_req in open_biddings:
        # Check if forwarder already bid
        existing_bid = db.query(Bid).filter(
            Bid.bidding_id == bidding.id,
            Bid.forwarder_id == forwarder_id
        ).first()
        
        if existing_bid:
            continue
        
        # Calculate recommendation score
        reason = ""
        if (quote_req.pol, quote_req.pod, quote_req.shipping_type) in route_set:
            reason = "과거 낙찰 경험이 있는 구간"
        elif (quote_req.pol, quote_req.pod, None) in route_set or any(
            r[0] == quote_req.pol and r[1] == quote_req.pod for r in route_set
        ):
            reason = "유사 구간 경험"
        else:
            continue  # Skip if no match
        
        # Get bid count
        bid_count = db.query(Bid).filter(
            Bid.bidding_id == bidding.id,
            Bid.status == "submitted"
        ).count()
        
        recommendations.append(RecommendedBidding(
            bidding_id=bidding.id,
            bidding_no=bidding.bidding_no,
            pol=quote_req.pol,
            pod=quote_req.pod,
            shipping_type=quote_req.shipping_type,
            deadline=bidding.deadline,
            avg_bid_price_krw=None,
            bid_count=bid_count,
            reason=reason
        ))
        
        if len(recommendations) >= limit:
            break
    
    return BiddingRecommendationResponse(
        forwarder_id=forwarder_id,
        recommendations=recommendations
    )


@app.get("/api/price-guide/{pol}/{pod}", response_model=PriceGuideResponse, tags=["Recommendation"])
def get_price_guide(
    pol: str,
    pod: str,
    shipping_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """구간별 가격 가이드"""
    query = db.query(Bid).join(
        Bidding, Bid.bidding_id == Bidding.id
    ).join(
        QuoteRequest, Bidding.quote_request_id == QuoteRequest.id
    ).filter(
        QuoteRequest.pol == pol,
        QuoteRequest.pod == pod,
        Bid.status.in_(["submitted", "awarded"])
    )
    
    if shipping_type:
        query = query.filter(QuoteRequest.shipping_type == shipping_type)
    
    bids = query.all()
    
    if not bids:
        return PriceGuideResponse(
            pol=pol,
            pod=pod,
            shipping_type=shipping_type,
            sample_count=0,
            avg_price_krw=0,
            min_price_krw=0,
            max_price_krw=0,
            median_price_krw=0
        )
    
    prices = []
    for bid in bids:
        price = float(bid.total_amount_krw) if bid.total_amount_krw else convert_to_krw(float(bid.total_amount))
        prices.append(price)
    
    prices.sort()
    median_idx = len(prices) // 2
    median = prices[median_idx] if len(prices) % 2 == 1 else (prices[median_idx - 1] + prices[median_idx]) / 2
    
    return PriceGuideResponse(
        pol=pol,
        pod=pod,
        shipping_type=shipping_type,
        sample_count=len(prices),
        avg_price_krw=round(sum(prices) / len(prices), 0),
        min_price_krw=round(min(prices), 0),
        max_price_krw=round(max(prices), 0),
        median_price_krw=round(median, 0)
    )


# ==========================================
# SETTLEMENT DISPUTE APIs
# ==========================================

@app.post("/api/settlement/{settlement_id}/dispute", tags=["Settlement Dispute"])
def file_dispute(
    settlement_id: int,
    customer_id: int,
    reason: str,
    evidence: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """정산 분쟁 제기 (화주)"""
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    if settlement.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Not authorized to dispute this settlement")
    
    if settlement.status not in ["pending", "requested"]:
        raise HTTPException(status_code=400, detail=f"Cannot dispute settlement in '{settlement.status}' status")
    
    # Update settlement to disputed
    settlement.status = "disputed"
    settlement.disputed_at = datetime.now()
    settlement.dispute_reason = reason
    settlement.dispute_evidence = evidence
    
    # Notify forwarder
    notification = Notification(
        recipient_type="forwarder",
        recipient_id=settlement.forwarder_id,
        notification_type="settlement_disputed",
        title="정산 분쟁이 제기되었습니다",
        message=f"정산번호 {settlement.settlement_no}에 분쟁이 제기되었습니다. 7일 내 응답해주세요.",
        related_type="settlement",
        related_id=settlement.id
    )
    db.add(notification)
    
    db.commit()
    db.refresh(settlement)
    
    return {
        "success": True,
        "settlement_no": settlement.settlement_no,
        "status": settlement.status,
        "disputed_at": settlement.disputed_at.isoformat(),
        "message": "분쟁이 정상적으로 제기되었습니다. 포워더에게 알림이 발송되었습니다."
    }


@app.post("/api/settlement/{settlement_id}/respond", tags=["Settlement Dispute"])
def respond_to_dispute(
    settlement_id: int,
    forwarder_id: int,
    response: str,
    proposed_amount: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """분쟁 응답 (포워더)"""
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    if settlement.forwarder_id != forwarder_id:
        raise HTTPException(status_code=403, detail="Not authorized to respond to this dispute")
    
    if settlement.status != "disputed":
        raise HTTPException(status_code=400, detail="Settlement is not in disputed status")
    
    # Record response
    settlement.forwarder_response = response
    settlement.forwarder_response_at = datetime.now()
    
    if proposed_amount is not None:
        settlement.adjusted_amount = proposed_amount
    
    # Notify customer
    notification = Notification(
        recipient_type="customer",
        recipient_id=settlement.customer_id,
        notification_type="dispute_response",
        title="분쟁 응답이 도착했습니다",
        message=f"정산번호 {settlement.settlement_no}의 분쟁에 포워더가 응답했습니다.",
        related_type="settlement",
        related_id=settlement.id
    )
    db.add(notification)
    
    db.commit()
    db.refresh(settlement)
    
    return {
        "success": True,
        "settlement_no": settlement.settlement_no,
        "response": response,
        "proposed_amount": proposed_amount,
        "responded_at": settlement.forwarder_response_at.isoformat(),
        "message": "응답이 정상적으로 등록되었습니다."
    }


@app.post("/api/settlement/{settlement_id}/resolve", tags=["Settlement Dispute"])
def resolve_dispute(
    settlement_id: int,
    resolution_type: str,  # agreement, mediation, cancel
    resolution_note: str,
    final_amount: Optional[float] = None,
    resolved_by: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """분쟁 해결"""
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    if settlement.status != "disputed":
        raise HTTPException(status_code=400, detail="Settlement is not in disputed status")
    
    valid_resolution_types = ["agreement", "mediation", "cancel"]
    if resolution_type not in valid_resolution_types:
        raise HTTPException(status_code=400, detail=f"Invalid resolution type. Must be one of: {valid_resolution_types}")
    
    now = datetime.now()
    
    # Update settlement
    if resolution_type == "cancel":
        settlement.status = "cancelled"
    else:
        settlement.status = "completed"
    
    settlement.resolved_at = now
    settlement.resolution_type = resolution_type
    settlement.resolution_note = resolution_note
    settlement.resolved_by = resolved_by
    
    if final_amount is not None:
        settlement.adjusted_amount = final_amount
        settlement.net_amount = final_amount - float(settlement.service_fee or 0)
    
    # Notify both parties
    resolution_labels = {
        "agreement": "양측 합의",
        "mediation": "관리자 중재",
        "cancel": "취소"
    }
    
    for recipient_type, recipient_id in [
        ("customer", settlement.customer_id),
        ("forwarder", settlement.forwarder_id)
    ]:
        notification = Notification(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            notification_type="dispute_resolved",
            title="분쟁이 해결되었습니다",
            message=f"정산번호 {settlement.settlement_no}의 분쟁이 {resolution_labels[resolution_type]}로 해결되었습니다.",
            related_type="settlement",
            related_id=settlement.id
        )
        db.add(notification)
    
    db.commit()
    db.refresh(settlement)
    
    return {
        "success": True,
        "settlement_no": settlement.settlement_no,
        "status": settlement.status,
        "resolution_type": resolution_type,
        "resolution_note": resolution_note,
        "final_amount": float(settlement.adjusted_amount) if settlement.adjusted_amount else float(settlement.net_amount),
        "resolved_at": settlement.resolved_at.isoformat(),
        "message": "분쟁이 정상적으로 해결되었습니다."
    }


@app.get("/api/settlement/{settlement_id}/dispute-detail", tags=["Settlement Dispute"])
def get_dispute_detail(
    settlement_id: int,
    db: Session = Depends(get_db)
):
    """분쟁 상세 조회"""
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    # Get related contract info
    contract = db.query(Contract).filter(Contract.id == settlement.contract_id).first()
    
    # Get customer and forwarder names
    customer = db.query(Customer).filter(Customer.id == settlement.customer_id).first()
    forwarder = db.query(Forwarder).filter(Forwarder.id == settlement.forwarder_id).first()
    
    response = {
        "settlement_id": settlement.id,
        "settlement_no": settlement.settlement_no,
        "status": settlement.status,
        
        # Parties
        "customer_id": settlement.customer_id,
        "customer_name": customer.company if customer else None,
        "forwarder_id": settlement.forwarder_id,
        "forwarder_name": forwarder.company if forwarder else None,
        
        # Amounts
        "original_amount_krw": float(settlement.total_amount_krw),
        "service_fee": float(settlement.service_fee) if settlement.service_fee else 0,
        "adjusted_amount_krw": float(settlement.adjusted_amount) if settlement.adjusted_amount else None,
        "final_net_amount": float(settlement.net_amount),
        
        # Dispute info
        "disputed_at": settlement.disputed_at.isoformat() if settlement.disputed_at else None,
        "dispute_reason": settlement.dispute_reason,
        "dispute_evidence": settlement.dispute_evidence,
        
        # Response info
        "forwarder_response": settlement.forwarder_response,
        "forwarder_response_at": settlement.forwarder_response_at.isoformat() if settlement.forwarder_response_at else None,
        
        # Resolution info
        "resolved_at": settlement.resolved_at.isoformat() if settlement.resolved_at else None,
        "resolution_type": settlement.resolution_type,
        "resolution_note": settlement.resolution_note,
        "resolved_by": settlement.resolved_by,
        
        # Timestamps
        "created_at": settlement.created_at.isoformat() if settlement.created_at else None,
        "updated_at": settlement.updated_at.isoformat() if settlement.updated_at else None
    }
    
    # Calculate days since dispute
    if settlement.disputed_at and settlement.status == "disputed":
        days_since_dispute = (datetime.now() - settlement.disputed_at).days
        response["days_since_dispute"] = days_since_dispute
        response["auto_resolve_in_days"] = max(0, 7 - days_since_dispute) if not settlement.forwarder_response else None
    
    return response


@app.get("/api/settlements/disputes", tags=["Settlement Dispute"])
def list_disputes(
    status: Optional[str] = None,  # disputed, resolved, all
    customer_id: Optional[int] = None,
    forwarder_id: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """분쟁 목록 조회"""
    query = db.query(Settlement).filter(
        or_(
            Settlement.status == "disputed",
            Settlement.resolution_type.isnot(None)  # Has been resolved from dispute
        )
    )
    
    if status == "disputed":
        query = query.filter(Settlement.status == "disputed")
    elif status == "resolved":
        query = query.filter(Settlement.resolution_type.isnot(None))
    
    if customer_id:
        query = query.filter(Settlement.customer_id == customer_id)
    if forwarder_id:
        query = query.filter(Settlement.forwarder_id == forwarder_id)
    
    total = query.count()
    disputes = query.order_by(Settlement.disputed_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    items = []
    for s in disputes:
        customer = db.query(Customer).filter(Customer.id == s.customer_id).first()
        forwarder = db.query(Forwarder).filter(Forwarder.id == s.forwarder_id).first()
        
        items.append({
            "settlement_id": s.id,
            "settlement_no": s.settlement_no,
            "status": s.status,
            "customer_name": customer.company if customer else None,
            "forwarder_name": forwarder.company if forwarder else None,
            "original_amount_krw": float(s.total_amount_krw),
            "dispute_reason": s.dispute_reason[:100] + "..." if s.dispute_reason and len(s.dispute_reason) > 100 else s.dispute_reason,
            "disputed_at": s.disputed_at.isoformat() if s.disputed_at else None,
            "has_response": s.forwarder_response is not None,
            "resolved_at": s.resolved_at.isoformat() if s.resolved_at else None,
            "resolution_type": s.resolution_type
        })
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "disputes": items
    }


# ==========================================
# SCHEDULER APIs
# ==========================================

@app.post("/api/admin/run-scheduled-tasks", tags=["Admin"])
def run_scheduled_tasks_manually(admin_key: str):
    """스케줄 작업 수동 실행 (관리자용)"""
    # Simple admin key check (in production, use proper auth)
    if admin_key != "admin_secret_key_12345":
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    from scheduler import run_all_scheduled_tasks
    results = run_all_scheduled_tasks()
    
    return {
        "success": True,
        "message": "Scheduled tasks executed",
        "results": results
    }


@app.get("/api/admin/scheduler-status", tags=["Admin"])
def get_scheduler_status(admin_key: str):
    """스케줄러 상태 조회 (관리자용)"""
    if admin_key != "admin_secret_key_12345":
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    return {
        "scheduler": "active",
        "tasks": [
            {"name": "auto_expire_biddings", "schedule": "매 1시간"},
            {"name": "check_delivery_reminders", "schedule": "매일 09:00"},
            {"name": "check_dispute_deadlines", "schedule": "매일 09:00"}
        ],
        "last_run": datetime.now().isoformat(),
        "next_run": (datetime.now() + timedelta(hours=1)).isoformat()
    }


# ==========================================
# DASHBOARD API (Shipper & Forwarder)
# ==========================================

@app.get("/api/dashboard/shipper/volume-trend", tags=["Dashboard"])
def get_shipper_volume_trend(
    customer_email: Optional[str] = None,
    customer_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """화주 물량 추이 (월별 TEU/CBM/KGS)"""
    # Resolve customer_id from email if needed
    if customer_email and not customer_id:
        customer = db.query(Customer).filter(Customer.email == customer_email).first()
        if customer:
            customer_id = customer.id
        else:
            raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_email or customer_id required")
    
    # Parse dates
    try:
        start_date = datetime.strptime(from_date, "%Y-%m-%d") if from_date else datetime.now() - timedelta(days=180)
        end_date = datetime.strptime(to_date, "%Y-%m-%d") if to_date else datetime.now()
    except:
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now()
    
    # Query awarded contracts with cargo details
    from sqlalchemy import func, extract
    
    contracts = db.query(
        extract('year', Contract.confirmed_at).label('year'),
        extract('month', Contract.confirmed_at).label('month'),
        func.sum(CargoDetail.qty).label('total_qty'),
        func.sum(CargoDetail.cbm).label('total_cbm'),
        func.sum(CargoDetail.gross_weight).label('total_kgs')
    ).join(Bid, Contract.bid_id == Bid.id
    ).join(Bidding, Bid.bidding_id == Bidding.id
    ).join(QuoteRequest, Bidding.quote_request_id == QuoteRequest.id
    ).join(CargoDetail, CargoDetail.quote_request_id == QuoteRequest.id
    ).filter(
        QuoteRequest.customer_id == customer_id,
        Contract.confirmed_at >= start_date,
        Contract.confirmed_at <= end_date
    ).group_by(
        extract('year', Contract.confirmed_at),
        extract('month', Contract.confirmed_at)
    ).order_by('year', 'month').all()
    
    # Format response
    data = []
    for row in contracts:
        month_str = f"{int(row.year)}-{int(row.month):02d}"
        data.append({
            "month": month_str,
            "teu": int(row.total_qty or 0),
            "cbm": float(row.total_cbm or 0),
            "kgs": float(row.total_kgs or 0)
        })
    
    # If no data, generate mock for demo
    if not data:
        for i in range(6):
            month = datetime.now() - timedelta(days=30 * (5 - i))
            data.append({
                "month": month.strftime("%Y-%m"),
                "teu": random.randint(20, 80),
                "cbm": random.randint(200, 500),
                "kgs": random.randint(20000, 50000)
            })
    
    return {"success": True, "data": data}


@app.get("/api/dashboard/shipper/top-export", tags=["Dashboard"])
def get_shipper_top_export(
    customer_email: Optional[str] = None,
    customer_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """화주 주요 수출국 TOP N"""
    if customer_email and not customer_id:
        customer = db.query(Customer).filter(Customer.email == customer_email).first()
        if customer:
            customer_id = customer.id
        else:
            raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_email or customer_id required")
    
    from sqlalchemy import func
    
    # Group by POL country (assuming POL contains country info)
    results = db.query(
        QuoteRequest.pol,
        func.count(QuoteRequest.id).label('count')
    ).filter(
        QuoteRequest.customer_id == customer_id,
        QuoteRequest.incoterms.in_(['EXW', 'FCA', 'FAS', 'FOB', 'CFR', 'CIF', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP'])
    ).group_by(QuoteRequest.pol
    ).order_by(func.count(QuoteRequest.id).desc()
    ).limit(limit).all()
    
    data = [{"country": r.pol or "Unknown", "count": r.count, "volume": r.count * 10} for r in results]
    
    # Mock data if empty
    if not data:
        data = [
            {"country": "중국", "count": 15, "volume": 120},
            {"country": "미국", "count": 12, "volume": 95},
            {"country": "일본", "count": 8, "volume": 65},
            {"country": "베트남", "count": 6, "volume": 48},
            {"country": "태국", "count": 4, "volume": 32}
        ]
    
    return {"success": True, "data": data}


@app.get("/api/dashboard/shipper/top-import", tags=["Dashboard"])
def get_shipper_top_import(
    customer_email: Optional[str] = None,
    customer_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """화주 주요 수입국 TOP N"""
    if customer_email and not customer_id:
        customer = db.query(Customer).filter(Customer.email == customer_email).first()
        if customer:
            customer_id = customer.id
        else:
            raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_email or customer_id required")
    
    from sqlalchemy import func
    
    # Group by POD country
    results = db.query(
        QuoteRequest.pod,
        func.count(QuoteRequest.id).label('count')
    ).filter(
        QuoteRequest.customer_id == customer_id
    ).group_by(QuoteRequest.pod
    ).order_by(func.count(QuoteRequest.id).desc()
    ).limit(limit).all()
    
    data = [{"country": r.pod or "Unknown", "count": r.count, "volume": r.count * 10} for r in results]
    
    # Mock data if empty
    if not data:
        data = [
            {"country": "독일", "count": 10, "volume": 85},
            {"country": "미국", "count": 8, "volume": 72},
            {"country": "중국", "count": 7, "volume": 58},
            {"country": "일본", "count": 5, "volume": 42},
            {"country": "프랑스", "count": 3, "volume": 25}
        ]
    
    return {"success": True, "data": data}


@app.get("/api/dashboard/shipper/container-efficiency", tags=["Dashboard"])
def get_shipper_container_efficiency(
    customer_email: Optional[str] = None,
    customer_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """화주 FCL 컨테이너 적재 효율"""
    if customer_email and not customer_id:
        customer = db.query(Customer).filter(Customer.email == customer_email).first()
        if customer:
            customer_id = customer.id
        else:
            raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_email or customer_id required")
    
    # Container max weights (typical values in kg)
    container_max_weight = {
        "20GP": 21800, "20'GP": 21800, "20FT": 21800,
        "40GP": 26500, "40'GP": 26500, "40FT": 26500,
        "40HC": 26500, "40'HC": 26500,
        "20RF": 20000, "20'RF": 20000,
        "40RF": 26000, "40'RF": 26000,
        "45HC": 25500, "45'HC": 25500
    }
    
    from sqlalchemy import func
    
    # Query FCL cargo details
    results = db.query(
        CargoDetail.container_type,
        func.count(CargoDetail.id).label('count'),
        func.avg(CargoDetail.gross_weight).label('avg_weight')
    ).join(QuoteRequest, CargoDetail.quote_request_id == QuoteRequest.id
    ).filter(
        QuoteRequest.customer_id == customer_id,
        QuoteRequest.load_type == 'FCL',
        CargoDetail.container_type.isnot(None)
    ).group_by(CargoDetail.container_type).all()
    
    data = []
    for r in results:
        container_type = r.container_type
        max_weight = container_max_weight.get(container_type, 25000)
        avg_weight = r.avg_weight or 0
        efficiency = min(100, int((avg_weight / max_weight) * 100)) if max_weight > 0 else 0
        
        # Get abbreviation from ContainerType table
        ct = db.query(ContainerType).filter(ContainerType.code == container_type).first()
        display_name = ct.abbreviation if ct and ct.abbreviation else container_type
        
        data.append({
            "container_type": display_name,
            "efficiency": efficiency,
            "count": r.count
        })
    
    # Mock data if empty
    if not data:
        data = [
            {"container_type": "20'GP", "efficiency": 82, "count": 15},
            {"container_type": "40'GP", "efficiency": 75, "count": 12},
            {"container_type": "40'HC", "efficiency": 88, "count": 8},
            {"container_type": "20'RF", "efficiency": 65, "count": 3}
        ]
    
    return {"success": True, "data": data}


@app.get("/api/dashboard/forwarder/route-stats", tags=["Dashboard"])
def get_forwarder_route_stats(
    forwarder_email: Optional[str] = None,
    forwarder_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """포워더 구간별 낙찰 현황 + Sparkline"""
    if forwarder_email and not forwarder_id:
        forwarder = db.query(Forwarder).filter(Forwarder.email == forwarder_email).first()
        if forwarder:
            forwarder_id = forwarder.id
        else:
            raise HTTPException(status_code=404, detail="Forwarder not found")
    
    if not forwarder_id:
        raise HTTPException(status_code=400, detail="forwarder_email or forwarder_id required")
    
    from sqlalchemy import func, case
    
    # Parse dates
    try:
        start_date = datetime.strptime(from_date, "%Y-%m-%d") if from_date else datetime.now() - timedelta(days=180)
        end_date = datetime.strptime(to_date, "%Y-%m-%d") if to_date else datetime.now()
    except:
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now()
    
    # Query route stats
    results = db.query(
        QuoteRequest.pol,
        QuoteRequest.pod,
        func.count(Bid.id).label('total_bids'),
        func.sum(case((Contract.id.isnot(None), 1), else_=0)).label('awards'),
        func.sum(case((Contract.id.isnot(None), Contract.final_price_krw), else_=0)).label('total_revenue')
    ).join(Bidding, Bidding.quote_request_id == QuoteRequest.id
    ).join(Bid, Bid.bidding_id == Bidding.id
    ).outerjoin(Contract, Contract.bid_id == Bid.id
    ).filter(
        Bid.forwarder_id == forwarder_id,
        Bid.created_at >= start_date,
        Bid.created_at <= end_date
    ).group_by(QuoteRequest.pol, QuoteRequest.pod
    ).order_by(func.count(Bid.id).desc()
    ).limit(limit).all()
    
    data = []
    for r in results:
        route = f"{r.pol} → {r.pod}"
        total_bids = r.total_bids or 0
        awards = r.awards or 0
        award_rate = round((awards / total_bids) * 100, 1) if total_bids > 0 else 0
        
        # Generate sparkline data (last 6 months)
        sparkline = []
        for i in range(6):
            month_start = datetime.now() - timedelta(days=30 * (6 - i))
            month_end = datetime.now() - timedelta(days=30 * (5 - i))
            
            month_awards = db.query(func.count(Contract.id)).join(
                Bid, Contract.bid_id == Bid.id
            ).join(Bidding, Bid.bidding_id == Bidding.id
            ).join(QuoteRequest, Bidding.quote_request_id == QuoteRequest.id
            ).filter(
                Bid.forwarder_id == forwarder_id,
                QuoteRequest.pol == r.pol,
                QuoteRequest.pod == r.pod,
                Contract.confirmed_at >= month_start,
                Contract.confirmed_at < month_end
            ).scalar() or 0
            sparkline.append(month_awards)
        
        data.append({
            "route": route,
            "bids": total_bids,
            "awards": awards,
            "award_rate": award_rate,
            "total_revenue_krw": int(r.total_revenue or 0),
            "sparkline": sparkline
        })
    
    # Mock data if empty
    if not data:
        data = [
            {"route": "부산 → LA", "bids": 15, "awards": 8, "award_rate": 53.3, "total_revenue_krw": 120000000, "sparkline": [3, 5, 2, 4, 6, 3]},
            {"route": "부산 → 상하이", "bids": 12, "awards": 5, "award_rate": 41.7, "total_revenue_krw": 45000000, "sparkline": [2, 3, 4, 3, 5, 4]},
            {"route": "인천 → 나리타", "bids": 8, "awards": 4, "award_rate": 50.0, "total_revenue_krw": 32000000, "sparkline": [1, 2, 1, 2, 1, 2]},
            {"route": "부산 → 싱가포르", "bids": 10, "awards": 2, "award_rate": 20.0, "total_revenue_krw": 28000000, "sparkline": [0, 1, 0, 1, 0, 1]},
            {"route": "광양 → 로테르담", "bids": 6, "awards": 3, "award_rate": 50.0, "total_revenue_krw": 54000000, "sparkline": [1, 1, 0, 2, 1, 1]}
        ]
    
    return {"success": True, "data": data}


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":
    import uvicorn
    # reload=False for subprocess compatibility
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)

