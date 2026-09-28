"""The screen a child program paints on.

This is the other half of :mod:`navkit.terminal`.  There, bytes arriving from
the user are decoded into events; here, bytes arriving from a program
Navigator started are decoded into cells.  Having them -- rather than letting
them go straight to the terminal -- is the whole point: DOS Navigator could
show the last program's output behind its panels because in DOS there was one
screen and the output was still sitting in it.  A terminal will not hand its
cells back, so the only way to have them is to have been the one who received
them.

The emulation itself is `pyte`_, which is a complete and well-tested VT
implementation and the one run-time dependency Navigator carries.  What lives
here is the translation between pyte's idea of a screen and navkit's:

* pyte stores colours as *names* (``"brown"``, ``"brightblue"``) or six-digit
  hex strings, where :class:`~navkit.style.Style` wants a palette index or an
  ``(r, g, b)`` triple.  :data:`PALETTE_NAMES` is the whole of that seam.
* pyte's grid is a sparse mapping; navkit's is a list of rows.  The mirror
  below converts only the rows pyte reports as dirty, so a screenful of output
  costs one row conversion per line that actually changed, and painting the
  console costs one bulk row copy per frame.

The two happen to agree on the thing that would have been painful to
reconcile: a double-width character occupies its own cell plus a following
cell holding ``""``.

.. _pyte: https://github.com/selectel/pyte
"""

from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache

import re
from collections import defaultdict
from typing import Any, Callable

import pyte
from pyte import graphics as _graphics
from pyte.screens import Char, StaticDefaultDict

from navkit.screen import ScreenBuffer, Surface
from navkit.style import Color, Style

#: How many lines of scrollback a console keeps by default.
DEFAULT_HISTORY = 2000

#: pyte's colour names, in the order of the sixteen palette registers.  pyte
#: takes its names from the SGR tables -- 33 is "brown" and 93 is
#: "brightbrown" -- so these are not navkit's constant names, but they land on
#: navkit's indices, which is what a pinned palette resolves.
PALETTE_NAMES: dict[str, Color] = {
    "black": 0,
    "red": 1,
    "green": 2,
    "brown": 3,
    "blue": 4,
    "magenta": 5,
    "cyan": 6,
    "white": 7,
    "brightblack": 8,
    "brightred": 9,
    "brightgreen": 10,
    "brightbrown": 11,
    "brightblue": 12,
    "brightmagenta": 13,
    "brightcyan": 14,
    "brightwhite": 15,
    # pyte 0.8.2 misspells the background form of bright magenta in
    # `graphics.BG_AIXTERM`.  Carrying the typo is what keeps `ESC [ 105 m`
    # from silently losing its colour; the correct spelling is above, so this
    # costs nothing if a later release fixes it.
    "bfightmagenta": 13,
}

#: The hex strings pyte produces for the first sixteen entries of the 256
#: colour cube, mapped back to the index they came from.  Without this
#: ``ESC [ 38;5;4 m`` would arrive as an ``(r, g, b)`` triple and step around
#: the pinned palette, so the same blue would come out two different colours
#: depending on which escape asked for it.  Index 16 of the cube is also pure
#: black and folds onto index 0, which is the colour it already was.
_INDEXED_HEX: dict[str, Color] = {
    hexcode: index
    for index, hexcode in enumerate(_graphics.FG_BG_256[:16])
}


@lru_cache(maxsize=256)
def color_of(name: str) -> Color | None:
    """Translate one pyte colour name into a navkit colour.

    ``None`` for ``"default"`` -- meaning the terminal's own -- an index where
    the colour came from the sixteen, and an ``(r, g, b)`` triple otherwise.
    """
    if name == "default":
        return None
    indexed = PALETTE_NAMES.get(name)
    if indexed is not None:
        return indexed
    indexed = _INDEXED_HEX.get(name)
    if indexed is not None:
        return indexed
    try:
        packed = int(name, 16)
    except ValueError:
        return None
    return ((packed >> 16) & 0xFF, (packed >> 8) & 0xFF, packed & 0xFF)


@lru_cache(maxsize=256)
def _style(
    fg: str, bg: str, bold: bool, italics: bool, underscore: bool, reverse: bool
) -> Style:
    return Style(
        fg=color_of(fg),
        bg=color_of(bg),
        bold=bold,
        italic=italics,
        underline=underscore,
        reverse=reverse,
        # The program asked for the terminal's colours, not DOS Navigator's.
        terminal_palette=True,
    )


