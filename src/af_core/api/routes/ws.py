"""WebSocket endpoint for realtime mission events."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from af_core.services.event_bus import event_bus

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/missions/{mission_id}")
async def mission_ws(websocket: WebSocket, mission_id: str) -> None:
    """Stream mission events to connected clients in real time."""
    await websocket.accept()

    async def on_event(payload: dict) -> None:
        try:
            await websocket.send_text(json.dumps(payload))
        except Exception:
            pass

    event_bus.subscribe_mission(mission_id, on_event)
    try:
        while True:
            # Keep connection alive; client can send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        event_bus.unsubscribe_mission(mission_id, on_event)
