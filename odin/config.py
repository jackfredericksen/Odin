"""
Odin Bitcoin Trading Bot - Configuration Management (Fixed)
"""

import os
from typing import Optional
from functools import lru_cache

try:
    from pydantic import Field
    from pydantic_settings import BaseSettings
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

if PYDANTIC_AVAILABLE:
    class Settings(BaseSettings):
        """Application settings using Pydantic."""
        
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

else:
    # Fallback simple settings without Pydantic
    class Settings:
        """Simple application settings."""
        
        def __init__(self):
            # Application
            self.environment = os.getenv("ODIN_ENV", "development")
            self.debug = os.getenv("ODIN_DEBUG", "false").lower() == "true"
            self.host = os.getenv("ODIN_HOST", "0.0.0.0")
            self.port = int(os.getenv("ODIN_PORT", "8000"))
            self.secret_key = os.getenv("ODIN_SECRET_KEY", "change-this-in-production")
            
            # Database
            self.database_url = os.getenv("DATABASE_URL", "sqlite:///./data/bitcoin_data.db")
            
            # Trading
            self.enable_live_trading = os.getenv("ENABLE_LIVE_TRADING", "false").lower() == "true"
            self.max_position_size = float(os.getenv("MAX_POSITION_SIZE", "0.95"))
            self.risk_per_trade = float(os.getenv("RISK_PER_TRADE", "0.02"))
            
            # Exchange
            self.exchange_name = os.getenv("EXCHANGE_NAME", "binance")
            self.exchange_api_key = os.getenv("EXCHANGE_API_KEY")
            self.exchange_secret_key = os.getenv("EXCHANGE_SECRET_KEY")
            self.exchange_sandbox = os.getenv("EXCHANGE_SANDBOX", "true").lower() == "true"
            
            # Security
            self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-this")
            self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
            self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()