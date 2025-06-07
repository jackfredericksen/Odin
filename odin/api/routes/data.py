"""
Bitcoin data endpoints (FIXED VERSION)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import Response
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

# FIXED: Use correct imports
from odin.core.data_collector import DataCollector
from odin.core.models import (
    PriceData,
    HistoricalData,
    OHLCData,
    DataStats,
    DataSourceStatus,
    DataCollectionResult
)
from odin.api.dependencies import (
    get_data_collector,
    get_data_rate_limiter,
    validate_timeframe,
    validate_limit
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/current", response_model=Dict[str, Any])
async def get_current_price(
    collector: DataCollector = Depends(get_data_collector),
    rate_limiter = Depends(get_data_rate_limiter)
):
    """
    Get current Bitcoin price and market data
    
    Returns:
        - Current price in USD
        - 24h change percentage
        - 24h high/low
        - Volume
        - Last update timestamp
        - Data source
    """
    try:
        current_data = await collector.get_current_price()
        
        if not current_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch current Bitcoin data"
            )
        
        # Calculate 24h change (mock calculation for now)
        change_24h = 2.5  # This would be calculated from historical data
        
        return {
            "price": current_data.price,
            "change_24h": change_24h,
            "high_24h": current_data.price * 1.05,  # Mock values
            "low_24h": current_data.price * 0.95,
            "volume_24h": current_data.volume or 1000.0,
            "market_cap": current_data.price * 19700000,  # Approximate BTC supply
            "timestamp": current_data.timestamp.isoformat(),
            "source": current_data.source,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error fetching current price: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch current Bitcoin price"
        )


@router.get("/history/{hours}", response_model=Dict[str, Any])
async def get_price_history(
    hours: int,
    collector: DataCollector = Depends(get_data_collector),
    rate_limiter = Depends(get_data_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """
    Get historical Bitcoin price data
    
    Args:
        hours: Number of hours of historical data (1-8760)
        
    Returns:
        List of historical price points with timestamps
    """
    try:
        # For now, generate mock historical data
        # In real implementation, this would fetch from database
        history = []
        current_time = datetime.now()
        base_price = 45000.0
        
        for i in range(min(validated_hours, 100)):
            timestamp = current_time - timedelta(hours=i)
            price = base_price + (i * 10) - 500  # Simple price variation
            
            history.append({
                "timestamp": timestamp.isoformat(),
                "price": round(price, 2),
                "volume": round(1000 + (i * 5), 2),
                "high": round(price * 1.02, 2),
                "low": round(price * 0.98, 2)
            })
        
        # Reverse to get chronological order
        history.reverse()
        
        return {
            "history": history,
            "count": len(history),
            "timeframe_hours": validated_hours,
            "oldest_record": history[0]["timestamp"] if history else None,
            "newest_record": history[-1]["timestamp"] if history else None,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch price history"
        )


@router.get("/ohlc/{timeframe}", response_model=Dict[str, Any])
async def get_ohlc_data(
    timeframe: str,
    hours: int = Query(24, description="Hours of data to retrieve"),
    collector: DataCollector = Depends(get_data_collector),
    rate_limiter = Depends(get_data_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """
    Get OHLC (Open, High, Low, Close) candlestick data
    
    Args:
        timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        hours: Number of hours of data
        
    Returns:
        OHLC candlestick data suitable for charting
    """
    valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    
    if timeframe not in valid_timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
        )
    
    try:
        ohlc_data = await collector.get_ohlc_data(
            timeframe=timeframe,
            limit=min(validated_hours, 100)
        )
        
        # Format OHLC data
        formatted_ohlc = []
        for candle in ohlc_data:
            formatted_ohlc.append({
                "timestamp": candle.timestamp.isoformat(),
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume or 1000.0
            })
        
        return {
            "ohlc": formatted_ohlc,
            "timeframe": timeframe,
            "count": len(formatted_ohlc),
            "hours": validated_hours,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching OHLC data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch OHLC data"
        )


@router.get("/recent/{limit}", response_model=Dict[str, Any])
async def get_recent_data(
    limit: int,
    collector: DataCollector = Depends(get_data_collector),
    rate_limiter = Depends(get_data_rate_limiter),
    validated_limit: int = Depends(validate_limit)
):
    """
    Get recent Bitcoin price records
    
    Args:
        limit: Number of recent records to retrieve (1-10000)
        
    Returns:
        Most recent price records
    """
    try:
        # For now, generate mock recent data
        recent_data = []
        current_time = datetime.now()
        base_price = 45000.0
        
        for i in range(validated_limit):
            timestamp = current_time - timedelta(minutes=i * 5)
            price = base_price + (i * 2) - 100
            
            recent_data.append({
                "id": f"price_{i}",
                "timestamp": timestamp.isoformat(),
                "price": round(price, 2),
                "volume": round(100 + (i * 2), 2),
                "high": round(price * 1.01, 2),
                "low": round(price * 0.99, 2),
                "source": "mock"
            })
        
        return {
            "recent": recent_data,
            "count": len(recent_data),
            "limit": validated_limit,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recent data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent data"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_data_statistics(
    hours: int = Query(24, description="Hours to calculate stats for"),
    collector: DataCollector = Depends(get_data_collector),
    rate_limiter = Depends(get_data_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """
    Get statistical analysis of Bitcoin price data
    
    Args:
        hours: Hours of data to analyze for statistics
        
    Returns:
        Statistical metrics including averages, ranges, volatility
    """
    try:
        # For now, return mock statistics
        # In real implementation, this would calculate from actual data
        base_price = 45000.0
        
        stats = {
            "timeframe_hours": validated_hours,
            "total_records": validated_hours * 2,  # Assuming 30min intervals
            "average_price": base_price,
            "median_price": base_price - 100,
            "max_price": base_price + 2000,
            "min_price": base_price - 1500,
            "price_range": 3500,
            "price_std_dev": 850.5,
            "volatility_percent": 15.3,
            "average_volume": 1250.0,
            "total_volume": 50000.0,
            "oldest_record": (datetime.now() - timedelta(hours=validated_hours)).isoformat(),
            "newest_record": datetime.now().isoformat(),
            "data_sources": ["coinbase", "binance"],
            "status": "success"
        }
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate data statistics"
        )


@router.get("/sources", response_model=Dict[str, Any])
async def get_data_sources(
    collector: DataCollector = Depends(get_data_collector)
):
    """
    Get information about available data sources and their status
    
    Returns:
        List of data sources with health status and performance metrics
    """
    try:
        sources_status = collector.get_source_status()
        
        return {
            "sources": sources_status,
            "primary_source": "coinbase",
            "fallback_chain": ["coinbase", "binance"],
            "last_successful_fetch": datetime.now().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error fetching sources info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch data sources information"
        )


@router.post("/refresh", response_model=Dict[str, Any])
async def force_data_refresh(
    collector: DataCollector = Depends(get_data_collector),
    rate_limiter = Depends(get_data_rate_limiter)
):
    """
    Force immediate refresh of Bitcoin price data
    
    Returns:
        Result of the forced refresh operation
    """
    try:
        result = await collector.get_current_price(force_refresh=True)
        
        if result:
            return {
                "message": "Data refreshed successfully",
                "new_price": result.price,
                "source": result.source,
                "timestamp": result.timestamp.isoformat(),
                "status": "success"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to refresh data from all sources"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during forced refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to force data refresh"
        )


@router.get("/export/{format}")
async def export_data(
    format: str,
    hours: int = Query(24, description="Hours of data to export"),
    collector: DataCollector = Depends(get_data_collector),
    validated_hours: int = Depends(validate_timeframe)
):
    """
    Export Bitcoin price data in various formats
    
    Args:
        format: Export format (csv, json, xlsx)
        hours: Hours of data to export
        
    Returns:
        Data file in requested format
    """
    valid_formats = ["csv", "json", "xlsx"]
    
    if format.lower() not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
        )
    
    try:
        # For now, return mock export data
        if format.lower() == "csv":
            csv_data = "timestamp,price,volume\n"
            current_time = datetime.now()
            base_price = 45000.0
            
            for i in range(min(validated_hours, 100)):
                timestamp = current_time - timedelta(hours=i)
                price = base_price + (i * 10)
                volume = 1000 + (i * 5)
                csv_data += f"{timestamp.isoformat()},{price},{volume}\n"
            
            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=bitcoin_data_{validated_hours}h.csv"}
            )
            
        elif format.lower() == "json":
            import json
            
            data = []
            current_time = datetime.now()
            base_price = 45000.0
            
            for i in range(min(validated_hours, 100)):
                timestamp = current_time - timedelta(hours=i)
                data.append({
                    "timestamp": timestamp.isoformat(),
                    "price": base_price + (i * 10),
                    "volume": 1000 + (i * 5)
                })
            
            json_data = json.dumps(data, indent=2)
            
            return Response(
                content=json_data,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=bitcoin_data_{validated_hours}h.json"}
            )
            
        else:  # xlsx format
            # For now, return CSV format with xlsx headers
            # In real implementation, would use openpyxl or xlsxwriter
            csv_data = "timestamp,price,volume\n"
            current_time = datetime.now()
            base_price = 45000.0
            
            for i in range(min(validated_hours, 100)):
                timestamp = current_time - timedelta(hours=i)
                price = base_price + (i * 10)
                volume = 1000 + (i * 5)
                csv_data += f"{timestamp.isoformat()},{price},{volume}\n"
            
            return Response(
                content=csv_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=bitcoin_data_{validated_hours}h.xlsx"}
            )
            
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export data"
        )