def style_of(char: Char) -> Style:
    """The :class:`~navkit.style.Style` a pyte cell is asking for.

    Memoised on the cell's *appearance* rather than on the cell.  A ``Char``
    carries its character too, so caching the whole of it would key the table
    by ``(character, appearance)`` and miss on every new letter; a screen full
    of program output has thousands of cells and a handful of appearances
    between them, which is the ratio worth exploiting.

    pyte's ``blink`` and ``strikethrough`` have nowhere to go -- ``Style``
    carries the seven attributes a DOS Navigator cell could have, and those
    are not among them.
    """
    return _style(
        char.fg, char.bg, char.bold, char.italics, char.underscore, char.reverse
    )


#: The private modes that switch to the alternate screen: 47 and 1047 swap
#: the buffer, 1049 saves the cursor as well.  xterm's, and what every
#: full-screen program's ``smcup`` sends.
ALT_SCREEN_MODES = frozenset({47, 1047, 1049})

#: The private modes that turn mouse reporting on, least to most: X10 (press
#: only), normal (press and release), button-event (and drags), any-event.
MOUSE_MODES = (9, 1000, 1002, 1003)

#: DECCKM, application cursor keys.
_DECCKM = 1 << 5
#: SGR mouse encoding, ``CSI < b ; x ; y M``.
_MOUSE_SGR = 1006 << 5


class _Screen(pyte.HistoryScreen):
    """pyte's screen with the two things a full-screen program needs of it.

    **The alternate screen.**  pyte records mode 1049 and does nothing about
    it, so ``htop`` drew over the shell's output and its last frame stayed
    there after it quit.  Here the main buffer is put aside on the way in and
    brought back on the way out, as xterm does; nothing scrolled off the
    alternate screen reaches the scrollback, which is the main screen's.

    **Answers.**  A program asking the terminal something -- where the cursor
    is, what the terminal is -- gets pyte's reply through
    :meth:`write_process_input`, which pyte leaves a no-op.  *respond* is
    where it goes, which is the pty; a curses program that asks and never
    hears back can sit waiting for an answer.
    """

    def __init__(self, columns: int, lines: int, history: int) -> None:
        self._main: Any = None
        self.respond: Callable[[bytes], None] | None = None
        super().__init__(columns, lines, history=history)

    @property
    def alternate(self) -> bool:
        return self._main is not None

    def write_process_input(self, data: str) -> None:
        if self.respond is not None:
            self.respond(data.encode())

    def set_mode(self, *modes: int, **kwargs: Any) -> None:
        if kwargs.get("private") and ALT_SCREEN_MODES.intersection(modes):
            self._enter_alternate(save_cursor=1049 in modes)
        super().set_mode(*modes, **kwargs)

    def reset_mode(self, *modes: int, **kwargs: Any) -> None:
        if kwargs.get("private") and ALT_SCREEN_MODES.intersection(modes):
            self._leave_alternate(restore_cursor=1049 in modes)
        super().reset_mode(*modes, **kwargs)

    def _enter_alternate(self, save_cursor: bool) -> None:
        if self._main is not None:
            return
        if save_cursor:
            self.save_cursor()
        self._main = self.buffer
        self.buffer = defaultdict(lambda: StaticDefaultDict(self.default_char))
        self.dirty.update(range(self.lines))

    def _leave_alternate(self, restore_cursor: bool) -> None:
        if self._main is None:
            return
        self.buffer, self._main = self._main, None
        if restore_cursor:
            self.restore_cursor()
        self.dirty.update(range(self.lines))

    # pyte hands a private CSI (``CSI ? ...``) to the plain handler with
    # ``private=True``, and most of them take no such keyword: ``mc`` sends
    # xterm's ``CSI ? Pm r`` (restore private modes) on the way out, and
    # ``set_margins`` raised.  A private form pyte has no meaning for is
    # dropped here; ``CSI ? K``, DECSEL, is an erase whatever it protects.

    def erase_in_line(self, how: int = 0, private: bool = False, **_: Any) -> None:
        super().erase_in_line(how)

    def index(self) -> None:
        if self._main is not None:
            # The alternate screen has no history: skip HistoryScreen's.
            pyte.Screen.index(self)
        else:
            super().index()

    def reset(self) -> None:
        self._main = None
        super().reset()


def _drop_private(name: str) -> Callable[..., None]:
    base = getattr(pyte.HistoryScreen, name)

    def handler(self: Any, *params: Any, private: bool = False, **_: Any) -> None:
        if not private:
            base(self, *params)

    handler.__name__ = name
    return handler


