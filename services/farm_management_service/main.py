"""Farm management service container (port 8001). Provides APIs 1-4.

Run: uvicorn services.farm_management_service.main:app --port 8001
"""

from fastapi import FastAPI

from services.farm_management_service.routes.farms.router import router
from services.farm_management_service.routes.farms.service import FarmService
from services.farm_management_service.infrastructure.farm_repository import InMemoryFarmRepository
from services.shared.app_factory import create_service_app
from services.shared.events import InMemoryEventPublisher


def create_app() -> FastAPI:
    app = create_service_app(
        title="OzAgriMate Farm Management Service",
        description="Manages farms, users and settings. Authoritative owner of farm records.",
    )
    app.state.event_publisher = InMemoryEventPublisher()
    app.state.farm_service = FarmService(InMemoryFarmRepository(), app.state.event_publisher)
    app.include_router(router)
    return app


app = create_app()
