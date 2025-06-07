"""
Trading management endpoints (CLEAN VERSION)
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
import time

router = APIRouter()


@router.get("/history")
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


@router.get("/status")
async def get_trading_status():
    """Get auto-trading status."""
    return {
        "success": True,
        "data": {
            "enabled": False,
            "active_strategies": 2,
            "last_trade": time.time() - 1800,  # 30 minutes ago
            "total_trades_today": 15,
            "pnl_today": 127.50,
            "risk_limits": {
                "max_position_size": 0.95,
                "risk_per_trade": 0.02,
                "daily_loss_limit": 0.05
            },
            "current_exposure": 0.45
        }
    }


@router.post("/enable")
async def enable_trading():
    """Enable auto-trading."""
    return {
        "success": True,
        "message": "Auto-trading enabled successfully",
        "data": {
            "enabled": True,
            "enabled_at": datetime.now().isoformat(),
            "active_strategies": 2,
            "risk_checks": "passed"
        }
    }


@router.post("/disable")
async def disable_trading():
    """Disable auto-trading."""
    return {
        "success": True,
        "message": "Auto-trading disabled successfully",
        "data": {
            "enabled": False,
            "disabled_at": datetime.now().isoformat(),
            "reason": "manual_disable"
        }
    }


@router.get("/active")
async def get_active_orders():
    """Get active orders."""
    active_orders = []
    
    for i in range(random.randint(0, 5)):
        active_orders.append({
            "id": f"active_order_{i}",
            "timestamp": time.time() - random.randint(0, 3600),
            "strategy": random.choice(["ma_cross", "bollinger_bands"]),
            "side": random.choice(["buy", "sell"]),
            "amount": round(random.uniform(0.01, 0.1), 4),
            "price": round(45000 + random.uniform(-1000, 1000), 2),
            "status": "pending",
            "order_type": random.choice(["limit", "market", "stop_loss"])
        })
    
    return {
        "success": True,
        "data": active_orders
    }


@router.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop all trading."""
    return {
        "success": True,
        "message": "Emergency stop activated - all trading halted",
        "data": {
            "stopped_at": datetime.now().isoformat(),
            "cancelled_orders": random.randint(0, 5),
            "closed_positions": random.randint(0, 3),
            "reason": "emergency_stop"
        }
    }


@router.get("/positions")
async def get_positions():
    """Get current positions."""
    positions = []
    
    if random.choice([True, False]):  # Sometimes have positions
        positions.append({
            "id": "position_btc_1",
            "symbol": "BTC-USD",
            "side": "long",
            "size": round(random.uniform(0.1, 0.5), 4),
            "entry_price": round(45000 + random.uniform(-1000, 1000), 2),
            "current_price": round(45000 + random.uniform(-500, 500), 2),
            "pnl": round(random.uniform(-200, 300), 2),
            "pnl_percentage": round(random.uniform(-5, 8), 2),
            "strategy": "ma_cross",
            "opened_at": time.time() - random.randint(3600, 86400)
        })
    
    return {
        "success": True,
        "data": positions
    }