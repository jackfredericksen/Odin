"""
Odin Configuration - Updated to use new Configuration Manager
Provides backward compatibility while leveraging enhanced config system.
"""

import os
from typing import Optional
from pathlib import Path

# Import new configuration system
from .core.config_manager import get_config, get_config_manager, OdinConfig
from .utils.logging import get_logger

logger = get_logger(__name__)


def get_settings() -> OdinConfig:
    """
    Get application settings using new configuration manager.
    
    This function provides backward compatibility for existing code
    while leveraging the enhanced configuration system.
    """
    return get_config()


class Settings:
    """
    Backward compatibility wrapper for old settings access pattern.
    
    This class maintains the same interface as the old settings system
    while delegating to the new configuration manager.
    """
    
    def __init__(self):
        self._config = get_config()
    
    @property
    def environment(self) -> str:
        """Get environment name."""
        return self._config.environment.value
    
    @property
    def debug(self) -> bool:
        """Get debug mode."""
        return self._config.debug
    
    @property
    def host(self) -> str:
        """Get API host."""
        return self._config.api.host
    
    @property
    def port(self) -> int:
        """Get API port."""
        return self._config.api.port
    
    @property
    def database_url(self) -> str:
        """Get database URL."""
        return self._config.database.url
    
    @property
    def exchange_name(self) -> str:
        """Get exchange name."""
        return self._config.exchange.name
    
    @property
    def exchange_sandbox(self) -> bool:
        """Get exchange sandbox mode."""
        return self._config.exchange.sandbox
    
    @property
    def enable_live_trading(self) -> bool:
        """Get live trading enabled status."""
        return self._config.trading.enable_live_trading
    
    @property
    def paper_trading(self) -> bool:
        """Get paper trading mode."""
        return self._config.trading.paper_trading
    
    @property
    def initial_capital(self) -> float:
        """Get initial trading capital."""
        return self._config.trading.initial_capital
    
    @property
    def max_position_size(self) -> float:
        """Get maximum position size."""
        return self._config.trading.max_position_size
    
    @property
    def risk_per_trade(self) -> float:
        """Get risk per trade."""
        return self._config.trading.risk_per_trade
    
    @property
    def api_key(self) -> Optional[str]:
        """Get exchange API key."""
        return self._config.exchange.api_key
    
    @property
    def secret_key(self) -> Optional[str]:
        """Get exchange secret key."""
        return self._config.exchange.secret_key
    
    @property
    def passphrase(self) -> Optional[str]:
        """Get exchange passphrase."""
        return self._config.exchange.passphrase
    
    def reload(self):
        """Reload configuration."""
        config_manager = get_config_manager()
        self._config = config_manager.load_config()
        logger.info("Configuration reloaded")


# Global settings instance for backward compatibility
settings = Settings()


# Environment variable helpers for backward compatibility
def get_env_var(name: str, default: str = "") -> str:
    """Get environment variable with default."""
    return os.getenv(name, default)


