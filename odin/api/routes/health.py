"""
Health check endpoints
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict

import psutil
from fastapi import APIRouter, Depends, HTTPException, status

from odin.api.dependencies import get_data_collector
from odin.config import settings
from odin.core.data_collector import BitcoinDataCollector
from odin.core.database import DatabaseManager
from odin.utils.cache import get_cache_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Store startup time
startup_time = datetime.utcnow()


@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """
    Basic health check endpoint

    Returns:
        Basic health status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "odin-bitcoin-bot",
    }


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check(
    collector: BitcoinDataCollector = Depends(get_data_collector),
):
    """
    Detailed health check with system metrics

    Returns:
        Comprehensive health status including system metrics
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Calculate uptime
        uptime = datetime.utcnow() - startup_time

        # Database health
        db_health = await check_database_health()

        # Data collection health
        data_health = await check_data_collection_health(collector)

        # External APIs health
        api_health = await check_external_apis_health(collector)

        # Overall health score (0-100)
        health_components = [
            db_health["healthy"],
            data_health["healthy"],
            api_health["healthy"],
            cpu_percent < 90,  # CPU not overloaded
            memory.percent < 90,  # Memory not overloaded
            disk.percent < 90,  # Disk not full
        ]

        health_score = sum(health_components) / len(health_components) * 100
        overall_healthy = health_score >= 80

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "health_score": round(health_score, 1),
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime),
            "version": "1.0.0",
            "environment": settings.ODIN_ENV,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
            },
            "database": db_health,
            "data_collection": data_health,
            "external_apis": api_health,
            "checks_passed": sum(health_components),
            "total_checks": len(health_components),
        }

    except Exception as e:
        logger.error(f"Error in detailed health check: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/database", response_model=Dict[str, Any])
async def check_database_health():
    """
    Check database connectivity and performance

    Returns:
        Database health status and metrics
    """
    try:
        db_manager = DatabaseManager()
        start_time = time.time()

        # Test database connection
        with db_manager.get_session() as db:
            # Simple query to test connectivity
            result = db.execute("SELECT 1").fetchone()

        response_time = (time.time() - start_time) * 1000  # Convert to ms

        # Check database file size (for SQLite)
        db_size_mb = 0
        try:
            import os

            if os.path.exists(db_manager.db_path):
                db_size_mb = os.path.getsize(db_manager.db_path) / (1024 * 1024)
        except:
            pass

        return {
            "healthy": True,
            "response_time_ms": round(response_time, 2),
            "database_size_mb": round(db_size_mb, 2),
            "connection_pool_size": getattr(db_manager.engine.pool, "size", "N/A"),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "connected",
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "disconnected",
        }


@router.get("/data-collection", response_model=Dict[str, Any])
async def check_data_collection_health(
    collector: BitcoinDataCollector = Depends(get_data_collector),
):
    """
    Check data collection system health

    Returns:
        Data collection health status and metrics
    """
    try:
        # Check last successful data fetch
        last_fetch = collector.get_last_successful_fetch()

        if not last_fetch:
            return {
                "healthy": False,
                "error": "No successful data fetches recorded",
                "last_fetch": None,
                "status": "no_data",
            }

        # Check if data is recent (within last 5 minutes)
        time_since_last = datetime.utcnow() - last_fetch
        is_recent = time_since_last < timedelta(minutes=5)

        # Get data collection stats
        try:
            stats = await collector.get_collection_stats()
        except:
            stats = {}

        # Check data sources status
        sources_status = await collector.get_sources_status()
        healthy_sources = sum(
            1 for source in sources_status if source.get("healthy", False)
        )

        return {
            "healthy": is_recent and healthy_sources > 0,
            "last_fetch": last_fetch.isoformat(),
            "minutes_since_last": round(time_since_last.total_seconds() / 60, 1),
            "is_recent": is_recent,
            "healthy_sources": healthy_sources,
            "total_sources": len(sources_status),
            "collection_stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active" if is_recent else "stale",
        }

    except Exception as e:
        logger.error(f"Data collection health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
        }


@router.get("/external-apis", response_model=Dict[str, Any])
async def check_external_apis_health(
    collector: BitcoinDataCollector = Depends(get_data_collector),
):
    """
    Check external API health and response times

    Returns:
        External API health status for all data sources
    """
    try:
        api_sources = ["coindesk", "blockchain_info", "coingecko", "cryptocompare"]

        api_health = {}
        overall_healthy = False

        for source in api_sources:
            try:
                start_time = time.time()
                health_check = await collector.check_api_health(source)
                response_time = (time.time() - start_time) * 1000

                api_health[source] = {
                    "healthy": health_check.get("healthy", False),
                    "response_time_ms": round(response_time, 2),
                    "status_code": health_check.get("status_code"),
                    "error": health_check.get("error"),
                    "last_successful": health_check.get("last_successful"),
                }

                if health_check.get("healthy", False):
                    overall_healthy = True

            except Exception as e:
                api_health[source] = {
                    "healthy": False,
                    "error": str(e),
                    "response_time_ms": None,
                }

        # Calculate average response time for healthy APIs
        healthy_times = [
            api["response_time_ms"]
            for api in api_health.values()
            if api.get("healthy") and api.get("response_time_ms")
        ]
        avg_response_time = (
            sum(healthy_times) / len(healthy_times) if healthy_times else 0
        )

        return {
            "healthy": overall_healthy,
            "apis": api_health,
            "healthy_count": sum(
                1 for api in api_health.values() if api.get("healthy")
            ),
            "total_count": len(api_sources),
            "average_response_time_ms": round(avg_response_time, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "operational" if overall_healthy else "degraded",
        }

    except Exception as e:
        logger.error(f"External APIs health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
        }


@router.get("/metrics", response_model=Dict[str, Any])
async def get_system_metrics():
    """
    Get detailed system performance metrics

    Returns:
        Comprehensive system metrics for monitoring
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Disk metrics
        disk_usage = psutil.disk_usage("/")

        # Network metrics (if available)
        try:
            network = psutil.net_io_counters()
            network_stats = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            }
        except:
            network_stats = {}

        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()

        # Uptime
        uptime = datetime.utcnow() - startup_time

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency_mhz": cpu_freq.current if cpu_freq else None,
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
            },
            "swap": {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "percent": swap.percent,
            },
            "disk": {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "percent": round((disk_usage.used / disk_usage.total) * 100, 1),
            },
            "network": network_stats,
            "process": {
                "memory_rss_mb": round(process_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
            },
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system metrics",
        )


