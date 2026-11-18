from __future__ import annotations

from pathlib import Path

from bodhan_dub.cache import ContentAddressedCache, stable_hash


def test_stable_hash_deterministic() -> None:
    assert stable_hash({"a": 1, "b": 2}) == stable_hash({"b": 2, "a": 1})


def test_cache_roundtrip(tmp_cache_dir: Path) -> None:
    cache = ContentAddressedCache(tmp_cache_dir)
    key = cache.make_key("indic-translate", {"text": "hello", "target_language": "hi"})
    assert cache.get(key) is None
    cache.set(key, {"translation": "नमस्ते"})
    assert cache.get(key) == {"translation": "नमस्ते"}


def test_mark_seen_dedupes_within_run(tmp_cache_dir: Path) -> None:
    cache = ContentAddressedCache(tmp_cache_dir)
    key = "abc"
    assert cache.mark_seen(key) is False
    assert cache.mark_seen(key) is True
