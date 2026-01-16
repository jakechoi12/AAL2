"""
Seed Data - Initial Reference Data for Quote Request System
Run this after database initialization to populate master tables
"""

from database import SessionLocal, engine, init_db
from models import Port, ContainerType, TruckType, Incoterm, Base


def seed_ports(db):
    """Seed Ports (POL/POD) data"""
    ports = [
        # South Korea - Ocean Ports
        {"code": "KRPUS", "name": "Busan Port", "name_ko": "부산항", "country": "South Korea", "country_code": "KR", "port_type": "ocean"},
        {"code": "KRINC", "name": "Incheon Port", "name_ko": "인천항", "country": "South Korea", "country_code": "KR", "port_type": "ocean"},
        {"code": "KRKAN", "name": "Gwangyang Port", "name_ko": "광양항", "country": "South Korea", "country_code": "KR", "port_type": "ocean"},
        {"code": "KRPTK", "name": "Pyeongtaek Port", "name_ko": "평택항", "country": "South Korea", "country_code": "KR", "port_type": "ocean"},
        {"code": "KRULS", "name": "Ulsan Port", "name_ko": "울산항", "country": "South Korea", "country_code": "KR", "port_type": "ocean"},
        
        # South Korea - Airports
        {"code": "KRICN", "name": "Incheon International Airport", "name_ko": "인천국제공항", "country": "South Korea", "country_code": "KR", "port_type": "air"},
        {"code": "KRGMP", "name": "Gimpo International Airport", "name_ko": "김포국제공항", "country": "South Korea", "country_code": "KR", "port_type": "air"},
        
        # China - Ocean Ports
        {"code": "CNSHA", "name": "Shanghai Port", "name_ko": "상하이항", "country": "China", "country_code": "CN", "port_type": "ocean"},
        {"code": "CNNGB", "name": "Ningbo Port", "name_ko": "닝보항", "country": "China", "country_code": "CN", "port_type": "ocean"},
        {"code": "CNSZX", "name": "Shenzhen Port", "name_ko": "선전항", "country": "China", "country_code": "CN", "port_type": "ocean"},
        {"code": "CNQIN", "name": "Qingdao Port", "name_ko": "청도항", "country": "China", "country_code": "CN", "port_type": "ocean"},
        {"code": "CNTAO", "name": "Tianjin Port", "name_ko": "천진항", "country": "China", "country_code": "CN", "port_type": "ocean"},
        {"code": "CNDLC", "name": "Dalian Port", "name_ko": "대련항", "country": "China", "country_code": "CN", "port_type": "ocean"},
        
        # China - Airports
        {"code": "CNPVG", "name": "Shanghai Pudong International Airport", "name_ko": "상하이 푸동 국제공항", "country": "China", "country_code": "CN", "port_type": "air"},
        {"code": "CNPEK", "name": "Beijing Capital International Airport", "name_ko": "베이징 수도 국제공항", "country": "China", "country_code": "CN", "port_type": "air"},
        
        # Japan - Ocean Ports
        {"code": "JPTYO", "name": "Tokyo Port", "name_ko": "도쿄항", "country": "Japan", "country_code": "JP", "port_type": "ocean"},
        {"code": "JPYOK", "name": "Yokohama Port", "name_ko": "요코하마항", "country": "Japan", "country_code": "JP", "port_type": "ocean"},
        {"code": "JPOSA", "name": "Osaka Port", "name_ko": "오사카항", "country": "Japan", "country_code": "JP", "port_type": "ocean"},
        {"code": "JPKOB", "name": "Kobe Port", "name_ko": "고베항", "country": "Japan", "country_code": "JP", "port_type": "ocean"},
        {"code": "JPNGO", "name": "Nagoya Port", "name_ko": "나고야항", "country": "Japan", "country_code": "JP", "port_type": "ocean"},
        
        # Japan - Airports
        {"code": "JPNRT", "name": "Narita International Airport", "name_ko": "나리타 국제공항", "country": "Japan", "country_code": "JP", "port_type": "air"},
        {"code": "JPHND", "name": "Haneda Airport", "name_ko": "하네다 공항", "country": "Japan", "country_code": "JP", "port_type": "air"},
        {"code": "JPKIX", "name": "Kansai International Airport", "name_ko": "간사이 국제공항", "country": "Japan", "country_code": "JP", "port_type": "air"},
        
        # USA - Ocean Ports
        {"code": "USLAX", "name": "Los Angeles Port", "name_ko": "로스앤젤레스항", "country": "United States", "country_code": "US", "port_type": "ocean"},
        {"code": "USLGB", "name": "Long Beach Port", "name_ko": "롱비치항", "country": "United States", "country_code": "US", "port_type": "ocean"},
        {"code": "USNYC", "name": "New York Port", "name_ko": "뉴욕항", "country": "United States", "country_code": "US", "port_type": "ocean"},
        {"code": "USSEA", "name": "Seattle Port", "name_ko": "시애틀항", "country": "United States", "country_code": "US", "port_type": "ocean"},
        {"code": "USOAK", "name": "Oakland Port", "name_ko": "오클랜드항", "country": "United States", "country_code": "US", "port_type": "ocean"},
        {"code": "USSAV", "name": "Savannah Port", "name_ko": "사바나항", "country": "United States", "country_code": "US", "port_type": "ocean"},
        
        # USA - Airports
        {"code": "USJFK", "name": "John F. Kennedy International Airport", "name_ko": "JFK 국제공항", "country": "United States", "country_code": "US", "port_type": "air"},
        {"code": "USLGB_AIR", "name": "Los Angeles International Airport", "name_ko": "LA 국제공항", "country": "United States", "country_code": "US", "port_type": "air"},
        {"code": "USORD", "name": "O'Hare International Airport", "name_ko": "오헤어 국제공항", "country": "United States", "country_code": "US", "port_type": "air"},
        
        # Europe - Ocean Ports
        {"code": "NLRTM", "name": "Rotterdam Port", "name_ko": "로테르담항", "country": "Netherlands", "country_code": "NL", "port_type": "ocean"},
        {"code": "DEHAM", "name": "Hamburg Port", "name_ko": "함부르크항", "country": "Germany", "country_code": "DE", "port_type": "ocean"},
        {"code": "BEANR", "name": "Antwerp Port", "name_ko": "앤트워프항", "country": "Belgium", "country_code": "BE", "port_type": "ocean"},
        {"code": "GBFXT", "name": "Felixstowe Port", "name_ko": "펠릭스토우항", "country": "United Kingdom", "country_code": "GB", "port_type": "ocean"},
        
        # Europe - Airports
        {"code": "DEFRA", "name": "Frankfurt Airport", "name_ko": "프랑크푸르트 공항", "country": "Germany", "country_code": "DE", "port_type": "air"},
        {"code": "NLAMS", "name": "Amsterdam Schiphol Airport", "name_ko": "암스테르담 스키폴 공항", "country": "Netherlands", "country_code": "NL", "port_type": "air"},
        {"code": "GBLHR", "name": "London Heathrow Airport", "name_ko": "런던 히드로 공항", "country": "United Kingdom", "country_code": "GB", "port_type": "air"},
        
        # Southeast Asia
        {"code": "SGSIN", "name": "Singapore Port", "name_ko": "싱가포르항", "country": "Singapore", "country_code": "SG", "port_type": "both"},
        {"code": "VNSGN", "name": "Ho Chi Minh Port", "name_ko": "호치민항", "country": "Vietnam", "country_code": "VN", "port_type": "ocean"},
        {"code": "VNHPH", "name": "Hai Phong Port", "name_ko": "하이퐁항", "country": "Vietnam", "country_code": "VN", "port_type": "ocean"},
        {"code": "THBKK", "name": "Bangkok Port", "name_ko": "방콕항", "country": "Thailand", "country_code": "TH", "port_type": "ocean"},
        {"code": "MYPKG", "name": "Port Klang", "name_ko": "포트클랑", "country": "Malaysia", "country_code": "MY", "port_type": "ocean"},
    ]
    
    for port_data in ports:
        existing = db.query(Port).filter(Port.code == port_data["code"]).first()
        if not existing:
            db.add(Port(**port_data))
    
    db.commit()
    print(f"[OK] Seeded {len(ports)} ports")


