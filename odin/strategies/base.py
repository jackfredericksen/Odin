"""
Base Strategy Class - FIXED VERSION

Abstract base class for all trading strategies in the Odin Bitcoin trading bot.
Defines the interface and common functionality that all strategies must implement.

FIXED: Removed duplicate StrategySignal enum, now uses SignalType from models.py
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import SignalType from models instead of defining duplicate
from ..core.models import SignalType

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Strategy classification types."""

    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    MOMENTUM = "momentum"
    ARBITRAGE = "arbitrage"


@dataclass
class Signal:
    """Trading signal with metadata."""

    signal: SignalType  # FIXED: Now uses SignalType from models
    confidence: float  # 0-1 confidence score
    timestamp: datetime
    price: float
    reasoning: str
    indicators: Dict[str, float]  # Technical indicator values
    risk_score: float  # 0-1 risk assessment


@dataclass
class StrategyPerformance:
    """Strategy performance metrics."""

    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    avg_trade_duration: timedelta
    volatility: float
    calmar_ratio: float
    sortino_ratio: float


@dataclass
class BacktestResult:
    """Backtesting results."""

    performance: StrategyPerformance
    signals: List[Signal]
    equity_curve: pd.Series
    trades: List[Dict[str, Any]]
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float


class Strategy(ABC):
    """
    Abstract base class for all trading strategies.

    All concrete strategies must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, name: str, strategy_type: StrategyType, **kwargs):
        """
        Initialize strategy.

        Args:
            name: Strategy name
            strategy_type: Strategy classification
            **kwargs: Strategy-specific parameters
        """
        self.name = name
        self.strategy_type = strategy_type
        self.parameters = kwargs
        self.is_enabled = True
        self.last_signal = None
        self.performance_cache = {}
        self.logger = logging.getLogger(f"{__name__}.{name}")

        # Performance tracking
        self.signals_history: List[Signal] = []
        self.trades_history: List[Dict[str, Any]] = []

        # Risk management
        self.max_position_size = kwargs.get("max_position_size", 0.95)
        self.stop_loss_pct = kwargs.get("stop_loss_pct", 0.05)
        self.take_profit_pct = kwargs.get("take_profit_pct", 0.10)

        self.logger.info(f"Initialized {name} strategy with parameters: {kwargs}")

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on current market data.

        Args:
            data: OHLCV price data with technical indicators

        Returns:
            Trading signal with confidence and metadata
        """
        pass

    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators required for the strategy.

        Args:
            data: Raw OHLCV price data

        Returns:
            Data with additional indicator columns
        """
        pass

    @abstractmethod
    def get_parameter_ranges(self) -> Dict[str, Tuple[float, float]]:
        """
        Get parameter ranges for optimization.

        Returns:
            Dictionary mapping parameter names to (min, max) tuples
        """
        pass

    @abstractmethod
    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Update strategy parameters.

        Args:
            parameters: New parameter values
        """
        pass

    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data format and completeness.

        Args:
            data: Input price data

        Returns:
            True if data is valid

        Raises:
            ValueError: If data is invalid
        """
        required_columns = ["open", "high", "low", "close", "volume"]

        if data.empty:
            raise ValueError("Data cannot be empty")

        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        if data.isnull().any().any():
            self.logger.warning("Data contains null values, forward filling")
            data.fillna(method="ffill", inplace=True)

        return True

    def calculate_position_size(
        self, signal: Signal, available_capital: float
    ) -> float:
        """
        Calculate position size based on signal confidence and risk management.

        Args:
            signal: Trading signal
            available_capital: Available capital for trading

        Returns:
            Position size in dollars
        """
        base_size = available_capital * self.max_position_size
        confidence_adjusted = base_size * signal.confidence
        risk_adjusted = confidence_adjusted * (1 - signal.risk_score)

        return min(risk_adjusted, available_capital)

    def backtest(
        self, data: pd.DataFrame, initial_capital: float = 10000
    ) -> BacktestResult:
        """
        Backtest strategy on historical data.

        Args:
            data: Historical OHLCV data
            initial_capital: Starting capital amount

        Returns:
            Backtesting results with performance metrics
        """
        self.logger.info(f"Starting backtest for {self.name} strategy")

        # Validate and prepare data
        self.validate_data(data)
        data_with_indicators = self.calculate_indicators(data.copy())

        # Initialize tracking variables
        capital = initial_capital
        position = 0.0  # BTC holdings
        cash = capital
        trades = []
        signals = []
        equity_curve = []

        for i in range(len(data_with_indicators)):
            current_data = data_with_indicators.iloc[: i + 1]

            if len(current_data) < 20:  # Need minimum data for indicators
                equity_curve.append(capital)
                continue

            # Generate signal
            signal = self.generate_signal(current_data)
            signals.append(signal)

            current_price = current_data["close"].iloc[-1]

            # Execute trades based on signal (FIXED: Use SignalType)
            if signal.signal == SignalType.BUY and position == 0:
                # Buy signal and no current position
                position_size = self.calculate_position_size(signal, cash)
                btc_bought = position_size / current_price

                position += btc_bought
                cash -= position_size

                trades.append(
                    {
                        "type": "buy",
                        "timestamp": signal.timestamp,
                        "price": current_price,
                        "amount": btc_bought,
                        "value": position_size,
                        "confidence": signal.confidence,
                    }
                )

            elif signal.signal == SignalType.SELL and position > 0:
                # Sell signal and have position
                sell_value = position * current_price
                cash += sell_value

                trades.append(
                    {
                        "type": "sell",
                        "timestamp": signal.timestamp,
                        "price": current_price,
                        "amount": position,
                        "value": sell_value,
                        "confidence": signal.confidence,
                    }
                )

                position = 0.0

            # Calculate current equity
            current_equity = cash + (position * current_price)
            equity_curve.append(current_equity)

        # Calculate performance metrics
        equity_series = pd.Series(equity_curve, index=data_with_indicators.index)
        performance = self._calculate_performance_metrics(
            equity_series, trades, initial_capital
        )

        result = BacktestResult(
            performance=performance,
            signals=signals,
            equity_curve=equity_series,
            trades=trades,
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=initial_capital,
            final_capital=equity_curve[-1] if equity_curve else initial_capital,
        )

        self.logger.info(
            f"Backtest completed. Total return: {performance.total_return:.2%}"
        )
        return result

    # ... rest of the methods remain the same ...

    def __str__(self) -> str:
        return f"{self.name}Strategy(type={self.strategy_type.value}, enabled={self.is_enabled})"

    def __repr__(self) -> str:
        return self.__str__()


# Keep alias for backward compatibility, but log deprecation
import warnings


class StrategySignal:
    """DEPRECATED: Use SignalType from models.py instead"""

    def __init__(self):
        warnings.warn(
            "StrategySignal is deprecated. Use SignalType from odin.core.models instead.",
            DeprecationWarning,
            stacklevel=2,
        )


BaseStrategy = Strategy  # Alias for backward compatibility