for _name in (
    "insert_characters", "cursor_up", "cursor_down", "cursor_forward",
    "cursor_back", "cursor_down1", "cursor_up1", "cursor_to_column",
    "cursor_position", "insert_lines", "delete_lines", "delete_characters",
    "erase_characters", "cursor_to_line", "clear_tab_stop",
    "select_graphic_rendition", "report_device_status", "set_margins",
):
    setattr(_Screen, _name, _drop_private(_name))
del _name

#: ``CSI > Pm m`` and friends: xterm's key-modifier and query forms, which
#: pyte skips the ``>`` of and then dispatches as the plain sequence -- so
#: vim's ``CSI > 4 ; 2 m`` arrived as underline and bold.  None of them draw.
_XTERM_GT = re.compile(rb"\x1b\[[>=][0-9;]*[a-zA-Z]")


class ConsoleScreen:
    """A terminal screen Navigator owns, and the cells it currently shows.

    Feed it the bytes a child program writes and it keeps a
    :class:`~navkit.screen.ScreenBuffer` up to date; :meth:`blit_into` paints
    that buffer wherever it is wanted.
    """

    def __init__(
        self,
        columns: int = 80,
        lines: int = 24,
        *,
        history: int = DEFAULT_HISTORY,
    ):
        columns, lines = max(1, columns), max(1, lines)
        self.screen = _Screen(columns, lines, history)
        self.stream = pyte.ByteStream(self.screen)
        # The mirror.  pyte's buffer is a sparse mapping of rows to sparse
        # mappings of columns, which is the right shape for an emulator and
        # the wrong one for a blit; keeping a real grid beside it means the
        # per-frame cost is a row copy rather than a lookup per cell.
        self._mirror = ScreenBuffer(columns, lines)
        self._synced = False

    # -- geometry ------------------------------------------------------------

    @property
    def columns(self) -> int:
        return self.screen.columns

    @property
    def lines(self) -> int:
        return self.screen.lines

    def resize(self, columns: int, lines: int) -> None:
        columns, lines = max(1, columns), max(1, lines)
        if (columns, lines) == (self.screen.columns, self.screen.lines):
            return
        self.screen.resize(lines, columns)
        self._mirror.resize(columns, lines)
        self.screen.dirty.update(range(lines))
        self._synced = False

    # -- input ---------------------------------------------------------------

    def feed(self, data: bytes) -> None:
        """Decode *data* onto the screen.

        ``ByteStream`` keeps whatever it cannot yet decode, so a UTF-8
        character or an escape sequence split across two reads is handled
        once the rest arrives -- the same guarantee
        :class:`~navkit.terminal.InputParser` gives in the other direction.
        """
        if data:
            if b"\x1b[>" in data or b"\x1b[=" in data:
                data = _XTERM_GT.sub(b"", data)
            try:
                self.stream.feed(data)
            except Exception:
                # A sequence pyte chokes on must not take the console with it:
                # its parser is a generator, which an exception closes for
                # good.  Start a fresh one; the rest of this read is lost,
                # and whatever the program draws next lands.
                self.stream = pyte.ByteStream(self.screen)
            self._synced = False

    def reset(self) -> None:
        self.screen.reset()
        self.screen.dirty.update(range(self.screen.lines))
        self._synced = False

    # -- what the program asked the terminal for --------------------------------

    @property
    def respond(self) -> Callable[[bytes], None] | None:
        """Where the screen's answers to the program's queries are written."""
        return self.screen.respond

    @respond.setter
    def respond(self, callback: Callable[[bytes], None] | None) -> None:
        self.screen.respond = callback

    @property
    def application_cursor(self) -> bool:
        """DECCKM: the program wants its arrows as ``SS3``, not ``CSI``."""
        return _DECCKM in self.screen.mode

    @property
    def mouse_tracking(self) -> int:
        """The mouse mode the program turned on (9, 1000, 1002, 1003), or 0."""
        mode = self.screen.mode
        for tracking in reversed(MOUSE_MODES):
            if tracking << 5 in mode:
                return tracking
        return 0

    @property
    def mouse_sgr(self) -> bool:
        """Mode 1006: mouse reports in SGR's ``CSI < b ; x ; y M/m`` form."""
        return _MOUSE_SGR in self.screen.mode

    @property
    def alternate(self) -> bool:
        """A full-screen program is on the alternate screen."""
        return self.screen.alternate

    # -- scrollback ----------------------------------------------------------

    def prev_page(self) -> None:
        """Scroll one page back into history."""
        self.screen.prev_page()
        self._synced = False

    def next_page(self) -> None:
        """Scroll one page forward, back towards the live screen."""
        self.screen.next_page()
        self._synced = False

    @property
    def scrolled_back(self) -> bool:
        """True when the view is somewhere above the live screen."""
        history = self.screen.history
        return history.position < history.size

    # -- output --------------------------------------------------------------

    @property
    def cursor(self) -> tuple[int, int, bool]:
        """``(x, y, hidden)`` for the child's cursor."""
        cursor = self.screen.cursor
        return cursor.x, cursor.y, bool(cursor.hidden)

    def sync(self) -> bool:
        """Bring the mirror up to date; return whether anything moved.

        Only the rows pyte marked dirty are converted, and the mark is cleared
        afterwards, which is the contract pyte documents for ``Screen.dirty``.
        """
        if self._synced:
            return False
        dirty = self.screen.dirty
        self._synced = True
        if not dirty:
            return False
        mirror, columns = self._mirror, self.screen.columns
        for y in sorted(dirty):
            if not 0 <= y < mirror.height:
                continue
            row = self.screen.buffer[y]
            for x in range(columns):
                char = row[x]
                # A cell holding "" is the trailing half of a wide character,
                # and set_cell wrote it when it wrote the character itself.
                mirror.set_cell(x, y, char.data, style_of(char))
        dirty.clear()
        return True

    @property
    def surface(self) -> Surface:
        """The cells the child has painted, synced as of this call."""
        self.sync()
        return self._mirror

    def blit_into(self, surface: Surface, x: int = 0, y: int = 0) -> None:
        """Paint the console onto *surface* at *x*, *y*."""
        self.sync()
        surface.blit(self._mirror, x, y)


