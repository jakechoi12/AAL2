"""
B2B Commerce Seed Data
초기 테스트 데이터 생성 스크립트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date, timedelta
import uuid
import bcrypt

from database import SessionLocal, engine
from commerce_models import (
    Company, CompanyCertification, CommerceUser, Category, Product,
    ProductRFQ, ProductRFQItem, ProductQuotation, ProductQuotationItem
)

# Import Base to ensure all models are registered
from commerce_models import Base


def hash_password(password: str) -> str:
    """비밀번호 해시"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def seed_categories(db):
    """카테고리 시드 데이터"""
    categories = [
        # Level 1 - 대분류
        {"id": "cat-001", "code": "ELEC", "name_ko": "전자/전기", "name_en": "Electronics", "level": 1, "path": "/전자/전기", "sort_order": 1},
        {"id": "cat-002", "code": "CHEM", "name_ko": "화학/소재", "name_en": "Chemicals & Materials", "level": 1, "path": "/화학/소재", "sort_order": 2},
        {"id": "cat-003", "code": "MACH", "name_ko": "기계/장비", "name_en": "Machinery & Equipment", "level": 1, "path": "/기계/장비", "sort_order": 3},
        {"id": "cat-004", "code": "AUTO", "name_ko": "자동차/부품", "name_en": "Automotive", "level": 1, "path": "/자동차/부품", "sort_order": 4},
        {"id": "cat-005", "code": "FOOD", "name_ko": "식품/농산물", "name_en": "Food & Agriculture", "level": 1, "path": "/식품/농산물", "sort_order": 5},
        {"id": "cat-006", "code": "TEXT", "name_ko": "섬유/의류", "name_en": "Textiles & Apparel", "level": 1, "path": "/섬유/의류", "sort_order": 6},
        
        # Level 2 - 중분류 (전자/전기)
        {"id": "cat-011", "code": "ELEC-SEMI", "name_ko": "반도체", "name_en": "Semiconductors", "level": 2, "path": "/전자/전기/반도체", "parent_id": "cat-001", "sort_order": 1},
        {"id": "cat-012", "code": "ELEC-DISP", "name_ko": "디스플레이", "name_en": "Display", "level": 2, "path": "/전자/전기/디스플레이", "parent_id": "cat-001", "sort_order": 2},
        {"id": "cat-013", "code": "ELEC-BATT", "name_ko": "배터리", "name_en": "Battery", "level": 2, "path": "/전자/전기/배터리", "parent_id": "cat-001", "sort_order": 3},
        {"id": "cat-014", "code": "ELEC-COMP", "name_ko": "전자부품", "name_en": "Electronic Components", "level": 2, "path": "/전자/전기/전자부품", "parent_id": "cat-001", "sort_order": 4},
        
        # Level 2 - 중분류 (화학/소재)
        {"id": "cat-021", "code": "CHEM-POLY", "name_ko": "플라스틱/폴리머", "name_en": "Plastics & Polymers", "level": 2, "path": "/화학/소재/플라스틱", "parent_id": "cat-002", "sort_order": 1},
        {"id": "cat-022", "code": "CHEM-SPEC", "name_ko": "정밀화학", "name_en": "Specialty Chemicals", "level": 2, "path": "/화학/소재/정밀화학", "parent_id": "cat-002", "sort_order": 2},
        {"id": "cat-023", "code": "CHEM-META", "name_ko": "금속/합금", "name_en": "Metals & Alloys", "level": 2, "path": "/화학/소재/금속", "parent_id": "cat-002", "sort_order": 3},
        
        # Level 2 - 중분류 (자동차/부품)
        {"id": "cat-041", "code": "AUTO-ENG", "name_ko": "엔진/동력계", "name_en": "Engine & Powertrain", "level": 2, "path": "/자동차/부품/엔진", "parent_id": "cat-004", "sort_order": 1},
        {"id": "cat-042", "code": "AUTO-BODY", "name_ko": "차체/외장", "name_en": "Body & Exterior", "level": 2, "path": "/자동차/부품/차체", "parent_id": "cat-004", "sort_order": 2},
        {"id": "cat-043", "code": "AUTO-ELEC", "name_ko": "전장부품", "name_en": "Auto Electronics", "level": 2, "path": "/자동차/부품/전장", "parent_id": "cat-004", "sort_order": 3},
    ]
    
    for cat_data in categories:
        existing = db.query(Category).filter(Category.code == cat_data["code"]).first()
        if not existing:
            category = Category(**cat_data)
            db.add(category)
            print(f"  + Category: {cat_data['name_ko']}")
    
    db.commit()


