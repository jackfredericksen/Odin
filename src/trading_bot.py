import sys
import os
import time
import threading
from datetime import datetime, timedelta
import json

# Add project paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'strategies'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'paper_trading'))

try:
    from ma_crossover import MovingAverageCrossoverStrategy
    from rsi_strategy import RSIStrategy
    from bollinger_bands import BollingerBandsStrategy
    from macd_strategy import MACDStrategy
    from portfolio_manager import PaperTradingPortfolio, AutomatedTrader
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all strategy files are in the strategies/ folder")
    sys.exit(1)

class OdinTradingBot:
    def __init__(self, initial_balance: float = 10000.0, trading_enabled: bool = False):
        """
        Odin Trading Bot - Automated cryptocurrency trading system with real market data
        
        Args:
            initial_balance: Starting balance for paper trading
            trading_enabled: Enable/disable automated trading
        """
        self.trading_enabled = trading_enabled
        self.running = False
        self.current_price = 0.0
        self.price_source = "Unknown"
        self.data_collector = None
        self.price_history = []
        
        # Connect to real market data
        self.real_data_connected = self._connect_to_data_source()
        
        # Initialize paper trading portfolio
        self.portfolio = PaperTradingPortfolio(initial_balance)
        
        # Initialize automated trader
        self.auto_trader = AutomatedTrader(self.portfolio)
        
        # Initialize strategies
        self.strategies = {
            'MA': MovingAverageCrossoverStrategy(),
            'RSI': RSIStrategy(),
            'BB': BollingerBandsStrategy(),
            'MACD': MACDStrategy()
        }
        
        # Register strategies for automated trading
        if trading_enabled:
            for name, strategy in self.strategies.items():
                self.auto_trader.register_strategy(name, strategy)
                
        # Trading statistics
        self.stats = {
            'total_signals': 0,
            'executed_trades': 0,
            'start_time': datetime.now(),
            'last_trade_time': None,
            'price_updates': 0,
            'real_data_usage': 0
        }
        
        print(f"⚡ Odin Trading Bot Initialized")
        print(f"   💰 Initial Balance: ${initial_balance:,.2f}")
        print(f"   🤖 Auto Trading: {'ENABLED' if trading_enabled else 'DISABLED'}")
        print(f"   📊 Real Market Data: {'CONNECTED' if self.real_data_connected else 'DISCONNECTED'}")
        print(f"   🎯 Strategies: {', '.join(self.strategies.keys())}")
        
    def _connect_to_data_source(self):
        """Connect to the existing Bitcoin data collection system"""
        try:
            # Try to import and connect to the main data collector
            from btc_api_server import collector
            self.data_collector = collector
            print("✅ Connected to real Bitcoin market data source")
            return True
        except ImportError as e:
            print(f"⚠️ Could not connect to real data source: {e}")
            print("⚠️ Trading bot will use fallback price data")
            return False
    
    def get_current_bitcoin_price(self) -> float:
        """Get current Bitcoin price from real market data sources"""
        try:
            if self.real_data_connected and self.data_collector:
                # Try to get latest price from the main data collector
                if hasattr(self.data_collector, 'latest_data') and self.data_collector.latest_data:
                    price_data = self.data_collector.latest_data
                    price = price_data['price']
                    self.price_source = f"Real market data from {price_data['source']}"
                    self.stats['real_data_usage'] += 1
                    
                    # Track price history for trend analysis
                    self.price_history.append({
                        'price': price,
                        'timestamp': price_data['timestamp'],
                        'source': price_data['source']
                    })
                    
                    # Keep only last 100 prices for performance
                    if len(self.price_history) > 100:
                        self.price_history = self.price_history[-100:]
                    
                    return price
                
                # Try to fetch fresh data from APIs
                print("📊 Fetching fresh market data...")
                price_data = self.data_collector.fetch_current_price()
                if price_data:
                    price = price_data['price']
                    self.price_source = f"Fresh market data from {price_data['source']}"
                    self.stats['real_data_usage'] += 1
                    return price
                
                # Fallback to database
                print("📊 Using latest database price...")
                df = self.data_collector.get_recent_prices(1)
                if len(df) > 0:
                    price = float(df.iloc[0]['price'])
                    self.price_source = "Latest database price"
                    return price
            
            # Final fallback - use last known price or default
            if self.current_price > 0:
                self.price_source = "Last known price (data unavailable)"
                print("⚠️ Using last known price - real market data unavailable")
                return self.current_price
            else:
                self.price_source = "Default fallback price"
                print("⚠️ No price data available - using fallback")
                return 45000.0
                
        except Exception as e:
            print(f"❌ Error getting Bitcoin price: {e}")
            self.price_source = f"Error fallback: {str(e)}"
            return self.current_price or 45000.0
    
    def get_price_change_info(self) -> dict:
        """Get price change information from real market data"""
        if len(self.price_history) < 2:
            return {
                'change': 0,
                'change_percent': 0,
                'trend': 'NEUTRAL',
                'current_price': self.current_price,
                'previous_price': self.current_price
            }
        
        current = self.price_history[-1]['price']
        previous = self.price_history[-2]['price']
        
        change = current - previous
        change_percent = (change / previous) * 100 if previous != 0 else 0
        
        # Determine trend based on price movement
        if change_percent > 0.1:
            trend = 'BULLISH'
        elif change_percent < -0.1:
            trend = 'BEARISH'
        else:
            trend = 'NEUTRAL'
        
        return {
            'change': change,
            'change_percent': change_percent,
            'trend': trend,
            'current_price': current,
            'previous_price': previous
        }
    
    def analyze_market(self) -> dict:
        """Analyze market using all strategies with real data"""
        analysis_results = {}
        
        for name, strategy in self.strategies.items():
            try:
                analysis = strategy.analyze_current_market()
                analysis_results[name] = analysis
            except Exception as e:
                print(f"❌ Error analyzing {name} strategy: {e}")
                analysis_results[name] = {'error': str(e)}
                
        return analysis_results
        
    def process_trading_cycle(self):
        """Execute one complete trading cycle with real market data"""
        # Get REAL current price
        previous_price = self.current_price
        self.current_price = self.get_current_bitcoin_price()
        self.stats['price_updates'] += 1
        
        # Get price change information
        price_info = self.get_price_change_info()
        
        # Log price updates with real market context
        if previous_price != self.current_price and previous_price > 0:
            change = self.current_price - previous_price
            change_pct = (change / previous_price * 100) if previous_price else 0
            trend_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            print(f"📊 {trend_emoji} Price Update: ${self.current_price:,.2f} ({change_pct:+.2f}%) - {self.price_source}")
        
        # Analyze market conditions
        market_analysis = self.analyze_market()
        
        # Count and analyze signals
        active_signals = 0
        signal_details = []
        for name, analysis in market_analysis.items():
            if 'error' not in analysis and analysis.get('current_signal'):
                active_signals += 1
                self.stats['total_signals'] += 1
                signal_details.append({
                    'strategy': name,
                    'signal': analysis['current_signal']['type'],
                    'strength': analysis['current_signal'].get('strength', 1.0),
                    'price': analysis['current_signal'].get('price', self.current_price)
                })
                
        # Process automated trading if enabled
        executed_trades = []
        if self.trading_enabled and active_signals > 0:
            print(f"🤖 Processing {active_signals} signals with REAL price ${self.current_price:,.2f}")
            executed_trades = self.auto_trader.process_signals(self.current_price)
            
            if executed_trades:
                self.stats['executed_trades'] += len(executed_trades)
                self.stats['last_trade_time'] = datetime.now()
                print(f"✅ Executed {len(executed_trades)} trades at REAL market price!")
                
        # Update portfolio with REAL current price
        self.portfolio.update_positions(self.current_price)
        
        # Get portfolio summary
        portfolio_summary = self.portfolio.get_portfolio_summary()
        
        # Enhanced logging with real market context
        print(f"\n🔄 Trading Cycle @ {datetime.now().strftime('%H:%M:%S')}")
        print(f"   💰 BTC Price: ${self.current_price:,.2f} ({price_info['trend']})")
        print(f"   📡 Data Source: {self.price_source}")
        print(f"   🎯 Active Signals: {active_signals}")
        
        # Show signal details
        if signal_details:
            for signal in signal_details:
                strength_bar = "🟢" * int(signal['strength'] * 5)
                print(f"      {signal['strategy']}: {signal['signal']} {strength_bar}")
        
        print(f"   💼 Portfolio Value: ${portfolio_summary['total_equity']:,.2f}")
        print(f"   📈 P&L: ${portfolio_summary['total_pnl']:+,.2f} ({portfolio_summary['total_return_percent']:+.2f}%)")
        
        # Show executed trades with real price confirmation
        if executed_trades:
            print(f"   ⚡ Executed {len(executed_trades)} trades at REAL price:")
            for trade in executed_trades:
                print(f"      {trade.side.upper()} {trade.quantity:.6f} BTC @ ${trade.price:,.2f} ({trade.strategy})")
                
        return {
            'current_price': self.current_price,
            'price_source': self.price_source,
            'price_info': price_info,
            'market_analysis': market_analysis,
            'executed_trades': [trade.to_dict() for trade in executed_trades],
            'portfolio_summary': portfolio_summary,
            'active_signals': active_signals,
            'signal_details': signal_details
        }
        
    def start_trading(self, cycle_interval: int = 60):
        """Start the automated trading bot with real market data"""
        if self.running:
            print("⚠️ Trading bot is already running")
            return
            
        self.running = True
        print(f"\n🚀 Starting Odin Trading Bot")
        print(f"   ⏱️ Cycle Interval: {cycle_interval} seconds")
        print(f"   📊 Real Market Data: {'CONNECTED' if self.real_data_connected else 'FALLBACK MODE'}")
        print(f"   🤖 Automated Trading: {'ON' if self.trading_enabled else 'OFF'}")
        print(f"   🛑 Press Ctrl+C to stop")
        
        if not self.real_data_connected:
            print("⚠️ WARNING: Not connected to real market data! Trades may not reflect actual market conditions.")
        
        try:
            while self.running:
                cycle_result = self.process_trading_cycle()
                
                # Sleep until next cycle
                time.sleep(cycle_interval)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Trading bot stopped by user")
        except Exception as e:
            print(f"\n❌ Trading bot error: {e}")
        finally:
            self.running = False
            self.stop_trading()
            
    def stop_trading(self):
        """Stop the trading bot and save final state"""
        self.running = False
        
        # Save portfolio state
        self.portfolio.save_portfolio_state()
        
        # Print final statistics
        self.print_final_stats()
        
    def print_final_stats(self):
        """Print comprehensive trading session statistics with real data context"""
        print(f"\n📊 Odin Trading Session Summary")
        print("=" * 50)
        
        # Session stats
        runtime = datetime.now() - self.stats['start_time']
        print(f"⏱️ Runtime: {str(runtime).split('.')[0]}")
        print(f"📊 Market Data: {'REAL' if self.real_data_connected else 'FALLBACK'}")
        print(f"📈 Price Updates: {self.stats['price_updates']}")
        print(f"✅ Real Data Usage: {self.stats['real_data_usage']}/{self.stats['price_updates']}")
        print(f"🎯 Total Signals: {self.stats['total_signals']}")
        print(f"⚡ Executed Trades: {self.stats['executed_trades']}")
        
        if self.stats['last_trade_time']:
            print(f"🕐 Last Trade: {self.stats['last_trade_time'].strftime('%H:%M:%S')}")
            
        # Show recent data sources if available
        if self.price_history:
            recent_sources = [p['source'] for p in self.price_history[-10:]]
            unique_sources = list(set(recent_sources))
            print(f"📡 Data Sources Used: {', '.join(unique_sources)}")
            
        # Portfolio performance
        portfolio_summary = self.portfolio.get_portfolio_summary()
        print(f"\n💼 Portfolio Performance:")
        print(f"   Initial Balance: ${self.portfolio.initial_balance:,.2f}")
        print(f"   Final Equity: ${portfolio_summary['total_equity']:,.2f}")
        print(f"   Total P&L: ${portfolio_summary['total_pnl']:+,.2f}")
        print(f"   Return: {portfolio_summary['total_return_percent']:+.2f}%")
        print(f"   Cash Balance: ${portfolio_summary['cash_balance']:,.2f}")
        print(f"   Position Value: ${portfolio_summary['position_value']:,.2f}")
        print(f"   Active Positions: {portfolio_summary['position_count']}")
        print(f"   Final BTC Price: ${self.current_price:,.2f}")
        
        # Strategy performance
        print(f"\n🧠 Strategy Performance:")
        best_strategy = None
        best_performance = float('-inf')
        
        for strategy_name in self.strategies.keys():
            perf = self.portfolio.get_strategy_performance(strategy_name)
            if 'error' not in perf and perf['completed_trades'] > 0:
                print(f"   {strategy_name}:")
                print(f"      Trades: {perf['completed_trades']}")
                print(f"      Win Rate: {perf['win_rate']:.1f}%")
                print(f"      P&L: ${perf['net_pnl']:+,.2f}")
                print(f"      Avg Trade: ${perf['avg_trade_pnl']:+,.2f}")
                
                if perf['net_pnl'] > best_performance:
                    best_performance = perf['net_pnl']
                    best_strategy = strategy_name
                    
        if best_strategy:
            print(f"\n🏆 Best Strategy: {best_strategy} (${best_performance:+,.2f})")
        
        # Data quality summary
        if self.real_data_connected and self.stats['real_data_usage'] > 0:
            data_quality = (self.stats['real_data_usage'] / self.stats['price_updates']) * 100
            print(f"\n📊 Data Quality: {data_quality:.1f}% real market data")
            print(f"✅ All trades executed with real market prices")
        else:
            print(f"\n⚠️ Limited real market data - results may not reflect actual trading conditions")
            
        print(f"\n💾 Portfolio state saved to database")
        
    def get_portfolio_status(self) -> dict:
        """Get current portfolio status for API"""
        portfolio_summary = self.portfolio.get_portfolio_summary()
        
        # Add bot-specific information with real data context
        portfolio_summary.update({
            'bot_running': self.running,
            'trading_enabled': self.trading_enabled,
            'current_price': self.current_price,
            'price_source': self.price_source,
            'real_data_connected': self.real_data_connected,
            'total_signals': self.stats['total_signals'],
            'executed_trades': self.stats['executed_trades'],
            'price_updates': self.stats['price_updates'],
            'real_data_usage': self.stats['real_data_usage'],
            'runtime': str(datetime.now() - self.stats['start_time']).split('.')[0] if self.stats['start_time'] else '0:00:00'
        })
        
        return portfolio_summary
        
    def enable_trading(self):
        """Enable automated trading"""
        if not self.trading_enabled:
            self.trading_enabled = True
            # Register all strategies
            for name, strategy in self.strategies.items():
                self.auto_trader.register_strategy(name, strategy)
            print("✅ Automated trading ENABLED (using real market data)")
        else:
            print("⚠️ Automated trading already enabled")
            
    def disable_trading(self):
        """Disable automated trading"""
        if self.trading_enabled:
            self.trading_enabled = False
            # Clear registered strategies
            self.auto_trader.active_strategies.clear()
            self.auto_trader.last_signals.clear()
            print("🛑 Automated trading DISABLED")
        else:
            print("⚠️ Automated trading already disabled")
            
    def manual_trade(self, side: str, quantity: float, strategy: str = 'Manual') -> dict:
        """Execute a manual trade at real market price"""
        try:
            # Get current REAL market price
            current_price = self.get_current_bitcoin_price()
            
            print(f"📊 Executing manual {side} trade at real market price: ${current_price:,.2f}")
            print(f"📡 Price source: {self.price_source}")
            
            trade = self.portfolio.execute_trade(
                symbol='BTC',
                side=side,
                quantity=quantity,
                price=current_price,
                strategy=strategy,
                signal_strength=1.0
            )
            
            if trade:
                return {
                    'success': True,
                    'trade': trade.to_dict(),
                    'portfolio': self.portfolio.get_portfolio_summary(),
                    'real_price': current_price,
                    'price_source': self.price_source
                }
            else:
                return {
                    'success': False,
                    'error': 'Trade execution failed',
                    'price_source': self.price_source
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'price_source': getattr(self, 'price_source', 'Unknown')
            }
            
    def reset_portfolio(self, new_balance: float = 10000.0):
        """Reset portfolio to initial state"""
        try:
            # Clear all positions and trades
            self.portfolio.positions.clear()
            self.portfolio.trade_history.clear()
            self.portfolio.cash_balance = new_balance
            self.portfolio.initial_balance = new_balance
            
            # Clear database
            import sqlite3
            conn = sqlite3.connect(self.portfolio.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM positions')
            cursor.execute('DELETE FROM trades') 
            cursor.execute('DELETE FROM portfolio_state')
            cursor.execute('DELETE FROM strategy_performance')
            
            conn.commit()
            conn.close()
            
            # Reset stats
            self.stats = {
                'total_signals': 0,
                'executed_trades': 0,
                'start_time': datetime.now(),
                'last_trade_time': None,
                'price_updates': 0,
                'real_data_usage': 0
            }
            
            print(f"🔄 Portfolio reset to ${new_balance:,.2f}")
            print(f"📊 Real market data connection: {'ACTIVE' if self.real_data_connected else 'INACTIVE'}")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting portfolio: {e}")
            return False

def main():
    """Main function to run Odin Trading Bot with real market data"""
    print("⚡ Odin - Advanced Bitcoin Trading Bot")
    print("=" * 50)
    
    # Configuration
    INITIAL_BALANCE = 10000.0
    TRADING_ENABLED = False  # Set to True for live automated trading
    CYCLE_INTERVAL = 60  # seconds between trading cycles
    
    # Create trading bot
    bot = OdinTradingBot(
        initial_balance=INITIAL_BALANCE,
        trading_enabled=TRADING_ENABLED
    )
    
    # Test real market data connection
    test_price = bot.get_current_bitcoin_price()
    print(f"📊 Current Bitcoin Price: ${test_price:,.2f}")
    print(f"📡 Data Source: {bot.price_source}")
    
    # Interactive menu
    while True:
        print(f"\n⚡ Odin Trading Bot Menu")
        print("1. 🚀 Start Trading Bot")
        print("2. 📊 View Portfolio Status")
        print("3. 📈 View Strategy Performance")
        print("4. 💰 Manual Trade")
        print("5. 🤖 Toggle Auto Trading")
        print("6. 🔄 Reset Portfolio")
        print("7. 📋 View Recent Trades")
        print("8. 📡 Check Market Data Connection")
        print("9. 🛑 Exit")
        
        choice = input("\nSelect option (1-9): ").strip()
        
        if choice == '1':
            if not bot.running:
                cycle_interval = input(f"Cycle interval (default {CYCLE_INTERVAL}s): ").strip()
                interval = int(cycle_interval) if cycle_interval.isdigit() else CYCLE_INTERVAL
                bot.start_trading(interval)
            else:
                print("⚠️ Bot is already running")
                
        elif choice == '2':
            status = bot.get_portfolio_status()
            print(f"\n💼 Portfolio Status:")
            print(f"   Total Equity: ${status['total_equity']:,.2f}")
            print(f"   Cash: ${status['cash_balance']:,.2f}")
            print(f"   Positions: ${status['position_value']:,.2f}")
            print(f"   P&L: ${status['total_pnl']:+,.2f} ({status['total_return_percent']:+.2f}%)")
            print(f"   Active Positions: {status['position_count']}")
            print(f"   Total Trades: {status['total_trades']}")
            print(f"   Bot Status: {'RUNNING' if status['bot_running'] else 'STOPPED'}")
            print(f"   Auto Trading: {'ON' if status['trading_enabled'] else 'OFF'}")
            print(f"   Current Price: ${status['current_price']:,.2f}")
            print(f"   Data Source: {status['price_source']}")
            print(f"   Real Data: {'CONNECTED' if status['real_data_connected'] else 'DISCONNECTED'}")
            
        elif choice == '3':
            print(f"\n🧠 Strategy Performance:")
            for strategy_name in bot.strategies.keys():
                perf = bot.portfolio.get_strategy_performance(strategy_name)
                if 'error' not in perf and perf['completed_trades'] > 0:
                    print(f"   {strategy_name}:")
                    print(f"      Completed Trades: {perf['completed_trades']}")
                    print(f"      Win Rate: {perf['win_rate']:.1f}%")
                    print(f"      Total P&L: ${perf['total_realized_pnl']:+,.2f}")
                    print(f"      Net P&L: ${perf['net_pnl']:+,.2f}")
                    print(f"      Avg Trade: ${perf['avg_trade_pnl']:+,.2f}")
                else:
                    print(f"   {strategy_name}: No completed trades")
                    
        elif choice == '4':
            side = input("Trade side (buy/sell): ").strip().lower()
            if side in ['buy', 'sell']:
                try:
                    quantity = float(input("Quantity (BTC): ").strip())
                    result = bot.manual_trade(side, quantity)
                    
                    if result['success']:
                        trade = result['trade']
                        print(f"✅ Trade executed at REAL market price:")
                        print(f"   {trade['side'].upper()} {trade['quantity']:.6f} BTC @ ${trade['price']:,.2f}")
                        print(f"   Commission: ${trade['commission']:.2f}")
                        print(f"   Price Source: {result['price_source']}")
                        print(f"   New Portfolio Value: ${result['portfolio']['total_equity']:,.2f}")
                    else:
                        print(f"❌ Trade failed: {result['error']}")
                        
                except ValueError:
                    print("❌ Invalid quantity")
            else:
                print("❌ Invalid side (use 'buy' or 'sell')")
                
        elif choice == '5':
            if bot.trading_enabled:
                bot.disable_trading()
            else:
                bot.enable_trading()
                
        elif choice == '6':
            confirm = input("Reset portfolio? This will delete all trades and positions (y/N): ").strip().lower()
            if confirm == 'y':
                balance = input(f"New balance (default ${INITIAL_BALANCE:,.0f}): ").strip()
                new_balance = float(balance) if balance.replace('.','').isdigit() else INITIAL_BALANCE
                bot.reset_portfolio(new_balance)
            else:
                print("❌ Reset cancelled")
                
        elif choice == '7':
            summary = bot.portfolio.get_portfolio_summary()
            recent_trades = summary.get('recent_trades', [])
            
            if recent_trades:
                print(f"\n📋 Recent Trades (Last {len(recent_trades)}):")
                for trade in reversed(recent_trades):  # Show newest first
                    timestamp = datetime.fromisoformat(trade['timestamp']).strftime('%m/%d %H:%M')
                    print(f"   {timestamp} | {trade['side'].upper()} {trade['quantity']:.6f} BTC @ ${trade['price']:,.2f} | {trade['strategy']}")
            else:
                print("\n📋 No recent trades")
                
        elif choice == '8':
            print(f"\n📡 Market Data Connection Status:")
            print(f"   Real Data Connected: {'✅ YES' if bot.real_data_connected else '❌ NO'}")
            print(f"   Current Price: ${bot.current_price:,.2f}")
            print(f"   Price Source: {bot.price_source}")
            print(f"   Price Updates: {bot.stats['price_updates']}")
            print(f"   Real Data Usage: {bot.stats['real_data_usage']}/{bot.stats['price_updates']}")
            
            # Test connection
            print(f"\n🧪 Testing connection...")
            test_price = bot.get_current_bitcoin_price()
            print(f"   Test Price: ${test_price:,.2f}")
            print(f"   Test Source: {bot.price_source}")
                
        elif choice == '9':
            if bot.running:
                print("🛑 Stopping trading bot...")
                bot.stop_trading()
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()