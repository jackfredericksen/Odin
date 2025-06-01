"""
Authentication, rate limiting, and other middleware
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
import json
from typing import Callable, Dict, Any
from datetime import datetime, timedelta
import hashlib
import asyncio

from odin.config import settings

# Setup logging
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} - User-Agent: {request.headers.get('user-agent', 'Unknown')}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} for {request.method} {request.url.path} "
                f"in {process_time:.3f}s"
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Server"] = "Odin-Bitcoin-Bot"
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} for {request.method} {request.url.path} "
                f"in {process_time:.3f}s from {client_ip}"
            )
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with different limits for different endpoints
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.requests: Dict[str, list] = {}
        self.cleanup_interval = 60  # Cleanup every minute
        self.last_cleanup = time.time()
        
        # Rate limits by endpoint pattern
        self.rate_limits = {
            "/api/v1/data/current": {"requests": 60, "window": 60},  # 60 per minute
            "/api/v1/data/history": {"requests": 30, "window": 60},  # 30 per minute
            "/api/v1/strategies": {"requests": 20, "window": 60},    # 20 per minute
            "default": {"requests": 100, "window": 60}               # 100 per minute default
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client identifier
        client_id = self.get_client_id(request)
        
        # Get rate limit for this endpoint
        limit_config = self.get_rate_limit_config(request.url.path)
        
        # Check rate limit
        if not self.is_allowed(client_id, limit_config):
            logger.warning(f"Rate limit exceeded for {client_id} on {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {limit_config['requests']} per {limit_config['window']} seconds",
                    "status": "error"
                },
                headers={
                    "Retry-After": str(limit_config['window']),
                    "X-RateLimit-Limit": str(limit_config['requests']),
                    "X-RateLimit-Window": str(limit_config['window'])
                }
            )
        
        # Cleanup old requests periodically
        await self.cleanup_old_requests()
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.get_remaining_requests(client_id, limit_config)
        response.headers["X-RateLimit-Limit"] = str(limit_config['requests'])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(limit_config['window'])
        
        return response
    
    def get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get authenticated user first
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Hash the auth header for privacy
            return hashlib.sha256(auth_header.encode()).hexdigest()[:16]
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip_{ip}"
    
    def get_rate_limit_config(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for path"""
        for pattern, config in self.rate_limits.items():
            if pattern == "default":
                continue
            if path.startswith(pattern):
                return config
        return self.rate_limits["default"]
    
    def is_allowed(self, client_id: str, limit_config: Dict[str, int]) -> bool:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - limit_config['window']
        
        # Initialize or clean client requests
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.requests[client_id]) >= limit_config['requests']:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True
    
    def get_remaining_requests(self, client_id: str, limit_config: Dict[str, int]) -> int:
        """Get remaining requests for client"""
        current_count = len(self.requests.get(client_id, []))
        return max(0, limit_config['requests'] - current_count)
    
    async def cleanup_old_requests(self):
        """Cleanup old request records"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Remove empty client records
        to_remove = []
        for client_id, requests in self.requests.items():
            if not requests or (now - max(requests)) > 3600:  # 1 hour old
                to_remove.append(client_id)
        
        for client_id in to_remove:
            del self.requests[client_id]
        
        self.last_cleanup = now


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for protected endpoints
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Protected endpoints (require authentication)
        self.protected_endpoints = {
            "/api/v1/admin/",
            "/api/v1/trading/",
            "/api/v1/portfolio/"
        }
        
        # Admin endpoints (require admin role)
        self.admin_endpoints = {
            "/api/v1/admin/",
            "/api/v1/system/"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        # Check if endpoint requires authentication
        requires_auth = any(path.startswith(endpoint) for endpoint in self.protected_endpoints)
        requires_admin = any(path.startswith(endpoint) for endpoint in self.admin_endpoints)
        
        if requires_auth or requires_admin:
            auth_header = request.headers.get("Authorization")
            
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Authentication required",
                        "message": "Missing or invalid authorization header",
                        "status": "error"
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Extract token (this would normally validate JWT)
            token = auth_header.split(" ")[1]
            
            # For demo purposes, we'll use simple token validation
            # In production, you'd validate JWT tokens properly
            user = self.validate_token(token)
            
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Invalid token",
                        "message": "The provided token is invalid or expired",
                        "status": "error"
                    }
                )
            
            # Check admin access
            if requires_admin and user.get("role") != "admin":
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Insufficient privileges",
                        "message": "Admin access required",
                        "status": "error"
                    }
                )
            
            # Add user to request state
            request.state.user = user
        
        return await call_next(request)
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate authentication token
        
        In production, this would:
        1. Validate JWT signature
        2. Check expiration
        3. Fetch user from database
        4. Validate permissions
        """
        # Demo implementation
        demo_tokens = {
            "demo_user_token": {"username": "demo_user", "role": "user"},
            "demo_admin_token": {"username": "admin", "role": "admin"}
        }
        
        return demo_tokens.get(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to responses
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'",
        }
        
        if settings.ODIN_ENV == "production":
            self.security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """
    Handle health check requests quickly without processing
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Quick health check response
        if request.url.path == "/health":
            return JSONResponse(
                content={
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0.0"
                }
            )
        
        return await call_next(request)


def setup_middleware(app):
    """
    Setup all middleware in the correct order
    """
    # The order matters - middleware is processed in reverse order
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(HealthCheckMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(LoggingMiddleware)