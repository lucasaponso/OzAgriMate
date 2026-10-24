"""Creates each service's FastAPI application with the shared cross-cutting concerns."""

import logging

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from services.shared.errors import register_error_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _openapi_matching_api_design(app: FastAPI):
    """Generate OpenAPI without FastAPI's default 422 response.

    Validation errors return 400, as documented in the API design (ADR 08), so the
    generated docs must not advertise a 422 the service never sends.
    """

    def openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        for path_item in schema.get("paths", {}).values():
            for operation in path_item.values():
                operation.get("responses", {}).pop("422", None)
        for name in ("HTTPValidationError", "ValidationError"):
            schema.get("components", {}).get("schemas", {}).pop(name, None)
        app.openapi_schema = schema
        return schema

    return openapi


def create_service_app(*, title: str, description: str, version: str = "1.0.0") -> FastAPI:
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    register_error_handlers(app)
    app.openapi = _openapi_matching_api_design(app)
    return app
