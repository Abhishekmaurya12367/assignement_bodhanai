"""Indic-Transcribe client: POST /v1/audio/transcriptions (OpenAI-compatible).

Request shape from https://console.bodhan.ai/api-docs/:
  multipart: file, model=indic-transcribe, language=<code>
  max 30 s audio; WAV preferred.
Response: { "text": "..." }
"""

from __future__ import annotations

import time
from pathlib import Path

import httpx

from bodhan_dub.cache import ContentAddressedCache, stable_hash
from bodhan_dub.clients.base import ConcurrencyLimiter, api_error_from_response, with_retries
from bodhan_dub.clients.protocols import TranscribeResult
from bodhan_dub.config.pricing import Pricing
from bodhan_dub.cost import CostTracker
from bodhan_dub.logging_utils import get_logger, log_event

logger = get_logger(__name__)


class HttpTranscribeClient:
    def __init__(
        self,
        *,
        api_key: str,
        v1_base: str,
        limiter: ConcurrencyLimiter,
        cache: ContentAddressedCache,
        cost: CostTracker,
        pricing: Pricing | None = None,
        timeout_s: float = 120.0,
    ) -> None:
        self._api_key = api_key
        self._url = f"{v1_base.rstrip('/')}/audio/transcriptions"
        self._limiter = limiter
        self._cache = cache
        self._cost = cost
        self._pricing = pricing or Pricing()
        self._timeout_s = timeout_s

    def transcribe(
        self,
        audio_path: Path,
        *,
        language: str,
        stage: str = "transcribe",
        audio_seconds: float | None = None,
    ) -> TranscribeResult:
        audio_bytes = audio_path.read_bytes()
        # Duration for billing: caller should pass measured seconds; fallback later.
        duration = audio_seconds if audio_seconds is not None else 0.0
        key = self._cache.make_key(
            "indic-transcribe",
            {
                "language": language,
                "audio_sha256": stable_hash(audio_bytes),
            },
        )
        cached = self._cache.get(key)
        if cached is not None:
            cost_inr = float(cached.get("cost_inr", 0.0))
            result = TranscribeResult(
                text=str(cached["text"]),
                audio_seconds=float(cached.get("audio_seconds", duration)),
                cost_inr=cost_inr,
                request_id=cached.get("request_id"),
                cached=True,
            )
            log_event(
                logger,
                "transcribe_cache_hit",
                stage=stage,
                model="indic-transcribe",
                cache_hit=True,
                cost_inr=0.0,
            )
            return result

        def _call() -> TranscribeResult:
            t0 = time.perf_counter()

            def _http() -> TranscribeResult:
                with audio_path.open("rb") as fh:
                    files = {"file": (audio_path.name, fh, "audio/wav")}
                    data = {"model": "indic-transcribe", "language": language}
                    with httpx.Client(timeout=self._timeout_s) as client:
                        resp = client.post(
                            self._url,
                            headers={"Authorization": f"Bearer {self._api_key}"},
                            files=files,
                            data=data,
                        )
                request_id = resp.headers.get("x-request-id")
                if resp.status_code >= 400:
                    try:
                        body: dict[str, object] | str = resp.json()
                    except Exception:
                        body = resp.text
                    raise api_error_from_response(resp.status_code, body, request_id=request_id)
                payload = resp.json()
                text = str(payload.get("text", ""))
                # Prefer measured duration from caller; else estimate from file later.
                secs = duration
                cost_inr = self._pricing.transcribe_cost(secs)
                self._cache.set(
                    key,
                    {
                        "text": text,
                        "audio_seconds": secs,
                        "cost_inr": cost_inr,
                        "request_id": request_id,
                    },
                )
                self._cost.add(
                    model="indic-transcribe",
                    stage=stage,
                    cost_inr=cost_inr,
                    audio_seconds=secs,
                )
                latency_ms = (time.perf_counter() - t0) * 1000
                log_event(
                    logger,
                    "transcribe_ok",
                    stage=stage,
                    model="indic-transcribe",
                    latency_ms=latency_ms,
                    cost_inr=cost_inr,
                    cache_hit=False,
                )
                return TranscribeResult(
                    text=text,
                    audio_seconds=secs,
                    cost_inr=cost_inr,
                    request_id=request_id,
                    cached=False,
                )

            return self._limiter.run(_http)

        return with_retries(_call)
