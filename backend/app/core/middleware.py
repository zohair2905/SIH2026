from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, request_id_var

log = get_logger("middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        response: Response | None = None
        try:
            response = await call_next(request)
        finally:
            log.info(
                "request method=%s path=%s status=%s",
                request.method,
                request.url.path,
                getattr(response, "status_code", "?"),
            )
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response