def seed_from_host(console: ConsoleScreen) -> str | None:
    """Fill *console* with whatever was on the real screen before we started.

    Best effort, and usually impossible: output printed before Navigator ran
    belongs to the terminal, and no escape sequence asks for it back.  Where a
    host does keep it and will say so, this is the closest thing to what DOS
    Navigator got for free by reading video memory.  Returns the name of the
    route that worked, or ``None``.
    """
    for name, capture in (
        ("tmux", _capture_tmux),
        ("kitty", _capture_kitty),
        ("vcsa", _capture_vcsa),
    ):
        try:
            data = capture(console.lines)
        except (OSError, ValueError, subprocess.SubprocessError):
            continue
        if data:
            console.feed(data)
            return name
    return None


def _run(argv: list[str]) -> bytes | None:
    if shutil.which(argv[0]) is None:
        return None
    done = subprocess.run(argv, capture_output=True, timeout=2)
    return done.stdout if done.returncode == 0 else None


def _capture_tmux(lines: int) -> bytes | None:
    if not os.environ.get("TMUX"):
        return None
    # -e keeps the attributes, -p writes to stdout, -S starts `lines` rows
    # above the visible region so the seed is a full screen and not a stub.
    return _run(["tmux", "capture-pane", "-p", "-e", "-S", f"-{lines}"])


def _capture_kitty(lines: int) -> bytes | None:
    if not os.environ.get("KITTY_WINDOW_ID"):
        return None
    return _run(["kitty", "@", "get-text", "--extent", "screen", "--ansi"])


def _capture_vcsa(lines: int) -> bytes | None:
    """Read a Linux virtual console straight out of the kernel.

    ``/dev/vcsa<n>`` is this project's ancestor: four header bytes, then one
    attribute byte and one character byte per cell -- the layout DOS
    Navigator read at ``B800:0000``.  It exists only on a real VT, and only
    for a process that may open it.
    """
    tty = os.environ.get("TTY") or _controlling_tty()
    if not tty or not tty.startswith("/dev/tty") or not tty[8:].isdigit():
        return None
    with open(f"/dev/vcsa{tty[8:]}", "rb") as handle:
        raw = handle.read()
    if len(raw) < 4:
        return None
    rows, columns = raw[0], raw[1]
    cells = raw[4:]
    out: list[str] = []
    for row in range(rows):
        for column in range(columns):
            offset = (row * columns + column) * 2
            if offset + 1 >= len(cells):
                break
            char, attr = cells[offset], cells[offset + 1]
            # The VGA attribute byte: low nibble foreground, high nibble
            # background, with the top bit meaning bright background on a
            # console that is not blinking.
            out.append(f"\x1b[0;{30 + (attr & 7)};{40 + ((attr >> 4) & 7)}m")
            if attr & 0x08:
                out.append("\x1b[1m")
            out.append(chr(char) if 32 <= char < 127 else " ")
        out.append("\x1b[0m\r\n")
    return "".join(out).encode("utf-8", "replace")


def _controlling_tty() -> str | None:
    try:
        return os.ttyname(0)
    except OSError:
        return None
