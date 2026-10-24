"""Domain event contract for the event-driven backbone (ADR 01).

Services publish events through the EventPublisher port. In production the adapter
publishes to the RabbitMQ event broker over AMQP. The brief does not require an event
bus, so the in-memory adapter records each event and logs it.
"""

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from services.shared.clock import utc_now

logger = logging.getLogger("ozagrimate.events")


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    source: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:12]}")
    correlation_id: str | None = None
    occurred_at: datetime = field(default_factory=utc_now)


class EventPublisher(Protocol):
    def publish(self, event: DomainEvent) -> None: ...


class InMemoryEventPublisher:
    """Stand-in for the RabbitMQ (AMQP) publisher."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.published: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        with self._lock:
            self.published.append(event)
        logger.info("event published type=%s source=%s id=%s", event.event_type, event.source, event.event_id)
