"""
Market State Definitions for Regime Detection
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class MarketRegime(Enum):
    """Enumeration of market regimes"""
    BULL_TRENDING = "bull_trending"
    BEAR_TRENDING = "bear_trending"  
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    CRISIS = "crisis"
    UNKNOWN = "unknown"

@dataclass
class RegimeCharacteristics:
    """Characteristics that define a market regime"""
    regime: MarketRegime
    description: str
    typical_duration_days: int
    volatility_range: tuple  # (min, max)
    momentum_range: tuple    # (min, max) 
    volume_characteristics: str
    typical_indicators: List[str]
    trading_approach: str
    risk_level: str

# Define regime characteristics
REGIME_DEFINITIONS = {
    MarketRegime.BULL_TRENDING: RegimeCharacteristics(
        regime=MarketRegime.BULL_TRENDING,
        description="Strong sustained upward price movement with momentum",
        typical_duration_days=45,
        volatility_range=(0.01, 0.04),
        momentum_range=(0.005, 0.05),
        volume_characteristics="Increasing volume on advances",
        typical_indicators=[
            "Price > MA(20) > MA(50)",
            "RSI > 50 trending higher", 
            "MACD > Signal line",
            "Bollinger Bands expanding upward"
        ],
        trading_approach="Trend following, momentum strategies",
        risk_level="Medium-High"
    ),
    
    MarketRegime.BEAR_TRENDING: RegimeCharacteristics(
        regime=MarketRegime.BEAR_TRENDING,
        description="Sustained downward pressure with selling momentum",
        typical_duration_days=30,
        volatility_range=(0.015, 0.06),
        momentum_range=(-0.05, -0.005),
        volume_characteristics="High volume on declines",
        typical_indicators=[
            "Price < MA(20) < MA(50)",
            "RSI < 50 trending lower",
            "MACD < Signal line", 
            "Bollinger Bands expanding downward"
        ],
        trading_approach="Short selling, defensive positioning",
        risk_level="High"
    ),
    
    MarketRegime.SIDEWAYS: RegimeCharacteristics(
        regime=MarketRegime.SIDEWAYS,
        description="Range-bound trading with no clear directional bias",
        typical_duration_days=60,
        volatility_range=(0.005, 0.025),
        momentum_range=(-0.01, 0.01),
        volume_characteristics="Stable, moderate volume",
        typical_indicators=[
            "Price oscillating around MA(20)",
            "RSI between 40-60",
            "MACD near zero line",
            "Bollinger Bands contracting"
        ],
        trading_approach="Mean reversion, range trading",
        risk_level="Medium"
    ),
    
    MarketRegime.HIGH_VOLATILITY: RegimeCharacteristics(
        regime=MarketRegime.HIGH_VOLATILITY,
        description="Elevated price swings with uncertain direction",
        typical_duration_days=15,
        volatility_range=(0.04, 0.12),
        momentum_range=(-0.03, 0.03),
        volume_characteristics="Erratic, often elevated volume",
        typical_indicators=[
            "Wide Bollinger Bands",
            "RSI making extreme swings",
            "MACD highly volatile",
            "Price gaps and large candles"
        ],
        trading_approach="Volatility strategies, smaller positions",
        risk_level="Very High"
    ),
    
    MarketRegime.CRISIS: RegimeCharacteristics(
        regime=MarketRegime.CRISIS,
        description="Extreme market stress with potential for large losses",
        typical_duration_days=7,
        volatility_range=(0.08, 0.30),
        momentum_range=(-0.15, -0.02),
        volume_characteristics="Panic selling, very high volume",
        typical_indicators=[
            "Extreme price movements (>5% daily)",
            "RSI < 30 or > 70 sustained",
            "Volume spikes > 3x average",
            "News-driven price action"
        ],
        trading_approach="Risk-off, capital preservation",
        risk_level="Extreme"
    )
}

def get_regime_characteristics(regime: MarketRegime) -> Optional[RegimeCharacteristics]:
    """Get characteristics for a specific regime"""
    return REGIME_DEFINITIONS.get(regime)

def get_all_regime_info() -> Dict[str, Dict]:
    """Get information about all regimes"""
    return {
        regime.value: {
            "description": chars.description,
            "typical_duration": chars.typical_duration_days,
            "risk_level": chars.risk_level,
            "trading_approach": chars.trading_approach,
            "indicators": chars.typical_indicators
        }
        for regime, chars in REGIME_DEFINITIONS.items()
    }
