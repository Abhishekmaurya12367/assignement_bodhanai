from __future__ import annotations

import json
from pathlib import Path

from bodhan_dub.cli import main


def test_cli_scaffold_writes_report(tiny_video: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    code = main(
        [
            "--input",
            str(tiny_video),
            "--langs",
            "hi,ta",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "scaffold"
    assert [x["code"] for x in report["languages"]] == ["hi", "ta"]


def test_cli_rejects_bad_lang(tiny_video: Path, tmp_path: Path) -> None:
    code = main(
        [
            "--input",
            str(tiny_video),
            "--langs",
            "xx",
            "--out",
            str(tmp_path / "out"),
        ]
    )
    assert code == 2


def test_cli_missing_input(tmp_path: Path) -> None:
    code = main(
        [
            "--input",
            str(tmp_path / "missing.mp4"),
            "--langs",
            "hi",
            "--out",
            str(tmp_path / "out"),
        ]
    )
    assert code == 2