def seed_companies(db):
    """기업 시드 데이터"""
    companies = [
        {
            "id": "comp-001",
            "company_name": "삼성전자 주식회사",
            "company_name_en": "Samsung Electronics Co., Ltd.",
            "company_type": "seller",
            "business_number": "124-81-00998",
            "country_code": "KR",
            "region": "경기도 수원시",
            "address": "삼성로 129",
            "industry_code": "ELEC",
            "company_size": "large",
            "employee_count": 120000,
            "annual_revenue": 230000000000,
            "export_ratio": 80,
            "founded_year": 1969,
            "website": "https://www.samsung.com",
            "description": "글로벌 전자기업. 반도체, 디스플레이, 스마트폰 등 제조",
            "verification_status": "enterprise",
            "trust_score": 4.8,
            "preferred_incoterms": ["FOB", "CIF"],
            "preferred_payment": ["T/T", "L/C"]
        },
        {
            "id": "comp-002",
            "company_name": "현대자동차 주식회사",
            "company_name_en": "Hyundai Motor Company",
            "company_type": "buyer",
            "business_number": "101-81-00001",
            "country_code": "KR",
            "region": "서울특별시 서초구",
            "address": "헌릉로 12",
            "industry_code": "AUTO",
            "company_size": "large",
            "employee_count": 75000,
            "annual_revenue": 120000000000,
            "export_ratio": 60,
            "founded_year": 1967,
            "website": "https://www.hyundai.com",
            "description": "글로벌 자동차 제조기업",
            "verification_status": "enterprise",
            "trust_score": 4.7,
            "preferred_incoterms": ["DDP", "FOB"],
            "preferred_payment": ["T/T", "L/C"]
        },
        {
            "id": "comp-003",
            "company_name": "글로벌 테크 솔루션즈",
            "company_name_en": "Global Tech Solutions Inc.",
            "company_type": "both",
            "business_number": "US-12345678",
            "country_code": "US",
            "region": "California",
            "address": "123 Tech Street, San Jose, CA 95110",
            "industry_code": "ELEC",
            "company_size": "medium",
            "employee_count": 500,
            "annual_revenue": 50000000,
            "export_ratio": 40,
            "founded_year": 2010,
            "website": "https://www.globaltech.com",
            "description": "Electronic components supplier for automotive and consumer electronics",
            "verification_status": "verified",
            "trust_score": 4.2,
            "preferred_incoterms": ["FOB", "EXW"],
            "preferred_payment": ["T/T"]
        },
        {
            "id": "comp-004",
            "company_name": "상해 화학재료 유한공사",
            "company_name_en": "Shanghai Chemical Materials Co., Ltd.",
            "company_type": "seller",
            "business_number": "CN-91310000",
            "country_code": "CN",
            "region": "上海市 浦东新区",
            "address": "张江高科技园区 科苑路88号",
            "industry_code": "CHEM",
            "company_size": "medium",
            "employee_count": 300,
            "annual_revenue": 30000000,
            "export_ratio": 70,
            "founded_year": 2005,
            "website": "https://www.shchem.cn",
            "description": "精密化学品及高分子材料专业制造商",
            "verification_status": "verified",
            "trust_score": 4.0,
            "preferred_incoterms": ["FOB", "CIF"],
            "preferred_payment": ["T/T", "L/C"]
        },
        {
            "id": "comp-005",
            "company_name": "한국중소기업",
            "company_name_en": "Korea SME Corp.",
            "company_type": "buyer",
            "business_number": "123-45-67890",
            "country_code": "KR",
            "region": "경기도 안산시",
            "address": "공단로 123",
            "industry_code": "MACH",
            "company_size": "small",
            "employee_count": 50,
            "annual_revenue": 5000000,
            "export_ratio": 20,
            "founded_year": 2015,
            "website": "https://www.krsme.co.kr",
            "description": "정밀 기계 부품 제조업체",
            "verification_status": "pending",
            "trust_score": 3.5,
            "preferred_incoterms": ["FOB"],
            "preferred_payment": ["T/T"]
        }
    ]
    
    for comp_data in companies:
        existing = db.query(Company).filter(Company.id == comp_data["id"]).first()
        if not existing:
            company = Company(**comp_data)
            db.add(company)
            print(f"  + Company: {comp_data['company_name']}")
    
    db.commit()


