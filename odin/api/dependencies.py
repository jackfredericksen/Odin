# odin/api/dependencies.py
"""
Enhanced dependency injection for Odin API with AI components
Provides access to all core services and AI features
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

# Import core components
from ..core.data_collector import BitcoinDataCollector
from ..core.database import Database
from ..core.trading_engine import TradingEngine
from ..core.portfolio_manager import PortfolioManager
from ..core.risk_manager import RiskManager

# Import AI components
from ..ai.regime_detection.regime_detector import MarketRegimeDetector
from ..ai.strategy_selection.adaptive_manager import AdaptiveStrategyManager
from ..strategies.ai_adaptive import AIAdaptiveStrategy

# Import configuration
from ..config import get_config

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)
config = get_config()

# Global instances (in production, these would be managed by dependency injection container)
_data_collector: Optional[BitcoinDataCollector] = None
_database: Optional[Database] = None
_trading_engine: Optional[TradingEngine] = None
_portfolio_manager: Optional[PortfolioManager] = None
_risk_manager: Optional[RiskManager] = None

# AI component instances
_regime_detector: Optional[MarketRegimeDetector] = None
_strategy_manager: Optional[AdaptiveStrategyManager] = None
_ai_strategy: Optional[AIAdaptiveStrategy] = None

# Rate limiting storage (in production, use Redis)
_rate_limit_storage: Dict[str, Dict[str, Any]] = {}

def get_data_collector() -> BitcoinDataCollector:
    """Get data collector instance"""
    global _data_collector
    if _data_collector is None:
        _data_collector = BitcoinDataCollector()
    return _data_collector

def get_database() -> Database:
    """Get database instance"""
    global _database
    if _database is None:
        _database = Database(config.database.database_url)
    return _database

def get_trading_engine() -> TradingEngine:
    """Get trading engine instance"""
    global _trading_engine
    if _trading_engine is None:
        portfolio_manager = get_portfolio_manager()
        risk_manager = get_risk_manager()
        _trading_engine = TradingEngine(
            portfolio_manager=portfolio_manager,
            risk_manager=risk_manager,
            live_trading_enabled=config.trading.enable_live_trading
        )
    return _trading_engine

def get_portfolio_manager() -> PortfolioManager:
    """Get portfolio manager instance"""
    global _portfolio_manager
    if _portfolio_manager is None:
        risk_manager = get_risk_manager()
        _portfolio_manager = PortfolioManager(risk_manager=risk_manager)
    return _portfolio_manager

def get_risk_manager() -> RiskManager:
    """Get risk manager instance"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager(
            max_position_size=config.trading.max_position_size,
            risk_per_trade=config.trading.risk_per_trade
        )
    return _risk_manager

# AI Dependencies
def get_regime_detector() -> MarketRegimeDetector:
    """Get AI regime detector instance"""
    global _regime_detector
    if _regime_detector is None:
        _regime_detector = MarketRegimeDetector(config.ai.regime_model_path)
        # Try to load existing models
        _regime_detector.load_models()
    return _regime_detector

def get_strategy_manager() -> AdaptiveStrategyManager:
    """Get adaptive strategy manager instance"""
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = AdaptiveStrategyManager(config.ai.strategy_config_path)
    return _strategy_manager

def get_ai_strategy() -> AIAdaptiveStrategy:
    """Get AI adaptive strategy instance"""
    global _ai_strategy
    if _ai_strategy is None:
        _ai_strategy = AIAdaptiveStrategy(
            regime_update_frequency=config.ai.regime_update_frequency,
            min_regime_confidence=config.ai.min_regime_confidence,
            strategy_rebalance_frequency=config.ai.strategy_rebalance_frequency
        )
    return _ai_strategy

# Authentication dependencies
async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and return user information
    
    Args:
        credentials: HTTP Bearer token
        
    Returns:
        User information if token is valid, None if no token provided
        
    Raises:
        HTTPException: If token is invalid
    """
    if not credentials:
        return None
    
    try:
        # In a real implementation, you would:
        # 1. Decode the JWT token
        # 2. Verify the signature
        # 3. Check expiration
        # 4. Return user information
        
        # For now, we'll implement a simple token check
        token = credentials.credentials
        
        # Mock token validation (replace with real JWT verification)
        if token == "development-token":
            return {
                "user_id": "dev-user",
                "username": "developer",
                "permissions": ["read", "write", "admin"],
                "expires_at": datetime.now() + timedelta(hours=1)
            }
        
        # If token is provided but invalid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user(user_info: Optional[Dict[str, Any]] = Depends(verify_token)) -> Dict[str, Any]:
    """
    Get current authenticated user (required authentication)
    
    Args:
        user_info: User information from token verification
        
    Returns:
        User information
        
    Raises:
        HTTPException: If no valid authentication provided
    """
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_info

async def get_optional_user(user_info: Optional[Dict[str, Any]] = Depends(verify_token)) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated (optional authentication)
    
    Args:
        user_info: User information from token verification
        
    Returns:
        User information if authenticated, None otherwise
    """
    return user_info

