"""Indic-Speak client: POST /v1/audio/speech → WAV (PCM16, 24 kHz, mono).

Body: { model, input, voice, instructions } where instructions is a JSON
string: {"lang": "<code>", "style": "..."? }.
Keep inputs to a sentence or two (~30 s of speech).
"""

from __future__ import annotations

import json
import time
import wave
from pathlib import Path

import httpx

from bodhan_dub.cache import ContentAddressedCache, stable_hash
from bodhan_dub.clients.base import ConcurrencyLimiter, api_error_from_response, with_retries
from bodhan_dub.clients.protocols import SpeakResult
from bodhan_dub.config.pricing import Pricing
from bodhan_dub.cost import CostTracker
from bodhan_dub.logging_utils import get_logger, log_event

logger = get_logger(__name__)


def _wav_duration_s(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate) if rate else 0.0


class HttpSpeakClient:
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
        self._url = f"{v1_base.rstrip('/')}/audio/speech"
        self._limiter = limiter
        self._cache = cache
        self._cost = cost
        self._pricing = pricing or Pricing()
        self._timeout_s = timeout_s

    def speak(
        self,
        text: str,
        *,
        language: str,
        voice: str,
        out_path: Path,
        style: str | None = None,
        stage: str = "speak",
        lang: str | None = None,
        segment_id: str | None = None,
    ) -> SpeakResult:
        instructions_obj: dict[str, str] = {"lang": language}
        if style:
            instructions_obj["style"] = style
        instructions = json.dumps(instructions_obj, separators=(",", ":"))
        key = self._cache.make_key(
            "indic-speak",
            {
                "input": text,
                "voice": voice,
                "instructions": instructions,
            },
        )
        cached = self._cache.get(key)
        if cached is not None:
            cached_audio = self._cache.get_or_set_bytes_sidecar(key, "wav")
            if cached_audio.exists():
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(cached_audio.read_bytes())
                log_event(
                    logger,
                    "speak_cache_hit",
                    stage=stage,
                    lang=lang or language,
                    segment_id=segment_id,
                    model="indic-speak",
                    cache_hit=True,
                    cost_inr=0.0,
                )
                return SpeakResult(
                    audio_path=out_path,
                    input_chars=int(cached.get("input_chars", len(text))),
                    cost_inr=float(cached.get("cost_inr", 0.0)),
                    duration_s=float(cached["duration_s"]) if cached.get("duration_s") else None,
                    request_id=cached.get("request_id"),
                    cached=True,
                )
            # Cache JSON without audio — fall through to re-fetch.

        def _call() -> SpeakResult:
            t0 = time.perf_counter()

            def _http() -> SpeakResult:
                body = {
                    "model": "indic-speak",
                    "input": text,
                    "voice": voice,
                    "instructions": instructions,
                }
                with httpx.Client(timeout=self._timeout_s) as client:
                    resp = client.post(
                        self._url,
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        },
                        json=body,
                    )
                request_id = resp.headers.get("x-request-id")
                if resp.status_code >= 400:
                    try:
                        err_body: dict[str, object] | str = resp.json()
                    except Exception:
                        err_body = resp.text
                    raise api_error_from_response(resp.status_code, err_body, request_id=request_id)
                audio = resp.content
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(audio)
                self._cache.get_or_set_bytes_sidecar(key, "wav", audio)
                duration_s = _wav_duration_s(out_path)
                input_chars = len(text)
                cost_inr = self._pricing.speak_cost(input_chars)
                self._cache.set(
                    key,
                    {
                        "input_chars": input_chars,
                        "cost_inr": cost_inr,
                        "duration_s": duration_s,
                        "audio_sha256": stable_hash(audio),
                        "request_id": request_id,
                    },
                )
                self._cost.add(
                    model="indic-speak",
                    stage=stage,
                    cost_inr=cost_inr,
                    lang=lang or language,
                    segment_id=segment_id,
                    input_chars=input_chars,
                )
                log_event(
                    logger,
                    "speak_ok",
                    stage=stage,
                    lang=lang or language,
                    segment_id=segment_id,
                    model="indic-speak",
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    cost_inr=cost_inr,
                    cache_hit=False,
                )
                return SpeakResult(
                    audio_path=out_path,
                    input_chars=input_chars,
                    cost_inr=cost_inr,
                    duration_s=duration_s,
                    request_id=request_id,
                    cached=False,
                )

            return self._limiter.run(_http)

        return with_retries(_call)
