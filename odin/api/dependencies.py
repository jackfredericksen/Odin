"""
Dependency injection container for FastAPI (FIXED VERSION)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Generator
import jwt
from datetime import datetime, timedelta

# FIXED: Use absolute imports
from odin.core.database import DatabaseManager
from odin.core.data_collector import DataCollector
from odin.strategies.moving_average import MovingAverageStrategy
from odin.strategies.rsi import RSIStrategy
from odin.strategies.bollinger_bands import BollingerBandsStrategy
from odin.strategies.macd import MACDStrategy
from odin.config import get_settings


# Security
security = HTTPBearer(auto_error=False)

# Database manager instance
db_manager = DatabaseManager()

# Data collector instance - FIXED: Use correct class name
data_collector = DataCollector(database=db_manager)

# Strategy instances
ma_strategy = MovingAverageStrategy()
rsi_strategy = RSIStrategy()
bb_strategy = BollingerBandsStrategy()
macd_strategy = MACDStrategy()


def get_database() -> DatabaseManager:
    """
    Get database manager dependency
    """
    return db_manager


def get_data_collector() -> DataCollector:
    """
    Get data collector dependency
    """
    return data_collector


def get_ma_strategy() -> MovingAverageStrategy:
    """
    Get Moving Average strategy dependency
    """
    return ma_strategy


def get_rsi_strategy() -> RSIStrategy:
    """
    Get RSI strategy dependency
    """
    return rsi_strategy


def get_bb_strategy() -> BollingerBandsStrategy:
    """
    Get Bollinger Bands strategy dependency
    """
    return bb_strategy


def get_macd_strategy() -> MACDStrategy:
    """
    Get MACD strategy dependency
    """
    return macd_strategy


def get_strategy_by_name(strategy_name: str):
    """
    Get strategy by name dependency
    """
    strategies = {
        "ma": ma_strategy,
        "moving_average": ma_strategy,
        "rsi": rsi_strategy,
        "bb": bb_strategy,
        "bollinger_bands": bb_strategy,
        "macd": macd_strategy,

        "ma_cross": ma_strategy,           
        "rsi_momentum": rsi_strategy,      
        "bollinger_bands": bb_strategy,    
        "macd_trend": macd_strategy
    }
    
    strategy = strategies.get(strategy_name.lower())
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_name}' not found"
        )
    
    return strategy


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current authenticated user
    """
    if not credentials:
        return None
    
    try:
        settings = get_settings()
        
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        username: str = payload.get("sub")
        if username is None:
            return None
            
        # In a real app, you would fetch user from database
        return {"username": username, "role": "user"}
        
    except jwt.PyJWTError:
        return None


async def require_authentication(
    current_user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """
    Require user to be authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def require_admin(
    current_user: dict = Depends(require_authentication)
) -> dict:
    """
    Require user to have admin role
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def validate_timeframe(hours: int) -> int:
    """
    Validate timeframe parameter
    """
    if hours < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timeframe must be at least 1 hour"
        )
    
    if hours > 8760:  # 1 year
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timeframe cannot exceed 1 year (8760 hours)"
        )
    
    return hours


def validate_limit(limit: int) -> int:
    """
    Validate limit parameter
    """
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be at least 1"
        )
    
    if limit > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 10,000"
        )
    
    return limit


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create JWT access token
    """
    settings = get_settings()
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


# Rate limiting dependency
class RateLimiter:
    """
    Simple rate limiter for API endpoints
    """
    def __init__(self, max_requests: int = 100, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        """
        Check if request is allowed based on rate limit
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # Check if under limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True


# Global rate limiter instances
api_rate_limiter = RateLimiter(max_requests=100, window_minutes=1)
data_rate_limiter = RateLimiter(max_requests=60, window_minutes=1)
strategy_rate_limiter = RateLimiter(max_requests=30, window_minutes=1)


def get_api_rate_limiter() -> RateLimiter:
    """Get API rate limiter dependency"""
    return api_rate_limiter


def get_data_rate_limiter() -> RateLimiter:
    """Get data rate limiter dependency"""
    return data_rate_limiter


def get_strategy_rate_limiter() -> RateLimiter:
    """Get strategy rate limiter dependency"""
    return strategy_rate_limiter