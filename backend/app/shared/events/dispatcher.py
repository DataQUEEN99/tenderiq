from typing import Callable, Dict, List
from app.shared.events.events import DomainEvent
from app.shared.logging.logger import app_logger


class EventDispatcher:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[DomainEvent], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)

    async def dispatch(self, event: DomainEvent) -> None:
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if hasattr(handler, "__call__"):
                    await handler(event) if hasattr(handler, "__await__") else handler(event)
            except Exception as exc:
                app_logger.error(
                    f"Event handler failed for {event.event_type}",
                    extra={"event_id": event.event_id, "error": str(exc)},
                )


event_dispatcher = EventDispatcher()