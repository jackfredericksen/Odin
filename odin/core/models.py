"""Pydantic models for Odin trading bot."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class SignalType(str, Enum):
    """Trading signal types."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TrendType(str, Enum):
    """Market trend types."""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"


class StrategyType(str, Enum):
    """Strategy types."""
    MOVING_AVERAGE = "moving_average"
    RSI = "rsi"
    BOLLINGER_BANDS = "bollinger_bands"
    MACD = "macd"


class PriceData(BaseModel):
    """Bitcoin price data model."""
    
    timestamp: datetime
    price: float = Field(..., gt=0, description="Bitcoin price in USD")
    volume: Optional[float] = Field(None, ge=0, description="24h trading volume")
    high: Optional[float] = Field(None, gt=0, description="24h high price")
    low: Optional[float] = Field(None, gt=0, description="24h low price")
    change_24h: Optional[float] = Field(None, description="24h price change percentage")
    source: str = Field(..., description="Data source")
    
    @validator('high', 'low')
    def validate_high_low(cls, v, values):
        """Validate high/low prices are reasonable."""
        if v is not None and 'price' in values:
            price = values['price']
            if v > price * 2 or v < price * 0.5:
                raise ValueError("High/low price seems unrealistic")
        return v


class TradingSignal(BaseModel):
    """Trading signal model."""
    
    timestamp: datetime
    signal_type: SignalType
    price: float = Field(..., gt=0)
    confidence: float = Field(..., ge=0, le=1, description="Signal confidence (0-1)")
    strategy: StrategyType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class StrategyAnalysis(BaseModel):
    """Strategy analysis result model."""
    
    strategy: StrategyType
    current_price: float = Field(..., gt=0)
    trend: TrendType
    signal: Optional[TradingSignal] = None
    indicators: Dict[str, float] = Field(default_factory=dict)
    data_points: int = Field(..., ge=0)
    timestamp: datetime
    
    class Config:
        use_enum_values = True


class BacktestResult(BaseModel):
    """Backtest result model."""
    
    strategy: StrategyType
    period_hours: int = Field(..., gt=0)
    initial_balance: float = Field(..., gt=0)
    final_value: float = Field(..., gt=0)
    total_return_percent: float
    total_trades: int = Field(..., ge=0)
    winning_trades: int = Field(..., ge=0)
    losing_trades: int = Field(..., ge=0)
    win_rate_percent: float = Field(..., ge=0, le=100)
    max_drawdown_percent: float = Field(..., le=0)
    sharpe_ratio: Optional[float] = None
    trades: List[Dict[str, Any]] = Field(default_factory=list)
    
    @validator('winning_trades', 'losing_trades')
    def validate_trade_counts(cls, v, values):
        """Validate trade counts are consistent."""
        if 'total_trades' in values:
            total = values['total_trades']
            if 'winning_trades' in values and 'losing_trades' in values:
                if values['winning_trades'] + values['losing_trades'] > total:
                    raise ValueError("Winning + losing trades cannot exceed total trades")
        return v
    
    class Config:
        use_enum_values = True


class HealthStatus(BaseModel):
    """Health check status model."""
    
    status: str = Field(..., description="Overall status")
    timestamp: datetime
    uptime: float = Field(..., ge=0, description="Uptime in seconds")
    version: str
    database_status: str
    data_collector_status: str
    last_data_update: Optional[datetime] = None
    data_points_count: int = Field(..., ge=0)
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "uptime": 3600.0,
                "version": "2.0.0",
                "database_status": "connected",
                "data_collector_status": "running",
                "last_data_update": "2024-01-01T00:00:00Z",
                "data_points_count": 1000,
            }
        }


class APIResponse(BaseModel):
    """Generic API response model."""
    
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    @classmethod
    def success_response(cls, data: Any, message: str = "Success") -> "APIResponse":
        """Create success response."""
        return cls(
            success=True,
            message=message,
            data=data,
            timestamp=datetime.utcnow()
        )
    
    @classmethod
    def error_response(
        cls, 
        message: str, 
        error_details: Optional[Dict[str, Any]] = None
    ) -> "APIResponse":
        """Create error response."""
        return cls(
            success=False,
            message=message,
            error=error_details,
            timestamp=datetime.utcnow()
        )


class StrategyConfig(BaseModel):
    """Strategy configuration model."""
    
    strategy_type: StrategyType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "strategy_type": "moving_average",
                "parameters": {
                    "short_period": 5,
                    "long_period": 20
                },
                "enabled": True
            }
        }