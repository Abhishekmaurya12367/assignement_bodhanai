from __future__ import annotations

import pytest

from bodhan_dub.clients.base import with_retries
from bodhan_dub.errors import ApiError


def test_retries_then_succeeds() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ApiError("rate", status_code=429)
        return "ok"

    assert with_retries(flaky, max_attempts=5, base_delay_s=0.01) == "ok"
    assert calls["n"] == 3


def test_non_retryable_4xx_raises_immediately() -> None:
    calls = {"n": 0}

    def bad() -> None:
        calls["n"] += 1
        raise ApiError("bad request", status_code=400)

    with pytest.raises(ApiError):
        with_retries(bad, max_attempts=5, base_delay_s=0.01)
    assert calls["n"] == 1
