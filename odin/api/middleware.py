# odin/api/middleware.py
"""
Custom middleware for Odin API
Includes security headers, rate limiting, and request logging
Compatible with Python 3.8+
"""

import time
import logging
from typing import Callable, Dict, Any, Tuple, List, Union
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # API identification
        response.headers["X-API-Version"] = "2.0.0"
        response.headers["X-Powered-By"] = "Odin Trading Bot"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with per-endpoint limits"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.client_requests: Dict[str, Dict[str, Any]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        if request.url.path.startswith("/static"):
            return await call_next(request)
        # Skip rate limiting for WebSocket connections1
        if request.url.path.startswith("/ws"):
            return await call_next(request)
        # Get client identifier
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Determine endpoint type and rate limit
        endpoint_type, limit, window = self._get_rate_limit_for_path(request.url.path)
        
        # Check rate limit
        if not self._check_rate_limit(client_ip, endpoint_type, limit, window, current_time):
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint_type}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {limit} requests per {window} seconds for {endpoint_type} endpoints",
                    "retry_after": window
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(window)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining_requests(client_ip, endpoint_type, limit, window, current_time)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + window))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded header (load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _get_rate_limit_for_path(self, path: str) -> Tuple[str, int, int]:
        """Get rate limit configuration for path"""
        if "/ai/" in path:
            return "ai", 40, 60  # 40 requests per minute
        elif "/trading/" in path:
            return "trading", 30, 60  # 30 requests per minute
        elif "/data/" in path:
            return "data", 60, 60  # 60 requests per minute
        elif "/strategies/" in path:
            return "strategies", 20, 60  # 20 requests per minute
        elif "/portfolio/" in path:
            return "portfolio", 50, 60  # 50 requests per minute
        elif "/market/" in path:
            return "market", 40, 60  # 40 requests per minute
        else:
            return "general", 100, 60  # 100 requests per minute
    
    def _check_rate_limit(self, client_ip: str, endpoint_type: str, limit: int, window: int, current_time: float) -> bool:
        """Check if request is within rate limit"""
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = {}
        
        if endpoint_type not in self.client_requests[client_ip]:
            self.client_requests[client_ip][endpoint_type] = []
        
        # Clean old requests outside the window
        self.client_requests[client_ip][endpoint_type] = [
            req_time for req_time in self.client_requests[client_ip][endpoint_type]
            if current_time - req_time < window
        ]
        
        # Check if limit exceeded
        if len(self.client_requests[client_ip][endpoint_type]) >= limit:
            return False
        
        # Add current request
        self.client_requests[client_ip][endpoint_type].append(current_time)
        return True
    
    def _get_remaining_requests(self, client_ip: str, endpoint_type: str, limit: int, window: int, current_time: float) -> int:
        """Get remaining requests in current window"""
        if client_ip not in self.client_requests or endpoint_type not in self.client_requests[client_ip]:
            return limit
        
        # Count requests in current window
        requests_in_window = len([
            req_time for req_time in self.client_requests[client_ip][endpoint_type]
            if current_time - req_time < window
        ])
        
        return max(0, limit - requests_in_window)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Request and response logging middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} for {request.method} {request.url.path} "
                f"({process_time:.3f}s)"
            )
            
            # Add response time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} for {request.method} {request.url.path} "
                f"({process_time:.3f}s)"
            )
            raise

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Request validation and sanitization middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate request size
        if hasattr(request, 'headers'):
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large", "max_size": "10MB"}
                )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get('content-type', '')
            valid_types = ['application/json', 'multipart/form-data', 'application/x-www-form-urlencoded']
            
            if content_type and not any(ct in content_type for ct in valid_types):
                return JSONResponse(
                    status_code=415,
                    content={
                        "error": "Unsupported media type", 
                        "supported": valid_types
                    }
                )
        
        return await call_next(request)

class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add appropriate cache control headers"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Set cache control based on endpoint
        path = request.url.path
        
        if "/static/" in path:
            # Static files - cache for 1 hour
            response.headers["Cache-Control"] = "public, max-age=3600"
        elif "/api/v1/data/" in path:
            # Data endpoints - cache for 30 seconds
            response.headers["Cache-Control"] = "public, max-age=30"
        elif "/api/v1/health" in path:
            # Health checks - cache for 10 seconds
            response.headers["Cache-Control"] = "public, max-age=10"
        elif "/docs" in path or "/redoc" in path:
            # Documentation - cache for 5 minutes
            response.headers["Cache-Control"] = "public, max-age=300"
        else:
            # Other endpoints - no cache
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response

