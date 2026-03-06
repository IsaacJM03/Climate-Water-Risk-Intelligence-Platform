from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections grouped by organization ID."""

    def __init__(self) -> None:
        self._connections: dict[int, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, org_id: int) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(org_id, []).append(websocket)
        logger.debug("WS connected org=%d total=%d", org_id, len(self._connections[org_id]))

    async def disconnect(self, websocket: WebSocket, org_id: int) -> None:
        async with self._lock:
            conns = self._connections.get(org_id, [])
            if websocket in conns:
                conns.remove(websocket)
        logger.debug("WS disconnected org=%d", org_id)

    async def broadcast_to_org(self, org_id: int, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        async with self._lock:
            conns = list(self._connections.get(org_id, []))

        for ws in conns:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                current = self._connections.get(org_id, [])
                self._connections[org_id] = [c for c in current if c not in dead]

    async def get_connection_count(self, org_id: int) -> int:
        async with self._lock:
            return len(self._connections.get(org_id, []))


manager = ConnectionManager()
