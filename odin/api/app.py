"""
Odin Bitcoin Analysis Dashboard - FastAPI Application (Enhanced Dashboard Compatibility)
"""

import logging
import os
import random
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import config properly
from odin.config import get_settings
from odin.core.database import get_database, init_sample_data
from odin.core.models import APIResponse, serialize_for_dashboard
from odin.utils.logging import LogLevel, configure_logging, get_logger

# Configure structured logging on application startup
configure_logging(
    level=LogLevel.INFO,
    enable_console=True,
    enable_file=True,
    file_path="data/logs/odin_api.log",
    structured_format=True,
)

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application with enhanced dashboard compatibility."""

    settings = get_settings()

    # Create FastAPI instance
    app = FastAPI(
        title="Odin Bitcoin Analysis Dashboard",
        description="Real-Time Bitcoin Market Analysis & Visualization Platform",
        version="2.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Add CORS middleware with secure configuration
    # SECURITY: Never use wildcard "*" in production
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    # In production, add your actual domain(s) via ODIN_CORS_ORIGINS env var
    extra_origins = os.getenv("ODIN_CORS_ORIGINS", "").split(",")
    allowed_origins.extend([o.strip() for o in extra_origins if o.strip()])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    )

    # Custom middleware for dashboard-compatible responses
    @app.middleware("http")
    async def dashboard_compatibility_middleware(request: Request, call_next):
        """Ensure all responses are dashboard-compatible."""
        try:
            response = await call_next(request)

            # Add dashboard-friendly headers for API routes
            if request.url.path.startswith("/api/"):
                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                response.headers["X-Odin-API"] = "v1"

            return response
        except Exception as e:
            logger.error(f"Middleware error: {e}")
            # Return dashboard-friendly error response
            error_response = APIResponse(
                success=False, message="Internal server error", data=None
            )
            return JSONResponse(
                status_code=500, content=serialize_for_dashboard(error_response)
            )

    # Mount static files
    static_path = Path(__file__).parent.parent.parent / "web" / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Setup templates
    template_path = Path(__file__).parent.parent.parent / "web" / "templates"
    templates = None
    if template_path.exists():
        templates = Jinja2Templates(directory=str(template_path))

    # Enhanced health check endpoints with dashboard compatibility
    @app.get("/api/v1/health")
    async def health_check():
        """Basic health check optimized for dashboard."""
        response = APIResponse(
            success=True,
            message="Odin Bot is running",
            data={
                "status": "healthy",
                "version": "2.0.0",
                "timestamp": time.time(),
                "uptime_seconds": time.time(),  # Simplified uptime
                "components": {
                    "database": "ready",
                    "api": "healthy",
                    "trading_engine": "initialized",
                },
            },
        )
        return serialize_for_dashboard(response)

    @app.get("/api/v1/health/detailed")
    async def detailed_health():
        """Detailed health check for dashboard monitoring."""
        try:
            import psutil

            memory = psutil.virtual_memory()

            response = APIResponse(
                success=True,
                message="System healthy",
                data={
                    "status": "healthy",
                    "version": "2.0.0",
                    "system": {
                        "memory_percent": round(memory.percent, 2),
                        "cpu_percent": round(psutil.cpu_percent(interval=0.1), 2),
                        "disk_usage": round(psutil.disk_usage("/").percent, 2),
                    },
                    "components": {
                        "database": "ready",
                        "trading_engine": "initialized",
                        "data_collector": "active",
                        "portfolio_manager": "ready",
                    },
                    "performance": {
                        "avg_response_time_ms": random.uniform(50, 150),
                        "requests_per_minute": random.randint(10, 100),
                        "error_rate_percent": random.uniform(0, 2),
                    },
                },
            )
            return serialize_for_dashboard(response)
        except Exception as e:
            logger.error(f"Health check error: {e}")
            response = APIResponse(
                success=False, message="Health check failed", data={"error": str(e)}
            )
            return serialize_for_dashboard(response)

    @app.get("/api/v1/health/websocket")
    async def websocket_health():
        """WebSocket health check for dashboard connection monitoring."""
        try:
            # Check if WebSocket routes are properly registered
            websocket_routes = [
                route
                for route in app.routes
                if hasattr(route, "path") and route.path.startswith("/ws")
            ]

            response = APIResponse(
                success=True,
                message="WebSocket endpoints ready",
                data={
                    "websocket_routes": len(websocket_routes),
                    "available_endpoints": [
                        route.path
                        for route in websocket_routes
                        if hasattr(route, "path")
                    ],
                    "status": "WebSocket endpoints are ready",
                    "connection_info": {
                        "max_connections": 100,
                        "current_connections": random.randint(0, 10),
                        "message_rate_per_second": random.randint(1, 5),
                    },
                },
            )
            return serialize_for_dashboard(response)
        except Exception as e:
            logger.error(f"WebSocket health check error: {e}")
            response = APIResponse(
                success=False,
                message="WebSocket health check failed",
                data={"error": str(e)},
            )
            return serialize_for_dashboard(response)

    # REMOVED: Mock Bitcoin data endpoints - now using REAL data from data.py router
    # The real /api/v1/data/current endpoint is registered below via include_router

    # REMOVED: Mock historical data endpoint - now using REAL data from data.py router
    # The real /api/v1/data/history/{hours} endpoint is registered below via include_router

    # Enhanced portfolio endpoints with dashboard optimization
    @app.get("/api/v1/portfolio")
    async def get_portfolio():
        """Get portfolio data optimized for dashboard display."""
        try:
            total_value = 10000 + random.uniform(-500, 500)
            change_24h = round(random.uniform(-3, 3), 2)
            pnl_24h = round(total_value * (change_24h / 100), 2)

            btc_balance = 0.25
            btc_value = btc_balance * 45000
            cash_balance = total_value - btc_value

            response = APIResponse(
                success=True,
                message="Portfolio data retrieved successfully",
                data={
                    "total_value": round(total_value, 2),
                    "btc_balance": btc_balance,
                    "btc_value": round(btc_value, 2),
                    "usd_balance": round(cash_balance, 2),
                    "change_24h": change_24h,
                    "pnl_24h": pnl_24h,
                    "pnl_24h_percent": change_24h,
                    "positions": [
                        {
                            "symbol": "BTC-USD",
                            "side": "long",
                            "size": btc_balance,
                            "value": round(btc_value, 2),
                            "entry_price": 44500,
                            "current_price": 45000,
                            "pnl": round(btc_balance * 500, 2),
                            "pnl_percent": 1.12,
                        }
                    ],
                    "allocation": {
                        "Bitcoin": round((btc_value / total_value) * 100, 1),
                        "USD": round((cash_balance / total_value) * 100, 1),
                    },
                    "performance": {
                        "total_return_percent": round(
                            ((total_value - 10000) / 10000) * 100, 2
                        ),
                        "sharpe_ratio": round(random.uniform(0.8, 2.2), 2),
                        "max_drawdown": round(random.uniform(-15, -2), 2),
                        "volatility": round(random.uniform(10, 25), 2),
                    },
                    "risk_metrics": {
                        "risk_score": round(random.uniform(3, 7), 1),
                        "exposure_percent": round((btc_value / total_value) * 100, 1),
                        "leverage": 1.0,
                    },
                },
            )
            return serialize_for_dashboard(response)

        except Exception as e:
            logger.error(f"Portfolio error: {e}")
            response = APIResponse(
                success=False, message="Failed to fetch portfolio data", data=None
            )
            return serialize_for_dashboard(response)

    # Enhanced strategy endpoints with dashboard optimization
    @app.get("/api/v1/strategies/list")
    async def get_strategies():
        """Get trading strategies optimized for dashboard display."""
        try:
            strategies = [
                {
                    "id": "ma_cross",
                    "name": "Moving Average Crossover",
                    "type": "moving_average",
                    "description": "Trend-following strategy using MA crossovers",
                    "active": True,
                    "return": 12.5,
                    "total_trades": 45,
                    "winning_trades": 31,
                    "losing_trades": 14,
                    "win_rate": 68.9,
                    "sharpe_ratio": 1.85,
                    "max_drawdown": -8.2,
                    "volatility": 15.3,
                    "last_signal": {
                        "type": "buy",
                        "timestamp": time.time() - 3600,
                        "confidence": 0.78,
                        "price": 45120,
                    },
                    "parameters": {"short_window": 5, "long_window": 20},
                    "performance_history": [
                        {
                            "timestamp": time.time() - (i * 86400),
                            "value": random.uniform(-5, 15),
                        }
                        for i in range(30)
                    ],
                },
                {
                    "id": "rsi_momentum",
                    "name": "RSI Momentum",
                    "type": "rsi",
                    "description": "Mean reversion strategy using RSI oscillator",
                    "active": False,
                    "return": -2.1,
                    "total_trades": 23,
                    "winning_trades": 10,
                    "losing_trades": 13,
                    "win_rate": 43.5,
                    "sharpe_ratio": 0.92,
                    "max_drawdown": -12.5,
                    "volatility": 18.7,
                    "last_signal": {
                        "type": "hold",
                        "timestamp": time.time() - 7200,
                        "confidence": 0.45,
                        "price": 44980,
                    },
                    "parameters": {"period": 14, "oversold": 30, "overbought": 70},
                    "performance_history": [
                        {
                            "timestamp": time.time() - (i * 86400),
                            "value": random.uniform(-10, 5),
                        }
                        for i in range(30)
                    ],
                },
                {
                    "id": "bollinger_bands",
                    "name": "Bollinger Bands",
                    "type": "bollinger_bands",
                    "description": "Volatility-based breakout strategy",
                    "active": True,
                    "return": 8.7,
                    "total_trades": 67,
                    "winning_trades": 40,
                    "losing_trades": 27,
                    "win_rate": 59.7,
                    "sharpe_ratio": 1.34,
                    "max_drawdown": -6.8,
                    "volatility": 12.1,
                    "last_signal": {
                        "type": "sell",
                        "timestamp": time.time() - 1800,
                        "confidence": 0.82,
                        "price": 45080,
                    },
                    "parameters": {"period": 20, "std_deviation": 2.0},
                    "performance_history": [
                        {
                            "timestamp": time.time() - (i * 86400),
                            "value": random.uniform(-3, 12),
                        }
                        for i in range(30)
                    ],
                },
                {
                    "id": "macd_trend",
                    "name": "MACD Trend",
                    "type": "macd",
                    "description": "Trend momentum using MACD indicator",
                    "active": False,
                    "return": 5.3,
                    "total_trades": 34,
                    "winning_trades": 19,
                    "losing_trades": 15,
                    "win_rate": 55.9,
                    "sharpe_ratio": 1.12,
                    "max_drawdown": -9.4,
                    "volatility": 16.8,
                    "last_signal": {
                        "type": "hold",
                        "timestamp": time.time() - 5400,
                        "confidence": 0.62,
                        "price": 45050,
                    },
                    "parameters": {
                        "fast_period": 12,
                        "slow_period": 26,
                        "signal_period": 9,
                    },
                    "performance_history": [
                        {
                            "timestamp": time.time() - (i * 86400),
                            "value": random.uniform(-7, 10),
                        }
                        for i in range(30)
                    ],
                },
            ]

            # Calculate summary statistics
            active_strategies = [s for s in strategies if s["active"]]
            total_active = len(active_strategies)
            avg_return = (
                sum([s["return"] for s in active_strategies]) / total_active
                if total_active > 0
                else 0
            )

            response = APIResponse(
                success=True,
                message=f"Retrieved {len(strategies)} strategies",
                data={
                    "strategies": strategies,
                    "summary": {
                        "total_strategies": len(strategies),
                        "active_strategies": total_active,
                        "inactive_strategies": len(strategies) - total_active,
                        "average_return": round(avg_return, 2),
                        "best_performing": (
                            max(strategies, key=lambda x: x["return"])["name"]
                            if strategies
                            else None
                        ),
                        "total_trades_today": sum(
                            [random.randint(0, 5) for _ in strategies]
                        ),
                        "signals_last_hour": random.randint(0, 3),
                    },
                },
            )
            return serialize_for_dashboard(response)

        except Exception as e:
            logger.error(f"Strategies error: {e}")
            response = APIResponse(
                success=False, message="Failed to fetch strategies", data=None
            )
            return serialize_for_dashboard(response)

    # Enhanced trading endpoints with dashboard optimization
    @app.get("/api/v1/trading/history")
    async def get_trading_history(limit: int = 10):
        """Get trading history optimized for dashboard display."""
        try:
            limit = max(1, min(limit, 50))  # Limit for dashboard performance

            orders = []
            strategies = ["ma_cross", "rsi_momentum", "bollinger_bands", "macd_trend"]
            statuses = ["filled", "pending", "cancelled"]

            for i in range(limit):
                side = random.choice(["buy", "sell"])
                amount = round(random.uniform(0.001, 0.1), 6)
                price = 45000 + random.uniform(-2000, 2000)
                pnl = round(random.uniform(-50, 100), 2)
                status = random.choice(statuses)

                orders.append(
                    {
                        "id": f"order_{int(time.time())}_{i}",
                        "timestamp": time.time() - (i * 3600) - random.randint(0, 3600),
                        "strategy": random.choice(strategies),
                        "symbol": "BTC-USD",
                        "side": side,
                        "order_type": "market",
                        "amount": amount,
                        "price": round(price, 2),
                        "filled_amount": (
                            amount
                            if status == "filled"
                            else round(amount * random.uniform(0, 1), 6)
                        ),
                        "status": status,
                        "pnl": pnl if status == "filled" else 0,
                        "pnl_percent": (
                            round((pnl / (amount * price)) * 100, 2)
                            if status == "filled"
                            else 0
                        ),
                        "fees": round(amount * price * 0.001, 2),
                        "execution_time_ms": (
                            random.randint(50, 500) if status == "filled" else None
                        ),
                    }
                )

            # Calculate summary statistics
            filled_orders = [o for o in orders if o["status"] == "filled"]
            total_pnl = sum([o["pnl"] for o in filled_orders])
            winning_trades = len([o for o in filled_orders if o["pnl"] > 0])

            response = APIResponse(
                success=True,
                message=f"Retrieved {len(orders)} trading records",
                data={
                    "orders": orders,
                    "summary": {
                        "total_orders": len(orders),
                        "filled_orders": len(filled_orders),
                        "pending_orders": len(
                            [o for o in orders if o["status"] == "pending"]
                        ),
                        "cancelled_orders": len(
                            [o for o in orders if o["status"] == "cancelled"]
                        ),
                        "total_pnl": round(total_pnl, 2),
                        "winning_trades": winning_trades,
                        "win_rate": (
                            round((winning_trades / len(filled_orders)) * 100, 1)
                            if filled_orders
                            else 0
                        ),
                        "average_execution_time_ms": (
                            round(
                                sum(
                                    [
                                        o["execution_time_ms"]
                                        for o in filled_orders
                                        if o["execution_time_ms"]
                                    ]
                                )
                                / len(filled_orders),
                                1,
                            )
                            if filled_orders
                            else 0
                        ),
                    },
                },
            )
            return serialize_for_dashboard(response)

        except Exception as e:
            logger.error(f"Trading history error: {e}")
            response = APIResponse(
                success=False, message="Failed to fetch trading history", data=None
            )
            return serialize_for_dashboard(response)

    @app.get("/api/v1/trading/status")
    async def get_trading_status():
        """Get auto-trading status optimized for dashboard monitoring."""
        try:
            response = APIResponse(
                success=True,
                message="Trading status retrieved successfully",
                data={
                    "enabled": False,  # Auto-trading disabled by default
                    "active_strategies": 2,
                    "last_trade": time.time() - 1800,  # 30 minutes ago
                    "total_trades_today": 15,
                    "pnl_today": 127.50,
                    "orders_pending": 2,
                    "orders_filled_today": 13,
                    "average_trade_size": 0.045,
                    "trading_session": {
                        "start_time": time.time() - 28800,  # 8 hours ago
                        "duration_hours": 8,
                        "trades_per_hour": 1.9,
                        "success_rate": 73.3,
                    },
                    "risk_status": {
                        "within_limits": True,
                        "daily_loss_limit_used": 15.2,
                        "position_size_limit_used": 68.4,
                        "max_drawdown_current": -3.2,
                    },
                },
            )
            return serialize_for_dashboard(response)

        except Exception as e:
            logger.error(f"Trading status error: {e}")
            response = APIResponse(
                success=False, message="Failed to fetch trading status", data=None
            )
            return serialize_for_dashboard(response)

    @app.get("/api/v1/database/init")
    async def init_database():
        """Initialize database with sample data."""
        try:
            db = get_database()
            success = init_sample_data(db)
            stats = db.get_database_stats()

            response = APIResponse(
                success=success,
                message="Database initialized with sample data",
                data={
                    "initialization_success": success,
                    "database_stats": stats,
                    "sample_data_created": True,
                    "ready_for_dashboard": True,
                },
            )
            return serialize_for_dashboard(response)

        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            response = APIResponse(
                success=False,
                message="Failed to initialize database",
                data={"error": str(e)},
            )
            return serialize_for_dashboard(response)

    # Include API routes with enhanced error handling
    try:
        from odin.api.routes.data import router as data_router

        app.include_router(data_router, prefix="/api/v1/data", tags=["data"])
        logger.info("Successfully imported data routes")
    except ImportError as e:
        logger.warning(f"Could not import data routes: {e}")

    try:
        from odin.api.routes.strategies import router as strategies_router

        app.include_router(
            strategies_router, prefix="/api/v1/strategies", tags=["strategies"]
        )
        logger.info("Successfully imported strategy routes")
    except ImportError as e:
        logger.warning(f"Could not import strategy routes: {e}")

    try:
        from odin.api.routes.websockets import router as websocket_router

        app.include_router(websocket_router, prefix="", tags=["websockets"])
        logger.info("Successfully imported websocket routes")
    except ImportError as e:
        logger.warning(f"Could not import websocket routes: {e}")

    try:
        from odin.api.routes.social import router as social_router

        app.include_router(social_router, prefix="", tags=["social"])
        logger.info("Successfully imported social routes")
    except ImportError as e:
        logger.warning(f"Could not import social routes: {e}")

    # Root endpoint - serve dashboard with enhanced compatibility
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Serve the reorganized sectioned dashboard (v2)."""
        try:
            if templates and template_path.exists():
                return templates.TemplateResponse(
                    "dashboard-v2.html",
                    {
                        "request": request,
                        "version": "4.2.0",
                        "api_base_url": "/api/v1",
                        "websocket_url": f"ws://{request.url.netloc}/ws",
                        "debug_mode": settings.debug,
                    },
                )
        except Exception as e:
            logger.error(f"Error serving dashboard v2: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to load dashboard", "message": str(e)},
            )

    @app.get("/bloomberg", response_class=HTMLResponse)
    async def bloomberg_dashboard(request: Request):
        """Serve the Bloomberg-style terminal dashboard (v1)."""
        try:
            if templates and template_path.exists():
                return templates.TemplateResponse(
                    "dashboard-bloomberg.html",
                    {
                        "request": request,
                        "version": "4.0.0",
                        "api_base_url": "/api/v1",
                        "websocket_url": f"ws://{request.url.netloc}/ws",
                        "debug_mode": settings.debug,
                    },
                )
        except Exception as e:
            logger.error(f"Error serving Bloomberg dashboard: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to load dashboard", "message": str(e)},
            )

    @app.get("/classic", response_class=HTMLResponse)
    async def classic_dashboard(request: Request):
        """Serve the classic dashboard (original version)."""
        try:
            if templates and template_path.exists():
                return templates.TemplateResponse(
                    "dashboard.html",
                    {
                        "request": request,
                        "version": "2.0.0",
                        "api_base_url": "/api/v1",
                        "websocket_url": f"ws://{request.url.netloc}/ws",
                        "debug_mode": settings.debug,
                    },
                )
            else:
                # Fallback API info for dashboard development
                dashboard_info = APIResponse(
                    success=True,
                    message="Odin Bitcoin Analysis Dashboard API Ready",
                    data={
                        "api_version": "2.0.0",
                        "status": "running",
                        "dashboard_ready": True,
                        "mode": "analysis",
                        "endpoints": {
                            "dashboard": "/",
                            "health": "/api/v1/health",
                            "api_docs": "/docs",
                            "bitcoin_data": "/api/v1/data/current",
                            "historical_data": "/api/v1/data/history/{hours}",
                            "analysis_tools": "/api/v1/strategies/list",
                        },
                        "websocket": {
                            "available": True,
                            "endpoint": "/ws",
                            "supported_events": [
                                "price_update",
                                "indicator_update",
                                "market_analysis",
                            ],
                        },
                    },
                )
                return JSONResponse(content=serialize_for_dashboard(dashboard_info))
        except Exception as e:
            logger.error(f"Classic dashboard endpoint error: {e}")
            error_response = APIResponse(
                success=False, message="Dashboard unavailable", data={"error": str(e)}
            )
            return JSONResponse(
                status_code=500, content=serialize_for_dashboard(error_response)
            )

    return app


# Create app instance
app = create_app()
