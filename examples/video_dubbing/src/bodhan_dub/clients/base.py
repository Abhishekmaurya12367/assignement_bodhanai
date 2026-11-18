"""Shared HTTP helpers: global concurrency limiter + exponential backoff."""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable
from typing import TypeVar

from bodhan_dub.errors import ApiError
from bodhan_dub.logging_utils import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ConcurrencyLimiter:
    """Process-wide semaphore for all Bodhan/LLM HTTP calls."""

    def __init__(self, limit: int) -> None:
        if limit < 1:
            raise ValueError("concurrency limit must be >= 1")
        self._sem = threading.Semaphore(limit)

    def run(self, fn: Callable[[], T]) -> T:
        self._sem.acquire()
        try:
            return fn()
        finally:
            self._sem.release()


def with_retries(
    fn: Callable[[], T],
    *,
    max_attempts: int = 5,
    base_delay_s: float = 0.5,
    max_delay_s: float = 30.0,
    retry_on: tuple[type[BaseException], ...] = (ApiError,),
    is_retryable: Callable[[BaseException], bool] | None = None,
) -> T:
    """Exponential backoff with full jitter. Retries 429 / 5xx / timeouts."""
    last_exc: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except retry_on as exc:
            last_exc = exc
            retryable = True
            if is_retryable is not None:
                retryable = is_retryable(exc)
            elif isinstance(exc, ApiError) and exc.status_code is not None:
                retryable = exc.status_code == 429 or exc.status_code >= 500
            if not retryable or attempt == max_attempts:
                raise
            # Full jitter: sleep in [0, min(max, base * 2^(attempt-1))]
            ceiling = min(max_delay_s, base_delay_s * (2 ** (attempt - 1)))
            delay = random.uniform(0, ceiling)
            logger.warning(
                "retry attempt=%s delay=%.2fs error=%s",
                attempt,
                delay,
                exc,
            )
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc


def api_error_from_response(
    status_code: int,
    body: dict[str, object] | str,
    *,
    request_id: str | None = None,
) -> ApiError:
    code: str | None = None
    message = f"HTTP {status_code}"
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            message = str(err.get("message") or message)
            code = str(err.get("code")) if err.get("code") is not None else None
            request_id = request_id or (
                str(err.get("request_id")) if err.get("request_id") else None
            )
    elif isinstance(body, str) and body:
        message = body[:500]
    return ApiError(message, status_code=status_code, code=code, request_id=request_id)
