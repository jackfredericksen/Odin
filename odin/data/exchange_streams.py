"""
Direct Exchange WebSocket Connections
Connects directly to exchange WebSocket APIs for real-time data streaming.
Inspired by flowsurface's approach - direct connections, no REST polling.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosed

from odin.utils.logging import get_logger

logger = get_logger(__name__)


class StreamType(Enum):
    TICKER = "ticker"
    TRADE = "trade"
    DEPTH = "depth"
    KLINE = "kline"


@dataclass
class StreamData:
    """Normalized data from exchange streams."""
    exchange: str
    symbol: str
    stream_type: StreamType
    timestamp: float
    data: Dict[str, Any]


@dataclass
class ExchangeStream:
    """Represents an active stream subscription."""
    exchange: str
    symbol: str
    stream_type: StreamType
    subscribers: Set[str] = field(default_factory=set)


class ExchangeConnector(ABC):
    """Base class for exchange WebSocket connectors."""

    def __init__(self, on_data: Callable[[StreamData], None]):
        self.on_data = on_data
        self.ws = None
        self.subscriptions: Dict[str, Set[StreamType]] = {}
        self.running = False
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60

    @abstractmethod
    async def connect(self):
        """Connect to exchange WebSocket."""
        pass

    @abstractmethod
    async def subscribe(self, symbol: str, stream_types: List[StreamType]):
        """Subscribe to streams for a symbol."""
        pass

    @abstractmethod
    async def unsubscribe(self, symbol: str, stream_types: List[StreamType]):
        """Unsubscribe from streams."""
        pass

    @abstractmethod
    def _normalize_symbol(self, symbol: str) -> str:
        """Convert generic symbol to exchange format."""
        pass

    async def disconnect(self):
        """Disconnect from exchange."""
        self.running = False
        if self.ws:
            await self.ws.close()


class BinanceConnector(ExchangeConnector):
    """
    Direct WebSocket connection to Binance.
    Uses combined stream endpoint for multiple subscriptions.
    """

    WS_URL = "wss://stream.binance.com:9443/ws"
    COMBINED_URL = "wss://stream.binance.com:9443/stream"

    SYMBOL_MAP = {
        "BTC": "btcusdt",
        "ETH": "ethusdt",
        "SOL": "solusdt",
        "XRP": "xrpusdt",
        "BNB": "bnbusdt",
        "SUI": "suiusdt",
        "HYPE": "hypeusdt",
    }

    def __init__(self, on_data: Callable[[StreamData], None]):
        super().__init__(on_data)
        self.stream_id = 1
        self.pending_subscriptions: List[str] = []

    def _normalize_symbol(self, symbol: str) -> str:
        return self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.lower()}usdt")

    async def connect(self):
        """Connect to Binance WebSocket."""
        self.running = True
        while self.running:
            try:
                logger.info("Connecting to Binance WebSocket...")
                async with websockets.connect(
                    self.WS_URL,
                    ping_interval=20,
                    ping_timeout=10,
                ) as ws:
                    self.ws = ws
                    self.reconnect_delay = 1
                    logger.info("Connected to Binance WebSocket")

                    # Resubscribe to existing subscriptions
                    if self.subscriptions:
                        for symbol, stream_types in self.subscriptions.items():
                            await self._send_subscribe(symbol, list(stream_types))

                    # Process messages
                    await self._message_loop()

            except ConnectionClosed as e:
                logger.warning(f"Binance WebSocket closed: {e}")
            except Exception as e:
                logger.error(f"Binance WebSocket error: {e}")

            if self.running:
                logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(
                    self.reconnect_delay * 2, self.max_reconnect_delay
                )

    async def _message_loop(self):
        """Process incoming WebSocket messages."""
        async for message in self.ws:
            try:
                data = json.loads(message)
                await self._handle_message(data)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from Binance: {message[:100]}")
            except Exception as e:
                logger.error(f"Error processing Binance message: {e}")

    async def _handle_message(self, data: dict):
        """Parse and normalize Binance message."""
        # Combined stream format
        if "stream" in data:
            stream_name = data["stream"]
            payload = data["data"]
        else:
            stream_name = data.get("e", "")
            payload = data

        event_type = payload.get("e", "")

        if event_type == "24hrTicker" or "ticker" in stream_name:
            await self._handle_ticker(payload)
        elif event_type == "trade" or "trade" in stream_name:
            await self._handle_trade(payload)
        elif event_type == "depthUpdate" or "depth" in stream_name:
            await self._handle_depth(payload)
        elif event_type == "kline" or "kline" in stream_name:
            await self._handle_kline(payload)

    async def _handle_ticker(self, data: dict):
        """Process ticker update."""
        symbol = data.get("s", "").replace("USDT", "")
        stream_data = StreamData(
            exchange="binance",
            symbol=symbol,
            stream_type=StreamType.TICKER,
            timestamp=time.time(),
            data={
                "price": float(data.get("c", 0)),
                "change_24h": float(data.get("P", 0)),
                "high_24h": float(data.get("h", 0)),
                "low_24h": float(data.get("l", 0)),
                "volume_24h": float(data.get("v", 0)),
                "quote_volume": float(data.get("q", 0)),
            }
        )
        self.on_data(stream_data)

    async def _handle_trade(self, data: dict):
        """Process trade update."""
        symbol = data.get("s", "").replace("USDT", "")
        stream_data = StreamData(
            exchange="binance",
            symbol=symbol,
            stream_type=StreamType.TRADE,
            timestamp=time.time(),
            data={
                "price": float(data.get("p", 0)),
                "quantity": float(data.get("q", 0)),
                "side": "sell" if data.get("m", False) else "buy",
                "trade_time": data.get("T", 0),
            }
        )
        self.on_data(stream_data)

    async def _handle_depth(self, data: dict):
        """Process order book depth update."""
        symbol = data.get("s", "").replace("USDT", "")
        stream_data = StreamData(
            exchange="binance",
            symbol=symbol,
            stream_type=StreamType.DEPTH,
            timestamp=time.time(),
            data={
                "bids": [[float(p), float(q)] for p, q in data.get("b", [])],
                "asks": [[float(p), float(q)] for p, q in data.get("a", [])],
            }
        )
        self.on_data(stream_data)

    async def _handle_kline(self, data: dict):
        """Process kline/candlestick update."""
        kline = data.get("k", {})
        symbol = kline.get("s", "").replace("USDT", "")
        stream_data = StreamData(
            exchange="binance",
            symbol=symbol,
            stream_type=StreamType.KLINE,
            timestamp=time.time(),
            data={
                "open": float(kline.get("o", 0)),
                "high": float(kline.get("h", 0)),
                "low": float(kline.get("l", 0)),
                "close": float(kline.get("c", 0)),
                "volume": float(kline.get("v", 0)),
                "interval": kline.get("i", "1m"),
                "is_closed": kline.get("x", False),
            }
        )
        self.on_data(stream_data)

    async def subscribe(self, symbol: str, stream_types: List[StreamType]):
        """Subscribe to Binance streams."""
        binance_symbol = self._normalize_symbol(symbol)

        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = set()
        self.subscriptions[symbol].update(stream_types)

        if self.ws and self.ws.open:
            await self._send_subscribe(symbol, stream_types)

    async def _send_subscribe(self, symbol: str, stream_types: List[StreamType]):
        """Send subscription request to Binance."""
        binance_symbol = self._normalize_symbol(symbol)
        streams = []

        for st in stream_types:
            if st == StreamType.TICKER:
                streams.append(f"{binance_symbol}@ticker")
            elif st == StreamType.TRADE:
                streams.append(f"{binance_symbol}@trade")
            elif st == StreamType.DEPTH:
                streams.append(f"{binance_symbol}@depth@100ms")
            elif st == StreamType.KLINE:
                streams.append(f"{binance_symbol}@kline_1m")

        if streams:
            msg = {
                "method": "SUBSCRIBE",
                "params": streams,
                "id": self.stream_id
            }
            self.stream_id += 1
            await self.ws.send(json.dumps(msg))
            logger.info(f"Subscribed to Binance streams: {streams}")

    async def unsubscribe(self, symbol: str, stream_types: List[StreamType]):
        """Unsubscribe from Binance streams."""
        if symbol in self.subscriptions:
            self.subscriptions[symbol] -= set(stream_types)
            if not self.subscriptions[symbol]:
                del self.subscriptions[symbol]

        if self.ws and self.ws.open:
            binance_symbol = self._normalize_symbol(symbol)
            streams = []
            for st in stream_types:
                if st == StreamType.TICKER:
                    streams.append(f"{binance_symbol}@ticker")
                elif st == StreamType.TRADE:
                    streams.append(f"{binance_symbol}@trade")
                elif st == StreamType.DEPTH:
                    streams.append(f"{binance_symbol}@depth@100ms")

            if streams:
                msg = {
                    "method": "UNSUBSCRIBE",
                    "params": streams,
                    "id": self.stream_id
                }
                self.stream_id += 1
                await self.ws.send(json.dumps(msg))


class KrakenConnector(ExchangeConnector):
    """
    Direct WebSocket connection to Kraken.
    """

    WS_URL = "wss://ws.kraken.com"

    SYMBOL_MAP = {
        "BTC": "XBT/USD",
        "ETH": "ETH/USD",
        "SOL": "SOL/USD",
        "XRP": "XRP/USD",
        "BNB": "BNB/USD",
        "SUI": "SUI/USD",
    }

    def _normalize_symbol(self, symbol: str) -> str:
        return self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}/USD")

    async def connect(self):
        """Connect to Kraken WebSocket."""
        self.running = True
        while self.running:
            try:
                logger.info("Connecting to Kraken WebSocket...")
                async with websockets.connect(
                    self.WS_URL,
                    ping_interval=30,
                ) as ws:
                    self.ws = ws
                    self.reconnect_delay = 1
                    logger.info("Connected to Kraken WebSocket")

                    # Resubscribe
                    if self.subscriptions:
                        for symbol, stream_types in self.subscriptions.items():
                            await self._send_subscribe(symbol, list(stream_types))

                    await self._message_loop()

            except ConnectionClosed as e:
                logger.warning(f"Kraken WebSocket closed: {e}")
            except Exception as e:
                logger.error(f"Kraken WebSocket error: {e}")

            if self.running:
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(
                    self.reconnect_delay * 2, self.max_reconnect_delay
                )

    async def _message_loop(self):
        """Process Kraken messages."""
        async for message in self.ws:
            try:
                data = json.loads(message)
                await self._handle_message(data)
            except Exception as e:
                logger.error(f"Error processing Kraken message: {e}")

    async def _handle_message(self, data):
        """Parse Kraken message format."""
        # Kraken sends arrays for data, dicts for status
        if isinstance(data, dict):
            # Status/subscription message
            return

        if isinstance(data, list) and len(data) >= 4:
            channel_name = data[-2]
            pair = data[-1]
            payload = data[1]

            # Extract symbol
            symbol = pair.replace("/USD", "").replace("XBT", "BTC")

            if channel_name == "ticker":
                await self._handle_ticker(symbol, payload)
            elif channel_name == "trade":
                await self._handle_trade(symbol, payload)
            elif channel_name.startswith("book"):
                await self._handle_depth(symbol, payload)

    async def _handle_ticker(self, symbol: str, data: dict):
        """Process Kraken ticker."""
        stream_data = StreamData(
            exchange="kraken",
            symbol=symbol,
            stream_type=StreamType.TICKER,
            timestamp=time.time(),
            data={
                "price": float(data.get("c", [0])[0]),
                "high_24h": float(data.get("h", [0, 0])[1]),
                "low_24h": float(data.get("l", [0, 0])[1]),
                "volume_24h": float(data.get("v", [0, 0])[1]),
                "bid": float(data.get("b", [0])[0]),
                "ask": float(data.get("a", [0])[0]),
            }
        )
        self.on_data(stream_data)

    async def _handle_trade(self, symbol: str, trades: list):
        """Process Kraken trades."""
        for trade in trades:
            stream_data = StreamData(
                exchange="kraken",
                symbol=symbol,
                stream_type=StreamType.TRADE,
                timestamp=time.time(),
                data={
                    "price": float(trade[0]),
                    "quantity": float(trade[1]),
                    "side": "buy" if trade[3] == "b" else "sell",
                    "trade_time": float(trade[2]),
                }
            )
            self.on_data(stream_data)

    async def _handle_depth(self, symbol: str, data: dict):
        """Process Kraken order book."""
        stream_data = StreamData(
            exchange="kraken",
            symbol=symbol,
            stream_type=StreamType.DEPTH,
            timestamp=time.time(),
            data={
                "bids": [[float(p), float(q)] for p, q, _ in data.get("bs", data.get("b", []))],
                "asks": [[float(p), float(q)] for p, q, _ in data.get("as", data.get("a", []))],
            }
        )
        self.on_data(stream_data)

    async def subscribe(self, symbol: str, stream_types: List[StreamType]):
        """Subscribe to Kraken streams."""
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = set()
        self.subscriptions[symbol].update(stream_types)

        if self.ws and self.ws.open:
            await self._send_subscribe(symbol, stream_types)

    async def _send_subscribe(self, symbol: str, stream_types: List[StreamType]):
        """Send Kraken subscription."""
        kraken_symbol = self._normalize_symbol(symbol)

        for st in stream_types:
            if st == StreamType.TICKER:
                msg = {
                    "event": "subscribe",
                    "pair": [kraken_symbol],
                    "subscription": {"name": "ticker"}
                }
            elif st == StreamType.TRADE:
                msg = {
                    "event": "subscribe",
                    "pair": [kraken_symbol],
                    "subscription": {"name": "trade"}
                }
            elif st == StreamType.DEPTH:
                msg = {
                    "event": "subscribe",
                    "pair": [kraken_symbol],
                    "subscription": {"name": "book", "depth": 10}
                }
            else:
                continue

            await self.ws.send(json.dumps(msg))
            logger.info(f"Subscribed to Kraken {st.value} for {symbol}")

    async def unsubscribe(self, symbol: str, stream_types: List[StreamType]):
        """Unsubscribe from Kraken."""
        if symbol in self.subscriptions:
            self.subscriptions[symbol] -= set(stream_types)

        if self.ws and self.ws.open:
            kraken_symbol = self._normalize_symbol(symbol)
            for st in stream_types:
                msg = {
                    "event": "unsubscribe",
                    "pair": [kraken_symbol],
                    "subscription": {"name": st.value}
                }
                await self.ws.send(json.dumps(msg))


class StreamManager:
    """
    Manages all exchange connections and routes data to subscribers.
    Implements pause→buffer→resume pattern for instant symbol switching.
    """

    def __init__(self):
        self.connectors: Dict[str, ExchangeConnector] = {}
        self.subscribers: Dict[str, Set[Callable]] = {}  # symbol -> callbacks
        self.paused_symbols: Set[str] = set()
        self.buffers: Dict[str, List[StreamData]] = {}
        self.latest_data: Dict[str, StreamData] = {}  # symbol -> latest ticker
        self._lock = asyncio.Lock()

    def _on_stream_data(self, data: StreamData):
        """Handle incoming stream data."""
        symbol = data.symbol.upper()

        # Always update latest data cache
        if data.stream_type == StreamType.TICKER:
            self.latest_data[symbol] = data

        # Check if symbol is paused (during switching)
        if symbol in self.paused_symbols:
            if symbol not in self.buffers:
                self.buffers[symbol] = []
            self.buffers[symbol].append(data)
            return

        # Route to subscribers
        if symbol in self.subscribers:
            for callback in self.subscribers[symbol]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in stream callback: {e}")

    async def start(self, exchanges: List[str] = None):
        """Start exchange connections."""
        if exchanges is None:
            exchanges = ["binance"]  # Default to Binance for speed

        tasks = []
        for exchange in exchanges:
            if exchange == "binance":
                connector = BinanceConnector(self._on_stream_data)
            elif exchange == "kraken":
                connector = KrakenConnector(self._on_stream_data)
            else:
                continue

            self.connectors[exchange] = connector
            tasks.append(asyncio.create_task(connector.connect()))

        if tasks:
            logger.info(f"Started {len(tasks)} exchange connections")

    async def stop(self):
        """Stop all connections."""
        for connector in self.connectors.values():
            await connector.disconnect()

    async def subscribe(
        self,
        symbol: str,
        callback: Callable[[StreamData], None],
        stream_types: List[StreamType] = None,
        exchange: str = "binance"
    ):
        """Subscribe to symbol data."""
        symbol = symbol.upper()
        if stream_types is None:
            stream_types = [StreamType.TICKER, StreamType.TRADE]

        async with self._lock:
            if symbol not in self.subscribers:
                self.subscribers[symbol] = set()
            self.subscribers[symbol].add(callback)

        # Subscribe on exchange
        if exchange in self.connectors:
            await self.connectors[exchange].subscribe(symbol, stream_types)

        # Send cached data immediately if available
        if symbol in self.latest_data:
            callback(self.latest_data[symbol])

    async def unsubscribe(self, symbol: str, callback: Callable):
        """Unsubscribe from symbol."""
        symbol = symbol.upper()
        async with self._lock:
            if symbol in self.subscribers:
                self.subscribers[symbol].discard(callback)

    async def switch_symbol(
        self,
        old_symbol: str,
        new_symbol: str,
        callback: Callable[[StreamData], None],
        exchange: str = "binance"
    ) -> Optional[StreamData]:
        """
        Instant symbol switch using pause→buffer→resume pattern.
        Returns cached data for new symbol immediately if available.
        """
        old_symbol = old_symbol.upper()
        new_symbol = new_symbol.upper()

        async with self._lock:
            # 1. Pause old symbol
            self.paused_symbols.add(old_symbol)

            # 2. Unsubscribe callback from old
            if old_symbol in self.subscribers:
                self.subscribers[old_symbol].discard(callback)

            # 3. Subscribe to new symbol
            if new_symbol not in self.subscribers:
                self.subscribers[new_symbol] = set()
            self.subscribers[new_symbol].add(callback)

        # 4. Subscribe on exchange
        if exchange in self.connectors:
            await self.connectors[exchange].subscribe(
                new_symbol,
                [StreamType.TICKER, StreamType.TRADE]
            )

        # 5. Return cached data immediately
        cached = self.latest_data.get(new_symbol)

        # 6. Resume old symbol and flush buffer (in background)
        asyncio.create_task(self._resume_symbol(old_symbol))

        return cached

    async def _resume_symbol(self, symbol: str):
        """Resume symbol and flush buffered data."""
        await asyncio.sleep(0.1)  # Small delay for stability

        async with self._lock:
            self.paused_symbols.discard(symbol)

            # Flush buffer to remaining subscribers
            if symbol in self.buffers and symbol in self.subscribers:
                for data in self.buffers[symbol]:
                    for callback in self.subscribers[symbol]:
                        try:
                            callback(data)
                        except Exception:
                            pass
                del self.buffers[symbol]

    def get_latest(self, symbol: str) -> Optional[StreamData]:
        """Get latest cached data for symbol."""
        return self.latest_data.get(symbol.upper())


# Global stream manager instance
_stream_manager: Optional[StreamManager] = None


def get_stream_manager() -> StreamManager:
    """Get or create global stream manager."""
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = StreamManager()
    return _stream_manager
