"""
Odin Core Trading Engine - Live Trade Execution Engine

Professional trading engine for the Odin trading bot providing live trade execution,
order management, exchange integration, slippage control, and execution quality
monitoring with comprehensive safety controls and performance tracking.

File: odin/core/trading_engine.py
Author: Odin Development Team
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass
import aiohttp
import hashlib
import hmac
import time
import json

from .database import Database
from .models import (
    TradeOrder, TradeExecution, TradeSignal, OrderType, OrderSide, 
    OrderStatus, PriceData
)
from .exceptions import (
    TradingEngineException, InvalidOrderException, OrderExecutionException,
    InsufficientFundsException, ExchangeConnectionException
)

logger = logging.getLogger(__name__)


class ExecutionStrategy(str, Enum):
    """Order execution strategies."""
    AGGRESSIVE = "aggressive"      # Market orders, immediate execution
    PASSIVE = "passive"           # Limit orders, better prices
    ADAPTIVE = "adaptive"         # Adjust based on market conditions
    TWAP = "twap"                # Time-weighted average price
    VWAP = "vwap"                # Volume-weighted average price


@dataclass
class ExecutionQuality:
    """Trade execution quality metrics."""
    slippage: float              # Price slippage vs expected
    market_impact: float         # Market impact estimate
    fill_rate: float            # Percentage filled
    execution_time: float       # Time to complete (seconds)
    effective_spread: float     # Effective bid-ask spread
    implementation_shortfall: float  # Cost vs benchmark


@dataclass
class Orderbook:
    """Order book data."""
    symbol: str
    timestamp: datetime
    bids: List[Tuple[float, float]]  # [(price, size), ...]
    asks: List[Tuple[float, float]]  # [(price, size), ...]
    
    @property
    def best_bid(self) -> Optional[float]:
        return self.bids[0][0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[float]:
        return self.asks[0][0] if self.asks else None
    
    @property
    def spread(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None
    
    @property
    def mid_price(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return None


class ExchangeInterface:
    """Base class for exchange interfaces."""
    
    def __init__(self, name: str, api_key: str = "", secret_key: str = "", sandbox: bool = True):
        self.name = name
        self.api_key = api_key
        self.secret_key = secret_key
        self.sandbox = sandbox
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0
        
        # Connection status
        self.connected = False
        self.last_heartbeat = None
    
    async def connect(self):
        """Connect to exchange."""
        try:
            self.session = aiohttp.ClientSession()
            await self._authenticate()
            self.connected = True
            logger.info(f"Connected to {self.name} exchange")
        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {e}")
            raise ExchangeConnectionException(self.name, str(e))
    
    async def disconnect(self):
        """Disconnect from exchange."""
        if self.session:
            await self.session.close()
        self.connected = False
        logger.info(f"Disconnected from {self.name} exchange")
    
    async def _authenticate(self):
        """Authenticate with exchange (implement in subclass)."""
        pass
    
    async def _rate_limit(self):
        """Apply rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    async def place_order(self, order: TradeOrder) -> str:
        """Place order on exchange (implement in subclass)."""
        raise NotImplementedError
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order on exchange (implement in subclass)."""
        raise NotImplementedError
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status from exchange (implement in subclass)."""
        raise NotImplementedError
    
    async def get_orderbook(self, symbol: str) -> Orderbook:
        """Get order book from exchange (implement in subclass)."""
        raise NotImplementedError
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balances (implement in subclass)."""
        raise NotImplementedError


class CoinbaseExchange(ExchangeInterface):
    """Coinbase Pro/Advanced Trade exchange interface."""
    
    def __init__(self, api_key: str = "", secret_key: str = "", passphrase: str = "", sandbox: bool = True):
        super().__init__("coinbase", api_key, secret_key, sandbox)
        self.passphrase = passphrase
        self.base_url = "https://api-public.sandbox.exchange.coinbase.com" if sandbox else "https://api.exchange.coinbase.com"
    
    async def _authenticate(self):
        """Test authentication with Coinbase."""
        if not self.api_key or not self.secret_key:
            logger.warning("Coinbase API credentials not provided - using paper trading mode")
            return
        
        # Test authentication by getting account info
        try:
            await self._make_request("GET", "/accounts")
            logger.info("Coinbase authentication successful")
        except Exception as e:
            logger.error(f"Coinbase authentication failed: {e}")
            raise
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Coinbase."""
        await self._rate_limit()
        
        timestamp = str(int(time.time()))
        message = timestamp + method + endpoint
        
        if data:
            body = json.dumps(data)
            message += body
        else:
            body = ""
        
        # Create signature
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }
        
        url = self.base_url + endpoint
        
        async with self.session.request(method, url, headers=headers, data=body) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise OrderExecutionException(f"Coinbase API error: {response.status} - {error_text}")
    
    async def place_order(self, order: TradeOrder) -> str:
        """Place order on Coinbase."""
        try:
            # Convert to Coinbase order format
            order_data = {
                "product_id": "BTC-USD",
                "side": order.side.value.lower(),
                "size": str(order.quantity),
                "type": order.order_type.value.lower()
            }
            
            if order.order_type == OrderType.LIMIT:
                order_data["price"] = str(order.price)
            
            if order.time_in_force:
                order_data["time_in_force"] = order.time_in_force
            
            if order.stop_price:
                order_data["stop_price"] = str(order.stop_price)
            
            response = await self._make_request("POST", "/orders", order_data)
            
            if "id" in response:
                logger.info(f"Order placed on Coinbase: {response['id']}")
                return response["id"]
            else:
                raise OrderExecutionException(f"Failed to place order: {response}")
                
        except Exception as e:
            logger.error(f"Coinbase order placement error: {e}")
            raise OrderExecutionException(f"Failed to place order on Coinbase: {str(e)}")
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order on Coinbase."""
        try:
            response = await self._make_request("DELETE", f"/orders/{order_id}")
            logger.info(f"Order cancelled on Coinbase: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Coinbase order cancellation error: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status from Coinbase."""
        try:
            response = await self._make_request("GET", f"/orders/{order_id}")
            return {
                "id": response["id"],
                "status": response["status"],
                "filled_size": float(response.get("filled_size", 0)),
                "remaining_size": float(response.get("size", 0)) - float(response.get("filled_size", 0)),
                "executed_value": float(response.get("executed_value", 0)),
                "fill_fees": float(response.get("fill_fees", 0))
            }
        except Exception as e:
            logger.error(f"Coinbase order status error: {e}")
            raise OrderExecutionException(f"Failed to get order status: {str(e)}")
    
    async def get_orderbook(self, symbol: str = "BTC-USD") -> Orderbook:
        """Get order book from Coinbase."""
        try:
            # Use public endpoint for order book
            url = f"{self.base_url.replace('/v2', '')}/products/{symbol}/book?level=2"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    bids = [(float(price), float(size)) for price, size, _ in data["bids"]]
                    asks = [(float(price), float(size)) for price, size, _ in data["asks"]]
                    
                    return Orderbook(
                        symbol=symbol,
                        timestamp=datetime.now(timezone.utc),
                        bids=bids,
                        asks=asks
                    )
                else:
                    raise OrderExecutionException(f"Failed to get orderbook: {response.status}")
                    
        except Exception as e:
            logger.error(f"Coinbase orderbook error: {e}")
            raise OrderExecutionException(f"Failed to get orderbook: {str(e)}")
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balances from Coinbase."""
        try:
            response = await self._make_request("GET", "/accounts")
            
            balances = {}
            for account in response:
                currency = account["currency"]
                balance = float(account["balance"])
                balances[currency] = balance
            
            return balances
            
        except Exception as e:
            logger.error(f"Coinbase balance error: {e}")
            raise OrderExecutionException(f"Failed to get balances: {str(e)}")


class PaperTradingExchange(ExchangeInterface):
    """Paper trading exchange for testing."""
    
    def __init__(self):
        super().__init__("paper_trading", sandbox=True)
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.balances = {"USD": 100000.0, "BTC": 0.0}
        self.order_counter = 1
    
    async def connect(self):
        """Connect to paper trading."""
        self.connected = True
        logger.info("Paper trading mode activated")
    
    async def place_order(self, order: TradeOrder) -> str:
        """Simulate order placement."""
        order_id = f"paper_{self.order_counter}"
        self.order_counter += 1
        
        # Simulate order in exchange
        self.orders[order_id] = {
            "id": order_id,
            "order": order,
            "status": "pending",
            "filled_size": 0.0,
            "timestamp": datetime.now(timezone.utc)
        }
        
        # Simulate immediate fill for market orders
        if order.order_type == OrderType.MARKET:
            await self._simulate_fill(order_id, order)
        
        logger.info(f"Paper order placed: {order_id}")
        return order_id
    
    async def _simulate_fill(self, order_id: str, order: TradeOrder):
        """Simulate order fill."""
        # Get simulated current price (would use real market data)
        current_price = 50000.0  # Placeholder
        
        # Add small slippage for market orders
        if order.order_type == OrderType.MARKET:
            slippage = 0.001  # 0.1% slippage
            if order.side == OrderSide.BUY:
                fill_price = current_price * (1 + slippage)
            else:
                fill_price = current_price * (1 - slippage)
        else:
            fill_price = order.price or current_price
        
        # Calculate trade value and fees
        trade_value = order.quantity * fill_price
        fee = trade_value * 0.005  # 0.5% fee
        
        # Update balances
        if order.side == OrderSide.BUY:
            if self.balances["USD"] >= trade_value + fee:
                self.balances["USD"] -= trade_value + fee
                self.balances["BTC"] += order.quantity
                
                # Update order status
                self.orders[order_id]["status"] = "filled"
                self.orders[order_id]["filled_size"] = order.quantity
                self.orders[order_id]["fill_price"] = fill_price
                self.orders[order_id]["fee"] = fee
                
                logger.info(f"Paper BUY filled: {order.quantity:.6f} BTC at ${fill_price:.2f}")
            else:
                self.orders[order_id]["status"] = "rejected"
                logger.warning("Paper order rejected: insufficient USD balance")
        
        else:  # SELL
            if self.balances["BTC"] >= order.quantity:
                self.balances["BTC"] -= order.quantity
                self.balances["USD"] += trade_value - fee
                
                # Update order status
                self.orders[order_id]["status"] = "filled"
                self.orders[order_id]["filled_size"] = order.quantity
                self.orders[order_id]["fill_price"] = fill_price
                self.orders[order_id]["fee"] = fee
                
                logger.info(f"Paper SELL filled: {order.quantity:.6f} BTC at ${fill_price:.2f}")
            else:
                self.orders[order_id]["status"] = "rejected"
                logger.warning("Paper order rejected: insufficient BTC balance")
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel paper order."""
        if order_id in self.orders:
            self.orders[order_id]["status"] = "cancelled"
            logger.info(f"Paper order cancelled: {order_id}")
            return True
        return False
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get paper order status."""
        if order_id in self.orders:
            order_data = self.orders[order_id]
            return {
                "id": order_id,
                "status": order_data["status"],
                "filled_size": order_data.get("filled_size", 0.0),
                "remaining_size": order_data["order"].quantity - order_data.get("filled_size", 0.0),
                "executed_value": order_data.get("filled_size", 0.0) * order_data.get("fill_price", 0.0),
                "fill_fees": order_data.get("fee", 0.0)
            }
        else:
            raise OrderExecutionException(f"Order not found: {order_id}")
    
    async def get_orderbook(self, symbol: str = "BTC-USD") -> Orderbook:
        """Get simulated order book."""
        current_price = 50000.0  # Placeholder
        spread = 10.0  # $10 spread
        
        bids = [(current_price - spread/2 - i, 1.0) for i in range(10)]
        asks = [(current_price + spread/2 + i, 1.0) for i in range(10)]
        
        return Orderbook(
            symbol=symbol,
            timestamp=datetime.now(timezone.utc),
            bids=bids,
            asks=asks
        )
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get paper trading balances."""
        return self.balances.copy()


