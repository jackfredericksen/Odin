# src/btc_api_server.py (Fixed Version)
"""
Enhanced Bitcoin Trading Bot API Server - Fixed Version
Handles missing modules gracefully and fixes database path issues
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import pandas as pd
import json

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Create necessary directories
os.makedirs(os.path.join(project_root, 'data'), exist_ok=True)
os.makedirs(os.path.join(project_root, 'logs'), exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import core modules with error handling
try:
    from src.data_manager import DataManager
    DATA_MANAGER_AVAILABLE = True
    logger.info("✅ DataManager imported successfully")
except ImportError as e:
    DATA_MANAGER_AVAILABLE = False
    logger.warning(f"⚠️ DataManager not available: {e}")

# Import strategies with error handling
strategies_available = {}
try:
    from strategies.ma_crossover import MovingAverageCrossoverStrategy
    strategies_available['ma_crossover'] = MovingAverageCrossoverStrategy
    logger.info("✅ MA Crossover strategy imported")
except ImportError:
    logger.warning("⚠️ MA Crossover strategy not available")

try:
    from strategies.rsi_strategy import RSIStrategy
    strategies_available['rsi'] = RSIStrategy
    logger.info("✅ RSI strategy imported")
except ImportError:
    logger.warning("⚠️ RSI strategy not available")

try:
    from strategies.bollinger_bands import BollingerBandsStrategy
    strategies_available['bollinger_bands'] = BollingerBandsStrategy
    logger.info("✅ Bollinger Bands strategy imported")
except ImportError:
    logger.warning("⚠️ Bollinger Bands strategy not available")

try:
    from strategies.macd_strategy import MACDStrategy
    strategies_available['macd'] = MACDStrategy
    logger.info("✅ MACD strategy imported")
except ImportError:
    logger.warning("⚠️ MACD strategy not available")

# Import advanced features with error handling
ADVANCED_FEATURES = False
try:
    from risk_management.risk_calculator import RiskCalculator
    from risk_management.portfolio_protector import PortfolioProtector
    from notifications.notification_manager import NotificationManager
    from analytics.performance_analyzer import PerformanceAnalyzer
    ADVANCED_FEATURES = True
    logger.info("✅ Advanced features available")
except ImportError:
    ADVANCED_FEATURES = False
    logger.warning("⚠️ Advanced features not available - modules not found")

# Simple fallback data collector if DataManager not available
class SimpleBitcoinCollector:
    """Fallback data collector if DataManager is not available"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
        self.latest_data = None
        self.setup_database()
        
    def setup_database(self):
        """Create database if it doesn't exist"""
        try:
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
            logger.info(f"✅ Database setup completed: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ Database setup error: {e}")
            # Create a fallback in-memory database
            self.db_path = ":memory:"
    
    def get_latest_price(self):
        """Get latest price (fallback implementation)"""
        try:
            import requests
            response = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10)
            data = response.json()
            price = float(data['bpi']['USD']['rate'].replace(',', ''))
            
            from dataclasses import dataclass
            @dataclass
            class PriceData:
                timestamp: datetime
                price: float
                volume: float
                high: float
                low: float
                source: str
            
            return PriceData(
                timestamp=datetime.now(),
                price=price,
                volume=50000000000,
                high=price * 1.02,
                low=price * 0.98,
                source='coindesk_fallback'
            )
        except Exception as e:
            logger.error(f"Error fetching price: {e}")
            return None
    
    def get_unified_data(self, hours=24, **kwargs):
        """Get data (fallback implementation)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            df = pd.read_sql_query('''
                SELECT timestamp, price, volume, high, low, source
                FROM btc_prices 
                WHERE timestamp >= ? 
                ORDER BY timestamp ASC
            ''', conn, params=(cutoff_time,))
            
            conn.close()
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting data: {e}")
            return pd.DataFrame()
    
    def get_statistics(self):
        """Get basic statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM btc_prices")
            total_records = cursor.fetchone()[0]
            conn.close()
            
            return {
                'total_records': total_records,
                'status': 'fallback_mode'
            }
        except Exception:
            return {'total_records': 0, 'status': 'fallback_mode'}