def seed_users(db):
    """사용자 시드 데이터"""
    users = [
        {
            "id": "user-001",
            "company_id": "comp-001",
            "email": "sales@samsung.com",
            "password_hash": hash_password("test1234"),
            "name": "김영업",
            "name_en": "Kim Young-up",
            "phone": "010-1234-5678",
            "department": "해외영업팀",
            "position": "과장",
            "role": "seller",
            "email_verified": True
        },
        {
            "id": "user-002",
            "company_id": "comp-002",
            "email": "procurement@hyundai.com",
            "password_hash": hash_password("test1234"),
            "name": "박구매",
            "name_en": "Park Gu-mae",
            "phone": "010-2345-6789",
            "department": "구매팀",
            "position": "대리",
            "role": "buyer",
            "email_verified": True
        },
        {
            "id": "user-003",
            "company_id": "comp-003",
            "email": "john@globaltech.com",
            "password_hash": hash_password("test1234"),
            "name": "John Smith",
            "name_en": "John Smith",
            "phone": "+1-408-555-0123",
            "department": "Sales",
            "position": "Manager",
            "role": "both",
            "language": "en",
            "timezone": "America/Los_Angeles",
            "email_verified": True
        },
        {
            "id": "user-004",
            "company_id": "comp-004",
            "email": "wang@shchem.cn",
            "password_hash": hash_password("test1234"),
            "name": "王明",
            "name_en": "Wang Ming",
            "phone": "+86-21-5555-1234",
            "department": "国际贸易部",
            "position": "经理",
            "role": "seller",
            "language": "zh",
            "timezone": "Asia/Shanghai",
            "email_verified": True
        },
        {
            "id": "user-005",
            "company_id": "comp-005",
            "email": "lee@krsme.co.kr",
            "password_hash": hash_password("test1234"),
            "name": "이중소",
            "name_en": "Lee Jung-so",
            "phone": "010-3456-7890",
            "department": "경영지원팀",
            "position": "팀장",
            "role": "buyer",
            "email_verified": True
        }
    ]
    
    for user_data in users:
        existing = db.query(CommerceUser).filter(CommerceUser.email == user_data["email"]).first()
        if not existing:
            user = CommerceUser(**user_data)
            db.add(user)
            print(f"  + User: {user_data['email']}")
    
    db.commit()


