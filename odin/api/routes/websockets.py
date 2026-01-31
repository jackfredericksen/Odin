"""
WebSocket endpoints for real-time data streaming.
Uses DIRECT exchange WebSocket connections for instant data.
Implements pause→buffer→resume pattern for instant symbol switching.
"""

import asyncio
import json
import time
from typing import Dict, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from odin.api.routes.data import COIN_MAPPINGS
from odin.data.exchange_streams import (
    StreamData,
    StreamType,
    get_stream_manager,
)
from odin.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Track if stream manager has been started
_stream_manager_started = False


class ClientConnection:
    """Represents a connected WebSocket client with its subscriptions."""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.symbol: str = "BTC"
        self.subscribed_types: Set[StreamType] = {StreamType.TICKER}
        self.paused = False
        self.buffer: list = []

    async def send(self, data: dict):
        """Send data to client."""
        try:
            await self.websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")

    def on_stream_data(self, stream_data: StreamData):
        """Callback for stream data - queues for async send."""
        if self.paused:
            self.buffer.append(stream_data)
            return

        # Queue the send operation
        asyncio.create_task(self._send_stream_data(stream_data))

    async def _send_stream_data(self, stream_data: StreamData):
        """Send stream data to client."""
        message = {
            "type": "price_update",
            "symbol": stream_data.symbol,
            "exchange": stream_data.exchange,
            "stream_type": stream_data.stream_type.value,
            "data": stream_data.data,
            "timestamp": stream_data.timestamp,
        }
        await self.send(message)

    async def flush_buffer(self):
        """Flush buffered data after resume."""
        for data in self.buffer:
            await self._send_stream_data(data)
        self.buffer.clear()


class ConnectionManager:
    """Manages WebSocket connections with stream subscriptions."""

    def __init__(self):
        self.connections: Dict[WebSocket, ClientConnection] = {}

    async def connect(self, websocket: WebSocket) -> ClientConnection:
        """Accept new connection."""
        await websocket.accept()
        client = ClientConnection(websocket)
        self.connections[websocket] = client
        logger.info(f"WebSocket connected, total: {len(self.connections)}")
        return client

    def disconnect(self, websocket: WebSocket):
        """Remove connection."""
        if websocket in self.connections:
            del self.connections[websocket]
        logger.info(f"WebSocket disconnected, total: {len(self.connections)}")

    def get_client(self, websocket: WebSocket) -> Optional[ClientConnection]:
        """Get client for websocket."""
        return self.connections.get(websocket)


manager = ConnectionManager()


async def ensure_stream_manager_started():
    """Start the stream manager if not already running."""
    global _stream_manager_started
    if not _stream_manager_started:
        stream_mgr = get_stream_manager()
        asyncio.create_task(stream_mgr.start(["binance"]))
        _stream_manager_started = True
        logger.info("Stream manager started with Binance connection")
        # Give it a moment to connect
        await asyncio.sleep(1)


