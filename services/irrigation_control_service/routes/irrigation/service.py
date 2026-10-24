"""Irrigation command use cases (runtime diagram B).

Submit: validate, authorise, de-duplicate by commandId, record, then dispatch to the gateway.
A retry with the same commandId and the same content returns the original result and is
not dispatched again, so a pump is never started twice. Reusing a commandId for a
different command returns 409.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from services.irrigation_control_service.domain.models import (
    CommandAction,
    CommandStatus,
    IrrigationCommand,
)
from services.irrigation_control_service.infrastructure.authorization_client import AuthorizationClient
from services.irrigation_control_service.infrastructure.command_repository import InMemoryCommandRepository
from services.irrigation_control_service.infrastructure.device_registry import (
    InMemoryIrrigationDeviceRegistry,
)
from services.irrigation_control_service.infrastructure.gateway_command_dispatcher import (
    StubMqttCommandDispatcher,
)
from services.shared.audit import InMemoryAuditLog
from services.shared.clock import utc_now
from services.shared.errors import bad_request, conflict, forbidden, not_found
from services.shared.events import DomainEvent, EventPublisher


@dataclass(frozen=True)
class SubmitCommand:
    command_id: str
    farm_id: str
    device_id: str
    action: CommandAction
    duration_seconds: int | None
    actor: str = "farm-manager"


@dataclass(frozen=True)
class SubmitResult:
    command: IrrigationCommand
    replayed: bool


class IrrigationCommandService:
    def __init__(
        self,
        repository: InMemoryCommandRepository,
        devices: InMemoryIrrigationDeviceRegistry,
        authorization: AuthorizationClient,
        dispatcher: StubMqttCommandDispatcher,
        publisher: EventPublisher,
        audit: InMemoryAuditLog,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._repository = repository
        self._devices = devices
        self._authorization = authorization
        self._dispatcher = dispatcher
        self._publisher = publisher
        self._audit = audit
        self._clock = clock

    def submit(self, cmd: SubmitCommand) -> SubmitResult:
        # Order follows runtime diagram B: validate -> authorise -> de-duplicate -> record -> dispatch.

        # 1. Validate the target equipment belongs to the farm.
        device = self._devices.find(cmd.device_id)
        if device is None or device.farm_id != cmd.farm_id:
            raise bad_request("unknown-device", f"Device '{cmd.device_id}' is not irrigation equipment on farm '{cmd.farm_id}'.")

        # 2. Authorise before anything is looked up or transmitted (ADR 06).
        if not self._authorization.can_operate(cmd.actor, cmd.farm_id, cmd.device_id):
            self._audit.record(cmd.actor, "IRRIGATION_COMMAND", cmd.command_id, "DENIED")
            raise forbidden(f"Not authorised to operate '{cmd.device_id}' on farm '{cmd.farm_id}'.")

        # 3. De-duplicate: a resubmitted command (e.g. a client retry) is not executed twice.
        existing = self._repository.get(cmd.command_id)
        if existing is not None:
            return self._replay_or_conflict(existing, cmd)

        # 4. Record, then 5. dispatch to the gateway.
        command = IrrigationCommand(
            cmd.command_id, cmd.farm_id, cmd.device_id, cmd.action, cmd.duration_seconds,
            CommandStatus.ACCEPTED, self._clock(),
        )
        raced = self._repository.add_if_absent(command)
        if raced is not None:
            return self._replay_or_conflict(raced, cmd)

        self._dispatcher.dispatch(command)
        self._audit.record(cmd.actor, "IRRIGATION_COMMAND", command.command_id)
        self._publisher.publish(
            DomainEvent(
                "IrrigationCommandAccepted",
                "irrigation-control-service",
                {"commandId": command.command_id, "farmId": command.farm_id, "deviceId": command.device_id,
                 "action": command.action.value, "durationSeconds": command.duration_seconds},
                correlation_id=command.command_id,
            )
        )
        return SubmitResult(command, replayed=False)

    def get_status(self, command_id: str) -> IrrigationCommand:
        command = self._repository.get(command_id)
        if command is None:
            raise not_found("Irrigation command", command_id)
        return command

    @staticmethod
    def _replay_or_conflict(existing: IrrigationCommand, cmd: SubmitCommand) -> SubmitResult:
        if existing.same_request_as(cmd.farm_id, cmd.device_id, cmd.action, cmd.duration_seconds):
            return SubmitResult(existing, replayed=True)
        raise conflict(
            "command-id-conflict",
            f"commandId '{cmd.command_id}' was already used for a different command.",
            commandId=cmd.command_id,
        )
