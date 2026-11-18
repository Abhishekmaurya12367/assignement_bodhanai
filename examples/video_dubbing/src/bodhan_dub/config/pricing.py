"""Cost rates in Indian rupees (assignment pricing). Track every call."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pricing:
    """Per-model rates used by the cost tracker.

    Indic-Transcribe: Rs 0.10 per input audio minute.
    Indic-Translate: Rs 0.20 per 10,000 output tokens.
    Indic-Speak: Rs 6.00 per 10,000 input characters (dominant cost).
    """

    transcribe_inr_per_audio_minute: float = 0.10
    translate_inr_per_10k_output_tokens: float = 0.20
    speak_inr_per_10k_input_chars: float = 6.00

    def transcribe_cost(self, audio_seconds: float) -> float:
        return (audio_seconds / 60.0) * self.transcribe_inr_per_audio_minute

    def translate_cost(self, output_tokens: int) -> float:
        return (output_tokens / 10_000.0) * self.translate_inr_per_10k_output_tokens

    def speak_cost(self, input_chars: int) -> float:
        return (input_chars / 10_000.0) * self.speak_inr_per_10k_input_chars
