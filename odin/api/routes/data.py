"""
Bitcoin data endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import Response
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from odin.core.data_collector import BitcoinDataCollector
from odin.core.models import (
    PriceData,
    HistoricalData,
    OHLCData,
    DataStats
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
    collector: BitcoinDataCollector = Depends(get_data_collector),
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
        current_data = await collector.get_current_data()
        
        if not current_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch current Bitcoin data"
            )
        
        return {
            "price": current_data.price,
            "change_24h": current_data.change_24h,
            "high_24h": current_data.high_24h,
            "low_24h": current_data.low_24h,
            "volume_24h": current_data.volume_24h,
            "market_cap": current_data.market_cap,
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
    collector: BitcoinDataCollector = Depends(get_data_collector),
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
        history = await collector.get_price_history(hours=validated_hours)
        
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No historical data available for {validated_hours} hours"
            )
        
        # Format history for response
        formatted_history = []
        for record in history:
            formatted_history.append({
                "timestamp": record.timestamp.isoformat(),
                "price": record.price,
                "volume": record.volume,
                "high": record.high,
                "low": record.low
            })
        
        return {
            "history": formatted_history,
            "count": len(formatted_history),
            "timeframe_hours": validated_hours,
            "oldest_record": formatted_history[-1]["timestamp"] if formatted_history else None,
            "newest_record": formatted_history[0]["timestamp"] if formatted_history else None,
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
    collector: BitcoinDataCollector = Depends(get_data_collector),
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
            hours=validated_hours
        )
        
        if not ohlc_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No OHLC data available for {timeframe} timeframe"
            )
        
        # Format OHLC data
        formatted_ohlc = []
        for candle in ohlc_data:
            formatted_ohlc.append({
                "timestamp": candle.timestamp.isoformat(),
                "open": candle.open_price,
                "high": candle.high_price,
                "low": candle.low_price,
                "close": candle.close_price,
                "volume": candle.volume
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
    collector: BitcoinDataCollector = Depends(get_data_collector),
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
        recent_data = await collector.get_recent_data(limit=validated_limit)
        
        if not recent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No recent data available"
            )
        
        # Format recent data
        formatted_data = []
        for record in recent_data:
            formatted_data.append({
                "id": record.id,
                "timestamp": record.timestamp.isoformat(),
                "price": record.price,
                "volume": record.volume,
                "high": record.high,
                "low": record.low,
                "source": record.source
            })
        
        return {
            "recent": formatted_data,
            "count": len(formatted_data),
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
    collector: BitcoinDataCollector = Depends(get_data_collector),
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
        stats = await collector.get_statistics(hours=validated_hours)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insufficient data for statistics calculation"
            )
        
        return {
            "timeframe_hours": validated_hours,
            "total_records": stats.total_records,
            "average_price": stats.average_price,
            "median_price": stats.median_price,
            "max_price": stats.max_price,
            "min_price": stats.min_price,
            "price_range": stats.price_range,
            "price_std_dev": stats.price_std_dev,
            "volatility_percent": stats.volatility_percent,
            "average_volume": stats.average_volume,
            "total_volume": stats.total_volume,
            "oldest_record": stats.oldest_record.isoformat() if stats.oldest_record else None,
            "newest_record": stats.newest_record.isoformat() if stats.newest_record else None,
            "data_sources": stats.data_sources,
            "status": "success"
        }
        
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
    collector: BitcoinDataCollector = Depends(get_data_collector)
):
    """
    Get information about available data sources and their status
    
    Returns:
        List of data sources with health status and performance metrics
    """
    try:
        sources_info = await collector.get_sources_status()
        
        return {
            "sources": sources_info,
            "primary_source": collector.get_primary_source(),
            "fallback_chain": collector.get_fallback_chain(),
            "last_successful_fetch": collector.get_last_successful_fetch().isoformat() if collector.get_last_successful_fetch() else None,
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
    collector: BitcoinDataCollector = Depends(get_data_collector),
    rate_limiter = Depends(get_data_rate_limiter)
):
    """
    Force immediate refresh of Bitcoin price data
    
    Returns:
        Result of the forced refresh operation
    """
    try:
        result = await collector.force_refresh()
        
        if result.success:
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
                detail=f"Failed to refresh data: {result.error}"
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
    collector: BitcoinDataCollector = Depends(get_data_collector),
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
        export_result = await collector.export_data(
            format=format.lower(),
            hours=validated_hours
        )
        
        if format.lower() == "csv":
            return Response(
                content=export_result,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=bitcoin_data_{validated_hours}h.csv"}
            )
        elif format.lower() == "json":
            return Response(
                content=export_result,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=bitcoin_data_{validated_hours}h.json"}
            )
        elif format.lower() == "xlsx":
            return Response(
                content=export_result,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=bitcoin_data_{validated_hours}h.xlsx"}
            )
            
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export data"
        )