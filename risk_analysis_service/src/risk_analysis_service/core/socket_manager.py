from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect


class ConnectionManager:
    """Manages active WebSocket connections per organization.

    Keeps a mapping from organization UUID to a list of active WebSocket connections.
    Provides helpers to connect, disconnect, and broadcast alerts to all sockets
    associated with a given organization.
    """

    def __init__(self) -> None:
                                                                            
        self.active_connections: dict[UUID, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, org_id: UUID) -> None:
        """Accept a new WebSocket connection and associate it with an organization.

        Args:
            websocket: Incoming WebSocket connection.
            org_id: Organization UUID the connection belongs to.
        """
        await websocket.accept()
        self.active_connections.setdefault(org_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, org_id: UUID) -> None:
        """Remove a WebSocket connection from an organization's active list.

        Args:
            websocket: WebSocket connection to remove.
            org_id: Organization UUID the connection belongs to.
        """
        connections: Optional[list[WebSocket]] = self.active_connections.get(org_id)
        if not connections:
            return
        try:
            connections.remove(websocket)
        except ValueError:
                                                     
            pass
        if not connections:
                                                                      
            self.active_connections.pop(org_id, None)

    async def broadcast(self, alert: dict, org_id: UUID) -> None:
        """Broadcast an alert payload to all active sockets for an organization.

        Any sockets that fail during send (e.g., disconnected) are removed.

        Args:
            alert: JSON-serializable alert payload.
            org_id: Organization UUID to broadcast to.
        """
        connections = self.active_connections.get(org_id)
        if not connections:
            return

                                                                    
        for ws in list(connections):
            try:
                await ws.send_json(alert)
            except (WebSocketDisconnect, RuntimeError, ConnectionError, OSError):
                                                  
                self.disconnect(ws, org_id)
            except Exception:
                                                                                 
                self.disconnect(ws, org_id)


                                      
manager = ConnectionManager()