def seed_products(db):
    """상품 시드 데이터"""
    products = [
        {
            "id": "prod-001",
            "company_id": "comp-001",
            "category_id": "cat-011",
            "sku": "SAM-DDR5-16G",
            "name_ko": "DDR5 DRAM 16GB 모듈",
            "name_en": "DDR5 DRAM 16GB Module",
            "description": "최신 DDR5 규격의 고성능 메모리 모듈. 서버 및 고성능 PC용.",
            "specifications": {
                "capacity": "16GB",
                "speed": "4800MT/s",
                "voltage": "1.1V",
                "form_factor": "DIMM"
            },
            "price_type": "range",
            "price_min": 80,
            "price_max": 120,
            "price_currency": "USD",
            "price_unit": "per piece",
            "moq": 1000,
            "moq_unit": "pcs",
            "lead_time_min": 14,
            "lead_time_max": 21,
            "stock_status": "in_stock",
            "origin_country": "KR",
            "hs_code": "8542.32",
            "certifications": ["ISO9001", "ISO14001", "IATF16949"],
            "images": [{"url": "/images/ddr5-module.jpg", "is_primary": True}],
            "is_featured": True
        },
        {
            "id": "prod-002",
            "company_id": "comp-001",
            "category_id": "cat-012",
            "sku": "SAM-OLED-65",
            "name_ko": "65인치 OLED 패널",
            "name_en": "65-inch OLED Panel",
            "description": "TV용 65인치 OLED 디스플레이 패널. 4K UHD 해상도.",
            "specifications": {
                "size": "65 inch",
                "resolution": "3840x2160",
                "technology": "OLED",
                "brightness": "800 nits"
            },
            "price_type": "private",
            "price_currency": "USD",
            "price_unit": "per panel",
            "moq": 100,
            "moq_unit": "panels",
            "lead_time_min": 30,
            "lead_time_max": 45,
            "stock_status": "made_to_order",
            "origin_country": "KR",
            "hs_code": "8529.90",
            "certifications": ["ISO9001", "CE", "FCC"],
            "is_featured": True
        },
        {
            "id": "prod-003",
            "company_id": "comp-003",
            "category_id": "cat-014",
            "sku": "GTS-CAP-1000",
            "name_ko": "알루미늄 전해 커패시터",
            "name_en": "Aluminum Electrolytic Capacitor",
            "description": "자동차 전장용 고온 내성 알루미늄 전해 커패시터",
            "specifications": {
                "capacitance": "1000μF",
                "voltage": "50V",
                "temperature": "-40°C ~ +125°C",
                "lifetime": "10,000 hours"
            },
            "price_type": "public",
            "price": 0.85,
            "price_currency": "USD",
            "price_unit": "per piece",
            "moq": 5000,
            "moq_unit": "pcs",
            "lead_time_min": 7,
            "lead_time_max": 14,
            "stock_status": "in_stock",
            "origin_country": "US",
            "hs_code": "8532.22",
            "certifications": ["AEC-Q200", "ISO9001"],
            "is_featured": False
        },
        {
            "id": "prod-004",
            "company_id": "comp-004",
            "category_id": "cat-021",
            "sku": "SHC-PA66-GF30",
            "name_ko": "PA66 유리섬유 강화 플라스틱",
            "name_en": "PA66 Glass Fiber Reinforced Plastic",
            "description": "30% 유리섬유 강화 폴리아미드66. 자동차 엔진룸 부품용.",
            "specifications": {
                "base_resin": "PA66",
                "glass_fiber": "30%",
                "tensile_strength": "180 MPa",
                "heat_deflection": "250°C"
            },
            "price_type": "public",
            "price": 3.50,
            "price_currency": "USD",
            "price_unit": "per kg",
            "moq": 1000,
            "moq_unit": "kg",
            "lead_time_min": 14,
            "lead_time_max": 21,
            "stock_status": "in_stock",
            "origin_country": "CN",
            "hs_code": "3908.10",
            "certifications": ["ISO9001", "REACH", "RoHS"],
            "is_featured": False
        },
        {
            "id": "prod-005",
            "company_id": "comp-004",
            "category_id": "cat-022",
            "sku": "SHC-COAT-UV",
            "name_ko": "UV 경화 코팅제",
            "name_en": "UV Curable Coating",
            "description": "디스플레이 및 광학필름용 고경도 UV 경화 코팅제",
            "specifications": {
                "viscosity": "50-100 cps",
                "hardness": "4H",
                "transmittance": ">92%",
                "curing_time": "3 seconds"
            },
            "price_type": "range",
            "price_min": 15,
            "price_max": 25,
            "price_currency": "USD",
            "price_unit": "per kg",
            "moq": 200,
            "moq_unit": "kg",
            "lead_time_min": 21,
            "lead_time_max": 28,
            "stock_status": "limited",
            "origin_country": "CN",
            "hs_code": "3208.20",
            "certifications": ["ISO9001", "REACH"],
            "is_featured": True
        }
    ]
    
    for prod_data in products:
        existing = db.query(Product).filter(Product.id == prod_data["id"]).first()
        if not existing:
            product = Product(**prod_data)
            db.add(product)
            print(f"  + Product: {prod_data['name_ko']}")
    
    db.commit()


