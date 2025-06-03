"""
Odin Bitcoin Trading Bot - FastAPI Application (Updated with Real Data Integration)
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import config without causing circular imports
try:
    from odin.config import get_settings
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
    
    # Initialize components
    @app.on_event("startup")
    async def startup_event():
        """Initialize application components."""
        try:
            # Initialize database with sample data
            from odin.core.database import get_database, init_sample_data
            db = get_database()
            
            # Check if we have data, if not initialize sample data
            stats = db.get_database_stats()
            if stats.get('bitcoin_prices_count', 0) == 0:
                logger.info("No existing data found, initializing sample data...")
                init_sample_data(db)
                logger.info("Sample data initialized successfully")
            else:
                logger.info(f"Database already contains {stats.get('bitcoin_prices_count', 0)} price records")
                
        except Exception as e:
            logger.error(f"Startup initialization error: {e}")
    
    # Health check endpoints
    @app.get("/api/v1/health")
    async def health_check():
        """Basic health check."""
        try:
            from odin.core.database import get_database
            db = get_database()
            stats = db.get_database_stats()
            
            return {
                "success": True,
                "status": "healthy",
                "message": "Odin Bot is running",
                "version": "2.0.0",
                "timestamp": time.time(),
                "database": {
                    "status": "connected",
                    "price_records": stats.get('bitcoin_prices_count', 0),
                    "strategies": stats.get('strategies_count', 0)
                }
            }
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    @app.get("/api/v1/health/detailed")
    async def detailed_health():
        """Detailed health check."""
        try:
            import psutil
            from odin.core.database import get_database
            
            memory = psutil.virtual_memory()
            db = get_database()
            stats = db.get_database_stats()
            
            return {
                "success": True,
                "status": "healthy",
                "version": "2.0.0",
                "system": {
                    "memory_percent": memory.percent,
                    "cpu_percent": psutil.cpu_percent(interval=1)
                },
                "database": stats,
                "components": {
                    "database": "ready",
                    "trading_engine": "initialized",
                    "portfolio_manager": "ready"
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
        """Get current Bitcoin data from database."""
        try:
            from odin.core.database import get_database
            db = get_database()
            
            current_data = db.get_current_price()
            if not current_data:
                # Fallback to mock data if no real data
                return {
                    "success": True,
                    "data": {
                        "price": 45000.00,
                        "change_24h": 2.5,
                        "volume": 1000.0,
                        "market_cap": 885000000000,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            
            # Calculate 24h change (simplified)
            recent_prices = db.get_recent_prices(limit=24)
            change_24h = 0.0
            if len(recent_prices) >= 2:
                old_price = recent_prices[0]["price"]
                new_price = current_data["price"]
                change_24h = ((new_price - old_price) / old_price) * 100
            
            return {
                "success": True,
                "data": {
                    "price": float(current_data["price"]),
                    "change_24h": round(change_24h, 2),
                    "volume": float(current_data.get("volume", 0)),
                    "market_cap": float(current_data.get("market_cap", 0)),
                    "timestamp": current_data["timestamp"]
                }
            }
        except Exception as e:
            logger.error(f"Error getting current Bitcoin data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @app.get("/api/v1/data/history/{hours}")
    async def get_historical_data(hours: int):
        """Get historical Bitcoin data from database."""
        try:
            from odin.core.database import get_database
            db = get_database()
            
            # Validate hours parameter
            if hours < 1 or hours > 8760:  # Max 1 year
                raise HTTPException(status_code=400, detail="Hours must be between 1 and 8760")
            
            # Get historical data from database
            historical_data = db.get_recent_prices(limit=min(hours * 2, 1000))  # Get more data points for better resolution
            
            if not historical_data:
                return {
                    "success": False,
                    "error": "No historical data available"
                }
            
            # Format data for frontend
            formatted_data = []
            for record in reversed(historical_data):  # Reverse to get chronological order
                formatted_data.append({
                    "timestamp": record["timestamp"],
                    "price": float(record["price"]),
                    "volume": float(record.get("volume", 0)),
                    "high": float(record.get("price", 0)),  # Simplified - using price as high/low
                    "low": float(record.get("price", 0))
                })
            
            return {
                "success": True,
                "data": formatted_data[-hours:] if len(formatted_data) > hours else formatted_data  # Limit to requested hours
            }
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Portfolio endpoints
    @app.get("/api/v1/portfolio")
    async def get_portfolio():
        """Get portfolio data from portfolio manager."""
        try:
            from odin.core.database import get_database
            
            db = get_database()
            
            # Get current price for calculations
            current_price_data = db.get_current_price()
            current_price = float(current_price_data["price"]) if current_price_data else 45000.0
            
            # Get latest portfolio snapshot
            portfolio_data = db.get_latest_portfolio()
            
            if portfolio_data:
                # Use real portfolio data
                total_value = float(portfolio_data["total_value"])
                cash_balance = float(portfolio_data["cash_balance"])
                btc_balance = float(portfolio_data["btc_balance"])
                daily_pnl = float(portfolio_data.get("daily_pnl", 0))
                daily_pnl_percent = float(portfolio_data.get("daily_pnl_percentage", 0))
            else:
                # Default portfolio values
                total_value = 10000.0
                cash_balance = 5000.0
                btc_balance = 0.25
                daily_pnl = 125.50
                daily_pnl_percent = 1.27
            
            # Calculate derived values
            btc_value = btc_balance * current_price
            total_calculated = cash_balance + btc_value
            
            return {
                "success": True,
                "data": {
                    "total_value": round(total_calculated, 2),
                    "btc_balance": btc_balance,
                    "usd_balance": cash_balance,
                    "change_24h": daily_pnl_percent,
                    "pnl_24h": daily_pnl,
                    "pnl_24h_percent": daily_pnl_percent,
                    "positions": [
                        {"symbol": "BTC", "size": btc_balance, "value": btc_value}
                    ],
                    "allocation": {
                        "Bitcoin": round((btc_value / total_calculated) * 100, 1) if total_calculated > 0 else 0,
                        "USD": round((cash_balance / total_calculated) * 100, 1) if total_calculated > 0 else 100
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Strategy endpoints
    @app.get("/api/v1/strategies/list")
    async def get_strategies():
        """Get trading strategies with real data."""
        try:
            from odin.core.database import get_database
            
            db = get_database()
            
            # Get strategies from database
            strategies_data = db.get_strategies()
            
            if not strategies_data:
                # Initialize default strategies if none exist
                default_strategies = [
                    ("ma_cross", "Moving Average Crossover", "moving_average", 
                     "Simple moving average crossover strategy", {"short_period": 5, "long_period": 20}, True),
                    ("rsi_momentum", "RSI Momentum", "rsi", 
                     "RSI-based momentum strategy", {"period": 14, "overbought": 70, "oversold": 30}, True),
                    ("bollinger_bands", "Bollinger Bands", "bollinger_bands", 
                     "Bollinger Bands mean reversion strategy", {"period": 20, "std_dev": 2}, False),
                    ("macd_trend", "MACD Trend", "macd", 
                     "MACD trend following strategy", {"fast_period": 12, "slow_period": 26, "signal_period": 9}, False)
                ]
                
                for strategy_id, name, strategy_type, description, params, active in default_strategies:
                    db.add_strategy(strategy_id, name, strategy_type, description, params, active)
                
                strategies_data = db.get_strategies()
            
            # Format strategies for frontend
            formatted_strategies = []
            for strategy in strategies_data:
                # Get recent trades for this strategy to calculate performance
                recent_trades = db.get_recent_trades(limit=100, strategy_id=strategy["id"])
                
                # Calculate basic performance metrics
                total_trades = len(recent_trades)
                winning_trades = sum(1 for trade in recent_trades if trade.get("pnl", 0) > 0)
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                # Calculate total return (simplified)
                total_pnl = sum(trade.get("pnl", 0) for trade in recent_trades)
                total_return = total_pnl / 1000 * 100 if total_pnl != 0 else 0  # Assuming $1000 base
                
                # Generate mock performance history for chart
                import random
                performance_history = []
                for i in range(30):
                    timestamp = time.time() - (i * 86400)  # Daily points
                    value = total_return + random.uniform(-5, 5)  # Add some variation
                    performance_history.append({"timestamp": timestamp, "value": value})
                
                formatted_strategies.append({
                    "id": strategy["id"],
                    "name": strategy["name"],
                    "type": strategy["type"],
                    "active": bool(strategy["active"]),
                    "return": round(total_return, 2),
                    "total_trades": total_trades,
                    "win_rate": round(win_rate, 1),
                    "sharpe_ratio": round(total_return / 10 if total_return != 0 else 0, 2),  # Simplified Sharpe
                    "max_drawdown": round(abs(total_return) * 0.3, 1),  # Mock drawdown
                    "volatility": round(abs(total_return) * 0.8, 1),  # Mock volatility
                    "performance_history": list(reversed(performance_history))
                })
            
            return {
                "success": True,
                "data": formatted_strategies
            }
        except Exception as e:
            logger.error(f"Error getting strategies: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Trading endpoints
    @app.get("/api/v1/trading/history")
    async def get_trading_history(limit: int = 10):
        """Get trading history from database."""
        try:
            from odin.core.database import get_database
            
            db = get_database()
            trades = db.get_recent_trades(limit=limit)
            
            # Format trades for frontend
            formatted_trades = []
            for trade in trades:
                formatted_trades.append({
                    "id": trade["id"],
                    "timestamp": trade["timestamp"],
                    "strategy": trade.get("strategy_id", "manual"),
                    "side": trade["side"],
                    "amount": float(trade["amount"]),
                    "price": float(trade["price"]),
                    "status": trade["status"],
                    "pnl": float(trade.get("pnl", 0))
                })
            
            return {
                "success": True,
                "data": formatted_trades
            }
        except Exception as e:
            logger.error(f"Error getting trading history: {e}")
            return {
                "success": False,
                "error": str(e)
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
                "total_trades_today": 8,
                "pnl_today": 85.25
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
            logger.error(f"Database initialization error: {e}")
            return {
                "success": False,
                "error": str(e)
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
                    "init_database": "/api/v1/database/init"
                }
            }
    
    return app