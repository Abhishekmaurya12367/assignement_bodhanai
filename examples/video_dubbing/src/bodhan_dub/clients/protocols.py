"""Client interfaces — keep HTTP details behind these so tests can mock."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class TranscribeResult:
    text: str
    audio_seconds: float
    cost_inr: float
    request_id: str | None = None
    cached: bool = False


@dataclass(frozen=True)
class TranslateResult:
    translation: str
    target_language: str
    script: str
    truncated: bool
    output_tokens: int
    cost_inr: float
    request_id: str | None = None
    cached: bool = False


@dataclass(frozen=True)
class SpeakResult:
    audio_path: Path
    input_chars: int
    cost_inr: float
    duration_s: float | None = None
    request_id: str | None = None
    cached: bool = False


@dataclass(frozen=True)
class LLMResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached: bool = False


@runtime_checkable
class TranscribeClient(Protocol):
    def transcribe(
        self,
        audio_path: Path,
        *,
        language: str,
        stage: str = "transcribe",
    ) -> TranscribeResult: ...


@runtime_checkable
class TranslateClient(Protocol):
    def translate(
        self,
        text: str,
        *,
        target_language: str,
        script: str = "native",
        stage: str = "translate",
    ) -> TranslateResult: ...


@runtime_checkable
class SpeakClient(Protocol):
    def speak(
        self,
        text: str,
        *,
        language: str,
        voice: str,
        out_path: Path,
        style: str | None = None,
        stage: str = "speak",
    ) -> SpeakResult: ...


@runtime_checkable
class LLMClient(Protocol):
    def complete(
        self,
        *,
        system: str,
        user: str,
        stage: str = "llm",
    ) -> LLMResult: ...
