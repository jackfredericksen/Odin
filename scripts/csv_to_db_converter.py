#!/usr/bin/env python3
"""
Bitcoin CSV to Database Converter
Converts the historical Bitcoin CSV data to the bitcoin_data.db format
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import numpy as np

def convert_csv_to_db(csv_file_path, db_path=None, sample_rate_hours=1):
    """
    Convert Bitcoin CSV data to database format
    
    Args:
        csv_file_path (str): Path to the CSV file
        db_path (str): Path to the database (optional)
        sample_rate_hours (int): How many hours between data points (1=hourly, 24=daily)
    """
    
    # Set up database path
    if db_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir) if 'scripts' in current_dir else current_dir
        db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    print(f"📊 Converting Bitcoin CSV data to database")
    print(f"   CSV file: {csv_file_path}")
    print(f"   Database: {db_path}")
    print(f"   Sample rate: Every {sample_rate_hours} hour(s)")
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_file_path)
        print(f"✅ Loaded {len(df)} records from CSV")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False
    
    # Display CSV structure
    print(f"   Columns: {list(df.columns)}")
    print(f"   Date range: {df['Start'].iloc[-1]} to {df['End'].iloc[0]}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table (drop existing if it exists)
    cursor.execute('DROP TABLE IF EXISTS btc_prices')
    cursor.execute('''
        CREATE TABLE btc_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            price REAL,
            volume REAL,
            high REAL,
            low REAL,
            source TEXT
        )
    ''')
    
    # Process each day in the CSV
    records_inserted = 0
    
    for index, row in df.iterrows():
        try:
            # Parse start and end dates
            start_date = datetime.strptime(row['Start'], '%Y-%m-%d')
            end_date = datetime.strptime(row['End'], '%Y-%m-%d')
            
            # Generate hourly data points for this day
            current_time = start_date
            while current_time <= end_date:
                # Calculate intraday price (simulate price movement within the day)
                # Use a random walk between open and close prices
                day_progress = (current_time - start_date).total_seconds() / 86400  # 0 to 1
                
                # Simple linear interpolation with some randomness
                base_price = row['Open'] + (row['Close'] - row['Open']) * day_progress
                
                # Add some realistic intraday volatility (±2% random walk)
                volatility_factor = 1 + np.random.normal(0, 0.02)
                price = base_price * volatility_factor
                
                # Ensure price stays within daily high/low bounds
                price = max(min(price, row['High']), row['Low'])
                
                # Create timestamp string
                timestamp_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Insert record
                cursor.execute('''
                    INSERT INTO btc_prices (timestamp, price, volume, high, low, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp_str,
                    price,
                    row['Volume'],
                    row['High'],
                    row['Low'],
                    'csv_import'
                ))
                
                records_inserted += 1
                current_time += timedelta(hours=sample_rate_hours)
            
            # Progress update every 100 days
            if index % 100 == 0:
                print(f"   Processed {index}/{len(df)} days...")
                
        except Exception as e:
            print(f"⚠️ Error processing row {index}: {e}")
            continue
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"✅ Conversion complete!")
    print(f"   Records inserted: {records_inserted:,}")
    print(f"   Database file: {db_path}")
    print(f"   File size: {os.path.getsize(db_path) / 1024 / 1024:.1f} MB")
    
    return True


def verify_database(db_path=None):
    """Verify the converted database"""
    
    if db_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir) if 'scripts' in current_dir else current_dir
        db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    
    # Get basic stats
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM btc_prices")
    total_records = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM btc_prices")
    date_range = cursor.fetchone()
    
    cursor.execute("SELECT MIN(price), MAX(price), AVG(price) FROM btc_prices")
    price_stats = cursor.fetchone()
    
    cursor.execute("SELECT source, COUNT(*) FROM btc_prices GROUP BY source")
    sources = cursor.fetchall()
    
    # Get recent records
    cursor.execute("SELECT * FROM btc_prices ORDER BY timestamp DESC LIMIT 5")
    recent_records = cursor.fetchall()
    
    conn.close()
    
    print(f"📊 Database Verification:")
    print(f"   Total records: {total_records:,}")
    print(f"   Date range: {date_range[0]} to {date_range[1]}")
    print(f"   Price range: ${price_stats[0]:,.2f} to ${price_stats[1]:,.2f}")
    print(f"   Average price: ${price_stats[2]:,.2f}")
    print(f"   Data sources: {dict(sources)}")
    
    print(f"\n📋 Recent records:")
    for record in recent_records:
        print(f"   {record[1]}: ${record[2]:,.2f}")
    
    return True


def main():
    """Main conversion function"""
    print("🚀 Bitcoin CSV to Database Converter")
    print("=" * 50)
    
    # Get current working directory and script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    working_dir = os.getcwd()
    
    print(f"📁 Script directory: {current_dir}")
    print(f"📁 Working directory: {working_dir}")
    
    # Look for CSV file in multiple locations
    csv_candidates = [
        # In script directory
        os.path.join(current_dir, 'bitcoin_20080225_20250525.csv'),
        # In working directory
        os.path.join(working_dir, 'bitcoin_20080225_20250525.csv'),
        # In parent of script directory
        os.path.join(os.path.dirname(current_dir), 'bitcoin_20080225_20250525.csv'),
        # Just the filename (current directory)
        'bitcoin_20080225_20250525.csv'
    ]
    
    csv_file = None
    print("\n🔍 Looking for CSV file...")
    for candidate in csv_candidates:
        abs_path = os.path.abspath(candidate)
        print(f"   Checking: {abs_path}")
        if os.path.exists(candidate):
            csv_file = candidate
            print(f"   ✅ Found: {abs_path}")
            break
        else:
            print(f"   ❌ Not found")
    
    if not csv_file:
        print("\n❌ CSV file not found!")
        print("   Please ensure 'bitcoin_20080225_20250525.csv' is in one of these locations:")
        for candidate in csv_candidates:
            print(f"     {os.path.abspath(candidate)}")
        print("\n💡 Try copying the CSV file to the same directory as this script")
        return
    
    # Determine project root and database path
    if 'scripts' in current_dir:
        project_root = os.path.dirname(current_dir)
    else:
        project_root = current_dir
    
    db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
    
    print(f"\n📊 Conversion plan:")
    print(f"   CSV file: {os.path.abspath(csv_file)}")
    print(f"   Database: {os.path.abspath(db_path)}")
    print(f"   Project root: {project_root}")
    
    # Check if database exists
    if os.path.exists(db_path):
        try:
            response = input(f"\nDatabase exists. Overwrite? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
        except KeyboardInterrupt:
            print("\nCancelled by user.")
            return
    
    # Check for required modules
    try:
        import pandas as pd
        import numpy as np
        print("✅ Required modules available")
    except ImportError as e:
        print(f"❌ Missing required module: {e}")
        print("   Install with: pip install pandas numpy")
        return
    
    # Convert CSV to database
    print(f"\n🚀 Starting conversion...")
    success = convert_csv_to_db(csv_file, db_path, sample_rate_hours=1)
    
    if success:
        # Verify the conversion
        print(f"\n🔍 Verifying conversion...")
        verify_database(db_path)
        
        print(f"\n🎉 Ready to use!")
        print(f"   Your bitcoin_data.db now contains 17+ years of Bitcoin data")
        print(f"   Run your trading bot: python src/api_server.py")
        print(f"   Test strategy: python strategies/ma_crossover.py")
    else:
        print(f"❌ Conversion failed")


if __name__ == "__main__":
    main()