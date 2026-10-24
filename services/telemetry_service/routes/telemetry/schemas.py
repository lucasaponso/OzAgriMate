"""Request/response contracts for APIs 5-6, as documented in section 5 of the report."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, Field

from services.shared.api_models import CamelModel


class TelemetryReadingRequest(CamelModel):
    """Body for POST /api/v1/telemetry/readings."""

    reading_id: str = Field(min_length=1, max_length=64, examples=["r-17"])
    farm_id: str = Field(min_length=1, max_length=64, examples=["farm-101"])
    device_id: str = Field(min_length=1, max_length=64, examples=["dev-8"])
    metric: str = Field(min_length=1, max_length=40, examples=["soilMoisture"])
    value: float = Field(examples=[18.5])
    unit: str = Field(min_length=1, max_length=20, examples=["percent"])
    timestamp: AwareDatetime = Field(examples=["2026-10-18T02:00:00Z"])


class ReadingAcceptedResponse(CamelModel):
    reading_id: str
    status: Literal["accepted"] = "accepted"


class LatestReadingOut(CamelModel):
    reading_id: str
    metric: str
    value: float
    unit: str


class LatestReadingsResponse(CamelModel):
    farm_id: str
    readings: list[LatestReadingOut]
