"""Health check endpoints for Odin trading bot."""

import time
from datetime import datetime

from fastapi import APIRouter, Depends
import structlog

from odin import __version__
from odin.api.dependencies import get_database, get_data_collector
from odin.core.models import HealthStatus, APIResponse

logger = structlog.get_logger(__name__)
router = APIRouter()

# Track startup time for uptime calculation
_startup_time = time.time()


@router.get("/health", response_model=APIResponse)
async def health_check(
    database=Depends(get_database),
    data_collector=Depends(get_data_collector)
):
    """Health check endpoint."""
    try:
        # Calculate uptime
        uptime = time.time() - _startup_time
        
        # Check database status
        try:
            stats = await database.get_data_stats()
            database_status = "connected"
            data_points_count = stats.get("total_records", 0)
            last_data_update = stats.get("newest_record")
        except Exception as e:
            database_status = f"error: {str(e)}"
            data_points_count = 0
            last_data_update = None
        
        # Check data collector status
        try:
            collector_stats = await data_collector.get_collection_stats()
            data_collector_status = "running"
        except Exception as e:
            data_collector_status = f"error: {str(e)}"
        
        # Determine overall status
        overall_status = "healthy"
        if database_status.startswith("error") or data_collector_status.startswith("error"):
            overall_status = "degraded"
        
        health_data = HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow(),
            uptime=uptime,
            version=__version__,
            database_status=database_status,
            data_collector_status=data_collector_status,
            last_data_update=datetime.fromisoformat(last_data_update) if last_data_update else None,
            data_points_count=data_points_count,
        )
        
        return APIResponse.success_response(
            data=health_data.dict(),
            message="Health check completed"
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return APIResponse.error_response(
            message="Health check failed",
            error_details={"error": str(e)}
        )


@router.get("/health/database", response_model=APIResponse)
async def database_health(database=Depends(get_database)):
    """Database-specific health check."""
    try:
        stats = await database.get_data_stats()
        return APIResponse.success_response(
            data=stats,
            message="Database health check completed"
        )
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return APIResponse.error_response(
            message="Database health check failed",
            error_details={"error": str(e)}
        )


@router.get("/health/collector", response_model=APIResponse)
async def collector_health(data_collector=Depends(get_data_collector)):
    """Data collector health check."""
    try:
        stats = await data_collector.get_collection_stats()
        return APIResponse.success_response(
            data=stats,
            message="Data collector health check completed"
        )
    except Exception as e:
        logger.error("Data collector health check failed", error=str(e))
        return APIResponse.error_response(
            message="Data collector health check failed",
            error_details={"error": str(e)}
        )