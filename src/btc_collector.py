import requests
import sqlite3
import pandas as pd
import time
from datetime import datetime
import json

class BitcoinDataCollector:
    def __init__(self, db_path='bitcoin_data.db'):
        self.db_path = db_path
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        self.setup_database()
        
    def setup_database(self):
        """Create database and tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create price data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS btc_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                price REAL,
                volume REAL,
                high REAL,
                low REAL,
                source TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database initialized: {self.db_path}")
    
    def fetch_current_price(self):
        """Fetch current BTC price from CoinGecko"""
        try:
            print("Connecting to CoinGecko...")
            
            # Get current price data
            url = f"{self.coingecko_url}/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            print(f"CoinGecko response: {data}")
            
            btc_data = data['bitcoin']
            
            # Get additional market data
            market_url = f"{self.coingecko_url}/coins/bitcoin"
            market_response = requests.get(market_url, timeout=10)
            market_data = market_response.json()
            
            market_info = market_data['market_data']
            
            return {
                'timestamp': datetime.now(),
                'price': btc_data['usd'],
                'volume': btc_data.get('usd_24h_vol', 0),
                'high': market_info['high_24h']['usd'],
                'low': market_info['low_24h']['usd'],
                'source': 'coingecko'
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return None
        except KeyError as e:
            print(f"Data parsing error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def save_price(self, price_data):
        """Save price data to database"""
        if not price_data:
            return False
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert datetime to string to avoid deprecation warning
        timestamp_str = price_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO btc_prices (timestamp, price, volume, high, low, source)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            timestamp_str,
            price_data['price'],
            price_data['volume'],
            price_data['high'],
            price_data['low'],
            price_data['source']
        ))
        
        conn.commit()
        conn.close()
        return True
    
    def get_recent_prices(self, limit=10):
        """Get recent price data from database"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(f'''
            SELECT * FROM btc_prices 
            ORDER BY timestamp DESC 
            LIMIT {limit}
        ''', conn)
        conn.close()
        return df
    
    def collect_data_once(self):
        """Collect one data point"""
        print("Fetching Bitcoin price...")
        price_data = self.fetch_current_price()
        
        if price_data:
            success = self.save_price(price_data)
            if success:
                print(f"✅ BTC Price: ${price_data['price']:,.2f}")
                print(f"   Volume: {price_data['volume']:,.2f} BTC")
                print(f"   24h High: ${price_data['high']:,.2f}")
                print(f"   24h Low: ${price_data['low']:,.2f}")
                print(f"   Time: {price_data['timestamp']}")
                return True
            else:
                print("❌ Failed to save data")
                return False
        else:
            print("❌ Failed to fetch data")
            return False
    
    def start_continuous_collection(self, interval_seconds=60):
        """Start continuous data collection"""
        print(f"Starting continuous Bitcoin data collection (every {interval_seconds}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.collect_data_once()
                print(f"Waiting {interval_seconds} seconds...\n")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Data collection stopped by user")
        except Exception as e:
            print(f"\n❌ Error during collection: {e}")
    
    def show_statistics(self):
        """Show basic statistics of collected data"""
        df = self.get_recent_prices(100)  # Get last 100 records
        
        if len(df) == 0:
            print("No data collected yet")
            return
            
        print(f"\n📊 Bitcoin Data Statistics (Last {len(df)} records)")
        print(f"Current Price: ${df.iloc[0]['price']:,.2f}")
        print(f"Average Price: ${df['price'].mean():,.2f}")
        print(f"Highest Price: ${df['price'].max():,.2f}")
        print(f"Lowest Price: ${df['price'].min():,.2f}")
        print(f"Price Range: ${df['price'].max() - df['price'].min():,.2f}")
        print(f"Data collected from: {df.iloc[-1]['timestamp']} to {df.iloc[0]['timestamp']}")


if __name__ == "__main__":
    # Create collector instance
    collector = BitcoinDataCollector()
    
    print("🚀 Bitcoin Data Collector")
    print("=" * 40)
    
    # Show menu
    while True:
        print("\nOptions:")
        print("1. Collect single price point")
        print("2. Start continuous collection (60s intervals)")
        print("3. Show recent data")
        print("4. Show statistics")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            collector.collect_data_once()
            
        elif choice == '2':
            interval = input("Enter interval in seconds (default 60): ").strip()
            interval = int(interval) if interval.isdigit() else 60
            collector.start_continuous_collection(interval)
            
        elif choice == '3':
            print("\n📋 Recent Bitcoin Prices:")
            df = collector.get_recent_prices(5)
            if len(df) > 0:
                for _, row in df.iterrows():
                    print(f"${row['price']:,.2f} at {row['timestamp']}")
            else:
                print("No data available")
                
        elif choice == '4':
            collector.show_statistics()
            
        elif choice == '5':
            print("👋 Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")