"""Configuration management for Odin trading bot."""

from typing import List, Optional
from pydantic import BaseSettings, Field, validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=5000, ge=1, le=65535, description="API port")
    api_reload: bool = Field(default=False, description="Enable auto-reload in development")
    api_workers: int = Field(default=1, ge=1, le=10, description="Number of worker processes")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///data/bitcoin_data.db",
        description="Database connection URL"
    )
    
    # Data Collection Settings
    data_update_interval: int = Field(
        default=30, ge=10, le=300, description="Data collection interval in seconds"
    )
    data_sources: List[str] = Field(
        default=["coindesk", "blockchain_info", "coingecko"],
        description="Data sources in fallback order"
    )
    
    # Strategy Parameters
    ma_short_period: int = Field(default=5, ge=2, le=50, description="MA short period")
    ma_long_period: int = Field(default=20, ge=5, le=200, description="MA long period")
    rsi_period: int = Field(default=14, ge=2, le=50, description="RSI period")
    rsi_oversold: int = Field(default=30, ge=10, le=40, description="RSI oversold level")
    rsi_overbought: int = Field(default=70, ge=60, le=90, description="RSI overbought level")
    bb_period: int = Field(default=20, ge=5, le=50, description="Bollinger Bands period")
    bb_std_dev: float = Field(default=2.0, ge=1.0, le=3.0, description="BB standard deviation")
    macd_fast: int = Field(default=12, ge=5, le=50, description="MACD fast period")
    macd_slow: int = Field(default=26, ge=10, le=100, description="MACD slow period")
    macd_signal: int = Field(default=9, ge=3, le=20, description="MACD signal period")
    
    # Security Settings
    api_key: str = Field(default="", description="API authentication key")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5000"],
        description="Allowed CORS origins"
    )
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/odin.log", description="Log file path")
    
    # Rate Limiting
    rate_limit_calls: int = Field(default=100, ge=10, description="Rate limit calls per period")
    rate_limit_period: int = Field(default=60, ge=10, description="Rate limit period in seconds")
    
    # External API URLs
    coindesk_api_url: str = Field(
        default="https://api.coindesk.com/v1/bpi/currentprice.json",
        description="CoinDesk API URL"
    )
    blockchain_api_url: str = Field(
        default="https://api.blockchain.info/ticker",
        description="Blockchain.info API URL"
    )
    coingecko_api_url: str = Field(
        default="https://api.coingecko.com/api/v3",
        description="CoinGecko API base URL"
    )
    
    @validator('ma_long_period')
    def validate_ma_periods(cls, v, values):
        """Ensure long MA period is greater than short MA period."""
        if 'ma_short_period' in values and v <= values['ma_short_period']:
            raise ValueError('MA long period must be greater than short period')
        return v
    
    @validator('rsi_overbought')
    def validate_rsi_levels(cls, v, values):
        """Ensure RSI overbought is greater than oversold."""
        if 'rsi_oversold' in values and v <= values['rsi_oversold']:
            raise ValueError('RSI overbought must be greater than oversold')
        return v
    
    @validator('macd_slow')
    def validate_macd_periods(cls, v, values):
        """Ensure MACD slow period is greater than fast period."""
        if 'macd_fast' in values and v <= values['macd_fast']:
            raise ValueError('MACD slow period must be greater than fast period')
        return v
    
    @validator('log_file')
    def create_log_directory(cls, v):
        """Create log directory if it doesn't exist."""
        log_path = Path(v)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator('database_url')
    def create_data_directory(cls, v):
        """Create data directory for SQLite databases."""
        if v.startswith('sqlite:///'):
            db_path = Path(v.replace('sqlite:///', ''))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True


# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings instance."""
    return settings