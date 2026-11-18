"""Environment-only configuration. No secrets in code or the repo."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from bodhan_dub.errors import ConfigError


class Settings(BaseSettings):
    """Reads keys and endpoints from the environment (see .env.example)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Per-model Bodhan keys (console issues keys per model).
    bodhan_transcribe_key: str = Field(default="", alias="BODHAN_TRANSCRIBE_KEY")
    bodhan_translate_key: str = Field(default="", alias="BODHAN_TRANSLATE_KEY")
    bodhan_speak_key: str = Field(default="", alias="BODHAN_SPEAK_KEY")
    bodhan_ocr_key: str = Field(default="", alias="BODHAN_OCR_KEY")

    bodhan_api_base: str = Field(default="https://api.bodhan.ai", alias="BODHAN_API_BASE")

    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
    llm_model: str = Field(default="", alias="LLM_MODEL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")

    bodhan_max_concurrency: int = Field(default=4, alias="BODHAN_MAX_CONCURRENCY")
    bodhan_request_timeout_s: float = Field(default=120.0, alias="BODHAN_REQUEST_TIMEOUT_S")
    bodhan_cache_dir: Path = Field(default=Path(".cache"), alias="BODHAN_CACHE_DIR")

    # Pipeline knobs (not secrets; overridable via env for experiments).
    min_duration_s: float = 60.0  # 1 minute
    max_duration_s: float = 15 * 60.0  # 15 minutes
    transcribe_chunk_max_s: float = 30.0
    stretch_min: float = 0.85
    stretch_max: float = 1.2
    sync_start_tolerance_ms: float = 300.0
    output_duration_tolerance_ms: float = 100.0
    max_condense_attempts: int = 2
    qa_max_synth_retries: int = 3
    language_concurrency: int = 3

    def require_bodhan_keys(self) -> None:
        missing = [
            name
            for name, value in (
                ("BODHAN_TRANSCRIBE_KEY", self.bodhan_transcribe_key),
                ("BODHAN_TRANSLATE_KEY", self.bodhan_translate_key),
                ("BODHAN_SPEAK_KEY", self.bodhan_speak_key),
            )
            if not value
        ]
        if missing:
            raise ConfigError(
                "Missing required environment variables: "
                + ", ".join(missing)
                + ". Copy .env.example to .env and fill in keys."
            )

    def require_llm(self) -> None:
        missing = [
            name
            for name, value in (
                ("LLM_BASE_URL", self.llm_base_url),
                ("LLM_MODEL", self.llm_model),
                ("LLM_API_KEY", self.llm_api_key),
            )
            if not value
        ]
        if missing:
            raise ConfigError(
                "Missing LLM environment variables: "
                + ", ".join(missing)
                + ". The LLM is used only for English-side decisions."
            )

    @property
    def openai_compatible_v1_base(self) -> str:
        """Base URL for OpenAI SDK (/v1/audio/..., /v1/chat/...)."""
        base = self.bodhan_api_base.rstrip("/")
        return base if base.endswith("/v1") else f"{base}/v1"

    @property
    def translate_url(self) -> str:
        """Plain JSON translate endpoint (not under /v1)."""
        base = self.bodhan_api_base.rstrip("/")
        if base.endswith("/v1"):
            base = base[: -len("/v1")]
        return f"{base}/translate"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
