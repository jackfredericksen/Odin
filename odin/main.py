import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict

import structlog
import uvicorn
from fastapi import FastAPI

from odin.api.app import create_app
from odin.config import get_settings
from odin.core.data_collector import DataCollector
from odin.core.database import init_database
from odin.utils.logging import setup_logging

logger = structlog.get_logger(__name__)


class OdinBot:
    """Main Odin trading bot application."""
    
    def __init__(self) -> None:
        """Initialize the Odin bot."""
        self.settings = get_settings()
        self.data_collector: DataCollector | None = None
        self.app: FastAPI | None = None
        self._shutdown_event = asyncio.Event()
        
    async def startup(self) -> None:
        """Start the trading bot."""
        logger.info("Starting Odin trading bot", version="2.0.0")
        
        # Initialize database
        await init_database()
        logger.info("Database initialized")
        
        # Initialize data collector
        self.data_collector = DataCollector()
        await self.data_collector.startup()
        logger.info("Data collector started")
        
        # Start background data collection
        asyncio.create_task(self._background_data_collection())
        logger.info("Background data collection started")
        
    async def shutdown(self) -> None:
        """Shutdown the trading bot."""
        logger.info("Shutting down Odin trading bot")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Stop data collector
        if self.data_collector:
            await self.data_collector.shutdown()
            logger.info("Data collector stopped")
        
        logger.info("Odin trading bot shutdown complete")
        
    async def _background_data_collection(self) -> None:
        """Run background data collection."""
        while not self._shutdown_event.is_set():
            try:
                if self.data_collector:
                    await self.data_collector.collect_data()
                    logger.debug("Data collection completed")
                
                # Wait for next collection interval
                await asyncio.sleep(self.settings.data_update_interval)
                
            except asyncio.CancelledError:
                logger.info("Data collection task cancelled")
                break
            except Exception as e:
                logger.error("Error in background data collection", error=str(e))
                await asyncio.sleep(30)  # Wait before retry
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum: int, frame: Any) -> None:
            logger.info("Received shutdown signal", signal=signum)
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    bot = OdinBot()
    
    # Startup
    await bot.startup()
    
    # Store bot instance in app state
    app.state.bot = bot
    
    yield
    
    # Shutdown
    await bot.shutdown()


async def main() -> None:
    """Main application entry point."""
    # Setup logging
    setup_logging()
    
    settings = get_settings()
    logger.info("Starting Odin trading bot server", 
                host=settings.api_host, 
                port=settings.api_port)
    
    # Create FastAPI app
    app = create_app(lifespan=lifespan)
    
    # Setup signal handlers
    bot = OdinBot()
    bot.setup_signal_handlers()
    
    # Run server
    config = uvicorn.Config(
        app=app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=1,  # Single worker for simplicity with background tasks
        log_config=None,  # Use our custom logging
        access_log=False,  # Disable uvicorn access log
    )
    
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error("Server error", error=str(e))
        sys.exit(1)


def cli_main() -> None:
    """CLI entry point."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted")
    except Exception as e:
        logger.error("Application error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    cli_main()