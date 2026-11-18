"""Build the real client suite from Settings (tests inject mocks instead)."""

from __future__ import annotations

from dataclasses import dataclass

from bodhan_dub.cache import ContentAddressedCache
from bodhan_dub.clients.base import ConcurrencyLimiter
from bodhan_dub.clients.llm import OpenAICompatibleLLMClient
from bodhan_dub.clients.speak import HttpSpeakClient
from bodhan_dub.clients.transcribe import HttpTranscribeClient
from bodhan_dub.clients.translate import HttpTranslateClient
from bodhan_dub.config.pricing import Pricing
from bodhan_dub.config.settings import Settings
from bodhan_dub.cost import CostTracker


@dataclass
class ClientBundle:
    transcribe: HttpTranscribeClient
    translate: HttpTranslateClient
    speak: HttpSpeakClient
    llm: OpenAICompatibleLLMClient
    cache: ContentAddressedCache
    cost: CostTracker
    limiter: ConcurrencyLimiter


def build_clients(settings: Settings, *, require_llm: bool = True) -> ClientBundle:
    settings.require_bodhan_keys()
    if require_llm:
        settings.require_llm()

    cache = ContentAddressedCache(settings.bodhan_cache_dir)
    cost = CostTracker()
    limiter = ConcurrencyLimiter(settings.bodhan_max_concurrency)
    pricing = Pricing()
    v1 = settings.openai_compatible_v1_base

    return ClientBundle(
        transcribe=HttpTranscribeClient(
            api_key=settings.bodhan_transcribe_key,
            v1_base=v1,
            limiter=limiter,
            cache=cache,
            cost=cost,
            pricing=pricing,
            timeout_s=settings.bodhan_request_timeout_s,
        ),
        translate=HttpTranslateClient(
            api_key=settings.bodhan_translate_key,
            translate_url=settings.translate_url,
            limiter=limiter,
            cache=cache,
            cost=cost,
            pricing=pricing,
            timeout_s=settings.bodhan_request_timeout_s,
        ),
        speak=HttpSpeakClient(
            api_key=settings.bodhan_speak_key,
            v1_base=v1,
            limiter=limiter,
            cache=cache,
            cost=cost,
            pricing=pricing,
            timeout_s=settings.bodhan_request_timeout_s,
        ),
        llm=OpenAICompatibleLLMClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            limiter=limiter,
            cache=cache,
            timeout_s=settings.bodhan_request_timeout_s,
        ),
        cache=cache,
        cost=cost,
        limiter=limiter,
    )
