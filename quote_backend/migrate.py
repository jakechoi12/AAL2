"""
Database Migration Script
새로운 테이블 추가 및 스키마 변경
"""

import sqlite3
from datetime import datetime


def run_migration():
    """Execute database migrations"""
    conn = sqlite3.connect('quote.db')
    cursor = conn.cursor()
    
    # Contract table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_no VARCHAR(20) UNIQUE NOT NULL,
            bidding_id INTEGER NOT NULL,
            awarded_bid_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            forwarder_id INTEGER NOT NULL,
            total_amount_krw DECIMAL(15, 0) NOT NULL,
            freight_charge DECIMAL(15, 2),
            local_charge DECIMAL(15, 2),
            other_charge DECIMAL(15, 2),
            transit_time VARCHAR(50),
            carrier VARCHAR(100),
            contract_terms TEXT,
            shipper_confirmed BOOLEAN DEFAULT 0,
            shipper_confirmed_at DATETIME,
            forwarder_confirmed BOOLEAN DEFAULT 0,
            forwarder_confirmed_at DATETIME,
            status VARCHAR(20) DEFAULT 'pending',
            confirmed_at DATETIME,
            cancelled_by VARCHAR(20),
            cancelled_at DATETIME,
            cancel_reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bidding_id) REFERENCES biddings(id),
            FOREIGN KEY (awarded_bid_id) REFERENCES bids(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (forwarder_id) REFERENCES forwarders(id)
        )
    """)
    print("Created contracts table")
    
    # Shipment table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_no VARCHAR(20) UNIQUE NOT NULL,
            contract_id INTEGER NOT NULL,
            current_status VARCHAR(30) DEFAULT 'booked',
            current_location VARCHAR(200),
            estimated_pickup DATETIME,
            actual_pickup DATETIME,
            estimated_delivery DATETIME,
            actual_delivery DATETIME,
            bl_no VARCHAR(50),
            vessel_flight VARCHAR(100),
            delivery_confirmed BOOLEAN DEFAULT 0,
            delivery_confirmed_at DATETIME,
            auto_confirmed BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES contracts(id)
        )
    """)
    print("Created shipments table")
    
    # Shipment Tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipment_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_id INTEGER NOT NULL,
            status VARCHAR(30) NOT NULL,
            location VARCHAR(200),
            remark TEXT,
            updated_by_type VARCHAR(20) NOT NULL,
            updated_by_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shipment_id) REFERENCES shipments(id)
        )
    """)
    print("Created shipment_tracking table")
    
    # Settlement table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            settlement_no VARCHAR(20) UNIQUE NOT NULL,
            contract_id INTEGER NOT NULL,
            forwarder_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            total_amount_krw DECIMAL(15, 0) NOT NULL,
            service_fee DECIMAL(15, 0) DEFAULT 0,
            net_amount DECIMAL(15, 0) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            requested_at DATETIME,
            completed_at DATETIME,
            payment_method VARCHAR(50),
            payment_reference VARCHAR(100),
            remark TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES contracts(id),
            FOREIGN KEY (forwarder_id) REFERENCES forwarders(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    print("Created settlements table")
    
    # Message table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bidding_id INTEGER NOT NULL,
            sender_type VARCHAR(20) NOT NULL,
            sender_id INTEGER NOT NULL,
            recipient_type VARCHAR(20) NOT NULL,
            recipient_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            read_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bidding_id) REFERENCES biddings(id)
        )
    """)
    print("Created messages table")
    
    # Favorite Routes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorite_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            pol VARCHAR(50) NOT NULL,
            pod VARCHAR(50) NOT NULL,
            shipping_type VARCHAR(20),
            alias VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    print("Created favorite_routes table")
    
    # Bid Templates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bid_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forwarder_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            pol VARCHAR(50),
            pod VARCHAR(50),
            shipping_type VARCHAR(20),
            base_freight DECIMAL(15, 2),
            base_local DECIMAL(15, 2),
            base_other DECIMAL(15, 2),
            transit_time VARCHAR(50),
            carrier VARCHAR(100),
            default_remark TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (forwarder_id) REFERENCES forwarders(id)
        )
    """)
    print("Created bid_templates table")
    
    # Bookmarked Biddings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarked_biddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forwarder_id INTEGER NOT NULL,
            bidding_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (forwarder_id) REFERENCES forwarders(id),
            FOREIGN KEY (bidding_id) REFERENCES biddings(id)
        )
    """)
    print("Created bookmarked_biddings table")
    
    # Ocean Rate Sheets table (Quick Quotation 용)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ocean_rate_sheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pol_id INTEGER NOT NULL,
            pod_id INTEGER NOT NULL,
            carrier VARCHAR(100) DEFAULT 'HMM' NOT NULL,
            valid_from DATETIME NOT NULL,
            valid_to DATETIME NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            remark TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pol_id) REFERENCES ports(id),
            FOREIGN KEY (pod_id) REFERENCES ports(id)
        )
    """)
    print("Created ocean_rate_sheets table")
    
    # Ocean Rate Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ocean_rate_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sheet_id INTEGER NOT NULL,
            container_type_id INTEGER NOT NULL,
            freight_code_id INTEGER NOT NULL,
            freight_group VARCHAR(50) NOT NULL,
            unit VARCHAR(10) NOT NULL,
            currency VARCHAR(3) NOT NULL,
            rate DECIMAL(15, 2),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sheet_id) REFERENCES ocean_rate_sheets(id),
            FOREIGN KEY (container_type_id) REFERENCES container_types(id),
            FOREIGN KEY (freight_code_id) REFERENCES freight_codes(id)
        )
    """)
    print("Created ocean_rate_items table")
    
    # Trucking Rates table (내륙 운송 운임)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trucking_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cargo_type VARCHAR(20) DEFAULT '일반화물' NOT NULL,
            origin_port_id INTEGER NOT NULL,
            dest_province VARCHAR(50) NOT NULL,
            dest_city VARCHAR(50) NOT NULL,
            dest_district VARCHAR(50) NOT NULL,
            distance_km INTEGER,
            rate_20ft DECIMAL(15, 0),
            rate_40ft DECIMAL(15, 0),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (origin_port_id) REFERENCES ports(id)
        )
    """)
    print("Created trucking_rates table")
    
    # Create index for trucking_rates table
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_trucking_rates_origin 
        ON trucking_rates(origin_port_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_trucking_rates_dest 
        ON trucking_rates(dest_province, dest_city)
    """)
    print("Created indexes for trucking_rates table")
    
    # Add abbreviation column to container_types table if not exists
    try:
        cursor.execute("ALTER TABLE container_types ADD COLUMN abbreviation VARCHAR(20)")
        print("Added abbreviation column to container_types table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("abbreviation column already exists in container_types table")
        else:
            print(f"Note: {e}")
    
    # Add abbreviation column to truck_types table if not exists
    try:
        cursor.execute("ALTER TABLE truck_types ADD COLUMN abbreviation VARCHAR(20)")
        print("Added abbreviation column to truck_types table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("abbreviation column already exists in truck_types table")
        else:
            print(f"Note: {e}")
    
    conn.commit()
    conn.close()
    print("\nMigration completed successfully!")


if __name__ == "__main__":
    run_migration()
