"""Shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_cache_dir(tmp_path: Path) -> Path:
    d = tmp_path / "cache"
    d.mkdir()
    return d


@pytest.fixture
def tiny_video(tmp_path: Path) -> Path:
    """Placeholder file so CLI path checks pass (real ffmpeg clip in Phase 2)."""
    p = tmp_path / "clip.mp4"
    p.write_bytes(b"not-a-real-video")
    return p
