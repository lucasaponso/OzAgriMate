"""Irrigation control service container (port 8003). Provides APIs 7-8.

Run: uvicorn services.irrigation_control_service.main:app --port 8003
"""

from fastapi import FastAPI

from services.irrigation_control_service.routes.irrigation.router import router
from services.irrigation_control_service.routes.irrigation.service import IrrigationCommandService
from services.irrigation_control_service.infrastructure.authorization_client import StubAuthorizationClient
from services.irrigation_control_service.infrastructure.command_repository import InMemoryCommandRepository
from services.irrigation_control_service.infrastructure.device_registry import (
    InMemoryIrrigationDeviceRegistry,
)
from services.irrigation_control_service.infrastructure.gateway_command_dispatcher import (
    StubMqttCommandDispatcher,
)
from services.shared.app_factory import create_service_app
from services.shared.audit import InMemoryAuditLog
from services.shared.events import InMemoryEventPublisher


def create_app() -> FastAPI:
    app = create_service_app(
        title="OzAgriMate Irrigation Control Service",
        description="Validates, authorises, persists and dispatches irrigation commands.",
    )
    app.state.event_publisher = InMemoryEventPublisher()
    app.state.audit_log = InMemoryAuditLog()
    app.state.dispatcher = StubMqttCommandDispatcher()
    app.state.authorization = StubAuthorizationClient()
    app.state.command_service = IrrigationCommandService(
        repository=InMemoryCommandRepository(),
        devices=InMemoryIrrigationDeviceRegistry(),
        authorization=app.state.authorization,
        dispatcher=app.state.dispatcher,
        publisher=app.state.event_publisher,
        audit=app.state.audit_log,
    )
    app.include_router(router)
    return app


app = create_app()