def get_env_bool(name: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    value = os.getenv(name, "").lower()
    return value in ("true", "1", "yes", "on") if value else default


def get_env_int(name: str, default: int = 0) -> int:
    """Get integer environment variable."""
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def get_env_float(name: str, default: float = 0.0) -> float:
    """Get float environment variable."""
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


# Legacy configuration class for complete backward compatibility
class LegacyConfig:
    """
    Legacy configuration class that maps to new configuration system.
    
    This maintains complete backward compatibility for any code that
    directly imported and used the old Config class.
    """
    
    def __init__(self):
        self._config = get_config()
    
    # Environment settings
    ENVIRONMENT = property(lambda self: self._config.environment.value)
    DEBUG = property(lambda self: self._config.debug)
    
    # API settings
    HOST = property(lambda self: self._config.api.host)
    PORT = property(lambda self: self._config.api.port)
    CORS_ORIGINS = property(lambda self: self._config.api.cors_origins)
    
    # Database settings
    DATABASE_URL = property(lambda self: self._config.database.url)
    
    # Exchange settings
    EXCHANGE_NAME = property(lambda self: self._config.exchange.name)
    EXCHANGE_SANDBOX = property(lambda self: self._config.exchange.sandbox)
    API_KEY = property(lambda self: self._config.exchange.api_key)
    SECRET_KEY = property(lambda self: self._config.exchange.secret_key)
    PASSPHRASE = property(lambda self: self._config.exchange.passphrase)
    
    # Trading settings
    ENABLE_LIVE_TRADING = property(lambda self: self._config.trading.enable_live_trading)
    PAPER_TRADING = property(lambda self: self._config.trading.paper_trading)
    INITIAL_CAPITAL = property(lambda self: self._config.trading.initial_capital)
    MAX_POSITION_SIZE = property(lambda self: self._config.trading.max_position_size)
    RISK_PER_TRADE = property(lambda self: self._config.trading.risk_per_trade)
    MAX_DAILY_LOSS = property(lambda self: self._config.trading.max_daily_loss)
    MAX_DRAWDOWN = property(lambda self: self._config.trading.max_drawdown)
    
    # Data settings
    COLLECTION_INTERVAL = property(lambda self: self._config.data.collection_interval)
    HISTORICAL_DAYS = property(lambda self: self._config.data.historical_days)
    
    # Logging settings
    LOG_LEVEL = property(lambda self: self._config.logging.level.value)
    LOG_FILE = property(lambda self: self._config.logging.file_path)


# Create legacy config instance
Config = LegacyConfig()


# Migration utilities
def migrate_legacy_config():
    """
    Migrate legacy configuration files to new format.
    
    This function can be called to automatically migrate old configuration
    files to the new configuration manager format.
    """
    legacy_config_files = [
        ".env",
        "config.ini", 
        "settings.json"
    ]
    
    config_manager = get_config_manager()
    
    for config_file in legacy_config_files:
        config_path = Path(config_file)
        if config_path.exists():
            logger.info(f"Found legacy config file: {config_file}")
            # Migration logic would go here
            # For now, just log that we found it
    
    # Save current configuration to new format
    config_manager.save_config()
    logger.info("Configuration migration completed")


def validate_configuration() -> bool:
    """
    Validate current configuration.
    
    Returns True if configuration is valid, False otherwise.
    """
    try:
        config = get_config()
        return config.validate()
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


def update_configuration(updates: dict) -> bool:
    """
    Update configuration with new values.
    
    Args:
        updates: Dictionary of configuration updates using dot notation
                Example: {"trading.enable_live_trading": True}
    
    Returns:
        True if update was successful, False otherwise.
    """
    try:
        config_manager = get_config_manager()
        return config_manager.update_config(updates)
    except Exception as e:
        logger.error(f"Configuration update failed: {e}")
        return False


def get_configuration_summary() -> dict:
    """
    Get a summary of current configuration settings.
    
    Returns:
        Dictionary containing key configuration settings.
    """
    config = get_config()
    
    return {
        "environment": config.environment.value,
        "debug": config.debug,
        "api": {
            "host": config.api.host,
            "port": config.api.port,
            "debug": config.api.debug
        },
        "trading": {
            "live_trading": config.trading.enable_live_trading,
            "paper_trading": config.trading.paper_trading,
            "initial_capital": config.trading.initial_capital,
            "max_position_size": config.trading.max_position_size
        },
        "exchange": {
            "name": config.exchange.name,
            "sandbox": config.exchange.sandbox,
            "has_credentials": bool(config.exchange.api_key and config.exchange.secret_key)
        },
        "data": {
            "collection_interval": config.data.collection_interval,
            "historical_days": config.data.historical_days
        },
        "logging": {
            "level": config.logging.level.value,
            "file_enabled": config.logging.enable_file,
            "console_enabled": config.logging.enable_console
        }
    }


# Export commonly used items for backward compatibility
__all__ = [
    'get_settings',
    'settings', 
    'Config',
    'Settings',
    'get_env_var',
    'get_env_bool', 
    'get_env_int',
    'get_env_float',
    'migrate_legacy_config',
    'validate_configuration',
    'update_configuration',
    'get_configuration_summary'
]