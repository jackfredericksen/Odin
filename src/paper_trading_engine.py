# src/paper_trading_engine.py

import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import uuid
import os

@dataclass
class Trade:
    id: str
    strategy: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    timestamp: datetime
    signal_strength: float = 0.0
    
@dataclass 
class Position:
    id: str
    strategy: str
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    quantity: float
    entry_time: datetime
    current_value: float = 0.0
    unrealized_pnl: float = 0.0
    status: str = 'open'

@dataclass
class Portfolio:
    strategy: str
    cash_balance: float
    btc_holdings: float
    total_value: float
    total_pnl: float
    total_trades: int
    winning_trades: int
    win_rate: float
    last_updated: datetime

class PaperTradingEngine:
    def __init__(self, initial_balance=10000.0, db_path='data/paper_trading.db'):
        """
        Paper Trading Engine for Odin Bot
        
        Args:
            initial_balance (float): Starting cash balance per strategy
            db_path (str): Database path for paper trading data
        """
        self.initial_balance = initial_balance
        self.db_path = db_path
        
        # Initialize portfolios for each strategy
        self.portfolios = {
            'ma_crossover': Portfolio('ma_crossover', initial_balance, 0.0, initial_balance, 0.0, 0, 0, 0.0, datetime.now()),
            'rsi_strategy': Portfolio('rsi_strategy', initial_balance, 0.0, initial_balance, 0.0, 0, 0, 0.0, datetime.now()),
            'bollinger_bands': Portfolio('bollinger_bands', initial_balance, 0.0, initial_balance, 0.0, 0, 0, 0.0, datetime.now()),
            'macd_strategy': Portfolio('macd_strategy', initial_balance, 0.0, initial_balance, 0.0, 0, 0, 0.0, datetime.now())
        }
        
        self.positions = {}  # strategy -> list of positions
        self.trade_history = {}  # strategy -> list of trades
        
        self.setup_database()
        self.load_state()
        
    def setup_database(self):
        """Initialize paper trading database tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Portfolios table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                strategy TEXT PRIMARY KEY,
                cash_balance REAL,
                btc_holdings REAL,
                total_value REAL,
                total_pnl REAL,
                total_trades INTEGER,
                winning_trades INTEGER,
                win_rate REAL,
                last_updated TEXT
            )
        ''')
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                strategy TEXT,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                price REAL,
                timestamp TEXT,
                signal_strength REAL
            )
        ''')
        
        # Positions table  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id TEXT PRIMARY KEY,
                strategy TEXT,
                symbol TEXT,
                side TEXT,
                entry_price REAL,
                quantity REAL,
                entry_time TEXT,
                current_value REAL,
                unrealized_pnl REAL,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"📊 Paper trading database initialized: {self.db_path}")
    
    def execute_trade(self, strategy: str, signal: Dict, current_price: float) -> Dict:
        """
        Execute a paper trade based on strategy signal
        
        Args:
            strategy (str): Strategy name ('ma_crossover', 'rsi_strategy', etc.)
            signal (Dict): Strategy signal with type and strength
            current_price (float): Current Bitcoin price
            
        Returns:
            Dict with trade execution results
        """
        if strategy not in self.portfolios:
            return {'error': f'Unknown strategy: {strategy}'}
        
        portfolio = self.portfolios[strategy]
        signal_type = signal.get('signal_type', '').upper()
        signal_strength = signal.get('strength', 0.0)
        
        # Default trade size: 10% of portfolio value
        trade_size_pct = 0.10
        
        # Adjust trade size based on signal strength
        if signal_strength > 0.8:
            trade_size_pct = 0.15  # Strong signal = larger trade
        elif signal_strength < 0.5:
            trade_size_pct = 0.05  # Weak signal = smaller trade
        
        trade_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        if signal_type == 'BUY':
            return self._execute_buy(strategy, trade_id, current_price, trade_size_pct, signal_strength, timestamp)
        elif signal_type == 'SELL':
            return self._execute_sell(strategy, trade_id, current_price, signal_strength, timestamp)
        else:
            return {'error': f'Invalid signal type: {signal_type}'}
    
    def _execute_buy(self, strategy: str, trade_id: str, price: float, 
                    size_pct: float, signal_strength: float, timestamp: datetime) -> Dict:
        """Execute a buy order"""
        portfolio = self.portfolios[strategy]
        
        # Calculate trade amount
        trade_value = portfolio.total_value * size_pct
        
        # Check if enough cash
        if trade_value > portfolio.cash_balance:
            trade_value = portfolio.cash_balance * 0.95  # Use 95% of available cash
        
        if trade_value < 10:  # Minimum $10 trade
            return {'error': 'Insufficient funds for minimum trade'}
        
        quantity = trade_value / price
        
        # Create trade record
        trade = Trade(
            id=trade_id,
            strategy=strategy,
            symbol='BTC',
            side='buy',
            quantity=quantity,
            price=price,
            timestamp=timestamp,
            signal_strength=signal_strength
        )
        
        # Create position
        position = Position(
            id=str(uuid.uuid4()),
            strategy=strategy,
            symbol='BTC',
            side='long',
            entry_price=price,
            quantity=quantity,
            entry_time=timestamp,
            current_value=trade_value,
            unrealized_pnl=0.0,
            status='open'
        )
        
        # Update portfolio
        portfolio.cash_balance -= trade_value
        portfolio.btc_holdings += quantity
        portfolio.total_trades += 1
        portfolio.last_updated = timestamp
        
        # Store trade and position
        if strategy not in self.trade_history:
            self.trade_history[strategy] = []
        if strategy not in self.positions:
            self.positions[strategy] = []
            
        self.trade_history[strategy].append(trade)
        self.positions[strategy].append(position)
        
        # Save to database
        self._save_trade(trade)
        self._save_position(position)
        self._save_portfolio(portfolio)
        
        return {
            'success': True,
            'trade_id': trade_id,
            'action': 'BUY',
            'quantity': quantity,
            'price': price,
            'value': trade_value,
            'signal_strength': signal_strength,
            'portfolio_cash': portfolio.cash_balance,
            'portfolio_btc': portfolio.btc_holdings
        }
    
    def _execute_sell(self, strategy: str, trade_id: str, price: float, 
                     signal_strength: float, timestamp: datetime) -> Dict:
        """Execute a sell order"""
        portfolio = self.portfolios[strategy]
        
        if portfolio.btc_holdings < 0.0001:  # Minimum BTC to sell
            return {'error': 'No BTC holdings to sell'}
        
        # Sell all BTC holdings
        quantity = portfolio.btc_holdings
        trade_value = quantity * price
        
        # Create trade record
        trade = Trade(
            id=trade_id,
            strategy=strategy,
            symbol='BTC',
            side='sell',
            quantity=quantity,
            price=price,
            timestamp=timestamp,
            signal_strength=signal_strength
        )
        
        # Close positions and calculate P&L
        positions_to_close = [p for p in self.positions.get(strategy, []) if p.status == 'open']
        total_pnl = 0.0
        
        for position in positions_to_close:
            pnl = (price - position.entry_price) * position.quantity
            total_pnl += pnl
            position.status = 'closed'
            position.unrealized_pnl = pnl
        
        # Update portfolio
        portfolio.cash_balance += trade_value
        portfolio.btc_holdings = 0.0
        portfolio.total_trades += 1
        portfolio.total_pnl += total_pnl
        
        # Update win count
        if total_pnl > 0:
            portfolio.winning_trades += 1
        portfolio.win_rate = (portfolio.winning_trades / portfolio.total_trades) * 100 if portfolio.total_trades > 0 else 0
        portfolio.last_updated = timestamp
        
        # Store trade
        if strategy not in self.trade_history:
            self.trade_history[strategy] = []
        self.trade_history[strategy].append(trade)
        
        # Save to database
        self._save_trade(trade)
        for position in positions_to_close:
            self._save_position(position)
        self._save_portfolio(portfolio)
        
        return {
            'success': True,
            'trade_id': trade_id,
            'action': 'SELL',
            'quantity': quantity,
            'price': price,
            'value': trade_value,
            'pnl': total_pnl,
            'signal_strength': signal_strength,
            'portfolio_cash': portfolio.cash_balance,
            'portfolio_btc': portfolio.btc_holdings
        }
    
    def update_portfolios(self, current_price: float):
        """Update all portfolio values with current BTC price"""
        for strategy, portfolio in self.portfolios.items():
            portfolio.total_value = portfolio.cash_balance + (portfolio.btc_holdings * current_price)
            
            # Update unrealized P&L for open positions
            for position in self.positions.get(strategy, []):
                if position.status == 'open':
                    position.current_value = position.quantity * current_price
                    position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
    
    def get_portfolio_summary(self) -> Dict:
        """Get summary of all strategy portfolios"""
        summary = {}
        
        for strategy, portfolio in self.portfolios.items():
            open_positions = len([p for p in self.positions.get(strategy, []) if p.status == 'open'])
            recent_trades = len([t for t in self.trade_history.get(strategy, []) 
                               if t.timestamp > datetime.now() - timedelta(days=1)])
            
            summary[strategy] = {
                'cash_balance': portfolio.cash_balance,
                'btc_holdings': portfolio.btc_holdings,
                'total_value': portfolio.total_value,
                'total_pnl': portfolio.total_pnl,
                'total_pnl_pct': ((portfolio.total_value - self.initial_balance) / self.initial_balance) * 100,
                'total_trades': portfolio.total_trades,
                'winning_trades': portfolio.winning_trades,
                'win_rate': portfolio.win_rate,
                'open_positions': open_positions,
                'recent_trades_24h': recent_trades,
                'last_updated': portfolio.last_updated.isoformat()
            }
        
        return summary
    
    def get_strategy_leaderboard(self) -> List[Dict]:
        """Get strategy performance ranking"""
        leaderboard = []
        
        for strategy, portfolio in self.portfolios.items():
            pnl_pct = ((portfolio.total_value - self.initial_balance) / self.initial_balance) * 100
            
            leaderboard.append({
                'strategy': strategy,
                'total_return_pct': pnl_pct,
                'total_value': portfolio.total_value,
                'win_rate': portfolio.win_rate,
                'total_trades': portfolio.total_trades,
                'sharpe_ratio': self._calculate_sharpe_ratio(strategy)
            })
        
        # Sort by total return percentage
        leaderboard.sort(key=lambda x: x['total_return_pct'], reverse=True)
        
        return leaderboard
    
    def _calculate_sharpe_ratio(self, strategy: str) -> float:
        """Calculate Sharpe ratio for strategy (simplified)"""
        trades = self.trade_history.get(strategy, [])
        if len(trades) < 2:
            return 0.0
        
        # Get daily returns (simplified calculation)
        returns = []
        for i in range(1, len(trades)):
            if trades[i].side == 'sell' and trades[i-1].side == 'buy':
                daily_return = (trades[i].price - trades[i-1].price) / trades[i-1].price
                returns.append(daily_return)
        
        if not returns:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        std_return = (sum([(r - mean_return) ** 2 for r in returns]) / len(returns)) ** 0.5
        
        return (mean_return / std_return) if std_return > 0 else 0.0
    
    def _save_trade(self, trade: Trade):
        """Save trade to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO trades 
            (id, strategy, symbol, side, quantity, price, timestamp, signal_strength)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.id, trade.strategy, trade.symbol, trade.side,
            trade.quantity, trade.price, trade.timestamp.isoformat(),
            trade.signal_strength
        ))
        
        conn.commit()
        conn.close()
    
    def _save_position(self, position: Position):
        """Save position to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO positions 
            (id, strategy, symbol, side, entry_price, quantity, entry_time, 
             current_value, unrealized_pnl, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            position.id, position.strategy, position.symbol, position.side,
            position.entry_price, position.quantity, position.entry_time.isoformat(),
            position.current_value, position.unrealized_pnl, position.status
        ))
        
        conn.commit()
        conn.close()
    
    def _save_portfolio(self, portfolio: Portfolio):
        """Save portfolio to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO portfolios 
            (strategy, cash_balance, btc_holdings, total_value, total_pnl,
             total_trades, winning_trades, win_rate, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            portfolio.strategy, portfolio.cash_balance, portfolio.btc_holdings,
            portfolio.total_value, portfolio.total_pnl, portfolio.total_trades,
            portfolio.winning_trades, portfolio.win_rate, portfolio.last_updated.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def load_state(self):
        """Load portfolio state from database"""
        if not os.path.exists(self.db_path):
            return
        
        conn = sqlite3.connect(self.db_path)
        
        # Load portfolios
        portfolios_df = pd.read_sql_query('SELECT * FROM portfolios', conn)
        for _, row in portfolios_df.iterrows():
            strategy = row['strategy']
            if strategy in self.portfolios:
                self.portfolios[strategy] = Portfolio(
                    strategy=strategy,
                    cash_balance=row['cash_balance'],
                    btc_holdings=row['btc_holdings'],
                    total_value=row['total_value'],
                    total_pnl=row['total_pnl'],
                    total_trades=row['total_trades'],
                    winning_trades=row['winning_trades'],
                    win_rate=row['win_rate'],
                    last_updated=datetime.fromisoformat(row['last_updated'])
                )
        
        conn.close()


# Test the paper trading engine
if __name__ == "__main__":
    print("🎯 Testing Paper Trading Engine")
    print("=" * 50)
    
    # Initialize engine
    engine = PaperTradingEngine(initial_balance=10000)
    
    # Simulate some trades
    current_price = 108000
    
    # Test MA crossover buy signal
    ma_signal = {
        'signal_type': 'BUY',
        'strength': 0.85,
        'strategy': 'ma_crossover'
    }
    
    result = engine.execute_trade('ma_crossover', ma_signal, current_price)
    print(f"📈 MA Buy Trade: {result}")
    
    # Update portfolios with new price
    new_price = 109500
    engine.update_portfolios(new_price)
    
    # Test sell signal
    sell_signal = {
        'signal_type': 'SELL',
        'strength': 0.75,
        'strategy': 'ma_crossover'
    }
    
    result = engine.execute_trade('ma_crossover', sell_signal, new_price)
    print(f"📉 MA Sell Trade: {result}")
    
    # Get portfolio summary
    summary = engine.get_portfolio_summary()
    print(f"\n💼 Portfolio Summary:")
    for strategy, data in summary.items():
        print(f"   {strategy}: ${data['total_value']:,.2f} ({data['total_pnl_pct']:+.2f}%)")
    
    # Get leaderboard
    leaderboard = engine.get_strategy_leaderboard()
    print(f"\n🏆 Strategy Leaderboard:")
    for i, strategy in enumerate(leaderboard):
        print(f"   {i+1}. {strategy['strategy']}: {strategy['total_return_pct']:+.2f}% return")