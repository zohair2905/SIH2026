from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger, request_id_var

log = get_logger("exceptions")


class AppError(Exception):
    def __init__(
        self, message: str, *, status_code: int = 400, code: str = "error"
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=404, code="not_found")


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409, code="conflict")


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422, code="validation_error")


class ModelUnavailableError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=503, code="model_unavailable")


def _envelope(*, status_code: int, code: str, message: Any) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            {
                "error": {"code": code, "message": message},
                "detail": message,
                "request_id": request_id_var.get() or "-",
            }
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return _envelope(
            status_code=exc.status_code, code=exc.code, message=exc.message
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _envelope(
            status_code=exc.status_code,
            code=f"http_{exc.status_code}",
            message=exc.detail,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _envelope(
            status_code=422, code="validation_error", message=exc.errors()
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("Unhandled error on %s %s", request.method, request.url.path)
        return _envelope(
            status_code=500, code="internal_error", message="Internal server error"
        )