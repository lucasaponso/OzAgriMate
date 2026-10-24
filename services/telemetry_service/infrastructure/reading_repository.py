"""In-memory reading store. Stands in for the Telemetry DB (PostgreSQL, unique event IDs)."""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from services.telemetry_service.domain.models import Metric, Reading


class DuplicateReadingError(Exception):
    def __init__(self, reason: str, existing: Reading) -> None:
        super().__init__(reason)
        self.reason = reason
        self.existing = existing


class InMemoryReadingRepository:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_id: dict[str, Reading] = {}
        self._by_measurement: dict[tuple, Reading] = {}
        self._seed()

    def add(self, reading: Reading) -> None:
        """Insert atomically. Rejects a reused readingId or a repeated device/metric/timestamp."""
        with self._lock:
            if reading.reading_id in self._by_id:
                raise DuplicateReadingError("readingId", self._by_id[reading.reading_id])
            if reading.measurement_key in self._by_measurement:
                raise DuplicateReadingError("measurement", self._by_measurement[reading.measurement_key])
            self._by_id[reading.reading_id] = reading
            self._by_measurement[reading.measurement_key] = reading

    def latest_for_farm(self, farm_id: str) -> list[Reading]:
        """Most recent reading for each device and metric on the farm."""
        latest: dict[tuple[str, str], Reading] = {}
        for r in self._by_id.values():
            if r.farm_id != farm_id:
                continue
            key = (r.device_id, r.metric.value)
            if key not in latest or r.timestamp > latest[key].timestamp:
                latest[key] = r
        return sorted(latest.values(), key=lambda r: (r.device_id, r.metric.value))

    def _seed(self) -> None:
        # Dummy history for farm-100 only. farm-101 starts empty so the demo matches the API samples.
        base = datetime(2026, 10, 18, 1, 0, tzinfo=timezone.utc)
        rows = [
            ("r-10", "dev-3", Metric.SOIL_MOISTURE, 27.4, "percent", base),
            ("r-11", "dev-3", Metric.SOIL_MOISTURE, 26.9, "percent", base + timedelta(minutes=15)),
            ("r-12", "dev-4", Metric.AIR_TEMPERATURE, 21.3, "celsius", base + timedelta(minutes=15)),
        ]
        for reading_id, device, metric, value, unit, ts in rows:
            self.add(Reading(reading_id, "farm-100", device, metric, value, unit, ts, ts + timedelta(seconds=2)))