@router.get("/readiness", response_model=Dict[str, Any])
async def readiness_check(
    collector: BitcoinDataCollector = Depends(get_data_collector),
):
    """
    Kubernetes-style readiness probe

    Returns:
        Whether the service is ready to handle requests
    """
    try:
        # Check if essential components are ready
        checks = {"database": False, "data_collection": False, "external_apis": False}

        # Database check
        try:
            db_manager = DatabaseManager()
            with db_manager.get_session() as db:
                db.execute("SELECT 1").fetchone()
            checks["database"] = True
        except:
            pass

        # Data collection check
        try:
            last_fetch = collector.get_last_successful_fetch()
            if last_fetch and (datetime.utcnow() - last_fetch) < timedelta(minutes=10):
                checks["data_collection"] = True
        except:
            pass

        # External APIs check
        try:
            sources_status = await collector.get_sources_status()
            healthy_sources = sum(
                1 for source in sources_status if source.get("healthy", False)
            )
            if healthy_sources > 0:
                checks["external_apis"] = True
        except:
            pass

        # Service is ready if at least database and one API source work
        is_ready = checks["database"] and checks["external_apis"]

        return {
            "ready": is_ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ready" if is_ready else "not_ready",
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
        }


@router.get("/liveness", response_model=Dict[str, Any])
async def liveness_check():
    """
    Kubernetes-style liveness probe

    Returns:
        Whether the service is alive and not deadlocked
    """
    try:
        # Simple check to verify the service is responsive
        start_time = time.time()

        # Perform a simple async operation
        await asyncio.sleep(0.001)

        response_time = (time.time() - start_time) * 1000

        # Check if response time is reasonable (< 5 seconds)
        is_alive = response_time < 5000

        return {
            "alive": is_alive,
            "response_time_ms": round(response_time, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "alive" if is_alive else "slow_response",
        }

    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return {
            "alive": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
        }


@router.get("/cache", response_model=Dict[str, Any])
async def get_cache_stats():
    """
    Get API cache statistics and performance metrics.

    Returns:
        Cache hit rate, size, and other performance metrics
    """
    try:
        cache = get_cache_manager()
        stats = cache.get_stats()

        return {
            "success": True,
            "data": {
                "cache_size": stats["size"],
                "max_size": stats["max_size"],
                "utilization_pct": round((stats["size"] / stats["max_size"]) * 100, 2),
                "total_requests": stats["total_requests"],
                "cache_hits": stats["hits"],
                "cache_misses": stats["misses"],
                "hit_rate_pct": stats["hit_rate"],
                "evictions": stats["evictions"],
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
        }

    except Exception as e:
        logger.error(f"Cache stats check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
        }
