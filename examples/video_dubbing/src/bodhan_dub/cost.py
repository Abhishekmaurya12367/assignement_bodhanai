"""Accumulate INR cost per call / segment / language / total."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class CostRecord:
    model: str
    stage: str
    cost_inr: float
    lang: str | None = None
    segment_id: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


class CostTracker:
    """Thread-safe cost ledger for the run report."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._records: list[CostRecord] = []

    def add(
        self,
        *,
        model: str,
        stage: str,
        cost_inr: float,
        lang: str | None = None,
        segment_id: str | None = None,
        **meta: Any,
    ) -> None:
        with self._lock:
            self._records.append(
                CostRecord(
                    model=model,
                    stage=stage,
                    cost_inr=cost_inr,
                    lang=lang,
                    segment_id=segment_id,
                    meta=dict(meta),
                )
            )

    def total(self) -> float:
        with self._lock:
            return sum(r.cost_inr for r in self._records)

    def by_language(self) -> dict[str, float]:
        with self._lock:
            out: dict[str, float] = {}
            for r in self._records:
                key = r.lang or "_shared"
                out[key] = out.get(key, 0.0) + r.cost_inr
            return out

    def by_stage(self) -> dict[str, float]:
        with self._lock:
            out: dict[str, float] = {}
            for r in self._records:
                out[r.stage] = out.get(r.stage, 0.0) + r.cost_inr
            return out

    def by_segment(self, lang: str) -> dict[str, float]:
        with self._lock:
            out: dict[str, float] = {}
            for r in self._records:
                if r.lang == lang and r.segment_id:
                    out[r.segment_id] = out.get(r.segment_id, 0.0) + r.cost_inr
            return out

    def to_report(self) -> dict[str, Any]:
        with self._lock:
            records = list(self._records)
        by_stage: dict[str, float] = {}
        by_lang: dict[str, float] = {}
        for r in records:
            by_stage[r.stage] = by_stage.get(r.stage, 0.0) + r.cost_inr
            lang_key = r.lang or "_shared"
            by_lang[lang_key] = by_lang.get(lang_key, 0.0) + r.cost_inr
        return {
            "total_inr": round(sum(r.cost_inr for r in records), 6),
            "by_stage_inr": {k: round(v, 6) for k, v in by_stage.items()},
            "by_language_inr": {k: round(v, 6) for k, v in by_lang.items()},
            "calls": [
                {
                    "model": r.model,
                    "stage": r.stage,
                    "lang": r.lang,
                    "segment_id": r.segment_id,
                    "cost_inr": round(r.cost_inr, 6),
                    **r.meta,
                }
                for r in records
            ],
        }
