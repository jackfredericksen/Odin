import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Tuple
import uuid

class Position:
    def __init__(self, symbol: str, side: str, quantity: float, entry_price: float, 
                 strategy: str, timestamp: datetime = None):
        self.id = str(uuid.uuid4())
        self.symbol = symbol
        self.side = side  # 'long' or 'short'
        self.quantity = quantity
        self.entry_price = entry_price
        self.current_price = entry_price
        self.strategy = strategy
        self.timestamp = timestamp or datetime.now()
        self.unrealized_pnl = 0.0
        self.stop_loss = None
        self.take_profit = None
        
    def update_price(self, current_price: float):
        """Update current price and calculate unrealized PnL"""
        self.current_price = current_price
        
        if self.side == 'long':
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:  # short
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity
            
    def get_market_value(self) -> float:
        """Get current market value of the position"""
        return self.quantity * self.current_price
        
    def to_dict(self) -> dict:
        """Convert position to dictionary for storage"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'strategy': self.strategy,
            'timestamp': self.timestamp.isoformat(),
            'unrealized_pnl': self.unrealized_pnl,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit
        }

class Trade:
    def __init__(self, symbol: str, side: str, quantity: float, price: float, 
                 strategy: str, trade_type: str = 'market', timestamp: datetime = None):
        self.id = str(uuid.uuid4())
        self.symbol = symbol
        self.side = side  # 'buy' or 'sell'
        self.quantity = quantity
        self.price = price
        self.strategy = strategy
        self.trade_type = trade_type
        self.timestamp = timestamp or datetime.now()
        self.commission = self.calculate_commission()
        self.total_value = (quantity * price) + self.commission
        
    def calculate_commission(self) -> float:
        """Calculate trading commission (0.1% for paper trading)"""
        return (self.quantity * self.price) * 0.001
        
    def to_dict(self) -> dict:
        """Convert trade to dictionary for storage"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'strategy': self.strategy,
            'trade_type': self.trade_type,
            'timestamp': self.timestamp.isoformat(),
            'commission': self.commission,
            'total_value': self.total_value
        }

