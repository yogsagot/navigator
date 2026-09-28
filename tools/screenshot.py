#!/usr/bin/env python3
"""Paint Navigator's desktop headless and write it out as a screenshot.

Run it from the repository root::

    ./venv/bin/python tools/screenshot.py

It writes two things, both of them text:

- ``docs/screenshot.svg``, every cell in the colours the theme gives it, so
  the README can show the desktop the way a terminal does.  Neither GitHub nor
  PyPI will colour Markdown -- both strip ``style=`` and raw escapes, and
  GitHub ignores an ```` ```ansi ```` fence -- so an SVG made of ``<text>`` and
  ``<rect>`` is the closest a README gets to a terminal.
- the same screen as plain characters, written into ``README.md`` between the
  ``<!-- screenshot:begin -->`` and ``<!-- screenshot:end -->`` markers.
  Nothing outside the markers is touched.

``--check`` writes nothing and exits 1 if either would change, which is what
to run after a change to anything the desktop paints.

The screen is the real one: the application is constructed as ``nav``
constructs it and rendered into a :class:`~navkit.screen.ScreenBuffer`, with
the three things that would make it differ between runs pinned -- the
directory it lists (built here, with fixed sizes), the clock, and the shell
the console would otherwise fork.  This is the golden test's recipe
(``tests/test_nav.py``), applied to a directory worth looking at, with the
About box (≡ > About) open over it -- so the picture carries the version, and
a release makes ``--check`` stale until the screenshot is regenerated.

This is an asset pipeline, like ``palconv.py``: nothing under ``navigator/``
imports it.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import tempfile
import unicodedata
from dataclasses import replace
from datetime import datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from navkit.capabilities import FULL, VGA_PALETTE, TerminalInfo, rgb_of  # noqa: E402
from navkit.glyphs import GLYPHS_UNICODE  # noqa: E402
from navkit.screen import ScreenBuffer  # noqa: E402
from navkit.style import Style  # noqa: E402

SVG = ROOT / "docs" / "screenshot.svg"
README = ROOT / "README.md"
BEGIN, END = "<!-- screenshot:begin -->", "<!-- screenshot:end -->"
IMAGE_URL = "https://raw.githubusercontent.com/yogsagot/navigator/master/docs/screenshot.svg"

# What the panels list.  Sizes are fixed so the size column is; nothing reads
# a date, but they are pinned anyway so the scene is the same scene on disk.
TREE: dict[str, int | None] = {
    "bin": None,
    "docs": None,
    "src": None,
    "tests": None,
    ".gitignore": 214,
    "LICENSE": 1071,
    "Makefile": 2318,
    "README.md": 7482,
    "config.nss": 4096,
    "navigator.log": 183_552,
    "pyproject.toml": 1904,
    "setup.cfg": 612,
}
SUBTREE: dict[str, int | None] = {
    "navigator": None,
    "navkit": None,
    "navml": None,
    "__init__.py": 0,
    "app.py": 12_847,
    "console.py": 9_311,
    "screen.py": 18_205,
    "widgets.py": 22_596,
}
PINNED_TIME = datetime(1999, 12, 31, 23, 59).timestamp()


class HeadlessTerminal:
    """The surface :class:`~navkit.application.Application` needs of a tty.

    ``tests/conftest.py`` has the same thing for the suite; a tool does not
    import from ``tests/``.
    """

    def __init__(self, width: int, height: int, info: TerminalInfo):
        self.info = info
        self.size = (width, height)
        self.is_tty = False
        self.input_fd = -1

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def set_title(self, title: str) -> None: ...
    def read(self, size: int = 0) -> bytes: return b""
    def write(self, text: str) -> None: ...
    def flush(self) -> None: ...


def populate(directory: Path) -> None:
    def fill(where: Path, entries: dict[str, int | None]) -> None:
        for name, size in entries.items():
            path = where / name
            if size is None:
                path.mkdir()
            else:
                path.write_bytes(b"\0" * size)
            os.utime(path, (PINNED_TIME, PINNED_TIME))

    fill(directory, TREE)
    fill(directory / "src", SUBTREE)


def paint(theme: str, width: int, height: int) -> tuple[ScreenBuffer, TerminalInfo]:
    """The desktop as ``nav --theme THEME`` shows it in a WIDTHxHEIGHT tty."""
    from navigator.__main__ import Navigator
    from navigator.scheme import load_scheme
    from navigator.widgets.about_dialog import AboutDialog
    from navigator.widgets.clock import clock as clock_module
    from navigator.widgets.console import Console

    clock_module.now = lambda: datetime(2026, 1, 1, 12, 34)
    Console.start = lambda self, argv=None: None
    # The unicode tier, not the Nerd one: whoever views the SVG has no Nerd
    # Font, and the icon gutter would be a column of replacement boxes.
    info = replace(FULL, palette=VGA_PALETTE, glyphs=GLYPHS_UNICODE)

    async def main() -> ScreenBuffer:
        app = Navigator(
            Path("."),
            Path("src"),
            load_scheme(theme),
            terminal=HeadlessTerminal(width, height, info),
        )
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.15)
        # Started from here rather than through the command, which would need
        # a key or a menu walk; outside a dispatch, `execute' is content to
        # be awaited, and the task is cancelled with the app.
        asyncio.create_task(AboutDialog().execute(app))
        await asyncio.sleep(0.15)
        buffer = ScreenBuffer(width, height)
        app.shell.render_tree(buffer)
        app.exit()
        await task
        return buffer

    home = Path.cwd()
    with tempfile.TemporaryDirectory() as scratch:
        populate(Path(scratch))
        os.chdir(scratch)
        try:
            return asyncio.run(asyncio.wait_for(main(), 10)), info
        finally:
            os.chdir(home)


# -- plain text ---------------------------------------------------------------


def as_text(buffer: ScreenBuffer) -> str:
    rows = (
        "".join(buffer.get(x, y)[0] or "" for x in range(buffer.width)).rstrip()
        for y in range(buffer.height)
    )
    return "\n".join(rows) + "\n"


def readme_block(text: str, width: int, height: int) -> str:
    return (
        f"{BEGIN}\n"
        f"![Navigator, {width}x{height}]({IMAGE_URL})\n\n"
        "<details><summary>The same screen, as text</summary>\n\n"
        f"```text\n{text}```\n\n"
        "</details>\n"
        f"{END}"
    )


def with_block(readme: str, block: str) -> str:
    pattern = re.compile(re.escape(BEGIN) + ".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(readme):
        sys.exit(f"{README.name}: no {BEGIN} ... {END} markers to write between")
    return pattern.sub(lambda _: block, readme, count=1)


# -- SVG ----------------------------------------------------------------------

CELL_W, CELL_H = 10, 20
FONT_SIZE = 16.5
BASELINE = 15
PAD = 12
GAP = 2  # half the distance between the two strokes of a double line
FONTS = "'DejaVu Sans Mono', 'Cascadia Mono', Menlo, Consolas, 'Liberation Mono', monospace"

_DIRECTIONS = {
    "UP": "u",
    "DOWN": "d",
    "LEFT": "l",
    "RIGHT": "r",
    "HORIZONTAL": "lr",
    "VERTICAL": "ud",
}
_WEIGHTS = {"LIGHT": 1, "SINGLE": 1, "DOUBLE": 2}
_SHADES = {"░": 0.25, "▒": 0.5, "▓": 0.75, "█": 1.0}
_HALVES = {"▀": (0, 0, 1, 0.5), "▄": (0, 0.5, 1, 0.5), "▌": (0, 0, 0.5, 1), "▐": (0.5, 0, 0.5, 1)}


def box_arms(char: str) -> dict[str, int] | None:
    """The arms of a single/double box-drawing character and their weights.

    Read off the Unicode name, which spells every one of them the same two
    ways: ``LIGHT DOWN AND RIGHT`` (one weight throughout) or ``DOWN SINGLE
    AND RIGHT DOUBLE`` (a weight per group).  Heavy, dashed and rounded
    pieces answer None and are left to the font.
    """
    if not "─" <= char <= "╿":
        return None
    words = unicodedata.name(char, "").removeprefix("BOX DRAWINGS ").split()
    arms: dict[str, int] = {}
    if words and words[0] in ("LIGHT", "DOUBLE"):
        weight = _WEIGHTS[words[0]]
        for word in words[1:]:
            if word == "AND":
                continue
            if word not in _DIRECTIONS:
                return None
            for arm in _DIRECTIONS[word]:
                arms[arm] = weight
        return arms or None
    pending: list[str] = []
    for word in words:
        if word in _DIRECTIONS:
            pending.append(_DIRECTIONS[word])
        elif word in _WEIGHTS and pending:
            for group in pending:
                for arm in group:
                    arms[arm] = _WEIGHTS[word]
            pending = []
        elif word != "AND":
            return None
    return arms if arms and not pending else None


def box_lines(arms: dict[str, int], x: float, y: float) -> list[tuple[float, float, float, float]]:
    """Line segments drawing *arms* in the cell whose corner is *x*, *y*.

    Drawn rather than left to the font because a font's box glyphs meet
    their neighbours only if its line height is exactly the cell's, which an
    SVG in somebody else's browser cannot promise.
    """
    cx, cy = x + CELL_W / 2, y + CELL_H / 2
    edge = {"u": y, "d": y + CELL_H, "l": x, "r": x + CELL_W}
    perpendicular = {"u": "lr", "d": "lr", "l": "ud", "r": "ud"}
    sign = {"u": -1, "d": 1, "l": -1, "r": 1}
    lines = []
    for arm, weight in arms.items():
        vertical = arm in "ud"
        centre = cy if vertical else cx
        if weight == 1:
            doubles = [p for p in perpendicular[arm] if arms.get(p) == 2]
            # Through a double crossing, stop at the near stroke; round a
            # double corner, reach the far one.
            start = centre + sign[arm] * GAP * (1 if len(doubles) == 2 else -1) if doubles else centre
            if vertical:
                lines.append((cx, start, cx, edge[arm]))
            else:
                lines.append((start, cy, edge[arm], cy))
            continue
        for side in perpendicular[arm]:
            offset = sign[side] * GAP
            # The stroke on a side a double arm leaves by turns the corner
            # there; otherwise it runs across to the far stroke.
            start = centre + sign[arm] * GAP if arms.get(side) == 2 else centre - sign[arm] * GAP
            if vertical:
                lines.append((cx + offset, start, cx + offset, edge[arm]))
            else:
                lines.append((start, cy + offset, edge[arm], cy + offset))
    return lines


def hex_of(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def colours(style: Style, info: TerminalInfo) -> tuple[str, str]:
    """Foreground and background as ``#rrggbb``, as a VGA text screen shows them."""
    fg = rgb_of(info.adapt(style.fg)) if style.fg is not None else VGA_PALETTE[7]
    bg = rgb_of(info.adapt(style.bg)) if style.bg is not None else VGA_PALETTE[0]
    if style.reverse:
        fg, bg = bg, fg
    if style.dim:
        fg = tuple((f + b) // 2 for f, b in zip(fg, bg))
    return hex_of(fg), hex_of(bg)


def as_svg(buffer: ScreenBuffer, info: TerminalInfo) -> str:
    width, height = buffer.width * CELL_W, buffer.height * CELL_H
    backgrounds, strokes, texts = [], [], []
    for row in range(buffer.height):
        y = row * CELL_H
        cells = [buffer.get(x, row) for x in range(buffer.width)]
        painted = [colours(style, info) for _, style in cells]

        start = 0
        for x in range(1, buffer.width + 1):
            if x == buffer.width or painted[x][1] != painted[start][1]:
                backgrounds.append(
                    f'<rect x="{start * CELL_W}" y="{y}" width="{(x - start) * CELL_W}"'
                    f' height="{CELL_H}" fill="{painted[start][1]}"/>'
                )
                start = x

        run: list[str] = []
        run_start, run_key = 0, None

        def close_run(cells_each: int = 1) -> None:
            if not run:
                return
            fg, bold, italic, underline = run_key
            attributes = f' fill="{fg}"'
            attributes += ' font-weight="bold"' if bold else ""
            attributes += ' font-style="italic"' if italic else ""
            attributes += ' text-decoration="underline"' if underline else ""
            # One <text> per word, each placed on its own cell: a renderer
            # that collapses spaces then has none to collapse, and
            # textLength pins every word to exactly the cells it covers.
            for word in re.finditer(r"\S+", "".join(run)):
                texts.append(
                    f'<text x="{(run_start + word.start() * cells_each) * CELL_W}" y="{y + BASELINE}"'
                    f' textLength="{len(word.group()) * cells_each * CELL_W}" lengthAdjust="spacingAndGlyphs"'
                    f"{attributes}>{escape(word.group())}</text>"
                )

        x = 0
        while x < buffer.width:
            char, style = cells[x]
            fg, bg = painted[x]
            span = 2 if x + 1 < buffer.width and cells[x + 1][0] == "" else 1
            arms = box_arms(char)
            vector = arms is not None or char in _SHADES or char in _HALVES
            key = (fg, style.bold, style.italic, style.underline)
            if vector or key != run_key or span == 2:
                close_run()
                # A drawn cell is no part of any run, so the next one starts
                # after it.
                run, run_start, run_key = [], x + (span if vector else 0), None if vector else key
            if arms is not None:
                for x1, y1, x2, y2 in box_lines(arms, x * CELL_W, y):
                    strokes.append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{fg}"/>')
            elif char in _SHADES:
                strokes.append(
                    f'<rect x="{x * CELL_W}" y="{y}" width="{CELL_W}" height="{CELL_H}"'
                    f' fill="{fg}" fill-opacity="{_SHADES[char]}"/>'
                )
            elif char in _HALVES:
                left, top, w, h = _HALVES[char]
                strokes.append(
                    f'<rect x="{x * CELL_W + left * CELL_W:g}" y="{y + top * CELL_H:g}"'
                    f' width="{w * CELL_W:g}" height="{h * CELL_H:g}" fill="{fg}"/>'
                )
            else:
                run.append(char or " ")
                if span == 2:
                    # A wide character is a run of its own, two cells long.
                    close_run(cells_each=2)
                    run, run_start, run_key = [], x + span, None
            x += span
        close_run()

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width + 2 * PAD}"'
            f' height="{height + 2 * PAD}" viewBox="0 0 {width + 2 * PAD} {height + 2 * PAD}">',
            "<!-- generated by tools/screenshot.py; re-run it rather than editing this -->",
            f'<rect width="100%" height="100%" rx="8" fill="{hex_of(VGA_PALETTE[0])}"/>',
            f'<g transform="translate({PAD} {PAD})">',
            '<g shape-rendering="crispEdges">',
            *backgrounds,
            "</g>",
            f'<g font-family="{escape(FONTS)}" font-size="{FONT_SIZE}">',
            *texts,
            "</g>",
            '<g stroke-width="1.25" stroke-linecap="square">',
            *strokes,
            "</g>",
            "</g>",
            "</svg>",
            "",
        ]
    )


# -- the command line ---------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--theme", default="default", help="colour scheme (default: %(default)s)")
    parser.add_argument("--size", default="80x24", help="WIDTHxHEIGHT (default: %(default)s)")
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if anything would change")
    args = parser.parse_args(argv)
    try:
        width, height = (int(part) for part in args.size.lower().split("x"))
    except ValueError:
        parser.error(f"--size wants WIDTHxHEIGHT, not {args.size!r}")

    buffer, info = paint(args.theme, width, height)
    outputs = {
        SVG: as_svg(buffer, info),
        README: with_block(README.read_text(encoding="utf-8"), readme_block(as_text(buffer), width, height)),
    }
    stale = [path for path, text in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != text]
    if args.check:
        for path in stale:
            print(f"{path.relative_to(ROOT)} is out of date", file=sys.stderr)
        return 1 if stale else 0
    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(outputs[path], encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
