import requests
import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta
import json
import threading
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import sys

# Add the project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add import paths for strategies and trading
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'strategies'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'paper_trading'))

# Import strategies
try:
    from ma_crossover import MovingAverageCrossoverStrategy
    from rsi_strategy import RSIStrategy
    from bollinger_bands import BollingerBandsStrategy
    from macd_strategy import MACDStrategy
    STRATEGY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Strategy module not found: {e}. Strategy endpoints will be disabled.")
    STRATEGY_AVAILABLE = False

# Import trading modules
try:
    from portfolio_manager import PaperTradingPortfolio
    from trading_bot import OdinTradingBot
    TRADING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Trading modules not found: {e}. Trading endpoints will be disabled.")
    TRADING_AVAILABLE = False

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
                
                # Integrate with trading bot
                integrate_trading_with_price_updates()
                return True
            else:
                print("❌ Failed to save data")
                return False
        else:
            print("❌ Failed to fetch data")
            return False
    
    def start_continuous_collection(self, interval_seconds=30):
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

# Initialize strategies
if STRATEGY_AVAILABLE:
    ma_strategy = MovingAverageCrossoverStrategy()
    rsi_strategy = RSIStrategy()
    bb_strategy = BollingerBandsStrategy()
    macd_strategy = MACDStrategy()
else:
    ma_strategy = None
    rsi_strategy = None
    bb_strategy = None
    macd_strategy = None

# Initialize trading bot
if TRADING_AVAILABLE:
    # Initialize trading bot (paper trading only by default)
    trading_bot = OdinTradingBot(initial_balance=10000.0, trading_enabled=False)
    print("✅ Trading bot initialized (paper trading mode)")
else:
    trading_bot = None

def integrate_trading_with_price_updates():
    """Integrate trading bot with price updates"""
    if TRADING_AVAILABLE and trading_bot and collector.latest_data:
        try:
            current_price = collector.latest_data['price']
            previous_price = trading_bot.current_price
            trading_bot.current_price = current_price
            
            # Log price updates for trading context
            if previous_price and previous_price != current_price:
                change = current_price - previous_price
                change_pct = (change / previous_price) * 100
                print(f"📊 Trading Bot Price Update: ${current_price:,.2f} ({change_pct:+.2f}%) from {collector.latest_data['source']}")
            
            # Update portfolio positions with current REAL price
            trading_bot.portfolio.update_positions(current_price)
            
            # If automated trading is enabled, process signals with REAL price
            if trading_bot.trading_enabled:
                executed_trades = trading_bot.auto_trader.process_signals(current_price)
                if executed_trades:
                    print(f"🤖 Auto-executed {len(executed_trades)} trades at REAL market price ${current_price:,.2f}")
                    for trade in executed_trades:
                        print(f"   ⚡ {trade.side.upper()} {trade.quantity:.6f} BTC @ ${trade.price:,.2f} ({trade.strategy})")
        except Exception as e:
            print(f"❌ Error in trading integration: {e}")

# ============================================================================
# PRICE DATA ENDPOINTS
# ============================================================================

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

# ============================================================================
# STRATEGY ENDPOINTS
# ============================================================================

@app.route('/api/strategy/ma/analysis', methods=['GET'])
def get_ma_strategy_analysis():
    """Get current MA strategy analysis"""
    if not STRATEGY_AVAILABLE or ma_strategy is None:
        return jsonify({'error': 'MA Strategy not available', 'status': 'error'}), 503
    
    try:
        analysis = ma_strategy.analyze_current_market()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/strategy/ma/backtest/<int:hours>', methods=['GET'])
def get_ma_strategy_backtest(hours):
    """Get MA strategy backtest results"""
    if not STRATEGY_AVAILABLE or ma_strategy is None:
        return jsonify({'error': 'MA Strategy not available', 'status': 'error'}), 503
    
    try:
        backtest_results = ma_strategy.backtest(hours=hours)
        return jsonify(backtest_results)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/strategy/rsi/analysis', methods=['GET'])
