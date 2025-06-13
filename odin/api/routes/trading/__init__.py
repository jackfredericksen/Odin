# odin/api/routes/trading/__init__.py
"""
Trading routes module
"""

from fastapi import APIRouter

from . import automation, execution, orders, positions

router = APIRouter()

# Include trading sub-routers
router.include_router(execution.router, tags=["trade-execution"])
router.include_router(orders.router, tags=["order-management"])
router.include_router(positions.router, tags=["position-management"])
router.include_router(automation.router, tags=["auto-trading"])

__all__ = ["router"]
