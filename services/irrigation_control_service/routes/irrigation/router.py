"""Irrigation command controller: APIs 7-8."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, Response, status

from services.irrigation_control_service.routes.irrigation.schemas import (
    CommandAcceptedResponse,
    CommandStatusResponse,
    IrrigationCommandRequest,
)
from services.irrigation_control_service.routes.irrigation.service import (
    IrrigationCommandService,
    SubmitCommand,
)

router = APIRouter(prefix="/api/v1/irrigation", tags=["Irrigation"])

CommandId = Annotated[str, Path(alias="commandId", min_length=1, max_length=64)]


def get_service(request: Request) -> IrrigationCommandService:
    return request.app.state.command_service


@router.post(
    "/commands",
    response_model=CommandAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="API 7: Submit an idempotent irrigation command",
    responses={400: {"description": "Invalid command"}, 409: {"description": "commandId reused for a different command"}},
)
def submit_command(
    body: IrrigationCommandRequest,
    response: Response,
    service: IrrigationCommandService = Depends(get_service),
) -> CommandAcceptedResponse:
    result = service.submit(
        SubmitCommand(body.command_id, body.farm_id, body.device_id, body.action, body.duration_seconds)
    )
    response.headers["Location"] = f"/api/v1/irrigation/commands/{result.command.command_id}"
    if result.replayed:
        response.headers["Idempotent-Replayed"] = "true"
    return CommandAcceptedResponse(command_id=result.command.command_id, status=result.command.status.value)


@router.get(
    "/commands/{commandId}",
    response_model=CommandStatusResponse,
    summary="API 8: Check irrigation command processing status",
    responses={404: {"description": "Command not found"}},
)
def get_command_status(
    command_id: CommandId, service: IrrigationCommandService = Depends(get_service)
) -> CommandStatusResponse:
    command = service.get_status(command_id)
    return CommandStatusResponse(command_id=command.command_id, farm_id=command.farm_id, status=command.status.value)
