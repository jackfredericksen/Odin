"""
Odin Core Configuration Manager - Centralized Configuration System
Handles all application configuration with validation and environment overrides.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite:///data/odin.db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


@dataclass
class ExchangeConfig:
    """Exchange configuration."""
    name: str = "coinbase"
    sandbox: bool = True
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    passphrase: Optional[str] = None
    rate_limit_delay: float = 0.1
    max_retries: int = 3
    timeout: int = 30


@dataclass
class TradingConfig:
    """Trading configuration."""
    enable_live_trading: bool = False
    paper_trading: bool = True
    initial_capital: float = 100000.0
    
    # Risk management
    max_position_size: float = 0.95
    risk_per_trade: float = 0.02
    max_daily_loss: float = 0.05
    max_drawdown: float = 0.15
    
    # Position management
    max_open_positions: int = 10
    position_timeout_hours: int = 24
    auto_close_on_stop_loss: bool = True
    
    # Rebalancing
    auto_rebalance: bool = True
    rebalance_threshold: float = 0.05
    rebalance_frequency_hours: int = 24


@dataclass
class StrategyConfig:
    """Strategy configuration."""
    enabled: bool = True
    max_allocation: float = 0.25
    min_confidence: float = 0.6
    cooldown_minutes: int = 60
    stop_loss_percent: float = 0.05
    take_profit_percent: float = 0.10


@dataclass
class DataConfig:
    """Data collection configuration."""
    collection_interval: int = 60  # seconds
    historical_days: int = 365
    backup_frequency_hours: int = 24
    cleanup_old_data_days: int = 90
    max_price_deviation: float = 0.1  # 10% max price jump
    
    # Data sources
    enable_yfinance: bool = True
    enable_coinbase: bool = True
    enable_binance: bool = False
    fallback_to_mock: bool = True


@dataclass
class APIConfig:
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    cors_origins: list = field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "data/logs/odin.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = "odin-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30


@dataclass
class OdinConfig:
    """Main application configuration."""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    data: DataConfig = field(default_factory=DataConfig)
    api: APIConfig = field(default_factory=APIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Strategy configurations
    strategies: Dict[str, StrategyConfig] = field(default_factory=lambda: {
        "moving_average": StrategyConfig(enabled=True, max_allocation=0.25),
        "rsi": StrategyConfig(enabled=True, max_allocation=0.25),
        "bollinger_bands": StrategyConfig(enabled=True, max_allocation=0.25),
        "macd": StrategyConfig(enabled=True, max_allocation=0.25)
    })
    
    def validate(self) -> bool:
        """Validate configuration."""
        errors = []
        
        # Validate trading config
        if not 0 <= self.trading.max_position_size <= 1:
            errors.append("max_position_size must be between 0 and 1")
        
        if not 0 <= self.trading.risk_per_trade <= 0.1:
            errors.append("risk_per_trade must be between 0 and 0.1")
        
        if not 0 <= self.trading.max_daily_loss <= 0.5:
            errors.append("max_daily_loss must be between 0 and 0.5")
        
        # Validate strategy allocations
        total_allocation = sum(s.max_allocation for s in self.strategies.values())
        if total_allocation > 1.0:
            errors.append(f"Total strategy allocation ({total_allocation:.2f}) exceeds 1.0")
        
        # Validate exchange config for live trading
        if self.trading.enable_live_trading and not self.exchange.sandbox:
            if not all([self.exchange.api_key, self.exchange.secret_key]):
                errors.append("Live trading requires exchange API credentials")
        
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        
        return True


class ConfigManager:
    """Configuration manager with file loading and environment overrides."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config.json")
        self.env_file = Path(".env")
        self._config: Optional[OdinConfig] = None
    
    def load_config(self) -> OdinConfig:
        """Load configuration from file and environment."""
        if self._config is None:
            self._config = self._create_default_config()
            
            # Load from file if exists
            if self.config_path.exists():
                self._load_from_file()
            
            # Override with environment variables
            self._load_from_environment()
            
            # Validate configuration
            if not self._config.validate():
                raise ValueError("Configuration validation failed")
            
            logger.info(f"Configuration loaded successfully ({self._config.environment})")
        
        return self._config
    
    def save_config(self, config: Optional[OdinConfig] = None) -> bool:
        """Save configuration to file."""
        try:
            config_to_save = config or self._config
            if not config_to_save:
                logger.error("No configuration to save")
                return False
            
            config_dict = self._config_to_dict(config_to_save)
            
            with open(self.config_path, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values."""
        try:
            if not self._config:
                self.load_config()
            
            self._apply_updates(self._config, updates)
            
            if self._config.validate():
                logger.info("Configuration updated successfully")
                return True
            else:
                logger.error("Configuration update failed validation")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False
    
    def get_strategy_config(self, strategy_name: str) -> Optional[StrategyConfig]:
        """Get configuration for specific strategy."""
        if not self._config:
            self.load_config()
        
        return self._config.strategies.get(strategy_name)
    
    def is_live_trading_enabled(self) -> bool:
        """Check if live trading is enabled and properly configured."""
        if not self._config:
            self.load_config()
        
        return (
            self._config.trading.enable_live_trading and 
            not self._config.trading.paper_trading and
            self._config.validate()
        )
    
    def _create_default_config(self) -> OdinConfig:
        """Create default configuration."""
        return OdinConfig()
    
    def _load_from_file(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = json.load(f)
            
            self._dict_to_config(config_dict, self._config)
            logger.info(f"Configuration loaded from {self.config_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load configuration file: {e}")
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            # Trading
            "ODIN_ENABLE_LIVE_TRADING": ("trading.enable_live_trading", bool),
            "ODIN_PAPER_TRADING": ("trading.paper_trading", bool),
            "ODIN_INITIAL_CAPITAL": ("trading.initial_capital", float),
            "ODIN_MAX_POSITION_SIZE": ("trading.max_position_size", float),
            "ODIN_RISK_PER_TRADE": ("trading.risk_per_trade", float),
            
            # Exchange
            "ODIN_EXCHANGE_NAME": ("exchange.name", str),
            "ODIN_EXCHANGE_SANDBOX": ("exchange.sandbox", bool),
            "ODIN_API_KEY": ("exchange.api_key", str),
            "ODIN_SECRET_KEY": ("exchange.secret_key", str),
            "ODIN_PASSPHRASE": ("exchange.passphrase", str),
            
            # API
            "ODIN_HOST": ("api.host", str),
            "ODIN_PORT": ("api.port", int),
            "ODIN_DEBUG": ("api.debug", bool),
            
            # Database
            "ODIN_DATABASE_URL": ("database.url", str),
            
            # Environment
            "ODIN_ENVIRONMENT": ("environment", str),
        }
        
        for env_var, (config_path, value_type) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if value_type == bool:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type in (int, float):
                        value = value_type(value)
                    
                    self._set_nested_value(self._config, config_path, value)
                    
                except ValueError as e:
                    logger.warning(f"Invalid value for {env_var}: {value} ({e})")
    
    def _config_to_dict(self, config: OdinConfig) -> Dict[str, Any]:
        """Convert config object to dictionary."""
        result = {}
        
        for field_name, field_value in config.__dict__.items():
            if hasattr(field_value, '__dict__'):
                result[field_name] = field_value.__dict__.copy()
            else:
                result[field_name] = field_value
        
        return result
    
    def _dict_to_config(self, config_dict: Dict[str, Any], config: OdinConfig) -> None:
        """Update config object from dictionary."""
        for key, value in config_dict.items():
            if hasattr(config, key):
                config_attr = getattr(config, key)
                
                if hasattr(config_attr, '__dict__') and isinstance(value, dict):
                    # Update nested config object
                    for nested_key, nested_value in value.items():
                        if hasattr(config_attr, nested_key):
                            setattr(config_attr, nested_key, nested_value)
                else:
                    setattr(config, key, value)
    
    def _set_nested_value(self, obj: Any, path: str, value: Any) -> None:
        """Set nested value using dot notation."""
        parts = path.split('.')
        current = obj
        
        for part in parts[:-1]:
            current = getattr(current, part)
        
        setattr(current, parts[-1], value)
    
    def _apply_updates(self, config: OdinConfig, updates: Dict[str, Any]) -> None:
        """Apply updates to configuration."""
        for key, value in updates.items():
            if '.' in key:
                self._set_nested_value(config, key, value)
            else:
                if hasattr(config, key):
                    setattr(config, key, value)


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> OdinConfig:
    """Get current configuration."""
    return get_config_manager().load_config()


def update_config(updates: Dict[str, Any]) -> bool:
    """Update global configuration."""
    return get_config_manager().update_config(updates)


def save_config() -> bool:
    """Save current configuration to file."""
    return get_config_manager().save_config()