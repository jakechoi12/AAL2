"""
Report & Insight - Seed Data
Seed reports from JSON file + PDF files into PostgreSQL/SQLite database
MVP Version: No Auth, PDF stored in database as bytea
"""

import os
import sys
import json
import uuid
import hashlib
from datetime import date
from pathlib import Path
from .models import ReportDB, ReportFileDB, init_db, SessionLocal

# Seed data directory (same as this file's directory)
SEED_DIR = Path(__file__).parent
SEED_JSON = SEED_DIR / "reports_seed.json"
SEED_PDFS_DIR = SEED_DIR / "seed_pdfs"


def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def read_pdf_file(file_path: str) -> tuple:
    """Read PDF file and return (bytes, size, sha256)"""
    path = Path(file_path)
    if not path.exists():
        return None, 0, None
    
    with open(path, "rb") as f:
        file_bytes = f.read()
    
    file_size = len(file_bytes)
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    
    return file_bytes, file_size, sha256


def seed_from_json(json_path: str = None, pdf_base_dir: str = None):
    """
    Seed reports from JSON file and PDF files
    
    JSON format:
    [
        {
            "title": "Report Title",
            "source": "Organization Name",
            "category_key": "global_research",
            "published_at": "2025-12-20",
            "tags": ["Tag1", "Tag2"],
            "summary": "Summary text...",
            "key_insights": ["Insight 1", "Insight 2"],
            "canonical_url": "https://...",
            "pdf_path": "./seed_pdfs/report.pdf",
            "is_featured": true
        }
    ]
    """
    json_path = Path(json_path) if json_path else SEED_JSON
    pdf_base_dir = Path(pdf_base_dir) if pdf_base_dir else json_path.parent
    
    if not json_path.exists():
        print(f"JSON file not found: {json_path}")
        print("Creating sample JSON file...")
        create_sample_seed_json(json_path)
        return
    
    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        reports_data = json.load(f)
    
    print(f"Found {len(reports_data)} reports in {json_path}")
    
    init_db()
    db = SessionLocal()
    
    try:
        inserted_count = 0
        skipped_count = 0
        error_count = 0
        
        for report_data in reports_data:
            try:
                # Generate or use provided ID
                report_id = report_data.get("id") or f"RPT-{uuid.uuid4().hex[:8].upper()}"
                
                # Check if report already exists
                existing = db.query(ReportDB).filter(ReportDB.id == report_id).first()
                if existing:
                    print(f"  [SKIP] Report exists: {report_id}")
                    skipped_count += 1
                    continue
                
                # Create report
                db_report = ReportDB(
                    id=report_id,
                    title=report_data.get("title"),
                    category=report_data.get("category_key") or report_data.get("category"),
                    organization=report_data.get("source") or report_data.get("organization"),
                    published_date=date.fromisoformat(report_data.get("published_at") or report_data.get("published_date")),
                    summary=report_data.get("summary"),
                    canonical_url=report_data.get("canonical_url"),
                    is_featured=report_data.get("is_featured", False)
                )
                db_report.set_tags(report_data.get("tags", []))
                db_report.set_key_insights(report_data.get("key_insights", []))
                
                db.add(db_report)
                db.flush()  # Get report ID
                
                # Process PDF if provided
                pdf_path = report_data.get("pdf_path")
                if pdf_path:
                    full_pdf_path = pdf_base_dir / pdf_path
                    if full_pdf_path.exists():
                        file_bytes, file_size, sha256 = read_pdf_file(full_pdf_path)
                        
                        # Check for duplicate by SHA256
                        existing_file = db.query(ReportFileDB).filter(
                            ReportFileDB.sha256 == sha256
                        ).first()
                        
                        if existing_file:
                            print(f"  [WARN] Duplicate PDF (sha256): {pdf_path} -> reusing existing")
                            # Link to existing file's data is not needed, skip file creation
                        else:
                            # Create file record
                            file_id = f"FILE-{uuid.uuid4().hex[:8].upper()}"
                            db_file = ReportFileDB(
                                id=file_id,
                                report_id=report_id,
                                file_name=full_pdf_path.name,
                                mime_type="application/pdf",
                                file_size=file_size,
                                sha256=sha256,
                                file_bytes=file_bytes
                            )
                            db.add(db_file)
                            print(f"  [PDF] Stored: {full_pdf_path.name} ({file_size} bytes)")
                    else:
                        print(f"  [WARN] PDF not found: {pdf_path}")
                
                db.commit()
                print(f"  [OK] Inserted: {report_id} - {db_report.title[:50]}...")
                inserted_count += 1
                
            except Exception as e:
                db.rollback()
                print(f"  [ERROR] Failed to insert report: {e}")
                error_count += 1
                continue
        
        print("\n" + "="*50)
        print(f"Seed completed!")
        print(f"  Inserted: {inserted_count}")
        print(f"  Skipped:  {skipped_count}")
        print(f"  Errors:   {error_count}")
        print("="*50)
        
        # Print summary by category
        for category in ["global_research", "government", "company"]:
            count = db.query(ReportDB).filter(ReportDB.category == category).count()
            print(f"  - {category}: {count} reports")
        
        featured = db.query(ReportDB).filter(ReportDB.is_featured == True).count()
        print(f"  - Featured: {featured} reports")
        
        files_count = db.query(ReportFileDB).count()
        print(f"  - PDF files: {files_count}")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


