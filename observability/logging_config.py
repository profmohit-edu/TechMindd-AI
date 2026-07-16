"""Structured JSON logging with size-based rotation."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from observability.context import correlation_id, request_id

_STANDARD_FIELDS = set(logging.makeLogRecord({}).__dict__)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id.get(),
            "correlation_id": correlation_id.get(),
        }
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_FIELDS and key not in {"message", "asctime"}
        }
        if extras:
            payload["context"] = extras
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    formatter = JsonFormatter()
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    handlers: list[logging.Handler] = [stream]

    log_path = Path(os.getenv("LOG_FILE", "logs/techmindd.jsonl"))
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        rotating = RotatingFileHandler(
            log_path,
            maxBytes=int(os.getenv("LOG_MAX_BYTES", "10485760")),
            backupCount=int(os.getenv("LOG_BACKUP_COUNT", "5")),
            encoding="utf-8",
        )
        rotating.setFormatter(formatter)
        handlers.append(rotating)
    except OSError:
        logging.getLogger(__name__).warning("Rotating log file is unavailable")

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    for handler in handlers:
        root.addHandler(handler)