def get_rsi_strategy_analysis():
    """Get current RSI strategy analysis"""
    if not STRATEGY_AVAILABLE or rsi_strategy is None:
        return jsonify({'error': 'RSI Strategy not available', 'status': 'error'}), 503
    
    try:
        analysis = rsi_strategy.analyze_current_market()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/strategy/rsi/backtest/<int:hours>', methods=['GET'])
def get_rsi_strategy_backtest(hours):
    """Get RSI strategy backtest results"""
    if not STRATEGY_AVAILABLE or rsi_strategy is None:
        return jsonify({'error': 'RSI Strategy not available', 'status': 'error'}), 503
    
    try:
        backtest_results = rsi_strategy.backtest(hours=hours)
        return jsonify(backtest_results)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/strategy/rsi/summary/<int:hours>', methods=['GET'])
def get_rsi_signals_summary(hours):
    """Get RSI signals summary"""
    if not STRATEGY_AVAILABLE or rsi_strategy is None:
        return jsonify({'error': 'RSI Strategy not available', 'status': 'error'}), 503
    
    try:
        summary = rsi_strategy.get_rsi_signals_summary(hours=hours)
        if summary is None:
            return jsonify({'error': 'Not enough data for summary', 'status': 'error'}), 404
        
        return jsonify({
            'summary': summary,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/strategy/bb/analysis', methods=['GET'])
def get_bb_strategy_analysis():
    """Get current Bollinger Bands strategy analysis"""
    if not STRATEGY_AVAILABLE or bb_strategy is None:
        return jsonify({'error': 'Bollinger Bands Strategy not available', 'status': 'error'}), 503
    
    try:
        analysis = bb_strategy.analyze_current_market()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/strategy/bb/backtest/<int:hours>', methods=['GET'])
def get_bb_strategy_backtest(hours):
    """Get Bollinger Bands strategy backtest results"""
    if not STRATEGY_AVAILABLE or bb_strategy is None:
        return jsonify({'error': 'Bollinger Bands Strategy not available', 'status': 'error'}), 503
    
    try:
        backtest_results = bb_strategy.backtest(hours=hours)
        return jsonify(backtest_results)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/strategy/macd/analysis', methods=['GET'])
def get_macd_strategy_analysis():
    """Get current MACD strategy analysis"""
    if not STRATEGY_AVAILABLE or macd_strategy is None:
        return jsonify({'error': 'MACD Strategy not available', 'status': 'error'}), 503
    
    try:
        analysis = macd_strategy.analyze_current_market()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/strategy/macd/backtest/<int:hours>', methods=['GET'])
def get_macd_strategy_backtest(hours):
    """Get MACD strategy backtest results"""
    if not STRATEGY_AVAILABLE or macd_strategy is None:
        return jsonify({'error': 'MACD Strategy not available', 'status': 'error'}), 503
    
    try:
        backtest_results = macd_strategy.backtest(hours=hours)
        return jsonify(backtest_results)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/strategy/compare/all/<int:hours>', methods=['GET'])
def compare_all_strategies(hours):
    """Compare all four strategies"""
    if not STRATEGY_AVAILABLE:
        return jsonify({'error': 'Strategies not available', 'status': 'error'}), 503
    
    try:
        strategies = {}
        
        # Get backtest results for all strategies
        if ma_strategy:
            ma_results = ma_strategy.backtest(hours=hours)
            if 'error' not in ma_results:
                strategies['MA'] = {
                    'name': ma_results['strategy'],
                    'return_percent': ma_results['total_return_percent'],
                    'total_trades': ma_results['total_trades'],
                    'win_rate': ma_results['win_rate_percent'],
                    'final_value': ma_results['final_value']
                }
        
        if rsi_strategy:
            rsi_results = rsi_strategy.backtest(hours=hours)
            if 'error' not in rsi_results:
                strategies['RSI'] = {
                    'name': rsi_results['strategy'],
                    'return_percent': rsi_results['total_return_percent'],
                    'total_trades': rsi_results['total_trades'],
                    'win_rate': rsi_results['win_rate_percent'],
                    'final_value': rsi_results['final_value']
                }
        
        if bb_strategy:
            bb_results = bb_strategy.backtest(hours=hours)
            if 'error' not in bb_results:
                strategies['BB'] = {
                    'name': bb_results['strategy'],
                    'return_percent': bb_results['total_return_percent'],
                    'total_trades': bb_results['total_trades'],
                    'win_rate': bb_results['win_rate_percent'],
                    'final_value': bb_results['final_value']
                }
        
        if macd_strategy:
            macd_results = macd_strategy.backtest(hours=hours)
            if 'error' not in macd_results:
                strategies['MACD'] = {
                    'name': macd_results['strategy'],
                    'return_percent': macd_results['total_return_percent'],
                    'total_trades': macd_results['total_trades'],
                    'win_rate': macd_results['win_rate_percent'],
                    'final_value': macd_results['final_value']
                }
        
        if not strategies:
            return jsonify({'error': 'No strategies have enough data', 'status': 'error'}), 404
        
        # Find the winner (best return)
        winner = max(strategies.items(), key=lambda x: x[1]['return_percent'])
        
        comparison = {
            'period_hours': hours,
            'strategies': strategies,
            'winner': {
                'name': winner[0],
                'return_percent': winner[1]['return_percent']
            },
            'total_strategies': len(strategies),
            'status': 'success'
        }
        
        return jsonify(comparison)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

# ============================================================================
# TRADING BOT ENDPOINTS
# ============================================================================

@app.route('/api/trading/portfolio', methods=['GET'])
def get_portfolio_status():
    """Get current portfolio status"""
    if not TRADING_AVAILABLE or trading_bot is None:
        return jsonify({'error': 'Trading not available', 'status': 'error'}), 503
    
    try:
        portfolio_status = trading_bot.get_portfolio_status()
        return jsonify({
            'portfolio': portfolio_status,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/trading/trades', methods=['GET'])
def get_recent_trades():
    """Get recent trades"""
    if not TRADING_AVAILABLE or trading_bot is None:
        return jsonify({'error': 'Trading not available', 'status': 'error'}), 503
    
    try:
        limit = request.args.get('limit', 20, type=int)
        portfolio_summary = trading_bot.portfolio.get_portfolio_summary()
        recent_trades = portfolio_summary.get('recent_trades', [])
        
        return jsonify({
            'trades': recent_trades[-limit:],
            'count': len(recent_trades),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/trading/positions', methods=['GET'])
def get_active_positions():
    """Get active positions"""
    if not TRADING_AVAILABLE or trading_bot is None:
        return jsonify({'error': 'Trading not available', 'status': 'error'}), 503
    
    try:
        portfolio_summary = trading_bot.portfolio.get_portfolio_summary()
        return jsonify({
            'positions': portfolio_summary['active_positions'],
            'count': portfolio_summary['position_count'],
            'total_value': portfolio_summary['position_value'],
            'unrealized_pnl': portfolio_summary['unrealized_pnl'],
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/trading/performance', methods=['GET'])
def get_trading_performance():
    """Get trading performance by strategy"""
    if not TRADING_AVAILABLE or trading_bot is None:
        return jsonify({'error': 'Trading not available', 'status': 'error'}), 503
    
    try:
        strategy = request.args.get('strategy', None)
        performance = trading_bot.portfolio.get_strategy_performance(strategy)
        
        return jsonify({
            'performance': performance,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/trading/execute', methods=['POST'])
def execute_manual_trade():
    """Execute a manual trade"""
    if not TRADING_AVAILABLE or trading_bot is None:
        return jsonify({'error': 'Trading not available', 'status': 'error'}), 503
    
    try:
        data = request.get_json()
        side = data.get('side')  # 'buy' or 'sell'
        quantity = float(data.get('quantity', 0))
        strategy = data.get('strategy', 'Manual')
        
        if side not in ['buy', 'sell']:
            return jsonify({'error': 'Invalid side. Use buy or sell', 'status': 'error'}), 400
            
        if quantity <= 0:
            return jsonify({'error': 'Invalid quantity', 'status': 'error'}), 400
        
        result = trading_bot.manual_trade(side, quantity, strategy)
        
        if result['success']:
            return jsonify({
                'trade': result['trade'],
                'portfolio': result['portfolio'],
                'status': 'success'
            })
        else:
            return jsonify({'error': result['error'], 'status': 'error'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/trading/bot/start', methods=['POST'])
def start_trading_bot():
    """Start the automated trading bot"""
    if not TRADING_AVAILABLE or trading_bot is None:
        return jsonify({'error': 'Trading not available', 'status': 'error'}), 503
    
    try:
        if trading_bot.running:
            return jsonify({'error': 'Trading bot already running', 'status': 'error'}), 400
        
        # Start bot in background thread
        data = request.get_json() or {}
        cycle_interval = data.get('cycle_interval', 60)
        
        def run_bot():
            trading_bot.start_trading(cycle_interval)
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        return jsonify({
            'message': 'Trading bot started',
            'cycle_interval': cycle_interval,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/trading/bot/stop', methods=['POST'])
def stop_trading_bot():
    """Stop the automated trading bot"""
    if not TRADING_AVAILABLE or trading_bot is None:
        return jsonify({'error': 'Trading not available', 'status': 'error'}), 503
    
    try:
        if not trading_bot.running:
            return jsonify({'error': 'Trading bot not running', 'status': 'error'}), 400
        
        trading_bot.stop_trading()
        
        return jsonify({
            'message': 'Trading bot stopped',
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/trading/bot/toggle', methods=['POST'])
def toggle_auto_trading():
    """Toggle automated trading on/off"""
    if not TRADING_AVAILABLE or trading_bot is None:
        return jsonify({'error': 'Trading not available', 'status': 'error'}), 503
    
    try:
        if trading_bot.trading_enabled:
            trading_bot.disable_trading()
            message = 'Automated trading disabled'
        else:
            trading_bot.enable_trading()
            message = 'Automated trading enabled'
        
        return jsonify({
            'message': message,
            'trading_enabled': trading_bot.trading_enabled,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/trading/reset', methods=['POST'])
def reset_portfolio():
    """Reset portfolio to initial state"""
    if not TRADING_AVAILABLE or trading_bot is None:
        return jsonify({'error': 'Trading not available', 'status': 'error'}), 503
    
    try:
        data = request.get_json() or {}
        new_balance = float(data.get('balance', 10000.0))
        
        success = trading_bot.reset_portfolio(new_balance)
        
        if success:
            return jsonify({
                'message': f'Portfolio reset to ${new_balance:,.2f}',
                'new_balance': new_balance,
                'status': 'success'
            })
        else:
            return jsonify({'error': 'Failed to reset portfolio', 'status': 'error'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/trading/status', methods=['GET'])
def get_trading_bot_status():
    """Get trading bot status"""
    if not TRADING_AVAILABLE or trading_bot is None:
        return jsonify({'error': 'Trading not available', 'status': 'error'}), 503
    
    try:
        return jsonify({
            'bot_running': trading_bot.running,
            'trading_enabled': trading_bot.trading_enabled,
            'current_price': trading_bot.current_price,
            'total_signals': trading_bot.stats['total_signals'],
            'executed_trades': trading_bot.stats['executed_trades'],
            'runtime': str(datetime.now() - trading_bot.stats['start_time']).split('.')[0],
            'active_strategies': list(trading_bot.strategies.keys()),
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

# ============================================================================
# LEGACY ENDPOINTS (for backward compatibility)
# ============================================================================

@app.route('/api/strategy/analysis', methods=['GET'])
def get_strategy_analysis():
    """Get current strategy analysis (defaults to MA for backward compatibility)"""
    return get_ma_strategy_analysis()

@app.route('/api/strategy/backtest/<int:hours>', methods=['GET'])
def get_strategy_backtest(hours):
    """Get strategy backtest results (defaults to MA for backward compatibility)"""
    return get_ma_strategy_backtest(hours)

@app.route('/api/strategy/chart/<int:hours>', methods=['GET'])
def get_strategy_chart_data(hours):
    """Get strategy data for charting (defaults to MA for backward compatibility)"""
    if not STRATEGY_AVAILABLE or ma_strategy is None:
        return jsonify({'error': 'Strategy not available', 'status': 'error'}), 503
    
    try:
        chart_data = ma_strategy.get_strategy_data_for_chart(hours=hours)
        
        if chart_data is None:
            return jsonify({'error': 'Not enough data for chart', 'status': 'error'}), 404
        
        return jsonify({
            'data': chart_data,
            'strategy': f'MA({ma_strategy.short_window},{ma_strategy.long_window})',
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

# ============================================================================
# WEB DASHBOARD
# ============================================================================

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
        trading_status = "Available" if TRADING_AVAILABLE else "Not available"
        strategy_status = "Available" if STRATEGY_AVAILABLE else "Not available"
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>⚡ Odin - Bitcoin Trading Bot API</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                .status {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .endpoints {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .endpoint {{ margin: 10px 0; padding: 8px; background: white; border-left: 4px solid #3498db; }}
                .error {{ color: #e74c3c; background: #ffeaea; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                a {{ color: #3498db; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚡ Odin - Bitcoin Trading Bot API</h1>
                <p>Your advanced Bitcoin trading bot API is running successfully!</p>
                
                <div class="status">
                    <h3>📊 System Status</h3>
                    <p><strong>Database:</strong> {collector.db_path}</p>
                    <p><strong>Strategies:</strong> {strategy_status}</p>
                    <p><strong>Trading Bot:</strong> {trading_status}</p>
                    <p><strong>Data Sources:</strong> CoinDesk → Blockchain.info → CoinGecko</p>
                </div>

                <div class="endpoints">
                    <h3>🔌 Available API Endpoints</h3>
                    
                    <h4>💰 Price Data</h4>
                    <div class="endpoint"><a href="/api/current">/api/current</a> - Current Bitcoin price and stats</div>
                    <div class="endpoint"><a href="/api/history/24">/api/history/24</a> - 24-hour price history</div>
                    <div class="endpoint"><a href="/api/recent/10">/api/recent/10</a> - Recent 10 price records</div>
                    <div class="endpoint"><a href="/api/stats">/api/stats</a> - Overall statistics</div>
                    
                    <h4>🧠 Strategy Analysis</h4>
                    <div class="endpoint"><a href="/api/strategy/ma/analysis">/api/strategy/ma/analysis</a> - Moving Average analysis</div>
                    <div class="endpoint"><a href="/api/strategy/rsi/analysis">/api/strategy/rsi/analysis</a> - RSI analysis</div>
                    <div class="endpoint"><a href="/api/strategy/bb/analysis">/api/strategy/bb/analysis</a> - Bollinger Bands analysis</div>
                    <div class="endpoint"><a href="/api/strategy/macd/analysis">/api/strategy/macd/analysis</a> - MACD analysis</div>
                    <div class="endpoint"><a href="/api/strategy/compare/all/48">/api/strategy/compare/all/48</a> - Compare all strategies</div>
                    
                    <h4>📈 Backtesting</h4>
                    <div class="endpoint"><a href="/api/strategy/ma/backtest/24">/api/strategy/ma/backtest/24</a> - MA strategy backtest</div>
                    <div class="endpoint"><a href="/api/strategy/rsi/backtest/24">/api/strategy/rsi/backtest/24</a> - RSI strategy backtest</div>
                    <div class="endpoint"><a href="/api/strategy/bb/backtest/24">/api/strategy/bb/backtest/24</a> - Bollinger Bands backtest</div>
                    <div class="endpoint"><a href="/api/strategy/macd/backtest/24">/api/strategy/macd/backtest/24</a> - MACD strategy backtest</div>
                    
                    <h4>🤖 Trading Bot</h4>
                    <div class="endpoint"><a href="/api/trading/portfolio">/api/trading/portfolio</a> - Portfolio status</div>
                    <div class="endpoint"><a href="/api/trading/trades">/api/trading/trades</a> - Recent trades</div>
                    <div class="endpoint"><a href="/api/trading/positions">/api/trading/positions</a> - Active positions</div>
                    <div class="endpoint"><a href="/api/trading/status">/api/trading/status</a> - Trading bot status</div>
                    <div class="endpoint">/api/trading/execute (POST) - Execute manual trade</div>
                    <div class="endpoint">/api/trading/bot/start (POST) - Start automated trading</div>
                    <div class="endpoint">/api/trading/bot/stop (POST) - Stop automated trading</div>
                    <div class="endpoint">/api/trading/bot/toggle (POST) - Toggle auto trading</div>
                    <div class="endpoint">/api/trading/reset (POST) - Reset portfolio</div>
                </div>

                <div class="error">
                    <strong>Dashboard Error:</strong> {e}<br>
                    <strong>Solution:</strong> Place dashboard.html in web_interface/ folder
                </div>
                
                <p><strong>🎯 Quick Start:</strong></p>
                <ul>
                    <li>Dashboard: Create <code>web_interface/dashboard.html</code></li>
                    <li>Test Strategies: <code>python strategies/ma_crossover.py</code></li>
                    <li>Run Trading Bot: <code>python src/trading_bot.py</code></li>
                    <li>Generate Sample Data: <code>python scripts/fetch_historical_data.py</code></li>
                </ul>
            </div>
        </body>
        </html>
        '''

def main():
    print("⚡ Odin - Advanced Bitcoin Trading Bot API Server")
    print("=" * 60)
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🗄️ Database Path: {collector.db_path}")
    print(f"🧠 Strategies Available: {STRATEGY_AVAILABLE}")
    print(f"🤖 Trading Available: {TRADING_AVAILABLE}")
    print(f"📊 Data Sources: CoinDesk → Blockchain.info → CoinGecko")
    
    if STRATEGY_AVAILABLE:
        print(f"🎯 Active Strategies: MA, RSI, Bollinger Bands, MACD")
    else:
        print(f"⚠️ Strategies not loaded - check strategies/ folder")
        
    if TRADING_AVAILABLE:
        print(f"💰 Paper Trading: Initialized with $10,000")
        print(f"🤖 Auto Trading: Disabled (can be enabled via API)")
    else:
        print(f"⚠️ Trading bot not loaded - check paper_trading/ folder")
    
    # Start data collection in background
    print(f"\n🔄 Starting background data collection...")
    collector.start_continuous_collection(interval_seconds=30)  # 30 seconds for better responsiveness
    
    # Collect initial data
    print("📊 Fetching initial Bitcoin price data...")
    collector.collect_data_once()
    
    print(f"\n🌐 Starting Odin API server...")
    print(f"🎛️ Dashboard: http://localhost:5000")
    print(f"🔌 API Root: http://localhost:5000/api/")
    print(f"📈 Strategy Analysis: http://localhost:5000/api/strategy/compare/all/24")
    print(f"🤖 Trading Status: http://localhost:5000/api/trading/status")
    print(f"✅ Data Collection: Every 30 seconds")
    print(f"\n🛑 Press Ctrl+C to stop the server")
    
    # Start Flask server
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print(f"\n🛑 Odin server stopped by user")
        if TRADING_AVAILABLE and trading_bot:
            trading_bot.stop_trading()
            print("💾 Trading bot state saved")

if __name__ == "__main__":
    main()