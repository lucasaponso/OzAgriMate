"""Dispatches authorised commands to farm gateways (MQTT via AWS IoT Core in the deployment view).

The stub records the MQTT messages it would publish.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from services.irrigation_control_service.domain.models import IrrigationCommand

logger = logging.getLogger("ozagrimate.irrigation.dispatcher")


@dataclass(frozen=True)
class MqttMessage:
    topic: str
    payload: str
    qos: int = 1


class StubMqttCommandDispatcher:
    def __init__(self) -> None:
        self.sent: list[MqttMessage] = []

    def dispatch(self, command: IrrigationCommand) -> MqttMessage:
        message = MqttMessage(
            topic=f"ozagrimate/{command.farm_id}/{command.device_id}/commands",
            payload=json.dumps(
                {
                    "commandId": command.command_id,
                    "action": command.action.value,
                    "durationSeconds": command.duration_seconds,
                }
            ),
        )
        self.sent.append(message)
        logger.info("mqtt publish topic=%s payload=%s", message.topic, message.payload)
        return message
