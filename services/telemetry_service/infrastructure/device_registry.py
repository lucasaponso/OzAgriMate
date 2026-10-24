"""Local registry of provisioned devices per farm.

Holds only references, not farm records. In production it is kept up to date from
farm and device events on the event broker (ADR 07).
"""

from __future__ import annotations

from services.telemetry_service.domain.models import Device, Metric as M


class InMemoryDeviceRegistry:
    def __init__(self) -> None:
        devices = [
            Device("dev-8", "farm-101", frozenset({M.SOIL_MOISTURE, M.SOIL_TEMPERATURE})),
            Device("dev-9", "farm-101", frozenset({M.RAINFALL, M.AIR_TEMPERATURE})),
            Device("dev-3", "farm-100", frozenset({M.SOIL_MOISTURE})),
            Device("dev-4", "farm-100", frozenset({M.AIR_TEMPERATURE})),
        ]
        self._devices = {d.device_id: d for d in devices}

    def find(self, device_id: str) -> Device | None:
        return self._devices.get(device_id)