@router.websocket("/ws")
async def websocket_main_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time price data.
    Uses DIRECT exchange WebSocket connections.

    Client messages:
    - {"type": "switch_symbol", "symbol": "ETH"} - Instant symbol switch
    - {"type": "subscribe", "symbols": ["BTC", "ETH"]} - Subscribe to multiple
    - {"type": "ping"} - Heartbeat
    """
    # Ensure stream manager is running
    await ensure_stream_manager_started()

    client = await manager.connect(websocket)
    stream_mgr = get_stream_manager()

    try:
        # Send welcome message
        await client.send({
            "type": "connection",
            "message": "Connected to Odin - Direct Exchange Streams",
            "supported_symbols": list(COIN_MAPPINGS.keys()),
            "timestamp": time.time(),
        })

        # Subscribe to default symbol (BTC)
        await stream_mgr.subscribe(
            client.symbol,
            client.on_stream_data,
            [StreamType.TICKER, StreamType.TRADE],
        )

        # Send cached data immediately if available
        cached = stream_mgr.get_latest(client.symbol)
        if cached:
            await client._send_stream_data(cached)

        # Handle incoming messages
        async for message in websocket.iter_text():
            try:
                data = json.loads(message)
                await handle_client_message(client, data, stream_mgr)
            except json.JSONDecodeError:
                await client.send({
                    "type": "error",
                    "message": "Invalid JSON",
                    "timestamp": time.time(),
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup subscription
        await stream_mgr.unsubscribe(client.symbol, client.on_stream_data)
        manager.disconnect(websocket)


async def handle_client_message(
    client: ClientConnection,
    message: dict,
    stream_mgr
):
    """Handle incoming client message."""
    msg_type = message.get("type", "")

    if msg_type == "switch_symbol" or msg_type == "set_symbol":
        new_symbol = message.get("symbol", "BTC").upper()

        if new_symbol not in COIN_MAPPINGS:
            await client.send({
                "type": "error",
                "message": f"Unknown symbol: {new_symbol}",
                "timestamp": time.time(),
            })
            return

        if new_symbol == client.symbol:
            return  # Already on this symbol

        old_symbol = client.symbol
        logger.info(f"Switching {old_symbol} → {new_symbol}")

        # Pause client to buffer data during switch
        client.paused = True

        # Use stream manager's instant switch
        cached = await stream_mgr.switch_symbol(
            old_symbol,
            new_symbol,
            client.on_stream_data,
        )

        # Update client state
        client.symbol = new_symbol
        client.paused = False

        # Send cached data immediately (instant feedback!)
        if cached:
            await client._send_stream_data(cached)
            await client.send({
                "type": "symbol_switched",
                "symbol": new_symbol,
                "cached": True,
                "timestamp": time.time(),
            })
        else:
            await client.send({
                "type": "symbol_switched",
                "symbol": new_symbol,
                "cached": False,
                "timestamp": time.time(),
            })

        # Flush any buffered data
        await client.flush_buffer()

    elif msg_type == "subscribe":
        symbols = message.get("symbols", [])
        if isinstance(symbols, str):
            symbols = [symbols]

        for symbol in symbols:
            symbol = symbol.upper()
            if symbol in COIN_MAPPINGS:
                await stream_mgr.subscribe(
                    symbol,
                    client.on_stream_data,
                    [StreamType.TICKER],
                )

        await client.send({
            "type": "subscribed",
            "symbols": symbols,
            "timestamp": time.time(),
        })

    elif msg_type == "unsubscribe":
        symbols = message.get("symbols", [])
        for symbol in symbols:
            await stream_mgr.unsubscribe(symbol.upper(), client.on_stream_data)

    elif msg_type == "ping":
        await client.send({
            "type": "pong",
            "timestamp": time.time(),
        })

    elif msg_type == "request_data":
        # Send latest cached data
        cached = stream_mgr.get_latest(client.symbol)
        if cached:
            await client._send_stream_data(cached)


@router.websocket("/ws/stream/{symbol}")
async def websocket_symbol_stream(websocket: WebSocket, symbol: str):
    """
    Direct stream endpoint for a specific symbol.
    Connects directly to exchange WebSocket for that symbol.
    """
    symbol = symbol.upper()
    if symbol not in COIN_MAPPINGS:
        await websocket.close(code=4000, reason=f"Unknown symbol: {symbol}")
        return

    await ensure_stream_manager_started()
    client = await manager.connect(websocket)
    client.symbol = symbol
    stream_mgr = get_stream_manager()

    try:
        await client.send({
            "type": "connection",
            "message": f"Connected to {symbol} stream",
            "symbol": symbol,
            "timestamp": time.time(),
        })

        # Subscribe to symbol
        await stream_mgr.subscribe(
            symbol,
            client.on_stream_data,
            [StreamType.TICKER, StreamType.TRADE],
        )

        # Send cached data
        cached = stream_mgr.get_latest(symbol)
        if cached:
            await client._send_stream_data(cached)

        # Keep connection alive, handle messages
        async for message in websocket.iter_text():
            try:
                data = json.loads(message)
                if data.get("type") == "ping":
                    await client.send({"type": "pong", "timestamp": time.time()})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        pass
    finally:
        await stream_mgr.unsubscribe(symbol, client.on_stream_data)
        manager.disconnect(websocket)
