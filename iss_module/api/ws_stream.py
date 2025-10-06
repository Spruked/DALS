"""
DALS Phase 1 WebSocket Stream
Real-time telemetry streaming for live dashboard updates
"""

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import List, Dict, Any, Set
import json
import asyncio
import logging
from datetime import datetime, timezone
import weakref

# Configure logging
logger = logging.getLogger(__name__)

# WebSocket router
ws_router = APIRouter()

# Connection manager for WebSocket clients
class TelemetryConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscription_map: Dict[WebSocket, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscription_map[websocket] = set()
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscription_map:
            del self.subscription_map[websocket]
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
        
    async def subscribe(self, websocket: WebSocket, modules: List[str]):
        """Subscribe WebSocket to specific module updates"""
        if websocket in self.subscription_map:
            self.subscription_map[websocket].update(modules)
            await self.send_personal_message(websocket, {
                "type": "subscription_update",
                "subscribed_modules": list(self.subscription_map[websocket]),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to client: {e}")
            self.disconnect(websocket)
            
    async def broadcast_telemetry(self, module: str, data: dict):
        """Broadcast telemetry data to subscribed clients"""
        if not self.active_connections:
            return
            
        message = {
            "type": "telemetry_update",
            "module": module,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                # Check if client is subscribed to this module
                subscriptions = self.subscription_map.get(connection, set())
                if not subscriptions or module in subscriptions or "all" in subscriptions:
                    await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to client: {e}")
                disconnected.append(connection)
                
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
            
    async def send_status_update(self, status_data: dict):
        """Send system status updates to all connected clients"""
        message = {
            "type": "status_update",
            "data": status_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send status update: {e}")
                disconnected.append(connection)
                
        # Remove disconnected clients  
        for connection in disconnected:
            self.disconnect(connection)

# Global connection manager instance
manager = TelemetryConnectionManager()

@ws_router.websocket("/ws/telemetry")
async def telemetry_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time telemetry streaming
    
    Client can send subscription messages to filter data:
    {"action": "subscribe", "modules": ["certsig", "caleon", "iss"]}
    {"action": "unsubscribe", "modules": ["certsig"]}
    {"action": "ping"}
    """
    await manager.connect(websocket)
    
    # Send welcome message
    await manager.send_personal_message(websocket, {
        "type": "welcome",
        "message": "Connected to DALS Phase 1 Telemetry Stream",
        "available_modules": ["certsig", "caleon", "iss"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "subscribe":
                    modules = message.get("modules", [])
                    await manager.subscribe(websocket, modules)
                    
                elif action == "unsubscribe":
                    modules = message.get("modules", [])
                    if websocket in manager.subscription_map:
                        for module in modules:
                            manager.subscription_map[websocket].discard(module)
                        await manager.send_personal_message(websocket, {
                            "type": "subscription_update",
                            "subscribed_modules": list(manager.subscription_map[websocket]),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                elif action == "ping":
                    await manager.send_personal_message(websocket, {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                else:
                    await manager.send_personal_message(websocket, {
                        "type": "error",
                        "message": f"Unknown action: {action}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
            except json.JSONDecodeError:
                await manager.send_personal_message(websocket, {
                    "type": "error", 
                    "message": "Invalid JSON message",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Function to broadcast telemetry from API endpoints
async def broadcast_telemetry_update(module: str, data: dict):
    """
    Called by telemetry API endpoints to broadcast updates
    """
    await manager.broadcast_telemetry(module, data)

# Function to broadcast status updates
async def broadcast_status_update(status_data: dict):
    """
    Called by system monitoring to broadcast status changes
    """
    await manager.send_status_update(status_data)

# Background task for periodic status updates
async def periodic_status_broadcaster():
    """
    Background task to send periodic system status updates
    """
    while True:
        try:
            # Import here to avoid circular imports
            from .telemetry_api import telemetry_cache
            
            # Calculate status from current telemetry cache
            total_packets = sum(len(data_list) for data_list in telemetry_cache.values())
            active_modules = sum(1 for data_list in telemetry_cache.values() if len(data_list) > 0)
            
            status_data = {
                "total_packets": total_packets,
                "active_modules": active_modules,
                "system_health": "optimal" if active_modules >= 2 else "degraded" if active_modules >= 1 else "offline",
                "connected_clients": len(manager.active_connections)
            }
            
            await manager.send_status_update(status_data)
            
        except Exception as e:
            logger.error(f"Status broadcaster error: {e}")
            
        # Wait 30 seconds before next update
        await asyncio.sleep(30)

# Heartbeat monitor for WebSocket connections
async def websocket_heartbeat_monitor():
    """
    Monitor WebSocket connections and send periodic heartbeats
    """
    while True:
        try:
            if manager.active_connections:
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "server_status": "active"
                }
                
                disconnected = []
                for connection in manager.active_connections:
                    try:
                        await connection.send_text(json.dumps(heartbeat_message))
                    except Exception as e:
                        logger.warning(f"Heartbeat failed for client: {e}")
                        disconnected.append(connection)
                
                # Remove disconnected clients
                for connection in disconnected:
                    manager.disconnect(connection)
                    
        except Exception as e:
            logger.error(f"Heartbeat monitor error: {e}")
            
        # Send heartbeat every 60 seconds
        await asyncio.sleep(60)