# Rate limiting dependencies
def get_client_id(request: Request) -> str:
    """
    Get client identifier for rate limiting
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client identifier (IP address or user ID)
    """
    # Try to get user ID from authentication
    # If not authenticated, use IP address
    client_ip = request.client.host if request.client else "unknown"
    
    # In production, you might want to use:
    # - X-Forwarded-For header for load balancers
    # - User ID for authenticated requests
    # - API key for API consumers
    
    return client_ip

def check_rate_limit(
    request: Request,
    endpoint_type: str = "general",
    client_id: str = Depends(get_client_id)
) -> bool:
    """
    Check rate limit for client and endpoint type
    
    Args:
        request: FastAPI request object
        endpoint_type: Type of endpoint (general, data, trading, etc.)
        client_id: Client identifier
        
    Returns:
        True if request is allowed
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    if not config.security.rate_limit_enabled:
        return True
    
    current_time = datetime.now()
    window_size = timedelta(minutes=1)  # 1-minute window
    
    # Rate limits per endpoint type
    rate_limits = {
        "general": 100,
        "data": 60,
        "strategies": 20,
        "trading": 30,
        "ai": 40,
        "portfolio": 50,
        "market": 40
    }
    
    limit = rate_limits.get(endpoint_type, 100)
    
    # Get or create client rate limit data
    if client_id not in _rate_limit_storage:
        _rate_limit_storage[client_id] = {}
    
    if endpoint_type not in _rate_limit_storage[client_id]:
        _rate_limit_storage[client_id][endpoint_type] = {
            "requests": [],
            "window_start": current_time
        }
    
    client_data = _rate_limit_storage[client_id][endpoint_type]
    
    # Clean old requests outside the window
    client_data["requests"] = [
        req_time for req_time in client_data["requests"]
        if current_time - req_time < window_size
    ]
    
    # Check if limit exceeded
    if len(client_data["requests"]) >= limit:
        logger.warning(f"Rate limit exceeded for {client_id} on {endpoint_type}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {limit} requests per minute for {endpoint_type} endpoints.",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int((current_time + window_size).timestamp()))
            }
        )
    
    # Add current request
    client_data["requests"].append(current_time)
    
    return True

# Specific rate limiting dependencies for different endpoint types
async def rate_limit_general(request: Request, client_id: str = Depends(get_client_id)) -> bool:
    """Rate limit for general endpoints"""
    return check_rate_limit(request, "general", client_id)

async def rate_limit_data(request: Request, client_id: str = Depends(get_client_id)) -> bool:
    """Rate limit for data endpoints"""
    return check_rate_limit(request, "data", client_id)

async def rate_limit_strategies(request: Request, client_id: str = Depends(get_client_id)) -> bool:
    """Rate limit for strategy endpoints"""
    return check_rate_limit(request, "strategies", client_id)

async def rate_limit_trading(request: Request, client_id: str = Depends(get_client_id)) -> bool:
    """Rate limit for trading endpoints"""
    return check_rate_limit(request, "trading", client_id)

async def rate_limit_ai(request: Request, client_id: str = Depends(get_client_id)) -> bool:
    """Rate limit for AI endpoints"""
    return check_rate_limit(request, "ai", client_id)

async def rate_limit_portfolio(request: Request, client_id: str = Depends(get_client_id)) -> bool:
    """Rate limit for portfolio endpoints"""
    return check_rate_limit(request, "portfolio", client_id)

# Validation dependencies
def validate_timeframe(hours: int) -> int:
    """
    Validate timeframe parameter
    
    Args:
        hours: Number of hours
        
    Returns:
        Validated hours
        
    Raises:
        HTTPException: If timeframe is invalid
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

def validate_strategy_name(strategy: str) -> str:
    """
    Validate strategy name parameter
    
    Args:
        strategy: Strategy name
        
    Returns:
        Validated strategy name
        
    Raises:
        HTTPException: If strategy name is invalid
    """
    valid_strategies = [
        "moving_average",
        "rsi", 
        "bollinger_bands",
        "macd",
        "ai_adaptive"
    ]
    
    if strategy not in valid_strategies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid strategy. Must be one of: {', '.join(valid_strategies)}"
        )
    
    return strategy

def validate_regime_name(regime: str) -> str:
    """
    Validate regime name parameter
    
    Args:
        regime: Regime name
        
    Returns:
        Validated regime name
        
    Raises:
        HTTPException: If regime name is invalid
    """
    valid_regimes = [
        "bull_trending",
        "bear_trending",
        "sideways", 
        "high_volatility",
        "crisis"
    ]
    
    if regime not in valid_regimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid regime. Must be one of: {', '.join(valid_regimes)}"
        )
    
    return regime

# Dependency combinations for common use cases
async def get_authenticated_data_collector(
    _: Dict[str, Any] = Depends(get_current_user),
    _rate_limit: bool = Depends(rate_limit_data)
) -> BitcoinDataCollector:
    """Get data collector with authentication and rate limiting"""
    return get_data_collector()

async def get_authenticated_trading_engine(
    user: Dict[str, Any] = Depends(get_current_user),
    _rate_limit: bool = Depends(rate_limit_trading)
) -> TradingEngine:
    """Get trading engine with authentication and rate limiting"""
    # Check if user has trading permissions
    if "trading" not in user.get("permissions", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trading permissions required"
        )
    
    return get_trading_engine()

