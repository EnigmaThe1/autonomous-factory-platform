"""In-process event bus for mission events and WebSocket broadcast."""

import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger(__name__)

Listener = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class EventBus:
    """Simple pub/sub event bus for internal platform events.

    Listeners subscribe to event types. Events are dispatched asynchronously.
    WebSocket handlers subscribe to mission-specific channels.
    """

    def __init__(self) -> None:
        self._listeners: defaultdict[str, list[Listener]] = defaultdict(list)
        self._mission_listeners: defaultdict[str, list[Listener]] = defaultdict(list)

    def subscribe(self, event_type: str, listener: Listener) -> None:
        self._listeners[event_type].append(listener)

    def unsubscribe(self, event_type: str, listener: Listener) -> None:
        self._listeners[event_type] = [
            fn for fn in self._listeners[event_type] if fn is not listener
        ]

    def subscribe_mission(self, mission_id: str, listener: Listener) -> None:
        self._mission_listeners[mission_id].append(listener)

    def unsubscribe_mission(self, mission_id: str, listener: Listener) -> None:
        self._mission_listeners[mission_id] = [
            fn for fn in self._mission_listeners[mission_id] if fn is not listener
        ]

    async def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        tasks = []
        for fn in self._listeners.get(event_type, []):
            tasks.append(fn(payload))
        # Also notify mission-specific subscribers
        mission_id = payload.get("mission_id")
        if mission_id:
            for fn in self._mission_listeners.get(mission_id, []):
                tasks.append(fn(payload))
        for coro in tasks:
            try:
                await coro
            except Exception:
                logger.exception("Event listener error for %s", event_type)


# Singleton
event_bus = EventBus()
