"""
Trucking Rates Seeding Script
내륙 운송 운임 샘플 데이터 시딩
출처: D:\Planning_data\Alind\내륙 운송 운임\내륙 운임.xlsx
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import TruckingRate, Port, Base

# 내륙 운임 샘플 데이터 (BUSAN -> 강원도)
TRUCKING_DATA = [
    # (cargo_type, origin_port_code, dest_province, dest_city, dest_district, distance_km, rate_20ft, rate_40ft)
    ("일반화물", "KRPUS", "강원도", "강릉시", "강포동", 369, 914600, 1040100),
    ("일반화물", "KRPUS", "강원도", "강릉시", "성덕동", 362, 904800, 1027600),
    ("일반화물", "KRPUS", "강원도", "강릉시", "옥계면", 336, 864400, 977300),
    ("일반화물", "KRPUS", "강원도", "고성군", "간성읍", 531, 1142000, 1319900),
    ("일반화물", "KRPUS", "강원도", "동해시", "북삼동", 317, 832300, 937500),
    ("일반화물", "KRPUS", "강원도", "동해시", "북평동", 315, 828800, 933200),
    ("일반화물", "KRPUS", "강원도", "동해시", "송정동", 318, 834000, 939500),
    ("일반화물", "KRPUS", "강원도", "원주시", "문막읍", 348, 884400, 1002100),
    ("일반화물", "KRPUS", "강원도", "원주시", "부론면", 316, 830600, 935200),
    ("일반화물", "KRPUS", "강원도", "원주시", "소초면", 352, 890600, 1009800),
    ("일반화물", "KRPUS", "강원도", "원주시", "우산동", 339, 869400, 983400),
    ("일반화물", "KRPUS", "강원도", "원주시", "지정면", 346, 881100, 998000),
    ("일반화물", "KRPUS", "강원도", "원주시", "태장1동", 339, 869400, 983400),
    ("일반화물", "KRPUS", "강원도", "춘천시", "남면", 412, 974600, 1116000),
    ("일반화물", "KRPUS", "강원도", "춘천시", "남산면", 416, 980000, 1123000),
    ("일반화물", "KRPUS", "강원도", "춘천시", "동면", 415, 978800, 1121300),
    ("일반화물", "KRPUS", "강원도", "춘천시", "후산면", 396, 952400, 1087900),
    ("일반화물", "KRPUS", "강원도", "춘천시", "후평1동", 412, 974600, 1116000),
]


def seed_trucking_rates():
    """Seed trucking rates data"""
    db: Session = SessionLocal()
    
    try:
        # KRPUS (BUSAN) 포트 ID 조회
        busan_port = db.query(Port).filter(Port.code == "KRPUS").first()
        if not busan_port:
            print("Error: KRPUS (BUSAN) port not found in database")
            return
        
        print(f"Found BUSAN port: ID={busan_port.id}, Code={busan_port.code}")
        
        # 기존 데이터 확인
        existing_count = db.query(TruckingRate).filter(
            TruckingRate.origin_port_id == busan_port.id
        ).count()
        
        if existing_count > 0:
            print(f"Found {existing_count} existing trucking rates for BUSAN")
            user_input = input("Delete existing data and re-seed? (y/n): ")
            if user_input.lower() == 'y':
                db.query(TruckingRate).filter(
                    TruckingRate.origin_port_id == busan_port.id
                ).delete()
                db.commit()
                print("Deleted existing data")
            else:
                print("Skipping seed")
                return
        
        # 데이터 삽입
        inserted_count = 0
        for data in TRUCKING_DATA:
            cargo_type, origin_code, dest_province, dest_city, dest_district, distance_km, rate_20ft, rate_40ft = data
            
            rate = TruckingRate(
                cargo_type=cargo_type,
                origin_port_id=busan_port.id,
                dest_province=dest_province,
                dest_city=dest_city,
                dest_district=dest_district,
                distance_km=distance_km,
                rate_20ft=rate_20ft,
                rate_40ft=rate_40ft,
                is_active=True
            )
            db.add(rate)
            inserted_count += 1
        
        db.commit()
        print(f"\n[OK] Successfully inserted {inserted_count} trucking rates")
        
        # 삽입된 데이터 확인
        print("\n=== Inserted Trucking Rates ===")
        rates = db.query(TruckingRate).filter(
            TruckingRate.origin_port_id == busan_port.id
        ).all()
        
        for rate in rates[:5]:  # 처음 5개만 표시
            print(f"  {rate.dest_province} {rate.dest_city} {rate.dest_district}: "
                  f"20ft={rate.rate_20ft:,.0f}원, 40ft={rate.rate_40ft:,.0f}원")
        
        if len(rates) > 5:
            print(f"  ... and {len(rates) - 5} more")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


def seed_trucking_rates_auto():
    """Seed trucking rates data without user confirmation (for automated use)"""
    db: Session = SessionLocal()
    
    try:
        # KRPUS (BUSAN) 포트 ID 조회
        busan_port = db.query(Port).filter(Port.code == "KRPUS").first()
        if not busan_port:
            print("Error: KRPUS (BUSAN) port not found in database")
            return False
        
        print(f"Found BUSAN port: ID={busan_port.id}, Code={busan_port.code}")
        
        # 기존 데이터 삭제
        deleted = db.query(TruckingRate).filter(
            TruckingRate.origin_port_id == busan_port.id
        ).delete()
        if deleted:
            print(f"Deleted {deleted} existing trucking rates")
        
        # 데이터 삽입
        inserted_count = 0
        for data in TRUCKING_DATA:
            cargo_type, origin_code, dest_province, dest_city, dest_district, distance_km, rate_20ft, rate_40ft = data
            
            rate = TruckingRate(
                cargo_type=cargo_type,
                origin_port_id=busan_port.id,
                dest_province=dest_province,
                dest_city=dest_city,
                dest_district=dest_district,
                distance_km=distance_km,
                rate_20ft=rate_20ft,
                rate_40ft=rate_40ft,
                is_active=True
            )
            db.add(rate)
            inserted_count += 1
        
        db.commit()
        print(f"[OK] Successfully inserted {inserted_count} trucking rates")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Seed trucking rates data')
    parser.add_argument('--auto', action='store_true', help='Run without user confirmation')
    args = parser.parse_args()
    
    if args.auto:
        seed_trucking_rates_auto()
    else:
        seed_trucking_rates()
