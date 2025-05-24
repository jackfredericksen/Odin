import requests
import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta
import json
import threading
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os

class BitcoinDataCollector:
    def __init__(self, db_path='bitcoin_data.db'):
        self.db_path = db_path
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        self.setup_database()
        self.latest_data = None
        
    def setup_database(self):
        """Create database and tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create price data table
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
        print(f"Database initialized: {self.db_path}")
    
    def fetch_current_price(self):
        """Fetch current BTC price from CoinGecko"""
        try:
            print("Fetching Bitcoin price...")
            
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
            
            btc_data = data['bitcoin']
            
            # Get additional market data
            market_url = f"{self.coingecko_url}/coins/bitcoin"
            market_response = requests.get(market_url, timeout=10)
            market_data = market_response.json()
            
            market_info = market_data['market_data']
            
            price_data = {
                'timestamp': datetime.now(),
                'price': btc_data['usd'],
                'volume': btc_data.get('usd_24h_vol', 0),
                'high': market_info['high_24h']['usd'],
                'low': market_info['low_24h']['usd'],
                'change24h': btc_data.get('usd_24h_change', 0),
                'source': 'coingecko'
            }
            
            # Store latest data for API
            self.latest_data = price_data
            
            return price_data
            
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
    
    def get_recent_prices(self, limit=100):
        """Get recent price data from database"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(f'''
            SELECT * FROM btc_prices 
            ORDER BY timestamp DESC 
            LIMIT {limit}
        ''', conn)
        conn.close()
        return df
    
    def get_price_history(self, hours=24):
        """Get price history for specified hours"""
        conn = sqlite3.connect(self.db_path)
        cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        df = pd.read_sql_query('''
            SELECT timestamp, price FROM btc_prices 
            WHERE timestamp >= ? 
            ORDER BY timestamp ASC
        ''', conn, params=(cutoff_time,))
        conn.close()
        return df
    
    def collect_data_once(self):
        """Collect one data point"""
        price_data = self.fetch_current_price()
        
        if price_data:
            success = self.save_price(price_data)
            if success:
                print(f"✅ BTC Price: ${price_data['price']:,.2f} | Change: {price_data['change24h']:+.2f}%")
                return True
            else:
                print("❌ Failed to save data")
                return False
        else:
            print("❌ Failed to fetch data")
            return False
    
    def start_continuous_collection(self, interval_seconds=60):
        """Start continuous data collection in background"""
        def collect_loop():
            print(f"🔄 Starting continuous Bitcoin data collection (every {interval_seconds}s)")
            while True:
                try:
                    self.collect_data_once()
                    time.sleep(interval_seconds)
                except Exception as e:
                    print(f"Error in collection loop: {e}")
                    time.sleep(5)  # Short retry delay
        
        # Run in background thread
        thread = threading.Thread(target=collect_loop, daemon=True)
        thread.start()
        return thread

# Flask API Server
app = Flask(__name__)
CORS(app)  # Enable CORS for web dashboard

# Global collector instance
collector = BitcoinDataCollector()

@app.route('/api/current', methods=['GET'])
def get_current_data():
    """Get current Bitcoin price and stats"""
    try:
        # Get latest data from collector
        if collector.latest_data is None:
            # If no data yet, fetch once
            collector.collect_data_once()
        
        if collector.latest_data:
            # Get total data points
            df = collector.get_recent_prices(1000)
            data_points = len(df)
            
            return jsonify({
                'price': collector.latest_data['price'],
                'change24h': collector.latest_data['change24h'],
                'high24h': collector.latest_data['high'],
                'low24h': collector.latest_data['low'],
                'volume24h': collector.latest_data['volume'],
                'timestamp': collector.latest_data['timestamp'].isoformat(),
                'dataPoints': data_points,
                'status': 'success'
            })
        else:
            return jsonify({'error': 'No data available', 'status': 'error'}), 503
            
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/history/<int:hours>', methods=['GET'])
def get_price_history(hours):
    """Get price history for specified hours"""
    try:
        df = collector.get_price_history(hours)
        
        history = []
        for _, row in df.iterrows():
            history.append({
                'timestamp': row['timestamp'],
                'price': row['price']
            })
        
        return jsonify({
            'history': history,
            'count': len(history),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/recent/<int:limit>', methods=['GET'])
def get_recent_data(limit):
    """Get recent price records"""
    try:
        df = collector.get_recent_prices(limit)
        
        recent = []
        for _, row in df.iterrows():
            recent.append({
                'timestamp': row['timestamp'],
                'price': row['price'],
                'volume': row['volume'],
                'high': row['high'],
                'low': row['low']
            })
        
        return jsonify({
            'recent': recent,
            'count': len(recent),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    try:
        df = collector.get_recent_prices(1000)
        
        if len(df) == 0:
            return jsonify({'error': 'No data available', 'status': 'error'}), 404
        
        stats = {
            'totalRecords': len(df),
            'averagePrice': float(df['price'].mean()),
            'maxPrice': float(df['price'].max()),
            'minPrice': float(df['price'].min()),
            'priceRange': float(df['price'].max() - df['price'].min()),
            'oldestRecord': df.iloc[-1]['timestamp'] if len(df) > 0 else None,
            'newestRecord': df.iloc[0]['timestamp'] if len(df) > 0 else None,
            'status': 'success'
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/')
def serve_dashboard():
    """Serve the dashboard HTML file"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bitcoin Dashboard</title>
    </head>
    <body>
        <h1>Bitcoin API Server Running!</h1>
        <p>Your Bitcoin data API is running successfully.</p>
        <h2>Available Endpoints:</h2>
        <ul>
            <li><a href="/api/current">/api/current</a> - Current Bitcoin price</li>
            <li><a href="/api/history/24">/api/history/24</a> - 24-hour price history</li>
            <li><a href="/api/recent/10">/api/recent/10</a> - Recent 10 records</li>
            <li><a href="/api/stats">/api/stats</a> - Overall statistics</li>
        </ul>
        <p><strong>Next Step:</strong> Open your dashboard HTML file and it will connect to this API!</p>
    </body>
    </html>
    '''

def main():
    print("🚀 Bitcoin Trading Bot API Server")
    print("=" * 50)
    
    # Start data collection in background
    print("Starting background data collection...")
    collector.start_continuous_collection(interval_seconds=30)  # Collect every 30 seconds
    
    # Collect initial data
    print("Fetching initial data...")
    collector.collect_data_once()
    
    print("\n🌐 Starting API server...")
    print("Dashboard will be available at: http://localhost:5000")
    print("API endpoints available at: http://localhost:5000/api/")
    print("\nPress Ctrl+C to stop the server")
    
    # Start Flask server
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")

if __name__ == "__main__":
    main()