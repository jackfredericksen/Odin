"""
Strategy routes module
"""

from fastapi import APIRouter
from . import analysis, backtesting, comparison, optimization, signals, management

router = APIRouter()

# Include strategy sub-routers
router.include_router(analysis.router, tags=["strategy-analysis"])
router.include_router(backtesting.router, tags=["strategy-backtesting"])
router.include_router(comparison.router, tags=["strategy-comparison"])
router.include_router(optimization.router, tags=["strategy-optimization"])
router.include_router(signals.router, tags=["strategy-signals"])
router.include_router(management.router, tags=["strategy-management"])

__all__ = ["router"]