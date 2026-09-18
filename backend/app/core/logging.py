from __future__ import annotations

import logging
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

_FORMAT = (
    "%(asctime)s level=%(levelname)s request_id=%(request_id)s "
    "logger=%(name)s %(message)s"
)


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_FORMAT))
    handler.addFilter(_RequestIdFilter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"sih.{name}")