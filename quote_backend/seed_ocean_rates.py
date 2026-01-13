"""
Ocean Rate Seed Script - BUSAN → ROTTERDAM
Quick Quotation 기능을 위한 운임 데이터 삽입

Usage:
    python seed_ocean_rates.py
"""

from datetime import datetime
from database import SessionLocal, engine
from models import (
    Base, Port, ContainerType, FreightCode, FreightCategory,
    OceanRateSheet, OceanRateItem
)

# Create tables if not exist
Base.metadata.create_all(bind=engine)


def add_missing_container_types(db):
    """누락된 컨테이너 타입 추가 (45HC)"""
    existing = db.query(ContainerType).filter(ContainerType.code == "45DC").first()
    if not existing:
        ct = ContainerType(
            code="45DC",
            name="45 HC Dry Container",
            abbreviation="45'HC",
            description="45ft High Cube Dry Container",
            size="45",
            category="DC",
            is_active=True,
            sort_order=13
        )
        db.add(ct)
        db.commit()
        print("[OK] Added 45HC container type")
    else:
        print("[SKIP] 45HC container type already exists")


def add_missing_freight_codes(db):
    """누락된 운임 코드 추가"""
    # Get LOCAL_CHARGES category
    local_cat = db.query(FreightCategory).filter(FreightCategory.code == "LOCAL_CHARGES").first()
    ocean_cat = db.query(FreightCategory).filter(FreightCategory.code == "OCEAN").first()
    
    missing_codes = [
        # (code, category, group, name_en, name_ko, currency)
        ("ECC", ocean_cat.id, "SURCHARGE", "ENVIRONMENTAL COMPLIANCE CHARGE", "환경규제할증료", "USD"),
        ("PSS", ocean_cat.id, "SURCHARGE", "PEAK SEASON SURCHARGE", "성수기할증료", "USD"),
        ("EES", local_cat.id, "SURCHARGE", "EUROPE EMISSION SURCHARGE", "유럽환경할증료", "EUR"),
        ("ENS", local_cat.id, "DOCUMENT", "ENS/S&S CHARGE", "ENS/S&S 신고비용", "USD"),
        ("KLS", local_cat.id, "SURCHARGE", "KOREA LOW SULPHUR CHARGE", "한국 저유황유할증료", "USD"),
        ("CSL", local_cat.id, "ETC", "CONTAINER SEAL CHARGE", "컨테이너 씰 비용", "KRW"),
    ]
    
    added = 0
    for code, cat_id, group, name_en, name_ko, currency in missing_codes:
        existing = db.query(FreightCode).filter(FreightCode.code == code).first()
        if not existing:
            fc = FreightCode(
                code=code,
                category_id=cat_id,
                group_name=group,
                name_en=name_en,
                name_ko=name_ko,
                vat_applicable=False,
                default_currency=currency,
                is_active=True,
                sort_order=100 + added
            )
            db.add(fc)
            added += 1
    
    if added > 0:
        db.commit()
        print(f"[OK] Added {added} missing freight codes")
    else:
        print("[SKIP] All freight codes already exist")


