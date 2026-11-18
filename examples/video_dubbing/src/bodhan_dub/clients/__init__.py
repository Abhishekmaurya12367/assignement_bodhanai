"""Bodhan + LLM clients behind small mockable interfaces."""

from bodhan_dub.clients.protocols import (
    LLMClient,
    SpeakClient,
    TranscribeClient,
    TranslateClient,
)

__all__ = [
    "LLMClient",
    "SpeakClient",
    "TranscribeClient",
    "TranslateClient",
]
