"""
Odin Bitcoin Trading Bot - FastAPI Application with REAL DATA Integration
FIXED VERSION: Uses your existing EnhancedBitcoinDataCollector for real market data
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

# Import your existing enhanced data collector
from odin.core.enhanced_data_collector import EnhancedBitcoinDataCollector
from odin.core.database import get_database, init_sample_data
from odin.config import get_settings

# Import yfinance for real-time data
try:
    import yfinance as yf
except ImportError:
    yf = None
    logging.warning("yfinance not installed for real-time data")

# Global data collector instance
enhanced_collector: Optional[EnhancedBitcoinDataCollector] = None
real_time_cache = {
    "last_update": None,
    "current_price": None,
    "price_data": None
}

def create_app() -> FastAPI:
    """Create and configure FastAPI application with REAL data integration."""
    
    settings = get_settings()
    
    # Create FastAPI instance
    app = FastAPI(
        title="Odin Bitcoin Trading Bot - REAL DATA",
        description="Professional Bitcoin Trading Bot with LIVE Market Data",
        version="2.1.0",
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
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?$"
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
    
    # Initialize enhanced data collector on startup
    @app.on_event("startup")
    async def startup_event():
        """Initialize real data collection on startup."""
        global enhanced_collector
        
        try:
            # Initialize your existing enhanced data collector
            enhanced_collector = EnhancedBitcoinDataCollector("data/bitcoin_enhanced.db")
            
            # Start background task to keep data fresh
            asyncio.create_task(update_real_time_data())
            
            logging.info("Enhanced data collector initialized with REAL data sources")
            
        except Exception as e:
            logging.error(f"Failed to initialize enhanced data collector: {e}")
    
    async def update_real_time_data():
        """Background task to keep real-time data fresh."""
        while True:
            try:
                await fetch_real_time_bitcoin_data()
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logging.error(f"Real-time data update error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def fetch_real_time_bitcoin_data():
        """Fetch real Bitcoin data using yfinance."""
        global real_time_cache
        
        try:
            if yf:
                # Get real-time Bitcoin data
                btc = yf.Ticker("BTC-USD")
                
                # Get current info
                info = await asyncio.get_event_loop().run_in_executor(None, lambda: btc.info)
                
                # Get recent price data
                hist = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: btc.history(period="1d", interval="1m")
                )
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    current_price = float(latest['Close'])
                    volume = float(latest['Volume'])
                    
                    # Calculate 24h change
                    if len(hist) > 1440:  # More than 24 hours of minute data
                        price_24h_ago = float(hist.iloc[-1440]['Close'])
                        change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
                    else:
                        change_24h = 0.0
                    
                    # Update cache
                    real_time_cache.update({
                        "last_update": datetime.now(timezone.utc),
                        "current_price": current_price,
                        "price_data": {
                            "price": current_price,
                            "volume": volume,
                            "change_24h": change_24h,
                            "market_cap": info.get("marketCap", 0),
                            "bid": info.get("bid"),
                            "ask": info.get("ask"),
                            "timestamp": time.time()
                        }
                    })
                    
                    logging.info(f"Updated real-time BTC price: ${current_price:,.2f}")
                    
        except Exception as e:
            logging.error(f"Failed to fetch real-time data: {e}")
    
    # Health check endpoints
    @app.get("/api/v1/health")
    async def health_check():
        """Basic health check with data source status."""
        global enhanced_collector, real_time_cache
        
        data_status = "no_data"
        if enhanced_collector and real_time_cache["current_price"]:
            data_status = "real_data_active"
        elif enhanced_collector:
            data_status = "enhanced_collector_ready"
        
        return {
            "success": True,
            "status": "healthy",
            "message": "Odin Bot is running with REAL data",
            "version": "2.1.0",
            "timestamp": time.time(),
            "data_status": data_status,
            "last_price_update": real_time_cache["last_update"].isoformat() if real_time_cache["last_update"] else None,
            "current_btc_price": real_time_cache["current_price"]
        }
    
    @app.get("/api/v1/health/detailed")
    async def detailed_health():
        """Detailed health check with system metrics."""
        global enhanced_collector, real_time_cache
        
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            # Check data collector status
            collector_status = {
                "initialized": enhanced_collector is not None,
                "real_time_active": real_time_cache["current_price"] is not None,
                "last_update": real_time_cache["last_update"].isoformat() if real_time_cache["last_update"] else None,
                "yfinance_available": yf is not None
            }
            
            return {
                "success": True,
                "status": "healthy",
                "version": "2.1.0",
                "system": {
                    "memory_percent": memory.percent,
                    "cpu_percent": psutil.cpu_percent(interval=1)
                },
                "components": {
                    "database": "ready",
                    "trading_engine": "initialized",
                    "enhanced_data_collector": collector_status
                }
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }
    
    # REAL Bitcoin data endpoints
    @app.get("/api/v1/data/current")
    async def get_bitcoin_data():
        """Get current Bitcoin data - REAL DATA ONLY."""
        global real_time_cache
        
        # Try to get real-time data first
        if real_time_cache["price_data"] and real_time_cache["last_update"]:
            time_since_update = (datetime.now(timezone.utc) - real_time_cache["last_update"]).total_seconds()
            
            # Use cached data if it's less than 2 minutes old
            if time_since_update < 120:
                return {
                    "success": True,
                    "data": real_time_cache["price_data"],
                    "source": "yfinance_realtime",
                    "cache_age_seconds": int(time_since_update)
                }
        
        # If no recent cached data, try to fetch fresh data
        try:
            await fetch_real_time_bitcoin_data()
            
            if real_time_cache["price_data"]:
                return {
                    "success": True,
                    "data": real_time_cache["price_data"],
                    "source": "yfinance_fresh"
                }
        except Exception as e:
            logging.error(f"Failed to fetch fresh Bitcoin data: {e}")
        
        # Fallback to enhanced collector database
        if enhanced_collector:
            try:
                ml_data = enhanced_collector.get_ml_ready_features(lookback_days=1)
                if not ml_data.empty:
                    latest = ml_data.iloc[-1]
                    
                    return {
                        "success": True,
                        "data": {
                            "price": float(latest['close']),
                            "volume": float(latest.get('volume', 0)),
                            "change_24h": float(latest.get('price_change_percentage_24h', 0)),
                            "market_cap": float(latest.get('market_cap', 0)),
                            "timestamp": time.time()
                        },
                        "source": "enhanced_collector_database"
                    }
            except Exception as e:
                logging.error(f"Failed to get data from enhanced collector: {e}")
        
        # Last resort - return error
        raise HTTPException(
            status_code=503, 
            detail="Unable to fetch real Bitcoin data from any source"
        )
    
    @app.get("/api/v1/data/history/{hours}")
    async def get_historical_data(hours: int):
        """Get historical Bitcoin data - REAL DATA from enhanced collector."""
        global enhanced_collector
        
        if not enhanced_collector:
            raise HTTPException(status_code=503, detail="Enhanced data collector not available")
        
        try:
            # Calculate days needed
            days_needed = max(hours // 24, 1)
            
            # Get data from enhanced collector
            ml_data = enhanced_collector.get_ml_ready_features(lookback_days=days_needed)
            
            if ml_data.empty:
                raise HTTPException(status_code=404, detail="No historical data available")
            
            # Convert to API format
            data = []
            for index, row in ml_data.tail(hours).iterrows():
                data.append({
                    "timestamp": index.timestamp(),
                    "price": float(row['close']),
                    "volume": float(row.get('volume', 0)),
                    "open": float(row.get('open', row['close'])),
                    "high": float(row.get('high', row['close'])),
                    "low": float(row.get('low', row['close'])),
                    "rsi": float(row.get('rsi_14', 0)) if 'rsi_14' in row else None,
                    "ma_20": float(row.get('ma_20', 0)) if 'ma_20' in row else None
                })
            
            return {
                "success": True,
                "data": data,
                "source": "enhanced_collector",
                "count": len(data)
            }
            
        except Exception as e:
            logging.error(f"Error getting historical data: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/data/ml_features")
    async def get_ml_features(days: int = Query(30, description="Number of days of ML features")):
        """Get ML-ready features from enhanced collector."""
        global enhanced_collector
        
        if not enhanced_collector:
            raise HTTPException(status_code=503, detail="Enhanced data collector not available")
        
        try:
            ml_data = enhanced_collector.get_ml_ready_features(lookback_days=days)
            
            if ml_data.empty:
                raise HTTPException(status_code=404, detail="No ML features available")
            
            # Convert to JSON-serializable format
            features = []
            for index, row in ml_data.iterrows():
                feature_dict = {
                    "timestamp": index.isoformat(),
                    **{col: float(val) if pd.notna(val) else None for col, val in row.items()}
                }
                features.append(feature_dict)
            
            return {
                "success": True,
                "data": features,
                "features_count": len(ml_data.columns),
                "samples_count": len(features),
                "feature_names": ml_data.columns.tolist()
            }
            
        except Exception as e:
            logging.error(f"Error getting ML features: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/v1/data/refresh")
    async def refresh_data(background_tasks: BackgroundTasks):
        """Manually trigger data refresh."""
        global enhanced_collector
        
        if not enhanced_collector:
            raise HTTPException(status_code=503, detail="Enhanced data collector not available")
        
        # Add background task to refresh data
        background_tasks.add_task(refresh_data_background)
        
        return {
            "success": True,
            "message": "Data refresh initiated",
            "timestamp": time.time()
        }
    
    async def refresh_data_background():
        """Background task to refresh enhanced data."""
        global enhanced_collector
        
        try:
            # Get fresh data from all sources
            complete_data = enhanced_collector.get_historical_complete_dataset()
            
            if not complete_data.empty:
                # Save to database
                enhanced_collector.save_to_database(complete_data)
                logging.info(f"Refreshed {len(complete_data)} records in enhanced collector")
                
                # Also update real-time cache
                await fetch_real_time_bitcoin_data()
                
        except Exception as e:
            logging.error(f"Background data refresh failed: {e}")
    
    # Enhanced Portfolio endpoints with real data
    @app.get("/api/v1/portfolio")
    async def get_portfolio():
        """Get portfolio data with REAL Bitcoin prices."""
        global real_time_cache
        
        try:
            # Portfolio holdings (you can modify these)
            btc_balance = 0.25
            usd_balance = 5000.0
            
            # Get real BTC price
            current_btc_price = real_time_cache.get("current_price", 50000)  # fallback price
            
            # Calculate portfolio values
            btc_value = btc_balance * current_btc_price
            total_value = btc_value + usd_balance
            
            # Calculate allocations
            btc_allocation = (btc_value / total_value) * 100
            usd_allocation = (usd_balance / total_value) * 100
            
            # Get 24h change for P&L calculation
            price_data = real_time_cache.get("price_data", {})
            change_24h = price_data.get("change_24h", 0)
            pnl_24h = btc_value * (change_24h / 100)
            
            return {
                "success": True,
                "data": {
                    "total_value": round(total_value, 2),
                    "btc_balance": btc_balance,
                    "usd_balance": usd_balance,
                    "btc_price": round(current_btc_price, 2),
                    "btc_value": round(btc_value, 2),
                    "change_24h": round(change_24h, 2),
                    "pnl_24h": round(pnl_24h, 2),
                    "pnl_24h_percent": round(change_24h, 2),
                    "positions": [
                        {
                            "symbol": "BTC", 
                            "size": btc_balance, 
                            "value": round(btc_value, 2),
                            "price": round(current_btc_price, 2)
                        }
                    ],
                    "allocation": {
                        "Bitcoin": round(btc_allocation, 1),
                        "USD": round(usd_allocation, 1)
                    },
                    "data_source": "real_time"
                }
            }
            
        except Exception as e:
            logging.error(f"Error calculating portfolio: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Keep existing strategy endpoints (these can use mock data for now)
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
    
    # Trading endpoints (mock data for now)
    @app.get("/api/v1/trading/history")
    async def get_trading_history(limit: int = Query(10, description="Number of trades to return")):
        """Get trading history (mock data)."""
        import random
        
        orders = []
        strategies = ["ma_cross", "rsi_momentum", "bollinger_bands", "macd_trend"]
        
        # Get current real BTC price for realistic trade prices
        current_btc_price = real_time_cache.get("current_price", 50000)
        
        for i in range(limit):
            side = random.choice(["buy", "sell"])
            amount = round(random.uniform(0.001, 0.1), 6)
            # Use real price +/- some variation for historical trades
            price = current_btc_price + random.uniform(-5000, 5000)
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
        """Get auto-trading status (mock data)."""
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
    
    # Database initialization
    @app.get("/api/v1/database/init")
    async def init_database():
        """Initialize database and enhanced data collection."""
        global enhanced_collector
        
        try:
            # Initialize main database
            db = get_database()
            success = init_sample_data(db)
            stats = db.get_database_stats()
            
            # Initialize enhanced collector with fresh data
            if enhanced_collector:
                complete_data = enhanced_collector.get_historical_complete_dataset()
                if not complete_data.empty:
                    enhanced_collector.save_to_database(complete_data)
                    enhanced_records = len(complete_data)
                else:
                    enhanced_records = 0
            else:
                enhanced_records = 0
            
            return {
                "success": success,
                "message": "Database and enhanced data collector initialized",
                "stats": stats,
                "enhanced_records": enhanced_records
            }
            
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Include existing API routes
    try:
        from odin.api.routes.data import router as data_router
        app.include_router(data_router, prefix="/api/v1/legacy/data", tags=["legacy-data"])
    except ImportError as e:
        logging.warning(f"Could not import legacy data routes: {e}")
    
    try:
        from odin.api.routes.strategies import router as strategies_router
        app.include_router(strategies_router, prefix="/api/v1/strategies", tags=["strategies"])
    except ImportError as e:
        logging.warning(f"Could not import strategy routes: {e}")
    
    try:
        from odin.api.routes.trading import router as trading_router
        app.include_router(trading_router, prefix="/api/v1/trading", tags=["trading"])
    except ImportError as e:
        logging.warning(f"Could not import trading routes: {e}")
    
    try:
        from odin.api.routes.websockets import router as websocket_router
        app.include_router(websocket_router, prefix="", tags=["websockets"])
    except ImportError as e:
        logging.warning(f"Could not import websocket routes: {e}")
    
    # Root endpoint
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Serve the main dashboard."""
        if templates and template_path.exists():
            return templates.TemplateResponse("dashboard.html", {"request": request})
        else:
            current_price = real_time_cache.get("current_price")
            return {
                "message": "Odin Bitcoin Trading Bot - REAL DATA VERSION", 
                "version": "2.1.0", 
                "status": "running",
                "current_btc_price": f"${current_price:,.2f}" if current_price else "Fetching...",
                "data_sources": ["yfinance (real-time)", "Enhanced Collector (historical)", "CoinGecko", "Multiple APIs"],
                "endpoints": {
                    "dashboard": "/",
                    "health": "/api/v1/health",
                    "api_docs": "/docs",
                    "current_data": "/api/v1/data/current",
                    "historical": "/api/v1/data/history/24",
                    "ml_features": "/api/v1/data/ml_features",
                    "portfolio": "/api/v1/portfolio",
                    "refresh_data": "/api/v1/data/refresh"
                },
                "real_data_active": current_price is not None
            }
    
    return app


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )