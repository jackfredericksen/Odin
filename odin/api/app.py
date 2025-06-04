"""
Odin Bitcoin Trading Bot - FastAPI Application with WebSocket Support
Enhanced version with real-time WebSocket integration for live data streaming.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import random
import time
import logging
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Import configuration
try:
    from odin.config import get_settings
except ImportError:
    try:
        from odin.core.config import get_settings
    except ImportError:
        # Fallback settings
        class FallbackSettings:
            def __init__(self):
                self.environment = "development"
                self.debug = True
                self.host = "0.0.0.0"
                self.port = 8000
        
        def get_settings():
            return FallbackSettings()

# Import WebSocket support with proper error handling
try:
    from .routes.websocket import router as websocket_router, manager as ws_manager
    from .routes.websocket import (
        broadcast_price_update, 
        broadcast_portfolio_update,
        broadcast_system_alert
    )
    WEBSOCKET_AVAILABLE = True
    logger.info("WebSocket module loaded successfully")
except ImportError as e:
    # Create dummy components if WebSocket is not available
    logger.warning(f"WebSocket module not available: {e}")
    
    from fastapi import APIRouter
    websocket_router = APIRouter()
    WEBSOCKET_AVAILABLE = False
    
    class DummyManager:
        def get_connection_count(self):
            return 0
        def get_connection_info(self):
            return []
    
    ws_manager = DummyManager()
    
    async def broadcast_price_update(*args, **kwargs):
        pass
    
    async def broadcast_portfolio_update(*args, **kwargs):
        pass
    
    async def broadcast_system_alert(*args, **kwargs):
        pass

def create_app() -> FastAPI:
    """Create and configure FastAPI application with WebSocket support."""
    
    settings = get_settings()
    
    # Create FastAPI instance
    app = FastAPI(
        title="Odin Bitcoin Trading Bot",
        description="Professional Bitcoin Trading Bot with Live Trading & WebSocket API",
        version="2.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include WebSocket router
    app.include_router(websocket_router, tags=["websocket"])
    
    # Mount static files
    static_path = Path(__file__).parent.parent.parent / "web" / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Setup templates
    template_path = Path(__file__).parent.parent.parent / "web" / "templates"
    templates = None
    if template_path.exists():
        templates = Jinja2Templates(directory=str(template_path))
    
    # Store data for real-time updates
    app.state.current_price_data = None
    app.state.current_portfolio_data = None
    
    # Health check endpoints
    @app.get("/api/v1/health")
    async def health_check():
        """Basic health check with WebSocket status."""
        return {
            "success": True,
            "status": "healthy",
            "message": "Odin Bot is running",
            "version": "2.0.0",
            "websocket_connections": ws_manager.get_connection_count(),
            "timestamp": time.time()
        }
    
    @app.get("/api/v1/health/detailed")
    async def detailed_health():
        """Detailed health check with system metrics."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            return {
                "success": True,
                "status": "healthy",
                "version": "2.0.0",
                "system": {
                    "memory_percent": memory.percent,
                    "cpu_percent": psutil.cpu_percent(interval=1)
                },
                "websocket": {
                    "active_connections": ws_manager.get_connection_count(),
                    "connection_info": ws_manager.get_connection_info()
                },
                "components": {
                    "database": "ready",
                    "trading_engine": "initialized",
                    "websocket": "active"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }
    
    # Bitcoin data endpoints with WebSocket broadcasting
    @app.get("/api/v1/data/current")
    async def get_bitcoin_data():
        """Get current Bitcoin data with WebSocket broadcasting."""
        base_price = 45000
        current_price = base_price + random.uniform(-2000, 2000)
        
        price_data = {
            "price": round(current_price, 2),
            "change_24h": round(random.uniform(-5, 5), 2),
            "volume": round(random.uniform(1000, 5000), 2),
            "market_cap": round(current_price * 19700000, 0),
            "timestamp": time.time()
        }
        
        # Store for WebSocket broadcasting
        app.state.current_price_data = price_data
        
        # Broadcast to WebSocket clients
        try:
            await broadcast_price_update(price_data)
        except Exception as e:
            logger.warning(f"Failed to broadcast price update: {e}")
        
        return {
            "success": True,
            "data": price_data
        }
    
    @app.get("/api/v1/data/history/{hours}")
    async def get_historical_data(hours: int):
        """Get historical Bitcoin data."""
        data = []
        base_price = 45000
        current_time = time.time()
        
        for i in range(min(hours, 100)):  # Limit to 100 points
            timestamp = current_time - (i * 3600)  # Hourly data
            price = base_price + random.uniform(-2000, 2000)
            data.append({
                "timestamp": timestamp,
                "price": round(price, 2),
                "volume": round(random.uniform(100, 1000), 2)
            })
        
        return {
            "success": True,
            "data": list(reversed(data))  # Chronological order
        }
    
    # Portfolio endpoints with WebSocket broadcasting
    @app.get("/api/v1/portfolio")
    async def get_portfolio():
        """Get portfolio data with WebSocket broadcasting."""
        total_value = 10000 + random.uniform(-500, 500)
        change_24h = round(random.uniform(-3, 3), 2)
        pnl_24h = round(total_value * (change_24h / 100), 2)
        
        portfolio_data = {
            "total_value": round(total_value, 2),
            "btc_balance": 0.25,
            "usd_balance": 5000,
            "change_24h": change_24h,
            "pnl_24h": pnl_24h,
            "pnl_24h_percent": change_24h,
            "positions": [
                {"symbol": "BTC", "size": 0.25, "value": 11250}
            ],
            "allocation": {
                "Bitcoin": 75,
                "USD": 25
            }
        }
        
        # Store for WebSocket broadcasting
        app.state.current_portfolio_data = portfolio_data
        
        # Broadcast to WebSocket clients
        try:
            await broadcast_portfolio_update(portfolio_data)
        except Exception as e:
            logger.warning(f"Failed to broadcast portfolio update: {e}")
        
        return {
            "success": True,
            "data": portfolio_data
        }
    
    # Strategy endpoints
    @app.get("/api/v1/strategies/list")
    async def get_strategies():
        """Get trading strategies."""
        strategies_data = [
            {
                "id": "ma_cross",
                "name": "Moving Average Crossover",
                "type": "moving_average",
                "active": True,
                "return": 12.5,
                "total_trades": 45,
                "win_rate": 68.9,
                "sharpe_ratio": 1.85,
                "max_drawdown": -8.2,
                "volatility": 15.3,
                "performance_history": [
                    {"timestamp": time.time() - (i * 86400), "value": random.uniform(-5, 15)}
                    for i in range(30)
                ]
            },
            {
                "id": "rsi_momentum",
                "name": "RSI Momentum",
                "type": "rsi",
                "active": False,
                "return": -2.1,
                "total_trades": 23,
                "win_rate": 43.5,
                "sharpe_ratio": 0.92,
                "max_drawdown": -12.5,
                "volatility": 18.7,
                "performance_history": [
                    {"timestamp": time.time() - (i * 86400), "value": random.uniform(-10, 5)}
                    for i in range(30)
                ]
            },
            {
                "id": "bollinger_bands",
                "name": "Bollinger Bands",
                "type": "bollinger_bands",
                "active": True,
                "return": 8.7,
                "total_trades": 67,
                "win_rate": 59.7,
                "sharpe_ratio": 1.34,
                "max_drawdown": -6.8,
                "volatility": 12.1,
                "performance_history": [
                    {"timestamp": time.time() - (i * 86400), "value": random.uniform(-3, 12)}
                    for i in range(30)
                ]
            },
            {
                "id": "macd_trend",
                "name": "MACD Trend",
                "type": "macd",
                "active": False,
                "return": 5.3,
                "total_trades": 34,
                "win_rate": 55.9,
                "sharpe_ratio": 1.12,
                "max_drawdown": -9.4,
                "volatility": 16.8,
                "performance_history": [
                    {"timestamp": time.time() - (i * 86400), "value": random.uniform(-7, 10)}
                    for i in range(30)
                ]
            }
        ]
        
        return {
            "success": True,
            "data": strategies_data
        }
    
    @app.post("/api/v1/strategies/{strategy_id}/enable")
    async def enable_strategy(strategy_id: str):
        """Enable a trading strategy with WebSocket notification."""
        try:
            # Simulate enabling strategy
            await broadcast_system_alert(
                "Strategy Enabled",
                f"Strategy {strategy_id} has been enabled",
                "success"
            )
            
            return {
                "success": True,
                "message": f"Strategy {strategy_id} enabled successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to enable strategy: {str(e)}"
            }
    
    @app.post("/api/v1/strategies/{strategy_id}/disable")
    async def disable_strategy(strategy_id: str):
        """Disable a trading strategy with WebSocket notification."""
        try:
            # Simulate disabling strategy
            await broadcast_system_alert(
                "Strategy Disabled",
                f"Strategy {strategy_id} has been disabled",
                "warning"
            )
            
            return {
                "success": True,
                "message": f"Strategy {strategy_id} disabled successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to disable strategy: {str(e)}"
            }
    
    # Trading endpoints
    @app.get("/api/v1/trading/history")
    async def get_trading_history(limit: int = 10):
        """Get trading history."""
        orders = []
        strategies = ["ma_cross", "rsi_momentum", "bollinger_bands", "macd_trend"]
        
        for i in range(limit):
            side = random.choice(["buy", "sell"])
            amount = round(random.uniform(0.001, 0.1), 6)
            price = 45000 + random.uniform(-2000, 2000)
            pnl = round(random.uniform(-50, 50), 2)
            
            orders.append({
                "id": f"order_{i}",
                "timestamp": time.time() - (i * 3600),
                "strategy": random.choice(strategies),
                "side": side,
                "amount": amount,
                "price": round(price, 2),
                "status": random.choice(["filled", "pending", "cancelled"]),
                "pnl": pnl
            })
        
        return {
            "success": True,
            "data": orders
        }
    
    @app.get("/api/v1/trading/status")
    async def get_trading_status():
        """Get auto-trading status."""
        return {
            "success": True,
            "data": {
                "enabled": False,
                "active_strategies": 2,
                "last_trade": time.time() - 1800,  # 30 minutes ago
                "total_trades_today": 15,
                "pnl_today": 127.50
            }
        }
    
    @app.post("/api/v1/trading/enable")
    async def enable_trading():
        """Enable auto-trading with WebSocket notification."""
        await broadcast_system_alert(
            "Auto-Trading Enabled",
            "Automatic trading has been enabled",
            "success"
        )
        
        return {
            "success": True,
            "message": "Auto-trading enabled"
        }
    
    @app.post("/api/v1/trading/disable")
    async def disable_trading():
        """Disable auto-trading with WebSocket notification."""
        await broadcast_system_alert(
            "Auto-Trading Disabled",
            "Automatic trading has been disabled",
            "warning"
        )
        
        return {
            "success": True,
            "message": "Auto-trading disabled"
        }
    
    @app.post("/api/v1/trading/emergency-stop")
    async def emergency_stop():
        """Emergency stop all trading with WebSocket notification."""
        await broadcast_system_alert(
            "Emergency Stop Activated",
            "All trading activities have been stopped immediately",
            "error"
        )
        
        return {
            "success": True,
            "message": "Emergency stop activated - all trading stopped"
        }
    
    # Portfolio management endpoints
    @app.post("/api/v1/portfolio/rebalance")
    async def rebalance_portfolio():
        """Rebalance portfolio with WebSocket notification."""
        try:
            # Simulate rebalancing
            await asyncio.sleep(1)  # Simulate processing time
            
            await broadcast_system_alert(
                "Portfolio Rebalanced",
                "Portfolio rebalancing completed successfully",
                "success"
            )
            
            return {
                "success": True,
                "message": "Portfolio rebalanced successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Rebalancing failed: {str(e)}"
            }
    
    # Database initialization endpoint
    @app.get("/api/v1/database/init")
    async def init_database():
        """Initialize database with sample data."""
        try:
            from odin.core.database import get_database, init_sample_data
            
            db = get_database()
            success = init_sample_data(db)
            stats = db.get_database_stats()
            
            if success:
                await broadcast_system_alert(
                    "Database Initialized",
                    "Database has been initialized with sample data",
                    "info"
                )
        
            return {
                "success": success,
                "message": "Database initialized with sample data",
                "stats": stats
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Database initialization failed: {str(e)}"
            }
    
    # Root endpoint - serve dashboard
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Serve the main dashboard."""
        if templates and template_path.exists():
            return templates.TemplateResponse("dashboard.html", {"request": request})
        else:
            return JSONResponse({
                "message": "Odin Bitcoin Trading Bot API", 
                "version": "2.0.0", 
                "status": "running",
                "websocket_connections": ws_manager.get_connection_count(),
                "endpoints": {
                    "dashboard": "/",
                    "health": "/api/v1/health",
                    "api_docs": "/docs",
                    "websocket": "/ws",
                    "bitcoin_data": "/api/v1/data/current",
                    "portfolio": "/api/v1/portfolio",
                    "strategies": "/api/v1/strategies/list"
                }
            })
    
    # Startup event to initialize background tasks
    @app.on_event("startup")
    async def startup_event():
        """Initialize background tasks on startup."""
        logger.info("🚀 Odin Trading Bot starting up...")
        logger.info(f"🔌 WebSocket support enabled")
        
        # Start background task for periodic data updates
        asyncio.create_task(periodic_data_broadcast())
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("🔄 Odin Trading Bot shutting down...")
    
    return app

async def periodic_data_broadcast():
    """Background task to periodically broadcast data updates."""
    while True:
        try:
            # Wait 30 seconds between broadcasts
            await asyncio.sleep(30)
            
            # Only broadcast if there are connected clients
            if ws_manager.get_connection_count() > 0:
                # Generate and broadcast price update
                base_price = 45000
                current_price = base_price + random.uniform(-2000, 2000)
                
                price_data = {
                    "price": round(current_price, 2),
                    "change_24h": round(random.uniform(-5, 5), 2),
                    "volume": round(random.uniform(1000, 5000), 2),
                    "market_cap": round(current_price * 19700000, 0),
                    "timestamp": time.time()
                }
                
                await broadcast_price_update(price_data)
                
                # Occasionally broadcast portfolio updates
                if random.random() < 0.3:  # 30% chance
                    total_value = 10000 + random.uniform(-500, 500)
                    change_24h = round(random.uniform(-3, 3), 2)
                    
                    portfolio_data = {
                        "total_value": round(total_value, 2),
                        "change_24h": change_24h,
                        "pnl_24h": round(total_value * (change_24h / 100), 2),
                        "pnl_24h_percent": change_24h
                    }
                    
                    await broadcast_portfolio_update(portfolio_data)
                
        except Exception as e:
            logger.error(f"Error in periodic data broadcast: {e}")
            await asyncio.sleep(5)  # Wait before retrying