def seed_container_types(db):
    """Seed Container Types data with extended specifications"""
    container_types = [
        # 20ft Containers
        {
            "code": "20FR", "name": "20 Flat Rack Container", "abbreviation": "20'FR",
            "description": "20ft Flat Rack Container",
            "size": "20", "category": "FR", "size_teu": 1.0,
            "iso_standard": "22P1", "customs_port_standard": "22PC",
            "china_send_standard": "22PF", "china_receive": "22PF",
            "tare_weight": 2800.00, "max_weight_kg": 31200, "max_cbm": 38.27,
            "length_mm": 6058, "width_mm": 2438, "height_mm": 2591,
            "cbm_limit": False, "sort_order": 1
        },
        {
            "code": "20DC", "name": "20 Dry Container", "abbreviation": "20'DC",
            "description": "20ft Standard Dry Container",
            "size": "20", "category": "DC", "size_teu": 1.0,
            "iso_standard": "22G0", "customs_port_standard": "22GP",
            "china_send_standard": "GP20", "china_receive": "22GP",
            "tare_weight": 2200.00, "max_weight_kg": 28280, "max_cbm": 33.20,
            "length_mm": 5898, "width_mm": 2352, "height_mm": 2393,
            "cbm_limit": True, "sort_order": 2
        },
        {
            "code": "20OT", "name": "20 Open Top Container", "abbreviation": "20'OT",
            "description": "20ft Open Top Container",
            "size": "20", "category": "OT", "size_teu": 1.0,
            "iso_standard": "22U0", "customs_port_standard": "22UT",
            "china_send_standard": "OT20", "china_receive": "22UT",
            "tare_weight": 2100.00, "max_weight_kg": 28380, "max_cbm": 32.57,
            "length_mm": 5898, "width_mm": 2352, "height_mm": 2348,
            "cbm_limit": False, "sort_order": 3
        },
        {
            "code": "20RF", "name": "20 Reefer Container", "abbreviation": "20'RF",
            "description": "20ft Refrigerated Container",
            "size": "20", "category": "RF", "size_teu": 1.0,
            "iso_standard": "22R0", "customs_port_standard": "22RE",
            "china_send_standard": "RF20", "china_receive": "22RT",
            "tare_weight": 2910.00, "max_weight_kg": 27570, "max_cbm": 28.45,
            "length_mm": 5456, "width_mm": 2294, "height_mm": 2273,
            "cbm_limit": True, "sort_order": 4
        },
        {
            "code": "20TK", "name": "20 Tank Container", "abbreviation": "20'TK",
            "description": "20ft Tank Container",
            "size": "20", "category": "TK", "size_teu": 1.0,
            "iso_standard": "22K0", "customs_port_standard": "22TN",
            "china_send_standard": "22TN", "china_receive": "22TN",
            "tare_weight": 4190.00, "max_weight_kg": 31810, "max_cbm": 38.27,
            "length_mm": 6058, "width_mm": 2438, "height_mm": 2591,
            "cbm_limit": False, "sort_order": 5
        },
        # 40ft Containers
        {
            "code": "40FR", "name": "40 Flat Rack Container", "abbreviation": "40'FR",
            "description": "40ft Flat Rack Container",
            "size": "40", "category": "FR", "size_teu": 2.0,
            "iso_standard": "42P1", "customs_port_standard": "42PC",
            "china_send_standard": "42PF", "china_receive": "42PF",
            "tare_weight": 5600.00, "max_weight_kg": 39400, "max_cbm": 77.02,
            "length_mm": 12192, "width_mm": 2438, "height_mm": 2591,
            "cbm_limit": False, "sort_order": 6
        },
        {
            "code": "40DC", "name": "40 Dry Container", "abbreviation": "40'DC",
            "description": "40ft Standard Dry Container",
            "size": "40", "category": "DC", "size_teu": 2.0,
            "iso_standard": "42G0", "customs_port_standard": "42GP",
            "china_send_standard": "GP40", "china_receive": "42GP",
            "tare_weight": 3500.00, "max_weight_kg": 26980, "max_cbm": 67.64,
            "length_mm": 12032, "width_mm": 2352, "height_mm": 2390,
            "cbm_limit": True, "sort_order": 7
        },
        {
            "code": "4HDC", "name": "40 HC Dry Container", "abbreviation": "40'HC",
            "description": "40ft High Cube Dry Container",
            "size": "4H", "category": "DC", "size_teu": 2.0,
            "iso_standard": "45G0", "customs_port_standard": "45GP",
            "china_send_standard": "HC45", "china_receive": "45GP",
            "tare_weight": 4000.00, "max_weight_kg": 28500, "max_cbm": 76.35,
            "length_mm": 12032, "width_mm": 2352, "height_mm": 2698,
            "cbm_limit": True, "sort_order": 8
        },
        {
            "code": "40OT", "name": "40 Open Top Container", "abbreviation": "40'OT",
            "description": "40ft Open Top Container",
            "size": "40", "category": "OT", "size_teu": 2.0,
            "iso_standard": "42U0", "customs_port_standard": "42UT",
            "china_send_standard": "42UT", "china_receive": "42UT",
            "tare_weight": 4000.00, "max_weight_kg": 26480, "max_cbm": 66.45,
            "length_mm": 12032, "width_mm": 2352, "height_mm": 2348,
            "cbm_limit": False, "sort_order": 9
        },
        {
            "code": "40TK", "name": "40 Tank Container", "abbreviation": "40'TK",
            "description": "40ft Tank Container",
            "size": "40", "category": "TK", "size_teu": 2.0,
            "iso_standard": "42K0", "customs_port_standard": "42TN",
            "china_send_standard": "42TN", "china_receive": "42TN",
            "tare_weight": 5000.00, "max_weight_kg": 31000, "max_cbm": 77.02,
            "length_mm": 12192, "width_mm": 2438, "height_mm": 2591,
            "cbm_limit": False, "sort_order": 10
        },
        # 40ft High Cube Containers
        {
            "code": "4HFR", "name": "40 HC Flat Rack Container", "abbreviation": "40'HF",
            "description": "40ft High Cube Flat Rack Container",
            "size": "4H", "category": "FR", "size_teu": 2.0,
            "iso_standard": "45P1", "customs_port_standard": "45PC",
            "china_send_standard": "45PF", "china_receive": "45PF",
            "tare_weight": 5600.00, "max_weight_kg": 44400, "max_cbm": 86.08,
            "length_mm": 12192, "width_mm": 2438, "height_mm": 2896,
            "cbm_limit": False, "sort_order": 11
        },
        {
            "code": "4HRF", "name": "40 HC Reefer Container", "abbreviation": "40'HR",
            "description": "40ft High Cube Refrigerated Container",
            "size": "4H", "category": "RF", "size_teu": 2.0,
            "iso_standard": "45R0", "customs_port_standard": "45RE",
            "china_send_standard": "RF45", "china_receive": "45RT",
            "tare_weight": 4670.00, "max_weight_kg": 29330, "max_cbm": 67.95,
            "length_mm": 11584, "width_mm": 2294, "height_mm": 2557,
            "cbm_limit": True, "sort_order": 12
        },
    ]
    
    for ct_data in container_types:
        existing = db.query(ContainerType).filter(ContainerType.code == ct_data["code"]).first()
        if existing:
            # Update existing record with new fields
            for key, value in ct_data.items():
                setattr(existing, key, value)
        else:
            db.add(ContainerType(**ct_data))
    
    db.commit()
    print(f"[OK] Seeded {len(container_types)} container types")


