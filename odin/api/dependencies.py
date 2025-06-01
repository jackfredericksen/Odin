"""FastAPI dependencies for Odin trading bot."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException
import structlog

from odin.core.database import get_database as _get_database, Database
from odin.core.data_collector import DataCollector

logger = structlog.get_logger(__name__)

# Global instances
_data_collector: DataCollector | None = None


async def get_database() -> Database:
    """Dependency to get database instance."""
    try:
        return await _get_database()
    except Exception as e:
        logger.error("Failed to get database", error=str(e))
        raise HTTPException(status_code=500, detail="Database connection failed")


async def get_data_collector() -> DataCollector:
    """Dependency to get data collector instance."""
    global _data_collector
    
    if _data_collector is None:
        _data_collector = DataCollector()
        await _data_collector.startup()
    
    return _data_collector


async def get_current_user() -> dict:
    """Placeholder for authentication - implement as needed."""
    # TODO: Implement proper authentication
    return {"user_id": "anonymous", "permissions": ["read"]}