def seed_rfqs(db):
    """RFQ 시드 데이터"""
    rfqs = [
        {
            "id": "rfq-001",
            "company_id": "comp-002",
            "user_id": "user-002",
            "category_id": "cat-011",
            "rfq_number": "RFQ-20260115-A001",
            "rfq_type": "buy",
            "title": "전기차 BMS용 메모리 반도체 구매",
            "description": "2026년 신규 전기차 모델 BMS 시스템에 적용할 고신뢰성 메모리 반도체를 구매하고자 합니다.\n\n요구사항:\n- 자동차용 신뢰성 인증 필수 (AEC-Q100 등)\n- -40°C ~ +125°C 동작 온도 범위\n- 샘플 테스트 후 양산 진행",
            "visibility": "public",
            "status": "open",
            "target_countries": ["KR", "US", "JP"],
            "incoterms": "DDP",
            "destination_port": "KRPUS",
            "delivery_date": (datetime.now() + timedelta(days=90)).date(),
            "payment_terms": "T/T 30% / 70%",
            "required_certs": ["AEC-Q100", "ISO9001"],
            "deadline": datetime.now() + timedelta(days=14),
            "published_at": datetime.now() - timedelta(days=2)
        },
        {
            "id": "rfq-002",
            "company_id": "comp-005",
            "user_id": "user-005",
            "category_id": "cat-021",
            "rfq_number": "RFQ-20260116-B002",
            "rfq_type": "buy",
            "title": "엔지니어링 플라스틱 소재 견적 요청",
            "description": "사출 성형용 엔지니어링 플라스틱 소재를 구매합니다.\nPA66 GF30 또는 동급 소재로 견적 부탁드립니다.",
            "visibility": "public",
            "status": "open",
            "target_countries": ["CN", "KR", "DE"],
            "incoterms": "FOB",
            "destination_port": "KRPUS",
            "delivery_date": (datetime.now() + timedelta(days=45)).date(),
            "payment_terms": "T/T 100%",
            "deadline": datetime.now() + timedelta(days=7),
            "published_at": datetime.now() - timedelta(days=1)
        },
        {
            "id": "rfq-003",
            "company_id": "comp-001",
            "user_id": "user-001",
            "category_id": "cat-013",
            "rfq_number": "RFQ-20260117-S001",
            "rfq_type": "sell",
            "title": "[판매] 차세대 배터리 셀 공급 가능",
            "description": "삼성SDI 차세대 리튬이온 배터리 셀 공급 가능합니다.\n\n- 용량: 5000mAh 이상\n- 에너지 밀도: 300Wh/kg 이상\n- 사이클 수명: 1000회 이상\n\n대량 구매 시 가격 협의 가능",
            "visibility": "public",
            "status": "open",
            "target_countries": ["US", "DE", "FR", "JP"],
            "incoterms": "FOB",
            "origin_port": "KRPUS",
            "delivery_date": (datetime.now() + timedelta(days=60)).date(),
            "payment_terms": "L/C at sight",
            "deadline": datetime.now() + timedelta(days=30),
            "published_at": datetime.now()
        }
    ]
    
    for rfq_data in rfqs:
        existing = db.query(ProductRFQ).filter(ProductRFQ.id == rfq_data["id"]).first()
        if not existing:
            rfq = ProductRFQ(**rfq_data)
            db.add(rfq)
            print(f"  + RFQ: {rfq_data['title'][:30]}...")
    
    db.commit()
    
    # RFQ Items
    rfq_items = [
        # RFQ-001 Items
        {
            "id": "item-001-1",
            "rfq_id": "rfq-001",
            "item_number": 1,
            "name": "Automotive Grade DDR4 SDRAM",
            "specifications": {"capacity": "8GB", "speed": "3200MT/s", "package": "FBGA"},
            "quantity": 50000,
            "unit": "pcs",
            "target_price": 12.00,
            "target_currency": "USD",
            "notes": "AEC-Q100 Grade 2 필수"
        },
        {
            "id": "item-001-2",
            "rfq_id": "rfq-001",
            "item_number": 2,
            "name": "Automotive Grade eMMC",
            "specifications": {"capacity": "64GB", "interface": "eMMC 5.1"},
            "quantity": 30000,
            "unit": "pcs",
            "target_price": 8.00,
            "target_currency": "USD",
            "notes": "AEC-Q100 Grade 2 필수"
        },
        # RFQ-002 Items
        {
            "id": "item-002-1",
            "rfq_id": "rfq-002",
            "item_number": 1,
            "name": "PA66 GF30 Black",
            "specifications": {"color": "Black", "glass_fiber": "30%"},
            "quantity": 5000,
            "unit": "kg",
            "target_price": 3.50,
            "target_currency": "USD"
        },
        {
            "id": "item-002-2",
            "rfq_id": "rfq-002",
            "item_number": 2,
            "name": "PA66 GF30 Natural",
            "specifications": {"color": "Natural", "glass_fiber": "30%"},
            "quantity": 3000,
            "unit": "kg",
            "target_price": 3.30,
            "target_currency": "USD"
        },
        # RFQ-003 Items (Sell RFQ)
        {
            "id": "item-003-1",
            "rfq_id": "rfq-003",
            "item_number": 1,
            "name": "NCM 811 Battery Cell",
            "specifications": {"capacity": "5000mAh", "nominal_voltage": "3.7V", "energy_density": "300Wh/kg"},
            "quantity": 100000,
            "unit": "cells",
            "target_price": 15.00,
            "target_currency": "USD",
            "notes": "MOQ 10,000 cells"
        }
    ]
    
    for item_data in rfq_items:
        existing = db.query(ProductRFQItem).filter(ProductRFQItem.id == item_data["id"]).first()
        if not existing:
            item = ProductRFQItem(**item_data)
            db.add(item)
            print(f"    + RFQ Item: {item_data['name'][:25]}...")
    
    db.commit()


