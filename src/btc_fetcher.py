import requests
import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import json
import numpy as np

class ComprehensiveBitcoinDataFetcher:
    def __init__(self, db_path=None):
        """Enhanced Bitcoin data fetcher for complete historical data"""
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
        self.ensure_database()
        
        # Rate limiting for APIs
        self.last_request_time = {}
        self.request_delays = {
            'coingecko': 10,  # 10 seconds between requests
            'cryptocompare': 1,  # 1 second between requests
            'yahoo': 0.5,  # 0.5 seconds between requests
            'binance': 0.1   # 0.1 seconds between requests
        }
        
    def ensure_database(self):
        """Ensure database and table exist with enhanced schema"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced table with more data points
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS btc_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT UNIQUE,
                price REAL,
                volume REAL,
                high REAL,
                low REAL,
                open REAL,
                close REAL,
                market_cap REAL,
                source TEXT,
                timeframe TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON btc_prices(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON btc_prices(source)')
        
        conn.commit()
        conn.close()
    
    def rate_limit(self, source):
        """Implement rate limiting for API calls"""
        if source in self.last_request_time:
            elapsed = time.time() - self.last_request_time[source]
            required_delay = self.request_delays.get(source, 1)
            if elapsed < required_delay:
                sleep_time = required_delay - elapsed
                print(f"⏳ Rate limiting {source}: waiting {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        self.last_request_time[source] = time.time()
    
    def fetch_coingecko_max_history(self):
        """Fetch maximum available Bitcoin history from CoinGecko (since 2013)"""
        print("🔄 Fetching ALL Bitcoin history from CoinGecko (2013-present)...")
        
        try:
            self.rate_limit('coingecko')
            
            # CoinGecko max history endpoint
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': 'max',  # Maximum available data
                'interval': 'daily'  # Daily intervals for max range
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Process the data
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            market_caps = data.get('market_caps', [])
            
            historical_data = []
            print(f"📊 Processing {len(prices)} data points from CoinGecko...")
            
            for i, (timestamp_ms, price) in enumerate(prices):
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                
                # Get corresponding volume and market cap
                volume = volumes[i][1] if i < len(volumes) else 0
                market_cap = market_caps[i][1] if i < len(market_caps) else 0
                
                historical_data.append({
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'price': price,
                    'volume': volume,
                    'high': price * 1.01,  # Estimated high (CoinGecko daily doesn't provide OHLC)
                    'low': price * 0.99,   # Estimated low
                    'open': price,         # Use price as open
                    'close': price,        # Use price as close
                    'market_cap': market_cap,
                    'source': 'coingecko_max',
                    'timeframe': 'daily'
                })
            
            print(f"✅ CoinGecko: Fetched {len(historical_data)} days of Bitcoin history")
            print(f"   Date range: {historical_data[0]['timestamp']} to {historical_data[-1]['timestamp']}")
            return historical_data
            
        except Exception as e:
            print(f"❌ CoinGecko max history failed: {e}")
            return None
    
    def fetch_cryptocompare_max_history(self):
        """Fetch maximum Bitcoin history from CryptoCompare"""
        print("🔄 Fetching extended Bitcoin history from CryptoCompare...")
        
        all_data = []
        
        try:
            # Fetch daily data in chunks (CryptoCompare limit: 2000 days per request)
            end_time = int(datetime.now().timestamp())
            
            # Start from 2010 (Bitcoin's early days)
            start_date = datetime(2010, 1, 1)
            current_time = end_time
            
            chunk_count = 0
            while current_time > start_date.timestamp() and chunk_count < 10:  # Safety limit
                self.rate_limit('cryptocompare')
                
                url = "https://min-api.cryptocompare.com/data/v2/histoday"
                params = {
                    'fsym': 'BTC',
                    'tsym': 'USD',
                    'limit': 2000,  # Maximum allowed
                    'toTs': int(current_time)
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if data['Response'] != 'Success':
                    print(f"❌ CryptoCompare error: {data.get('Message', 'Unknown error')}")
                    break
                
                chunk_data = data['Data']['Data']
                print(f"📊 CryptoCompare chunk {chunk_count + 1}: {len(chunk_data)} days")
                
                for item in chunk_data:
                    timestamp = datetime.fromtimestamp(item['time'])
                    
                    all_data.append({
                        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'price': float(item['close']),
                        'volume': float(item['volumeto']),
                        'high': float(item['high']),
                        'low': float(item['low']),
                        'open': float(item['open']),
                        'close': float(item['close']),
                        'market_cap': 0,  # Not available
                        'source': 'cryptocompare_max',
                        'timeframe': 'daily'
                    })
                
                # Move to earlier time period
                current_time = chunk_data[0]['time'] - 86400  # Go back one day
                chunk_count += 1
            
            # Sort by timestamp (oldest first)
            all_data.sort(key=lambda x: x['timestamp'])
            
            print(f"✅ CryptoCompare: Fetched {len(all_data)} days total")
            if all_data:
                print(f"   Date range: {all_data[0]['timestamp']} to {all_data[-1]['timestamp']}")
            
            return all_data
            
        except Exception as e:
            print(f"❌ CryptoCompare max history failed: {e}")
            return None
    
    def fetch_yahoo_max_history(self):
        """Fetch Bitcoin history from Yahoo Finance"""
        print("🔄 Fetching Bitcoin history from Yahoo Finance...")
        
        try:
            import yfinance as yf
            
            # Download maximum available Bitcoin data
            ticker = yf.Ticker("BTC-USD")
            
            # Get max available history
            hist = ticker.history(period="max", interval="1d")
            
            if hist.empty:
                print("❌ No data from Yahoo Finance")
                return None
            
            historical_data = []
            for timestamp, row in hist.iterrows():
                historical_data.append({
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'price': float(row['Close']),
                    'volume': float(row['Volume']) if not pd.isna(row['Volume']) else 0,
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'open': float(row['Open']),
                    'close': float(row['Close']),
                    'market_cap': 0,  # Not available
                    'source': 'yahoo_max',
                    'timeframe': 'daily'
                })
            
            print(f"✅ Yahoo Finance: {len(historical_data)} days")
            print(f"   Date range: {historical_data[0]['timestamp']} to {historical_data[-1]['timestamp']}")
            return historical_data
            
        except ImportError:
            print("❌ yfinance not installed. Install with: pip install yfinance")
            return None
        except Exception as e:
            print(f"❌ Yahoo Finance failed: {e}")
            return None
    
    def fetch_binance_history(self, days=1000):
        """Fetch recent Bitcoin history from Binance (high quality, recent data)"""
        print(f"🔄 Fetching recent {days} days from Binance...")
        
        try:
            # Binance klines endpoint for BTCUSDT
            url = "https://api.binance.com/api/v3/klines"
            
            # Calculate start time
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = end_time - (days * 24 * 60 * 60 * 1000)
            
            params = {
                'symbol': 'BTCUSDT',
                'interval': '1d',  # Daily intervals
                'startTime': start_time,
                'endTime': end_time,
                'limit': 1000  # Binance limit
            }
            
            self.rate_limit('binance')
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            historical_data = []
            for item in data:
                timestamp = datetime.fromtimestamp(int(item[0]) / 1000)
                
                historical_data.append({
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'price': float(item[4]),  # Close price
                    'volume': float(item[5]),  # Volume
                    'high': float(item[2]),   # High
                    'low': float(item[3]),    # Low
                    'open': float(item[1]),   # Open
                    'close': float(item[4]),  # Close
                    'market_cap': 0,  # Not available
                    'source': 'binance',
                    'timeframe': 'daily'
                })
            
            print(f"✅ Binance: {len(historical_data)} days of high-quality data")
            return historical_data
            
        except Exception as e:
            print(f"❌ Binance failed: {e}")
            return None
    
    def save_historical_data(self, historical_data, replace_existing=False):
        """Save historical data to database with duplicate handling"""
        if not historical_data:
            print("❌ No data to save")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if replace_existing:
            print("🗑️ Clearing existing data...")
            cursor.execute("DELETE FROM btc_prices")
        
        print(f"💾 Saving {len(historical_data)} historical records...")
        
        saved_count = 0
        duplicate_count = 0
        error_count = 0
        
        for data_point in historical_data:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO btc_prices 
                    (timestamp, price, volume, high, low, open, close, market_cap, source, timeframe)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data_point['timestamp'],
                    data_point['price'],
                    data_point['volume'],
                    data_point['high'],
                    data_point['low'],
                    data_point['open'],
                    data_point['close'],
                    data_point['market_cap'],
                    data_point['source'],
                    data_point['timeframe']
                ))
                
                if cursor.rowcount > 0:
                    saved_count += 1
                else:
                    duplicate_count += 1
                    
            except Exception as e:
                error_count += 1
                if error_count < 5:  # Only show first few errors
                    print(f"⚠️ Error saving record: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database update complete:")
        print(f"   💾 Saved: {saved_count} new records")
        print(f"   🔄 Duplicates skipped: {duplicate_count}")
        if error_count > 0:
            print(f"   ❌ Errors: {error_count}")
        
        return saved_count > 0
    
    def get_data_summary(self):
        """Get comprehensive summary of stored data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute('SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM btc_prices')
        total, earliest, latest = cursor.fetchone()
        
        # By source
        cursor.execute('''
            SELECT source, COUNT(*), MIN(timestamp), MAX(timestamp) 
            FROM btc_prices 
            GROUP BY source 
            ORDER BY COUNT(*) DESC
        ''')
        sources = cursor.fetchall()
        
        # Price stats
        cursor.execute('SELECT MIN(price), MAX(price), AVG(price) FROM btc_prices WHERE price > 0')
        min_price, max_price, avg_price = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_records': total,
            'earliest_date': earliest,
            'latest_date': latest,
            'sources': sources,
            'price_stats': {
                'min': min_price,
                'max': max_price,
                'average': avg_price
            }
        }
    
    def fetch_complete_bitcoin_history(self, replace_existing=False):
        """Fetch complete Bitcoin history from all available sources"""
        print("🚀 Fetching COMPLETE Bitcoin History")
        print("=" * 50)
        print("This will fetch Bitcoin price data from:")
        print("📊 CoinGecko: 2013-present (daily)")
        print("📊 CryptoCompare: 2010-present (daily)")
        print("📊 Yahoo Finance: Available range")
        print("📊 Binance: Recent 1000 days (high quality)")
        print()
        
        if not replace_existing:
            current_summary = self.get_data_summary()
            if current_summary['total_records'] > 0:
                print(f"📈 Current database: {current_summary['total_records']} records")
                print(f"   Range: {current_summary['earliest_date']} to {current_summary['latest_date']}")
                
                choice = input("\nContinue and add new data? (y/N): ").lower().strip()
                if choice != 'y':
                    print("❌ Cancelled")
                    return
        
        print("\n🔄 Starting comprehensive data fetch...")
        
        # Track all fetched data
        all_sources_data = []
        
        # 1. CoinGecko (longest history)
        coingecko_data = self.fetch_coingecko_max_history()
        if coingecko_data:
            all_sources_data.extend(coingecko_data)
            print(f"✅ Added {len(coingecko_data)} CoinGecko records")
        
        # 2. CryptoCompare (comprehensive)
        cryptocompare_data = self.fetch_cryptocompare_max_history()
        if cryptocompare_data:
            all_sources_data.extend(cryptocompare_data)
            print(f"✅ Added {len(cryptocompare_data)} CryptoCompare records")
        
        # 3. Yahoo Finance
        yahoo_data = self.fetch_yahoo_max_history()
        if yahoo_data:
            all_sources_data.extend(yahoo_data)
            print(f"✅ Added {len(yahoo_data)} Yahoo Finance records")
        
        # 4. Binance (recent high-quality data)
        binance_data = self.fetch_binance_history(1000)
        if binance_data:
            all_sources_data.extend(binance_data)
            print(f"✅ Added {len(binance_data)} Binance records")
        
        if not all_sources_data:
            print("❌ No data fetched from any source")
            return False
        
        print(f"\n💾 Total data points to save: {len(all_sources_data)}")
        
        # Save all data
        success = self.save_historical_data(all_sources_data, replace_existing)
        
        if success:
            # Show final summary
            final_summary = self.get_data_summary()
            print(f"\n🎉 Complete Bitcoin History Fetch Successful!")
            print(f"📊 Total Records: {final_summary['total_records']:,}")
            print(f"📅 Date Range: {final_summary['earliest_date']} to {final_summary['latest_date']}")
            print(f"💰 Price Range: ${final_summary['price_stats']['min']:,.2f} to ${final_summary['price_stats']['max']:,.2f}")
            print(f"📈 Average Price: ${final_summary['price_stats']['average']:,.2f}")
            
            print(f"\n📊 Data Sources:")
            for source, count, min_date, max_date in final_summary['sources']:
                print(f"   {source}: {count:,} records ({min_date} to {max_date})")
            
            # Calculate coverage
            if final_summary['earliest_date'] and final_summary['latest_date']:
                start_date = datetime.strptime(final_summary['earliest_date'], '%Y-%m-%d %H:%M:%S')
                end_date = datetime.strptime(final_summary['latest_date'], '%Y-%m-%d %H:%M:%S')
                coverage_days = (end_date - start_date).days
                print(f"\n⏱️ Total Coverage: {coverage_days:,} days")
            
            print(f"\n✅ Your Odin trading bot now has access to COMPLETE Bitcoin history!")
            print(f"🎯 Strategies can now analyze across ALL market cycles")
            print(f"📈 Backtesting available across entire Bitcoin timeline")
            
        return success

