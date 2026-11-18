# Video dubbing (`bodhan_dub`)

Agentic English-video → Indian-language dubbing pipeline using **Bodhan models only**
(Indic-Transcribe, Indic-Translate, Indic-Speak).

> **Status:** Phase 1 scaffold. Stages 2–10 land in later phases. No fabricated media.

## Setup

System dependency: **ffmpeg** (+ ffprobe) on `PATH`.

```bash
cd examples/video_dubbing
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill Bodhan + LLM keys when you run live
```

## Run

```bash
python -m bodhan_dub --input path/to/video.mp4 --langs hi,ta,bn --out ./out
```

Optional: `--glossary glossary.yaml` `--voices voices.yaml` `--code-mixed`

Phase 1 writes a skeleton `out/report.json` after validating languages and paths
(no API calls). Full dubbing arrives in Phases 2–5.

## Check

```bash
make check    # ruff + mypy + pytest
```

## How it works

See upcoming `DESIGN.md` (Phase 6). Language support is driven from
`src/bodhan_dub/config/languages.py` — never hardcoded to the demo set.
