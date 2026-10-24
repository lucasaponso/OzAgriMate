"""Telemetry use cases (runtime diagram A): validate, de-duplicate, store, then publish ReadingAccepted."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from services.shared.clock import utc_now
from services.shared.errors import bad_request, conflict, not_found
from services.shared.events import DomainEvent, EventPublisher
from services.telemetry_service.routes.telemetry.reading_validator import ReadingValidator
from services.telemetry_service.domain.models import Metric, Reading
from services.telemetry_service.infrastructure.device_registry import InMemoryDeviceRegistry
from services.telemetry_service.infrastructure.reading_repository import (
    DuplicateReadingError,
    InMemoryReadingRepository,
)


@dataclass(frozen=True)
class SubmitReadingCommand:
    reading_id: str
    farm_id: str
    device_id: str
    metric: str
    value: float
    unit: str
    timestamp: datetime


class TelemetryService:
    def __init__(
        self,
        repository: InMemoryReadingRepository,
        devices: InMemoryDeviceRegistry,
        publisher: EventPublisher,
        validator: ReadingValidator | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._repository = repository
        self._devices = devices
        self._publisher = publisher
        self._validator = validator or ReadingValidator()
        self._clock = clock

    def submit_reading(self, cmd: SubmitReadingCommand) -> Reading:
        now = self._clock()
        try:
            metric = Metric(cmd.metric)
        except ValueError:
            allowed = ", ".join(m.value for m in Metric)
            raise bad_request("unsupported-metric", f"metric must be one of: {allowed}.") from None

        self._validator.validate(
            farm_id=cmd.farm_id, device=self._devices.find(cmd.device_id), device_id=cmd.device_id,
            metric=metric, value=cmd.value, unit=cmd.unit, timestamp=cmd.timestamp, now=now,
        )
        reading = Reading(
            cmd.reading_id, cmd.farm_id, cmd.device_id, metric, cmd.value, cmd.unit, cmd.timestamp, now
        )
        try:
            self._repository.add(reading)
        except DuplicateReadingError as dup:
            if dup.reason == "readingId":
                raise conflict(
                    "duplicate-reading", f"Reading '{cmd.reading_id}' has already been accepted.",
                    readingId=cmd.reading_id,
                ) from None
            raise conflict(
                "duplicate-measurement",
                f"Device '{cmd.device_id}' already reported {metric.value} at this timestamp "
                f"(reading '{dup.existing.reading_id}').",
                readingId=dup.existing.reading_id,
            ) from None

        # Consumed by the Alert service (threshold rules) and the AI decision service.
        self._publisher.publish(
            DomainEvent(
                "ReadingAccepted",
                "telemetry-service",
                {
                    "readingId": reading.reading_id,
                    "farmId": reading.farm_id,
                    "deviceId": reading.device_id,
                    "metric": reading.metric.value,
                    "value": reading.value,
                    "unit": reading.unit,
                    "timestamp": reading.timestamp.isoformat(),
                },
                correlation_id=reading.reading_id,
            )
        )
        return reading

    def latest_readings(self, farm_id: str) -> list[Reading]:
        readings = self._repository.latest_for_farm(farm_id)
        if not readings:
            raise not_found("Telemetry for farm", farm_id)
        return readings
