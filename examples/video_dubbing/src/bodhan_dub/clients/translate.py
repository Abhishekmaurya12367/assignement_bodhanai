"""Indic-Translate client: POST /translate (plain JSON, not /v1).

Request: { text, target_language, script?, max_output_tokens? }
Response: { translation, target_language, script, truncated, usage }
Only output tokens are billed.
"""

from __future__ import annotations

import time

import httpx

from bodhan_dub.cache import ContentAddressedCache
from bodhan_dub.clients.base import ConcurrencyLimiter, api_error_from_response, with_retries
from bodhan_dub.clients.protocols import TranslateResult
from bodhan_dub.config.pricing import Pricing
from bodhan_dub.cost import CostTracker
from bodhan_dub.errors import ApiError
from bodhan_dub.logging_utils import get_logger, log_event

logger = get_logger(__name__)


class HttpTranslateClient:
    def __init__(
        self,
        *,
        api_key: str,
        translate_url: str,
        limiter: ConcurrencyLimiter,
        cache: ContentAddressedCache,
        cost: CostTracker,
        pricing: Pricing | None = None,
        timeout_s: float = 120.0,
    ) -> None:
        self._api_key = api_key
        self._url = translate_url
        self._limiter = limiter
        self._cache = cache
        self._cost = cost
        self._pricing = pricing or Pricing()
        self._timeout_s = timeout_s

    def translate(
        self,
        text: str,
        *,
        target_language: str,
        script: str = "native",
        stage: str = "translate",
        lang: str | None = None,
        segment_id: str | None = None,
    ) -> TranslateResult:
        key = self._cache.make_key(
            "indic-translate",
            {"text": text, "target_language": target_language, "script": script},
        )
        cached = self._cache.get(key)
        if cached is not None:
            log_event(
                logger,
                "translate_cache_hit",
                stage=stage,
                lang=lang or target_language,
                segment_id=segment_id,
                model="indic-translate",
                cache_hit=True,
                cost_inr=0.0,
            )
            return TranslateResult(
                translation=str(cached["translation"]),
                target_language=str(cached["target_language"]),
                script=str(cached.get("script", script)),
                truncated=bool(cached.get("truncated", False)),
                output_tokens=int(cached.get("output_tokens", 0)),
                cost_inr=float(cached.get("cost_inr", 0.0)),
                request_id=cached.get("request_id"),
                cached=True,
            )

        def _call() -> TranslateResult:
            t0 = time.perf_counter()

            def _http() -> TranslateResult:
                body = {
                    "text": text,
                    "target_language": target_language,
                    "script": script,
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
                try:
                    payload = resp.json()
                except Exception:
                    payload = {"error": {"message": resp.text}}
                if resp.status_code >= 400 or "error" in payload:
                    raise api_error_from_response(resp.status_code, payload, request_id=request_id)
                if payload.get("truncated"):
                    raise ApiError(
                        "translation truncated (token budget)",
                        status_code=resp.status_code,
                        code="truncated",
                        request_id=request_id,
                    )
                usage = payload.get("usage") or {}
                output_tokens = int(usage.get("completion_tokens") or 0)
                cost_inr = self._pricing.translate_cost(output_tokens)
                translation = str(payload["translation"])
                self._cache.set(
                    key,
                    {
                        "translation": translation,
                        "target_language": payload.get("target_language", target_language),
                        "script": payload.get("script", script),
                        "truncated": False,
                        "output_tokens": output_tokens,
                        "cost_inr": cost_inr,
                        "request_id": request_id,
                    },
                )
                self._cost.add(
                    model="indic-translate",
                    stage=stage,
                    cost_inr=cost_inr,
                    lang=lang or target_language,
                    segment_id=segment_id,
                    output_tokens=output_tokens,
                )
                log_event(
                    logger,
                    "translate_ok",
                    stage=stage,
                    lang=lang or target_language,
                    segment_id=segment_id,
                    model="indic-translate",
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    cost_inr=cost_inr,
                    cache_hit=False,
                )
                return TranslateResult(
                    translation=translation,
                    target_language=str(payload.get("target_language", target_language)),
                    script=str(payload.get("script", script)),
                    truncated=False,
                    output_tokens=output_tokens,
                    cost_inr=cost_inr,
                    request_id=request_id,
                    cached=False,
                )

            return self._limiter.run(_http)

        return with_retries(_call)
