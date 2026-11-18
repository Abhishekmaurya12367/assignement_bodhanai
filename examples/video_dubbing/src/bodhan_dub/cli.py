"""CLI entry: python -m bodhan_dub --input ... --langs ... --out ..."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bodhan_dub.config.languages import list_supported_codes, resolve_languages
from bodhan_dub.config.settings import Settings, get_settings
from bodhan_dub.errors import BodhanDubError
from bodhan_dub.logging_utils import setup_logging
from bodhan_dub.pipeline import RunRequest, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    supported = ", ".join(list_supported_codes())
    p = argparse.ArgumentParser(
        prog="bodhan_dub",
        description=(
            "Agentic English-video → Indian-language dubbing "
            "(Bodhan Indic-Transcribe / Translate / Speak only)."
        ),
    )
    p.add_argument(
        "--input", required=True, type=Path, help="Local English video (MP4/MOV/MKV/WebM)"
    )
    p.add_argument(
        "--langs",
        required=True,
        help=f"Comma-separated language codes. Supported: {supported}",
    )
    p.add_argument("--out", required=True, type=Path, help="Output directory")
    p.add_argument("--glossary", type=Path, default=None, help="Optional glossary.yaml")
    p.add_argument("--voices", type=Path, default=None, help="Optional voices.yaml overrides")
    p.add_argument(
        "--code-mixed",
        action="store_true",
        help="Request Indic-Translate script=codemix when the language supports it",
    )
    p.add_argument(
        "--scaffold-only",
        action="store_true",
        help="Phase 1: validate args and write a skeleton report (no API calls)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        languages = resolve_languages(args.langs)
        settings: Settings = get_settings()

        if not args.input.exists():
            # Full media validation lands in Phase 2 (ffprobe). Fail clearly now.
            raise BodhanDubError(f"Input file not found: {args.input}")

        if args.glossary is not None and not args.glossary.exists():
            raise BodhanDubError(f"Glossary file not found: {args.glossary}")
        if args.voices is not None and not args.voices.exists():
            raise BodhanDubError(f"Voices file not found: {args.voices}")

        # Until Phase 2 wires the full pipeline, default behaviour is scaffold-safe:
        # do not call APIs unless the caller opts into a future --live path.
        req = RunRequest(
            input_video=args.input.resolve(),
            languages=languages,
            out_dir=args.out.resolve(),
            glossary_path=args.glossary.resolve() if args.glossary else None,
            voices_path=args.voices.resolve() if args.voices else None,
            code_mixed=bool(args.code_mixed),
        )
        result = run_pipeline(req, settings)
        return result.exit_code
    except BodhanDubError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
