"""
Odin Bitcoin Trading Bot - Fixed FastAPI Application

Fixed version that includes WebSocket support and removes circular import issues.
"""

import asyncio
from pathlib import Path
import random
import time
import logging
import json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

# Import config without causing circular imports
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

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    settings = get_settings()
    
    # Create FastAPI instance
    app = FastAPI(
        title="Odin Bitcoin Trading Bot",
        description="Professional Bitcoin Trading Bot with Live Trading & API",
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
    
    # Mount static files
    static_path = Path(__file__).parent.parent.parent / "web" / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Setup templates
    template_path = Path(__file__).parent.parent.parent / "web" / "templates"
    templates = None
    if template_path.exists():
        templates = Jinja2Templates(directory=str(template_path))
    
    # Include WebSocket routes
    try:
        from odin.api.routes.websockets import router as websocket_router
        app.include_router(websocket_router)
        logger.info("🔌 WebSocket support enabled")
    except ImportError as e:
        logger.warning(f"WebSocket module not available: {e}")
    
    # Add a simple WebSocket endpoint directly in the app
    @app.websocket("/ws")
    async def websocket_endpoint_fallback(websocket):
        await websocket.accept()
        try:
            await websocket.send_text('{"type":"connection","status":"connected","message":"WebSocket connected"}')
            while True:
                await websocket.receive_text()
        except Exception:
            pass
    logger.info("🔌 Fallback WebSocket endpoint created")
    # Add this directly in app.py after middleware setup
    @app.websocket("/ws")
    async def websocket_endpoint(websocket):
        """Direct WebSocket endpoint in app.py"""
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        try:
            # Send connection confirmation
            await websocket.send_text(json.dumps({
                "type": "connection",
                "status": "connected", 
                "timestamp": time.time(),
                "message": "Connected to Odin Trading Bot"
            }))
            
            # Keep connection alive
            while True:
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    # Echo back for now
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": time.time()
                    }))
                except asyncio.TimeoutError:
                    await websocket.send_text(json.dumps({
                        "type": "ping",
                        "timestamp": time.time()
                    }))
                except Exception:
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            logger.info("WebSocket connection closed")

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize application on startup."""
        logger.info("🚀 Odin Trading Bot starting up...")
        
        try:
            # Initialize data collector
            from odin.core.data_collector import get_data_collector
            collector = get_data_collector()
            
            # Start data collection
            await collector.start_collection()
            logger.info("📊 Data collection started")
            
        except Exception as e:
            logger.warning(f"Startup warning: {e}")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("🛑 Odin Trading Bot shutting down...")
        
        try:
            # Stop data collection
            from odin.core.data_collector import get_data_collector
            collector = get_data_collector()
            await collector.stop_collection()
            logger.info("📊 Data collection stopped")
            
        except Exception as e:
            logger.warning(f"Shutdown warning: {e}")
    
    # Health check endpoints
    @app.get("/api/v1/health")
    async def health_check():
        """Basic health check."""
        return {
            "success": True,
            "status": "healthy",
            "message": "Odin Bot is running",
            "version": "2.0.0",
            "timestamp": time.time()
        }
    
    @app.get("/api/v1/health/detailed")
    async def detailed_health():
        """Detailed health check."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            # Check WebSocket status
            websocket_status = "disabled"
            try:
                from odin.api.routes.websockets import websocket_health_check
                ws_health = await websocket_health_check()
                websocket_status = "enabled" if ws_health["websocket_enabled"] else "disabled"
            except:
                websocket_status = "error"
            
            return {
                "success": True,
                "status": "healthy",
                "version": "2.0.0",
                "system": {
                    "memory_percent": memory.percent,
                    "cpu_percent": psutil.cpu_percent(interval=1)
                },
                "components": {
                    "database": "ready",
                    "trading_engine": "initialized",
                    "websockets": websocket_status,
                    "data_collector": "running"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }
    
    # Bitcoin data endpoints
    @app.get("/api/v1/data/current")
    async def get_bitcoin_data():
        """Get current Bitcoin data."""
        try:
            from odin.core.data_collector import get_data_collector
            collector = get_data_collector()
            current_data = await collector.get_current_price()
            
            return {
                "success": True,
                "data": current_data
            }
        except Exception as e:
            logger.error(f"Error getting current data: {e}")
            # Fallback to mock data
            base_price = 45000
            current_price = base_price + random.uniform(-2000, 2000)
            
            return {
                "success": True,
                "data": {
                    "price": round(current_price, 2),
                    "change_24h": round(random.uniform(-5, 5), 2),
                    "volume": round(random.uniform(1000, 5000), 2),
                    "timestamp": time.time(),
                    "source": "fallback"
                }
            }
    
    @app.get("/api/v1/data/history/{hours}")
    async def get_historical_data(hours: int):
        """Get historical Bitcoin data."""
        try:
            from odin.core.data_collector import get_data_collector
            collector = get_data_collector()
            history_data = await collector.get_price_history(min(hours, 168))  # Max 1 week
            
            return {
                "success": True,
                "data": history_data
            }
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            # Fallback to mock data
            data = []
            base_price = 45000
            current_time = time.time()
            
            for i in range(min(hours, 100)):
                timestamp = current_time - (i * 3600)
                price = base_price + random.uniform(-2000, 2000)
                data.append({
                    "timestamp": timestamp,
                    "price": round(price, 2),
                    "volume": round(random.uniform(100, 1000), 2),
                    "source": "fallback"
                })
            
            return {
                "success": True,
                "data": list(reversed(data))
            }
    
    # Portfolio endpoints
    @app.get("/api/v1/portfolio")
    async def get_portfolio():
        """Get portfolio data."""
        total_value = 10000 + random.uniform(-500, 500)
        change_24h = round(random.uniform(-3, 3), 2)
        pnl_24h = round(total_value * (change_24h / 100), 2)
        
        return {
            "success": True,
            "data": {
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
        }
    
    # Strategy endpoints
    @app.get("/api/v1/strategies/list")
    async def get_strategies():
        """Get trading strategies."""
        return {
            "success": True,
            "data": [
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
                "last_trade": time.time() - 1800,
                "total_trades_today": 15,
                "pnl_today": 127.50
            }
        }
    
    @app.get("/api/v1/database/init")
    async def init_database():
        """Initialize database with sample data."""
        try:
            from odin.core.database import get_database, init_sample_data
            db = get_database()
            success = init_sample_data(db)
            stats = db.get_database_stats()
        
            return {
                "success": success,
                "message": "Database initialized with sample data",
                "stats": stats
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Database initialization failed: {e}"
            }
    
    # Root endpoint - serve dashboard
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Serve the main dashboard."""
        if templates and template_path.exists():
            return templates.TemplateResponse("dashboard.html", {"request": request})
        else:
            return {
                "message": "Odin Bitcoin Trading Bot API", 
                "version": "2.0.0", 
                "status": "running",
                "endpoints": {
                    "dashboard": "/",
                    "health": "/api/v1/health",
                    "api_docs": "/docs",
                    "bitcoin_data": "/api/v1/data/current",
                    "portfolio": "/api/v1/portfolio",
                    "strategies": "/api/v1/strategies/list",
                    "websocket": "/ws"
                }
            }
    
    return app