"""Telemetry domain. This service is the authoritative owner of sensor measurements (ADR 07)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Metric(str, Enum):
    SOIL_MOISTURE = "soilMoisture"
    SOIL_TEMPERATURE = "soilTemperature"
    AIR_TEMPERATURE = "airTemperature"
    RAINFALL = "rainfall"
    FLOW_RATE = "flowRate"


@dataclass(frozen=True)
class MetricRule:
    unit: str
    min_value: float
    max_value: float


# Canonical data contract: protocol adapters map vendor payloads onto these units.
METRIC_RULES: dict[Metric, MetricRule] = {
    Metric.SOIL_MOISTURE: MetricRule("percent", 0, 100),
    Metric.SOIL_TEMPERATURE: MetricRule("celsius", -10, 60),
    Metric.AIR_TEMPERATURE: MetricRule("celsius", -20, 55),
    Metric.RAINFALL: MetricRule("mm", 0, 500),
    Metric.FLOW_RATE: MetricRule("litresPerMinute", 0, 5000),
}


@dataclass(frozen=True)
class Device:
    device_id: str
    farm_id: str
    metrics: frozenset[Metric]


@dataclass(frozen=True)
class Reading:
    reading_id: str
    farm_id: str
    device_id: str
    metric: Metric
    value: float
    unit: str
    timestamp: datetime
    received_at: datetime

    @property
    def measurement_key(self) -> tuple[str, str, datetime]:
        """One record per device, metric and timestamp."""
        return (self.device_id, self.metric.value, self.timestamp)