class APIMetricsMiddleware(BaseHTTPMiddleware):
    """Collect API metrics for monitoring"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.response_times: List[float] = []
        self.endpoint_stats: Dict[str, Dict[str, Union[int, float]]] = {}
        self.start_time = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        self.request_count += 1
        
        endpoint = f"{request.method} {request.url.path}"
        
        try:
            response = await call_next(request)
            
            # Record metrics
            process_time = time.time() - start_time
            self.response_times.append(process_time)
            
            # Keep only last 1000 response times
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
            
            # Update endpoint stats
            if endpoint not in self.endpoint_stats:
                self.endpoint_stats[endpoint] = {
                    "count": 0,
                    "total_time": 0.0,
                    "errors": 0,
                    "avg_time": 0.0
                }
            
            stats = self.endpoint_stats[endpoint]
            stats["count"] += 1
            stats["total_time"] += process_time
            stats["avg_time"] = stats["total_time"] / stats["count"]
            
            if response.status_code >= 400:
                self.error_count += 1
                stats["errors"] += 1
            
            # Add metrics headers
            response.headers["X-Request-Count"] = str(self.request_count)
            if self.response_times:
                avg_response_time = sum(self.response_times) / len(self.response_times)
                response.headers["X-Avg-Response-Time"] = f"{avg_response_time:.3f}"
            
            return response
            
        except Exception as e:
            self.error_count += 1
            if endpoint in self.endpoint_stats:
                self.endpoint_stats[endpoint]["errors"] += 1
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        current_time = time.time()
        uptime = current_time - self.start_time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        # Calculate requests per second
        rps = self.request_count / uptime if uptime > 0 else 0
        
        # Calculate error rate
        error_rate = (self.error_count / max(self.request_count, 1)) * 100
        
        # Get top endpoints by request count
        top_endpoints = sorted(
            self.endpoint_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]
        
        # Get slowest endpoints
        slowest_endpoints = sorted(
            [(k, v) for k, v in self.endpoint_stats.items() if v["count"] > 0],
            key=lambda x: x[1]["avg_time"],
            reverse=True
        )[:5]
        
        return {
            "uptime_seconds": round(uptime, 2),
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate_percent": round(error_rate, 2),
            "requests_per_second": round(rps, 2),
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "total_endpoints": len(self.endpoint_stats),
            "top_endpoints": [
                {
                    "endpoint": endpoint,
                    "count": int(stats["count"]),
                    "avg_time_ms": round(float(stats["avg_time"]) * 1000, 2),
                    "errors": int(stats["errors"])
                }
                for endpoint, stats in top_endpoints
            ],
            "slowest_endpoints": [
                {
                    "endpoint": endpoint,
                    "avg_time_ms": round(float(stats["avg_time"]) * 1000, 2),
                    "count": int(stats["count"])
                }
                for endpoint, stats in slowest_endpoints
            ],
            "response_time_percentiles": self._calculate_percentiles()
        }
    
    def _calculate_percentiles(self) -> Dict[str, float]:
        """Calculate response time percentiles"""
        if not self.response_times:
            return {}
        
        sorted_times = sorted(self.response_times)
        
        def percentile(data: List[float], p: float) -> float:
            """Calculate percentile"""
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = k - f
            if f == len(data) - 1:
                return data[f]
            return data[f] * (1 - c) + data[f + 1] * c
        
        return {
            "p50_ms": round(percentile(sorted_times, 50) * 1000, 2),
            "p90_ms": round(percentile(sorted_times, 90) * 1000, 2),
            "p95_ms": round(percentile(sorted_times, 95) * 1000, 2),
            "p99_ms": round(percentile(sorted_times, 99) * 1000, 2)
        }

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Add correlation IDs to requests for tracing"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import uuid
        
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response

class CompressionMiddleware(BaseHTTPMiddleware):
    """Add compression headers for large responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Check if client accepts compression
        accept_encoding = request.headers.get("Accept-Encoding", "")
        
        # Add appropriate headers for large responses
        if hasattr(response, 'body'):
            body = getattr(response, 'body', b'')
            if len(body) > 1024:
                if "gzip" in accept_encoding:
                    response.headers["Content-Encoding"] = "gzip"
                elif "deflate" in accept_encoding:
                    response.headers["Content-Encoding"] = "deflate"
        
        return response

# Global metrics instance for access in health checks
api_metrics: Union[APIMetricsMiddleware, None] = None

def get_api_metrics() -> Union[APIMetricsMiddleware, None]:
    """Get the API metrics middleware instance"""
    global api_metrics
    return api_metrics

def set_api_metrics(metrics: APIMetricsMiddleware) -> None:
    """Set the API metrics middleware instance"""
    global api_metrics
    api_metrics = metrics

# Middleware configuration helper
def get_middleware_stack() -> List[type]:
    """Get the recommended middleware stack"""
    return [
        SecurityHeadersMiddleware,
        CorrelationIdMiddleware,
        APIMetricsMiddleware,
        RateLimitMiddleware,
        RequestValidationMiddleware,
        CacheControlMiddleware,
        CompressionMiddleware,
        LoggingMiddleware
    ]

# Export all middleware classes
__all__ = [
    "SecurityHeadersMiddleware",
    "RateLimitMiddleware", 
    "LoggingMiddleware",
    "RequestValidationMiddleware",
    "CacheControlMiddleware",
    "APIMetricsMiddleware",
    "CorrelationIdMiddleware",
    "CompressionMiddleware",
    "get_api_metrics",
    "set_api_metrics",
    "get_middleware_stack"
]