def seed_truck_types(db):
    """Seed Truck Types data"""
    truck_types = [
        {"code": "1T_CARGO", "name": "1T Cargo", "abbreviation": "1T카고", "description": "1톤 카고", "max_weight_kg": 1000, "max_cbm": 5.0, "sort_order": 1},
        {"code": "1T_WING", "name": "1T Wing Body", "abbreviation": "1T윙", "description": "1톤 윙바디", "max_weight_kg": 1000, "max_cbm": 5.0, "sort_order": 2},
        {"code": "2.5T_CARGO", "name": "2.5T Cargo", "abbreviation": "2.5T카고", "description": "2.5톤 카고", "max_weight_kg": 2500, "max_cbm": 10.0, "sort_order": 3},
        {"code": "2.5T_WING", "name": "2.5T Wing Body", "abbreviation": "2.5T윙", "description": "2.5톤 윙바디", "max_weight_kg": 2500, "max_cbm": 10.0, "sort_order": 4},
        {"code": "5T_CARGO", "name": "5T Cargo", "abbreviation": "5T카고", "description": "5톤 카고", "max_weight_kg": 5000, "max_cbm": 20.0, "sort_order": 5},
        {"code": "5T_WING", "name": "5T Wing Body", "abbreviation": "5T윙", "description": "5톤 윙바디", "max_weight_kg": 5000, "max_cbm": 20.0, "sort_order": 6},
        {"code": "8T_CARGO", "name": "8T Cargo", "abbreviation": "8T카고", "description": "8톤 카고", "max_weight_kg": 8000, "max_cbm": 30.0, "sort_order": 7},
        {"code": "8T_WING", "name": "8T Wing Body", "abbreviation": "8T윙", "description": "8톤 윙바디", "max_weight_kg": 8000, "max_cbm": 30.0, "sort_order": 8},
        {"code": "11T_CARGO", "name": "11T Cargo", "abbreviation": "11T카고", "description": "11톤 카고", "max_weight_kg": 11000, "max_cbm": 40.0, "sort_order": 9},
        {"code": "11T_WING", "name": "11T Wing Body", "abbreviation": "11T윙", "description": "11톤 윙바디", "max_weight_kg": 11000, "max_cbm": 40.0, "sort_order": 10},
        {"code": "18T_WING", "name": "18T Wing Body", "abbreviation": "18T윙", "description": "18톤 윙바디", "max_weight_kg": 18000, "max_cbm": 55.0, "sort_order": 11},
        {"code": "25T_WING", "name": "25T Wing Body", "abbreviation": "25T윙", "description": "25톤 윙바디", "max_weight_kg": 25000, "max_cbm": 70.0, "sort_order": 12},
        {"code": "5T_COLD", "name": "5T Cold Chain", "abbreviation": "5T냉동", "description": "5톤 냉동", "max_weight_kg": 4500, "max_cbm": 18.0, "sort_order": 13},
        {"code": "11T_COLD", "name": "11T Cold Chain", "abbreviation": "11T냉동", "description": "11톤 냉동", "max_weight_kg": 10000, "max_cbm": 35.0, "sort_order": 14},
        {"code": "TRAILER", "name": "Trailer", "abbreviation": "TR", "description": "트레일러", "max_weight_kg": 24000, "max_cbm": 70.0, "sort_order": 15},
    ]
    
    for tt_data in truck_types:
        existing = db.query(TruckType).filter(TruckType.code == tt_data["code"]).first()
        if existing:
            # Update existing record with new fields (including abbreviation)
            for key, value in tt_data.items():
                setattr(existing, key, value)
        else:
            db.add(TruckType(**tt_data))
    
    db.commit()
    print(f"[OK] Seeded {len(truck_types)} truck types")