class EnhancedTradingBotServer:
    """Enhanced trading bot server with graceful fallbacks"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Initialize data manager (with fallback)
        if DATA_MANAGER_AVAILABLE:
            try:
                self.data_manager = DataManager()
                logger.info("✅ DataManager initialized successfully")
            except Exception as e:
                logger.error(f"❌ DataManager initialization failed: {e}")
                logger.info("🔄 Falling back to SimpleBitcoinCollector")
                self.data_manager = SimpleBitcoinCollector()
        else:
            logger.info("🔄 Using SimpleBitcoinCollector fallback")
            self.data_manager = SimpleBitcoinCollector()
        
        # Initialize strategies
        self.strategies = {}
        for name, strategy_class in strategies_available.items():
            try:
                self.strategies[name] = strategy_class()
                logger.info(f"✅ {name} strategy initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {name} strategy: {e}")
        
        # Initialize advanced components if available
        self.advanced_features_enabled = ADVANCED_FEATURES
        if self.advanced_features_enabled:
            try:
                self.risk_calculator = RiskCalculator()
                self.portfolio_protector = PortfolioProtector()
                self.notification_manager = NotificationManager()
                self.performance_analyzer = PerformanceAnalyzer()
                logger.info("✅ Advanced features initialized")
            except Exception as e:
                logger.error(f"❌ Advanced features initialization failed: {e}")
                self.advanced_features_enabled = False
        
        # Portfolio state
        self.portfolio = {
            'balance': 10000.0,
            'btc_holdings': 0.0,
            'total_value': 10000.0,
            'unrealized_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0
        }
        
        self.setup_routes()
        self.start_background_tasks()
    
    def setup_routes(self):
        """Setup all API routes with error handling"""
        
        # ===== CORE DATA ENDPOINTS =====
        self.app.route('/api/current', methods=['GET'])(self.get_current_data)
        self.app.route('/api/history/<int:hours>', methods=['GET'])(self.get_unified_history)
        self.app.route('/api/stats', methods=['GET'])(self.get_data_statistics)
        
        # ===== STRATEGY ENDPOINTS =====
        self.app.route('/api/strategy/<strategy_name>/analysis', methods=['GET'])(self.get_strategy_analysis)
        self.app.route('/api/strategy/<strategy_name>/backtest/<int:hours>', methods=['GET'])(self.run_strategy_backtest)
        self.app.route('/api/strategy/compare/all/<int:hours>', methods=['GET'])(self.compare_all_strategies)
        self.app.route('/api/strategy/signals', methods=['GET'])(self.get_combined_signals)
        
        # ===== PORTFOLIO ENDPOINTS =====
        self.app.route('/api/portfolio', methods=['GET'])(self.get_portfolio_status)
        self.app.route('/api/portfolio/performance', methods=['GET'])(self.get_portfolio_performance)
        
        # ===== RISK MANAGEMENT ENDPOINTS (if available) =====
        if self.advanced_features_enabled:
            self.app.route('/api/risk/metrics', methods=['GET'])(self.get_risk_metrics)
            self.app.route('/api/risk/position-size', methods=['POST'])(self.calculate_position_size_endpoint)
            self.app.route('/api/risk/limits', methods=['GET'])(self.get_risk_limits)
        
        # ===== NOTIFICATION ENDPOINTS (if available) =====
        if self.advanced_features_enabled:
            self.app.route('/api/notifications/status', methods=['GET'])(self.get_notification_status)
            self.app.route('/api/notifications/test', methods=['POST'])(self.send_test_notification)
            self.app.route('/api/notifications/history', methods=['GET'])(self.get_notification_history_endpoint)
        
        # ===== DASHBOARD ROUTES =====
        self.app.route('/', methods=['GET'])(self.serve_main_dashboard)
        self.app.route('/risk', methods=['GET'])(self.serve_risk_dashboard)
        self.app.route('/analytics', methods=['GET'])(self.serve_analytics_dashboard)
        self.app.route('/portfolio', methods=['GET'])(self.serve_portfolio_dashboard)
        
        # ===== ERROR HANDLERS =====
        self.app.errorhandler(404)(self.not_found)
        self.app.errorhandler(500)(self.server_error)
    
    def get_current_data(self):
        """Get current Bitcoin price with enhanced data"""
        try:
            latest_price = self.data_manager.get_latest_price()
            
            if not latest_price:
                return jsonify({'error': 'No current data available'}), 503
            
            # Calculate 24h change (simple version)
            change_24h = 0.0
            try:
                recent_data = self.data_manager.get_unified_data(hours=24)
                if len(recent_data) > 1:
                    old_price = recent_data.iloc[0]['price']
                    change_24h = ((latest_price.price - old_price) / old_price) * 100
            except Exception:
                pass  # Use default 0.0
            
            # Calculate portfolio value
            portfolio_value = self.calculate_portfolio_value(latest_price.price)
            
            response_data = {
                'price': latest_price.price,
                'change24h': change_24h,
                'volume24h': getattr(latest_price, 'volume', 0),
                'high24h': getattr(latest_price, 'high', latest_price.price),
                'low24h': getattr(latest_price, 'low', latest_price.price),
                'timestamp': latest_price.timestamp.isoformat(),
                'source': getattr(latest_price, 'source', 'unknown'),
                'portfolio_value': portfolio_value,
                'status': 'success'
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Error getting current data: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_unified_history(self, hours):
        """Get unified historical + live data"""
        try:
            resample = request.args.get('resample', None)
            
            data = self.data_manager.get_unified_data(
                hours=hours, 
                include_live=True if hasattr(self.data_manager, 'get_unified_data') else False,
                resample_frequency=resample
            )
            
            if data.empty:
                return jsonify({'error': 'No data available for specified period'}), 404
            
            # Convert to API format
            history = []
            for timestamp, row in data.iterrows():
                history.append({
                    'timestamp': timestamp.isoformat(),
                    'price': row['price'],
                    'volume': row.get('volume', 0),
                    'high': row.get('high', row['price']),
                    'low': row.get('low', row['price']),
                    'open': row.get('open', row['price']),
                    'source': row.get('source', 'unknown')
                })
            
            return jsonify({
                'history': history,
                'count': len(history),
                'period_hours': hours,
                'resample_frequency': resample,
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error getting unified history: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_data_statistics(self):
        """Get data statistics"""
        try:
            stats = self.data_manager.get_statistics()
            return jsonify({
                'statistics': stats,
                'status': 'success'
            })
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_strategy_analysis(self, strategy_name):
        """Get analysis from specific strategy"""
        try:
            if strategy_name not in self.strategies:
                return jsonify({'error': f'Strategy {strategy_name} not found'}), 404
            
            strategy = self.strategies[strategy_name]
            
            # Get recent data for analysis
            data = self.data_manager.get_unified_data(hours=48)
            
            if data.empty:
                return jsonify({'error': 'Insufficient data for analysis'}), 503
            
            # Run strategy analysis (with error handling)
            try:
                if hasattr(strategy, 'analyze_current_market'):
                    analysis = strategy.analyze_current_market(data)
                else:
                    # Fallback analysis
                    analysis = {
                        'current_price': data.iloc[-1]['price'] if not data.empty else 0,
                        'trend': 'UNKNOWN',
                        'signal': 'HOLD',
                        'data_points': len(data)
                    }
            except Exception as e:
                logger.error(f"Strategy analysis error: {e}")
                analysis = {'error': f'Analysis failed: {str(e)}'}
            
            return jsonify({
                'strategy': strategy_name,
                'analysis': analysis,
                'data_points': len(data),
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error in strategy analysis for {strategy_name}: {e}")
            return jsonify({'error': str(e)}), 500
    
    def run_strategy_backtest(self, strategy_name, hours):
        """Run backtest for specific strategy"""
        try:
            if strategy_name not in self.strategies:
                return jsonify({'error': f'Strategy {strategy_name} not found'}), 404
            
            strategy = self.strategies[strategy_name]
            data = self.data_manager.get_unified_data(hours=hours)
            
            if data.empty:
                return jsonify({'error': 'Insufficient data for backtesting'}), 503
            
            # Run backtest (with error handling)
            try:
                if hasattr(strategy, 'backtest'):
                    backtest_result = strategy.backtest(data)
                else:
                    # Fallback result
                    backtest_result = {
                        'total_return_percent': 0,
                        'total_trades': 0,
                        'win_rate_percent': 0,
                        'error': 'Backtest method not available'
                    }
            except Exception as e:
                logger.error(f"Backtest error: {e}")
                backtest_result = {'error': f'Backtest failed: {str(e)}'}
            
            return jsonify({
                'strategy': strategy_name,
                'backtest': backtest_result,
                'period_hours': hours,
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error running backtest for {strategy_name}: {e}")
            return jsonify({'error': str(e)}), 500
    
    def compare_all_strategies(self, hours):
        """Compare performance of all strategies"""
        try:
            results = {}
            data = self.data_manager.get_unified_data(hours=hours)
            
            if data.empty:
                return jsonify({'error': 'Insufficient data for comparison'}), 503
            
            for name, strategy in self.strategies.items():
                try:
                    if hasattr(strategy, 'backtest'):
                        backtest_result = strategy.backtest(data)
                        results[name] = {
                            'returns': backtest_result.get('total_return_percent', 0),
                            'trades': backtest_result.get('total_trades', 0),
                            'win_rate': backtest_result.get('win_rate_percent', 0),
                            'sharpe_ratio': backtest_result.get('sharpe_ratio', 0),
                            'max_drawdown': backtest_result.get('max_drawdown', 0)
                        }
                    else:
                        results[name] = {'error': 'Backtest method not available'}
                except Exception as e:
                    logger.warning(f"Strategy {name} comparison failed: {e}")
                    results[name] = {'error': str(e)}
            
            # Determine winner
            winner = 'none'
            if results:
                winner = max(
                    results.keys(), 
                    key=lambda k: results[k].get('returns', -999)
                )
            
            return jsonify({
                'comparison': results,
                'winner': winner,
                'period_hours': hours,
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error comparing strategies: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_combined_signals(self):
        """Get combined signals from all strategies"""
        try:
            signals = {}
            data = self.data_manager.get_unified_data(hours=24)
            
            for name, strategy in self.strategies.items():
                try:
                    if hasattr(strategy, 'get_current_signal'):
                        signal = strategy.get_current_signal(data)
                        signals[name] = signal
                    else:
                        signals[name] = {'signal': 'HOLD', 'strength': 0.5}
                except Exception as e:
                    signals[name] = {'error': str(e)}
            
            # Calculate combined signal
            hold_count = sum(1 for s in signals.values() if s.get('signal') == 'HOLD')
            buy_count = sum(1 for s in signals.values() if s.get('signal') == 'BUY')
            sell_count = sum(1 for s in signals.values() if s.get('signal') == 'SELL')
            
            combined_signal = 'HOLD'
            if buy_count > sell_count and buy_count > hold_count:
                combined_signal = 'BUY'
            elif sell_count > buy_count and sell_count > hold_count:
                combined_signal = 'SELL'
            
            return jsonify({
                'individual_signals': signals,
                'combined_signal': combined_signal,
                'consensus': f"{buy_count} Buy, {sell_count} Sell, {hold_count} Hold",
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error getting combined signals: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_portfolio_status(self):
        """Get portfolio status"""
        try:
            latest_price = self.data_manager.get_latest_price()
            current_price = latest_price.price if latest_price else 50000
            
            # Update portfolio value
            self.portfolio['total_value'] = self.calculate_portfolio_value(current_price)
            
            return jsonify({
                'portfolio': self.portfolio,
                'current_btc_price': current_price,
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error getting portfolio status: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_portfolio_performance(self):
        """Get portfolio performance metrics"""
        try:
            # Simple performance calculation
            initial_value = 10000.0
            current_value = self.portfolio['total_value']
            total_return = ((current_value - initial_value) / initial_value) * 100
            
            performance = {
                'initial_value': initial_value,
                'current_value': current_value,
                'total_return_percent': total_return,
                'total_trades': self.portfolio['total_trades'],
                'win_rate': (self.portfolio['winning_trades'] / max(self.portfolio['total_trades'], 1)) * 100
            }
            
            return jsonify({
                'performance': performance,
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error calculating performance: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ===== ADVANCED FEATURES ENDPOINTS =====
    
    def get_risk_metrics(self):
        """Get current risk metrics"""
        try:
            if not self.advanced_features_enabled:
                return jsonify({'error': 'Risk management not available'}), 503
            
            portfolio_status = self.portfolio
            risk_metrics = self.risk_calculator.calculate_comprehensive_risk(portfolio_status)
            
            # Check risk violations
            risk_violations = self.portfolio_protector.check_risk_violations(risk_metrics)
            
            return jsonify({
                'risk_metrics': risk_metrics,
                'violations': risk_violations,
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return jsonify({'error': str(e)}), 500
    
    def calculate_position_size_endpoint(self):
        """Calculate position size for a trade"""
        try:
            if not self.advanced_features_enabled:
                return jsonify({'error': 'Risk management not available'}), 503
            
            # Get request data
            data = request.get_json() or {}
            signal = data.get('signal', {})
            
            # Calculate position size
            position_size = self.risk_calculator.calculate_position_size(signal, self.portfolio)
            
            return jsonify({
                'position_size': position_size,
                'portfolio_value': self.portfolio['total_value'],
                'risk_percentage': (position_size / self.portfolio['total_value']) * 100,
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_risk_limits(self):
        """Get current risk limits and settings"""
        try:
            if not self.advanced_features_enabled:
                return jsonify({'error': 'Risk management not available'}), 503
            
            # Return risk configuration
            risk_limits = {
                'max_position_size': getattr(self.risk_calculator, 'max_position_size', 0.1),
                'risk_per_trade': getattr(self.risk_calculator, 'risk_per_trade', 0.02),
                'max_daily_loss': getattr(self.portfolio_protector, 'max_daily_loss', 0.05),
                'current_exposure': self.portfolio.get('btc_holdings', 0),
                'available_balance': self.portfolio.get('balance', 0)
            }
            
            return jsonify({
                'risk_limits': risk_limits,
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error getting risk limits: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_notification_status(self):
        """Get notification system status"""
        try:
            if not self.advanced_features_enabled:
                return jsonify({'error': 'Notifications not available'}), 503
            
            status = {
                'enabled': getattr(self.notification_manager, 'enabled', True),
                'notifications_sent_today': len(getattr(self.notification_manager, 'notifications_sent', [])),
                'last_notification': None
            }
            
            # Get last notification
            history = getattr(self.notification_manager, 'notifications_sent', [])
            if history:
                status['last_notification'] = history[-1]
            
            return jsonify({
                'notification_status': status,
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error getting notification status: {e}")
            return jsonify({'error': str(e)}), 500
    
    def send_test_notification(self):
        """Send a test notification"""
        try:
            if not self.advanced_features_enabled:
                return jsonify({'error': 'Notifications not available'}), 503
            
            # Send test notification
            self.notification_manager.send_alert(
                "Test Alert", 
                "This is a test notification from the trading bot", 
                "info"
            )
            
            return jsonify({
                'message': 'Test notification sent successfully',
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_notification_history_endpoint(self):
        """Get notification history"""
        try:
            if not self.advanced_features_enabled:
                return jsonify({'error': 'Notifications not available'}), 503
            
            history = self.notification_manager.get_notification_history()
            
            return jsonify({
                'notifications': history,
                'count': len(history),
                'status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            return jsonify({'error': str(e)}), 500
    
    def calculate_portfolio_value(self, current_price: float) -> float:
        """Calculate current portfolio value"""
        btc_value = self.portfolio['btc_holdings'] * current_price
        return self.portfolio['balance'] + btc_value
    
    def serve_main_dashboard(self):
        """Serve main dashboard"""
        try:
            dashboard_path = os.path.join(project_root, 'web_interface', 'dashboard.html')
            if os.path.exists(dashboard_path):
                return send_from_directory(os.path.join(project_root, 'web_interface'), 'dashboard.html')
            else:
                return self.generate_simple_dashboard()
        except Exception as e:
            logger.error(f"Dashboard serving error: {e}")
            return self.generate_simple_dashboard()
    
    def serve_risk_dashboard(self):
        """Serve risk dashboard"""
        return self.generate_simple_dashboard("Risk Management Dashboard")
    
    def serve_analytics_dashboard(self):
        """Serve analytics dashboard"""
        return self.generate_simple_dashboard("Analytics Dashboard")
    
    def serve_portfolio_dashboard(self):
        """Serve portfolio dashboard"""
        return self.generate_simple_dashboard("Portfolio Dashboard")
    
    def generate_simple_dashboard(self, title="Odin Trading Bot"):
        """Generate a simple HTML dashboard"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: white; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .card {{ background: #2d2d2d; padding: 20px; margin: 10px 0; border-radius: 8px; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                .status {{ color: #4CAF50; }}
                .error {{ color: #f44336; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 {title}</h1>
                <div class="card">
                    <h3 class="status">✅ Server Running</h3>
                    <p>Your enhanced trading bot is running successfully!</p>
                    <p><strong>Strategies Available:</strong> {len(self.strategies)}</p>
                    <p><strong>Advanced Features:</strong> {'Enabled' if self.advanced_features_enabled else 'Disabled'}</p>
                    <p><strong>Data Manager:</strong> {'Enhanced' if DATA_MANAGER_AVAILABLE else 'Fallback'}</p>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h3>📊 API Endpoints</h3>
                        <ul>
                            <li><a href="/api/current" style="color: #4CAF50;">/api/current</a> - Current price</li>
                            <li><a href="/api/history/24" style="color: #4CAF50;">/api/history/24</a> - 24h history</li>
                            <li><a href="/api/stats" style="color: #4CAF50;">/api/stats</a> - Statistics</li>
                            <li><a href="/api/portfolio" style="color: #4CAF50;">/api/portfolio</a> - Portfolio</li>
                        </ul>
                    </div>
                    
                    <div class="card">
                        <h3>🧠 Available Strategies</h3>
                        <ul>
                            {' '.join([f'<li>{name}</li>' for name in self.strategies.keys()])}
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def not_found(self, error):
        """404 error handler"""
        return jsonify({'error': 'Endpoint not found'}), 404
    
    def server_error(self, error):
        """500 error handler"""
        logger.error(f"Server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    def start_background_tasks(self):
        """Start background monitoring tasks"""
        def monitoring_loop():
            while True:
                try:
                    # Simple background monitoring
                    if hasattr(self.data_manager, 'cleanup_old_data'):
                        self.data_manager.cleanup_old_data()
                    
                    time.sleep(3600)  # Run every hour
                    
                except Exception as e:
                    logger.error(f"Background monitoring error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        thread = threading.Thread(target=monitoring_loop, daemon=True)
        thread.start()
        logger.info("✅ Background monitoring started")
    
    def run(self):
        """Run the enhanced trading bot server"""
        logger.info("🚀 Starting Enhanced Bitcoin Trading Bot Server")
        logger.info(f"📊 Data Manager: {'Enhanced' if DATA_MANAGER_AVAILABLE else 'Fallback mode'}")
        logger.info(f"🧠 Strategies loaded: {list(self.strategies.keys())}")
        logger.info(f"🔧 Advanced features: {'Enabled' if self.advanced_features_enabled else 'Disabled'}")
        logger.info(f"🌐 Server starting on http://localhost:5000")
        
        try:
            self.app.run(host='0.0.0.0', port=5000, debug=False)
        except KeyboardInterrupt:
            logger.info("🛑 Server stopped by user")
        except Exception as e:
            logger.error(f"❌ Server error: {e}")


if __name__ == "__main__":
    try:
        server = EnhancedTradingBotServer()
        server.run()
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        print(f"""
🔧 TROUBLESHOOTING HELP:

1. Database Issues:
   - Make sure the 'data' folder exists in your project root
   - Check file permissions
   - Ensure you have write access to the project directory

2. Missing Modules:
   - This server works with graceful fallbacks
   - Missing advanced features are optional
   - Core functionality should still work

3. Strategy Errors:
   - Check that your strategy files are in the 'strategies' folder
   - Ensure strategy classes have required methods

🚀 Try running again or check the logs above for specific errors.
        """)