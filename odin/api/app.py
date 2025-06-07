"""
Odin Bitcoin Trading Bot - FastAPI Application (FIXED VERSION)
"""
from odin.core.database import get_database, init_sample_data
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
import random
import time

# FIXED: Import config properly
from odin.config import get_settings

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
                    "trading_engine": "initialized"
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
        """Get current Bitcoin data (mock)."""
        base_price = 45000
        current_price = base_price + random.uniform(-2000, 2000)
        
        return {
            "success": True,
            "data": {
                "price": round(current_price, 2),
                "change_24h": round(random.uniform(-5, 5), 2),
                "volume": round(random.uniform(1000, 5000), 2),
                "market_cap": round(current_price * 19700000, 0),
                "timestamp": time.time()
            }
        }
    
    @app.get("/api/v1/data/history/{hours}")
    async def get_historical_data(hours: int):
        """Get historical Bitcoin data (mock)."""
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
    
    # Portfolio endpoints
    @app.get("/api/v1/portfolio")
    async def get_portfolio():
        """Get portfolio data (mock)."""
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
        """Get trading strategies (mock)."""
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
        """Get trading history (mock)."""
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
        """Get auto-trading status (mock)."""
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
    
    @app.get("/api/v1/database/init")
    async def init_database():
        """Initialize database with sample data."""
        db = get_database()
        success = init_sample_data(db)
        stats = db.get_database_stats()

        return {
            "success": success,
            "message": "Database initialized with sample data",
            "stats": stats
        }
    
    # Include API routes with better error handling
    try:
        from odin.api.routes.data import router as data_router
        app.include_router(data_router, prefix="/api/v1/data", tags=["data"])
        print("Successfully imported data routes")
    except ImportError as e:
        print(f"Could not import data routes: {e}")
    
    try:
        from odin.api.routes.strategies import router as strategies_router
        app.include_router(strategies_router, prefix="/api/v1/strategies", tags=["strategies"])
        print("Successfully imported strategy routes")
    except ImportError as e:
        print(f"Could not import strategy routes: {e}")
    
    try:
        from odin.api.routes.trading import router as trading_router
        app.include_router(trading_router, prefix="/api/v1/trading", tags=["trading"])
        print("Successfully imported trading routes")
    except ImportError as e:
        print(f"Could not import trading routes: {e}")
    
    try:
        from odin.api.routes.portfolio import router as portfolio_router
        app.include_router(portfolio_router, prefix="/api/v1/portfolio", tags=["portfolio"])
        print("Successfully imported portfolio routes")
    except ImportError as e:
        print(f"Could not import portfolio routes: {e}")
    
    try:
        from odin.api.routes.websockets import router as websocket_router
        app.include_router(websocket_router, prefix="/api/v1", tags=["websockets"])
        print("Successfully imported websocket routes")
    except ImportError as e:
        print(f"Could not import websocket routes: {e}")
    
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
                    "strategies": "/api/v1/strategies/list"
                }
            }
    
    return app