"""Local registry of irrigation equipment per farm (kept up to date from device events in production)."""

from __future__ import annotations

from services.irrigation_control_service.domain.models import IrrigationDevice


class InMemoryIrrigationDeviceRegistry:
    def __init__(self) -> None:
        devices = [
            IrrigationDevice("pump-2", "farm-101", "pump"),
            IrrigationDevice("valve-4", "farm-101", "valve"),
            IrrigationDevice("pump-1", "farm-100", "pump"),
        ]
        self._devices = {d.device_id: d for d in devices}

    def find(self, device_id: str) -> IrrigationDevice | None:
        return self._devices.get(device_id)
