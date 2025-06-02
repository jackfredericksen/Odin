"""
Odin Bitcoin Trading Bot - Configuration Management
"""

import os
from typing import Optional
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    environment: str = Field("development", env="ODIN_ENV")
    debug: bool = Field(False, env="ODIN_DEBUG")
    host: str = Field("0.0.0.0", env="ODIN_HOST")
    port: int = Field(8000, env="ODIN_PORT")
    secret_key: str = Field("change-this-in-production", env="ODIN_SECRET_KEY")
    
    # Database
    database_url: str = Field("sqlite:///./data/bitcoin_data.db", env="DATABASE_URL")
    
    # Trading
    enable_live_trading: bool = Field(False, env="ENABLE_LIVE_TRADING")
    max_position_size: float = Field(0.95, env="MAX_POSITION_SIZE")
    risk_per_trade: float = Field(0.02, env="RISK_PER_TRADE")
    
    # Exchange
    exchange_name: str = Field("binance", env="EXCHANGE_NAME")
    exchange_api_key: Optional[str] = Field(None, env="EXCHANGE_API_KEY")
    exchange_secret_key: Optional[str] = Field(None, env="EXCHANGE_SECRET_KEY")
    exchange_sandbox: bool = Field(True, env="EXCHANGE_SANDBOX")
    
    # Security
    jwt_secret_key: str = Field("jwt-secret-change-this", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()