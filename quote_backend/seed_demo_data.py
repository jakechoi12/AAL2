"""
Demo Data Seed Script for My Quotations Dashboard
데모 데이터 생성 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from decimal import Decimal
import random
from database import SessionLocal, engine
from models import (
    Customer, QuoteRequest, CargoDetail, Bidding, Forwarder, Bid, Rating, Base
)

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

def seed_demo_data():
    print("[*] Seeding demo data for My Quotations...")
    
    # 1. Create or get demo shipper (customer)
    shipper_email = "cjw096@naver.com"
    shipper = db.query(Customer).filter(Customer.email == shipper_email).first()
    if not shipper:
        shipper = Customer(
            company="AAL테스트화주(주)",
            name="테스트화주",
            email=shipper_email,
            phone="010-1234-5678"
        )
        db.add(shipper)
        db.commit()
        db.refresh(shipper)
        print(f"[+] Created demo shipper: {shipper.company} ({shipper_email})")
    else:
        print(f"[+] Using existing shipper: {shipper.company} ({shipper_email})")
    
    # 2. Create demo forwarders
    forwarders_data = [
        {"company": "삼정해운", "name": "이포워더", "email": "samjung@demo.com", "rating": 4.5, "rating_count": 28},
        {"company": "한진로지스틱스", "name": "박운송", "email": "hanjin@demo.com", "rating": 4.2, "rating_count": 35},
        {"company": "대한통운", "name": "최물류", "email": "daehan@demo.com", "rating": 3.8, "rating_count": 42},
        {"company": "글로벌쉽핑", "name": "정해운", "email": "global@demo.com", "rating": 3.5, "rating_count": 18},
        {"company": "에이스운송", "name": "강배송", "email": "ace@demo.com", "rating": 4.0, "rating_count": 25},
        {"company": "케이로지스", "name": "윤화물", "email": "klogis@demo.com", "rating": 4.7, "rating_count": 15},
        {"company": "오션프레이트", "name": "김해운", "email": "oceanfreight@demo.com", "rating": 4.3, "rating_count": 31},
        {"company": "스카이에어", "name": "조항공", "email": "skyair@demo.com", "rating": 4.6, "rating_count": 22},
    ]
    
    forwarders = []
    for fwd_data in forwarders_data:
        fwd = db.query(Forwarder).filter(Forwarder.email == fwd_data["email"]).first()
        if not fwd:
            fwd = Forwarder(
                company=fwd_data["company"],
                name=fwd_data["name"],
                email=fwd_data["email"],
                phone="02-1234-5678",
                rating=Decimal(str(fwd_data["rating"])),
                rating_count=fwd_data["rating_count"],
                password_hash="$2b$12$demo_hash_for_testing_only",
                is_verified=True
            )
            db.add(fwd)
            db.commit()
            db.refresh(fwd)
            print(f"  Created forwarder: {fwd.company}")
        forwarders.append(fwd)
    print(f"[+] {len(forwarders)} forwarders ready")
    
    # 3. Create demo quote requests and biddings
    routes = [
        {"pol": "KRPUS", "pod": "USLAX", "shipping": "ocean", "load": "FCL"},
        {"pol": "KRPUS", "pod": "NLRTM", "shipping": "ocean", "load": "FCL"},
        {"pol": "CNSHA", "pod": "KRPUS", "shipping": "air", "load": "Air"},
        {"pol": "KRPUS", "pod": "JPYOK", "shipping": "ocean", "load": "LCL"},
        {"pol": "KRPUS", "pod": "DEHAM", "shipping": "ocean", "load": "FCL"},
        {"pol": "VNSGN", "pod": "KRPUS", "shipping": "ocean", "load": "FCL"},
        {"pol": "KRPUS", "pod": "SGSIN", "shipping": "air", "load": "Air"},
        {"pol": "USNYC", "pod": "KRPUS", "shipping": "ocean", "load": "LCL"},
        {"pol": "KRPUS", "pod": "CNNBO", "shipping": "ocean", "load": "FCL"},
        {"pol": "THBKK", "pod": "KRPUS", "shipping": "air", "load": "Air"},
        {"pol": "KRPUS", "pod": "AEJEA", "shipping": "ocean", "load": "FCL"},
        {"pol": "KRPUS", "pod": "AUBNE", "shipping": "ocean", "load": "FCL"},
    ]
    
    statuses = ["open", "open", "open", "open", "open", "awarded", "awarded", "awarded", "awarded", "expired", "expired", "expired"]
    
    now = datetime.now()
    
    # Get current max bidding sequence
    existing_biddings = db.query(Bidding).all()
    existing_bidding_nos = [b.bidding_no for b in existing_biddings]
    
    created_count = 0
    
    for i, (route, status) in enumerate(zip(routes, statuses)):
        # Create quote request
        trade_mode = "import" if route["pod"] == "KRPUS" else "export"
        prefix = "IM" if trade_mode == "import" else "EX"
        shipping_prefix = route["shipping"][:3].upper()
        
        req_number = f"QR-{now.strftime('%Y%m%d')}-D{str(i+1).zfill(3)}"
        
        # Generate unique bidding_no
        seq = i + 100  # Start from 100 to avoid conflicts
        bidding_no = f"{prefix}{shipping_prefix}{str(seq).zfill(5)}"
        while bidding_no in existing_bidding_nos:
            seq += 1
            bidding_no = f"{prefix}{shipping_prefix}{str(seq).zfill(5)}"
        existing_bidding_nos.append(bidding_no)
        
        # Check if exists
        existing = db.query(QuoteRequest).filter(QuoteRequest.request_number == req_number).first()
        if existing:
            print(f"  Skipping existing: {req_number}")
            continue
        
        etd = now + timedelta(days=random.randint(7, 30))
        eta = etd + timedelta(days=random.randint(14, 45) if route["shipping"] == "ocean" else random.randint(3, 7))
        
        quote_req = QuoteRequest(
            request_number=req_number,
            trade_mode=trade_mode,
            shipping_type=route["shipping"],
            load_type=route["load"],
            incoterms="FOB" if trade_mode == "export" else "CIF",
            pol=route["pol"],
            pod=route["pod"],
            etd=etd,
            eta=eta,
            is_dg=False,
            customer_id=shipper.id,
            status="processing"
        )
        db.add(quote_req)
        db.commit()
        db.refresh(quote_req)
        
        # Create cargo detail
        if route["load"] == "FCL":
            cargo = CargoDetail(
                quote_request_id=quote_req.id,
                row_index=0,
                container_type="40HC",
                qty=random.randint(1, 5),
                gross_weight=Decimal(str(random.randint(15000, 25000)))
            )
        elif route["load"] == "Air":
            cargo = CargoDetail(
                quote_request_id=quote_req.id,
                row_index=0,
                length=100,
                width=80,
                height=60,
                qty=random.randint(5, 20),
                gross_weight=Decimal(str(random.randint(500, 2000))),
                chargeable_weight=random.randint(800, 3000)
            )
        else:  # LCL
            cargo = CargoDetail(
                quote_request_id=quote_req.id,
                row_index=0,
                length=120,
                width=100,
                height=100,
                qty=random.randint(3, 10),
                gross_weight=Decimal(str(random.randint(1000, 5000))),
                cbm=Decimal(str(random.randint(5, 20)))
            )
        db.add(cargo)
        
        # Create bidding
        if status == "expired":
            deadline = now - timedelta(days=random.randint(1, 5))
        elif status == "open":
            deadline = now + timedelta(days=random.randint(2, 10))
        else:
            deadline = now - timedelta(days=random.randint(1, 10))
            
        bidding = Bidding(
            bidding_no=bidding_no,
            quote_request_id=quote_req.id,
            deadline=deadline,
            status=status
        )
        db.add(bidding)
        db.commit()
        db.refresh(bidding)
        
        # Create bids for open/awarded biddings
        if status in ["open", "awarded"]:
            num_bids = random.randint(3, 6)
            selected_forwarders = random.sample(forwarders, min(num_bids, len(forwarders)))
            
            base_price = random.randint(2500000, 5000000)  # Base price in KRW
            
            for j, fwd in enumerate(selected_forwarders):
                price_variation = 1 + (random.random() * 0.4 - 0.1)  # -10% to +30%
                total_price = int(base_price * price_variation)
                
                bid_etd = etd + timedelta(days=random.randint(-2, 3))
                bid_eta = eta + timedelta(days=random.randint(-2, 3))
                
                bid = Bid(
                    bidding_id=bidding.id,
                    forwarder_id=fwd.id,
                    total_amount=Decimal(str(total_price)),
                    total_amount_krw=Decimal(str(total_price)),
                    freight_charge=Decimal(str(int(total_price * 0.6))),
                    local_charge=Decimal(str(int(total_price * 0.3))),
                    other_charge=Decimal(str(int(total_price * 0.1))),
                    etd=bid_etd,
                    eta=bid_eta,
                    transit_time=f"{random.randint(14, 35)}일" if route["shipping"] == "ocean" else f"{random.randint(3, 7)}일",
                    carrier="HMM" if route["shipping"] == "ocean" else "Korean Air",
                    status="submitted",
                    submitted_at=now - timedelta(days=random.randint(1, 5))
                )
                db.add(bid)
                db.commit()
                db.refresh(bid)
                
                # Award first bid for awarded status
                if status == "awarded" and j == 0:
                    bidding.awarded_bid_id = bid.id
                    bid.status = "awarded"
                    db.commit()
                    
                    # Create rating
                    rating = Rating(
                        bidding_id=bidding.id,
                        forwarder_id=fwd.id,
                        customer_id=shipper.id,
                        score=Decimal(str(round(random.uniform(3.5, 5.0) * 2) / 2)),
                        price_score=Decimal(str(round(random.uniform(3.0, 5.0) * 2) / 2)),
                        service_score=Decimal(str(round(random.uniform(3.5, 5.0) * 2) / 2)),
                        punctuality_score=Decimal(str(round(random.uniform(3.5, 5.0) * 2) / 2)),
                        communication_score=Decimal(str(round(random.uniform(3.0, 5.0) * 2) / 2)),
                        comment=random.choice([
                            "정확한 스케줄 관리와 친절한 커뮤니케이션 감사합니다",
                            "가격도 합리적이고 운송도 빨랐습니다",
                            "전반적으로 만족스러운 서비스였습니다",
                            "화물 상태도 좋고 신속한 처리 감사합니다",
                            "다음에도 이용하고 싶습니다",
                        ]),
                        is_visible=True
                    )
                    db.add(rating)
                    db.commit()
        
        created_count += 1
        print(f"  Created: {bidding_no} ({route['pol']} → {route['pod']}) [{status}]")
    
    print(f"\n[+] Created {created_count} demo quote requests and biddings")
    print("[DONE] Demo data seeding completed!")
    print("\n" + "="*50)
    print("[INFO] Login Info:")
    print(f"   Email: {shipper_email}")
    print("   (Login as shipper to view My Quotations)")
    print("="*50)

if __name__ == "__main__":
    try:
        seed_demo_data()
    finally:
        db.close()
