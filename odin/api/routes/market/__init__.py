# odin/api/routes/market/__init__.py
"""
Market routes module
"""

from fastapi import APIRouter

from . import alerts, depth, fees, regime

router = APIRouter()

# Include market sub-routers
router.include_router(regime.router, tags=["market-regime"])
router.include_router(alerts.router, tags=["market-alerts"])
router.include_router(depth.router, tags=["market-depth"])
router.include_router(fees.router, tags=["market-fees"])

__all__ = ["router"]
