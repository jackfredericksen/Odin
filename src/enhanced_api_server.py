# src/fixed_enhanced_api_server.py

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

# Try to import basic strategy first
try:
    from strategies.ma_crossover import MovingAverageCrossoverStrategy
    MA_STRATEGY_AVAILABLE = True
    print("✅ MA Crossover strategy loaded")
except ImportError:
    try:
        from strategies.ma_crossover import MovingAverageCrossoverStrategy
        MA_STRATEGY_AVAILABLE = True
        print("✅ MA Crossover strategy loaded (fallback path)")
    except ImportError:
        print("⚠️ MA Crossover strategy not found")
        MA_STRATEGY_AVAILABLE = False

# Try to import enhanced modules
ENHANCED_FEATURES = True
enhanced_imports = {}

try:
    from risk_management.risk_manager import RiskManager
    enhanced_imports['RiskManager'] = RiskManager
    print("✅ Risk Manager loaded")
except ImportError as e:
    print(f"⚠️ Risk Manager not available: {e}")
    ENHANCED_FEATURES = False

try:
    from strategies.enhanced_strategies import StrategyEnsemble, MultiTimeframeStrategy, MarketRegimeDetector
    enhanced_imports['StrategyEnsemble'] = StrategyEnsemble
    enhanced_imports['MultiTimeframeStrategy'] = MultiTimeframeStrategy
    enhanced_imports['MarketRegimeDetector'] = MarketRegimeDetector
    print("✅ Enhanced strategies loaded")
except ImportError as e:
    print(f"⚠️ Enhanced strategies not available: {e}")
    ENHANCED_FEATURES = False

try:
    from analytics.advanced_analytics import AdvancedAnalytics
    enhanced_imports['AdvancedAnalytics'] = AdvancedAnalytics
    print("✅ Advanced analytics loaded")
except ImportError as e:
    print(f"⚠️ Advanced analytics not available: {e}")
    ENHANCED_FEATURES = False

try:
    # Fixed the typo here: notification_system instead of notifiication_system
    from notifications.notification_system import NotificationSystem, TradeScheduler
    enhanced_imports['NotificationSystem'] = NotificationSystem
    enhanced_imports['TradeScheduler'] = TradeScheduler
    print("✅ Notification system loaded")
except ImportError as e:
    print(f"⚠️ Notification system not available: {e}")
    print("📦 Install required packages: pip install twilio")
    ENHANCED_FEATURES = False

# Import original components
try:
    from src.btc_api_server import BitcoinDataCollector
    DATA_COLLECTOR_AVAILABLE = True
    print("✅ Original data collector loaded")
except ImportError:
    try:
        from btc_api_server import BitcoinDataCollector
        DATA_COLLECTOR_AVAILABLE = True
        print("✅ Data collector loaded (fallback path)")
    except ImportError as e:
        print(f"⚠️ Data collector not available: {e}")
        DATA_COLLECTOR_AVAILABLE = False

# Fallback classes for when enhanced features aren't available
class FallbackStrategy:
    """Fallback strategy when MA crossover isn't available"""
    def analyze_current_market(self):
        import random
        signals = ['BUY', 'SELL', 'HOLD']
        signal = random.choice(signals)
        price = 108500 + random.uniform(-1000, 1000)
        
        return {
            'current_price': price,
            'ma_short': price * 0.995,
            'ma_long': price * 0.99,
            'trend': 'BULLISH' if signal == 'BUY' else 'BEARISH' if signal == 'SELL' else 'NEUTRAL',
            'current_signal': {
                'type': signal,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'price': price,
                'ma_short': price * 0.995,
                'ma_long': price * 0.99
            } if signal != 'HOLD' else None,
            'data_points': 50,
            'strategy': 'Demo Strategy (MA not available)'
        }