def create_sample_seed_json(json_path: Path):
    """Create a sample seed JSON file"""
    sample_data = [
        {
            "title": "Global Supply Chain Outlook 2025: Navigating Uncertainty",
            "source": "McKinsey & Company",
            "category_key": "global_research",
            "published_at": "2024-12-15",
            "tags": ["Supply Chain", "Logistics", "AI", "Sustainability", "Global Trade"],
            "summary": "This comprehensive report analyzes the evolving landscape of global supply chains in 2025, examining key disruptions, technological innovations, and strategic recommendations for businesses.",
            "key_insights": [
                "Digital transformation of global supply chains is accelerating rapidly",
                "AI-driven logistics optimization emerging as a key competitive advantage",
                "Sustainability becoming a core element of supply chain strategy"
            ],
            "canonical_url": "https://www.mckinsey.com/supply-chain-2025",
            "pdf_path": "./seed_pdfs/mckinsey_supply_chain_2025.pdf",
            "is_featured": True
        },
        {
            "title": "The Future of Maritime Shipping: Decarbonization Pathways",
            "source": "Boston Consulting Group",
            "category_key": "global_research",
            "published_at": "2024-12-10",
            "tags": ["Maritime", "Decarbonization", "Shipping", "Sustainability"],
            "summary": "An in-depth analysis of decarbonization strategies for the maritime shipping industry, exploring alternative fuels and regulatory frameworks.",
            "key_insights": [
                "Roadmap presented for achieving 2050 net-zero targets",
                "Accelerated adoption of methanol and ammonia fuels required",
                "Industry structural changes expected due to IMO regulations"
            ],
            "canonical_url": "https://www.bcg.com/maritime-decarbonization",
            "pdf_path": "./seed_pdfs/bcg_maritime_decarbonization.pdf",
            "is_featured": True
        },
        {
            "title": "Korea Trade Statistics Annual Report 2024",
            "source": "Korea Customs Service",
            "category_key": "government",
            "published_at": "2024-12-20",
            "tags": ["Korea", "Trade Statistics", "Customs", "Import Export"],
            "summary": "Official annual report on Korea's trade statistics including import/export volumes and major trading partners.",
            "key_insights": [
                "반도체 수출이 전체 수출의 20% 이상 차지",
                "중국, 미국, EU가 주요 교역국으로 유지",
                "전자상거래 수입 통관 건수 급증"
            ],
            "canonical_url": "https://www.customs.go.kr/report/2024",
            "pdf_path": "./seed_pdfs/kcs_trade_report_2024.pdf",
            "is_featured": False
        },
        {
            "title": "Maersk Sustainability Report 2024",
            "source": "A.P. Moller - Maersk",
            "category_key": "company",
            "published_at": "2024-12-18",
            "tags": ["Maersk", "Sustainability", "Shipping", "Net Zero", "ESG"],
            "summary": "Annual sustainability report detailing Maersk's progress towards net-zero emissions.",
            "key_insights": [
                "Expansion of methanol-powered vessel operations underway",
                "2040 carbon neutrality target maintained",
                "Enhanced collaboration for Scope 3 emission reduction"
            ],
            "canonical_url": "https://www.maersk.com/sustainability/2024",
            "pdf_path": "./seed_pdfs/maersk_sustainability_2024.pdf",
            "is_featured": True
        }
    ]
    
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"Created sample JSON file: {json_path}")
    print("Please add PDF files to the seed_pdfs folder and run again.")


