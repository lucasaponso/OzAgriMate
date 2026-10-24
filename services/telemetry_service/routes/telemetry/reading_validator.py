"""Reading validator: checks device ownership, metric, unit, value range and timestamp."""

from __future__ import annotations

from datetime import datetime, timedelta

from services.shared.errors import bad_request
from services.telemetry_service.domain.models import METRIC_RULES, Device, Metric

MAX_CLOCK_SKEW = timedelta(minutes=5)


class ReadingValidator:
    def validate(
        self, *, farm_id: str, device: Device | None, device_id: str, metric: Metric,
        value: float, unit: str, timestamp: datetime, now: datetime,
    ) -> None:
        if device is None or device.farm_id != farm_id:
            raise bad_request("unknown-device", f"Device '{device_id}' is not registered to farm '{farm_id}'.")
        if metric not in device.metrics:
            raise bad_request("unsupported-metric", f"Device '{device_id}' does not report '{metric.value}'.")
        rule = METRIC_RULES[metric]
        if unit != rule.unit:
            raise bad_request("unit-mismatch", f"{metric.value} must use unit '{rule.unit}', got '{unit}'.")
        if not rule.min_value <= value <= rule.max_value:
            raise bad_request(
                "value-out-of-range",
                f"{metric.value} must be between {rule.min_value:g} and {rule.max_value:g} {rule.unit}.",
            )
        if timestamp > now + MAX_CLOCK_SKEW:
            raise bad_request("timestamp-in-future", "timestamp is ahead of server time.")
