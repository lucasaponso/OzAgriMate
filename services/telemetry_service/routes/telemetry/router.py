"""Telemetry controller: APIs 5-6."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status

from services.telemetry_service.routes.telemetry.schemas import (
    LatestReadingOut,
    LatestReadingsResponse,
    ReadingAcceptedResponse,
    TelemetryReadingRequest,
)
from services.telemetry_service.routes.telemetry.service import SubmitReadingCommand, TelemetryService

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry"])

FarmId = Annotated[str, Path(alias="farmId", min_length=1, max_length=64)]


def get_service(request: Request) -> TelemetryService:
    return request.app.state.telemetry_service


@router.post(
    "/readings",
    response_model=ReadingAcceptedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="API 5: Accept a validated telemetry reading",
    responses={400: {"description": "Invalid reading"}, 409: {"description": "Duplicate reading"}},
)
def submit_reading(
    body: TelemetryReadingRequest, service: TelemetryService = Depends(get_service)
) -> ReadingAcceptedResponse:
    reading = service.submit_reading(
        SubmitReadingCommand(
            reading_id=body.reading_id,
            farm_id=body.farm_id,
            device_id=body.device_id,
            metric=body.metric,
            value=body.value,
            unit=body.unit,
            timestamp=body.timestamp,
        )
    )
    return ReadingAcceptedResponse(reading_id=reading.reading_id)


@router.get(
    "/farms/{farmId}/latest",
    response_model=LatestReadingsResponse,
    summary="API 6: Retrieve latest farm telemetry readings",
    responses={404: {"description": "No telemetry for farm"}},
)
def latest_readings(farm_id: FarmId, service: TelemetryService = Depends(get_service)) -> LatestReadingsResponse:
    readings = service.latest_readings(farm_id)
    return LatestReadingsResponse(
        farm_id=farm_id,
        readings=[
            LatestReadingOut(reading_id=r.reading_id, metric=r.metric.value, value=r.value, unit=r.unit)
            for r in readings
        ],
    )
