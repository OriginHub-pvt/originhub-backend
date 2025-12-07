"""
WebSocket endpoints for real-time updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import time

router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active connections per idea
idea_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, idea_id: str):
        """Connect a client to an idea's update stream"""
        await websocket.accept()
        if idea_id not in self.active_connections:
            self.active_connections[idea_id] = set()
        self.active_connections[idea_id].add(websocket)

    def disconnect(self, websocket: WebSocket, idea_id: str):
        """Disconnect a client from an idea's update stream"""
        if idea_id in self.active_connections:
            self.active_connections[idea_id].discard(websocket)
            if not self.active_connections[idea_id]:
                del self.active_connections[idea_id]

    async def broadcast_to_idea(self, idea_id: str, message: dict):
        """Broadcast update to all clients viewing a specific idea"""
        if idea_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[idea_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)

            # Remove disconnected clients
            for connection in disconnected:
                self.disconnect(connection, idea_id)


manager = ConnectionManager()


@router.websocket("/ideas/{idea_id}/updates")
async def websocket_idea_updates(websocket: WebSocket, idea_id: str):
    """
    WebSocket endpoint for real-time idea updates (upvotes, views, etc.)

    Clients connect to receive real-time updates when:
    - Upvote count changes
    - View count changes
    - Idea is updated

    Usage:
        const ws = new WebSocket('ws://localhost:8000/ws/ideas/{idea_id}/updates');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Update:', data);
        };
    """
    await manager.connect(websocket, idea_id)
    try:
        while True:
            # Keep connection alive and handle ping/pong
            data = await websocket.receive_text()
            # Echo back for connection health check
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, idea_id)
    except Exception as e:
        manager.disconnect(websocket, idea_id)
        print(f"WebSocket error: {e}")


async def broadcast_upvote_update(
    idea_id: str, upvotes: int, user_id: str, action: str
):
    """
    Broadcast upvote update to all connected clients viewing this idea.
    Called from the upvote endpoints.

    Args:
        idea_id: UUID of the idea
        upvotes: New upvote count
        user_id: User who performed the action
        action: "upvoted" or "removed_upvote"
    """
    message = {
        "type": "upvote_update",
        "idea_id": idea_id,
        "upvotes": upvotes,
        "user_id": user_id,
        "action": action,
        "timestamp": time.time(),
    }
    await manager.broadcast_to_idea(idea_id, message)


async def broadcast_view_update(idea_id: str, views: int):
    """
    Broadcast view count update to all connected clients.

    Args:
        idea_id: UUID of the idea
        views: New view count
    """
    message = {
        "type": "view_update",
        "idea_id": idea_id,
        "views": views,
        "timestamp": time.time(),
    }
    await manager.broadcast_to_idea(idea_id, message)
