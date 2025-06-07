# odin/config.py
"""
Enhanced Odin Configuration with AI Settings
Comprehensive configuration management for trading bot and AI features
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class AIConfig:
    """AI-specific configuration settings"""
    
    # Regime Detection Settings
    regime_update_frequency: int = 20  # How often to update regime (data points)
    min_regime_confidence: float = 0.6  # Minimum confidence for regime decisions
    regime_model_path: str = "data/models/regime_models/"
    n_regimes: int = 5  # Number of market regimes to detect
    
    # Strategy Management Settings
    strategy_rebalance_frequency: int = 100  # How often to rebalance weights
    adaptive_strategy_enabled: bool = True
    strategy_config_path: str = "data/strategy_configs/"
    
    # Performance Tracking
    performance_history_limit: int = 1000
    regime_history_limit: int = 500
    
    # Model Training Settings
    min_training_samples: int = 200
    feature_engineering_enabled: bool = True
    auto_retrain_threshold: float = 0.7  # Retrain if performance drops below this
    auto_retrain_enabled: bool = True
    
    # Data Collection for AI
    feature_lookback_window: int = 60  # Days of data for feature calculation
    regime_detection_window: int = 20  # Data points for regime detection
    
    # Risk Management per Regime
    crisis_mode_enabled: bool = True
    max_regime_exposure: Dict[str, float] = field(default_factory=lambda: {
        "bull_trending": 0.9,
        "bear_trending": 0.5,
        "sideways": 0.7,
        "high_volatility": 0.4,
        "crisis": 0.1
    })
    
    # Model Performance Monitoring
    performance_monitoring_enabled: bool = True
    health_check_interval: int = 300  # seconds
    model_freshness_threshold: int = 100  # data points before considering stale
    
    # Advanced AI Features
    ensemble_models_enabled: bool = True
    multi_timeframe_analysis: bool = True
    sentiment_analysis_enabled: bool = False  # Future feature
    
    def __post_init__(self):
        """Post-initialization setup"""
        # Ensure directories exist
        Path(self.regime_model_path).mkdir(parents=True, exist_ok=True)
        Path(self.strategy_config_path).mkdir(parents=True, exist_ok=True)
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate AI configuration settings"""
        assert 0.1 <= self.min_regime_confidence <= 1.0, "Regime confidence must be between 0.1 and 1.0"
        assert self.regime_update_frequency > 0, "Regime update frequency must be positive"
        assert self.min_training_samples >= 100, "Minimum training samples should be at least 100"
        assert 3 <= self.n_regimes <= 10, "Number of regimes should be between 3 and 10"

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    
    # Primary database
    database_url: str = "sqlite:///data/bitcoin_data.db"
    
    # Connection settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # Migration settings
    auto_migrate: bool = True
    backup_before_migration: bool = True
    
    # Performance settings
    echo_sql: bool = False  # Set to True for SQL debugging
    
    def __post_init__(self):
        """Ensure database directory exists for SQLite"""
        if self.database_url.startswith('sqlite:'):
            db_path = self.database_url.replace('sqlite:///', '')
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

@dataclass
class TradingConfig:
    """Trading-specific configuration"""
    
    # Core trading settings
    enable_live_trading: bool = False
    max_position_size: float = 0.95
    risk_per_trade: float = 0.02
    
    # Order execution
    default_order_type: str = "market"  # market, limit
    order_timeout: int = 300  # seconds
    max_slippage: float = 0.005  # 0.5%
    
    # Risk management
    max_daily_loss: float = 0.05  # 5% of portfolio
    max_drawdown: float = 0.15  # 15% maximum drawdown
    stop_loss_enabled: bool = True
    take_profit_enabled: bool = True
    
    # Position management
    max_concurrent_positions: int = 3
    position_sizing_method: str = "fixed_risk"  # fixed_risk, fixed_amount, kelly
    
    # Trading hours (UTC)
    trading_enabled_24_7: bool = True
    trading_start_hour: int = 0
    trading_end_hour: int = 24
    
    def __post_init__(self):
        """Validate trading configuration"""
        assert 0.1 <= self.max_position_size <= 1.0, "Max position size must be between 0.1 and 1.0"
        assert 0.001 <= self.risk_per_trade <= 0.1, "Risk per trade must be between 0.1% and 10%"
        assert self.max_daily_loss > 0, "Max daily loss must be positive"

