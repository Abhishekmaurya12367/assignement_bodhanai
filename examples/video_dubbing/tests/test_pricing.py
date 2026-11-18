from __future__ import annotations

import pytest

from bodhan_dub.config.pricing import Pricing


def test_transcribe_cost_per_minute() -> None:
    p = Pricing()
    assert p.transcribe_cost(60.0) == pytest.approx(0.10)
    assert p.transcribe_cost(30.0) == pytest.approx(0.05)


def test_translate_cost_per_10k_tokens() -> None:
    p = Pricing()
    assert p.translate_cost(10_000) == pytest.approx(0.20)
    assert p.translate_cost(5_000) == pytest.approx(0.10)


def test_speak_cost_per_10k_chars() -> None:
    p = Pricing()
    assert p.speak_cost(10_000) == pytest.approx(6.0)
    assert p.speak_cost(1_000) == pytest.approx(0.6)