class TradingEngine:
    """Main trading engine for live trade execution."""
    
    def __init__(
        self, 
        database: Database,
        exchange_config: Optional[Dict[str, Any]] = None,
        paper_trading: bool = True
    ):
        """
        Initialize trading engine.
        
        Args:
            database: Database instance
            exchange_config: Exchange configuration
            paper_trading: Use paper trading mode
        """
        self.database = database
        self.paper_trading = paper_trading
        
        # Initialize exchange interface
        if paper_trading:
            self.exchange = PaperTradingExchange()
        else:
            # Initialize real exchange (Coinbase by default)
            config = exchange_config or {}
            self.exchange = CoinbaseExchange(
                api_key=config.get("api_key", ""),
                secret_key=config.get("secret_key", ""),
                passphrase=config.get("passphrase", ""),
                sandbox=config.get("sandbox", True)
            )
        
        # Execution settings
        self.execution_strategy = ExecutionStrategy.ADAPTIVE
        self.max_slippage = 0.005  # 0.5% max slippage
        self.order_timeout = 300   # 5 minutes timeout
        
        # Order tracking
        self.active_orders: Dict[str, TradeOrder] = {}
        self.order_callbacks: List[Callable] = []
        
        # Execution quality tracking
        self.execution_history: List[ExecutionQuality] = []
        
        # Safety controls
        self.emergency_stop = False
        self.daily_trade_limit = 100
        self.daily_trade_count = 0
        self.trade_cooldown = {}  # strategy -> last_trade_time
        
        logger.info(f"Trading engine initialized ({'paper' if paper_trading else 'live'} trading)")
    
    async def start(self):
        """Start trading engine."""
        try:
            await self.exchange.connect()
            
            # Start order monitoring task
            asyncio.create_task(self._monitor_orders())
            
            logger.info("Trading engine started")
            
        except Exception as e:
            logger.error(f"Failed to start trading engine: {e}")
            raise TradingEngineException(
                message=f"Failed to start trading engine: {str(e)}",
                original_exception=e
            )
    
    async def stop(self):
        """Stop trading engine."""
        try:
            # Cancel all active orders
            await self.cancel_all_orders()
            
            # Disconnect from exchange
            await self.exchange.disconnect()
            
            logger.info("Trading engine stopped")
            
        except Exception as e:
            logger.error(f"Error stopping trading engine: {e}")
    
    def set_emergency_stop(self, enabled: bool):
        """Set emergency stop."""
        self.emergency_stop = enabled
        if enabled:
            logger.critical("TRADING EMERGENCY STOP ACTIVATED")
            asyncio.create_task(self.cancel_all_orders())
        else:
            logger.info("Trading emergency stop deactivated")
    
    async def execute_signal(
        self, 
        signal: TradeSignal, 
        current_price: float,
        position_size: float
    ) -> Optional[TradeExecution]:
        """
        Execute trading signal.
        
        Args:
            signal: Trading signal to execute
            current_price: Current market price
            position_size: Position size in BTC
            
        Returns:
            Trade execution result or None if not executed
        """
        try:
            # Safety checks
            if self.emergency_stop:
                logger.warning("Trade blocked: emergency stop active")
                return None
            
            if self.daily_trade_count >= self.daily_trade_limit:
                logger.warning("Trade blocked: daily trade limit reached")
                return None
            
            # Check cooldown period
            if await self._is_in_cooldown(signal.strategy_name):
                logger.debug(f"Trade blocked: {signal.strategy_name} in cooldown")
                return None
            
            # Create order from signal
            order = await self._create_order_from_signal(signal, current_price, position_size)
            
            # Execute order
            execution = await self.execute_order(order)
            
            if execution:
                # Update signal as executed
                signal.executed = True
                signal.execution_price = execution.price
                signal.execution_time = execution.created_at
                
                # Update cooldown
                self.trade_cooldown[signal.strategy_name] = datetime.now(timezone.utc)
                self.daily_trade_count += 1
                
                logger.info(f"Signal executed: {signal.strategy_name} {signal.signal_type}")
            
            return execution
            
        except Exception as e:
            logger.error(f"Signal execution error: {e}")
            raise TradingEngineException(
                message=f"Failed to execute signal: {str(e)}",
                context={"signal_id": str(signal.id)},
                original_exception=e
            )
    
    async def execute_order(self, order: TradeOrder) -> Optional[TradeExecution]:
        """
        Execute trade order.
        
        Args:
            order: Trade order to execute
            
        Returns:
            Trade execution result or None if not executed
        """
        try:
            logger.info(f"Executing order: {order.side.value} {order.quantity:.6f} BTC")
            
            # Validate order
            await self._validate_order(order)
            
            # Place order on exchange
            exchange_order_id = await self.exchange.place_order(order)
            order.exchange_order_id = exchange_order_id
            order.status = OrderStatus.PENDING
            
            # Track active order
            self.active_orders[exchange_order_id] = order
            
            # Monitor order execution
            execution = await self._monitor_order_execution(order)
            
            if execution:
                # Calculate execution quality
                quality = await self._calculate_execution_quality(order, execution)
                execution.slippage = quality.slippage
                execution.market_impact = quality.market_impact
                
                # Save to database
                await self.database.save_trade(execution)
                
                logger.info(
                    f"Order executed: {execution.quantity:.6f} BTC at ${execution.price:.2f} "
                    f"(slippage: {quality.slippage:.3f}%)"
                )
            
            return execution
            
        except Exception as e:
            logger.error(f"Order execution error: {e}")
            # Clean up failed order
            if order.exchange_order_id and order.exchange_order_id in self.active_orders:
                del self.active_orders[order.exchange_order_id]
            
            raise OrderExecutionException(
                message=f"Failed to execute order: {str(e)}",
                order_id=str(order.id),
                original_exception=e
            )
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel specific order."""
        try:
            if order_id in self.active_orders:
                success = await self.exchange.cancel_order(order_id)
                if success:
                    order = self.active_orders[order_id]
                    order.status = OrderStatus.CANCELLED
                    del self.active_orders[order_id]
                    logger.info(f"Order cancelled: {order_id}")
                return success
            else:
                logger.warning(f"Order not found for cancellation: {order_id}")
                return False
                
        except Exception as e:
            logger.error(f"Order cancellation error: {e}")
            return False
    
    async def cancel_all_orders(self):
        """Cancel all active orders."""
        try:
            cancellation_tasks = []
            for order_id in list(self.active_orders.keys()):
                task = asyncio.create_task(self.cancel_order(order_id))
                cancellation_tasks.append(task)
            
            if cancellation_tasks:
                await asyncio.gather(*cancellation_tasks, return_exceptions=True)
                logger.info(f"Cancelled {len(cancellation_tasks)} orders")
            
        except Exception as e:
            logger.error(f"Bulk order cancellation error: {e}")
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get current account balances."""
        try:
            return await self.exchange.get_account_balance()
        except Exception as e:
            logger.error(f"Balance retrieval error: {e}")
            return {}
    
    async def get_orderbook(self, symbol: str = "BTC-USD") -> Optional[Orderbook]:
        """Get current order book."""
        try:
            return await self.exchange.get_orderbook(symbol)
        except Exception as e:
            logger.error(f"Orderbook retrieval error: {e}")
            return None
    
    def get_execution_quality_stats(self) -> Dict[str, float]:
        """Get execution quality statistics."""
        if not self.execution_history:
            return {}
        
        slippages = [eq.slippage for eq in self.execution_history]
        execution_times = [eq.execution_time for eq in self.execution_history]
        fill_rates = [eq.fill_rate for eq in self.execution_history]
        
        return {
            "avg_slippage": sum(slippages) / len(slippages),
            "max_slippage": max(slippages),
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "avg_fill_rate": sum(fill_rates) / len(fill_rates),
            "total_executions": len(self.execution_history)
        }
    
    # Helper methods
    async def _validate_order(self, order: TradeOrder):
        """Validate order before execution."""
        if order.quantity <= 0:
            raise InvalidOrderException("Order quantity must be positive", order.dict())
        
        if order.order_type == OrderType.LIMIT and not order.price:
            raise InvalidOrderException("Limit orders require price", order.dict())
        
        if order.order_type == OrderType.STOP_LOSS and not order.stop_price:
            raise InvalidOrderException("Stop loss orders require stop price", order.dict())
        
        # Check account balance
        balances = await self.exchange.get_account_balance()
        
        if order.side == OrderSide.BUY:
            required_usd = order.quantity * (order.price or 50000)  # Estimate
            if balances.get("USD", 0) < required_usd:
                raise InsufficientFundsException(required_usd, balances.get("USD", 0), "USD")
        
        else:  # SELL
            if balances.get("BTC", 0) < order.quantity:
                raise InsufficientFundsException(order.quantity, balances.get("BTC", 0), "BTC")
    
    async def _create_order_from_signal(
        self, 
        signal: TradeSignal, 
        current_price: float, 
        position_size: float
    ) -> TradeOrder:
        """Create order from trading signal."""
        # Determine order side
        if signal.signal_type.value == "BUY":
            side = OrderSide.BUY
        elif signal.signal_type.value == "SELL":
            side = OrderSide.SELL
        else:
            raise InvalidOrderException(f"Invalid signal type: {signal.signal_type}")
        
        # Determine order type based on execution strategy
        if self.execution_strategy == ExecutionStrategy.AGGRESSIVE:
            order_type = OrderType.MARKET
            price = None
        else:
            order_type = OrderType.LIMIT
            # Set limit price with small buffer
            if side == OrderSide.BUY:
                price = current_price * 1.001  # 0.1% above market
            else:
                price = current_price * 0.999  # 0.1% below market
        
        return TradeOrder(
            strategy_name=signal.strategy_name,
            symbol=signal.symbol,
            order_type=order_type,
            side=side,
            quantity=position_size,
            price=price,
            time_in_force="GTC"
        )
    
    async def _monitor_order_execution(self, order: TradeOrder) -> Optional[TradeExecution]:
        """Monitor order until filled or timeout."""
        start_time = datetime.now(timezone.utc)
        timeout_time = start_time + timedelta(seconds=self.order_timeout)
        
        while datetime.now(timezone.utc) < timeout_time:
            try:
                status = await self.exchange.get_order_status(order.exchange_order_id)
                
                if status["status"] == "filled":
                    # Create execution record
                    execution = TradeExecution(
                        order_id=order.id,
                        strategy_name=order.strategy_name,
                        symbol=order.symbol,
                        side=order.side,
                        quantity=status["filled_size"],
                        price=status["executed_value"] / status["filled_size"],
                        fee=status["fill_fees"],
                        trade_id=order.exchange_order_id
                    )
                    
                    # Remove from active orders
                    if order.exchange_order_id in self.active_orders:
                        del self.active_orders[order.exchange_order_id]
                    
                    return execution
                
                elif status["status"] in ["cancelled", "rejected"]:
                    logger.warning(f"Order {order.exchange_order_id} {status['status']}")
                    if order.exchange_order_id in self.active_orders:
                        del self.active_orders[order.exchange_order_id]
                    return None
                
                # Check for partial fills
                if status["filled_size"] > 0:
                    order.filled_quantity = status["filled_size"]
                    logger.debug(f"Partial fill: {status['filled_size']}/{order.quantity}")
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Order monitoring error: {e}")
                await asyncio.sleep(5)  # Wait longer on error
        
        # Timeout reached - cancel order
        logger.warning(f"Order timeout: {order.exchange_order_id}")
        await self.cancel_order(order.exchange_order_id)
        return None
    
    async def _calculate_execution_quality(
        self, 
        order: TradeOrder, 
        execution: TradeExecution
    ) -> ExecutionQuality:
        """Calculate execution quality metrics."""
        # Get orderbook at execution time
        orderbook = await self.exchange.get_orderbook(order.symbol)
        
        if not orderbook:
            return ExecutionQuality(
                slippage=0.0,
                market_impact=0.0,
                fill_rate=1.0,
                execution_time=0.0,
                effective_spread=0.0,
                implementation_shortfall=0.0
            )
        
        # Calculate slippage
        if order.side == OrderSide.BUY:
            expected_price = orderbook.best_ask or execution.price
        else:
            expected_price = orderbook.best_bid or execution.price
        
        slippage = abs(execution.price - expected_price) / expected_price * 100
        
        # Calculate fill rate
        fill_rate = execution.quantity / order.quantity
        
        # Estimate market impact (simplified)
        spread = orderbook.spread or 0
        market_impact = spread / (2 * expected_price) * 100 if expected_price > 0 else 0
        
        # Calculate execution time
        execution_time = (execution.created_at - order.created_at).total_seconds()
        
        quality = ExecutionQuality(
            slippage=slippage,
            market_impact=market_impact,
            fill_rate=fill_rate,
            execution_time=execution_time,
            effective_spread=spread,
            implementation_shortfall=slippage + market_impact
        )
        
        # Store for statistics
        self.execution_history.append(quality)
        if len(self.execution_history) > 1000:  # Keep last 1000
            self.execution_history.pop(0)
        
        return quality
    
    async def _is_in_cooldown(self, strategy_name: str) -> bool:
        """Check if strategy is in cooldown period."""
        if strategy_name not in self.trade_cooldown:
            return False
        
        last_trade = self.trade_cooldown[strategy_name]
        cooldown_period = timedelta(hours=1)  # 1 hour cooldown
        
        return datetime.now(timezone.utc) - last_trade < cooldown_period
    
    async def _monitor_orders(self):
        """Background task to monitor active orders."""
        while True:
            try:
                if self.active_orders:
                    # Check status of all active orders
                    for order_id in list(self.active_orders.keys()):
                        try:
                            status = await self.exchange.get_order_status(order_id)
                            order = self.active_orders[order_id]
                            
                            # Update order status
                            if status["status"] == "filled":
                                order.status = OrderStatus.FILLED
                                order.filled_quantity = status["filled_size"]
                            elif status["status"] == "cancelled":
                                order.status = OrderStatus.CANCELLED
                            elif status["filled_size"] > order.filled_quantity:
                                order.status = OrderStatus.PARTIAL
                                order.filled_quantity = status["filled_size"]
                        
                        except Exception as e:
                            logger.error(f"Order status check error for {order_id}: {e}")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Order monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def health_check(self) -> Dict[str, Any]:
        """Trading engine health check."""
        try:
            balances = await self.get_account_balance()
            
            return {
                "connected": self.exchange.connected,
                "exchange": self.exchange.name,
                "paper_trading": self.paper_trading,
                "emergency_stop": self.emergency_stop,
                "active_orders": len(self.active_orders),
                "daily_trade_count": self.daily_trade_count,
                "daily_trade_limit": self.daily_trade_limit,
                "balances": balances,
                "execution_strategy": self.execution_strategy.value,
                "execution_quality": self.get_execution_quality_stats()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "emergency_stop": self.emergency_stop,
                "paper_trading": self.paper_trading
            }