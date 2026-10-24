"""Audit trail for sensitive operations such as irrigation commands (ADR 06)."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime

from services.shared.clock import utc_now

logger = logging.getLogger("ozagrimate.audit")


@dataclass(frozen=True)
class AuditEntry:
    actor: str
    action: str
    target: str
    outcome: str
    at: datetime = field(default_factory=utc_now)


class InMemoryAuditLog:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.entries: list[AuditEntry] = []

    def record(self, actor: str, action: str, target: str, outcome: str = "SUCCESS") -> AuditEntry:
        entry = AuditEntry(actor, action, target, outcome)
        with self._lock:
            self.entries.append(entry)
        logger.info("audit actor=%s action=%s target=%s outcome=%s", actor, action, target, outcome)
        return entry