def seed_incoterms(db):
    """Seed Incoterms data"""
    incoterms = [
        {
            "code": "EXW", 
            "name": "Ex Works", 
            "description": "The seller delivers the goods by placing them at the buyer's disposal at a named place of delivery. The buyer bears all costs and risks from taking over the goods.",
            "description_ko": "공장인도조건. 매도인은 자신의 영업소나 공장에서 물품을 매수인에게 인도. 이후 모든 비용과 위험은 매수인 부담.",
            "seller_responsibility": "Goods available at seller's premises",
            "buyer_responsibility": "All transportation and risks",
            "sort_order": 1
        },
        {
            "code": "FOB", 
            "name": "Free On Board", 
            "description": "The seller delivers the goods on board the vessel at the named port of shipment. Risk passes when goods are on board.",
            "description_ko": "본선인도조건. 매도인이 지정선적항에서 매수인이 지정한 본선에 물품을 적재. 본선 적재 시점에 위험 이전.",
            "seller_responsibility": "Delivery to vessel, export clearance",
            "buyer_responsibility": "Freight, insurance, import clearance",
            "sort_order": 2
        },
        {
            "code": "CFR", 
            "name": "Cost and Freight", 
            "description": "The seller delivers the goods on board the vessel and pays the freight to the named port of destination.",
            "description_ko": "운임포함조건. 매도인이 물품을 본선에 적재하고 목적항까지의 운임을 부담.",
            "seller_responsibility": "Delivery to vessel, freight to destination",
            "buyer_responsibility": "Insurance, import clearance",
            "sort_order": 3
        },
        {
            "code": "CIF", 
            "name": "Cost, Insurance and Freight", 
            "description": "The seller delivers the goods on board the vessel, pays freight and insurance to the named port of destination.",
            "description_ko": "운임보험료포함조건. 매도인이 물품을 본선에 적재하고 목적항까지의 운임과 보험료를 부담.",
            "seller_responsibility": "Delivery to vessel, freight, insurance",
            "buyer_responsibility": "Import clearance, delivery from port",
            "sort_order": 4
        },
        {
            "code": "DAP", 
            "name": "Delivered at Place", 
            "description": "The seller delivers when the goods are placed at the disposal of the buyer on the arriving means of transport, ready for unloading.",
            "description_ko": "도착장소인도조건. 매도인이 목적지까지 운송하여 양하준비 상태로 매수인에게 인도.",
            "seller_responsibility": "Delivery to destination, unloaded",
            "buyer_responsibility": "Import clearance, unloading",
            "sort_order": 5
        },
        {
            "code": "DDP", 
            "name": "Delivered Duty Paid", 
            "description": "The seller delivers the goods cleared for import, at the named place of destination. Maximum obligation for seller.",
            "description_ko": "관세지급인도조건. 매도인이 수입통관 완료 후 목적지까지 인도. 매도인의 최대 의무.",
            "seller_responsibility": "All costs including import duties",
            "buyer_responsibility": "Receive goods at destination",
            "sort_order": 6
        },
    ]
    
    for inco_data in incoterms:
        existing = db.query(Incoterm).filter(Incoterm.code == inco_data["code"]).first()
        if not existing:
            db.add(Incoterm(**inco_data))
    
    db.commit()
    print(f"[OK] Seeded {len(incoterms)} incoterms")


def run_all_seeds():
    """Run all seed functions"""
    print("\n[SEED] Starting database seeding...\n")
    
    # Initialize database (create tables)
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created\n")
    
    # Create session
    db = SessionLocal()
    
    try:
        seed_ports(db)
        seed_container_types(db)
        seed_truck_types(db)
        seed_incoterms(db)
        
        print("\n[SUCCESS] All seed data inserted successfully!")
        
    except Exception as e:
        print(f"[ERROR] Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run_all_seeds()

