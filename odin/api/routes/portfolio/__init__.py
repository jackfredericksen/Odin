# odin/api/routes/portfolio/__init__.py
"""
Portfolio routes module
"""

from fastapi import APIRouter

from . import performance, rebalancing, risk, status

router = APIRouter()

# Include portfolio sub-routers
router.include_router(status.router, tags=["portfolio-status"])
router.include_router(performance.router, tags=["portfolio-performance"])
router.include_router(rebalancing.router, tags=["portfolio-rebalancing"])
router.include_router(risk.router, tags=["portfolio-risk"])

__all__ = ["router"]