@dataclass
class DataConfig:
    """Data collection and processing configuration"""
    
    # Data sources
    data_sources: List[str] = field(default_factory=lambda: ["coinbase", "coingecko", "binance"])
    primary_data_source: str = "coinbase"
    
    # Collection settings
    data_update_interval: int = 30  # seconds
    historical_data_days: int = 365  # days to maintain
    
    # Data quality
    data_validation_enabled: bool = True
    outlier_detection_enabled: bool = True
    data_interpolation_method: str = "linear"
    
    # Technical indicators
    calculate_indicators: bool = True
    indicator_periods: Dict[str, int] = field(default_factory=lambda: {
        "rsi": 14,
        "ma_short": 20,
        "ma_long": 50,
        "bollinger": 20,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9
    })
    
    # Data storage
    data_compression: bool = True
    backup_data: bool = True
    backup_interval_hours: int = 24

@dataclass
class SecurityConfig:
    """Security and authentication configuration"""
    
    # API security
    secret_key: str = "your-secret-key-here-change-in-production"
    jwt_secret_key: str = "your-jwt-secret-here-change-in-production"
    access_token_expire_minutes: int = 30
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limits: Dict[str, str] = field(default_factory=lambda: {
        "default": "100/minute",
        "data": "60/minute", 
        "strategies": "20/minute",
        "trading": "30/minute",
        "ai": "40/minute"
    })
    
    # CORS settings
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])  # Restrict in production
    
    # API documentation
    docs_enabled: bool = True
    redoc_enabled: bool = True
    
    def __post_init__(self):
        """Validate security configuration"""
        if self.secret_key == "your-secret-key-here-change-in-production":
            import warnings
            warnings.warn("⚠️  Using default secret key - change for production!", UserWarning)

