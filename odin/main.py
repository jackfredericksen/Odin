#!/usr/bin/env python3
"""
Odin Bitcoin Trading Bot - Final Working Main Entry Point
"""

import sys
import uvicorn
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point."""
    try:
        # Import the fixed app directly
        from api.app import create_app
        
        # Create FastAPI app
        app = create_app()
        
        # Log startup
        logger.info("🚀 Starting Odin Bitcoin Trading Bot")
        logger.info("📊 Dashboard: http://localhost:8000")
        logger.info("📖 API Docs: http://localhost:8000/docs")
        logger.info("💚 Health: http://localhost:8000/api/v1/health")
        logger.info("₿ Bitcoin Data: http://localhost:8000/api/v1/data/current")
        
        # Initialize database
        try:
            from odin.core.database import get_database
            db = get_database()
            stats = db.get_database_stats()
            logger.info(f"📊 Database initialized: {stats.get('bitcoin_prices_count', 0)} price records")
        except Exception as e:
            logger.warning(f"Database initialization warning: {e}")
        
        # Run the application
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload to prevent import issues
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Please check:")
        logger.error("1. All dependencies are installed: pip install -r requirements.txt")
        logger.error("2. Pydantic v2 is properly installed: pip install pydantic==2.5.0 pydantic-settings==2.1.0")
        logger.error("3. Files are in correct locations")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()