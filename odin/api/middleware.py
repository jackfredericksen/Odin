"""Middleware for Odin trading bot API."""

import time
from collections import defaultdict
from typing import Callable, Dict

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from odin.core.exceptions import RateLimitError

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        """Initialize rate limiter."""
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.requests: Dict[str, list] = defaultdict(list)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Use IP address as client identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # TODO: Use API key or user ID if authentication is implemented
        return client_ip
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client is rate limited."""
        now = time.time()
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.period
        ]
        
        # Check rate limit
        if len(self.requests[client_id]) >= self.calls:
            return True
        
        # Add current request
        self.requests[client_id].append(now)
        return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        client_id = self._get_client_id(request)
        
        if self._is_rate_limited(client_id):
            logger.warning("Rate limit exceeded", client_id=client_id)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(self.period)}
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.calls - len(self.requests[client_id]))
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.period))
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log requests and responses."""
        start_time = time.time()
        
        # Log request
        logger.info("Request started",
                   method=request.method,
                   path=request.url.path,
                   client_ip=request.client.host if request.client else "unknown")
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info("Request completed",
                       method=request.method,
                       path=request.url.path,
                       status_code=response.status_code,
                       duration_ms=round(duration * 1000, 2))
            
            # Add timing header
            response.headers["X-Process-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error("Request failed",
                        method=request.method,
                        path=request.url.path,
                        error=str(e),
                        duration_ms=round(duration * 1000, 2))
            
            raise