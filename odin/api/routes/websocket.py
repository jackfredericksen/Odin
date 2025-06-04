"""
WebSocket Routes for Odin Bitcoin Trading Bot

Real-time data streaming via WebSockets for the dashboard.
Provides live Bitcoin price updates, trading signals, and system status.

File: odin/api/routes/websockets.py
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_count = 0
    
    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected WebSockets."""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)

# Global connection manager
manager = ConnectionManager()

# Create router
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time dashboard updates.
    
    Provides:
    - Bitcoin price updates
    - Portfolio changes
    - Trading signals
    - System status
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to Odin Trading Bot"
        }, websocket)
        
        # Send initial data
        await send_initial_data(websocket)
        
        # Start data streaming
        await start_data_stream(websocket)
        
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def send_initial_data(websocket: WebSocket):
    """Send initial data when client connects."""
    try:
        # Get current data
        from odin.core.data_collector import get_data_collector
        collector = get_data_collector()
        
        current_price = await collector.get_current_price()
        
        initial_data = {
            "type": "initial_data",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "bitcoin_price": current_price,
                "connection_status": "connected",
                "system_status": "operational"
            }
        }
        
        await manager.send_personal_message(initial_data, websocket)
        
    except Exception as e:
        logger.error(f"Failed to send initial data: {e}")

async def start_data_stream(websocket: WebSocket):
    """Start streaming real-time data to client."""
    try:
        from odin.core.data_collector import get_data_collector
        collector = get_data_collector()
        
        # Add callback for price updates
        async def price_callback(price_data):
            message = {
                "type": "price_update",
                "timestamp": datetime.now().isoformat(),
                "data": price_data
            }
            await manager.send_personal_message(message, websocket)
        
        collector.add_callback(price_callback)
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client message or timeout
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle client messages
                await handle_client_message(websocket, message)
                
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await manager.send_personal_message({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            except WebSocketDisconnect:
                break
                
        # Remove callback when disconnecting
        collector.remove_callback(price_callback)
        
    except Exception as e:
        logger.error(f"Data stream error: {e}")

async def handle_client_message(websocket: WebSocket, message: str):
    """Handle messages from WebSocket client."""
    try:
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "ping":
            # Respond to ping
            await manager.send_personal_message({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }, websocket)
            
        elif message_type == "request_data":
            # Client requesting specific data
            await handle_data_request(websocket, data)
            
        elif message_type == "subscribe":
            # Client subscribing to specific updates
            await handle_subscription(websocket, data)
            
        else:
            logger.warning(f"Unknown message type: {message_type}")
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON received from client")
    except Exception as e:
        logger.error(f"Error handling client message: {e}")

async def handle_data_request(websocket: WebSocket, data: dict):
    """Handle specific data requests from client."""
    try:
        request_type = data.get("request")
        
        if request_type == "portfolio":
            # Send portfolio data
            portfolio_data = {
                "type": "portfolio_data",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "total_value": 10000,
                    "btc_balance": 0.25,
                    "usd_balance": 8750,
                    "daily_pnl": 150.00,
                    "daily_pnl_percent": 1.5
                }
            }
            await manager.send_personal_message(portfolio_data, websocket)
            
        elif request_type == "strategies":
            # Send strategy data
            strategy_data = {
                "type": "strategy_data",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "active_strategies": 2,
                    "total_return": 12.5,
                    "best_strategy": "Moving Average"
                }
            }
            await manager.send_personal_message(strategy_data, websocket)
            
        elif request_type == "history":
            # Send historical data
            from odin.core.data_collector import get_data_collector
            collector = get_data_collector()
            
            hours = data.get("hours", 24)
            history = await collector.get_price_history(hours)
            
            history_data = {
                "type": "history_data",
                "timestamp": datetime.now().isoformat(),
                "data": history
            }
            await manager.send_personal_message(history_data, websocket)
            
    except Exception as e:
        logger.error(f"Error handling data request: {e}")

async def handle_subscription(websocket: WebSocket, data: dict):
    """Handle subscription requests from client."""
    try:
        channels = data.get("channels", [])
        
        response = {
            "type": "subscription_response",
            "timestamp": datetime.now().isoformat(),
            "subscribed_channels": channels,
            "status": "success"
        }
        
        await manager.send_personal_message(response, websocket)
        
    except Exception as e:
        logger.error(f"Error handling subscription: {e}")

# Broadcast functions for external use
async def broadcast_price_update(price_data: dict):
    """Broadcast price update to all connected clients."""
    message = {
        "type": "price_update",
        "timestamp": datetime.now().isoformat(),
        "data": price_data
    }
    await manager.broadcast(message)

async def broadcast_trade_signal(signal_data: dict):
    """Broadcast trading signal to all connected clients."""
    message = {
        "type": "trade_signal",
        "timestamp": datetime.now().isoformat(),
        "data": signal_data
    }
    await manager.broadcast(message)

async def broadcast_portfolio_update(portfolio_data: dict):
    """Broadcast portfolio update to all connected clients."""
    message = {
        "type": "portfolio_update",
        "timestamp": datetime.now().isoformat(),
        "data": portfolio_data
    }
    await manager.broadcast(message)

async def broadcast_system_alert(alert_data: dict):
    """Broadcast system alert to all connected clients."""
    message = {
        "type": "system_alert",
        "timestamp": datetime.now().isoformat(),
        "data": alert_data
    }
    await manager.broadcast(message)

def get_connection_manager():
    """Get the global connection manager."""
    return manager

# Health check for WebSocket system
async def websocket_health_check() -> dict:
    """Check WebSocket system health."""
    return {
        "websocket_enabled": True,
        "active_connections": manager.get_connection_count(),
        "status": "healthy"
    }