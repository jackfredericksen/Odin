#!/usr/bin/env python3
"""
Odin Bitcoin Trading Bot - Simple Standalone Runner
Place this file in your project root directory
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import logging
import random
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Odin Bitcoin Trading Bot",
    description="Professional Bitcoin Trading Bot",
    version="2.0.0"
)

# Setup static files and templates
static_path = Path(__file__).parent / "web" / "static"
template_path = Path(__file__).parent / "web" / "templates"

if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"✓ Static files mounted from: {static_path}")
else:
    logger.warning(f"⚠️  Static files directory not found: {static_path}")

if template_path.exists():
    templates = Jinja2Templates(directory=str(template_path))
    logger.info(f"✓ Templates loaded from: {template_path}")
else:
    logger.warning(f"⚠️  Templates directory not found: {template_path}")

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard."""
    if template_path.exists():
        return templates.TemplateResponse("dashboard.html", {"request": request})
    return {
        "message": "Odin Bitcoin Trading Bot", 
        "status": "running",
        "note": "Web interface not configured. Place HTML files in web/templates/"
    }

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
    import psutil
    
    try:
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

@app.get("/api/v1/data/current")
async def get_bitcoin_data():
    """Mock current Bitcoin data."""
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

@app.get("/api/v1/portfolio")
async def get_portfolio():
    """Mock portfolio data."""
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
            ]
        }
    }

@app.get("/api/v1/strategies/list")
async def get_strategies():
    """Mock strategies data."""
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
                "volatility": 12.1
            }
        ]
    }

@app.get("/api/v1/trading/history")
async def get_trading_history():
    """Mock trading history."""
    orders = []
    for i in range(10):
        side = random.choice(["buy", "sell"])
        amount = round(random.uniform(0.001, 0.1), 6)
        price = 45000 + random.uniform(-2000, 2000)
        pnl = round(random.uniform(-50, 50), 2)
        
        orders.append({
            "id": f"order_{i}",
            "timestamp": time.time() - (i * 3600),
            "strategy": random.choice(["ma_cross", "rsi_momentum", "bollinger_bands"]),
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

def main():
    """Run the application."""
    logger.info("🚀 Starting Odin Bitcoin Trading Bot")
    logger.info("📊 Dashboard: http://localhost:8000")
    logger.info("📖 API Docs: http://localhost:8000/docs")
    logger.info("💚 Health Check: http://localhost:8000/api/v1/health")
    
    # Check if web files exist
    if not template_path.exists():
        logger.warning("⚠️  Web templates not found. Create web/templates/dashboard.html for full UI")
    if not static_path.exists():
        logger.warning("⚠️  Static files not found. Create web/static/ directory for CSS/JS")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()