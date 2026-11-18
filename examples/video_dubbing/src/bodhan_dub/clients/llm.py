"""OpenAI-compatible LLM client (English-side decisions only).

Reads LLM_BASE_URL, LLM_MODEL, LLM_API_KEY. No provider-only features.
The LLM must NEVER write or polish Indian-language text — callers enforce that.
"""

from __future__ import annotations

import time

from openai import OpenAI

from bodhan_dub.cache import ContentAddressedCache
from bodhan_dub.clients.base import ConcurrencyLimiter, with_retries
from bodhan_dub.clients.protocols import LLMResult
from bodhan_dub.errors import ApiError
from bodhan_dub.logging_utils import get_logger, log_event

logger = get_logger(__name__)


class OpenAICompatibleLLMClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        limiter: ConcurrencyLimiter,
        cache: ContentAddressedCache,
        timeout_s: float = 120.0,
    ) -> None:
        self._model = model
        self._limiter = limiter
        self._cache = cache
        self._client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout_s)

    def complete(
        self,
        *,
        system: str,
        user: str,
        stage: str = "llm",
        lang: str | None = None,
        segment_id: str | None = None,
    ) -> LLMResult:
        key = self._cache.make_key(
            f"llm:{self._model}",
            {"system": system, "user": user},
        )
        cached = self._cache.get(key)
        if cached is not None:
            log_event(
                logger,
                "llm_cache_hit",
                stage=stage,
                lang=lang,
                segment_id=segment_id,
                model=self._model,
                cache_hit=True,
            )
            return LLMResult(
                text=str(cached["text"]),
                prompt_tokens=int(cached.get("prompt_tokens", 0)),
                completion_tokens=int(cached.get("completion_tokens", 0)),
                cached=True,
            )

        def _call() -> LLMResult:
            t0 = time.perf_counter()

            def _http() -> LLMResult:
                try:
                    resp = self._client.chat.completions.create(
                        model=self._model,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                    )
                except Exception as exc:  # noqa: BLE001 — normalize to ApiError
                    raise ApiError(str(exc), status_code=None, code="llm_error") from exc
                choice = resp.choices[0].message.content or ""
                usage = resp.usage
                prompt_tokens = int(usage.prompt_tokens) if usage else 0
                completion_tokens = int(usage.completion_tokens) if usage else 0
                self._cache.set(
                    key,
                    {
                        "text": choice,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                    },
                )
                log_event(
                    logger,
                    "llm_ok",
                    stage=stage,
                    lang=lang,
                    segment_id=segment_id,
                    model=self._model,
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    cache_hit=False,
                )
                return LLMResult(
                    text=choice,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cached=False,
                )

            return self._limiter.run(_http)

        return with_retries(_call)
