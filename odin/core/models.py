"""
Core Data Models for Odin Bitcoin Trading Bot
Complete set of Pydantic models for all data structures.
"""
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

# Enums
class StrategyType(str, Enum):
    """Strategy types."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    MOMENTUM = "momentum"
    ARBITRAGE = "arbitrage"

class StrategySignal(str, Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class OrderType(str, Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class OrderSide(str, Enum):
    """Order side enum."""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class PositionType(str, Enum):
    """Position types."""
    LONG = "long"
    SHORT = "short"

class SignalType(str, Enum):
    """Signal types (alias for StrategySignal)."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

# Price Data Models
class PriceData(BaseModel):
    """Bitcoin price data model."""
    symbol: str = "BTC-USD"
    price: float = Field(..., gt=0, description="Current price")
    volume: Optional[float] = Field(None, ge=0, description="Trading volume")
    bid: Optional[float] = Field(None, gt=0, description="Bid price")
    ask: Optional[float] = Field(None, gt=0, description="Ask price")
    source: str = Field(..., description="Data source")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Technical indicators (optional)
    sma_5: Optional[float] = None
    sma_20: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None

class OHLCData(BaseModel):
    """OHLC candlestick data model."""
    symbol: str = "BTC-USD"
    timeframe: str = Field(..., description="Timeframe (1m, 5m, 1h, 1d, etc.)")
    timestamp: datetime
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: float = Field(..., ge=0)
    
    # Technical indicators (optional)
    sma_20: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None

class HistoricalData(BaseModel):
    """Historical price data model."""
    timestamp: datetime
    price: float = Field(..., gt=0)
    volume: Optional[float] = Field(None, ge=0)
    high: Optional[float] = Field(None, gt=0)
    low: Optional[float] = Field(None, gt=0)
    open: Optional[float] = Field(None, gt=0)
    close: Optional[float] = Field(None, gt=0)
    source: str = "historical"

# Market Data Models
class MarketDepth(BaseModel):
    """Market depth/order book data."""
    symbol: str = "BTC-USD"
    bids: List[List[float]] = Field(..., description="Bid prices and sizes")
    asks: List[List[float]] = Field(..., description="Ask prices and sizes")
    timestamp: datetime = Field(default_factory=datetime.now)

class MarketSummary(BaseModel):
    """Market summary statistics."""
    symbol: str = "BTC-USD"
    price: float
    change_24h: float
    change_24h_percent: float
    volume_24h: float
    market_cap: Optional[float] = None
    high_24h: float
    low_24h: float
    timestamp: datetime = Field(default_factory=datetime.now)

# Trading Models
class Signal(BaseModel):
    """Trading signal with metadata."""
    signal: StrategySignal
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    timestamp: datetime = Field(default_factory=datetime.now)
    price: float = Field(..., gt=0)
    reasoning: str = Field(..., description="Signal reasoning")
    indicators: Dict[str, float] = Field(default_factory=dict)
    risk_score: float = Field(..., ge=0, le=1, description="Risk score 0-1")

class Trade(BaseModel):
    """Trade execution model."""
    id: str
    timestamp: datetime
    strategy_id: Optional[str] = None
    symbol: str = "BTC-USD"
    side: StrategySignal  # buy/sell
    order_type: OrderType
    amount: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    status: OrderStatus = OrderStatus.PENDING
    executed_amount: Optional[float] = Field(None, ge=0)
    executed_price: Optional[float] = Field(None, gt=0)
    fees: Optional[float] = Field(None, ge=0)
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    notes: Optional[str] = None

