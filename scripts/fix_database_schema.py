# scripts/fix_database_schema.py
"""
Database Migration Script - Fixes schema issues
Run this once to update your existing database schema
"""

import sqlite3
import os
import logging

def migrate_database(db_path):
    """Migrate existing database to new schema"""
    
    print(f"🔧 Migrating database schema: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(btc_prices)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📊 Current columns: {columns}")
        
        # Add missing columns if they don't exist
        new_columns = [
            ('data_type', 'TEXT DEFAULT "historical"'),
            ('open_price', 'REAL'),
            ('close_price', 'REAL')
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE btc_prices ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    print(f"⚠️ Could not add {column_name}: {e}")
        
        # Create indexes if they don't exist
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON btc_prices(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_data_type ON btc_prices(data_type)",
            "CREATE INDEX IF NOT EXISTS idx_source ON btc_prices(source)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print("✅ Index created")
            except Exception as e:
                print(f"⚠️ Index creation warning: {e}")
        
        # Update existing records to have data_type
        cursor.execute("UPDATE btc_prices SET data_type = 'historical' WHERE data_type IS NULL")
        
        conn.commit()
        conn.close()
        
        print("✅ Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    # Find database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
    
    if os.path.exists(db_path):
        migrate_database(db_path)
    else:
        print(f"❌ Database not found: {db_path}")

if __name__ == "__main__":
    main()