def seed_legacy_reports(force=False):
    """
    Seed the database with legacy sample reports (without PDF files)
    This is for backward compatibility with existing data
    
    Args:
        force: If True, add reports even if database is not empty
    """
    SAMPLE_REPORTS = [
        # Global Research (English)
        {
            "id": "RPT-GR001",
            "title": "Global Supply Chain Outlook 2025: Navigating Uncertainty",
            "category": "global_research",
            "organization": "McKinsey & Company",
            "published_date": date(2024, 12, 15),
            "summary": "This comprehensive report analyzes the evolving landscape of global supply chains in 2025, examining key disruptions, technological innovations, and strategic recommendations for businesses. The report covers major trends including nearshoring, AI-driven logistics optimization, and sustainable supply chain practices.",
            "tags": ["Supply Chain", "Logistics", "AI", "Sustainability", "Global Trade"],
            "key_insights": [
                "Digital transformation of global supply chains is accelerating rapidly",
                "AI-driven logistics optimization emerging as a key competitive advantage",
                "Sustainability becoming a core element of supply chain strategy"
            ],
            "is_featured": True
        },
        {
            "id": "RPT-GR002",
            "title": "The Future of Maritime Shipping: Decarbonization Pathways",
            "category": "global_research",
            "organization": "Boston Consulting Group",
            "published_date": date(2024, 12, 10),
            "summary": "An in-depth analysis of decarbonization strategies for the maritime shipping industry. This report explores alternative fuels, vessel design innovations, and regulatory frameworks that will shape the industry's path to net-zero emissions by 2050.",
            "tags": ["Maritime", "Decarbonization", "Shipping", "Sustainability"],
            "key_insights": [
                "Roadmap presented for achieving 2050 net-zero targets",
                "Accelerated adoption of alternative fuels like methanol and ammonia required",
                "Industry structural changes expected due to strengthened IMO regulations"
            ],
            "is_featured": True
        },
        {
            "id": "RPT-GR003",
            "title": "E-commerce Logistics Trends: Last-Mile Delivery Innovation",
            "category": "global_research",
            "organization": "Deloitte",
            "published_date": date(2024, 11, 28),
            "summary": "Exploring the latest trends in e-commerce logistics with a focus on last-mile delivery innovations. The report covers autonomous delivery vehicles, drone logistics, micro-fulfillment centers, and the growing importance of same-day delivery capabilities.",
            "tags": ["E-commerce", "Last-Mile", "Delivery", "Innovation", "Technology"],
            "key_insights": [
                "Last-mile delivery costs account for over 50% of total logistics costs",
                "Autonomous delivery robot market expected to grow rapidly",
                "Micro-fulfillment centers expanding due to increased same-day delivery demand"
            ],
            "is_featured": False
        },
        {
            "id": "RPT-GR004",
            "title": "AI in Logistics: Transforming Operations Through Intelligent Automation",
            "category": "global_research",
            "organization": "PwC",
            "published_date": date(2024, 11, 15),
            "summary": "A comprehensive study on how artificial intelligence is revolutionizing logistics operations. Topics include predictive analytics, route optimization, demand forecasting, warehouse automation, and the integration of large language models in supply chain management.",
            "tags": ["AI", "Automation", "Logistics", "Technology", "Digital Transformation"],
            "key_insights": [
                "AI adoption can reduce logistics costs by 15-20%",
                "Improved demand forecasting accuracy enables inventory optimization",
                "LLM-based customer service automation expanding across the industry"
            ],
            "is_featured": True
        },
        # Government Reports (Korean reports keep Korean insights)
        {
            "id": "RPT-GOV001",
            "title": "Korea Trade Statistics Annual Report 2024",
            "category": "government",
            "organization": "Korea Customs Service",
            "published_date": date(2024, 12, 20),
            "summary": "Official annual report on Korea's trade statistics including import/export volumes, major trading partners, commodity trends, and customs procedures. Includes detailed analysis of trade policy impacts and future outlook.",
            "tags": ["Korea", "Trade Statistics", "Customs", "Import Export"],
            "key_insights": [
                "반도체 수출이 전체 수출의 20% 이상 차지",
                "중국, 미국, EU가 주요 교역국으로 유지",
                "전자상거래 수입 통관 건수 급증"
            ],
            "is_featured": False
        },
        {
            "id": "RPT-GOV002",
            "title": "U.S. Maritime Administration: Freight Transportation Report",
            "category": "government",
            "organization": "U.S. Department of Transportation",
            "published_date": date(2024, 12, 1),
            "summary": "Comprehensive report on the state of freight transportation in the United States, covering modal shares, infrastructure investments, port performance metrics, and policy recommendations for improving supply chain resilience.",
            "tags": ["USA", "Maritime", "Freight", "Infrastructure", "Policy"],
            "key_insights": [
                "Port handling capacity improved through expanded infrastructure investment",
                "Need for inland logistics network improvements emphasized",
                "Green freight transportation policies being strengthened"
            ],
            "is_featured": False
        },
        {
            "id": "RPT-GOV003",
            "title": "EU Green Deal: Sustainable Logistics Framework 2030",
            "category": "government",
            "organization": "European Commission",
            "published_date": date(2024, 11, 20),
            "summary": "Policy framework document outlining the European Union's strategy for achieving sustainable logistics by 2030. Covers regulations on emissions, incentives for green technologies, and infrastructure development plans.",
            "tags": ["EU", "Green Deal", "Sustainability", "Policy", "Regulations"],
            "key_insights": [
                "Target of 55% carbon emission reduction in logistics sector by 2030",
                "Expanded incentives for eco-friendly vehicle adoption",
                "Push to increase rail freight transportation share"
            ],
            "is_featured": False
        },
        # Company Reports (English)
        {
            "id": "RPT-CO001",
            "title": "Maersk Sustainability Report 2024",
            "category": "company",
            "organization": "A.P. Moller - Maersk",
            "published_date": date(2024, 12, 18),
            "summary": "Annual sustainability report detailing Maersk's progress towards net-zero emissions, including methanol-powered vessel deployments, green corridor initiatives, and scope 3 emission reduction strategies.",
            "tags": ["Maersk", "Sustainability", "Shipping", "Net Zero", "ESG"],
            "key_insights": [
                "Expansion of methanol-powered vessel operations underway",
                "2040 carbon neutrality target maintained",
                "Enhanced customer collaboration for Scope 3 emission reduction"
            ],
            "is_featured": True
        },
        {
            "id": "RPT-CO002",
            "title": "DHL Global Connectedness Index 2024",
            "category": "company",
            "organization": "DHL",
            "published_date": date(2024, 12, 5),
            "summary": "Annual analysis of global trade, capital, information, and people flows. The report examines globalization trends, regional connectivity patterns, and the impact of geopolitical developments on international trade.",
            "tags": ["DHL", "Globalization", "Trade", "Connectivity Index"],
            "key_insights": [
                "Globalization index recovered to pre-COVID levels",
                "Asia-North America trade connectivity strengthened",
                "Digital trade flows surging dramatically"
            ],
            "is_featured": False
        },
        {
            "id": "RPT-CO003",
            "title": "FedEx Logistics Technology Innovation Report",
            "category": "company",
            "organization": "FedEx Corporation",
            "published_date": date(2024, 11, 25),
            "summary": "Overview of FedEx's technology investments and innovations, including autonomous delivery robots, AI-powered sorting systems, blockchain tracking solutions, and sustainability initiatives.",
            "tags": ["FedEx", "Technology", "Innovation", "Automation"],
            "key_insights": [
                "Autonomous delivery robot pilot programs expanding",
                "AI-based sorting systems improving efficiency by 30%",
                "Blockchain-based cargo tracking services being deployed"
            ],
            "is_featured": False
        },
    ]
    
    init_db()
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing = db.query(ReportDB).count()
        if existing > 0 and not force:
            print(f"Database already contains {existing} reports. Use --force to add anyway.")
            return
        
        # Insert sample reports
        inserted = 0
        for report_data in SAMPLE_REPORTS:
            # Skip if already exists
            if db.query(ReportDB).filter(ReportDB.id == report_data.get('id')).first():
                print(f"  [SKIP] Report exists: {report_data.get('id')}")
                continue
            
            report_data_copy = report_data.copy()
            tags = report_data_copy.pop("tags", [])
            key_insights = report_data_copy.pop("key_insights", [])
            report = ReportDB(**report_data_copy)
            report.set_tags(tags)
            report.set_key_insights(key_insights)
            db.add(report)
            inserted += 1
        
        db.commit()
        print(f"Successfully seeded {inserted} reports!")
        
        # Print summary
        for category in ["global_research", "government", "company"]:
            count = db.query(ReportDB).filter(ReportDB.category == category).count()
            print(f"  - {category}: {count} reports")
        
        featured = db.query(ReportDB).filter(ReportDB.is_featured == True).count()
        print(f"  - Featured: {featured} reports")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


def clear_reports():
    """Clear all reports from the database"""
    db = SessionLocal()
    try:
        # Delete files first (if cascade doesn't work)
        db.query(ReportFileDB).delete()
        db.query(ReportDB).delete()
        db.commit()
        print("All reports and files cleared!")
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed reports into database")
    parser.add_argument("--clear", action="store_true", help="Clear all reports")
    parser.add_argument("--legacy", action="store_true", help="Use legacy sample data (no PDF)")
    parser.add_argument("--force", action="store_true", help="Force adding data even if DB not empty")
    parser.add_argument("--json", type=str, help="Path to JSON seed file")
    parser.add_argument("--pdf-dir", type=str, help="Base directory for PDF files")
    
    args = parser.parse_args()
    
    if args.clear:
        clear_reports()
    elif args.legacy:
        seed_legacy_reports(force=args.force)
    else:
        seed_from_json(args.json, args.pdf_dir)