def main():
    """Main function to fetch complete Bitcoin history"""
    print("📊 Odin - Complete Bitcoin Historical Data Fetcher")
    print("=" * 60)
    
    fetcher = ComprehensiveBitcoinDataFetcher()
    
    # Show menu
    while True:
        print(f"\n📊 Bitcoin Data Fetcher Menu:")
        print("1. 🚀 Fetch COMPLETE Bitcoin History (All Sources)")
        print("2. 📈 Fetch CoinGecko Max History Only")
        print("3. 🔄 Fetch CryptoCompare Extended History")
        print("4. 📊 Fetch Recent Binance Data (1000 days)")
        print("5. 📋 View Current Database Summary")
        print("6. 🗑️ Replace All Existing Data")
        print("7. 🛑 Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            fetcher.fetch_complete_bitcoin_history()
            
        elif choice == '2':
            data = fetcher.fetch_coingecko_max_history()
            if data:
                fetcher.save_historical_data(data)
                
        elif choice == '3':
            data = fetcher.fetch_cryptocompare_max_history()
            if data:
                fetcher.save_historical_data(data)
                
        elif choice == '4':
            days = input("Days to fetch (default 1000): ").strip()
            days = int(days) if days.isdigit() else 1000
            data = fetcher.fetch_binance_history(days)
            if data:
                fetcher.save_historical_data(data)
                
        elif choice == '5':
            summary = fetcher.get_data_summary()
            print(f"\n📊 Database Summary:")
            print(f"   Total Records: {summary['total_records']:,}")
            print(f"   Date Range: {summary['earliest_date']} to {summary['latest_date']}")
            if summary['price_stats']['min']:
                print(f"   Price Range: ${summary['price_stats']['min']:,.2f} to ${summary['price_stats']['max']:,.2f}")
            print(f"\n📊 By Source:")
            for source, count, min_date, max_date in summary['sources']:
                print(f"   {source}: {count:,} records")
                
        elif choice == '6':
            confirm = input("⚠️ This will DELETE all existing data. Continue? (y/N): ").lower().strip()
            if confirm == 'y':
                fetcher.fetch_complete_bitcoin_history(replace_existing=True)
            else:
                print("❌ Cancelled")
                
        elif choice == '7':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()