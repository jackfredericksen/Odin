"""
Bitcoin data endpoints (CLEAN VERSION)
"""

from fastapi import APIRouter, HTTPException, Query, status, Response
from typing import Dict, Any
from datetime import datetime, timedelta
import random
import time
import json

router = APIRouter()


@router.get("/current", response_model=Dict[str, Any])
async def get_current_price():
    """Get current Bitcoin price and market data."""
    try:
        base_price = 45000
        current_price = base_price + random.uniform(-2000, 2000)
        
        return {
            "success": True,
            "price": round(current_price, 2),
            "change_24h": round(random.uniform(-5, 5), 2),
            "high_24h": round(current_price * 1.05, 2),
            "low_24h": round(current_price * 0.95, 2),
            "volume_24h": round(random.uniform(800, 1200), 2),
            "market_cap": round(current_price * 19700000, 0),
            "timestamp": datetime.now().isoformat(),
            "source": "mock",
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch current Bitcoin price"
        )


@router.get("/history/{hours}", response_model=Dict[str, Any])
async def get_price_history(hours: int):
    """Get historical Bitcoin price data."""
    # Validate hours
    if hours < 1 or hours > 8760:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hours must be between 1 and 8760"
        )
    
    try:
        history = []
        current_time = time.time()
        base_price = 45000.0
        
        for i in range(min(hours, 100)):
            timestamp = current_time - (i * 3600)
            price = base_price + (i * 10) - 500
            
            history.append({
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "price": round(price, 2),
                "volume": round(1000 + (i * 5), 2),
                "high": round(price * 1.02, 2),
                "low": round(price * 0.98, 2)
            })
        
        # Reverse to get chronological order
        history.reverse()
        
        return {
            "success": True,
            "history": history,
            "count": len(history),
            "timeframe_hours": hours,
            "oldest_record": history[0]["timestamp"] if history else None,
            "newest_record": history[-1]["timestamp"] if history else None,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch price history"
        )


@router.get("/ohlc/{timeframe}", response_model=Dict[str, Any])
async def get_ohlc_data(timeframe: str, hours: int = Query(24, description="Hours of data to retrieve")):
    """Get OHLC (Open, High, Low, Close) candlestick data."""
    valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    
    if timeframe not in valid_timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
        )
    
    if hours < 1 or hours > 8760:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hours must be between 1 and 8760"
        )
    
    try:
        ohlc_data = []
        current_time = time.time()
        base_price = 45000
        
        for i in range(min(hours, 100)):
            timestamp = current_time - (i * 3600)
            open_price = base_price + random.uniform(-1000, 1000)
            high_price = open_price + random.uniform(0, 500)
            low_price = open_price - random.uniform(0, 500)
            close_price = open_price + random.uniform(-300, 300)
            
            ohlc_data.append({
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": round(random.uniform(100, 500), 2)
            })
        
        return {
            "success": True,
            "ohlc": list(reversed(ohlc_data)),
            "timeframe": timeframe,
            "count": len(ohlc_data),
            "hours": hours,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch OHLC data"
        )


@router.get("/recent/{limit}", response_model=Dict[str, Any])
async def get_recent_data(limit: int):
    """Get recent Bitcoin price records."""
    if limit < 1 or limit > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 10000"
        )
    
    try:
        recent_data = []
        current_time = time.time()
        base_price = 45000.0
        
        for i in range(limit):
            timestamp = current_time - (i * 300)  # 5-minute intervals
            price = base_price + (i * 2) - 100
            
            recent_data.append({
                "id": f"price_{i}",
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "price": round(price, 2),
                "volume": round(100 + (i * 2), 2),
                "high": round(price * 1.01, 2),
                "low": round(price * 0.99, 2),
                "source": "mock"
            })
        
        return {
            "success": True,
            "recent": recent_data,
            "count": len(recent_data),
            "limit": limit,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent data"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_data_statistics(hours: int = Query(24, description="Hours to calculate stats for")):
    """Get statistical analysis of Bitcoin price data."""
    if hours < 1 or hours > 8760:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hours must be between 1 and 8760"
        )
    
    try:
        base_price = 45000.0
        
        stats = {
            "success": True,
            "timeframe_hours": hours,
            "total_records": hours * 2,
            "average_price": base_price,
            "median_price": base_price - 100,
            "max_price": base_price + 2000,
            "min_price": base_price - 1500,
            "price_range": 3500,
            "price_std_dev": 850.5,
            "volatility_percent": 15.3,
            "average_volume": 1250.0,
            "total_volume": 50000.0,
            "oldest_record": (datetime.now() - timedelta(hours=hours)).isoformat(),
            "newest_record": datetime.now().isoformat(),
            "data_sources": ["mock"],
            "status": "success"
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate data statistics"
        )


@router.get("/sources", response_model=Dict[str, Any])
async def get_data_sources():
    """Get information about available data sources and their status."""
    try:
        return {
            "success": True,
            "sources": {
                "mock": {
                    "enabled": True,
                    "healthy": True,
                    "priority": 99,
                    "error_count": 0,
                    "last_update": datetime.now().isoformat()
                }
            },
            "primary_source": "mock",
            "fallback_chain": ["mock"],
            "last_successful_fetch": datetime.now().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch data sources information"
        )


@router.post("/refresh", response_model=Dict[str, Any])
async def force_data_refresh():
    """Force immediate refresh of Bitcoin price data."""
    try:
        current_price = 45000 + random.uniform(-2000, 2000)
        
        return {
            "success": True,
            "message": "Data refreshed successfully",
            "new_price": round(current_price, 2),
            "source": "mock",
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to force data refresh"
        )


@router.get("/export/{format}")
async def export_data(format: str, hours: int = Query(24, description="Hours of data to export")):
    """Export Bitcoin price data in various formats."""
    valid_formats = ["csv", "json", "xlsx"]
    
    if format.lower() not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
        )
    
    if hours < 1 or hours > 8760:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hours must be between 1 and 8760"
        )
    
    try:
        if format.lower() == "csv":
            csv_data = "timestamp,price,volume\n"
            current_time = time.time()
            base_price = 45000.0
            
            for i in range(min(hours, 100)):
                timestamp = datetime.fromtimestamp(current_time - (i * 3600)).isoformat()
                price = base_price + (i * 10)
                volume = 1000 + (i * 5)
                csv_data += f"{timestamp},{price},{volume}\n"
            
            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=bitcoin_data_{hours}h.csv"}
            )
            
        elif format.lower() == "json":
            data = []
            current_time = time.time()
            base_price = 45000.0
            
            for i in range(min(hours, 100)):
                timestamp = datetime.fromtimestamp(current_time - (i * 3600)).isoformat()
                data.append({
                    "timestamp": timestamp,
                    "price": base_price + (i * 10),
                    "volume": 1000 + (i * 5)
                })
            
            json_data = json.dumps(data, indent=2)
            
            return Response(
                content=json_data,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=bitcoin_data_{hours}h.json"}
            )
            
        else:  # xlsx format - return CSV with xlsx headers for now
            csv_data = "timestamp,price,volume\n"
            current_time = time.time()
            base_price = 45000.0
            
            for i in range(min(hours, 100)):
                timestamp = datetime.fromtimestamp(current_time - (i * 3600)).isoformat()
                price = base_price + (i * 10)
                volume = 1000 + (i * 5)
                csv_data += f"{timestamp},{price},{volume}\n"
            
            return Response(
                content=csv_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=bitcoin_data_{hours}h.xlsx"}
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export data"
        )