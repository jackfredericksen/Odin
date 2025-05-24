import requests
import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import json

class HistoricalDataFetcher:
    def __init__(self, db_path=None):
        # Set up database path
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
        self.ensure_database()
    
    def ensure_database(self):
        """Ensure database and table exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS btc_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                price REAL,
                volume REAL,
                high REAL,
                low REAL,
                source TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def fetch_coingecko_data(self, days=90):
        """Fetch historical data from CoinGecko"""
        print(f"🔄 Fetching {days} days of Bitcoin data from CoinGecko...")
        
        try:
            # CoinGecko API for historical market data
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'hourly' if days <= 90 else 'daily'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract price, volume data
            prices = data['prices']
            volumes = data['total_volumes']
            
            historical_data = []
            for i, (timestamp_ms, price) in enumerate(prices):
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                volume = volumes[i][1] if i < len(volumes) else 0
                
                # Estimate high/low (CoinGecko doesn't provide OHLC for free)
                # Use price +/- 1% as rough estimate
                high = price * 1.01
                low = price * 0.99
                
                historical_data.append({
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'price': price,
                    'volume': volume,
                    'high': high,
                    'low': low,
                    'source': 'coingecko_historical'
                })
            
            return historical_data
            
        except Exception as e:
            print(f"❌ CoinGecko fetch failed: {e}")
            return None
    
    def fetch_yahoo_finance_data(self, days=90):
        """Fetch historical data using yfinance"""
        try:
            import yfinance as yf
            print(f"🔄 Fetching {days} days of Bitcoin data from Yahoo Finance...")
            
            # Download Bitcoin data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            btc = yf.download('BTC-USD', start=start_date, end=end_date, interval='1h')
            
            historical_data = []
            for timestamp, row in btc.iterrows():
                historical_data.append({
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'price': float(row['Close']),
                    'volume': float(row['Volume']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'source': 'yahoo_finance'
                })
            
            return historical_data
            
        except ImportError:
            print("❌ yfinance not installed. Install with: pip install yfinance")
            return None
        except Exception as e:
            print(f"❌ Yahoo Finance fetch failed: {e}")
            return None
    
    def fetch_cryptocompare_data(self, days=90):
        """Fetch historical data from CryptoCompare"""
        print(f"🔄 Fetching {days} days of Bitcoin data from CryptoCompare...")
        
        try:
            # CryptoCompare API for hourly data
            hours = min(days * 24, 2000)  # API limit
            url = "https://min-api.cryptocompare.com/data/v2/histohour"
            params = {
                'fsym': 'BTC',
                'tsym': 'USD',
                'limit': hours
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data['Response'] != 'Success':
                raise Exception(f"API Error: {data.get('Message', 'Unknown error')}")
            
            historical_data = []
            for item in data['Data']['Data']:
                timestamp = datetime.fromtimestamp(item['time'])
                
                historical_data.append({
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'price': float(item['close']),
                    'volume': float(item['volumeto']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'source': 'cryptocompare'
                })
            
            return historical_data
            
        except Exception as e:
            print(f"❌ CryptoCompare fetch failed: {e}")
            return None
    
    def save_historical_data(self, historical_data, replace_existing=False):
        """Save historical data to database"""
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
        for data_point in historical_data:
            try:
                cursor.execute('''
                    INSERT INTO btc_prices (timestamp, price, volume, high, low, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    data_point['timestamp'],
                    data_point['price'],
                    data_point['volume'],
                    data_point['high'],
                    data_point['low'],
                    data_point['source']
                ))
                saved_count += 1
            except sqlite3.IntegrityError:
                # Skip duplicates
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ Saved {saved_count} new records to database")
        return True
    
    def get_data_summary(self):
        """Get summary of data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get data summary
        cursor.execute('''
            SELECT 
                COUNT(*) as total_records,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest,
                source,
                COUNT(*) as count_by_source
            FROM btc_prices 
            GROUP BY source
        ''')
        
        results = cursor.fetchall()
        
        cursor.execute('SELECT COUNT(*) FROM btc_prices')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM btc_prices')
        earliest, latest = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_records': total,
            'earliest': earliest,
            'latest': latest,
            'sources': results
        }
    
    def fetch_all_sources(self, days=90, replace_existing=False):
        """Try fetching from multiple sources as fallback"""
        print(f"🚀 Fetching {days} days of Bitcoin historical data...")
        
        # Try sources in order of preference
        sources = [
            ('CryptoCompare', self.fetch_cryptocompare_data),
            ('CoinGecko', self.fetch_coingecko_data),
            ('Yahoo Finance', self.fetch_yahoo_finance_data)
        ]
        
        for source_name, fetch_func in sources:
            print(f"\n📡 Trying {source_name}...")
            historical_data = fetch_func(days)
            
            if historical_data:
                print(f"✅ Successfully fetched {len(historical_data)} records from {source_name}")
                success = self.save_historical_data(historical_data, replace_existing)
                if success:
                    return True
            else:
                print(f"❌ {source_name} failed, trying next source...")
                time.sleep(2)  # Brief delay between attempts
        
        print("❌ All data sources failed")
        return False


