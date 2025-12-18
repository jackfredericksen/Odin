#!/usr/bin/env python3
"""
Odin Bitcoin Analysis Dashboard - Enhanced Main Entry Point
Integrates new configuration, logging, error handling, and repository systems.
"""

import asyncio
import importlib.util
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import enhanced systems
from odin.core.config_manager import OdinConfig, get_config, get_config_manager
from odin.core.exceptions import (
    ErrorCode,
    ErrorHandler,
    ErrorSeverity,
    OdinException,
    SystemException,
)
from odin.core.repository import RepositoryManager, get_repository_manager
from odin.core.shutdown import ShutdownManager, get_shutdown_manager
from odin.utils.console import ConsoleFormatter, get_console_formatter
from odin.utils.logging import (
    LogContext,
    configure_logging,
    get_logger,
    set_correlation_id,
)

# Initialize systems
logger = get_logger(__name__)
error_handler = ErrorHandler()
console = get_console_formatter()


class OdinApplication:
    """Main application class with lifecycle management."""

    def __init__(self):
        self.config: Optional[OdinConfig] = None
        self.repo_manager: Optional[RepositoryManager] = None
        self.shutdown_manager: Optional[ShutdownManager] = None
        self.app = None
        self.server = None
        self.background_tasks = []
        self.startup_correlation_id = set_correlation_id()

    async def startup(self) -> bool:
        """Complete application startup sequence."""
        try:
            logger.info(
                "Starting Odin Bitcoin Analysis Dashboard",
                LogContext(component="application", operation="startup"),
            )

            # Phase 0: Initialize shutdown manager and free port
            if not await self._initialize_shutdown_manager():
                return False

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

            logger.info(
                "Odin application started successfully",
                LogContext(component="application", operation="startup_complete"),
            )

            self._display_access_information()
            return True

        except Exception as e:
            await error_handler.handle_exception(
                e,
                LogContext(component="application", operation="startup"),
                suppress_if_handled=False,
            )
            return False

    async def shutdown(self):
        """Graceful application shutdown."""
        try:
            logger.info(
                "Shutting down Odin application",
                LogContext(component="application", operation="shutdown"),
            )

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

    async def _initialize_shutdown_manager(self) -> bool:
        """Initialize shutdown manager and ensure port is free."""
        try:
            logger.info(
                "Initializing shutdown manager",
                LogContext(component="application", operation="init_shutdown_manager"),
            )

            # Get shutdown manager instance (defaults to port 8000)
            self.shutdown_manager = get_shutdown_manager(port=8000)

            # Install signal handlers for graceful shutdown
            self.shutdown_manager.install_signal_handlers()

            # Ensure port is free before starting
            if not self.shutdown_manager.ensure_port_free():
                logger.error("Failed to free port 8000 - cannot start application")
                return False

            logger.info("Shutdown manager initialized and port 8000 is available")
            return True

        except Exception as e:
            logger.error(f"Shutdown manager initialization failed: {e}")
            return False

    async def _load_configuration(self) -> bool:
        """Load and validate configuration."""
        try:
            logger.info(
                "Loading configuration",
                LogContext(component="application", operation="load_config"),
            )

            config_manager = get_config_manager()
            self.config = config_manager.load_config()

            if self.config is None:
                logger.error("Configuration manager returned None")
                return False

            logger.info(
                "Configuration loaded successfully",
                LogContext(
                    component="application",
                    operation="load_config",
                    additional_data={
                        "environment": self.config.environment.value,
                        "debug": self.config.debug,
                        "live_trading": self.config.trading.enable_live_trading,
                    },
                ),
            )

            return True

        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def _setup_logging(self) -> bool:
        """Setup enhanced logging system."""
        try:
            if not self.config:
                raise SystemException(
                    "Configuration not loaded",
                    ErrorCode.SYSTEM_CONFIG_INVALID,
                    ErrorSeverity.CRITICAL,
                )

            # Configure logging based on config
            configure_logging(
                level=self.config.logging.level,
                enable_console=self.config.logging.enable_console,
                enable_file=self.config.logging.enable_file,
                file_path=self.config.logging.file_path,
                max_file_size=self.config.logging.max_file_size,
                backup_count=self.config.logging.backup_count,
                structured_format=True,
            )

            logger.info(
                "Logging system configured",
                LogContext(
                    component="application",
                    operation="setup_logging",
                    additional_data={
                        "level": self.config.logging.level.value,
                        "file_logging": self.config.logging.enable_file,
                        "file_path": self.config.logging.file_path,
                    },
                ),
            )

            return True

        except Exception as e:
            # Use basic logging since structured logging might not be set up
            print(f"ERROR: Logging setup failed: {e}")
            return False

    async def _initialize_core_systems(self) -> bool:
        """Initialize core systems (database, repositories)."""
        try:
            logger.info(
                "Initializing core systems",
                LogContext(component="application", operation="init_core_systems"),
            )

            # Create necessary directories
            logger.info("Creating directories...")
            self._create_directories()

            # Initialize repository manager
            logger.info("Initializing repository manager...")
            self.repo_manager = await get_repository_manager()
            logger.info("Repository manager initialized")

            # Get database statistics
            logger.info("Getting database statistics...")
            db_stats = await self.repo_manager.get_stats()
            logger.info(
                "Database initialized",
                LogContext(
                    component="application",
                    operation="init_database",
                    additional_data=db_stats,
                ),
            )

            return True

        except Exception as e:
            logger.error(f"Core systems initialization failed: {e}")
            import traceback

            traceback.print_exc()
            await error_handler.handle_exception(
                e, LogContext(component="application", operation="init_core_systems")
            )
            return False

    async def _run_health_checks(self) -> bool:
        """Run comprehensive health checks."""
        try:
            logger.info(
                "Running health checks",
                LogContext(component="application", operation="health_checks"),
            )

            checks = [
                ("Python Version", self._check_python_version),
                ("Dependencies", self._check_dependencies),
                ("Database", self._check_database),
                ("Data Sources", self._check_data_sources),
                ("Trading Strategies", self._check_strategies),
                ("Exchange Configuration", self._check_exchange_config),
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
            logger.info(
                f"Health checks completed: {passed_checks}/{total_checks} passed",
                LogContext(
                    component="application",
                    operation="health_checks_complete",
                    additional_data={"success_rate": success_rate},
                ),
            )

            # Require at least 70% of checks to pass
            if success_rate < 0.7:
                logger.error("Too many health checks failed - stopping startup")
                return False

            return True

        except Exception as e:
            await error_handler.handle_exception(
                e, LogContext(component="application", operation="health_checks")
            )
            return False

    async def _initialize_services(self) -> bool:
        """Initialize application services."""
        try:
            logger.info(
                "Initializing services",
                LogContext(component="application", operation="init_services"),
            )

            # Import and create FastAPI app
            from odin.api.app import create_app

            self.app = create_app()

            logger.info(f"FastAPI app created with {len(self.app.routes)} routes")

            return True

        except Exception as e:
            await error_handler.handle_exception(
                e, LogContext(component="application", operation="init_services")
            )
            return False

    async def _start_background_tasks(self) -> bool:
        """Start background tasks."""
        try:
            logger.info(
                "Starting background tasks",
                LogContext(component="application", operation="start_background_tasks"),
            )

            # Start data collection if configured
            if self.config.data.collection_interval > 0:
                task = asyncio.create_task(self._data_collection_task())
                self.background_tasks.append(task)
                logger.info("Data collection task started")

            # Start error statistics cleanup
            task = asyncio.create_task(self._cleanup_task())
            self.background_tasks.append(task)

            logger.info(f"Started {len(self.background_tasks)} background tasks")
            return True

        except Exception as e:
            await error_handler.handle_exception(
                e,
                LogContext(component="application", operation="start_background_tasks"),
            )
            return False

    async def run_server(self):
        """Run the FastAPI server."""
        try:
            if not self.app:
                raise SystemException(
                    "Application not initialized",
                    ErrorCode.SYSTEM_STARTUP_FAILED,
                    ErrorSeverity.CRITICAL,
                )

            # Configure uvicorn server
            config = uvicorn.Config(
                self.app,
                host=self.config.api.host,
                port=self.config.api.port,
                reload=self.config.api.reload,
                log_level="info",
                access_log=True,
            )

            self.server = uvicorn.Server(config)
            await self.server.serve()

        except Exception as e:
            await error_handler.handle_exception(
                e, LogContext(component="application", operation="run_server")
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
            "fastapi",
            "uvicorn",
            "pydantic",
            "httpx",
            "pandas",
            "numpy",
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

            # Try a simple query using the price_repo attribute
            result = await self.repo_manager.price_repo.get_latest_price()
            return True  # If no exception, database is working

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

            healthy_sources = sum(
                1 for status in source_status.values() if status["healthy"]
            )
            return healthy_sources > 0

        except Exception as e:
            logger.warning(f"Data sources check failed: {e}")
            return True  # Non-critical for startup

    async def _check_strategies(self) -> bool:
        """Check trading strategies."""
        try:
            strategy_modules = [
                "odin.strategies.moving_average",
                "odin.strategies.rsi",
                "odin.strategies.bollinger_bands",
                "odin.strategies.macd",
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
            if (
                self.config.trading.enable_live_trading
                and not self.config.exchange.sandbox
            ):
                # Live trading requires API credentials
                if not all(
                    [self.config.exchange.api_key, self.config.exchange.secret_key]
                ):
                    logger.error(
                        "Live trading enabled but missing exchange credentials"
                    )
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
                e, LogContext(component="background_task", operation="data_collection")
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
                    await price_repo.cleanup_old_data(
                        self.config.data.cleanup_old_data_days
                    )

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")

    # Utility methods
    def _create_directories(self):
        """Create necessary directories."""
        directories = ["data", "data/logs", "data/backups", "data/backups/daily"]

        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {directory}")

    def _display_startup_banner(self):
        """Display startup banner."""
        print("\n")
        print(console.separator("=", 70))
        print(console.header("   ODIN BITCOIN ANALYSIS DASHBOARD - v3.1.0".center(70)))
        print(console.info("   Multi-Coin Trading Platform".center(70)))
        print(console.separator("=", 70))
        print("")

        # Display configuration info
        print(
            console.status_line(
                "Startup Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        print(
            console.status_line(
                "Environment", self.config.environment.value.upper(), "info"
            )
        )
        print(
            console.status_line(
                "Debug Mode",
                "ON" if self.config.debug else "OFF",
                "warning" if self.config.debug else "info",
            )
        )
        print(
            console.status_line(
                "Live Trading",
                "ENABLED" if self.config.trading.enable_live_trading else "DISABLED",
                "warning" if self.config.trading.enable_live_trading else "success",
            )
        )
        print("")

    def _display_access_information(self):
        """Display access information."""
        host = self.config.api.host
        port = self.config.api.port

        # Use localhost for display if binding to all interfaces
        display_host = "localhost" if host == "0.0.0.0" else host

        print(console.success("Application is now running!"))
        print("")
        print(console.separator("=", 70))
        print(console.header("   ACCESS POINTS"))
        print(console.separator("=", 70))
        print(f"  {console.info('Dashboard:')}          http://{display_host}:{port}")
        print(
            f"  {console.info('API Docs:')}           http://{display_host}:{port}/docs"
        )
        print(
            f"  {console.info('Alternative Docs:')}   http://{display_host}:{port}/redoc"
        )
        print(
            f"  {console.info('Health Check:')}       http://{display_host}:{port}/api/v1/health"
        )
        print(
            f"  {console.info('Market Data:')}        http://{display_host}:{port}/api/v1/data/current"
        )
        print(
            f"  {console.info('Strategies:')}         http://{display_host}:{port}/api/v1/strategies/list"
        )
        print(console.separator("=", 70))
        print("")
        print(console.dim("Press Ctrl+C to stop the application"))
        print("")


async def main():
    """Main application entry point."""
    app = OdinApplication()

    try:
        # Print clean starting message
        print("\n")
        print(console.separator("=", 70))
        print(console.header("   ODIN BITCOIN ANALYSIS DASHBOARD"))
        print(console.info("   Initializing system..."))
        print(console.separator("=", 70))
        print("")

        # Complete startup sequence
        if not await app.startup():
            print("")
            print(console.error("Application startup failed"))
            print("")
            sys.exit(1)

        # Display full banner after successful startup
        app._display_startup_banner()

        # Run the server
        await app.run_server()

    except KeyboardInterrupt:
        print("\n")
        print(console.warning("Shutdown signal received"))
        print(console.info("Stopping application gracefully..."))
        print("")
        await app.shutdown()
        print(console.success("Shutdown complete"))
        print("")

    except Exception as e:
        print("\n")
        print(console.error(f"Critical application error: {e}"))
        print("")
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
