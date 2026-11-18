"""Content-addressed disk cache for every model call.

Key = hash(model + exact input + params). Never send the same input to the
same model twice in one run (in-memory dedupe) or across runs (disk).
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Any

from bodhan_dub.logging_utils import get_logger

logger = get_logger(__name__)


def stable_hash(payload: dict[str, Any] | str | bytes) -> str:
    if isinstance(payload, bytes):
        data = payload
    elif isinstance(payload, str):
        data = payload.encode("utf-8")
    else:
        data = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class ContentAddressedCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._inflight: dict[str, Any] = {}
        self._seen_this_run: set[str] = set()
        self._lock = threading.Lock()

    def _path(self, key: str) -> Path:
        # Shard by first 2 hex chars to keep directories small.
        return self.root / key[:2] / f"{key}.json"

    def make_key(self, model: str, input_payload: dict[str, Any] | str | bytes) -> str:
        if isinstance(input_payload, bytes):
            body = {"bytes_sha256": stable_hash(input_payload)}
        elif isinstance(input_payload, str):
            body = {"text": input_payload}
        else:
            body = input_payload
        return stable_hash({"model": model, "input": body})

    def get(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            raw: object = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("cache_read_failed key=%s err=%s", key[:12], exc)
            return None
        if isinstance(raw, dict):
            return {str(k): v for k, v in raw.items()}
        return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
        with self._lock:
            self._seen_this_run.add(key)

    def get_or_set_bytes_sidecar(self, key: str, filename: str, data: bytes | None = None) -> Path:
        """Store binary blobs (audio) next to the JSON entry."""
        path = self._path(key).with_suffix("").parent / f"{key}.{filename}"
        if data is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return path

    def mark_seen(self, key: str) -> bool:
        """Return True if this key was already used earlier in *this* run."""
        with self._lock:
            if key in self._seen_this_run:
                return True
            self._seen_this_run.add(key)
            return False
