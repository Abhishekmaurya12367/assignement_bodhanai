"""Pipeline orchestrator — stages filled in Phases 2–5.

Phase 1 only validates CLI inputs and writes a stub report so the command
surface is stable for the debrief.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bodhan_dub.config.languages import LanguageInfo, default_voice_for
from bodhan_dub.config.settings import Settings
from bodhan_dub.logging_utils import get_logger, log_event

logger = get_logger(__name__)


@dataclass
class RunRequest:
    input_video: Path
    languages: list[LanguageInfo]
    out_dir: Path
    glossary_path: Path | None = None
    voices_path: Path | None = None
    code_mixed: bool = False
    voice_overrides: dict[str, str] = field(default_factory=dict)


@dataclass
class RunResult:
    exit_code: int
    report: dict[str, Any]


def load_voice_overrides(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    voices = data.get("voices") or {}
    return {str(k).lower(): str(v) for k, v in voices.items()}


def run_pipeline(req: RunRequest, settings: Settings) -> RunResult:
    """Phase 1 stub: validate paths/langs and emit a skeleton report.json."""
    log_event(
        logger,
        "pipeline_start",
        stage="orchestrate",
        decision="scaffold_only",
        reason="Phase 1: stages not implemented yet",
    )

    req.out_dir.mkdir(parents=True, exist_ok=True)
    overrides = load_voice_overrides(req.voices_path)
    lang_plan = []
    for info in req.languages:
        voice = default_voice_for(info.code, {**overrides, **req.voice_overrides})
        lang_dir = req.out_dir / info.code
        lang_dir.mkdir(parents=True, exist_ok=True)
        lang_plan.append(
            {
                "code": info.code,
                "name": info.name,
                "voice": voice,
                "supports_codemix": info.supports_codemix,
                "status": "pending",
                "note": "Phase 1 scaffold — dubbing stages land in Phases 2–5",
            }
        )

    report: dict[str, Any] = {
        "status": "scaffold",
        "input": str(req.input_video),
        "languages": lang_plan,
        "code_mixed": req.code_mixed,
        "glossary": str(req.glossary_path) if req.glossary_path else None,
        "settings": {
            "stretch_min": settings.stretch_min,
            "stretch_max": settings.stretch_max,
            "transcribe_chunk_max_s": settings.transcribe_chunk_max_s,
            "bodhan_api_base": settings.bodhan_api_base,
        },
        "targets": {
            "sync_start_ms": settings.sync_start_tolerance_ms,
            "output_duration_ms": settings.output_duration_tolerance_ms,
        },
        "message": (
            "Scaffold only. Run Phases 2–5 to execute ingest→dub→assemble. "
            "No fabricated media was written."
        ),
    }
    (req.out_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log_event(logger, "pipeline_scaffold_done", stage="orchestrate", decision="ok")
    # Non-zero would imply failure; scaffold succeeds so CI/CLI smoke can pass.
    return RunResult(exit_code=0, report=report)