def seed_quotations(db):
    """견적 시드 데이터"""
    quotations = [
        {
            "id": "quot-001",
            "rfq_id": "rfq-001",
            "company_id": "comp-001",
            "user_id": "user-001",
            "quotation_number": "QT-20260117-0001",
            "status": "submitted",
            "total_amount": 740000.00,
            "currency": "USD",
            "incoterms": "DDP",
            "payment_terms": "T/T 30% / 70%",
            "delivery_date": (datetime.now() + timedelta(days=75)).date(),
            "lead_time": 75,
            "validity_days": 30,
            "valid_until": (datetime.now() + timedelta(days=30)).date(),
            "notes": "AEC-Q100 Grade 2 인증 완료 제품입니다. 대량 구매 시 추가 할인 가능합니다.",
            "submitted_at": datetime.now() - timedelta(hours=12)
        },
        {
            "id": "quot-002",
            "rfq_id": "rfq-001",
            "company_id": "comp-003",
            "user_id": "user-003",
            "quotation_number": "QT-20260117-0002",
            "status": "submitted",
            "total_amount": 695000.00,
            "currency": "USD",
            "incoterms": "DDP",
            "payment_terms": "T/T 50% / 50%",
            "delivery_date": (datetime.now() + timedelta(days=85)).date(),
            "lead_time": 85,
            "validity_days": 21,
            "valid_until": (datetime.now() + timedelta(days=21)).date(),
            "notes": "Competitive pricing with equivalent automotive-grade products.",
            "submitted_at": datetime.now() - timedelta(hours=6)
        },
        {
            "id": "quot-003",
            "rfq_id": "rfq-002",
            "company_id": "comp-004",
            "user_id": "user-004",
            "quotation_number": "QT-20260118-0001",
            "status": "submitted",
            "total_amount": 27400.00,
            "currency": "USD",
            "incoterms": "FOB",
            "payment_terms": "T/T 100%",
            "delivery_date": (datetime.now() + timedelta(days=35)).date(),
            "lead_time": 35,
            "validity_days": 14,
            "valid_until": (datetime.now() + timedelta(days=14)).date(),
            "notes": "FOB Shanghai. 高品质PA66 GF30材料,满足汽车行业标准.",
            "submitted_at": datetime.now() - timedelta(hours=3)
        }
    ]
    
    for quot_data in quotations:
        existing = db.query(ProductQuotation).filter(ProductQuotation.id == quot_data["id"]).first()
        if not existing:
            quotation = ProductQuotation(**quot_data)
            db.add(quotation)
            print(f"  + Quotation: {quot_data['quotation_number']}")
    
    db.commit()
    
    # Quotation Items
    quot_items = [
        # Quotation 1 Items
        {
            "id": "qi-001-1",
            "quotation_id": "quot-001",
            "rfq_item_id": "item-001-1",
            "item_number": 1,
            "name": "Samsung Automotive DDR4 8GB",
            "specifications": {"capacity": "8GB", "speed": "3200MT/s", "grade": "AEC-Q100 Grade 2"},
            "quantity": 50000,
            "unit": "pcs",
            "unit_price": 11.00,
            "amount": 550000.00,
            "moq": 10000,
            "lead_time": 60
        },
        {
            "id": "qi-001-2",
            "quotation_id": "quot-001",
            "rfq_item_id": "item-001-2",
            "item_number": 2,
            "name": "Samsung Automotive eMMC 64GB",
            "specifications": {"capacity": "64GB", "interface": "eMMC 5.1", "grade": "AEC-Q100 Grade 2"},
            "quantity": 30000,
            "unit": "pcs",
            "unit_price": 6.33,
            "amount": 190000.00,
            "moq": 5000,
            "lead_time": 75
        },
        # Quotation 2 Items
        {
            "id": "qi-002-1",
            "quotation_id": "quot-002",
            "rfq_item_id": "item-001-1",
            "item_number": 1,
            "name": "GTS Automotive DDR4 8GB",
            "specifications": {"capacity": "8GB", "speed": "3200MT/s", "grade": "AEC-Q100 Grade 2"},
            "quantity": 50000,
            "unit": "pcs",
            "unit_price": 10.50,
            "amount": 525000.00,
            "moq": 20000,
            "lead_time": 70
        },
        {
            "id": "qi-002-2",
            "quotation_id": "quot-002",
            "rfq_item_id": "item-001-2",
            "item_number": 2,
            "name": "GTS Automotive eMMC 64GB",
            "specifications": {"capacity": "64GB", "interface": "eMMC 5.1", "grade": "AEC-Q100 Grade 2"},
            "quantity": 30000,
            "unit": "pcs",
            "unit_price": 5.67,
            "amount": 170000.00,
            "moq": 10000,
            "lead_time": 85
        },
        # Quotation 3 Items
        {
            "id": "qi-003-1",
            "quotation_id": "quot-003",
            "rfq_item_id": "item-002-1",
            "item_number": 1,
            "name": "Shanghai PA66 GF30 Black",
            "specifications": {"color": "Black", "glass_fiber": "30%", "standard": "ISO 9001"},
            "quantity": 5000,
            "unit": "kg",
            "unit_price": 3.40,
            "amount": 17000.00,
            "moq": 1000,
            "lead_time": 21
        },
        {
            "id": "qi-003-2",
            "quotation_id": "quot-003",
            "rfq_item_id": "item-002-2",
            "item_number": 2,
            "name": "Shanghai PA66 GF30 Natural",
            "specifications": {"color": "Natural", "glass_fiber": "30%", "standard": "ISO 9001"},
            "quantity": 3000,
            "unit": "kg",
            "unit_price": 3.20,
            "amount": 9600.00,
            "moq": 500,
            "lead_time": 14
        }
    ]
    
    for qi_data in quot_items:
        existing = db.query(ProductQuotationItem).filter(ProductQuotationItem.id == qi_data["id"]).first()
        if not existing:
            qi = ProductQuotationItem(**qi_data)
            db.add(qi)
            print(f"    + Quotation Item: {qi_data['name'][:25]}...")
    
    db.commit()