class TradeOrder(BaseModel):
    """Trade order model for placing orders."""
    id: str = Field(default_factory=lambda: f"order_{int(time.time() * 1000000)}")
    timestamp: datetime = Field(default_factory=datetime.now)
    strategy_name: str
    symbol: str = "BTC-USD"
    order_type: OrderType
    side: OrderSide
    quantity: float = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    time_in_force: Optional[str] = "GTC"
    
    # Order tracking
    exchange_order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = Field(0.0, ge=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

class TradeExecution(BaseModel):
    """Trade execution details."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    strategy_name: str
    symbol: str = "BTC-USD"
    side: OrderSide
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    fee: Optional[float] = Field(None, ge=0)
    trade_id: str
    order_id: Optional[str] = None
    slippage: Optional[float] = None
    market_impact: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)

class TradeSignal(BaseModel):
    """Trade signal model."""
    id: str = Field(default_factory=lambda: f"signal_{int(time.time() * 1000000)}")
    strategy_name: str
    symbol: str = "BTC-USD"
    signal_type: StrategySignal
    confidence: float = Field(..., ge=0, le=1)
    price: float = Field(..., gt=0)
    timestamp: datetime = Field(default_factory=datetime.now)
    reasoning: Optional[str] = None
    indicators: Dict[str, float] = Field(default_factory=dict)
    executed: bool = False
    execution_price: Optional[float] = None
    execution_time: Optional[datetime] = None

class Position(BaseModel):
    """Trading position model."""
    id: str
    symbol: str = "BTC-USD"
    side: StrategySignal
    size: float = Field(..., gt=0)
    entry_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    pnl: float
    pnl_percentage: float
    timestamp: datetime = Field(default_factory=datetime.now)

# Portfolio Models
class PortfolioSnapshot(BaseModel):
    """Portfolio snapshot model."""
    timestamp: datetime = Field(default_factory=datetime.now)
    total_value: float = Field(..., ge=0)
    cash_balance: float = Field(..., ge=0)
    btc_balance: float = Field(..., ge=0)
    daily_pnl: Optional[float] = None
    daily_pnl_percentage: Optional[float] = None
    allocation: Optional[Dict[str, float]] = None

class PortfolioSummary(BaseModel):
    """Portfolio summary with key metrics."""
    total_value: float
    cash_balance: float
    btc_balance: float
    positions: List[Position] = Field(default_factory=list)
    daily_pnl: float
    daily_pnl_percent: float
    allocation: Dict[str, float] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

# Strategy Models
class StrategyConfig(BaseModel):
    """Strategy configuration model."""
    id: str
    name: str
    type: StrategyType
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    active: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class StrategyPerformance(BaseModel):
    """Strategy performance metrics."""
    strategy_id: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    volatility: float
    calmar_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.now)

class BacktestResult(BaseModel):
    """Backtesting results."""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    performance: StrategyPerformance
    signals: List[Signal] = Field(default_factory=list)
    trades: List[Trade] = Field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = Field(default_factory=list)

# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class ConnectionStatus(BaseModel):
    """WebSocket connection status."""
    connected: bool
    connection_count: int
    last_ping: Optional[datetime] = None
    uptime: Optional[float] = None

# API Response Models
class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthCheck(BaseModel):
    """Health check response model."""
    status: str
    version: str
    uptime: float
    components: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

# Error Models
class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Statistics Models
class DataStats(BaseModel):
    """Data statistics model."""
    total_records: int = 0
    latest_timestamp: Optional[datetime] = None
    earliest_timestamp: Optional[datetime] = None
    average_price: Optional[float] = None
    price_range: Optional[Dict[str, float]] = None
    data_quality: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.now)

class DatabaseStats(BaseModel):
    """Database statistics model."""
    bitcoin_prices_count: int = 0
    strategies_count: int = 0
    trades_count: int = 0
    portfolio_snapshots_count: int = 0
    strategy_signals_count: int = 0
    active_strategies: int = 0
    trades_today: int = 0
    latest_portfolio_value: Optional[float] = None
    database_size_mb: float = 0.0
    price_data_range: Optional[Dict[str, str]] = None

# Configuration Models
class DatabaseConfig(BaseModel):
    """Database configuration model."""
    url: str
    max_connections: int = 10
    timeout: int = 30

class APIConfig(BaseModel):
    """API configuration model."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: List[str] = Field(default_factory=list)

class TradingConfig(BaseModel):
    """Trading configuration model."""
    max_position_size: float = Field(0.95, ge=0, le=1)
    risk_per_trade: float = Field(0.02, ge=0, le=0.1)
    stop_loss_pct: float = Field(0.05, ge=0, le=0.2)
    take_profit_pct: float = Field(0.10, ge=0, le=0.5)
    enable_live_trading: bool = False

# Utility Functions
def create_price_data(timestamp: datetime, price: float, volume: float = None, source: str = "api") -> PriceData:
    """Create a PriceData instance."""
    return PriceData(timestamp=timestamp, price=price, volume=volume, source=source)

def create_trade_execution(trade_id: str, strategy_name: str, side: str, quantity: float, price: float) -> TradeExecution:
    """Create a TradeExecution instance."""
    return TradeExecution(
        id=trade_id,
        strategy_name=strategy_name,
        symbol="BTC-USD",
        side=OrderSide(side),
        quantity=quantity,
        price=price,
        trade_id=trade_id
    )

def create_api_response(success: bool, data: Any = None, message: str = None) -> APIResponse:
    """Create an APIResponse instance."""
    return APIResponse(success=success, data=data, message=message)

# Export all models
__all__ = [
    # Enums
    'StrategyType', 'StrategySignal', 'OrderType', 'OrderSide', 'OrderStatus', 
    'PositionType', 'SignalType',
    
    # Price Models
    'PriceData', 'OHLCData', 'HistoricalData',
    
    # Market Models
    'MarketDepth', 'MarketSummary',
    
    # Trading Models
    'Signal', 'Trade', 'TradeOrder', 'TradeExecution', 'TradeSignal', 'Position',
    
    # Portfolio Models
    'PortfolioSnapshot', 'PortfolioSummary',
    
    # Strategy Models
    'StrategyConfig', 'StrategyPerformance', 'BacktestResult',
    
    # WebSocket Models
    'WebSocketMessage', 'ConnectionStatus',
    
    # API Models
    'APIResponse', 'HealthCheck', 'ErrorResponse',
    
    # Statistics Models
    'DataStats', 'DatabaseStats',
    
    # Configuration Models
    'DatabaseConfig', 'APIConfig', 'TradingConfig',
    
    # Utility Functions
    'create_price_data', 'create_trade_execution', 'create_api_response'
]