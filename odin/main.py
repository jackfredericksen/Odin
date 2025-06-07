#!/usr/bin/env python3
"""
Odin Bitcoin Trading Bot - Main Entry Point (WINDOWS COMPATIBLE)
"""

import sys
import os
import uvicorn
import logging
import asyncio
from pathlib import Path
from datetime import datetime
import importlib.util

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging with Windows-compatible format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

def create_directories():
    """Create necessary directories for the application."""
    directories = [
        'data',
        'data/logs',
        'data/backups',
        'data/backups/daily'
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")

def check_python_version():
    """Check if Python version is compatible."""
    min_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < min_version:
        logger.error(f"Python {min_version[0]}.{min_version[1]}+ required. Current: {current_version[0]}.{current_version[1]}")
        return False
    
    logger.info(f"Python version check passed: {current_version[0]}.{current_version[1]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic'),
        ('aiohttp', 'aiohttp'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy')
    ]
    
    missing_packages = []
    
    for package, display_name in required_packages:
        try:
            importlib.import_module(package)
            logger.debug(f"{display_name} installed")
        except ImportError:
            missing_packages.append(display_name)
            logger.error(f"{display_name} not installed")
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.error("Install with: pip install -r requirements.txt")
        return False
    
    logger.info("All required dependencies are installed")
    return True

def check_configuration():
    """Check application configuration."""
    try:
        from odin.config import get_settings
        settings = get_settings()
        
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"Host: {settings.host}:{settings.port}")
        logger.info(f"Exchange: {settings.exchange_name} (sandbox: {settings.exchange_sandbox})")
        logger.info(f"Live trading: {'enabled' if settings.enable_live_trading else 'disabled'}")
        
        # Check environment file
        env_file = Path('.env')
        if env_file.exists():
            logger.info("Environment file (.env) found")
        else:
            logger.warning("No .env file found - using defaults")
        
        return True
        
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return False

def initialize_database():
    """Initialize and check database connection."""
    try:
        from odin.core.database import get_database, init_sample_data
        
        logger.info("Initializing database...")
        db = get_database()
        
        # Get database statistics
        stats = db.get_database_stats()
        
        if stats.get('bitcoin_prices_count', 0) == 0:
            logger.info("No price data found, initializing with sample data...")
            success = init_sample_data(db)
            if success:
                stats = db.get_database_stats()
                logger.info("Sample data initialized successfully")
            else:
                logger.warning("Failed to initialize sample data")
        
        logger.info(f"Database statistics:")
        logger.info(f"   - Bitcoin prices: {stats.get('bitcoin_prices_count', 0)} records")
        logger.info(f"   - Strategies: {stats.get('strategies_count', 0)} configured")
        logger.info(f"   - Active strategies: {stats.get('active_strategies', 0)}")
        logger.info(f"   - Total trades: {stats.get('trades_today', 0)} today")
        logger.info(f"   - Database size: {stats.get('database_size_mb', 0):.2f} MB")
        
        if stats.get('price_data_range'):
            logger.info(f"   - Data range: {stats['price_data_range'].get('start')} to {stats['price_data_range'].get('end')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.error("Check database configuration and permissions")
        return False

def check_data_collector():
    """Check data collection system."""
    try:
        from odin.core.data_collector import DataCollector
        from odin.core.database import get_database
        
        logger.info("Checking data collection system...")
        
        db = get_database()
        collector = DataCollector(database=db)
        
        # Check data sources
        source_status = collector.get_source_status()
        healthy_sources = sum(1 for status in source_status.values() if status['healthy'])
        
        logger.info(f"Data sources: {healthy_sources}/{len(source_status)} healthy")
        
        for name, status in source_status.items():
            status_text = "OK" if status['healthy'] else "ERROR"
            logger.info(f"   {name}: {status_text} (priority {status['priority']}, errors: {status['error_count']})")
        
        if healthy_sources == 0:
            logger.warning("No healthy data sources available - using mock data")
        
        return True
        
    except Exception as e:
        logger.error(f"Data collector check failed: {e}")
        return False

def check_strategies():
    """Check trading strategies."""
    try:
        from odin.strategies.moving_average import MovingAverageStrategy
        from odin.strategies.rsi import RSIStrategy
        from odin.strategies.bollinger_bands import BollingerBandsStrategy
        from odin.strategies.macd import MACDStrategy
        
        strategies = [
            ("Moving Average", MovingAverageStrategy),
            ("RSI", RSIStrategy),
            ("Bollinger Bands", BollingerBandsStrategy),
            ("MACD", MACDStrategy)
        ]
        
        logger.info("Checking trading strategies...")
        
        loaded_strategies = 0
        for name, strategy_class in strategies:
            try:
                strategy = strategy_class()
                logger.info(f"   {name}: OK")
                loaded_strategies += 1
            except Exception as e:
                logger.error(f"   {name}: ERROR - {e}")
        
        logger.info(f"{loaded_strategies}/{len(strategies)} strategies loaded successfully")
        return loaded_strategies > 0
        
    except Exception as e:
        logger.error(f"Strategy check failed: {e}")
        return False

def check_api_routes():
    """Check API routes availability."""
    try:
        from odin.api.app import create_app
        
        logger.info("Checking API system...")
        
        # Try to create the app
        app = create_app()
        
        # Count routes
        route_count = len(app.routes)
        logger.info(f"FastAPI app created with {route_count} routes")
        
        # Check key endpoints exist
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        
        key_endpoints = [
            "/api/v1/health",
            "/api/v1/data/current",
            "/api/v1/portfolio",
            "/api/v1/strategies/list"
        ]
        
        for endpoint in key_endpoints:
            if endpoint in route_paths:
                logger.info(f"   {endpoint}: OK")
            else:
                logger.warning(f"   {endpoint}: NOT FOUND")
        
        return True
        
    except Exception as e:
        logger.error(f"API check failed: {e}")
        return False

async def startup_health_check():
    """Perform comprehensive startup health check."""
    logger.info("Performing startup health checks...")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration", check_configuration),
        ("Database", initialize_database),
        ("Data Collector", check_data_collector),
        ("Trading Strategies", check_strategies),
        ("API Routes", check_api_routes)
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check_name, check_function in checks:
        logger.info(f"Running {check_name} check...")
        try:
            if check_function():
                passed_checks += 1
            else:
                logger.warning(f"{check_name} check failed")
        except Exception as e:
            logger.error(f"{check_name} check error: {e}")
    
    logger.info(f"Health checks completed: {passed_checks}/{total_checks} passed")
    
    if passed_checks < total_checks:
        logger.warning("Some health checks failed - application may not work correctly")
        if passed_checks < total_checks // 2:
            logger.error("Too many critical checks failed - stopping startup")
            return False
    
    return True

def display_startup_banner():
    """Display startup banner with system information."""
    banner = """
    ================================================================
    
       ODIN BITCOIN TRADING BOT - v2.0.0
       Professional Trading Automation System
       
    ================================================================
    """
    print(banner)
    
    # System information
    logger.info("Starting Odin Bitcoin Trading Bot")
    logger.info(f"Startup time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python: {sys.version.split()[0]}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Project root: {project_root}")

def display_access_information():
    """Display access information for the user."""
    logger.info("")
    logger.info("Application is now running!")
    logger.info("================================================================")
    logger.info("Dashboard:          http://localhost:8000")
    logger.info("API Documentation:  http://localhost:8000/docs")
    logger.info("Alternative Docs:   http://localhost:8000/redoc")
    logger.info("Health Check:       http://localhost:8000/api/v1/health")
    logger.info("Bitcoin Data:       http://localhost:8000/api/v1/data/current")
    logger.info("Portfolio:          http://localhost:8000/api/v1/portfolio")
    logger.info("Strategies:         http://localhost:8000/api/v1/strategies/list")
    logger.info("================================================================")
    logger.info("")
    logger.info("Press Ctrl+C to stop the application")

async def main():
    """Main application entry point with comprehensive startup sequence."""
    try:
        # Create necessary directories
        create_directories()
        
        # Display startup banner
        display_startup_banner()
        
        # Run comprehensive health checks
        if not await startup_health_check():
            logger.error("Critical startup checks failed - exiting")
            sys.exit(1)
        
        # Import and create FastAPI app after all checks pass
        from odin.api.app import create_app
        app = create_app()
        
        # Display access information
        display_access_information()
        
        # Start data collection if available
        try:
            from odin.core.data_collector import DataCollector
            from odin.core.database import get_database
            
            db = get_database()
            collector = DataCollector(database=db)
            
            # Start data collection in background
            asyncio.create_task(collector.start_collection())
            logger.info("Data collection started in background")
            
        except Exception as e:
            logger.warning(f"Could not start data collection: {e}")
        
        # Configure uvicorn
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload to prevent import issues
            log_level="info",
            access_log=True
        )
        
        # Start the server
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        logger.info("Cleaning up...")
        
        # Cleanup operations
        try:
            # Stop data collection
            if 'collector' in locals():
                await collector.stop_collection()
                logger.info("Data collection stopped")
        except:
            pass
        
        logger.info("Cleanup completed")
        logger.info("Odin Trading Bot stopped successfully")
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Troubleshooting steps:")
        logger.error("   1. Install dependencies: pip install -r requirements.txt")
        logger.error("   2. Check Pydantic version: pip install pydantic==2.5.0 pydantic-settings==2.1.0")
        logger.error("   3. Verify file structure and imports")
        logger.error("   4. Check Python path and working directory")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error during startup: {e}")
        logger.error("Check the logs above for specific error details")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        sys.exit(1)

def sync_main():
    """Synchronous wrapper for async main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Already handled in main()
    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sync_main()