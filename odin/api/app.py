# odin/api/app.py
"""
FastAPI application setup and configuration - Production Ready
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from odin.config import settings
from odin.api.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    AuthenticationMiddleware,
    SecurityHeadersMiddleware,
    HealthCheckMiddleware
)
from odin.api.routes import (
    data,
    health,
    strategies_router,
    trading_router,
    portfolio_router,
    market_router
)
from odin.core.exceptions import (
    DataCollectionError,
    StrategyError,
    ValidationError,
    TradingError,
    RiskManagementError
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application for production
    """
    app = FastAPI(
        title="Odin Bitcoin Trading Bot API",
        description="Professional Bitcoin trading bot with live trading capabilities",
        version="1.0.0",
        docs_url="/docs" if settings.ODIN_ENV != "production" else None,
        redoc_url="/redoc" if settings.ODIN_ENV != "production" else None,
        openapi_url="/openapi.json" if settings.ODIN_ENV != "production" else None,
        contact={
            "name": "Odin Trading Bot",
            "url": "https://github.com/yourusername/odin-bitcoin-bot",
            "email": "support@odin-bot.com"
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    )

    # Setup middleware
    setup_middleware(app)
    
    # Setup routes
    setup_routes(app)
    
    # Setup static files and templates
    setup_static_files(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Setup startup and shutdown events
    setup_events(app)
    
    logger.info("Odin Bitcoin Trading Bot API initialized")
    return app


def setup_middleware(app: FastAPI) -> None:
    """Setup middleware stack in correct order"""
    
    # CORS middleware (first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time", "X-RateLimit-Remaining"]
    )
    
    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Custom middleware (order matters - last added is executed first)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(HealthCheckMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(LoggingMiddleware)


def setup_routes(app: FastAPI) -> None:
    """Setup API routes with proper organization"""
    
    # Health check (always available)
    app.include_router(
        health.router,
        prefix="/api/v1/health",
        tags=["Health & Monitoring"]
    )
    
    # Data endpoints
    app.include_router(
        data.router,
        prefix="/api/v1/data",
        tags=["Bitcoin Data"]
    )
    
    # Strategy management endpoints
    app.include_router(
        strategies_router,
        prefix="/api/v1/strategies",
        tags=["Strategy Management"]
    )
    
    # Live trading endpoints
    app.include_router(
        trading_router,
        prefix="/api/v1/trading",
        tags=["Live Trading"]
    )
    
    # Portfolio management endpoints
    app.include_router(
        portfolio_router,
        prefix="/api/v1/portfolio",
        tags=["Portfolio Management"]
    )
    
    # Market data endpoints
    app.include_router(
        market_router,
        prefix="/api/v1/market",
        tags=["Market Data & Analysis"]
    )


def setup_static_files(app: FastAPI) -> None:
    """Setup static files and templates"""
    
    # Static files
    static_dir = project_root / "web" / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Static files mounted from {static_dir}")
    
    # Templates
    templates_dir = project_root / "web" / "templates"
    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))
        
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def dashboard(request: Request):
            """Serve main trading dashboard"""
            return templates.TemplateResponse(
                "dashboard.html", 
                {
                    "request": request,
                    "title": "Odin Bitcoin Trading Dashboard",
                    "api_base_url": f"http://{settings.ODIN_HOST}:{settings.ODIN_PORT}",
                    "environment": settings.ODIN_ENV
                }
            )
        
        logger.info(f"Templates configured from {templates_dir}")


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup custom exception handlers for better error responses"""
    
    @app.exception_handler(DataCollectionError)
    async def data_collection_exception_handler(request: Request, exc: DataCollectionError):
        logger.error(f"Data collection error: {exc}")
        return JSONResponse(
            status_code=503,
            content={
                "error": "Data Collection Failed",
                "message": str(exc),
                "type": "data_collection_error",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            }
        )
    
    @app.exception_handler(StrategyError)
    async def strategy_exception_handler(request: Request, exc: StrategyError):
        logger.error(f"Strategy error: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "Strategy Analysis Failed",
                "message": str(exc),
                "type": "strategy_error",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            }
        )
    
    @app.exception_handler(TradingError)
    async def trading_exception_handler(request: Request, exc: TradingError):
        logger.error(f"Trading error: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "Trading Operation Failed",
                "message": str(exc),
                "type": "trading_error",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            }
        )
    
    @app.exception_handler(RiskManagementError)
    async def risk_management_exception_handler(request: Request, exc: RiskManagementError):
        logger.error(f"Risk management error: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "Risk Management Violation",
                "message": str(exc),
                "type": "risk_management_error",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            }
        )
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        logger.warning(f"Validation error: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Failed",
                "message": str(exc),
                "type": "validation_error",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Request validation error: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Request Validation Failed",
                "message": "Invalid request data",
                "details": exc.errors(),
                "type": "request_validation_error",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"HTTP {exc.status_code}",
                "message": exc.detail,
                "type": "http_error",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unexpected error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred" if settings.ODIN_ENV == "production" else str(exc),
                "type": "internal_server_error",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            }
        )


def setup_events(app: FastAPI) -> None:
    """Setup startup and shutdown events"""
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup"""
        logger.info("🚀 Odin Bitcoin Trading Bot starting up...")
        logger.info(f"Environment: {settings.ODIN_ENV}")
        logger.info(f"Host: {settings.ODIN_HOST}:{settings.ODIN_PORT}")
        
        # Initialize database
        try:
            from odin.core.database import DatabaseManager
            db_manager = DatabaseManager()
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
        
        # Initialize data collector
        try:
            from odin.core.data_collector import BitcoinDataCollector
            data_collector = BitcoinDataCollector()
            # Start background data collection
            if settings.ODIN_ENV != "test":
                data_collector.start_continuous_collection()
            logger.info("✅ Data collection service started")
        except Exception as e:
            logger.error(f"❌ Data collection service failed: {e}")
        
        # Initialize trading engine (if live trading enabled)
        if getattr(settings, 'ENABLE_LIVE_TRADING', False):
            try:
                from odin.core.trading_engine import TradingEngine
                trading_engine = TradingEngine()
                logger.info("✅ Trading engine initialized")
            except Exception as e:
                logger.error(f"❌ Trading engine initialization failed: {e}")
        
        logger.info("🎯 Odin Bitcoin Trading Bot ready for action!")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        logger.info("🛑 Odin Bitcoin Trading Bot shutting down...")
        
        # Stop data collection
        try:
            from odin.core.data_collector import BitcoinDataCollector
            data_collector = BitcoinDataCollector()
            data_collector.stop_continuous_collection()
            logger.info("✅ Data collection stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping data collection: {e}")
        
        # Emergency stop all trading
        if getattr(settings, 'ENABLE_LIVE_TRADING', False):
            try:
                from odin.core.trading_engine import TradingEngine
                trading_engine = TradingEngine()
                await trading_engine.emergency_stop_all()
                logger.info("✅ All trading activities stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping trading: {e}")
        
        logger.info("👋 Odin Bitcoin Trading Bot shutdown complete")


