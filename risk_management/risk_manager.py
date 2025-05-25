# risk_management/risk_manager.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
import os

class RiskManager:
    def __init__(self, db_path=None, initial_balance=10000):
        """
        Advanced Risk Management System
        
        Args:
            db_path (str): Database path
            initial_balance (float): Starting portfolio balance
        """
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions = {}  # Current positions
        self.trade_history = []  # All completed trades
        
        # Risk parameters
        self.max_position_size_pct = 0.10  # 10% max per position
        self.stop_loss_pct = 0.05  # 5% stop loss
        self.take_profit_pct = 0.10  # 10% take profit
        self.max_drawdown_limit = 0.20  # 20% max drawdown
        self.volatility_lookback = 20  # Days for volatility calc
        self.correlation_threshold = 0.7  # Max correlation between strategies
        
        # Performance tracking
        self.daily_returns = []
        self.peak_balance = initial_balance
        self.current_drawdown = 0.0
        self.consecutive_losses = 0
        self.max_consecutive_losses = 5
        
        self.setup_risk_database()
    
    def setup_risk_database(self):
        """Initialize risk management tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT,
                symbol TEXT,
                entry_price REAL,
                current_price REAL,
                quantity REAL,
                stop_loss REAL,
                take_profit REAL,
                entry_time TEXT,
                status TEXT,
                unrealized_pnl REAL
            )
        ''')
        
        # Trade history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT,
                symbol TEXT,
                side TEXT,
                entry_price REAL,
                exit_price REAL,
                quantity REAL,
                entry_time TEXT,
                exit_time TEXT,
                pnl REAL,
                pnl_percent REAL,
                exit_reason TEXT
            )
        ''')
        
        # Risk metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                total_balance REAL,
                unrealized_pnl REAL,
                realized_pnl REAL,
                drawdown_pct REAL,
                var_95 REAL,
                sharpe_ratio REAL,
                volatility REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_position_size(self, price: float, volatility: float = None) -> float:
        """
        Calculate optimal position size based on risk parameters
        
        Args:
            price (float): Current asset price
            volatility (float): Asset volatility (optional)
        
        Returns:
            float: Position size in USD
        """
        # Base position size (percentage of portfolio)
        base_size = self.current_balance * self.max_position_size_pct
        
        # Adjust for volatility if provided
        if volatility is not None:
            # Reduce position size for high volatility assets
            volatility_adjustment = max(0.5, 1 - (volatility * 2))
            base_size *= volatility_adjustment
        
        # Adjust for current drawdown
        if self.current_drawdown > 0.1:  # 10% drawdown
            drawdown_adjustment = max(0.3, 1 - self.current_drawdown)
            base_size *= drawdown_adjustment
        
        # Adjust for consecutive losses
        if self.consecutive_losses > 3:
            loss_adjustment = max(0.5, 1 - (self.consecutive_losses * 0.1))
            base_size *= loss_adjustment
        
        return min(base_size, self.current_balance * 0.25)  # Never risk more than 25%
    
    def calculate_stop_loss(self, entry_price: float, side: str = 'long') -> float:
        """Calculate stop loss price"""
        if side == 'long':
            return entry_price * (1 - self.stop_loss_pct)
        else:  # short
            return entry_price * (1 + self.stop_loss_pct)
    
    def calculate_take_profit(self, entry_price: float, side: str = 'long') -> float:
        """Calculate take profit price"""
        if side == 'long':
            return entry_price * (1 + self.take_profit_pct)
        else:  # short
            return entry_price * (1 - self.take_profit_pct)
    
    def open_position(self, strategy_name: str, symbol: str, side: str, 
                     entry_price: float, volatility: float = None) -> Dict:
        """
        Open a new position with risk management
        
        Args:
            strategy_name (str): Name of the trading strategy
            symbol (str): Asset symbol (e.g., 'BTC')
            side (str): 'long' or 'short'
            entry_price (float): Entry price
            volatility (float): Asset volatility
        
        Returns:
            Dict: Position details or error
        """
        # Check if we can open position
        if self.current_drawdown > self.max_drawdown_limit:
            return {'error': 'Maximum drawdown limit exceeded'}
        
        if self.consecutive_losses >= self.max_consecutive_losses:
            return {'error': 'Too many consecutive losses'}
        
        # Calculate position size
        position_value = self.calculate_position_size(entry_price, volatility)
        quantity = position_value / entry_price
        
        # Calculate stop loss and take profit
        stop_loss = self.calculate_stop_loss(entry_price, side)
        take_profit = self.calculate_take_profit(entry_price, side)
        
        # Create position
        position = {
            'strategy_name': strategy_name,
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'current_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': datetime.now().isoformat(),
            'status': 'open',
            'unrealized_pnl': 0.0
        }
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO positions (strategy_name, symbol, entry_price, current_price, 
                                 quantity, stop_loss, take_profit, entry_time, status, unrealized_pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            position['strategy_name'], position['symbol'], position['entry_price'],
            position['current_price'], position['quantity'], position['stop_loss'],
            position['take_profit'], position['entry_time'], position['status'],
            position['unrealized_pnl']
        ))
        
        position_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.positions[position_id] = position
        
        return {'success': True, 'position_id': position_id, 'position': position}
    
    def update_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Update all open positions and check for stop loss/take profit
        
        Args:
            current_prices (Dict): Current prices for all symbols
        
        Returns:
            List[Dict]: List of closed positions
        """
        closed_positions = []
        
        for position_id, position in list(self.positions.items()):
            symbol = position['symbol']
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            position['current_price'] = current_price
            
            # Calculate unrealized P&L
            if position['side'] == 'long':
                pnl = (current_price - position['entry_price']) * position['quantity']
            else:  # short
                pnl = (position['entry_price'] - current_price) * position['quantity']
            
            position['unrealized_pnl'] = pnl
            
            # Check for stop loss or take profit
            should_close = False
            exit_reason = None
            
            if position['side'] == 'long':
                if current_price <= position['stop_loss']:
                    should_close = True
                    exit_reason = 'stop_loss'
                elif current_price >= position['take_profit']:
                    should_close = True
                    exit_reason = 'take_profit'
            else:  # short
                if current_price >= position['stop_loss']:
                    should_close = True
                    exit_reason = 'stop_loss'
                elif current_price <= position['take_profit']:
                    should_close = True
                    exit_reason = 'take_profit'
            
            if should_close:
                closed_position = self.close_position(position_id, current_price, exit_reason)
                closed_positions.append(closed_position)
        
        return closed_positions
    
    def close_position(self, position_id: int, exit_price: float, exit_reason: str = 'manual') -> Dict:
        """
        Close a position and record the trade
        
        Args:
            position_id (int): Position ID
            exit_price (float): Exit price
            exit_reason (str): Reason for closing
        
        Returns:
            Dict: Closed position details
        """
        if position_id not in self.positions:
            return {'error': 'Position not found'}
        
        position = self.positions[position_id]
        
        # Calculate P&L
        if position['side'] == 'long':
            pnl = (exit_price - position['entry_price']) * position['quantity']
        else:  # short
            pnl = (position['entry_price'] - exit_price) * position['quantity']
        
        pnl_percent = (pnl / (position['entry_price'] * position['quantity'])) * 100
        
        # Update balance
        self.current_balance += pnl
        
        # Track consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # Update peak balance and drawdown
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
        
        self.current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        
        # Create trade record
        trade = {
            'strategy_name': position['strategy_name'],
            'symbol': position['symbol'],
            'side': position['side'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'quantity': position['quantity'],
            'entry_time': position['entry_time'],
            'exit_time': datetime.now().isoformat(),
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'exit_reason': exit_reason
        }
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update position status
        cursor.execute('''
            UPDATE positions SET status = 'closed' WHERE id = ?
        ''', (position_id,))
        
        # Add to trade history
        cursor.execute('''
            INSERT INTO trade_history (strategy_name, symbol, side, entry_price, exit_price,
                                     quantity, entry_time, exit_time, pnl, pnl_percent, exit_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade['strategy_name'], trade['symbol'], trade['side'], trade['entry_price'],
            trade['exit_price'], trade['quantity'], trade['entry_time'], trade['exit_time'],
            trade['pnl'], trade['pnl_percent'], trade['exit_reason']
        ))
        
        conn.commit()
        conn.close()
        
        # Remove from active positions
        del self.positions[position_id]
        self.trade_history.append(trade)
        
        return {'success': True, 'trade': trade}
    
    def calculate_portfolio_metrics(self) -> Dict:
        """Calculate comprehensive portfolio risk metrics"""
        if len(self.trade_history) < 2:
            return {'error': 'Not enough trade history'}
        
        # Convert trade history to DataFrame
        df = pd.DataFrame(self.trade_history)
        
        # Calculate returns
        returns = df['pnl_percent'].values / 100
        
        # Sharpe Ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02 / 252  # Daily
        excess_returns = returns - risk_free_rate
        sharpe_ratio = np.mean(excess_returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        # Maximum Drawdown
        cumulative_returns = (1 + returns).cumprod()
        peak = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min()
        
        # Win Rate
        win_rate = (returns > 0).mean() * 100
        
        # Average Win/Loss
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        
        # Profit Factor
        total_wins = wins.sum() if len(wins) > 0 else 0
        total_losses = abs(losses.sum()) if len(losses) > 0 else 0.001
        profit_factor = total_wins / total_losses
        
        # Value at Risk (95%)
        var_95 = np.percentile(returns, 5) * self.current_balance
        
        # Current unrealized P&L
        unrealized_pnl = sum(pos['unrealized_pnl'] for pos in self.positions.values())
        
        return {
            'total_balance': self.current_balance,
            'unrealized_pnl': unrealized_pnl,
            'total_value': self.current_balance + unrealized_pnl,
            'total_return_pct': ((self.current_balance - self.initial_balance) / self.initial_balance) * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown * 100,
            'current_drawdown_pct': self.current_drawdown * 100,
            'win_rate_pct': win_rate,
            'avg_win_pct': avg_win * 100,
            'avg_loss_pct': avg_loss * 100,
            'profit_factor': profit_factor,
            'var_95': var_95,
            'total_trades': len(self.trade_history),
            'open_positions': len(self.positions),
            'consecutive_losses': self.consecutive_losses
        }
    
    def get_risk_signals(self) -> List[str]:
        """Get current risk warnings and signals"""
        signals = []
        
        if self.current_drawdown > 0.15:
            signals.append(f"HIGH DRAWDOWN WARNING: {self.current_drawdown*100:.1f}%")
        
        if self.consecutive_losses >= 4:
            signals.append(f"CONSECUTIVE LOSSES: {self.consecutive_losses}")
        
        if len(self.positions) > 5:
            signals.append(f"HIGH POSITION COUNT: {len(self.positions)}")
        
        # Check position concentration
        total_exposure = sum(abs(pos['unrealized_pnl']) for pos in self.positions.values())
        if total_exposure > self.current_balance * 0.5:
            signals.append("HIGH PORTFOLIO CONCENTRATION")
        
        if self.current_balance < self.initial_balance * 0.8:
            signals.append("SIGNIFICANT CAPITAL LOSS")
        
        return signals