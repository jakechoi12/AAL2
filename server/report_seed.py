"""
Report & Insight - Seed Data
Sample reports data for development and testing
"""

from datetime import date, datetime
from report_models import ReportDB, init_db, SessionLocal
import json

# Sample report data
SAMPLE_REPORTS = [
    # Global Research
    {
        "id": "RPT-GR001",
        "title": "Global Supply Chain Outlook 2025: Navigating Uncertainty",
        "category": "global_research",
        "organization": "McKinsey & Company",
        "published_date": date(2024, 12, 15),
        "summary": "This comprehensive report analyzes the evolving landscape of global supply chains in 2025, examining key disruptions, technological innovations, and strategic recommendations for businesses. The report covers major trends including nearshoring, AI-driven logistics optimization, and sustainable supply chain practices.",
        "tags": ["Supply Chain", "Logistics", "AI", "Sustainability", "Global Trade"],
        "pdf_url": "/reports/mckinsey_supply_chain_2025.pdf",
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
        "pdf_url": "/reports/bcg_maritime_decarbonization.pdf",
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
        "pdf_url": "/reports/deloitte_ecommerce_logistics.pdf",
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
        "pdf_url": "/reports/pwc_ai_logistics.pdf",
        "is_featured": True
    },
    {
        "id": "RPT-GR005",
        "title": "Global Trade Finance Report 2024",
        "category": "global_research",
        "organization": "World Economic Forum",
        "published_date": date(2024, 10, 30),
        "summary": "Analysis of global trade finance trends, including blockchain applications in trade documentation, supply chain financing innovations, and the impact of geopolitical tensions on trade credit availability.",
        "tags": ["Trade Finance", "Blockchain", "Global Trade", "Fintech"],
        "pdf_url": "/reports/wef_trade_finance_2024.pdf",
        "is_featured": False
    },
    {
        "id": "RPT-GR006",
        "title": "Cold Chain Logistics: Global Market Analysis and Forecasts",
        "category": "global_research",
        "organization": "KPMG",
        "published_date": date(2024, 10, 15),
        "summary": "Comprehensive analysis of the cold chain logistics market, covering pharmaceutical logistics, food supply chains, and the growing demand for temperature-controlled transportation in emerging markets.",
        "tags": ["Cold Chain", "Pharmaceutical", "Food Logistics", "Market Analysis"],
        "pdf_url": "/reports/kpmg_cold_chain.pdf",
        "is_featured": False
    },
    
    # Government Reports
    {
        "id": "RPT-GOV001",
        "title": "Korea Trade Statistics Annual Report 2024",
        "category": "government",
        "organization": "Korea Customs Service",
        "published_date": date(2024, 12, 20),
        "summary": "Official annual report on Korea's trade statistics including import/export volumes, major trading partners, commodity trends, and customs procedures. Includes detailed analysis of trade policy impacts and future outlook.",
        "tags": ["Korea", "Trade Statistics", "Customs", "Import Export"],
        "pdf_url": "/reports/kcs_trade_report_2024.pdf",
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
        "pdf_url": "/reports/usdot_freight_report.pdf",
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
        "pdf_url": "/reports/eu_green_logistics_2030.pdf",
        "is_featured": False
    },
    {
        "id": "RPT-GOV004",
        "title": "China Belt and Road Initiative: Infrastructure Progress Report",
        "category": "government",
        "organization": "Ministry of Commerce, China",
        "published_date": date(2024, 11, 5),
        "summary": "Progress report on the Belt and Road Initiative infrastructure projects, including railway corridors, port developments, and digital connectivity initiatives across participating countries.",
        "tags": ["China", "Belt and Road", "Infrastructure", "Trade Routes"],
        "pdf_url": "/reports/china_bri_progress.pdf",
        "is_featured": False
    },
    {
        "id": "RPT-GOV005",
        "title": "Japan Logistics Industry White Paper 2024",
        "category": "government",
        "organization": "Ministry of Land, Infrastructure, Transport and Tourism, Japan",
        "published_date": date(2024, 10, 25),
        "summary": "Official white paper on Japan's logistics industry, addressing labor shortages, automation adoption, regulatory reforms, and international competitiveness of Japanese logistics providers.",
        "tags": ["Japan", "Logistics", "White Paper", "Industry Analysis"],
        "pdf_url": "/reports/japan_logistics_whitepaper.pdf",
        "is_featured": False
    },
    {
        "id": "RPT-GOV006",
        "title": "Singapore Port Authority: Maritime Performance Report Q3 2024",
        "category": "government",
        "organization": "Maritime and Port Authority of Singapore",
        "published_date": date(2024, 10, 15),
        "summary": "Quarterly performance report of Singapore's maritime sector, including container throughput, vessel movements, transhipment volumes, and digital port initiatives.",
        "tags": ["Singapore", "Port", "Maritime", "Container Shipping"],
        "pdf_url": "/reports/mpa_singapore_q3_2024.pdf",
        "is_featured": False
    },
    
    # Company Reports
    {
        "id": "RPT-CO001",
        "title": "Maersk Sustainability Report 2024",
        "category": "company",
        "organization": "A.P. Moller - Maersk",
        "published_date": date(2024, 12, 18),
        "summary": "Annual sustainability report detailing Maersk's progress towards net-zero emissions, including methanol-powered vessel deployments, green corridor initiatives, and scope 3 emission reduction strategies.",
        "tags": ["Maersk", "Sustainability", "Shipping", "Net Zero", "ESG"],
        "pdf_url": "/reports/maersk_sustainability_2024.pdf",
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
        "pdf_url": "/reports/dhl_connectedness_2024.pdf",
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
        "pdf_url": "/reports/fedex_tech_innovation.pdf",
        "is_featured": False
    },
    {
        "id": "RPT-CO004",
        "title": "Amazon Logistics Network Expansion Strategy",
        "category": "company",
        "organization": "Amazon",
        "published_date": date(2024, 11, 10),
        "summary": "Strategic analysis of Amazon's logistics network expansion, including fulfillment center rollouts, delivery station optimization, and last-mile delivery innovations across global markets.",
        "tags": ["Amazon", "E-commerce", "Fulfillment", "Last-Mile"],
        "pdf_url": "/reports/amazon_logistics_strategy.pdf",
        "is_featured": False
    },
    {
        "id": "RPT-CO005",
        "title": "CMA CGM Group: Digital Transformation Journey",
        "category": "company",
        "organization": "CMA CGM",
        "published_date": date(2024, 10, 20),
        "summary": "Report on CMA CGM's digital transformation initiatives, covering e-commerce platforms, AI-powered cargo management, blockchain documentation, and sustainable shipping solutions.",
        "tags": ["CMA CGM", "Digital Transformation", "Shipping", "Technology"],
        "pdf_url": "/reports/cmacgm_digital_transformation.pdf",
        "is_featured": False
    },
    {
        "id": "RPT-CO006",
        "title": "UPS Supply Chain Solutions: Resilience Report 2024",
        "category": "company",
        "organization": "UPS",
        "published_date": date(2024, 10, 5),
        "summary": "Analysis of supply chain resilience strategies implemented by UPS, including risk management frameworks, inventory optimization techniques, and multi-modal transportation solutions.",
        "tags": ["UPS", "Supply Chain", "Resilience", "Risk Management"],
        "pdf_url": "/reports/ups_resilience_2024.pdf",
        "is_featured": False
    },
    {
        "id": "RPT-CO007",
        "title": "Flexport State of Global Freight Report",
        "category": "company",
        "organization": "Flexport",
        "published_date": date(2024, 9, 28),
        "summary": "Quarterly analysis of global freight market conditions, including ocean freight rates, air cargo capacity, trucking trends, and forward-looking indicators for supply chain professionals.",
        "tags": ["Flexport", "Freight", "Market Analysis", "Rates"],
        "pdf_url": "/reports/flexport_freight_report.pdf",
        "is_featured": False
    },
    {
        "id": "RPT-CO008",
        "title": "DB Schenker: Green Logistics Innovation Showcase",
        "category": "company",
        "organization": "DB Schenker",
        "published_date": date(2024, 9, 15),
        "summary": "Showcase of DB Schenker's green logistics innovations, including electric vehicle fleets, solar-powered warehouses, carbon-neutral shipping options, and sustainable packaging solutions.",
        "tags": ["DB Schenker", "Green Logistics", "Sustainability", "Innovation"],
        "pdf_url": "/reports/dbschenker_green_innovation.pdf",
        "is_featured": False
    }
]


def seed_reports():
    """Seed the database with sample reports"""
    init_db()
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing = db.query(ReportDB).count()
        if existing > 0:
            print(f"Database already contains {existing} reports. Skipping seed.")
            return
        
        # Insert sample reports
        for report_data in SAMPLE_REPORTS:
            tags = report_data.pop("tags", [])
            report = ReportDB(**report_data)
            report.set_tags(tags)
            db.add(report)
        
        db.commit()
        print(f"Successfully seeded {len(SAMPLE_REPORTS)} reports!")
        
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
        db.query(ReportDB).delete()
        db.commit()
        print("All reports cleared!")
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_reports()
    else:
        seed_reports()