def main():
    print("📊 Bitcoin Historical Data Fetcher")
    print("=" * 50)
    
    fetcher = HistoricalDataFetcher()
    
    # Check existing data
    summary = fetcher.get_data_summary()
    if summary['total_records'] > 0:
        print(f"📈 Existing data: {summary['total_records']} records")
        print(f"   Range: {summary['earliest']} to {summary['latest']}")
        print(f"   Sources: {[source[3] + ' (' + str(source[4]) + ' records)' for source in summary['sources']]}")
        
        choice = input("\n❓ Replace existing data? (y/N): ").lower().strip()
        replace_existing = choice == 'y'
    else:
        print("📭 No existing data found")
        replace_existing = False
    
    # Get user preferences
    days_input = input("\n📅 How many days of data to fetch? (default: 90): ").strip()
    days = int(days_input) if days_input.isdigit() else 90
    
    if days > 365:
        print("⚠️ Warning: Requesting more than 1 year of data may hit API limits")
    
    print(f"\n🎯 Fetching {days} days of Bitcoin data...")
    
    # Fetch data
    success = fetcher.fetch_all_sources(days, replace_existing)
    
    if success:
        # Show final summary
        final_summary = fetcher.get_data_summary()
        print(f"\n🎉 Success! Database now contains:")
        print(f"   📊 {final_summary['total_records']} total records")
        print(f"   📅 Range: {final_summary['earliest']} to {final_summary['latest']}")
        print("   🔍 Sources: " + str([source[3] + ' (' + str(source[4]) + ' records)' for source in final_summary['sources']]))
        
        # Calculate coverage
        if final_summary['earliest'] and final_summary['latest']:
            start_date = datetime.strptime(final_summary['earliest'], '%Y-%m-%d %H:%M:%S')
            end_date = datetime.strptime(final_summary['latest'], '%Y-%m-%d %H:%M:%S')
            coverage_days = (end_date - start_date).days
            print(f"   ⏱️ Coverage: {coverage_days} days")
        
        print(f"\n✅ Your strategies now have plenty of data to work with!")
        print(f"   🧠 Run: python strategies/ma_crossover.py")
        print(f"   🎯 Run: python strategies/rsi_strategy.py")
        print(f"   📊 Run: python strategies/bollinger_bands.py")
        print(f"   📈 Run: python strategies/macd_strategy.py")
        
    else:
        print(f"\n❌ Failed to fetch historical data")
        print(f"   💡 Try running again later or check your internet connection")
        print(f"   🛠️ You can still generate sample data: python scripts/generate_sample_data.py")


if __name__ == "__main__":
    main()