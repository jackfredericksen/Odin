"""Data endpoints for Odin trading bot."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
import structlog

from odin.api.dependencies import get_database, get_data_collector
from odin.core.models import APIResponse, PriceData
from odin.core.exceptions import DatabaseError, DataCollectionError

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/current", response_model=APIResponse)
async def get_current_data(
    database=Depends(get_database),
    data_collector=Depends(get_data_collector)
):
    """Get current Bitcoin price and statistics."""
    try:
        # Try to get latest price from data collector first
        latest_price = await data_collector.get_latest_price()
        
        if not latest_price:
            # If no recent data, try to collect new data
            try:
                latest_price = await data_collector.collect_data()
            except DataCollectionError:
                # Fall back to database
                recent_prices = await database.get_recent_prices(limit=1)
                if recent_prices:
                    latest_price = recent_prices[0]
                else:
                    raise HTTPException(
                        status_code=503,
                        detail="No current data available"
                    )
        
        # Get data statistics
        stats = await database.get_data_stats()
        
        response_data = {
            "price": latest_price.price,
            "change_24h": latest_price.change_24h or 0.0,
            "high_24h": latest_price.high,
            "low_24h": latest_price.low,
            "volume_24h": latest_price.volume,
            "timestamp": latest_price.timestamp.isoformat(),
            "source": latest_price.source,
            "data_points": stats.get("total_records", 0),
        }
        
        return APIResponse.success_response(
            data=response_data,
            message="Current data retrieved successfully"
        )
        
    except Exception as e:
        logger.error("Failed to get current data", error=str(e))
        return APIResponse.error_response(
            message="Failed to retrieve current data",
            error_details={"error": str(e)}
        )


@router.get("/history/{hours}", response_model=APIResponse)
async def get_price_history(
    hours: int = Query(..., ge=1, le=168, description="Hours of history to retrieve"),
    database=Depends(get_database)
):
    """Get price history for specified hours."""
    try:
        df = await database.get_price_history(hours=hours)
        
        if df.empty:
            return APIResponse.success_response(
                data={"history": [], "count": 0},
                message="No historical data found"
            )
        
        # Convert to list of dictionaries
        history = []
        for timestamp, row in df.iterrows():
            history.append({
                "timestamp": timestamp.isoformat(),
                "price": float(row["price"]),
                "volume": float(row["volume"]) if row["volume"] else None,
                "source": row["source"],
            })
        
        return APIResponse.success_response(
            data={"history": history, "count": len(history)},
            message=f"Retrieved {len(history)} historical data points"
        )
        
    except Exception as e:
        logger.error("Failed to get price history", error=str(e), hours=hours)
        return APIResponse.error_response(
            message="Failed to retrieve price history",
            error_details={"error": str(e)}
        )


@router.get("/recent/{limit}", response_model=APIResponse)
async def get_recent_data(
    limit: int = Query(..., ge=1, le=1000, description="Number of recent records"),
    database=Depends(get_database)
):
    """Get recent price records."""
    try:
        recent_prices = await database.get_recent_prices(limit=limit)
        
        # Convert to response format
        recent_data = []
        for price_data in recent_prices:
            recent_data.append({
                "timestamp": price_data.timestamp.isoformat(),
                "price": price_data.price,
                "volume": price_data.volume,
                "high": price_data.high,
                "low": price_data.low,
                "change_24h": price_data.change_24h,
                "source": price_data.source,
            })
        
        return APIResponse.success_response(
            data={"recent": recent_data, "count": len(recent_data)},
            message=f"Retrieved {len(recent_data)} recent records"
        )
        
    except Exception as e:
        logger.error("Failed to get recent data", error=str(e), limit=limit)
        return APIResponse.error_response(
            message="Failed to retrieve recent data",
            error_details={"error": str(e)}
        )


@router.get("/stats", response_model=APIResponse)
async def get_stats(database=Depends(get_database)):
    """Get overall data statistics."""
    try:
        stats = await database.get_data_stats()
        
        # Calculate additional statistics if we have data
        if stats["total_records"] > 0:
            # Get recent prices to calculate averages
            recent_df = await database.get_price_history(hours=24)
            
            if not recent_df.empty:
                stats.update({
                    "avg_price_24h": float(recent_df["price"].mean()),
                    "max_price_24h": float(recent_df["price"].max()),
                    "min_price_24h": float(recent_df["price"].min()),
                    "price_range_24h": float(recent_df["price"].max() - recent_df["price"].min()),
                })
        
        return APIResponse.success_response(
            data=stats,
            message="Statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        return APIResponse.error_response(
            message="Failed to retrieve statistics",
            error_details={"error": str(e)}
        )


@router.post("/collect", response_model=APIResponse)
async def trigger_data_collection(data_collector=Depends(get_data_collector)):
    """Manually trigger data collection."""
    try:
        price_data = await data_collector.collect_data()
        
        if price_data:
            return APIResponse.success_response(
                data={
                    "price": price_data.price,
                    "source": price_data.source,
                    "timestamp": price_data.timestamp.isoformat(),
                },
                message="Data collection completed successfully"
            )
        else:
            return APIResponse.error_response(
                message="Data collection failed - no data retrieved"
            )
            
    except Exception as e:
        logger.error("Manual data collection failed", error=str(e))
        return APIResponse.error_response(
            message="Data collection failed",
            error_details={"error": str(e)}
        )