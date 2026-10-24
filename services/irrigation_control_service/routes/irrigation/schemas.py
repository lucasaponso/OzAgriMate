"""Request/response contracts for APIs 7-8, as documented in section 5 of the report."""

from __future__ import annotations

from pydantic import Field, model_validator

from services.irrigation_control_service.domain.models import CommandAction
from services.shared.api_models import CamelModel

MAX_DURATION_SECONDS = 4 * 60 * 60


class IrrigationCommandRequest(CamelModel):
    """Body for POST /api/v1/irrigation/commands."""

    command_id: str = Field(min_length=1, max_length=64, examples=["cmd-7"])
    farm_id: str = Field(min_length=1, max_length=64, examples=["farm-101"])
    device_id: str = Field(min_length=1, max_length=64, examples=["pump-2"])
    action: CommandAction = Field(examples=["START"])
    duration_seconds: int | None = Field(default=None, ge=1, le=MAX_DURATION_SECONDS, examples=[120])

    @model_validator(mode="after")
    def _duration_matches_action(self):
        if self.action is CommandAction.START and self.duration_seconds is None:
            raise ValueError("durationSeconds is required when action is START")
        if self.action is CommandAction.STOP and self.duration_seconds is not None:
            raise ValueError("durationSeconds must be omitted when action is STOP")
        return self


class CommandAcceptedResponse(CamelModel):
    command_id: str
    status: str


class CommandStatusResponse(CamelModel):
    command_id: str
    farm_id: str
    status: str