class FallbackDataCollector:
    """Fallback data collector for demo purposes"""
    def __init__(self):
        self.latest_data = {
            'price': 108500,
            'change24h': 2.5,
            'high': 110000,
            'low': 107000,
            'volume': 45000000000,
            'timestamp': datetime.now()
        }
        print("✅ Using demo data collector")
        
    def collect_data_once(self):
        import random
        # Simulate realistic price movement
        change = random.uniform(-0.02, 0.02)  # ±2% change
        self.latest_data['price'] *= (1 + change)
        self.latest_data['change24h'] = random.uniform(-5, 5)
        self.latest_data['timestamp'] = datetime.now()
        return True
    
    def get_recent_prices(self, limit=100):
        # Generate demo historical data
        data = []
        base_price = self.latest_data['price']
        
        for i in range(limit):
            timestamp = datetime.now() - timedelta(minutes=i*5)
            price_variation = random.uniform(-0.01, 0.01)
            price = base_price * (1 + price_variation)
            
            data.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'price': price,
                'volume': self.latest_data['volume'] * random.uniform(0.8, 1.2),
                'high': price * 1.01,
                'low': price * 0.99,
                'source': 'demo'
            })
        
        return pd.DataFrame(data)
    
    def get_price_history(self, hours=24):
        # Generate demo historical data
        data = []
        base_price = self.latest_data['price']
        
        for i in range(min(hours * 12, 288)):  # 5-minute intervals
            timestamp = datetime.now() - timedelta(minutes=i*5)
            price_variation = random.uniform(-0.005, 0.005)
            price = base_price * (1 + price_variation)
            
            data.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'price': price
            })
        
        return pd.DataFrame(data)
    
    def start_continuous_collection(self, interval_seconds=60):
        def collect_loop():
            print(f"🔄 Starting demo data collection (every {interval_seconds}s)")
            while True:
                self.collect_data_once()
                time.sleep(interval_seconds)
        
        thread = threading.Thread(target=collect_loop, daemon=True)
        thread.start()
        return thread