async def get_authenticated_ai_components(
    _: Dict[str, Any] = Depends(get_current_user),
    _rate_limit: bool = Depends(rate_limit_ai)
) -> tuple[MarketRegimeDetector, AdaptiveStrategyManager, AIAdaptiveStrategy]:
    """Get AI components with authentication and rate limiting"""
    return (
        get_regime_detector(),
        get_strategy_manager(), 
        get_ai_strategy()
    )

# Health check dependencies
async def check_system_health() -> Dict[str, Any]:
    """
    Check overall system health
    
    Returns:
        System health status
    """
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "components": {}
    }
    
    try:
        # Check data collector
        data_collector = get_data_collector()
        health_status["components"]["data_collector"] = {
            "status": "healthy" if data_collector else "unhealthy",
            "details": "Data collection service operational"
        }
        
        # Check database
        database = get_database()
        health_status["components"]["database"] = {
            "status": "healthy" if database else "unhealthy", 
            "details": "Database connection operational"
        }
        
        # Check AI components
        try:
            regime_detector = get_regime_detector()
            models_loaded = regime_detector.hmm_model is not None
            health_status["components"]["ai_regime_detection"] = {
                "status": "healthy" if models_loaded else "degraded",
                "details": f"Models loaded: {models_loaded}"
            }
        except Exception as e:
            health_status["components"]["ai_regime_detection"] = {
                "status": "unhealthy",
                "details": f"AI initialization failed: {str(e)}"
            }
        
        # Check trading engine
        try:
            trading_engine = get_trading_engine()
            health_status["components"]["trading_engine"] = {
                "status": "healthy" if trading_engine else "unhealthy",
                "details": f"Live trading: {config.trading.enable_live_trading}"
            }
        except Exception as e:
            health_status["components"]["trading_engine"] = {
                "status": "unhealthy", 
                "details": f"Trading engine error: {str(e)}"
            }
        
        # Determine overall status
        component_statuses = [comp["status"] for comp in health_status["components"].values()]
        if "unhealthy" in component_statuses:
            health_status["overall_status"] = "unhealthy"
        elif "degraded" in component_statuses:
            health_status["overall_status"] = "degraded"
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status["overall_status"] = "unhealthy"
        health_status["error"] = str(e)
    
    return health_status

# Application state management
class ApplicationState:
    """Manages application state and component lifecycle"""
    
    def __init__(self):
        self.initialized = False
        self.startup_time = datetime.now()
        self.components = {}
    
    async def initialize(self):
        """Initialize all application components"""
        try:
            logger.info("Initializing application components...")
            
            # Initialize core components
            self.components["data_collector"] = get_data_collector()
            self.components["database"] = get_database()
            self.components["risk_manager"] = get_risk_manager()
            self.components["portfolio_manager"] = get_portfolio_manager()
            self.components["trading_engine"] = get_trading_engine()
            
            # Initialize AI components
            self.components["regime_detector"] = get_regime_detector()
            self.components["strategy_manager"] = get_strategy_manager()
            self.components["ai_strategy"] = get_ai_strategy()
            
            self.initialized = True
            logger.info("✅ Application components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown all application components"""
        try:
            logger.info("Shutting down application components...")
            
            # Shutdown components in reverse order
            for name, component in reversed(list(self.components.items())):
                try:
                    if hasattr(component, 'shutdown'):
                        await component.shutdown()
                    elif hasattr(component, 'close'):
                        await component.close()
                    logger.info(f"✅ {name} shutdown complete")
                except Exception as e:
                    logger.error(f"❌ {name} shutdown failed: {e}")
            
            logger.info("✅ Application shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Application shutdown failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get application status"""
        uptime = datetime.now() - self.startup_time
        
        return {
            "initialized": self.initialized,
            "startup_time": self.startup_time.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "component_count": len(self.components),
            "components": list(self.components.keys())
        }

# Global application state
app_state = ApplicationState()

def get_app_state() -> ApplicationState:
    """Get application state instance"""
    return app_state

# For backwards compatibility and ease of access
__all__ = [
    # Core dependencies
    "get_data_collector",
    "get_database", 
    "get_trading_engine",
    "get_portfolio_manager",
    "get_risk_manager",
    
    # AI dependencies
    "get_regime_detector",
    "get_strategy_manager", 
    "get_ai_strategy",
    
    # Authentication
    "verify_token",
    "get_current_user",
    "get_optional_user",
    
    # Rate limiting
    "rate_limit_general",
    "rate_limit_data",
    "rate_limit_strategies", 
    "rate_limit_trading",
    "rate_limit_ai",
    "rate_limit_portfolio",
    
    # Validation
    "validate_timeframe",
    "validate_strategy_name",
    "validate_regime_name",
    
    # Combined dependencies
    "get_authenticated_data_collector",
    "get_authenticated_trading_engine",
    "get_authenticated_ai_components",
    
    # Health and state
    "check_system_health",
    "get_app_state"
]