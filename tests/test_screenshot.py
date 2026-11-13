"""``tools/screenshot.py``: Help's pictures are up to date and keep to the
rules of the ``navigator-help`` skill.

The README's scene is left out: it shows About and so the version, and the
suite the release workflow runs would fail on the version it is releasing."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from navigator.lib.help import ansi
from tools import screenshot

ROOT = Path(__file__).resolve().parent.parent


def test_every_help_screenshot_is_up_to_date():
    done = subprocess.run(
        [sys.executable, "tools/screenshot.py", "--check", "--no-readme"], cwd=ROOT, capture_output=True, text=True
    )
    assert done.returncode == 0, done.stderr


def test_every_help_scene_has_both_files_and_they_are_the_same_size():
    shots = ROOT / "docs" / "en" / "shots"
    names = {scene.name for scene in screenshot.SCENES if scene is not screenshot.README_SCENE}
    assert {path.name for path in shots.iterdir()} == {f"{name}{ext}" for name in names for ext in (".svg", ".ans")}
    for name in names:
        rows = ansi.read((shots / f"{name}.ans").read_text(encoding="utf-8"))
        width = len(rows[0]) * screenshot.CELL_W + 2 * screenshot.PAD
        height = len(rows) * screenshot.CELL_H + 2 * screenshot.PAD
        svg = (shots / f"{name}.svg").read_text(encoding="utf-8")
        assert f'width="{width}" height="{height}"' in svg.splitlines()[0]
