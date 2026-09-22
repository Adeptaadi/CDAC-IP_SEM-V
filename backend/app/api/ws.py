from typing import Dict, List, Any
from fastapi import WebSocket


class ConnectionManager:
    """Manages real-time WebSocket connections and broadcasts events to connected clients."""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, investigation_id: str):
        await websocket.accept()
        if investigation_id not in self.active_connections:
            self.active_connections[investigation_id] = []
        self.active_connections[investigation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, investigation_id: str):
        if investigation_id in self.active_connections:
            if websocket in self.active_connections[investigation_id]:
                self.active_connections[investigation_id].remove(websocket)
            if not self.active_connections[investigation_id]:
                del self.active_connections[investigation_id]

    async def broadcast_to_investigation(self, investigation_id: str, message: Dict[str, Any]):
        """Broadcasts an event payload to all clients watching a specific investigation."""
        if investigation_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[investigation_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)

            for dead in dead_connections:
                self.disconnect(dead, investigation_id)

    async def broadcast_global(self, message: Dict[str, Any]):
        """Broadcasts an event payload to all active connections across all investigations."""
        for inv_id in list(self.active_connections.keys()):
            await self.broadcast_to_investigation(inv_id, message)


ws_manager = ConnectionManager()
