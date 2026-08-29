"""Structured JSON logging with a redaction layer.

Mitigates threat-model.md #9 (PII leakage through logs): fields whose names
suggest secrets/PII are redacted before emission. Passwords, tokens, and
raw identity data must never reach the log pipeline (docs/security/pii-handling.md).
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any

# Substrings that, if present in a log-extra key, cause the value to be redacted.
_REDACT_KEYS = (
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "refresh_token",
    "access_token",
    "password_hash",
    "jwt",
    "phone_number",
    "email",
    "date_of_birth",
    "line1",
    "declared_annual_income",
)

_REDACTED = "***REDACTED***"

# Reserved LogRecord attributes we do not treat as structured extras.
_RESERVED = set(
    logging.makeLogRecord({}).__dict__.keys()
) | {"message", "asctime", "taskName"}


def _redact(key: str, value: Any) -> Any:
    lowered = key.lower()
    if any(token in lowered for token in _REDACT_KEYS):
        return _REDACTED
    return value


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON with redacted extras."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            # Include only the exception type/message, never the full traceback
            # in the structured payload sent to clients or shared sinks.
            exc_type = record.exc_info[0]
            payload["error_type"] = exc_type.__name__ if exc_type else "Exception"

        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            payload[key] = _redact(key, value)

        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Install the JSON formatter on the root logger (idempotent)."""
    root = logging.getLogger()
    root.setLevel(level)
    # Remove existing handlers to avoid duplicate/plaintext output.
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
