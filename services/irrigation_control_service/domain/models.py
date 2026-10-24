"""Irrigation control domain. This service is the authoritative owner of command states (ADR 07)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CommandAction(str, Enum):
    START = "START"
    STOP = "STOP"


class CommandStatus(str, Enum):
    ACCEPTED = "accepted"   # authorised, recorded and dispatched to the farm gateway
    REJECTED = "rejected"   # refused by authorisation
    EXECUTED = "executed"   # gateway confirmed the equipment acted (confirmed separately, ADR 08)
    FAILED = "failed"       # gateway reported the equipment did not act


@dataclass(frozen=True)
class IrrigationDevice:
    device_id: str
    farm_id: str
    kind: str


@dataclass
class IrrigationCommand:
    command_id: str
    farm_id: str
    device_id: str
    action: CommandAction
    duration_seconds: int | None
    status: CommandStatus
    submitted_at: datetime

    def same_request_as(self, farm_id: str, device_id: str, action: CommandAction, duration: int | None) -> bool:
        """Idempotency check: is a resubmission identical to the stored command?"""
        return (self.farm_id, self.device_id, self.action, self.duration_seconds) == (
            farm_id, device_id, action, duration,
        )
