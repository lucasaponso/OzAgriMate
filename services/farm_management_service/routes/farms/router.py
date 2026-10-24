"""Farm controller: APIs 1-4."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, Response, status

from services.farm_management_service.routes.farms.schemas import FarmRequest, FarmResponse
from services.farm_management_service.routes.farms.service import FarmService
from services.farm_management_service.domain.models import Farm

router = APIRouter(prefix="/api/v1/farms", tags=["Farm"])

FarmId = Annotated[str, Path(alias="id", min_length=1, max_length=64)]


def get_service(request: Request) -> FarmService:
    return request.app.state.farm_service


def to_response(farm: Farm) -> FarmResponse:
    return FarmResponse(id=farm.id, name=farm.name, region=farm.region)


@router.get(
    "/{id}",
    response_model=FarmResponse,
    summary="API 1: Get a farm by identifier",
    responses={404: {"description": "Farm not found"}},
)
def get_farm(farm_id: FarmId, service: FarmService = Depends(get_service)) -> FarmResponse:
    return to_response(service.get_farm(farm_id))


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="API 2: Register a new farm",
    responses={400: {"description": "Invalid farm details"}},
)
def register_farm(
    body: FarmRequest, response: Response, service: FarmService = Depends(get_service)
) -> FarmResponse:
    farm = service.register_farm(body.name, body.region)
    response.headers["Location"] = f"/api/v1/farms/{farm.id}"
    return to_response(farm)


@router.put(
    "/{id}",
    response_model=FarmResponse,
    summary="API 3: Update an existing farm record",
    responses={400: {"description": "Invalid farm details"}, 404: {"description": "Farm not found"}},
)
def update_farm(farm_id: FarmId, body: FarmRequest, service: FarmService = Depends(get_service)) -> FarmResponse:
    return to_response(service.update_farm(farm_id, body.name, body.region))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="API 4: Delete a farm record",
    responses={404: {"description": "Farm not found"}},
)
def delete_farm(farm_id: FarmId, service: FarmService = Depends(get_service)) -> Response:
    service.delete_farm(farm_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
