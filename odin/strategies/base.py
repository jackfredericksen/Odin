"""Base strategy class for Odin trading bot."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np
import structlog

from odin.config import get_settings
from odin.core.database import get_database
from odin.core.exceptions import InsufficientDataError, StrategyError
from odin.core.models import (
    StrategyAnalysis, BacktestResult, TradingSignal, 
    SignalType, TrendType, StrategyType
)

logger = structlog.get_logger(__name__)


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize strategy."""
        self.settings = get_settings()
        self.db_path = db_path
        self.database: Optional[object] = None
        self.strategy_type: StrategyType = StrategyType.MOVING_AVERAGE  # Override in subclasses
        self.min_data_points: int = 20  # Override in subclasses
        
    async def initialize(self) -> None:
        """Initialize strategy resources."""
        self.database = await get_database()
        logger.info("Strategy initialized", strategy=self.strategy_type)
    
    async def get_historical_data(
        self, 
        hours: int = 48,
        min_points: Optional[int] = None
    ) -> pd.DataFrame:
        """Get historical price data for analysis."""
        if not self.database:
            await self.initialize()
        
        try:
            df = await self.database.get_price_history(hours=hours)
            
            if df.empty:
                raise InsufficientDataError(
                    "No historical data available",
                    required_points=min_points or self.min_data_points,
                    available_points=0
                )
            
            required_points = min_points or self.min_data_points
            if len(df) < required_points:
                raise InsufficientDataError(
                    f"Insufficient data for {self.strategy_type} strategy",
                    required_points=required_points,
                    available_points=len(df)
                )
            
            return df
            
        except Exception as e:
            logger.error("Failed to get historical data", 
                        strategy=self.strategy_type, error=str(e))
            raise StrategyError(f"Data retrieval failed: {e}")
    
    @abstractmethod
    async def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate strategy-specific indicators."""
        pass
    
    @abstractmethod
    async def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on indicators."""
        pass
    
    @abstractmethod
    async def analyze_current_market(self) -> StrategyAnalysis:
        """Analyze current market conditions."""
        pass
    
    async def backtest(
        self, 
        hours: int = 168,  # 1 week default
        initial_balance: float = 10000.0
    ) -> BacktestResult:
        """Run strategy backtest."""
        try:
            # Get historical data
            data = await self.get_historical_data(hours=hours)
            
            # Generate signals
            data_with_signals = await self.generate_signals(data)
            
            # Simulate trading
            return await self._simulate_trades(data_with_signals, initial_balance)
            
        except Exception as e:
            logger.error("Backtest failed", strategy=self.strategy_type, error=str(e))
            raise StrategyError(f"Backtest failed: {e}")
    
    async def _simulate_trades(
        self, 
        data: pd.DataFrame, 
        initial_balance: float
    ) -> BacktestResult:
        """Simulate trading based on signals."""
        balance = initial_balance
        position = 0.0  # Amount of BTC held
        trades = []
        equity_curve = []
        
        for idx, row in data.iterrows():
            current_price = row['price']
            current_equity = balance + (position * current_price)
            equity_curve.append(current_equity)
            
            # Check for trading signals
            if 'signal' in row and row['signal'] != 0:
                if row['signal'] == 1 and position == 0:  # Buy signal
                    # Buy with current balance
                    position = balance / current_price
                    trade_value = balance
                    balance = 0
                    
                    trades.append({
                        'type': 'BUY',
                        'timestamp': idx.strftime('%Y-%m-%d %H:%M:%S'),
                        'price': current_price,
                        'amount': position,
                        'value': trade_value,
                    })
                    
                elif row['signal'] == -1 and position > 0:  # Sell signal
                    # Sell all position
                    balance = position * current_price
                    trade_value = balance
                    
                    trades.append({
                        'type': 'SELL',
                        'timestamp': idx.strftime('%Y-%m-%d %H:%M:%S'),
                        'price': current_price,
                        'amount': position,
                        'value': trade_value,
                    })
                    
                    position = 0
        
        # Calculate final value
        final_price = data.iloc[-1]['price']
        final_value = balance + (position * final_price)
        
        # Calculate metrics
        total_return = ((final_value - initial_balance) / initial_balance) * 100
        
        # Calculate trade statistics
        winning_trades = 0
        losing_trades = 0
        
        for i in range(1, len(trades), 2):
            if i < len(trades) and trades[i-1]['type'] == 'BUY':
                buy_price = trades[i-1]['price']
                sell_price = trades[i]['price']
                
                if sell_price > buy_price:
                    winning_trades += 1
                else:
                    losing_trades += 1
        
        win_rate = (winning_trades / max(winning_trades + losing_trades, 1)) * 100
        
        # Calculate max drawdown
        max_drawdown = 0
        peak = initial_balance
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = ((peak - equity) / peak) * 100
            max_drawdown = min(max_drawdown, -drawdown)
        
        # Calculate Sharpe ratio (simplified)
        if len(equity_curve) > 1:
            returns = pd.Series(equity_curve).pct_change().dropna()
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(365 * 24) if returns.std() > 0 else None
        else:
            sharpe_ratio = None
        
        return BacktestResult(
            strategy=self.strategy_type,
            period_hours=hours,
            initial_balance=initial_balance,
            final_value=final_value,
            total_return_percent=total_return,
            total_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_percent=win_rate,
            max_drawdown_percent=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades=trades[-10:],  # Last 10 trades
        )
    
    def _determine_trend(self, data: pd.DataFrame) -> TrendType:
        """Determine market trend based on recent price action."""
        if len(data) < 10:
            return TrendType.SIDEWAYS
        
        recent_prices = data['price'].tail(10)
        first_half = recent_prices.iloc[:5].mean()
        second_half = recent_prices.iloc[5:].mean()
        
        change_percent = ((second_half - first_half) / first_half) * 100
        
        if change_percent > 1.0:
            return TrendType.BULLISH
        elif change_percent < -1.0:
            return TrendType.BEARISH
        else:
            return TrendType.SIDEWAYS
    
    def _get_latest_signal(self, data: pd.DataFrame) -> Optional[TradingSignal]:
        """Get the most recent trading signal."""
        if 'signal' not in data.columns:
            return None
        
        # Find most recent non-zero signal
        signals = data[data['signal'] != 0]
        if signals.empty:
            return None
        
        latest_signal = signals.iloc[-1]
        
        signal_type = SignalType.BUY if latest_signal['signal'] > 0 else SignalType.SELL
        
        # Calculate confidence based on signal strength
        confidence = min(abs(latest_signal['signal']), 1.0)
        
        return TradingSignal(
            timestamp=latest_signal.name,
            signal_type=signal_type,
            price=latest_signal['price'],
            confidence=confidence,
            strategy=self.strategy_type,
            metadata={}
        )
    
    async def get_strategy_data_for_chart(self, hours: int = 24) -> Optional[List[Dict[str, Any]]]:
        """Get strategy data formatted for charting."""
        try:
            data = await self.get_historical_data(hours=hours)
            data_with_indicators = await self.calculate_indicators(data)
            data_with_signals = await self.generate_signals(data_with_indicators)
            
            chart_data = []
            for timestamp, row in data_with_signals.iterrows():
                point = {
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'price': row['price'],
                    'signal': row.get('signal', 0),
                    'signal_type': row.get('signal_type', ''),
                }
                
                # Add strategy-specific indicators
                for col in row.index:
                    if col not in ['price', 'signal', 'signal_type', 'volume', 'high', 'low', 'change_24h', 'source']:
                        point[col] = row[col] if pd.notna(row[col]) else None
                
                chart_data.append(point)
            
            return chart_data
            
        except Exception as e:
            logger.error("Failed to get chart data", strategy=self.strategy_type, error=str(e))
            return None


def validate_data_columns(data: pd.DataFrame, required_columns: List[str]) -> None:
    """Validate that required columns exist in data."""
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise StrategyError(f"Missing required columns: {missing_columns}")


def safe_divide(numerator: pd.Series, denominator: pd.Series, fill_value: float = 0.0) -> pd.Series:
    """Safely divide two series, handling division by zero."""
    return numerator.div(denominator).fillna(fill_value).replace([np.inf, -np.inf], fill_value)