"""Language support table for Indic-Speak ∩ Indic-Translate.

Drive ALL language behaviour from this table — never hardcode hi/ta/bn in the
pipeline. Codes come from the public Bodhan API docs
(https://console.bodhan.ai/api-docs/).

Assumption (Phase 0 open question): we accept every language that has both
Translate and Speak support. If Bodhan later publishes a stricter
"13 production-tier" list, replace LANGUAGE_TABLE entries — do not change
call sites.
"""

from __future__ import annotations

from dataclasses import dataclass

from bodhan_dub.errors import UnsupportedLanguageError


@dataclass(frozen=True)
class LanguageInfo:
    code: str
    name: str
    translate_code: str
    speak_lang: str
    default_voice: str
    female_voice: str
    male_voice: str
    supports_codemix: bool = True


# Voices from Indic-Speak docs: any voice can read any language; defaults pick
# the voice recorded for that language when available.
LANGUAGE_TABLE: dict[str, LanguageInfo] = {
    info.code: info
    for info in (
        LanguageInfo("as", "Assamese", "as", "as", "Prastuti", "Prastuti", "Ankur"),
        LanguageInfo("bn", "Bengali", "bn", "bn", "Ishita", "Ishita", "Sourav"),
        LanguageInfo("brx", "Bodo", "brx", "brx", "Gwrbw", "Gwrbw", "Sansuma"),
        LanguageInfo("doi", "Dogri", "doi", "doi", "Preeti", "Preeti", "Sham"),
        LanguageInfo("gu", "Gujarati", "gu", "gu", "Dhara", "Dhara", "Parth"),
        LanguageInfo("hi", "Hindi", "hi", "hi", "Kavya", "Kavya", "Amit"),
        LanguageInfo("kn", "Kannada", "kn", "kn", "Deepika", "Deepika", "Adarsh"),
        LanguageInfo("kok", "Konkani", "kok", "kok", "Anjali", "Anjali", "Sandeep"),
        LanguageInfo("ks", "Kashmiri", "ks", "ks", "Zoon", "Zoon", "Ishfaq", supports_codemix=True),
        LanguageInfo("mai", "Maithili", "mai", "mai", "Vaidehi", "Vaidehi", "Madhukar"),
        LanguageInfo("ml", "Malayalam", "ml", "ml", "Lakshmi", "Lakshmi", "Kiran"),
        LanguageInfo("mni", "Manipuri", "mni", "mni", "Thoibi", "Thoibi", "Chaoba"),
        LanguageInfo("mr", "Marathi", "mr", "mr", "Anagha", "Anagha", "Chinmay"),
        LanguageInfo("ne", "Nepali", "ne", "ne", "Srijana", "Srijana", "Sagar"),
        LanguageInfo("or", "Odia", "or", "or", "Itishree", "Itishree", "Akash"),
        LanguageInfo("pa", "Punjabi", "pa", "pa", "Kaur", "Kaur", "Manpreet"),
        LanguageInfo("sa", "Sanskrit", "sa", "sa", "Bharati", "Bharati", "Aryaman"),
        LanguageInfo("sat", "Santali", "sat", "sat", "Phulmani", "Phulmani", "Sibu"),
        LanguageInfo("sd", "Sindhi", "sd", "sd", "Moomal", "Moomal", "Rano"),
        LanguageInfo("ta", "Tamil", "ta", "ta", "Anitha", "Anitha", "Arun"),
        LanguageInfo("te", "Telugu", "te", "te", "Sravani", "Sravani", "Vamsi"),
        LanguageInfo("ur", "Urdu", "ur", "ur", "Saba", "Saba", "Zaid"),
    )
}


def list_supported_codes() -> list[str]:
    return sorted(LANGUAGE_TABLE.keys())


def get_language(code: str) -> LanguageInfo:
    key = code.strip().lower()
    if key not in LANGUAGE_TABLE:
        raise UnsupportedLanguageError(key, list_supported_codes())
    return LANGUAGE_TABLE[key]


def resolve_languages(langs_csv: str) -> list[LanguageInfo]:
    """Parse `--langs hi,ta,bn` into LanguageInfo rows; reject unknowns early."""
    parts = [p.strip() for p in langs_csv.split(",") if p.strip()]
    if not parts:
        raise UnsupportedLanguageError("(empty)", list_supported_codes())
    seen: set[str] = set()
    out: list[LanguageInfo] = []
    for part in parts:
        info = get_language(part)
        if info.code not in seen:
            seen.add(info.code)
            out.append(info)
    return out


def default_voice_for(code: str, overrides: dict[str, str] | None = None) -> str:
    if overrides and code in overrides:
        return overrides[code]
    return get_language(code).default_voice
