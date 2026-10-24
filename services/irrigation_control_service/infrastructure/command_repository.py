"""In-memory command store. Stands in for the Command DB (PostgreSQL): command details and execution status."""

from __future__ import annotations

import threading
from datetime import datetime, timezone

from services.irrigation_control_service.domain.models import (
    CommandAction,
    CommandStatus,
    IrrigationCommand,
)


class InMemoryCommandRepository:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._commands: dict[str, IrrigationCommand] = {}
        # Dummy history: an earlier command on farm-100 that the gateway confirmed.
        self._commands["cmd-5"] = IrrigationCommand(
            "cmd-5", "farm-100", "pump-1", CommandAction.START, 300, CommandStatus.EXECUTED,
            datetime(2026, 10, 17, 20, 0, tzinfo=timezone.utc),
        )

    def get(self, command_id: str) -> IrrigationCommand | None:
        return self._commands.get(command_id)

    def add_if_absent(self, command: IrrigationCommand) -> IrrigationCommand | None:
        """Insert atomically. Returns the existing command if the commandId is already taken."""
        with self._lock:
            existing = self._commands.get(command.command_id)
            if existing is None:
                self._commands[command.command_id] = command
            return existing