class PaperTradingPortfolio:
    def __init__(self, initial_balance: float = 10000.0, db_path: str = None):
        self.initial_balance = initial_balance
        self.cash_balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.equity_history: List[dict] = []
        
        # Database setup
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'paper_trading.db')
        
        self.db_path = db_path
        self.setup_database()
        self.load_portfolio_state()
        
    def setup_database(self):
        """Create database tables for paper trading"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Portfolio state table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_state (
                id INTEGER PRIMARY KEY,
                cash_balance REAL,
                total_equity REAL,
                timestamp TEXT,
                daily_pnl REAL,
                total_pnl REAL
            )
        ''')
        
        # Positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id TEXT PRIMARY KEY,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                entry_price REAL,
                current_price REAL,
                strategy TEXT,
                timestamp TEXT,
                unrealized_pnl REAL,
                stop_loss REAL,
                take_profit REAL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                price REAL,
                strategy TEXT,
                trade_type TEXT,
                timestamp TEXT,
                commission REAL,
                total_value REAL
            )
        ''')
        
        # Strategy performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_performance (
                strategy TEXT,
                total_trades INTEGER,
                winning_trades INTEGER,
                total_pnl REAL,
                win_rate REAL,
                avg_trade_pnl REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                last_updated TEXT,
                PRIMARY KEY (strategy)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def load_portfolio_state(self):
        """Load portfolio state from database"""
        conn = sqlite3.connect(self.db_path)
        
        # Load cash balance
        cursor = conn.cursor()
        cursor.execute('SELECT cash_balance FROM portfolio_state ORDER BY timestamp DESC LIMIT 1')
        result = cursor.fetchone()
        if result:
            self.cash_balance = result[0]
            
        # Load active positions
        cursor.execute('SELECT * FROM positions WHERE is_active = 1')
        for row in cursor.fetchall():
            position = Position(
                symbol=row[1], side=row[2], quantity=row[3],
                entry_price=row[4], strategy=row[6],
                timestamp=datetime.fromisoformat(row[7])
            )
            position.id = row[0]
            position.current_price = row[5]
            position.unrealized_pnl = row[8]
            position.stop_loss = row[9]
            position.take_profit = row[10]
            self.positions[position.id] = position
            
        # Load recent trades
        cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC LIMIT 100')
        for row in cursor.fetchall():
            trade = Trade(
                symbol=row[1], side=row[2], quantity=row[3],
                price=row[4], strategy=row[5], trade_type=row[6],
                timestamp=datetime.fromisoformat(row[7])
            )
            trade.id = row[0]
            trade.commission = row[8]
            trade.total_value = row[9]
            self.trade_history.append(trade)
            
        conn.close()
        
    def save_portfolio_state(self):
        """Save current portfolio state to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Save portfolio state
        total_equity = self.get_total_equity()
        total_pnl = total_equity - self.initial_balance
        
        cursor.execute('''
            INSERT INTO portfolio_state (cash_balance, total_equity, timestamp, total_pnl)
            VALUES (?, ?, ?, ?)
        ''', (self.cash_balance, total_equity, datetime.now().isoformat(), total_pnl))
        
        # Save positions
        for position in self.positions.values():
            cursor.execute('''
                INSERT OR REPLACE INTO positions 
                (id, symbol, side, quantity, entry_price, current_price, strategy, 
                 timestamp, unrealized_pnl, stop_loss, take_profit, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                position.id, position.symbol, position.side, position.quantity,
                position.entry_price, position.current_price, position.strategy,
                position.timestamp.isoformat(), position.unrealized_pnl,
                position.stop_loss, position.take_profit
            ))
            
        conn.commit()
        conn.close()
        
    def execute_trade(self, symbol: str, side: str, quantity: float, price: float, 
                     strategy: str, signal_strength: float = 1.0) -> Optional[Trade]:
        """Execute a paper trade"""
        
        # Calculate position size based on signal strength
        max_position_size = self.cash_balance * 0.1  # Max 10% per trade
        position_value = max_position_size * signal_strength
        actual_quantity = min(quantity, position_value / price)
        
        # Check if we have enough cash for buy orders
        if side == 'buy':
            cost = actual_quantity * price
            commission = cost * 0.001
            total_cost = cost + commission
            
            if total_cost > self.cash_balance:
                print(f"Insufficient funds for {symbol} buy order: ${total_cost:.2f} > ${self.cash_balance:.2f}")
                return None
                
            # Deduct from cash balance
            self.cash_balance -= total_cost
            
            # Create long position
            position = Position(symbol, 'long', actual_quantity, price, strategy)
            self.positions[position.id] = position
            
        elif side == 'sell':
            # Find and close long positions or create short position
            long_positions = [p for p in self.positions.values() 
                            if p.symbol == symbol and p.side == 'long']
            
            if long_positions:
                # Close existing long position
                position = long_positions[0]
                sell_value = min(actual_quantity, position.quantity) * price
                commission = sell_value * 0.001
                net_proceeds = sell_value - commission
                
                # Add to cash balance
                self.cash_balance += net_proceeds
                
                # Update or remove position
                if actual_quantity >= position.quantity:
                    # Close entire position
                    self._close_position(position.id, price)
                else:
                    # Partial close
                    position.quantity -= actual_quantity
                    
            else:
                # Create short position (for advanced strategies)
                position = Position(symbol, 'short', actual_quantity, price, strategy)
                self.positions[position.id] = position
        
        # Create trade record
        trade = Trade(symbol, side, actual_quantity, price, strategy)
        self.trade_history.append(trade)
        
        # Save to database
        self._save_trade(trade)
        self.save_portfolio_state()
        
        print(f"✅ Executed {side} {actual_quantity:.6f} {symbol} @ ${price:.2f} ({strategy})")
        return trade
        
    def _close_position(self, position_id: str, exit_price: float):
        """Close a position and calculate realized PnL"""
        if position_id not in self.positions:
            return
            
        position = self.positions[position_id]
        
        # Calculate realized PnL
        if position.side == 'long':
            realized_pnl = (exit_price - position.entry_price) * position.quantity
        else:
            realized_pnl = (position.entry_price - exit_price) * position.quantity
            
        # Remove position
        del self.positions[position_id]
        
        # Mark position as closed in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE positions SET is_active = 0 WHERE id = ?', (position_id,))
        conn.commit()
        conn.close()
        
        print(f"🔒 Closed {position.side} position: {realized_pnl:+.2f} PnL")
        return realized_pnl
        
    def _save_trade(self, trade: Trade):
        """Save trade to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades 
            (id, symbol, side, quantity, price, strategy, trade_type, timestamp, commission, total_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.id, trade.symbol, trade.side, trade.quantity, trade.price,
            trade.strategy, trade.trade_type, trade.timestamp.isoformat(),
            trade.commission, trade.total_value
        ))
        
        conn.commit()
        conn.close()
        
    def update_positions(self, current_price: float, symbol: str = 'BTC'):
        """Update all positions with current market price"""
        for position in self.positions.values():
            if position.symbol == symbol:
                position.update_price(current_price)
                
    def get_total_equity(self) -> float:
        """Calculate total portfolio equity"""
        position_value = sum(pos.get_market_value() for pos in self.positions.values())
        return self.cash_balance + position_value
        
    def get_total_pnl(self) -> float:
        """Calculate total profit/loss"""
        return self.get_total_equity() - self.initial_balance
        
    def get_portfolio_summary(self) -> dict:
        """Get comprehensive portfolio summary"""
        total_equity = self.get_total_equity()
        total_pnl = self.get_total_pnl()
        total_return_pct = (total_pnl / self.initial_balance) * 100
        
        # Position summary
        position_count = len(self.positions)
        position_value = sum(pos.get_market_value() for pos in self.positions.values())
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        # Recent trades summary
        recent_trades = self.trade_history[-10:] if self.trade_history else []
        
        return {
            'cash_balance': self.cash_balance,
            'position_value': position_value,
            'total_equity': total_equity,
            'total_pnl': total_pnl,
            'total_return_percent': total_return_pct,
            'unrealized_pnl': unrealized_pnl,
            'position_count': position_count,
            'total_trades': len(self.trade_history),
            'recent_trades': [trade.to_dict() for trade in recent_trades],
            'active_positions': [pos.to_dict() for pos in self.positions.values()],
            'initial_balance': self.initial_balance
        }
        
    def get_strategy_performance(self, strategy: str = None) -> dict:
        """Get performance metrics for a specific strategy or all strategies"""
        if strategy:
            strategy_trades = [t for t in self.trade_history if t.strategy == strategy]
        else:
            strategy_trades = self.trade_history
            
        if not strategy_trades:
            return {'error': 'No trades found for strategy'}
            
        # Calculate metrics
        total_trades = len(strategy_trades)
        total_commission = sum(t.commission for t in strategy_trades)
        
        # Group buy/sell pairs to calculate PnL
        buy_trades = [t for t in strategy_trades if t.side == 'buy']
        sell_trades = [t for t in strategy_trades if t.side == 'sell']
        
        trade_pnls = []
        for i, buy_trade in enumerate(buy_trades):
            if i < len(sell_trades):
                sell_trade = sell_trades[i]
                pnl = (sell_trade.price - buy_trade.price) * min(buy_trade.quantity, sell_trade.quantity)
                trade_pnls.append(pnl)
                
        winning_trades = len([pnl for pnl in trade_pnls if pnl > 0])
        win_rate = (winning_trades / len(trade_pnls) * 100) if trade_pnls else 0
        total_realized_pnl = sum(trade_pnls)
        avg_trade_pnl = total_realized_pnl / len(trade_pnls) if trade_pnls else 0
        
        return {
            'strategy': strategy or 'All Strategies',
            'total_trades': total_trades,
            'completed_trades': len(trade_pnls),
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'total_realized_pnl': total_realized_pnl,
            'avg_trade_pnl': avg_trade_pnl,
            'total_commission': total_commission,
            'net_pnl': total_realized_pnl - total_commission
        }

# Automated Trading Engine
class AutomatedTrader:
    def __init__(self, portfolio: PaperTradingPortfolio):
        self.portfolio = portfolio
        self.active_strategies = {}
        self.last_signals = {}
        
    def register_strategy(self, strategy_name: str, strategy_instance):
        """Register a strategy for automated trading"""
        self.active_strategies[strategy_name] = strategy_instance
        self.last_signals[strategy_name] = None
        print(f"📝 Registered strategy: {strategy_name}")
        
    def process_signals(self, current_price: float, symbol: str = 'BTC'):
        """Process signals from all registered strategies"""
        executed_trades = []
        
        for strategy_name, strategy in self.active_strategies.items():
            try:
                # Get current market analysis
                analysis = strategy.analyze_current_market()
                
                if 'error' not in analysis and analysis.get('current_signal'):
                    signal = analysis['current_signal']
                    signal_type = signal['type']
                    signal_strength = signal.get('strength', 1.0)
                    
                    # Check if this is a new signal (avoid duplicate trades)
                    last_signal = self.last_signals.get(strategy_name)
                    if last_signal != signal['timestamp']:
                        
                        # Execute trade based on signal
                        if signal_type == 'BUY':
                            trade = self.portfolio.execute_trade(
                                symbol=symbol,
                                side='buy',
                                quantity=current_price / 100,  # Calculate appropriate quantity
                                price=current_price,
                                strategy=strategy_name,
                                signal_strength=signal_strength
                            )
                            if trade:
                                executed_trades.append(trade)
                                
                        elif signal_type == 'SELL':
                            trade = self.portfolio.execute_trade(
                                symbol=symbol,
                                side='sell',
                                quantity=current_price / 100,  # Calculate appropriate quantity
                                price=current_price,
                                strategy=strategy_name,
                                signal_strength=signal_strength
                            )
                            if trade:
                                executed_trades.append(trade)
                                
                        # Update last signal
                        self.last_signals[strategy_name] = signal['timestamp']
                        
            except Exception as e:
                print(f"❌ Error processing {strategy_name} strategy: {e}")
                
        # Update all positions with current price
        self.portfolio.update_positions(current_price, symbol)
        
        return executed_trades

def test_paper_trading():
    """Test the paper trading system"""
    print("🚀 Testing Odin Paper Trading System")
    print("=" * 50)
    
    # Create portfolio
    portfolio = PaperTradingPortfolio(initial_balance=10000)
    
    # Simulate some trades
    current_price = 45000
    
    # Buy signal
    trade1 = portfolio.execute_trade('BTC', 'buy', 0.1, current_price, 'MA_Strategy', 0.8)
    
    # Update price and show portfolio
    new_price = 46000
    portfolio.update_positions(new_price)
    
    summary = portfolio.get_portfolio_summary()
    print(f"\n📊 Portfolio Summary:")
    print(f"   Cash: ${summary['cash_balance']:,.2f}")
    print(f"   Positions: ${summary['position_value']:,.2f}")
    print(f"   Total Equity: ${summary['total_equity']:,.2f}")
    print(f"   Total P&L: ${summary['total_pnl']:+,.2f} ({summary['total_return_percent']:+.2f}%)")
    print(f"   Active Positions: {summary['position_count']}")
    
    # Sell signal
    trade2 = portfolio.execute_trade('BTC', 'sell', 0.1, new_price, 'MA_Strategy', 0.9)
    
    # Final summary
    final_summary = portfolio.get_portfolio_summary()
    print(f"\n📈 Final Portfolio:")
    print(f"   Total Equity: ${final_summary['total_equity']:,.2f}")
    print(f"   Total P&L: ${final_summary['total_pnl']:+,.2f}")
    print(f"   Total Trades: {final_summary['total_trades']}")
    
    return portfolio

if __name__ == "__main__":
    test_paper_trading()