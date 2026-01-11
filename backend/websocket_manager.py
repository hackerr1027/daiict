"""
WebSocket Manager for Real-Time Collaboration
Handles multi-user real-time updates, conflict resolution, and synchronization
"""

from typing import Dict, Set, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time collaboration"""
    
    def __init__(self):
        # Map of model_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket -> user info
        self.connection_info: Dict[WebSocket, Dict] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, model_id: str, user_id: Optional[str] = None):
        """Connect a user to a model's collaboration room"""
        await websocket.accept()
        
        async with self._lock:
            if model_id not in self.active_connections:
                self.active_connections[model_id] = set()
            
            self.active_connections[model_id].add(websocket)
            self.connection_info[websocket] = {
                "model_id": model_id,
                "user_id": user_id or f"user-{id(websocket)}",
                "connected_at": datetime.utcnow().isoformat()
            }
        
        # Notify others of new connection
        await self.broadcast_to_model(model_id, {
            "type": "user_joined",
            "user_id": user_id or f"user-{id(websocket)}",
            "timestamp": datetime.utcnow().isoformat()
        }, exclude=[websocket])
        
        # Send current state to new connection
        return self.connection_info[websocket]
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a user"""
        info = self.connection_info.get(websocket)
        if not info:
            return
        
        model_id = info["model_id"]
        user_id = info["user_id"]
        
        async with self._lock:
            if model_id in self.active_connections:
                self.active_connections[model_id].discard(websocket)
                if not self.active_connections[model_id]:
                    del self.active_connections[model_id]
            
            del self.connection_info[websocket]
        
        # Notify others of disconnection
        await self.broadcast_to_model(model_id, {
            "type": "user_left",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def broadcast_to_model(self, model_id: str, message: dict, exclude: Optional[List[WebSocket]] = None):
        """Broadcast message to all connections for a model"""
        if model_id not in self.active_connections:
            return
        
        exclude_set = set(exclude or [])
        disconnected = set()
        
        async with self._lock:
            connections = self.active_connections[model_id].copy()
        
        for connection in connections:
            if connection in exclude_set:
                continue
            
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        if disconnected:
            async with self._lock:
                self.active_connections[model_id] -= disconnected
                for conn in disconnected:
                    if conn in self.connection_info:
                        del self.connection_info[conn]
    
    async def handle_edit_event(self, websocket: WebSocket, event: dict):
        """Handle edit event from a client and broadcast to others"""
        info = self.connection_info.get(websocket)
        if not info:
            return
        
        model_id = info["model_id"]
        user_id = info["user_id"]
        
        # Broadcast edit event to other users (not sender)
        await self.broadcast_to_model(model_id, {
            "type": "edit_event",
            "user_id": user_id,
            "event": event,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude=[websocket])
    
    async def handle_cursor_position(self, websocket: WebSocket, position: dict):
        """Handle cursor position updates"""
        info = self.connection_info.get(websocket)
        if not info:
            return
        
        model_id = info["model_id"]
        user_id = info["user_id"]
        
        # Broadcast cursor position to others
        await self.broadcast_to_model(model_id, {
            "type": "cursor_update",
            "user_id": user_id,
            "position": position,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude=[websocket])
    
    async def get_active_users(self, model_id: str) -> List[Dict]:
        """Get list of active users for a model"""
        if model_id not in self.active_connections:
            return []
        
        users = []
        async with self._lock:
            connections = self.active_connections[model_id].copy()
        
        for conn in connections:
            if conn in self.connection_info:
                info = self.connection_info[conn]
                users.append({
                    "user_id": info["user_id"],
                    "connected_at": info["connected_at"]
                })
        
        return users


# Global connection manager instance
manager = ConnectionManager()
