"""FastAPI application factory for Odin trading bot."""

from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from odin import __version__, __description__
from odin.api.middleware import RateLimitMiddleware, LoggingMiddleware
from odin.api.routes import data, strategies, health
from odin.config import get_settings
from odin.core.exceptions import OdinException

logger = structlog.get_logger(__name__)


def create_app(lifespan: Callable = None) -> FastAPI:
    """Create and configure FastAPI application."""
    
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="Odin Trading Bot API",
        description=__description__,
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(LoggingMiddleware)
    
    if settings.rate_limit_calls > 0:
        app.add_middleware(
            RateLimitMiddleware,
            calls=settings.rate_limit_calls,
            period=settings.rate_limit_period,
        )
    
    # Add exception handlers
    @app.exception_handler(OdinException)
    async def odin_exception_handler(request: Request, exc: OdinException):
        """Handle Odin-specific exceptions."""
        logger.error("Odin exception occurred",
                    error=exc.message,
                    error_code=exc.error_code,
                    details=exc.details,
                    path=request.url.path)
        
        return JSONResponse(
            status_code=400,
            content=exc.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error("Unhandled exception occurred",
                    error=str(exc),
                    error_type=type(exc).__name__,
                    path=request.url.path)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An internal server error occurred",
                "details": {"error_type": type(exc).__name__}
            }
        )
    
    # Include routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(data.router, prefix="/api", tags=["data"])
    app.include_router(strategies.router, prefix="/api", tags=["strategies"])
    
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint - serve dashboard."""
        from fastapi.responses import FileResponse
        import os
        
        # Try to serve dashboard.html
        dashboard_path = os.path.join("web", "templates", "dashboard.html")
        if os.path.exists(dashboard_path):
            return FileResponse(dashboard_path)
        
        return {
            "message": "Odin Trading Bot API",
            "version": __version__,
            "docs": "/docs",
            "status": "running"
        }
    
    return app