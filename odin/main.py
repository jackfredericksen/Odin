#!/usr/bin/env python3
"""
Odin Bitcoin Trading Bot - Enhanced Main Entry Point
Integrates new configuration, logging, error handling, and repository systems.
"""

import sys
import os
import uvicorn
import asyncio
from pathlib import Path
from datetime import datetime
import importlib.util
from typing import Dict, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import enhanced systems
from odin.core.config_manager import get_config, get_config_manager, OdinConfig
from odin.utils.logging import configure_logging, get_logger, set_correlation_id, LogContext
from odin.core.exceptions import ErrorHandler, OdinException, ErrorCode, ErrorSeverity, SystemException
from odin.core.repository import get_repository_manager, RepositoryManager

# Initialize systems
logger = get_logger(__name__)
error_handler = ErrorHandler()


class OdinApplication:
    """Main application class with lifecycle management."""
    
    def __init__(self):
        self.config: Optional[OdinConfig] = None
        self.repo_manager: Optional[RepositoryManager] = None
        self.app = None
        self.server = None
        self.background_tasks = []
        self.startup_correlation_id = set_correlation_id()
    
    async def startup(self) -> bool:
        """Complete application startup sequence."""
        try:
            logger.info("Starting Odin Bitcoin Trading Bot", LogContext(
                component="application",
                operation="startup"
            ))
            
            # Phase 1: Load configuration
            if not await self._load_configuration():
                return False
            
            # Phase 2: Setup logging
            if not await self._setup_logging():
                return False
            
            # Phase 3: Initialize core systems
            if not await self._initialize_core_systems():
                return False
            
            # Phase 4: Run health checks
            if not await self._run_health_checks():
                return False
            
            # Phase 5: Initialize application services
            if not await self._initialize_services():
                return False
            
            # Phase 6: Start background tasks
            if not await self._start_background_tasks():
                return False
            
            logger.info("Odin application started successfully", LogContext(
                component="application",
                operation="startup_complete"
            ))
            
            self._display_access_information()
            return True
            
        except Exception as e:
            await error_handler.handle_exception(
                e,
                LogContext(component="application", operation="startup"),
                suppress_if_handled=False
            )
            return False
    
    async def shutdown(self):
        """Graceful application shutdown."""
        try:
            logger.info("Shutting down Odin application", LogContext(
                component="application",
                operation="shutdown"
            ))
            
            # Stop background tasks
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Close repositories
            if self.repo_manager:
                await self.repo_manager.close()
            
            # Stop server
            if self.server:
                self.server.should_exit = True
            
            logger.info("Odin application shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _load_configuration(self) -> bool:
        """Load and validate configuration."""
        try:
            logger.info("Loading configuration", LogContext(
                component="application",
                operation="load_config"
            ))
            
            config_manager = get_config_manager()
            self.config = config_manager.load_config()
            
            logger.info("Configuration loaded successfully", LogContext(
                component="application",
                operation="load_config",
                additional_data={
                    "environment": self.config.environment.value,
                    "debug": self.config.debug,
                    "live_trading": self.config.trading.enable_live_trading
                }
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            return False
    
    async def _setup_logging(self) -> bool:
        """Setup enhanced logging system."""
        try:
            if not self.config:
                raise SystemException(
                    "Configuration not loaded",
                    ErrorCode.SYSTEM_CONFIG_INVALID,
                    ErrorSeverity.CRITICAL
                )
            
            # Configure logging based on config
            configure_logging(
                level=self.config.logging.level,
                enable_console=self.config.logging.enable_console,
                enable_file=self.config.logging.enable_file,
                file_path=self.config.logging.file_path,
                max_file_size=self.config.logging.max_file_size,
                backup_count=self.config.logging.backup_count,
                structured_format=True
            )
            
            logger.info("Logging system configured", LogContext(
                component="application",
                operation="setup_logging",
                additional_data={
                    "level": self.config.logging.level.value,
                    "file_logging": self.config.logging.enable_file,
                    "file_path": self.config.logging.file_path
                }
            ))
            
            return True
            
        except Exception as e:
            # Use basic logging since structured logging might not be set up
            print(f"ERROR: Logging setup failed: {e}")
            return False
    
    async def _initialize_core_systems(self) -> bool:
        """Initialize core systems (database, repositories)."""
        try:
            logger.info("Initializing core systems", LogContext(
                component="application",
                operation="init_core_systems"
            ))
            
            # Create necessary directories
            self._create_directories()
            
            # Initialize repository manager
            self.repo_manager = await get_repository_manager()
            
            # Get database statistics
            db_stats = await self.repo_manager.get_database_stats()
            logger.info("Database initialized", LogContext(
                component="application",
                operation="init_database",
                additional_data=db_stats
            ))
            
            return True
            
        except Exception as e:
            await error_handler.handle_exception(
                e,
                LogContext(component="application", operation="init_core_systems")
            )
            return False
    
    async def _run_health_checks(self) -> bool:
        """Run comprehensive health checks."""
        try:
            logger.info("Running health checks", LogContext(
                component="application",
                operation="health_checks"
            ))
            
            checks = [
                ("Python Version", self._check_python_version),
                ("Dependencies", self._check_dependencies),
                ("Database", self._check_database),
                ("Data Sources", self._check_data_sources),
                ("Trading Strategies", self._check_strategies),
                ("Exchange Configuration", self._check_exchange_config)
            ]
            
            passed_checks = 0
            total_checks = len(checks)
            
            for check_name, check_function in checks:
                try:
                    if await check_function():
                        passed_checks += 1
                        logger.info(f"Health check passed: {check_name}")
                    else:
                        logger.warning(f"Health check failed: {check_name}")
                except Exception as e:
                    logger.error(f"Health check error ({check_name}): {e}")
            
            success_rate = passed_checks / total_checks
            logger.info(f"Health checks completed: {passed_checks}/{total_checks} passed", LogContext(
                component="application",
                operation="health_checks_complete",
                additional_data={"success_rate": success_rate}
            ))
            
            # Require at least 70% of checks to pass
            if success_rate < 0.7:
                logger.error("Too many health checks failed - stopping startup")
                return False
            
            return True
            
        except Exception as e:
            await error_handler.handle_exception(
                e,
                LogContext(component="application", operation="health_checks")
            )
            return False
    
    async def _initialize_services(self) -> bool:
        """Initialize application services."""
        try:
            logger.info("Initializing services", LogContext(
                component="application",
                operation="init_services"
            ))
            
            # Import and create FastAPI app
            from odin.api.app import create_app
            self.app = create_app()
            
            logger.info(f"FastAPI app created with {len(self.app.routes)} routes")
            
            return True
            
        except Exception as e:
            await error_handler.handle_exception(
                e,
                LogContext(component="application", operation="init_services")
            )
            return False
    
    async def _start_background_tasks(self) -> bool:
        """Start background tasks."""
        try:
            logger.info("Starting background tasks", LogContext(
                component="application",
                operation="start_background_tasks"
            ))
            
            # Start data collection if configured
            if self.config.data.collection_interval > 0:
                task = asyncio.create_task(self._data_collection_task())
                self.background_tasks.append(task)
                logger.info("Data collection task started")
            
            # Start portfolio tracking if enabled
            if self.config.trading.auto_rebalance:
                task = asyncio.create_task(self._portfolio_tracking_task())
                self.background_tasks.append(task)
                logger.info("Portfolio tracking task started")
            
            # Start error statistics cleanup
            task = asyncio.create_task(self._cleanup_task())
            self.background_tasks.append(task)
            
            logger.info(f"Started {len(self.background_tasks)} background tasks")
            return True
            
        except Exception as e:
            await error_handler.handle_exception(
                e,
                LogContext(component="application", operation="start_background_tasks")
            )
            return False
    
    async def run_server(self):
        """Run the FastAPI server."""
        try:
            if not self.app:
                raise SystemException(
                    "Application not initialized",
                    ErrorCode.SYSTEM_STARTUP_FAILED,
                    ErrorSeverity.CRITICAL
                )
            
            # Configure uvicorn server
            config = uvicorn.Config(
                self.app,
                host=self.config.api.host,
                port=self.config.api.port,
                reload=self.config.api.reload,
                log_level="info",
                access_log=True
            )
            
            self.server = uvicorn.Server(config)
            await self.server.serve()
            
        except Exception as e:
            await error_handler.handle_exception(
                e,
                LogContext(component="application", operation="run_server")
            )
    
    # Health check methods
    async def _check_python_version(self) -> bool:
        """Check Python version compatibility."""
        min_version = (3, 8)
        current_version = sys.version_info[:2]
        return current_version >= min_version
    
    async def _check_dependencies(self) -> bool:
        """Check required dependencies."""
        required_packages = [
            'fastapi', 'uvicorn', 'pydantic', 'aiohttp', 'pandas', 'numpy'
        ]
        
        for package in required_packages:
            try:
                importlib.import_module(package)
            except ImportError:
                logger.error(f"Missing dependency: {package}")
                return False
        
        return True
    
    async def _check_database(self) -> bool:
        """Check database connectivity."""
        try:
            if not self.repo_manager:
                return False
            
            # Try a simple query
            price_repo = self.repo_manager.get_price_repository()
            result = await price_repo.find_latest(limit=1)
            return result.success
            
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return False
    
    async def _check_data_sources(self) -> bool:
        """Check data source availability."""
        try:
            # Import and test data collector
            from odin.core.data_collector import DataCollector
            
            collector = DataCollector(database=None)  # Mock database for test
            source_status = collector.get_source_status()
            
            healthy_sources = sum(1 for status in source_status.values() if status['healthy'])
            return healthy_sources > 0
            
        except Exception as e:
            logger.warning(f"Data sources check failed: {e}")
            return True  # Non-critical for startup
    
    async def _check_strategies(self) -> bool:
        """Check trading strategies."""
        try:
            strategy_modules = [
                'odin.strategies.moving_average',
                'odin.strategies.rsi',
                'odin.strategies.bollinger_bands',
                'odin.strategies.macd'
            ]
            
            loaded_count = 0
            for module_name in strategy_modules:
                try:
                    importlib.import_module(module_name)
                    loaded_count += 1
                except ImportError as e:
                    logger.warning(f"Strategy module not found: {module_name}")
            
            return loaded_count > 0
            
        except Exception as e:
            logger.error(f"Strategy check failed: {e}")
            return False
    
    async def _check_exchange_config(self) -> bool:
        """Check exchange configuration."""
        try:
            if self.config.trading.enable_live_trading and not self.config.exchange.sandbox:
                # Live trading requires API credentials
                if not all([self.config.exchange.api_key, self.config.exchange.secret_key]):
                    logger.error("Live trading enabled but missing exchange credentials")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Exchange config check failed: {e}")
            return False
    
    # Background task methods
    async def _data_collection_task(self):
        """Background data collection task."""
        try:
            from odin.core.data_collector import DataCollector
            
            collector = DataCollector(database=self.repo_manager.db_manager)
            await collector.start_collection()
            
        except Exception as e:
            await error_handler.handle_exception(
                e,
                LogContext(component="background_task", operation="data_collection")
            )
    
    async def _portfolio_tracking_task(self):
        """Background portfolio tracking task."""
        try:
            # This would start portfolio tracking
            logger.info("Portfolio tracking task placeholder")
            
            while True:
                await asyncio.sleep(300)  # 5 minutes
                # Add portfolio tracking logic here
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            await error_handler.handle_exception(
                e,
                LogContext(component="background_task", operation="portfolio_tracking")
            )
    
    async def _cleanup_task(self):
        """Background cleanup task."""
        try:
            while True:
                await asyncio.sleep(3600)  # 1 hour
                
                # Clean up old error records
                error_handler.clear_error_records(older_than_hours=24)
                
                # Clean up old price data if configured
                if self.config.data.cleanup_old_data_days > 0:
                    price_repo = self.repo_manager.get_price_repository()
                    await price_repo.cleanup_old_data(self.config.data.cleanup_old_data_days)
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
    
    # Utility methods
    def _create_directories(self):
        """Create necessary directories."""
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
                logger.debug(f"Created directory: {directory}")
    
    def _display_startup_banner(self):
        """Display startup banner."""
        banner = """
        ================================================================
        
           ODIN BITCOIN TRADING BOT - v2.0.0
           Professional Trading Automation System
           
        ================================================================
        """
        print(banner)
        
        logger.info("Starting Odin Bitcoin Trading Bot")
        logger.info(f"Startup time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Environment: {self.config.environment.value}")
        logger.info(f"Debug mode: {self.config.debug}")
        logger.info(f"Live trading: {'enabled' if self.config.trading.enable_live_trading else 'disabled'}")
    
    def _display_access_information(self):
        """Display access information."""
        host = self.config.api.host
        port = self.config.api.port
        
        # Use localhost for display if binding to all interfaces
        display_host = "localhost" if host == "0.0.0.0" else host
        
        logger.info("")
        logger.info("Application is now running!")
        logger.info("================================================================")
        logger.info(f"Dashboard:          http://{display_host}:{port}")
        logger.info(f"API Documentation:  http://{display_host}:{port}/docs")
        logger.info(f"Alternative Docs:   http://{display_host}:{port}/redoc")
        logger.info(f"Health Check:       http://{display_host}:{port}/api/v1/health")
        logger.info(f"Bitcoin Data:       http://{display_host}:{port}/api/v1/data/current")
        logger.info(f"Portfolio:          http://{display_host}:{port}/api/v1/portfolio")
        logger.info(f"Strategies:         http://{display_host}:{port}/api/v1/strategies/list")
        logger.info("================================================================")
        logger.info("")
        logger.info("Press Ctrl+C to stop the application")


async def main():
    """Main application entry point."""
    app = OdinApplication()
    
    try:
        # Display startup banner
        app._display_startup_banner()
        
        # Complete startup sequence
        if not await app.startup():
            logger.error("Application startup failed")
            sys.exit(1)
        
        # Run the server
        await app.run_server()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        await app.shutdown()
        
    except Exception as e:
        logger.critical(f"Critical application error: {e}")
        await app.shutdown()
        sys.exit(1)


def sync_main():
    """Synchronous wrapper for async main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Already handled in main()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    sync_main()