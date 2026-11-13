#!/usr/bin/env python3
"""Paint Navigator headless and write its screens out as screenshots.

Run it from the repository root::

    ./venv/bin/python tools/screenshot.py

It paints every scene in :data:`SCENES`.  The first, ``desktop``, is the
README's, and writes two things, both of them text:

- ``docs/screenshot.svg``, every cell in the colours the theme gives it, so
  the README can show the desktop the way a terminal does.  Neither GitHub nor
  PyPI will colour Markdown -- both strip ``style=`` and raw escapes, and
  GitHub ignores an ```` ```ansi ```` fence -- so an SVG made of ``<text>`` and
  ``<rect>`` is the closest a README gets to a terminal.
- the same screen as plain characters, written into ``README.md`` between the
  ``<!-- screenshot:begin -->`` and ``<!-- screenshot:end -->`` markers.
  Nothing outside the markers is touched.

Every other scene is one of Help's pictures (the ``navigator-help`` skill has
the rules), cropped to the thing it shows and written twice into
``docs/en/shots/``:

- ``NAME.svg``, which the page's Markdown names and GitHub shows;
- ``NAME.ans``, the same cells as text with SGR colours, which Navigator's
  own help window reads in the SVG's place (:func:`as_ansi` has the grammar,
  ``navigator/lib/help/ansi.py`` the reader) and ``cat`` shows in a terminal.

``--check`` writes nothing and exits 1 if anything would change, which is what
to run after a change to anything a scene paints.  ``--only NAME`` paints one
scene; ``--no-readme`` leaves the desktop out, which is what the test runs
(``tests/test_screenshot.py``): the desktop shows the version, so a release
makes it stale, and the suite a release runs must not fail on that.

``--language CODE`` paints the scenes in another catalogue's language -- a
right-to-left one (``he``, ``ar``) mirrored, as ``nav --language he`` shows
it.  The desktop then writes only ``docs/screenshot-CODE.svg`` (the README's
picture and text block stay the English scene), and Help's pictures go to
``docs/CODE/shots/``.

The screen is the real one: the application is constructed as ``nav``
constructs it and rendered into a :class:`~navkit.screen.ScreenBuffer`, with
the four things that would make it differ between runs pinned -- the
directory it lists (built here, with fixed sizes), the clock, the free
space under each panel, and the shell the console would otherwise fork.  This is the golden test's recipe
(``tests/test_nav.py``), applied to a directory worth looking at, with the
About box (≡ > About) open over it -- so the picture carries the version, and
a release makes ``--check`` stale until the screenshot is regenerated.

The panels are drawn in the simple mode, not the shipped default
(``[panel_defaults] view_mode = detailed``): a decision, so the picture keeps
DN's classic two-column look -- a change of default panel mode does not
change the screenshot.

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
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from navkit.bidi import has_rtl  # noqa: E402
from navkit.capabilities import FULL, VGA_PALETTE, TerminalInfo, rgb_of  # noqa: E402
from navkit.glyphs import GLYPHS_UNICODE  # noqa: E402
from navkit.screen import ScreenBuffer  # noqa: E402
from navkit.style import RESET_SGR, Style  # noqa: E402

SVG = ROOT / "docs" / "screenshot.svg"
README = ROOT / "README.md"
BEGIN, END = "<!-- screenshot:begin -->", "<!-- screenshot:end -->"
IMAGE_URL = "https://raw.githubusercontent.com/yogsagot/navigator/master/docs/screenshot.svg"
DOCS = ROOT / "docs"

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
PROMPT = (
    b"\x1b[01;38;2;85;255;85mjuris@juris-dev\x1b[00;38;2;255;255;255m:"
    b"\x1b[01;38;2;85;85;255m~/development/navigator\x1b[00;38;2;255;255;255m$ "
)


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
    # Filling a directory moved its time again: the *Current file* line on
    # ``src``'s ``..`` shows it.
    for path in (directory / "src", directory):
        os.utime(path, (PINNED_TIME, PINNED_TIME))


# -- the scenes ---------------------------------------------------------------


@dataclass(frozen=True)
class Scene:
    """One picture: what is opened over the pinned desktop, and how much of
    the screen is kept."""

    name: str
    #: Opens what the picture shows, over the running application.  It answers
    #: the widget to crop to (with its shadow), or None for the whole screen.
    #: A dialog is started with ``asyncio.create_task(dialog.execute(app))``
    #: rather than through its command, which would need a key or a menu
    #: walk; outside a dispatch, ``execute`` is content to be awaited, and
    #: the task is cancelled with the app.
    stage: Callable[[Any], Awaitable[Any]]
    size: tuple[int, int] = (80, 24)


async def _about(app: Any) -> None:
    from navigator.widgets.about_dialog import AboutDialog

    asyncio.create_task(AboutDialog().execute(app))
    return None


async def _make_directory(app: Any) -> Any:
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

    dialog = MkdirDialog()
    asyncio.create_task(dialog.execute(app))
    return dialog


#: The first is the README's and is written where the README wants it; the
#: rest are Help's.  A Help scene shows nothing that changes between runs or
#: releases (no version, no date that is not pinned), and is cropped to at
#: most 72 columns unless it is meant for the website alone: wider, a help
#: window on an 80-column terminal shows its alt text instead.
SCENES: tuple[Scene, ...] = (
    Scene("desktop", _about),
    Scene("make-directory", _make_directory),
)
README_SCENE = SCENES[0]


def cropped(buffer: ScreenBuffer, widget: Any) -> ScreenBuffer:
    """The cells of *buffer* under *widget* and its shadow.

    *widget* is a child of the root (an overlay), so its ``x``/``y`` are the
    screen's; on a mirrored screen the rectangle is mirrored with it.
    """
    shadow = 2 if widget.shadow else 0
    left = max(0, widget.x)
    top = max(0, widget.y)
    right = min(buffer.width, widget.x + widget.width + shadow)
    bottom = min(buffer.height, widget.y + widget.height + shadow // 2)
    if buffer.rtl:
        left, right = buffer.width - right, buffer.width - left
    piece = ScreenBuffer(right - left, bottom - top)
    piece.blit(buffer, 0, 0, left, top, right - left, bottom - top)
    return piece


def paint(
    scene: Scene, theme: str, size: tuple[int, int] | None = None, language_code: str | None = None
) -> tuple[ScreenBuffer, TerminalInfo]:
    """*scene* as ``nav --theme THEME`` shows it in a tty of the scene's size
    (or *size*) -- in *language_code*'s catalogue, mirrored if it reads right
    to left -- cropped to what the scene keeps."""
    from navigator.__main__ import Navigator
    from navigator.lib.appearance.scheme import load_scheme
    from navigator.settings import SETTINGS
    from navigator.widgets.shell.clock import clock as clock_module
    from navigator.lib.drives import listing as listing_module
    from navigator.widgets.shell.console import Console

    clock_module.now = lambda: datetime(2026, 1, 1, 12, 34)
    Console.start = lambda self, argv=None: None
    listing_module.free_space_of = lambda path: (412_316_860_416, "/")
    # The simple mode, whatever the shipped default: see the module docstring.
    SETTINGS.panel_defaults.view_mode = "simple"
    # No option strips on the panels' bottom frames: the picture is of the
    # file manager DN drew, not of the switches Navigator added to it.
    SETTINGS.file_manager.show_options = False
    # Nor git's letters and branch, whatever repository the directory is in.
    SETTINGS.file_manager.git_status = False
    # The unicode tier, not the Nerd one: whoever views the SVG has no Nerd
    # Font, and the icon gutter would be a column of replacement boxes.
    info = replace(FULL, palette=VGA_PALETTE, glyphs=GLYPHS_UNICODE)
    width, height = size or scene.size

    async def main() -> ScreenBuffer:
        app = Navigator(
            Path("."),
            Path("src"),
            load_scheme(theme),
            terminal=HeadlessTerminal(width, height, info),
        )
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.15)
        # Staged for the picture, and untrue on purpose: under a modal the key
        # bar is empty, since nothing the dialog binds carries a caption, and
        # most of the file panel's commands are greyed until they exist.  The
        # line is kept as the file panel shows it, every item enabled.
        bound = app.bindings()
        app.bindings = lambda start=None: bound
        # The shell's own prompt, as if it had printed one where the panel
        # is: Debian's default bash PS1, in xfce4-terminal's default colours
        # (its VGA palette, bold shown bright, a white foreground), spelled as RGB so the theme's
        # palette cannot repaint it.
        app.shell.console._prompted(PROMPT, app.shell._front_directory())
        app.command_enabled = lambda command: True
        keep = await scene.stage(app)
        await asyncio.sleep(0.15)
        buffer = ScreenBuffer(width, height)
        # Composed left to right and flipped on the way out, as the
        # application does a frame (Application._back, ScreenBuffer.mirrored).
        buffer.rtl = app.rtl
        app.shell.render_tree(buffer)
        if buffer.rtl:
            mirrored = buffer.mirrored()
            mirrored.rtl = True
            buffer = mirrored
        if keep is not None:
            buffer = cropped(buffer, keep)
        app.exit()
        await task
        return buffer

    home = Path.cwd()
    if language_code is not None:
        from navigator.lib.config import language

        language.install(Path(tempfile.gettempdir()) / "navigator-screenshot-none")
        language.apply(language_code)
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


# -- colours ------------------------------------------------------------------

type RGB = tuple[int, int, int]


def resolved(style: Style, info: TerminalInfo) -> tuple[RGB, RGB]:
    """Foreground and background as a VGA text screen shows *style*: the
    palette, reverse and dim applied.  One answer for the SVG and the ``.ans``
    file, so the two are the same picture."""
    fg = VGA_PALETTE[7] if style.fg is None else rgb_of(info.adapt(style.fg))
    bg = VGA_PALETTE[0] if style.bg is None else rgb_of(info.adapt(style.bg))
    if style.reverse:
        fg, bg = bg, fg
    if style.dim:
        fg = ((fg[0] + bg[0]) // 2, (fg[1] + bg[1]) // 2, (fg[2] + bg[2]) // 2)
    return fg, bg


# -- ANSI ---------------------------------------------------------------------


def as_ansi(buffer: ScreenBuffer, info: TerminalInfo) -> str:
    """*buffer* as text a terminal paints and ``navigator/lib/help/ansi.py`` reads.

    The whole grammar, kept this small so the reader can be strict:

    - one line a screen row, each ended ``ESC[0m`` and a newline; no cursor
      movement and no other escape;
    - every run of cells that look alike is preceded by one ``ESC[0;...m``
      that says all of its look (:meth:`~navkit.style.Style.sgr` starts with
      a reset), never a change from the run before;
    - both colours are always there and always ``38;2;r;g;b``/``48;2;r;g;b``,
      resolved here exactly as the SVG's are -- the palette, reverse and dim
      already applied -- so the file means the same colours in any terminal
      and under any theme; of the attributes only bold (1), italic (3),
      underline (4) and strike (9) are left to say;
    - a wide character is written once, its second cell not at all.
    """
    lines = []
    for row in range(buffer.height):
        parts: list[str] = []
        last: Style | None = None
        for x in range(buffer.width):
            char, style = buffer.get(x, row)
            if char == "":
                continue  # the second half of a wide character
            fg, bg = resolved(style, info)
            look = Style(
                fg=fg, bg=bg, bold=style.bold, italic=style.italic,
                underline=style.underline, strike=style.strike,
            )
            if look != last:
                parts.append(look.sgr())
                last = look
            parts.append(char)
        lines.append("".join(parts) + RESET_SGR + "\n")
    return "".join(lines)


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
    fg, bg = resolved(style, info)
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
            fg, bold, italic, underline, strike = run_key
            attributes = f' fill="{fg}"'
            attributes += ' font-weight="bold"' if bold else ""
            attributes += ' font-style="italic"' if italic else ""
            decoration = " ".join(name for name, on in (("underline", underline), ("line-through", strike)) if on)
            attributes += f' text-decoration="{decoration}"' if decoration else ""
            # One <text> per word, each placed on its own cell: a renderer
            # that collapses spaces then has none to collapse, and
            # textLength pins every word to exactly the cells it covers.
            for word in re.finditer(r"\S+", "".join(run)):
                # The cells are in the order they are painted already (a
                # Hebrew scene's laid out by navkit.bidi): a renderer must not
                # turn a right-to-left word round a second time.
                override = ' unicode-bidi="bidi-override" direction="ltr"' if has_rtl(word.group()) else ""
                texts.append(
                    f'<text x="{(run_start + word.start() * cells_each) * CELL_W}" y="{y + BASELINE}"'
                    f' textLength="{len(word.group()) * cells_each * CELL_W}" lengthAdjust="spacingAndGlyphs"'
                    f"{override}{attributes}>{escape(word.group())}</text>"
                )

        x = 0
        while x < buffer.width:
            char, style = cells[x]
            fg, bg = painted[x]
            span = 2 if x + 1 < buffer.width and cells[x + 1][0] == "" else 1
            arms = box_arms(char)
            vector = arms is not None or char in _SHADES or char in _HALVES
            key = (fg, style.bold, style.italic, style.underline, style.strike)
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


def shots_dir(language_code: str | None) -> Path:
    """Where a language's Help pictures go: ``docs/CODE/shots``."""
    return DOCS / (language_code or "en") / "shots"


def outputs_of(
    scene: Scene, theme: str, size: tuple[int, int] | None, language_code: str | None
) -> dict[Path, str]:
    """Every file *scene* writes, by path."""
    buffer, info = paint(scene, theme, size, language_code)
    if scene is not README_SCENE:
        where = shots_dir(language_code)
        return {
            where / f"{scene.name}.svg": as_svg(buffer, info),
            where / f"{scene.name}.ans": as_ansi(buffer, info),
        }
    if language_code is not None:
        return {SVG.with_name(f"screenshot-{language_code}.svg"): as_svg(buffer, info)}
    return {
        SVG: as_svg(buffer, info),
        README: with_block(
            README.read_text(encoding="utf-8"), readme_block(as_text(buffer), buffer.width, buffer.height)
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--theme", default="default", help="colour scheme (default: %(default)s)")
    parser.add_argument("--size", default=None, help="WIDTHxHEIGHT of the terminal (default: the scene's, 80x24)")
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if anything would change")
    parser.add_argument(
        "--only", default=None, metavar="NAME", choices=[scene.name for scene in SCENES],
        help="paint this scene alone (%(choices)s)",
    )
    parser.add_argument(
        "--no-readme", action="store_true",
        help="leave the README's scene out: Help's pictures alone, which no release makes stale",
    )
    parser.add_argument(
        "--language", default=None, metavar="CODE",
        help="paint in this catalogue's language (he, ar mirrored): the desktop into docs/screenshot-CODE.svg "
             "instead of the README's English scene, Help's pictures into docs/CODE/shots/",
    )
    args = parser.parse_args(argv)
    size = None
    if args.size is not None:
        try:
            width, height = (int(part) for part in args.size.lower().split("x"))
        except ValueError:
            parser.error(f"--size wants WIDTHxHEIGHT, not {args.size!r}")
        size = (width, height)

    outputs: dict[Path, str] = {}
    for scene in SCENES:
        if args.only in (None, scene.name) and not (args.no_readme and scene is README_SCENE):
            outputs.update(outputs_of(scene, args.theme, size, args.language))
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
