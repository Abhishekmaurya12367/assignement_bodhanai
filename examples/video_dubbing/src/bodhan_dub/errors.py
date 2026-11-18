"""Typed errors for graceful CLI reporting. Never hide failures."""

from __future__ import annotations


class BodhanDubError(Exception):
    """Base error for the pipeline."""


class ConfigError(BodhanDubError):
    """Missing or invalid environment / CLI configuration."""


class UnsupportedLanguageError(BodhanDubError):
    """`--langs` contains a code not in the supported language table."""

    def __init__(self, bad: str, supported: list[str]) -> None:
        self.bad = bad
        self.supported = supported
        codes = ", ".join(supported)
        super().__init__(f"Unsupported language '{bad}'. Supported: {codes}")


class InputValidationError(BodhanDubError):
    """Bad input media (missing file, wrong format, duration out of range, no audio)."""


class NoSpeechError(BodhanDubError):
    """VAD found no speech regions; exit cleanly with an honest report."""


class StageError(BodhanDubError):
    """A pipeline stage failed. Recorded honestly in report.json."""

    def __init__(self, stage: str, message: str, *, lang: str | None = None) -> None:
        self.stage = stage
        self.lang = lang
        prefix = f"[{stage}]" if lang is None else f"[{stage}/{lang}]"
        super().__init__(f"{prefix} {message}")


class ApiError(BodhanDubError):
    """Bodhan or LLM HTTP/API failure after retries exhausted."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.request_id = request_id
        super().__init__(message)


class CacheError(BodhanDubError):
    """Cache read/write failure (non-fatal callers may fall through)."""
