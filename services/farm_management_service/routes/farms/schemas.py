"""Request/response contracts for APIs 1-4, as documented in section 5 of the report."""

from __future__ import annotations

from pydantic import Field, field_validator

from services.farm_management_service.domain.models import Region
from services.shared.api_models import CamelModel


class FarmRequest(CamelModel):
    """Body for POST /api/v1/farms and PUT /api/v1/farms/{id}."""

    name: str = Field(min_length=1, max_length=100, examples=["Green Valley"])
    region: Region = Field(examples=["VIC"])

    @field_validator("name")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be blank")
        return value.strip()


class FarmResponse(CamelModel):
    id: str = Field(examples=["farm-101"])
    name: str = Field(examples=["Green Valley"])
    region: Region = Field(examples=["VIC"])
