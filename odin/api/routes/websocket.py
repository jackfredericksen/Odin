"""
WebSocket endpoint for real-time data streaming in Odin Trading Bot
Clean version without circular imports.

File: odin/api/routes/websocket.py
Author: Odin Development Team
License: MIT
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

logger = logging.getLogger(__name__)

# WebSocket router
router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections for real-time data streaming."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_info[websocket] = {
            "client_id": client_id,
            "connected_at": datetime.now(),
            "last_ping": datetime.now()
        }
        logger.info(f"WebSocket connected: {client_id or 'unknown'} (Total: {len(self.active_connections)})")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            client_info = self.connection_info.pop(websocket, {})
            client_id = client_info.get("client_id", "unknown")
            logger.info(f"WebSocket disconnected: {client_id} (Total: {len(self.active_connections)})")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_json(self, data: dict):
        """Broadcast JSON data to all connected clients."""
        message = json.dumps(data)
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict]:
        """Get information about all active connections."""
        return [
            {
                "client_id": info.get("client_id"),
                "connected_at": info.get("connected_at").isoformat(),
                "last_ping": info.get("last_ping").isoformat()
            }
            for info in self.connection_info.values()
        ]

# Global connection manager instance
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """
    WebSocket endpoint for real-time data streaming.
    
    Supports the following message types:
    - price_update: Real-time Bitcoin price updates
    - portfolio_update: Portfolio value changes
    - strategy_signal: Trading strategy signals
    - trade_execution: Trade execution notifications
    - system_alert: System alerts and notifications
    """
    await manager.connect(websocket, client_id)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "data": {
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "message": "WebSocket connection established successfully"
            }
        }
        await manager.send_personal_message(json.dumps(welcome_message), websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client with timeout
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=300.0  # 5 minute timeout
                )
                
                # Parse incoming message
                try:
                    message = json.loads(data)
                    await handle_client_message(websocket, message)
                except json.JSONDecodeError:
                    error_response = {
                        "type": "error",
                        "data": {
                            "message": "Invalid JSON format",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    await manager.send_personal_message(json.dumps(error_response), websocket)
                
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                ping_message = {
                    "type": "ping",
                    "data": {
                        "timestamp": datetime.now().isoformat()
                    }
                }
                await manager.send_personal_message(json.dumps(ping_message), websocket)
                
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected normally")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket)

async def handle_client_message(websocket: WebSocket, message: dict):
    """Handle incoming messages from WebSocket clients."""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping with pong
        pong_response = {
            "type": "pong",
            "data": {
                "timestamp": datetime.now().isoformat()
            }
        }
        await manager.send_personal_message(json.dumps(pong_response), websocket)
        
        # Update last ping time
        if websocket in manager.connection_info:
            manager.connection_info[websocket]["last_ping"] = datetime.now()
    
    elif message_type == "pong":
        # Handle pong response
        if websocket in manager.connection_info:
            manager.connection_info[websocket]["last_ping"] = datetime.now()
    
    elif message_type == "subscribe":
        # Handle subscription to specific data feeds
        feeds = message.get("data", {}).get("feeds", [])
        response = {
            "type": "subscription_confirmed",
            "data": {
                "feeds": feeds,
                "timestamp": datetime.now().isoformat(),
                "message": f"Subscribed to {len(feeds)} feeds"
            }
        }
        await manager.send_personal_message(json.dumps(response), websocket)
    
    elif message_type == "unsubscribe":
        # Handle unsubscription
        feeds = message.get("data", {}).get("feeds", [])
        response = {
            "type": "unsubscription_confirmed",
            "data": {
                "feeds": feeds,
                "timestamp": datetime.now().isoformat(),
                "message": f"Unsubscribed from {len(feeds)} feeds"
            }
        }
        await manager.send_personal_message(json.dumps(response), websocket)
    
    else:
        # Unknown message type
        error_response = {
            "type": "error",
            "data": {
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.now().isoformat()
            }
        }
        await manager.send_personal_message(json.dumps(error_response), websocket)

# Utility functions for broadcasting data

async def broadcast_price_update(price_data: dict):
    """Broadcast Bitcoin price update to all connected clients."""
    if manager.get_connection_count() == 0:
        return  # No clients connected
    
    message = {
        "type": "price_update",
        "data": price_data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_json(message)

async def broadcast_portfolio_update(portfolio_data: dict):
    """Broadcast portfolio update to all connected clients."""
    if manager.get_connection_count() == 0:
        return  # No clients connected
    
    message = {
        "type": "portfolio_update",
        "data": portfolio_data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_json(message)

async def broadcast_strategy_signal(strategy_name: str, signal_type: str, confidence: float, price: float):
    """Broadcast strategy signal to all connected clients."""
    if manager.get_connection_count() == 0:
        return  # No clients connected
    
    message = {
        "type": "strategy_signal",
        "data": {
            "strategy": strategy_name,
            "signal": signal_type,
            "confidence": confidence,
            "price": price
        },
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_json(message)

async def broadcast_trade_execution(trade_data: dict):
    """Broadcast trade execution to all connected clients."""
    if manager.get_connection_count() == 0:
        return  # No clients connected
    
    message = {
        "type": "trade_execution",
        "data": trade_data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_json(message)

async def broadcast_system_alert(title: str, message_text: str, alert_type: str = "info"):
    """Broadcast system alert to all connected clients."""
    if manager.get_connection_count() == 0:
        return  # No clients connected
    
    message = {
        "type": "system_alert",
        "data": {
            "title": title,
            "message": message_text,
            "type": alert_type
        },
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_json(message)

async def broadcast_custom_message(message_type: str, data: dict):
    """Broadcast custom message to all connected clients."""
    if manager.get_connection_count() == 0:
        return  # No clients connected
    
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_json(message)

# Health check endpoint for WebSocket connections
@router.get("/ws/health")
async def websocket_health():
    """Get WebSocket connection health information."""
    return {
        "success": True,
        "data": {
            "active_connections": manager.get_connection_count(),
            "connection_info": manager.get_connection_info(),
            "websocket_enabled": True,
            "status": "healthy"
        },
        "timestamp": datetime.now().isoformat()
    }

# WebSocket statistics endpoint
@router.get("/ws/stats")
async def websocket_stats():
    """Get detailed WebSocket statistics."""
    return {
        "success": True,
        "data": {
            "total_connections": manager.get_connection_count(),
            "connection_details": manager.get_connection_info(),
            "server_time": datetime.now().isoformat(),
            "websocket_version": "1.0.0"
        }
    }

# Export all needed components
__all__ = [
    "router", 
    "manager", 
    "broadcast_price_update", 
    "broadcast_portfolio_update",
    "broadcast_strategy_signal", 
    "broadcast_trade_execution", 
    "broadcast_system_alert",
    "broadcast_custom_message"
]