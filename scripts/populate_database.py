#!/usr/bin/env python3
"""
Simple Database Population Script - Windows Compatible
Populates database with sample Bitcoin price data for testing.
"""

import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Simple imports to avoid dependency issues
try:
    from odin.core.repository import get_repository_manager, save_price_data
    REPO_AVAILABLE = True
except ImportError:
    REPO_AVAILABLE = False
    print("Repository system not available")

async def create_sample_data():
    """Create sample Bitcoin price data."""
    if not REPO_AVAILABLE:
        print("Cannot populate database - repository system not available")
        return False
    
    try:
        print("Creating sample Bitcoin price data...")
        
        # Create sample price data for the last 30 days
        base_price = 42000.0  # Starting price
        current_time = datetime.now()
        
        sample_data = []
        for i in range(30):
            # Create timestamp (30 days ago to now)
            timestamp = current_time - timedelta(days=30-i)
            
            # Simulate realistic price movement (small random changes)
            import random
            price_change = random.uniform(-0.05, 0.05)  # +/- 5% daily
            base_price *= (1 + price_change)
            
            # Keep price in reasonable range
            base_price = max(30000, min(70000, base_price))
            
            price_data = {
                "timestamp": timestamp,
                "price": round(base_price, 2),
                "volume": random.uniform(1000000, 5000000),
                "source": "sample_data"
            }
            
            sample_data.append(price_data)
        
        # Save to database
        success_count = 0
        for data in sample_data:
            if await save_price_data(data):
                success_count += 1
        
        print(f"Successfully saved {success_count}/{len(sample_data)} price records")
        
        # Verify data was saved
        repo_manager = await get_repository_manager()
        stats = await repo_manager.get_stats()
        print(f"Database now contains {stats.get('price_records', 0)} price records")
        
        return success_count > 0
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        return False

async def main():
    """Main function."""
    print("Simple Database Population Script")
    print("=" * 40)
    
    if not REPO_AVAILABLE:
        print("Repository system not available. Please ensure:")
        print("1. odin/core/repository.py exists")
        print("2. All dependencies are installed")
        return
    
    try:
        success = await create_sample_data()
        
        if success:
            print("\nDatabase population completed successfully!")
            print("You can now run the CLI with sample data:")
            print("python odin_cli.py")
        else:
            print("\nDatabase population failed!")
            
    except Exception as e:
        print(f"Script failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())