def seed_busan_rotterdam_rates(db):
    """BUSAN → ROTTERDAM 운임 데이터 시딩"""
    
    # Get ports
    pol = db.query(Port).filter(Port.code == "KRPUS").first()
    pod = db.query(Port).filter(Port.code == "NLRTM").first()
    
    if not pol or not pod:
        print("[ERROR] KRPUS or NLRTM port not found")
        return
    
    # Check if sheet already exists
    existing_sheet = db.query(OceanRateSheet).filter(
        OceanRateSheet.pol_id == pol.id,
        OceanRateSheet.pod_id == pod.id,
        OceanRateSheet.carrier == "HMM"
    ).first()
    
    if existing_sheet:
        print(f"[SKIP] Rate sheet for KRPUS -> NLRTM (HMM) already exists (id={existing_sheet.id})")
        return
    
    # Create rate sheet
    sheet = OceanRateSheet(
        pol_id=pol.id,
        pod_id=pod.id,
        carrier="HMM",
        valid_from=datetime(2026, 1, 1),
        valid_to=datetime(2026, 1, 31),
        is_active=True,
        remark="BUSAN → ROTTERDAM HMM Ocean Freight Rates (Jan 2026)"
    )
    db.add(sheet)
    db.flush()  # Get sheet.id
    
    print(f"[OK] Created rate sheet (id={sheet.id})")
    
    # Get container types
    container_types = {ct.code: ct.id for ct in db.query(ContainerType).all()}
    
    # Get freight codes
    freight_codes = {fc.code: fc.id for fc in db.query(FreightCode).all()}
    
    # Container type mapping from Excel to DB
    ct_mapping = {
        "20 Flat Rack Container": "20FR",
        "20 Dry Container": "20DC",
        "20 Open Top Container": "20OT",
        "20 Reefer Container": "20RF",
        "20 Tank Container": "20TK",
        "40 Flat Rack Container": "40FR",
        "40 Dry Container": "40DC",
        "40 HC Dry Container": "4HDC",
        "40 Open Top Container": "40OT",
        "40 Tank Container": "40TK",
        "40 HC Flat Rack Container": "4HFR",
        "40 HC Reefer Container": "4HRF",
        "45 HC Dry Container": "45DC",
    }
    
    # Rate data from Excel (BUSAN → ROTTERDAM)
    # Format: [(container_name, freight_code, freight_group, unit, currency, rate), ...]
    rate_data = [
        # ===== Ocean Freight (OFR) =====
        ("20 Flat Rack Container", "FRT", "Ocean Freight", "Qty", "USD", None),  # N/A
        ("20 Dry Container", "FRT", "Ocean Freight", "Qty", "USD", 858),
        ("20 Open Top Container", "FRT", "Ocean Freight", "Qty", "USD", None),  # N/A
        ("20 Reefer Container", "FRT", "Ocean Freight", "Qty", "USD", None),  # N/A
        ("20 Tank Container", "FRT", "Ocean Freight", "Qty", "USD", None),  # N/A
        ("40 Flat Rack Container", "FRT", "Ocean Freight", "Qty", "USD", None),  # N/A
        ("40 Dry Container", "FRT", "Ocean Freight", "Qty", "USD", 1316),
        ("40 HC Dry Container", "FRT", "Ocean Freight", "Qty", "USD", 1316),
        ("40 Open Top Container", "FRT", "Ocean Freight", "Qty", "USD", None),  # N/A
        ("40 Tank Container", "FRT", "Ocean Freight", "Qty", "USD", None),  # N/A
        ("40 HC Flat Rack Container", "FRT", "Ocean Freight", "Qty", "USD", None),  # N/A
        ("40 HC Reefer Container", "FRT", "Ocean Freight", "Qty", "USD", None),  # N/A
        ("45 HC Dry Container", "FRT", "Ocean Freight", "Qty", "USD", 2116),
        
        # ===== Environmental Compliance Charge (ECC) =====
        ("20 Flat Rack Container", "ECC", "Ocean Freight", "Qty", "USD", 64),
        ("20 Dry Container", "ECC", "Ocean Freight", "Qty", "USD", 64),
        ("20 Open Top Container", "ECC", "Ocean Freight", "Qty", "USD", 64),
        ("20 Reefer Container", "ECC", "Ocean Freight", "Qty", "USD", 64),
        ("20 Tank Container", "ECC", "Ocean Freight", "Qty", "USD", 64),
        ("40 Flat Rack Container", "ECC", "Ocean Freight", "Qty", "USD", 128),
        ("40 Dry Container", "ECC", "Ocean Freight", "Qty", "USD", 128),
        ("40 HC Dry Container", "ECC", "Ocean Freight", "Qty", "USD", 128),
        ("40 Open Top Container", "ECC", "Ocean Freight", "Qty", "USD", 128),
        ("40 Tank Container", "ECC", "Ocean Freight", "Qty", "USD", 128),
        ("40 HC Flat Rack Container", "ECC", "Ocean Freight", "Qty", "USD", 128),
        ("40 HC Reefer Container", "ECC", "Ocean Freight", "Qty", "USD", 128),
        ("45 HC Dry Container", "ECC", "Ocean Freight", "Qty", "USD", 128),
        
        # ===== Peak Season Surcharge (PSS) =====
        ("20 Flat Rack Container", "PSS", "Ocean Freight", "Qty", "USD", 500),
        ("20 Dry Container", "PSS", "Ocean Freight", "Qty", "USD", 500),
        ("20 Open Top Container", "PSS", "Ocean Freight", "Qty", "USD", 500),
        ("20 Reefer Container", "PSS", "Ocean Freight", "Qty", "USD", 500),
        ("20 Tank Container", "PSS", "Ocean Freight", "Qty", "USD", 500),
        ("40 Flat Rack Container", "PSS", "Ocean Freight", "Qty", "USD", 1000),
        ("40 Dry Container", "PSS", "Ocean Freight", "Qty", "USD", 1000),
        ("40 HC Dry Container", "PSS", "Ocean Freight", "Qty", "USD", 1000),
        ("40 Open Top Container", "PSS", "Ocean Freight", "Qty", "USD", 1000),
        ("40 Tank Container", "PSS", "Ocean Freight", "Qty", "USD", 1000),
        ("40 HC Flat Rack Container", "PSS", "Ocean Freight", "Qty", "USD", 1000),
        ("40 HC Reefer Container", "PSS", "Ocean Freight", "Qty", "USD", 1000),
        ("45 HC Dry Container", "PSS", "Ocean Freight", "Qty", "USD", 1000),
        
        # ===== Document Fee (DOC) =====
        ("20 Flat Rack Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("20 Dry Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("20 Open Top Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("20 Reefer Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("20 Tank Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("40 Flat Rack Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("40 Dry Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("40 HC Dry Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("40 Open Top Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("40 Tank Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("40 HC Flat Rack Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("40 HC Reefer Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        ("45 HC Dry Container", "DOC", "Origin Local Charges", "BL", "KRW", 50000),
        
        # ===== Europe Emission Surcharge (EES) =====
        ("20 Flat Rack Container", "EES", "Origin Local Charges", "Qty", "EUR", 42),
        ("20 Dry Container", "EES", "Origin Local Charges", "Qty", "EUR", 42),
        ("20 Open Top Container", "EES", "Origin Local Charges", "Qty", "EUR", 42),
        ("20 Reefer Container", "EES", "Origin Local Charges", "Qty", "EUR", 42),
        ("20 Tank Container", "EES", "Origin Local Charges", "Qty", "EUR", 42),
        ("40 Flat Rack Container", "EES", "Origin Local Charges", "Qty", "EUR", 84),
        ("40 Dry Container", "EES", "Origin Local Charges", "Qty", "EUR", 84),
        ("40 HC Dry Container", "EES", "Origin Local Charges", "Qty", "EUR", 84),
        ("40 Open Top Container", "EES", "Origin Local Charges", "Qty", "EUR", 84),
        ("40 Tank Container", "EES", "Origin Local Charges", "Qty", "EUR", 84),
        ("40 HC Flat Rack Container", "EES", "Origin Local Charges", "Qty", "EUR", 84),
        ("40 HC Reefer Container", "EES", "Origin Local Charges", "Qty", "EUR", 84),
        ("45 HC Dry Container", "EES", "Origin Local Charges", "Qty", "EUR", 84),
        
        # ===== ENS/S&S CHARGE (ENS) =====
        ("20 Flat Rack Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("20 Dry Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("20 Open Top Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("20 Reefer Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("20 Tank Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("40 Flat Rack Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("40 Dry Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("40 HC Dry Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("40 Open Top Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("40 Tank Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("40 HC Flat Rack Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("40 HC Reefer Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        ("45 HC Dry Container", "ENS", "Origin Local Charges", "BL", "USD", 35),
        
        # ===== Korea Low Sulphur Charge (KLS) =====
        ("20 Flat Rack Container", "KLS", "Origin Local Charges", "Qty", "USD", 3),
        ("20 Dry Container", "KLS", "Origin Local Charges", "Qty", "USD", 3),
        ("20 Open Top Container", "KLS", "Origin Local Charges", "Qty", "USD", 3),
        ("20 Reefer Container", "KLS", "Origin Local Charges", "Qty", "USD", 3),
        ("20 Tank Container", "KLS", "Origin Local Charges", "Qty", "USD", 3),
        ("40 Flat Rack Container", "KLS", "Origin Local Charges", "Qty", "USD", 6),
        ("40 Dry Container", "KLS", "Origin Local Charges", "Qty", "USD", 6),
        ("40 HC Dry Container", "KLS", "Origin Local Charges", "Qty", "USD", 6),
        ("40 Open Top Container", "KLS", "Origin Local Charges", "Qty", "USD", 6),
        ("40 Tank Container", "KLS", "Origin Local Charges", "Qty", "USD", 6),
        ("40 HC Flat Rack Container", "KLS", "Origin Local Charges", "Qty", "USD", 6),
        ("40 HC Reefer Container", "KLS", "Origin Local Charges", "Qty", "USD", 6),
        ("45 HC Dry Container", "KLS", "Origin Local Charges", "Qty", "USD", 6),
        
        # ===== Container Seal Charge (CSL) =====
        ("20 Flat Rack Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("20 Dry Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("20 Open Top Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("20 Reefer Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("20 Tank Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("40 Flat Rack Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("40 Dry Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("40 HC Dry Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("40 Open Top Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("40 Tank Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("40 HC Flat Rack Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("40 HC Reefer Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        ("45 HC Dry Container", "CSL", "Origin Local Charges", "Qty", "KRW", 10000),
        
        # ===== THC (Terminal Handling Charge) =====
        ("20 Flat Rack Container", "THC", "Origin Local Charges", "Qty", "KRW", 150000),
        ("20 Dry Container", "THC", "Origin Local Charges", "Qty", "KRW", 150000),
        ("20 Open Top Container", "THC", "Origin Local Charges", "Qty", "KRW", 150000),
        ("20 Reefer Container", "THC", "Origin Local Charges", "Qty", "KRW", 150000),
        ("20 Tank Container", "THC", "Origin Local Charges", "Qty", "KRW", 150000),
        ("40 Flat Rack Container", "THC", "Origin Local Charges", "Qty", "KRW", 210000),
        ("40 Dry Container", "THC", "Origin Local Charges", "Qty", "KRW", 210000),
        ("40 HC Dry Container", "THC", "Origin Local Charges", "Qty", "KRW", 210000),
        ("40 Open Top Container", "THC", "Origin Local Charges", "Qty", "KRW", 210000),
        ("40 Tank Container", "THC", "Origin Local Charges", "Qty", "KRW", 210000),
        ("40 HC Flat Rack Container", "THC", "Origin Local Charges", "Qty", "KRW", 210000),
        ("40 HC Reefer Container", "THC", "Origin Local Charges", "Qty", "KRW", 210000),
        ("45 HC Dry Container", "THC", "Origin Local Charges", "Qty", "KRW", 250000),
    ]
    
    # Insert rate items
    item_count = 0
    for container_name, fc_code, freight_group, unit, currency, rate in rate_data:
        ct_code = ct_mapping.get(container_name)
        if not ct_code or ct_code not in container_types:
            print(f"[WARN] Container type not found: {container_name} -> {ct_code}")
            continue
        
        if fc_code not in freight_codes:
            print(f"[WARN] Freight code not found: {fc_code}")
            continue
        
        item = OceanRateItem(
            sheet_id=sheet.id,
            container_type_id=container_types[ct_code],
            freight_code_id=freight_codes[fc_code],
            freight_group=freight_group,
            unit=unit,
            currency=currency,
            rate=rate,  # None for N/A (Quick Quotation = N)
            is_active=True
        )
        db.add(item)
        item_count += 1
    
    db.commit()
    print(f"[OK] Added {item_count} rate items")


def main():
    db = SessionLocal()
    
    try:
        print("=" * 50)
        print("Ocean Rate Seeder - BUSAN → ROTTERDAM")
        print("=" * 50)
        
        # Step 1: Add missing container types
        add_missing_container_types(db)
        
        # Step 2: Add missing freight codes
        add_missing_freight_codes(db)
        
        # Step 3: Seed rate data
        seed_busan_rotterdam_rates(db)
        
        print("\n[DONE] Ocean rate seed completed!")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