class EnhancedTradingServer:
    def __init__(self):
        """Enhanced trading server with proper fallbacks"""
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Initialize data collector
        if DATA_COLLECTOR_AVAILABLE:
            self.data_collector = BitcoinDataCollector()
        else:
            self.data_collector = FallbackDataCollector()
        
        # Initialize strategy
        if MA_STRATEGY_AVAILABLE:
            self.ma_strategy = MovingAverageCrossoverStrategy()
        else:
            self.ma_strategy = FallbackStrategy()
        
        # Initialize enhanced components if available
        if ENHANCED_FEATURES:
            try:
                self.risk_manager = enhanced_imports['RiskManager']()
                self.strategy_ensemble = enhanced_imports['StrategyEnsemble']()
                self.analytics_engine = enhanced_imports['AdvancedAnalytics']()
                self.notification_system = enhanced_imports['NotificationSystem']()
                self.trade_scheduler = enhanced_imports['TradeScheduler']()
                
                # Start scheduler
                self.trade_scheduler.start_scheduler()
                print("✅ All enhanced features initialized")
            except Exception as e:
                print(f"⚠️ Error initializing enhanced features: {e}")
                ENHANCED_FEATURES = False
        
        # Demo portfolio data
        self.demo_portfolio = {
            'total_value': 10000,
            'unrealized_pnl': 0,
            'realized_pnl': 0,
            'open_positions': 0,
            'total_trades': 0,
            'win_rate': 65.5,
            'total_return_pct': 0,
            'max_drawdown_pct': 0,
            'current_drawdown_pct': 0
        }
        
        self.demo_positions = []
        self.demo_trades = []
        self.auto_trading_enabled = False
        self.trading_thread = None
        
        self.setup_routes()
        print(f"🚀 Enhanced Trading Server initialized (Enhanced: {ENHANCED_FEATURES})")
        
    def setup_routes(self):
        """Setup all API routes"""
        # Core routes (always available)
        self.app.route('/api/current', methods=['GET'])(self.get_current_data)
        self.app.route('/api/history/<int:hours>', methods=['GET'])(self.get_price_history)
        self.app.route('/api/recent/<int:limit>', methods=['GET'])(self.get_recent_data)
        self.app.route('/api/stats', methods=['GET'])(self.get_stats)
        self.app.route('/api/strategy/analysis', methods=['GET'])(self.get_strategy_analysis)
        
        # Enhanced routes (with fallbacks)
        self.app.route('/api/ensemble/signal', methods=['GET'])(self.get_ensemble_signal)
        self.app.route('/api/portfolio/status', methods=['GET'])(self.get_portfolio_status)
        self.app.route('/api/portfolio/positions', methods=['GET'])(self.get_open_positions)
        self.app.route('/api/portfolio/trades', methods=['GET'])(self.get_trade_history)
        self.app.route('/api/trading/signals', methods=['GET'])(self.get_trading_signals)
        self.app.route('/api/risk/analysis', methods=['GET'])(self.get_risk_analysis)
        self.app.route('/api/analytics/comprehensive', methods=['GET'])(self.get_comprehensive_analytics)
        
        # Trading actions
        self.app.route('/api/trading/open_position', methods=['POST'])(self.open_position)
        self.app.route('/api/trading/close_position/<int:position_id>', methods=['POST'])(self.close_position)
        self.app.route('/api/trading/auto_toggle', methods=['POST'])(self.toggle_auto_trading)
        
        # Notification routes
        self.app.route('/api/notifications/test', methods=['POST'])(self.test_notification)
        
        # Dashboard route
        self.app.route('/', methods=['GET'])(self.serve_dashboard)
    
    # Core API methods (always work)
    def get_current_data(self):
        """Get current Bitcoin price and stats"""
        try:
            if self.data_collector.latest_data is None:
                self.data_collector.collect_data_once()
            
            if self.data_collector.latest_data:
                df = self.data_collector.get_recent_prices(100)
                data_points = len(df)
                
                return jsonify({
                    'price': self.data_collector.latest_data['price'],
                    'change24h': self.data_collector.latest_data['change24h'],
                    'high24h': self.data_collector.latest_data['high'],
                    'low24h': self.data_collector.latest_data['low'],
                    'volume24h': self.data_collector.latest_data['volume'],
                    'timestamp': self.data_collector.latest_data['timestamp'].isoformat(),
                    'dataPoints': data_points,
                    'status': 'success'
                })
            else:
                return jsonify({'error': 'No data available', 'status': 'error'}), 503
                
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def get_price_history(self, hours):
        """Get price history for specified hours"""
        try:
            df = self.data_collector.get_price_history(hours)
            
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
    
    def get_recent_data(self, limit):
        """Get recent price records"""
        try:
            df = self.data_collector.get_recent_prices(limit)
            
            recent = []
            for _, row in df.iterrows():
                recent.append({
                    'timestamp': row['timestamp'],
                    'price': row['price'],
                    'volume': row.get('volume', 50000000000),
                    'high': row.get('high', row['price'] * 1.02),
                    'low': row.get('low', row['price'] * 0.98)
                })
            
            return jsonify({
                'recent': recent,
                'count': len(recent),
                'status': 'success'
            })
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def get_stats(self):
        """Get overall statistics"""
        try:
            df = self.data_collector.get_recent_prices(1000)
            
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
                'enhancedFeatures': ENHANCED_FEATURES,
                'status': 'success'
            }
            
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def get_strategy_analysis(self):
        """Get strategy analysis"""
        try:
            analysis = self.ma_strategy.analyze_current_market()
            return jsonify(analysis)
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    # Enhanced API methods (with fallbacks)
    def get_ensemble_signal(self):
        """Get ensemble strategy signal (or fallback)"""
        try:
            if ENHANCED_FEATURES and hasattr(self, 'strategy_ensemble'):
                signal_data = self.strategy_ensemble.get_ensemble_signal()
                return jsonify(signal_data)
            else:
                # Fallback to basic strategy
                analysis = self.ma_strategy.analyze_current_market()
                
                # Convert to ensemble format
                signal = 'HOLD'
                confidence = 0.3
                
                if analysis.get('current_signal'):
                    signal = analysis['current_signal']['type']
                    confidence = 0.7
                elif analysis.get('trend') == 'BULLISH':
                    signal = 'BUY'
                    confidence = 0.4
                elif analysis.get('trend') == 'BEARISH':
                    signal = 'SELL'
                    confidence = 0.4
                
                return jsonify({
                    'ensemble_signal': signal,
                    'confidence': confidence,
                    'individual_signals': {
                        'ma_crossover': {
                            'signal': signal,
                            'confidence': confidence
                        }
                    },
                    'market_regime': {'regime': 'UNKNOWN'},
                    'status': 'fallback'
                })
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def get_portfolio_status(self):
        """Get portfolio status (enhanced or demo)"""
        try:
            if ENHANCED_FEATURES and hasattr(self, 'risk_manager'):
                metrics = self.risk_manager.calculate_portfolio_metrics()
                return jsonify(metrics)
            else:
                # Return demo portfolio data
                import random
                self.demo_portfolio['daily_pnl'] = random.uniform(-100, 100)
                return jsonify(self.demo_portfolio)
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def get_open_positions(self):
        """Get open positions"""
        try:
            if ENHANCED_FEATURES and hasattr(self, 'risk_manager'):
                positions = []
                for pos_id, position in self.risk_manager.positions.items():
                    positions.append({
                        'id': pos_id,
                        'strategy_name': position['strategy_name'],
                        'symbol': position['symbol'],
                        'side': position['side'],
                        'entry_price': position['entry_price'],
                        'current_price': position['current_price'],
                        'quantity': position['quantity'],
                        'unrealized_pnl': position['unrealized_pnl'],
                        'stop_loss': position['stop_loss'],
                        'take_profit': position['take_profit'],
                        'entry_time': position['entry_time'],
                        'duration': (datetime.now() - datetime.fromisoformat(position['entry_time'])).total_seconds() / 3600
                    })
                return jsonify({'positions': positions, 'count': len(positions)})
            else:
                return jsonify({'positions': self.demo_positions, 'count': len(self.demo_positions)})
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def get_trade_history(self):
        """Get trade history"""
        try:
            if ENHANCED_FEATURES and hasattr(self, 'risk_manager'):
                trades = self.risk_manager.trade_history[-50:]
                return jsonify({'trades': trades, 'count': len(trades)})
            else:
                return jsonify({'trades': self.demo_trades, 'count': len(self.demo_trades)})
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def get_trading_signals(self):
        """Get current trading signals"""
        return self.get_ensemble_signal()  # Same as ensemble signal
    
    def get_risk_analysis(self):
        """Get risk analysis"""
        try:
            if ENHANCED_FEATURES and hasattr(self, 'risk_manager'):
                metrics = self.risk_manager.calculate_portfolio_metrics()
                risk_signals = self.risk_manager.get_risk_signals()
                return jsonify({
                    'metrics': metrics,
                    'risk_signals': risk_signals,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'metrics': self.demo_portfolio,
                    'risk_signals': [],
                    'timestamp': datetime.now().isoformat(),
                    'status': 'demo'
                })
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def get_comprehensive_analytics(self):
        """Get comprehensive analytics"""
        try:
            if ENHANCED_FEATURES and hasattr(self, 'analytics_engine'):
                report = self.analytics_engine.generate_comprehensive_report()
                return jsonify(report)
            else:
                # Return demo analytics
                return jsonify({
                    'basic_statistics': {
                        'total_trades': 0,
                        'profitable_trades': 0,
                        'win_rate': 0,
                        'total_pnl': 0,
                        'avg_win_percent': 0,
                        'avg_loss_percent': 0,
                        'profit_factor': 0
                    },
                    'risk_adjusted_metrics': {
                        'sharpe_ratio': 0,
                        'sortino_ratio': 0,
                        'calmar_ratio': 0,
                        'var_95_percent': 0,
                        'cvar_95_percent': 0
                    },
                    'status': 'demo'
                })
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    # Trading actions (demo versions)
    def open_position(self):
        """Open a trading position (demo)"""
        try:
            data = request.get_json()
            
            if ENHANCED_FEATURES and hasattr(self, 'risk_manager'):
                # Use real risk manager
                strategy_name = data.get('strategy', 'manual')
                current_price = self.data_collector.latest_data['price']
                side = data.get('side', 'long')
                
                result = self.risk_manager.open_position(
                    strategy_name=strategy_name,
                    symbol='BTC',
                    side=side,
                    entry_price=current_price
                )
                return jsonify(result)
            else:
                # Demo mode
                import random
                position_id = len(self.demo_positions) + 1
                current_price = self.data_collector.latest_data['price']
                
                position = {
                    'id': position_id,
                    'strategy_name': data.get('strategy', 'manual'),
                    'symbol': 'BTC',
                    'side': data.get('side', 'long'),
                    'entry_price': current_price,
                    'current_price': current_price,
                    'quantity': 100 / current_price,  # $100 position
                    'unrealized_pnl': 0,
                    'entry_time': datetime.now().isoformat(),
                    'stop_loss': current_price * 0.95,
                    'take_profit': current_price * 1.10
                }
                
                self.demo_positions.append(position)
                self.demo_portfolio['open_positions'] = len(self.demo_positions)
                
                return jsonify({'success': True, 'position_id': position_id, 'position': position})
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def close_position(self, position_id):
        """Close a trading position (demo)"""
        try:
            if ENHANCED_FEATURES and hasattr(self, 'risk_manager'):
                current_price = self.data_collector.latest_data['price']
                result = self.risk_manager.close_position(position_id, current_price, 'manual')
                return jsonify(result)
            else:
                # Demo mode
                for i, position in enumerate(self.demo_positions):
                    if position['id'] == position_id:
                        current_price = self.data_collector.latest_data['price']
                        
                        # Calculate P&L
                        if position['side'] == 'long':
                            pnl = (current_price - position['entry_price']) * position['quantity']
                        else:
                            pnl = (position['entry_price'] - current_price) * position['quantity']
                        
                        # Create trade record
                        trade = {
                            'id': len(self.demo_trades) + 1,
                            'strategy_name': position['strategy_name'],
                            'symbol': position['symbol'],
                            'side': position['side'],
                            'entry_price': position['entry_price'],
                            'exit_price': current_price,
                            'quantity': position['quantity'],
                            'entry_time': position['entry_time'],
                            'exit_time': datetime.now().isoformat(),
                            'pnl': pnl,
                            'pnl_percent': (pnl / (position['entry_price'] * position['quantity'])) * 100,
                            'exit_reason': 'manual'
                        }
                        
                        self.demo_trades.append(trade)
                        self.demo_positions.pop(i)
                        self.demo_portfolio['open_positions'] = len(self.demo_positions)
                        self.demo_portfolio['realized_pnl'] += pnl
                        
                        return jsonify({'success': True, 'trade': trade})
                
                return jsonify({'error': 'Position not found'}, 404)
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def toggle_auto_trading(self):
        """Toggle auto trading"""
        try:
            self.auto_trading_enabled = not self.auto_trading_enabled
            
            message = "Auto trading enabled" if self.auto_trading_enabled else "Auto trading disabled"
            
            return jsonify({
                'auto_trading_enabled': self.auto_trading_enabled,
                'message': message,
                'enhanced_features': ENHANCED_FEATURES
            })
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def test_notification(self):
        """Test notification system"""
        try:
            if ENHANCED_FEATURES and hasattr(self, 'notification_system'):
                data = request.get_json()
                message = data.get('message', 'Test notification from Bitcoin Trading Bot')
                alert_type = data.get('type', 'info')
                
                result = self.notification_system.send_system_alert(message, alert_type)
                return jsonify(result)
            else:
                return jsonify({
                    'success': False,
                    'message': 'Notification system not available',
                    'enhanced_features': ENHANCED_FEATURES
                })
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    def serve_dashboard(self):
        """Serve the dashboard"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            dashboard_path = os.path.join(project_root, 'web_interface')
            
            # Try enhanced dashboard first
            enhanced_dashboard_path = os.path.join(dashboard_path, 'enhanced_dashboard.html')
            if os.path.exists(enhanced_dashboard_path):
                return send_from_directory(dashboard_path, 'enhanced_dashboard.html')
            
            # Try original dashboard
            original_dashboard_path = os.path.join(dashboard_path, 'dashboard.html')
            if os.path.exists(original_dashboard_path):
                return send_from_directory(dashboard_path, 'dashboard.html')
            
            # Return status page if no dashboard found
            return self.get_status_page()
        except Exception as e:
            return self.get_status_page(str(e))
    
    def get_status_page(self, error_msg=None):
        """Generate status page"""
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bitcoin Trading Bot - Fixed Enhanced Server</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
                    color: white;
                    margin: 0;
                    padding: 40px;
                    min-height: 100vh;
                }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .status {{ padding: 20px; background: rgba(255,255,255,0.1); border-radius: 15px; margin: 20px 0; }}
                .success {{ border-left: 4px solid #00ff88; }}
                .warning {{ border-left: 4px solid #ffa500; }}
                .error {{ border-left: 4px solid #ff4757; }}
                .endpoints {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                .endpoint-group {{ background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; }}
                .endpoint {{ margin: 8px 0; }}
                .endpoint a {{ color: #00ff88; text-decoration: none; }}
                .endpoint a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Bitcoin Trading Bot - Fixed Enhanced Server</h1>
                    <p>Status: <strong>{"✅ RUNNING" if not error_msg else "❌ ERROR"}</strong></p>
                </div>
                
                <div class="status {'success' if ENHANCED_FEATURES else 'warning'}">
                    <h3>🧠 Enhanced Features: {"✅ AVAILABLE" if ENHANCED_FEATURES else "⚠️ FALLBACK MODE"}</h3>
                    <p>MA Strategy: {"✅" if MA_STRATEGY_AVAILABLE else "❌"} | 
                       Data Collector: {"✅" if DATA_COLLECTOR_AVAILABLE else "❌ (using demo)"}</p>
                </div>
                
                {f'<div class="status error"><h3>❌ Error</h3><p>{error_msg}</p></div>' if error_msg else ''}
                
                <div class="endpoints">
                    <div class="endpoint-group">
                        <h3>📊 Core API (Always Available)</h3>
                        <div class="endpoint"><a href="/api/current">/api/current</a> - Current price</div>
                        <div class="endpoint"><a href="/api/history/24">/api/history/24</a> - 24h history</div>
                        <div class="endpoint"><a href="/api/recent/10">/api/recent/10</a> - Recent data</div>
                        <div class="endpoint"><a href="/api/stats">/api/stats</a> - Statistics</div>
                        <div class="endpoint"><a href="/api/strategy/analysis">/api/strategy/analysis</a> - Strategy</div>
                    </div>
                    
                    <div class="endpoint-group">
                        <h3>🎯 Enhanced API ({"Available" if ENHANCED_FEATURES else "Demo Mode"})</h3>
                        <div class="endpoint"><a href="/api/ensemble/signal">/api/ensemble/signal</a> - Ensemble signal</div>
                        <div class="endpoint"><a href="/api/portfolio/status">/api/portfolio/status</a> - Portfolio</div>
                        <div class="endpoint"><a href="/api/risk/analysis">/api/risk/analysis</a> - Risk analysis</div>
                        <div class="endpoint"><a href="/api/analytics/comprehensive">/api/analytics/comprehensive</a> - Analytics</div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 40px; opacity: 0.8;">
                    <p>🌐 Server running on port 5000 | 📊 {"Real" if DATA_COLLECTOR_AVAILABLE else "Demo"} data</p>
                    <p>🚀 Dashboard: Place enhanced_dashboard.html in web_interface/ folder</p>
                    <p>📦 To enable all features: pip install twilio scipy</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the fixed enhanced trading server"""
        print("\n🚀 Bitcoin Trading Bot - Fixed Enhanced Server")
        print("=" * 60)
        print(f"📁 Working Directory: {os.getcwd()}")
        print(f"🧠 Enhanced Features: {'✅ ENABLED' if ENHANCED_FEATURES else '⚠️ FALLBACK MODE'}")
        print(f"📊 Data Source: {'✅ Real API' if DATA_COLLECTOR_AVAILABLE else '⚠️ Demo Data'}")
        print(f"🎯 MA Strategy: {'✅ Available' if MA_STRATEGY_AVAILABLE else '⚠️ Demo Signals'}")
        
        if ENHANCED_FEATURES:
            print(f"⚡ Risk Management: ✅ Active")
            print(f"🧠 Strategy Ensemble: ✅ Multi-timeframe")
            print(f"📈 Advanced Analytics: ✅ Comprehensive")
            print(f"🔔 Notifications: ✅ Multi-channel")
        else:
            print(f"📦 To enable enhanced features:")
            print(f"   1. pip install twilio scipy")
            print(f"   2. Create missing module files")
            print(f"   3. Restart server")
        
        # Start data collection
        print(f"\n🔄 Starting background data collection...")
        self.data_collector.start_continuous_collection(interval_seconds=60)
        
        # Collect initial data
        print(f"📊 Fetching initial data...")
        self.data_collector.collect_data_once()
        
        print(f"\n🌐 Starting API server...")
        print(f"📱 Dashboard: http://localhost:{port}")
        print(f"🔗 API Status: http://localhost:{port}/api/current")
        print(f"📊 Full API list: http://localhost:{port}")
        print(f"\n{'✅ All systems ready!' if ENHANCED_FEATURES else '⚠️ Running in fallback mode - basic features only'}")
        print(f"Press Ctrl+C to stop the server\n")
        
        try:
            self.app.run(host=host, port=port, debug=debug, threaded=True)
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            if ENHANCED_FEATURES and hasattr(self, 'trade_scheduler'):
                self.trade_scheduler.stop_scheduler()


def main():
    """Main entry point with error handling"""
    try:
        server = EnhancedTradingServer()
        server.run(debug=False)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print(f"\n🔧 Troubleshooting:")
        print(f"1. Check if all required files are in place")
        print(f"2. Install dependencies: pip install pandas numpy flask flask-cors")
        print(f"3. For enhanced features: pip install twilio scipy")
        print(f"4. Make sure port 5000 is available")


if __name__ == "__main__":
    main()