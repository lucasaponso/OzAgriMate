"""Telemetry service container (port 8002). Provides APIs 5-6.

Run: uvicorn services.telemetry_service.main:app --port 8002
"""

from fastapi import FastAPI

from services.shared.app_factory import create_service_app
from services.shared.events import InMemoryEventPublisher
from services.telemetry_service.routes.telemetry.router import router
from services.telemetry_service.routes.telemetry.service import TelemetryService
from services.telemetry_service.infrastructure.device_registry import InMemoryDeviceRegistry
from services.telemetry_service.infrastructure.reading_repository import InMemoryReadingRepository


def create_app() -> FastAPI:
    app = create_service_app(
        title="OzAgriMate Telemetry Service",
        description="Ingests and stores sensor data: validates, de-duplicates and publishes ReadingAccepted.",
    )
    app.state.event_publisher = InMemoryEventPublisher()
    app.state.telemetry_service = TelemetryService(
        repository=InMemoryReadingRepository(),
        devices=InMemoryDeviceRegistry(),
        publisher=app.state.event_publisher,
    )
    app.include_router(router)
    return app


app = create_app()