def run_seed():
    """시드 데이터 실행"""
    print("\n" + "=" * 60)
    print("  B2B Commerce Seed Data")
    print("=" * 60)
    
    # Create tables
    print("\n[1/7] Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("  [OK] Tables created")
    
    db = SessionLocal()
    
    try:
        print("\n[2/7] Seeding Categories...")
        seed_categories(db)
        
        print("\n[3/7] Seeding Companies...")
        seed_companies(db)
        
        print("\n[4/7] Seeding Users...")
        seed_users(db)
        
        print("\n[5/7] Seeding Products...")
        seed_products(db)
        
        print("\n[6/7] Seeding RFQs...")
        seed_rfqs(db)
        
        print("\n[7/7] Seeding Quotations...")
        seed_quotations(db)
        
        # Update RFQ quotation counts
        rfq1 = db.query(ProductRFQ).filter(ProductRFQ.id == "rfq-001").first()
        if rfq1:
            rfq1.quotation_count = 2
        rfq2 = db.query(ProductRFQ).filter(ProductRFQ.id == "rfq-002").first()
        if rfq2:
            rfq2.quotation_count = 1
        db.commit()
        
        print("\n" + "=" * 60)
        print("  [OK] Seed data completed successfully!")
        print("=" * 60)
        
        # Summary
        print("\nSummary:")
        print(f"  - Categories: {db.query(Category).count()}")
        print(f"  - Companies: {db.query(Company).count()}")
        print(f"  - Users: {db.query(CommerceUser).count()}")
        print(f"  - Products: {db.query(Product).count()}")
        print(f"  - RFQs: {db.query(ProductRFQ).count()}")
        print(f"  - Quotations: {db.query(ProductQuotation).count()}")
        print()
        
    except Exception as e:
        print(f"\n[ERROR] Seed failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()

