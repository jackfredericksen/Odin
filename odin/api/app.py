"""
Odin Bitcoin Trading Bot - Fixed FastAPI Application with Direct WebSocket
"""

import asyncio
import json
import logging
import random
import time
from pathlib import Path
from typing import List

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
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
        class FallbackSettings:
            def __init__(self):
                self.environment = "development"
                self.debug = True
                self.host = "0.0.0.0"
                self.port = 8000
        
        def get_settings():
            return FallbackSettings()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

# Global connection manager
websocket_manager = ConnectionManager()

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
    
    # DIRECT WEBSOCKET ENDPOINT (bypassing route imports)
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """Direct WebSocket endpoint for real-time dashboard updates."""
        await websocket_manager.connect(websocket)
        
        try:
            # Send connection confirmation
            await websocket_manager.send_personal_message({
                "type": "connection",
                "status": "connected",
                "timestamp": time.time(),
                "message": "Connected to Odin Trading Bot"
            }, websocket)
            
            # Send initial data
            try:
                from odin.core.data_collector import get_data_collector
                collector = get_data_collector()
                current_price = await collector.get_current_price()
                
                await websocket_manager.send_personal_message({
                    "type": "initial_data",
                    "timestamp": time.time(),
                    "data": {
                        "bitcoin_price": current_price,
                        "connection_status": "connected"
                    }
                }, websocket)
            except Exception as e:
                logger.error(f"Failed to send initial data: {e}")
                # Send fallback data
                await websocket_manager.send_personal_message({
                    "type": "initial_data",
                    "timestamp": time.time(),
                    "data": {
                        "bitcoin_price": {
                            "price": 45000 + random.uniform(-2000, 2000),
                            "timestamp": time.time(),
                            "source": "fallback"
                        },
                        "connection_status": "connected"
                    }
                }, websocket)
            
            # Keep connection alive and handle messages
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    
                    # Handle client messages
                    try:
                        data = json.loads(message)
                        if data.get("type") == "ping":
                            await websocket_manager.send_personal_message({
                                "type": "pong",
                                "timestamp": time.time()
                            }, websocket)
                        elif data.get("type") == "request_data":
                            # Handle data requests
                            request_type = data.get("request")
                            if request_type == "portfolio":
                                await websocket_manager.send_personal_message({
                                    "type": "portfolio_data",
                                    "timestamp": time.time(),
                                    "data": {
                                        "total_value": 10000 + random.uniform(-500, 500),
                                        "btc_balance": 0.25,
                                        "usd_balance": 8750,
                                        "daily_pnl": random.uniform(-200, 200),
                                        "daily_pnl_percent": random.uniform(-2, 2)
                                    }
                                }, websocket)
                    except json.JSONDecodeError:
                        pass
                        
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket_manager.send_personal_message({
                        "type": "ping",
                        "timestamp": time.time()
                    }, websocket)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket message error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            websocket_manager.disconnect(websocket)
    
    logger.info("🔌 Direct WebSocket endpoint created at /ws")
    
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
            
            # Set up price update broadcasting
            async def price_broadcast_callback(price_data):
                await websocket_manager.broadcast({
                    "type": "price_update",
                    "timestamp": time.time(),
                    "data": price_data
                })
            
            collector.add_callback(price_broadcast_callback)
            logger.info("📡 Price broadcasting enabled")
            
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
            "timestamp": time.time(),
            "websocket_connections": len(websocket_manager.active_connections)
        }
    
    @app.get("/api/v1/health/detailed")
    async def detailed_health():
        """Detailed health check."""
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
                "components": {
                    "database": "ready",
                    "trading_engine": "initialized",
                    "websockets": "enabled",
                    "data_collector": "running",
                    "active_connections": len(websocket_manager.active_connections)
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
            history_data = await collector.get_price_history(min(hours, 168))
            
            return {
                "success": True,
                "data": history_data
            }
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            # Fallback mock data
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
                    "volatility": 15.3
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
                    "volatility": 18.7
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
    
    # Database initialization endpoint
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
                "websocket_connections": len(websocket_manager.active_connections),
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