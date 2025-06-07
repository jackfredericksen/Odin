# odin/api/app.py
"""
Enhanced FastAPI application with AI route integration
Main API application setup with all routes and middleware
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

# Import existing routes
from .routes import health, data
from .routes.strategies import analysis, backtesting, comparison, optimization, signals, management
from .routes.trading import execution, orders, positions, automation
from .routes.portfolio import status, performance, rebalancing, risk
from .routes.market import regime, alerts, depth, fees

# Import new AI routes
from .routes.ai import regime as ai_regime

# Import middleware and dependencies
from .middleware import RateLimitMiddleware, SecurityHeadersMiddleware, LoggingMiddleware

logger = logging.getLogger(__name__)

def create_custom_openapi(app: FastAPI):
    """Create custom OpenAPI schema with AI documentation"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Odin Bitcoin Trading Bot API",
        version="2.0.0",
        description="""
        ## Professional Bitcoin Trading Bot with AI-Powered Features
        
        ### 🚀 Core Features
        - **Real-time Bitcoin Trading** with multiple exchange support
        - **Advanced Technical Analysis** with 40+ indicators
        - **AI-Powered Regime Detection** using machine learning
        - **Adaptive Strategy Selection** based on market conditions
        - **Professional Risk Management** with automated controls
        - **Portfolio Optimization** with performance tracking
        
        ### 🤖 AI Features (NEW)
        - **Market Regime Detection** - Automatically identifies market conditions
        - **Adaptive Strategies** - Switches strategies based on detected regimes
        - **Intelligent Position Sizing** - AI-driven risk management
        - **Performance Analytics** - ML-powered performance insights
        
        ### 📊 API Categories
        - **Health & Monitoring** - System status and health checks
        - **Data Collection** - Bitcoin price and market data
        - **Strategy Management** - Trading strategy configuration and analysis
        - **Live Trading** - Order execution and position management
        - **Portfolio Management** - Portfolio tracking and optimization
        - **Market Analysis** - Market data and regime detection
        - **AI Features** - Regime detection and adaptive strategies
        
        ### 🔐 Authentication
        Most endpoints require JWT authentication. Obtain a token via the authentication endpoints.
        
        ### 📈 Rate Limits
        - Data endpoints: 60 requests/minute
        - Strategy endpoints: 20 requests/minute  
        - Trading endpoints: 30 requests/minute
        - AI endpoints: 40 requests/minute
        - General endpoints: 100 requests/minute
        """,
        routes=app.routes,
    )
    
    # Add custom sections to OpenAPI
    openapi_schema["info"]["x-logo"] = {
        "url": "/static/images/logo.png"
    }
    
    # Add AI-specific tags
    openapi_schema["tags"] = [
        {
            "name": "Health & Monitoring",
            "description": "System health checks and monitoring endpoints"
        },
        {
            "name": "Bitcoin Data",
            "description": "Real-time and historical Bitcoin market data"
        },
        {
            "name": "Strategy Analysis", 
            "description": "Trading strategy analysis and backtesting"
        },
        {
            "name": "Live Trading",
            "description": "Live trade execution and order management"
        },
        {
            "name": "Portfolio Management",
            "description": "Portfolio tracking and performance analytics"
        },
        {
            "name": "Market Analysis",
            "description": "Market regime detection and analysis"
        },
        {
            "name": "AI Regime Detection",
            "description": "🤖 AI-powered market regime detection and adaptive strategies"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def create_app(lifespan: Optional[asynccontextmanager] = None) -> FastAPI:
    """
    Create and configure FastAPI application with all features
    
    Args:
        lifespan: Optional lifespan context manager for startup/shutdown
        
    Returns:
        Configured FastAPI application
    """
    
    app = FastAPI(
        title="Odin Bitcoin Trading Bot",
        description="Professional Bitcoin Trading Bot with AI-Powered Regime Detection",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add custom OpenAPI schema
    app.openapi = lambda: create_custom_openapi(app)
    
    # Add security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly for production
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"]  # Configure properly for production
    )
    
    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware)
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Include health and monitoring routes
    app.include_router(
        health.router, 
        prefix="/api/v1",
        tags=["Health & Monitoring"]
    )
    
    # Include data collection routes
    app.include_router(
        data.router, 
        prefix="/api/v1",
        tags=["Bitcoin Data"]
    )
    
    # Include strategy routes
    app.include_router(
        analysis.router, 
        prefix="/api/v1/strategies",
        tags=["Strategy Analysis"]
    )
    app.include_router(
        backtesting.router, 
        prefix="/api/v1/strategies",
        tags=["Strategy Analysis"]
    )
    app.include_router(
        comparison.router, 
        prefix="/api/v1/strategies",
        tags=["Strategy Analysis"]
    )
    app.include_router(
        optimization.router, 
        prefix="/api/v1/strategies",
        tags=["Strategy Analysis"]
    )
    app.include_router(
        signals.router, 
        prefix="/api/v1/strategies",
        tags=["Strategy Analysis"]
    )
    app.include_router(
        management.router, 
        prefix="/api/v1/strategies",
        tags=["Strategy Analysis"]
    )
    
    # Include trading routes
    app.include_router(
        execution.router, 
        prefix="/api/v1/trading",
        tags=["Live Trading"]
    )
    app.include_router(
        orders.router, 
        prefix="/api/v1/trading",
        tags=["Live Trading"]
    )
    app.include_router(
        positions.router, 
        prefix="/api/v1/trading",
        tags=["Live Trading"]
    )
    app.include_router(
        automation.router, 
        prefix="/api/v1/trading",
        tags=["Live Trading"]
    )
    
    # Include portfolio routes
    app.include_router(
        status.router, 
        prefix="/api/v1/portfolio",
        tags=["Portfolio Management"]
    )
    app.include_router(
        performance.router, 
        prefix="/api/v1/portfolio",
        tags=["Portfolio Management"]
    )
    app.include_router(
        rebalancing.router, 
        prefix="/api/v1/portfolio",
        tags=["Portfolio Management"]
    )
    app.include_router(
        risk.router, 
        prefix="/api/v1/portfolio",
        tags=["Portfolio Management"]
    )
    
    # Include market routes
    app.include_router(
        regime.router, 
        prefix="/api/v1/market",
        tags=["Market Analysis"]
    )
    app.include_router(
        alerts.router, 
        prefix="/api/v1/market",
        tags=["Market Analysis"]
    )
    app.include_router(
        depth.router, 
        prefix="/api/v1/market",
        tags=["Market Analysis"]
    )
    app.include_router(
        fees.router, 
        prefix="/api/v1/market",
        tags=["Market Analysis"]
    )
    
    # NEW: Include AI routes
    app.include_router(
        ai_regime.router, 
        prefix="/api/v1",
        tags=["AI Regime Detection"]
    )
    
    # Global exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with detailed error messages"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "type": "HTTPException",
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                    "path": str(request.url),
                    "method": request.method
                },
                "timestamp": time.time()
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
        logger.error(f"Request: {request.method} {request.url}")
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "type": "InternalServerError",
                    "status_code": 500,
                    "detail": "An internal server error occurred",
                    "path": str(request.url),
                    "method": request.method
                },
                "timestamp": time.time()
            }
        )
    
    # Root endpoint with enhanced information
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information and AI status"""
        return {
            "message": "🚀 Odin Bitcoin Trading Bot with AI",
            "version": "2.0.0",
            "description": "Professional Bitcoin trading bot with AI-powered regime detection",
            "features": {
                "core": [
                    "Real-time Bitcoin trading",
                    "Advanced technical analysis",
                    "Professional risk management",
                    "Portfolio optimization",
                    "Live trading execution"
                ],
                "ai": [
                    "Market regime detection",
                    "Adaptive strategy selection", 
                    "Intelligent position sizing",
                    "Performance analytics"
                ]
            },
            "api": {
                "documentation": "/docs",
                "alternative_docs": "/redoc",
                "openapi_schema": "/openapi.json",
                "health_check": "/api/v1/health"
            },
            "endpoints": {
                "health": "/api/v1/health",
                "current_regime": "/api/v1/ai/regime/current",
                "adaptive_strategies": "/api/v1/ai/strategies/adaptive",
                "bitcoin_data": "/api/v1/data/current",
                "portfolio_status": "/api/v1/portfolio/"
            },
            "status": "🟢 Online and Ready",
            "timestamp": time.time()
        }
    
    # API information endpoint
    @app.get("/api", tags=["Root"])
    async def api_info():
        """API information and statistics"""
        
        # Count routes by category
        route_counts = {
            "health": len([r for r in app.routes if "/health" in str(r.path)]),
            "data": len([r for r in app.routes if "/data" in str(r.path)]),
            "strategies": len([r for r in app.routes if "/strategies" in str(r.path)]),
            "trading": len([r for r in app.routes if "/trading" in str(r.path)]),
            "portfolio": len([r for r in app.routes if "/portfolio" in str(r.path)]),
            "market": len([r for r in app.routes if "/market" in str(r.path)]),
            "ai": len([r for r in app.routes if "/ai" in str(r.path)])
        }
        
        total_routes = sum(route_counts.values())
        
        return {
            "api_version": "2.0.0",
            "total_endpoints": total_routes,
            "endpoint_categories": route_counts,
            "features": {
                "authentication": "JWT-based",
                "rate_limiting": "Enabled",
                "cors": "Configured",
                "documentation": "OpenAPI 3.0",
                "ai_features": "Market regime detection & adaptive strategies"
            },
            "rate_limits": {
                "general": "100/minute",
                "data": "60/minute",
                "strategies": "20/minute", 
                "trading": "30/minute",
                "ai": "40/minute"
            },
            "supported_formats": ["JSON"],
            "websocket_support": "Available for real-time data",
            "last_updated": time.time()
        }
    
    # API health summary
    @app.get("/api/v1/status", tags=["Health & Monitoring"])
    async def api_status():
        """Quick API status check"""
        return {
            "status": "healthy",
            "version": "2.0.0",
            "uptime": time.time(),
            "features": {
                "trading_engine": "active",
                "data_collection": "active", 
                "ai_regime_detection": "active",
                "adaptive_strategies": "active"
            },
            "timestamp": time.time()
        }
    
    return app

# Development server runner
if __name__ == "__main__":
    import uvicorn
    
    # Create app for development
    development_app = create_app()
    
    # Run development server
    uvicorn.run(
        development_app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )