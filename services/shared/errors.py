"""Consistent RFC 7807 (application/problem+json) error responses for every service."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"
PROBLEM_TYPE_BASE = "https://api.ozagrimate.com.au/problems/"


class ApiError(Exception):
    """Domain/application error that maps directly to an HTTP problem response."""

    def __init__(
        self,
        status: int,
        code: str,
        title: str,
        detail: str,
        headers: dict[str, str] | None = None,
        **extensions: Any,
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail
        self.headers = headers
        self.extensions = extensions


def not_found(resource: str, identifier: str) -> ApiError:
    return ApiError(404, "not-found", f"{resource} not found", f"{resource} '{identifier}' does not exist.")


def forbidden(detail: str) -> ApiError:
    return ApiError(403, "forbidden", "Forbidden", detail)


def conflict(code: str, detail: str, **extensions: Any) -> ApiError:
    return ApiError(409, code, "Conflict", detail, **extensions)


def bad_request(code: str, detail: str, **extensions: Any) -> ApiError:
    return ApiError(400, code, "Bad request", detail, **extensions)


def _problem(request: Request, status: int, code: str, title: str, detail: str, **ext: Any) -> dict[str, Any]:
    body = {
        "type": PROBLEM_TYPE_BASE + code,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
    }
    body.update(ext)
    return body


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content=_problem(request, exc.status, exc.code, exc.title, exc.detail, **exc.extensions),
            media_type=PROBLEM_JSON,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # The API design (ADR 08) specifies 400 for invalid requests, not FastAPI's default 422.
        errors = [
            {
                "field": ".".join(str(part) for part in err["loc"] if part not in ("body",)),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=_problem(
                request, 400, "validation-error", "Bad request",
                "One or more fields are missing or invalid.", errors=errors,
            ),
            media_type=PROBLEM_JSON,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "not-found", 405: "method-not-allowed"}.get(exc.status_code, "http-error")
        return JSONResponse(
            status_code=exc.status_code,
            content=_problem(request, exc.status_code, code, str(exc.detail), str(exc.detail)),
            media_type=PROBLEM_JSON,
            headers=getattr(exc, "headers", None),
        )
