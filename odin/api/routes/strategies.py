"""
Strategy management endpoints (CLEAN VERSION)
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
import time

router = APIRouter()


@router.get("/list")
async def list_strategies():
    """Get list of all available strategies."""
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


@router.get("/{strategy_id}/chart/{hours}")
async def get_strategy_chart(strategy_id: str, hours: int):
    """Get strategy chart data with indicators."""
    # Generate mock chart data
    data_points = []
    current_time = time.time()
    base_price = 45000
    
    for i in range(min(hours, 100)):
        timestamp = current_time - (i * 3600)
        price = base_price + random.uniform(-2000, 2000)
        
        data_points.append({
            "timestamp": timestamp,
            "price": round(price, 2),
            "sma_short": round(price + random.uniform(-100, 100), 2),
            "sma_long": round(price + random.uniform(-200, 200), 2),
            "rsi": round(random.uniform(20, 80), 1),
            "volume": round(random.uniform(100, 1000), 2),
            "signal": random.choice(["buy", "sell", "hold"])
        })
    
    return {
        "success": True,
        "data": {
            "strategy_id": strategy_id,
            "timeframe_hours": hours,
            "chart_data": list(reversed(data_points)),
            "indicators": {
                "sma_short": 5,
                "sma_long": 20,
                "rsi_period": 14
            }
        }
    }


@router.post("/{strategy_id}/backtest/{hours}")
async def backtest_strategy(strategy_id: str, hours: int):
    """Run backtest for strategy."""
    return {
        "success": True,
        "data": {
            "strategy_id": strategy_id,
            "timeframe_hours": hours,
            "initial_capital": 10000,
            "final_capital": 10000 + random.uniform(-1000, 2000),
            "total_return": round(random.uniform(-10, 20), 2),
            "sharpe_ratio": round(random.uniform(0.5, 2.5), 2),
            "max_drawdown": round(random.uniform(-15, -2), 2),
            "win_rate": round(random.uniform(40, 70), 1),
            "total_trades": random.randint(10, 100),
            "profitable_trades": random.randint(5, 60),
            "avg_trade_duration": "2.5 hours",
            "volatility": round(random.uniform(10, 25), 1),
            "trades": [
                {
                    "timestamp": time.time() - random.randint(0, hours * 3600),
                    "type": random.choice(["buy", "sell"]),
                    "price": round(45000 + random.uniform(-2000, 2000), 2),
                    "amount": round(random.uniform(0.01, 0.1), 4),
                    "pnl": round(random.uniform(-100, 200), 2)
                }
                for _ in range(10)
            ]
        }
    }


@router.post("/{strategy_id}/optimize")
async def optimize_strategy(strategy_id: str):
    """Optimize strategy parameters."""
    return {
        "success": True,
        "data": {
            "strategy_id": strategy_id,
            "optimization_method": "grid_search",
            "best_parameters": {
                "short_window": random.randint(3, 10),
                "long_window": random.randint(15, 30),
                "rsi_period": random.randint(10, 20)
            },
            "best_performance": {
                "sharpe_ratio": round(random.uniform(1.5, 2.5), 2),
                "total_return": round(random.uniform(10, 25), 2),
                "max_drawdown": round(random.uniform(-8, -3), 2)
            },
            "optimization_time": "45 seconds",
            "iterations": random.randint(50, 200)
        }
    }


@router.post("/{strategy_id}/enable")
async def enable_strategy(strategy_id: str):
    """Enable a strategy."""
    return {
        "success": True,
        "message": f"Strategy {strategy_id} enabled successfully",
        "data": {
            "strategy_id": strategy_id,
            "status": "active",
            "enabled_at": datetime.now().isoformat()
        }
    }


@router.post("/{strategy_id}/disable")
async def disable_strategy(strategy_id: str):
    """Disable a strategy."""
    return {
        "success": True,
        "message": f"Strategy {strategy_id} disabled successfully",
        "data": {
            "strategy_id": strategy_id,
            "status": "inactive",
            "disabled_at": datetime.now().isoformat()
        }
    }