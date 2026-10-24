"""MQTT protocol adapter (interoperability).

The deployment view shows gateways delivering readings over MQTT (AWS IoT Core) as well
as REST. This adapter maps an MQTT message onto the same submit command the REST
controller uses, so both paths share validation and de-duplication. It is not
connected to a broker in this prototype.
"""

from __future__ import annotations

import json
from datetime import datetime

from services.telemetry_service.routes.telemetry.service import SubmitReadingCommand


class MqttReadingAdapter:
    """Topic: ozagrimate/{farmId}/{deviceId}/readings, payload: {"id","m","v","u","ts"}."""

    def to_command(self, topic: str, payload: bytes) -> SubmitReadingCommand:
        _, farm_id, device_id, _ = topic.split("/")
        body = json.loads(payload)
        return SubmitReadingCommand(
            reading_id=body["id"],
            farm_id=farm_id,
            device_id=device_id,
            metric=body["m"],
            value=float(body["v"]),
            unit=body["u"],
            timestamp=datetime.fromisoformat(body["ts"].replace("Z", "+00:00")),
        )
