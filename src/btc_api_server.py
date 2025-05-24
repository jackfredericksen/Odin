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
import sys

# Add the project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add import for the strategy
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'strategies'))

try:
    from ma_crossover import MovingAverageCrossoverStrategy
    STRATEGY_AVAILABLE = True
except ImportError:
    print("⚠️ Strategy module not found. Strategy endpoints will be disabled.")
    STRATEGY_AVAILABLE = False

class BitcoinDataCollector:
    def __init__(self, db_path=None):
        # Get the project root directory (parent of src folder)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        if db_path is None:
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.cmc_url = "https://pro-api.coinmarketcap.com/v1"
        self.cmc_sandbox_url = "https://sandbox-api.coinmarketcap.com/v1"  # For testing
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
        """Fetch current BTC price from multiple free sources as fallback"""
        try:
            print("Fetching Bitcoin price...")
            
            # Try multiple free APIs in order of preference
            sources = [
                self._fetch_from_coindesk,
                self._fetch_from_blockchain_info,
                self._fetch_from_coingecko_simple
            ]
            
            for source in sources:
                try:
                    price_data = source()
                    if price_data:
                        self.latest_data = price_data
                        return price_data
                except Exception as e:
                    print(f"Source failed: {e}")
                    continue
            
            print("All sources failed")
            return None
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def _fetch_from_coindesk(self):
        """Fetch from CoinDesk API (completely free)"""
        print("Trying CoinDesk API...")
        
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        price = float(data['bpi']['USD']['rate'].replace(',', ''))
        
        # CoinDesk only provides current price, so we'll estimate other values
        price_data = {
            'timestamp': datetime.now(),
            'price': price,
            'volume': 50000000000,  # Estimated volume
            'high': price * 1.02,   # Estimated high
            'low': price * 0.98,    # Estimated low
            'change24h': 0.0,       # Not available from CoinDesk
            'source': 'coindesk'
        }
        
        print(f"✅ CoinDesk: ${price:,.2f}")
        return price_data
    
    def _fetch_from_blockchain_info(self):
        """Fetch from Blockchain.info API (free)"""
        print("Trying Blockchain.info API...")
        
        response = requests.get("https://api.blockchain.info/ticker", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        usd_data = data['USD']
        price = float(usd_data['last'])
        
        price_data = {
            'timestamp': datetime.now(),
            'price': price,
            'volume': 50000000000,  # Estimated volume
            'high': price * 1.02,   # Estimated high
            'low': price * 0.98,    # Estimated low
            'change24h': 0.0,       # Not available
            'source': 'blockchain.info'
        }
        
        print(f"✅ Blockchain.info: ${price:,.2f}")
        return price_data
    
    def _fetch_from_coingecko_simple(self):
        """Fetch from CoinGecko simple API (slower rate limit)"""
        print("Trying CoinGecko simple API...")
        
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        btc_data = data['bitcoin']
        price = float(btc_data['usd'])
        change_24h = float(btc_data.get('usd_24h_change', 0))
        
        price_data = {
            'timestamp': datetime.now(),
            'price': price,
            'volume': 50000000000,  # Estimated
            'high': price * (1 + abs(change_24h)/100/2),
            'low': price * (1 - abs(change_24h)/100/2),
            'change24h': change_24h,
            'source': 'coingecko'
        }
        
        print(f"✅ CoinGecko: ${price:,.2f} ({change_24h:+.2f}%)")
        return price_data
    
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
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        print("⚠️ Rate limit hit - waiting 2 minutes before retry...")
                        time.sleep(120)  # Wait 2 minutes for rate limits
                    else:
                        time.sleep(30)  # Short retry delay for other errors
        
        # Run in background thread
        thread = threading.Thread(target=collect_loop, daemon=True)
        thread.start()
        return thread

# Flask API Server
app = Flask(__name__)
CORS(app)  # Enable CORS for web dashboard

# Global collector and strategy instances
collector = BitcoinDataCollector()
if STRATEGY_AVAILABLE:
    strategy = MovingAverageCrossoverStrategy()
else:
    strategy = None

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

@app.route('/api/strategy/analysis', methods=['GET'])
def get_strategy_analysis():
    """Get current strategy analysis"""
    if not STRATEGY_AVAILABLE or strategy is None:
        return jsonify({'error': 'Strategy not available', 'status': 'error'}), 503
    
    try:
        analysis = strategy.analyze_current_market()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/strategy/backtest/<int:hours>', methods=['GET'])
def get_strategy_backtest(hours):
    """Get strategy backtest results"""
    if not STRATEGY_AVAILABLE or strategy is None:
        return jsonify({'error': 'Strategy not available', 'status': 'error'}), 503
    
    try:
        backtest_results = strategy.backtest(hours=hours)
        return jsonify(backtest_results)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/strategy/chart/<int:hours>', methods=['GET'])
def get_strategy_chart_data(hours):
    """Get strategy data for charting"""
    if not STRATEGY_AVAILABLE or strategy is None:
        return jsonify({'error': 'Strategy not available', 'status': 'error'}), 503
    
    try:
        chart_data = strategy.get_strategy_data_for_chart(hours=hours)
        
        if chart_data is None:
            return jsonify({'error': 'Not enough data for chart', 'status': 'error'}), 404
        
        return jsonify({
            'data': chart_data,
            'strategy': f'MA({strategy.short_window},{strategy.long_window})',
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/')
def serve_dashboard():
    """Serve the dashboard HTML file"""
    try:
        # Get project root and dashboard path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        dashboard_path = os.path.join(project_root, 'web_interface')
        
        return send_from_directory(dashboard_path, 'dashboard.html')
    except Exception as e:
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bitcoin API Server</title>
        </head>
        <body>
            <h1>🚀 Bitcoin API Server Running!</h1>
            <p>Your Bitcoin data API is running successfully.</p>
            <h2>Available Endpoints:</h2>
            <ul>
                <li><a href="/api/current">/api/current</a> - Current Bitcoin price</li>
                <li><a href="/api/history/24">/api/history/24</a> - 24-hour price history</li>
                <li><a href="/api/recent/10">/api/recent/10</a> - Recent 10 records</li>
                <li><a href="/api/stats">/api/stats</a> - Overall statistics</li>
            </ul>
            <p><strong>Dashboard:</strong> Place dashboard.html in web_interface/ folder</p>
            <p><strong>Database:</strong> {collector.db_path}</p>
            <p><strong>Strategy:</strong> {"Available" if STRATEGY_AVAILABLE else "Not available"}</p>
            <p><strong>Error:</strong> {e}</p>
        </body>
        </html>
        '''

def main():
    print("🚀 Bitcoin Trading Bot API Server")
    print("=" * 50)
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🗄️ Database Path: {collector.db_path}")
    print(f"🧠 Strategy Available: {STRATEGY_AVAILABLE}")
    print(f"📊 Data Sources: CoinDesk → Blockchain.info → CoinGecko (fallback chain)")
    
    # Start data collection in background
    print("Starting background data collection...")
    collector.start_continuous_collection(interval_seconds=60)  # 60 seconds for multiple API calls
    
    # Collect initial data
    print("Fetching initial data...")
    collector.collect_data_once()
    
    print("\n🌐 Starting API server...")
    print("Dashboard available at: http://localhost:5000")
    print("API endpoints available at: http://localhost:5000/api/")
    print("📊 Dashboard file: web_interface/dashboard.html")
    print("✅ Data collection: Every 60 seconds (with fallback sources)")
    print("\nPress Ctrl+C to stop the server")
    
    # Start Flask server
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")

if __name__ == "__main__":
    main()