@dataclass 
class Config:
    """
    Main Odin configuration class
    Combines all configuration sections
    """
    
    # Environment
    environment: str = "development"  # development, production, testing
    debug: bool = False
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Odin Bitcoin Trading Bot"
    api_version: str = "2.0.0"
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    data: DataConfig = field(default_factory=DataConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # Application paths
    data_directory: str = "data"
    logs_directory: str = "data/logs"
    models_directory: str = "data/models"
    
    def __post_init__(self):
        """Post-initialization setup and validation"""
        # Create required directories
        self._create_directories()
        
        # Validate configuration
        self._validate_config()
        
        # Apply environment-specific overrides
        self._apply_environment_overrides()
    
    def _create_directories(self):
        """Create required directories"""
        directories = [
            self.data_directory,
            self.logs_directory,
            self.models_directory,
            f"{self.data_directory}/backups",
            f"{self.data_directory}/exports"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _validate_config(self):
        """Validate overall configuration"""
        assert self.environment in ["development", "production", "testing"], \
            "Environment must be development, production, or testing"
        assert 1000 <= self.api_port <= 65535, "API port must be between 1000 and 65535"
        assert self.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], \
            "Log level must be valid Python logging level"
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides"""
        if self.environment == "production":
            # Production overrides
            self.debug = False
            self.security.docs_enabled = False  # Disable docs in production
            self.security.cors_origins = []  # Restrict CORS in production
            self.database.echo_sql = False
            self.log_level = "WARNING"
            
        elif self.environment == "testing":
            # Testing overrides
            self.database.database_url = "sqlite:///data/test_bitcoin_data.db"
            self.trading.enable_live_trading = False
            self.data.data_update_interval = 5  # Faster updates for testing
            self.ai.regime_update_frequency = 5
            
        elif self.environment == "development":
            # Development overrides
            self.debug = True
            self.database.echo_sql = True
            self.log_level = "DEBUG"

def get_config() -> Config:
    """
    Get configuration from environment variables and defaults
    
    Returns:
        Configured Config instance
    """
    config = Config()
    
    # Environment detection
    config.environment = os.getenv("ODIN_ENV", config.environment)
    config.debug = os.getenv("ODIN_DEBUG", "false").lower() == "true"
    
    # API settings
    config.api_host = os.getenv("ODIN_HOST", config.api_host)
    config.api_port = int(os.getenv("ODIN_PORT", config.api_port))
    
    # Database settings
    config.database.database_url = os.getenv("DATABASE_URL", config.database.database_url)
    
    # Trading settings
    config.trading.enable_live_trading = os.getenv("ENABLE_LIVE_TRADING", "false").lower() == "true"
    config.trading.max_position_size = float(os.getenv("MAX_POSITION_SIZE", config.trading.max_position_size))
    config.trading.risk_per_trade = float(os.getenv("RISK_PER_TRADE", config.trading.risk_per_trade))
    
    # Security settings
    config.security.secret_key = os.getenv("ODIN_SECRET_KEY", config.security.secret_key)
    config.security.jwt_secret_key = os.getenv("JWT_SECRET_KEY", config.security.jwt_secret_key)
    config.security.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", config.security.access_token_expire_minutes))
    
    # AI-specific environment variables
    config.ai.regime_update_frequency = int(os.getenv("AI_REGIME_UPDATE_FREQ", config.ai.regime_update_frequency))
    config.ai.min_regime_confidence = float(os.getenv("AI_MIN_REGIME_CONFIDENCE", config.ai.min_regime_confidence))
    config.ai.adaptive_strategy_enabled = os.getenv("AI_ADAPTIVE_STRATEGIES", "true").lower() == "true"
    config.ai.auto_retrain_enabled = os.getenv("AI_AUTO_RETRAIN", "true").lower() == "true"
    config.ai.performance_monitoring_enabled = os.getenv("AI_PERFORMANCE_MONITORING", "true").lower() == "true"
    
    # Data collection settings
    config.data.data_update_interval = int(os.getenv("DATA_UPDATE_INTERVAL", config.data.data_update_interval))
    config.data.primary_data_source = os.getenv("PRIMARY_DATA_SOURCE", config.data.primary_data_source)
    
    # Logging settings
    config.log_level = os.getenv("LOG_LEVEL", config.log_level)
    
    # Exchange API settings (for live trading)
    exchange_api_key = os.getenv("EXCHANGE_API_KEY")
    exchange_secret_key = os.getenv("EXCHANGE_SECRET_KEY")
    exchange_sandbox = os.getenv("EXCHANGE_SANDBOX", "true").lower() == "true"
    
    if exchange_api_key and exchange_secret_key:
        # Store exchange credentials securely
        config.trading.exchange_credentials = {
            "api_key": exchange_api_key,
            "secret_key": exchange_secret_key,
            "sandbox": exchange_sandbox
        }
    
    return config

def load_config_from_file(file_path: str = "config/config.yaml") -> Optional[Config]:
    """
    Load configuration from YAML file
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        Config instance or None if file doesn't exist
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        import yaml
        
        with open(file_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Create config instance from loaded data
        # This would need custom deserialization logic
        # For now, return None to use environment-based config
        return None
        
    except ImportError:
        print("⚠️  PyYAML not installed, using environment configuration")
        return None
    except Exception as e:
        print(f"⚠️  Failed to load config file: {e}")
        return None

def save_config_template(file_path: str = "config/config.example.yaml"):
    """
    Save configuration template file
    
    Args:
        file_path: Path where to save the template
    """
    try:
        import yaml
        
        # Create example configuration
        example_config = {
            "environment": "development",
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": True
            },
            "database": {
                "url": "sqlite:///data/bitcoin_data.db"
            },
            "trading": {
                "enable_live_trading": False,
                "max_position_size": 0.95,
                "risk_per_trade": 0.02
            },
            "ai": {
                "regime_update_frequency": 20,
                "min_regime_confidence": 0.6,
                "adaptive_strategy_enabled": True,
                "auto_retrain_enabled": True
            },
            "data": {
                "sources": ["coinbase", "coingecko", "binance"],
                "update_interval": 30
            },
            "security": {
                "secret_key": "CHANGE_THIS_IN_PRODUCTION",
                "jwt_secret_key": "CHANGE_THIS_IN_PRODUCTION",
                "access_token_expire_minutes": 30
            }
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write template
        with open(file_path, 'w') as f:
            yaml.dump(example_config, f, default_flow_style=False, indent=2)
        
        print(f"✓ Configuration template saved to {file_path}")
        
    except ImportError:
        print("⚠️  PyYAML not installed, cannot save config template")
    except Exception as e:
        print(f"❌ Failed to save config template: {e}")

# Configuration validation helpers
def validate_production_config(config: Config) -> List[str]:
    """
    Validate configuration for production deployment
    
    Args:
        config: Configuration instance to validate
        
    Returns:
        List of validation warnings/errors
    """
    issues = []
    
    # Security checks
    if config.security.secret_key == "your-secret-key-here-change-in-production":
        issues.append("🔴 CRITICAL: Default secret key detected - change before production!")
    
    if config.security.jwt_secret_key == "your-jwt-secret-here-change-in-production":
        issues.append("🔴 CRITICAL: Default JWT secret detected - change before production!")
    
    if config.environment == "production":
        if config.debug:
            issues.append("🟡 WARNING: Debug mode enabled in production")
        
        if config.security.docs_enabled:
            issues.append("🟡 WARNING: API documentation enabled in production")
        
        if "*" in config.security.cors_origins:
            issues.append("🟡 WARNING: CORS allows all origins in production")
        
        if config.database.echo_sql:
            issues.append("🟡 WARNING: SQL echo enabled in production")
    
    # Trading checks
    if config.trading.enable_live_trading:
        if not hasattr(config.trading, 'exchange_credentials'):
            issues.append("🔴 CRITICAL: Live trading enabled but no exchange credentials configured")
        
        if config.trading.max_position_size > 0.95:
            issues.append("🟡 WARNING: Very high max position size (>95%)")
        
        if config.trading.risk_per_trade > 0.05:
            issues.append("🟡 WARNING: High risk per trade (>5%)")
    
    # AI checks
    if config.ai.min_regime_confidence < 0.5:
        issues.append("🟡 WARNING: Low minimum regime confidence (<50%)")
    
    # Database checks
    if config.database.database_url.startswith('sqlite:') and config.environment == "production":
        issues.append("🟡 WARNING: Using SQLite in production - consider PostgreSQL")
    
    return issues

def print_config_summary(config: Config):
    """Print a summary of the current configuration"""
    
    print("🔧 Odin Configuration Summary")
    print("=" * 50)
    print(f"Environment: {config.environment}")
    print(f"Debug Mode: {config.debug}")
    print(f"API: {config.api_host}:{config.api_port}")
    print(f"Database: {config.database.database_url}")
    print()
    
    print("💰 Trading Configuration:")
    print(f"  Live Trading: {config.trading.enable_live_trading}")
    print(f"  Max Position Size: {config.trading.max_position_size * 100:.1f}%")
    print(f"  Risk Per Trade: {config.trading.risk_per_trade * 100:.1f}%")
    print()
    
    print("🤖 AI Configuration:")
    print(f"  Adaptive Strategies: {config.ai.adaptive_strategy_enabled}")
    print(f"  Regime Update Freq: {config.ai.regime_update_frequency}")
    print(f"  Min Confidence: {config.ai.min_regime_confidence * 100:.1f}%")
    print(f"  Auto Retrain: {config.ai.auto_retrain_enabled}")
    print()
    
    print("📊 Data Configuration:")
    print(f"  Primary Source: {config.data.primary_data_source}")
    print(f"  Update Interval: {config.data.data_update_interval}s")
    print(f"  Sources: {', '.join(config.data.data_sources)}")
    print()
    
    # Validation check
    if config.environment == "production":
        issues = validate_production_config(config)
        if issues:
            print("⚠️  Production Validation Issues:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("✅ Production configuration validation passed")

if __name__ == "__main__":
    # Configuration testing and utilities
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validate":
            config = get_config()
            issues = validate_production_config(config)
            
            if issues:
                print("Configuration issues found:")
                for issue in issues:
                    print(f"  {issue}")
                sys.exit(1)
            else:
                print("✅ Configuration validation passed")
                
        elif command == "template":
            save_config_template()
            
        elif command == "summary":
            config = get_config()
            print_config_summary(config)
            
        else:
            print("Usage: python config.py [validate|template|summary]")
    else:
        # Default: show configuration summary
        config = get_config()
        print_config_summary(config)