def get_cors_origins() -> list:
    """Get CORS origins based on environment"""
    if settings.ODIN_ENV == "development":
        return [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            f"http://localhost:{settings.ODIN_PORT}",
            f"http://127.0.0.1:{settings.ODIN_PORT}"
        ]
    elif settings.ODIN_ENV == "production":
        return [
            "https://yourdomain.com",
            "https://api.yourdomain.com",
            "https://app.yourdomain.com"
        ]
    else:
        return ["*"]  # Test environment


# Create application instance
app = create_app()


# Root endpoint for API information
@app.get("/api", include_in_schema=False)
async def api_info():
    """API information endpoint"""
    return {
        "name": "Odin Bitcoin Trading Bot API",
        "version": "1.0.0",
        "description": "Professional Bitcoin trading bot with live trading capabilities",
        "environment": settings.ODIN_ENV,
        "endpoints": {
            "docs": "/docs" if settings.ODIN_ENV != "production" else "disabled",
            "redoc": "/redoc" if settings.ODIN_ENV != "production" else "disabled",
            "health": "/api/v1/health",
            "data": "/api/v1/data",
            "strategies": "/api/v1/strategies", 
            "trading": "/api/v1/trading",
            "portfolio": "/api/v1/portfolio",
            "market": "/api/v1/market"
        },
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    # Development server
    uvicorn.run(
        "odin.api.app:app",
        host=settings.ODIN_HOST,
        port=settings.ODIN_PORT,
        reload=settings.ODIN_ENV == "development",
        log_level="info",
        access_log=True,
        use_colors=True
    )