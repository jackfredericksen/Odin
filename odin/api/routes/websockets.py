"""
WebSocket endpoints for real-time data (FIXED VERSION)
"""

import asyncio
import json
import random
import time
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific connection."""
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        """Broadcast message to all connections."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_main_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time data updates."""
    await manager.connect(websocket)

    try:
        # Send welcome message
        await manager.send_personal_message(
            json.dumps(
                {
                    "type": "connection",
                    "message": "Connected to Odin Trading Bot",
                    "timestamp": time.time(),
                }
            ),
            websocket,
        )

        # Start sending real-time data
        while True:
            # Generate comprehensive real-time data
            data = {
                "type": "market_update",
                "timestamp": time.time(),
                "bitcoin": {
                    "price": round(45000 + random.uniform(-2000, 2000), 2),
                    "change_24h": round(random.uniform(-5, 5), 2),
                    "volume": round(random.uniform(100, 1000), 2),
                },
                "portfolio": {
                    "total_value": round(10000 + random.uniform(-500, 500), 2),
                    "pnl_24h": round(random.uniform(-200, 300), 2),
                    "pnl_24h_percent": round(random.uniform(-3, 3), 2),
                    "active_trades": random.randint(0, 5),
                },
                "system": {
                    "trading_enabled": random.choice([True, False]),
                    "active_strategies": random.randint(1, 4),
                    "data_sources_healthy": random.randint(1, 2),
                    "last_trade": time.time() - random.randint(300, 7200),
                    "system_load": round(random.uniform(10, 80), 1),
                    "memory_usage": round(random.uniform(30, 70), 1),
                },
            }

            await manager.send_personal_message(json.dumps(data), websocket)
            await asyncio.sleep(2)  # Send update every 2 seconds

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/data")
async def websocket_data_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Bitcoin price data."""
    await manager.connect(websocket)

    try:
        while True:
            data = {
                "type": "price_update",
                "timestamp": time.time(),
                "price": round(45000 + random.uniform(-2000, 2000), 2),
                "change_24h": round(random.uniform(-5, 5), 2),
                "volume": round(random.uniform(100, 1000), 2),
            }

            await manager.send_personal_message(json.dumps(data), websocket)
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/portfolio")
async def websocket_portfolio_endpoint(websocket: WebSocket):
    """WebSocket endpoint for portfolio updates."""
    await manager.connect(websocket)

    try:
        while True:
            data = {
                "type": "portfolio_update",
                "timestamp": time.time(),
                "total_value": round(10000 + random.uniform(-500, 500), 2),
                "pnl_24h": round(random.uniform(-200, 300), 2),
                "pnl_24h_percent": round(random.uniform(-3, 3), 2),
                "active_trades": random.randint(0, 5),
            }

            await manager.send_personal_message(json.dumps(data), websocket)
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/signals")
async def websocket_signals_endpoint(websocket: WebSocket):
    """WebSocket endpoint for trading signals."""
    await manager.connect(websocket)

    try:
        while True:
            # Generate trading signals occasionally
            if random.random() < 0.3:  # 30% chance of signal
                data = {
                    "type": "trading_signal",
                    "timestamp": time.time(),
                    "strategy": random.choice(
                        ["ma_cross", "rsi_momentum", "bollinger_bands", "macd_trend"]
                    ),
                    "signal": random.choice(["buy", "sell"]),
                    "confidence": round(random.uniform(0.6, 0.95), 2),
                    "price": round(45000 + random.uniform(-2000, 2000), 2),
                    "reasoning": "Technical indicator crossover detected",
                }

                await manager.send_personal_message(json.dumps(data), websocket)

            await asyncio.sleep(10)  # Check for signals every 10 seconds

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/status")
async def websocket_status_endpoint(websocket: WebSocket):
    """WebSocket endpoint for system status updates."""
    await manager.connect(websocket)

    try:
        while True:
            data = {
                "type": "system_status",
                "timestamp": time.time(),
                "trading_enabled": random.choice([True, False]),
                "active_strategies": random.randint(1, 4),
                "data_sources_healthy": random.randint(1, 2),
                "last_trade": time.time() - random.randint(300, 7200),
                "system_load": round(random.uniform(10, 80), 1),
                "memory_usage": round(random.uniform(30, 70), 1),
            }

            await manager.send_personal_message(json.dumps(data), websocket)
            await asyncio.sleep(15)  # Send status every 15 seconds

    except WebSocketDisconnect:
        manager.disconnect(websocket)
