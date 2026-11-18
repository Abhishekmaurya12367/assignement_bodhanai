"""Structured JSON logs so every stage/segment decision is traceable."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Extra fields attached via logger.info("...", extra={...})
        for key in (
            "stage",
            "lang",
            "segment_id",
            "decision",
            "reason",
            "latency_ms",
            "cost_inr",
            "model",
            "cache_hit",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        # Already configured (e.g. tests).
        root.setLevel(level)
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonLogFormatter())
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    message: str,
    *,
    stage: str,
    lang: str | None = None,
    segment_id: str | None = None,
    decision: str | None = None,
    reason: str | None = None,
    latency_ms: float | None = None,
    cost_inr: float | None = None,
    model: str | None = None,
    cache_hit: bool | None = None,
    level: int = logging.INFO,
) -> None:
    extra = {
        "stage": stage,
        "lang": lang,
        "segment_id": segment_id,
        "decision": decision,
        "reason": reason,
        "latency_ms": latency_ms,
        "cost_inr": cost_inr,
        "model": model,
        "cache_hit": cache_hit,
    }
    logger.log(level, message, extra=extra)
