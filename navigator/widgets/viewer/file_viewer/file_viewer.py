"""F3's view: DOS Navigator's ``TFileViewer``, painting what ``navigator.viewer`` reads.

**Written in Python alone**, because everything it shows is painted -- rows of
a file, in one of three modes -- and it declares nothing a document would place.
The window around it, ``FileWindow``, is the one with a markup half.

**Its state is a handful of numbers.**  ``top`` is the byte offset of the first
row shown, ``x_delta`` how far the text is scrolled sideways, ``cursor`` the
byte the hex cursor is on; ``mode``, ``wrap`` and ``filter`` are the three
switches the key bar flips.  Every one is reactive, so a key handler assigns
one and the frame follows -- nothing here paints on demand.  The rows are not
state: they are read from the source on every render, which costs one
``line()`` per visible row and is what lets ``top`` be a plain offset.

The keys are ``FVIEWER.PAS``'s ``HandleEvent``, and they differ between text and
the two hex modes the way they did there: in text the arrows move the *view*,
in hex they move a *cursor* and the view follows it.
"""

from __future__ import annotations

import bisect
import threading
from pathlib import Path
from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navkit.widget import Widget
from navml.background import Background, Outcome

from navigator import highlight
from navigator.settings import SETTINGS
from navigator.viewer import (
    DUMP_CHARS_AT,
    FILTER_TAGS,
    HEX_PAIRS_AT,
    ViewSource,
    byte_table,
    ENCODINGS,
    dump_row,
    dump_row_bytes,
    group_digits,
    hex_chars_at,
    hex_row,
    hex_row_bytes,
)

#: The three modes F4 cycles through, in DN's order.
MODES = ("text", "hex", "dump")

#: How many rows one wheel notch moves.
WHEEL_ROWS = 3

#: How far Ctrl+Left and Ctrl+Right move text sideways.
BIG_STEP = 20

#: The thread syntax highlighting lexes on.
_LEXER = Background("nav-view-lex", workers=1)

#: How far before the top the lexing starts, and how far past it it goes:
#: a file this size or less is lexed whole, from its start, and coloured
#: exactly; further into a bigger one, a comment or string opened more than
#: ``LEX_BACK`` above the window is not known to be open.
LEX_BACK = 256 * 1024
LEX_AHEAD = 256 * 1024

#: How much of the file's start is read for its ``#!`` line.
HEAD = 256


def _lex_window(name: str, data: bytes | None, low: int, high: int, size: int,
                codec: str, stop: threading.Event) -> Any:
    """On the thread: the spans of the whole lines in ``[low, high)`` of the
    file, as ``(start, end, spans)``, False when it has no lexer, None when
    stopped.  *data* is the whole file when the viewer holds it (``/proc``),
    else it is read here."""
    if data is None:
        with open(name, "rb") as stream:
            head = stream.read(HEAD)
            stream.seek(low)
            window = stream.read(high - low)
    else:
        head, window = data[:HEAD], data[low:high]
    first = head.split(b"\n", 1)[0].decode("utf-8", errors="replace")
    lexer = highlight.lexer_for(name, first)
    if lexer is None:
        return False
    start, end = low, low + len(window)
    if low > 0:
        # From the first whole line: a lexer starts in its root state.
        cut = window.find(b"\n")
        if cut >= 0:
            window, start = window[cut + 1:], low + cut + 1
    if end < size:
        cut = window.rfind(b"\n")
        if cut >= 0:
            window, end = window[:cut + 1], start + cut + 1
    spans = highlight.lex_bytes(lexer, window, start, codec, stop)
    return None if spans is None else (start, end, spans)


class FileViewer(Widget):
    """The inside of a viewer window: a file's rows, and the keys that move them."""

    #: A search hit, drawn in *Selected text* [118]; a syntax token
    #: (:mod:`navigator.highlight`), by its classes.
    parts = ("selected", "token")

    #: The file, once :meth:`open` has read it.  Reactive so that the window's
    #: title can follow it; assigned only by :meth:`open`.
    path: Path | None = reactive(None)

    #: How many bytes the file had when it was opened.
    size: int = reactive(0)

    mode: str = reactive("text")
    wrap: bool = reactive(False)
    filter: int = reactive(0)
    #: File > Encoding: the code page the bytes are read in, one of
    #: ``viewer.ENCODINGS``'s; ``utf-8`` is DN's viewer with no ``XLT`` loaded.
    encoding: str = reactive("utf-8")

    #: The offset of the first row shown.
    top: int = reactive(0)

    #: Columns the text is scrolled to the left, in text mode.
    x_delta: int = reactive(0)

    #: The byte the hex cursor is on, in hex mode.
    cursor: int = reactive(0)

    #: The last search's hit, as ``(offset, length)``, drawn until the next.
    hit: tuple[int, int] | None = reactive(None)

    #: Text coloured by syntax, as ``highlight.ini`` says: a departure, DN's
    #: viewer had none.  Seeded from the setting, switched by View.
    syntax_highlight: bool = reactive(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source: ViewSource | None = None
        self.syntax_highlight = SETTINGS.viewer.syntax_highlight
        self.rehighlight()
        # In __init__, not the class body: a plain class attribute would
        # shadow the reactive descriptor, as `Console` learned.
        self.can_focus = True

    def open(self, path: Path | str, *, source: ViewSource | None = None) -> None:
        """Show *path* from its start.  Raises ``OSError`` if it cannot be read.

        Given the *source*, opened already on a thread, nothing is read here.
        """
        if source is None:
            source = ViewSource(path)
        if self.source is not None:
            self.source.close()
        self.source = source
        source.table = byte_table(self.encoding)
        self.rehighlight()
        self.path = source.path
        self.size = source.size
        self.top = self.x_delta = self.cursor = 0
        self.hit = None

    def close_file(self) -> None:
        """Show nothing: what a quick view shows for a directory."""
        if self.source is not None:
            self.source.close()
        self.source = None
        self.rehighlight()
        self.path = None
        self.size = 0
        self.top = self.x_delta = self.cursor = 0
        self.hit = None

    def unmounting(self) -> None:
        # Let the file go with the window.  A read reopens it, so a viewer
        # that is put back somewhere still works.
        super().unmounting()
        if self.source is not None:
            self.source.close()

    # -- geometry of the modes -------------------------------------------------

    @property
    def wrap_width(self) -> int | None:
        """The width rows are wrapped at, or ``None`` when they are not."""
        return max(1, self.width) if self.wrap and self.mode == "text" else None

    def row_bytes(self) -> int:
        """How many bytes one hex or dump row shows."""
        if self.mode == "dump":
            return dump_row_bytes(self.width)
        return hex_row_bytes(self.width)

    def _text_rows(self, count: int, max_cols: int | None = None):
        """The first *count* text rows from ``top``, fewer at the end of the file."""
        rows, offset = [], self.top
        source = self.source
        if source is None:
            return rows
        for _ in range(count):
            row = source.line(offset, self.wrap_width, filter=self.filter,
                              max_cols=max_cols)
            if row is None:
                break
            rows.append(row)
            offset = row.next
        return rows

    def _last_top(self) -> int:
        """The furthest ``top`` may go: the last row on the last screen row."""
        if self.source is None:
            return 0
        if self.mode == "text":
            return self.source.last_page_top(self.height, self.wrap_width)
        per = self.row_bytes()
        if self.size == 0:
            return 0
        # Keep the phase ``top`` has, so Ctrl+Left's shift survives the end.
        phase = self.top % per
        last_row = self.size - 1 - (self.size - 1 - phase) % per
        return max(min(phase, self.top), last_row - (max(1, self.height) - 1) * per)

    # -- the info line ----------------------------------------------------------

    @computed
    def info_text(self) -> str:
        """DN's ``TViewInfo``: ``[<=>][42% of 12,345 Bytes]{ASCII}``.

        In hex mode the percentage gives way to the cursor's offset and a
        ruler of the row's columns, as ``TViewInfo.Draw`` wrote it.
        """
        if self.mode == "hex":
            per = self.row_bytes()
            phase = self.top % per
            ruler = "─".join(f"{(i + phase) % 256:02X}" for i in range(per))
            text = f"[{self.cursor & 0xFFFFFFFF:08X} {ruler}"
        else:
            text = "[>=<][" if self.wrap else "[<=>]["
            text += tr("{percent}% of {size} Bytes").format(percent=self.percent(), size=group_digits(self.size))
        tag = "" if self.encoding == "utf-8" else "{" + dict(ENCODINGS)[self.encoding].split()[0] + "}"
        return text + "]" + FILTER_TAGS[self.filter] + tag

    def percent(self) -> int:
        """How far into the file the view is: 100 once the end is showing."""
        if self.size == 0 or self._end_showing():
            return 100
        return self.top * 100 // self.size

    def _end_showing(self) -> bool:
        if self.mode == "text":
            rows = self._text_rows(self.height, max_cols=1)
            return len(rows) < self.height or (bool(rows) and rows[-1].next >= self.size)
        return self.top + self.height * self.row_bytes() >= self.size

    # -- moving ----------------------------------------------------------------

    def seek(self, offset: int) -> None:
        """Show the row holding *offset* at the top, as far as the end allows.

        What the scroll bar and a goto both call: DN's ``Seek`` followed by
        the ``CountUp`` that snaps it to a line start.
        """
        if self.source is None:
            return
        offset = max(0, min(offset, self.size))
        if self.mode == "text":
            self.top = min(self.source.line_start(offset, self.wrap_width), self._last_top())
            return
        per = self.row_bytes()
        self.top = max(0, offset - (offset - self.top) % per)
        self.top = min(self.top, max(0, self._last_top()))
        self._keep_cursor()

    def scroll_rows(self, count: int) -> None:
        """Move the view *count* rows, down for positive; the ends stop it."""
        if self.source is None:
            return
        if self.mode != "text":
            per = self.row_bytes()
            top = self.top + count * per
            if top < 0:
                top = self.top % per
            self.top = max(0, min(top, self._last_top()))
            self._keep_cursor()
            return
        width = self.wrap_width
        top = self.top
        if count < 0:
            for _ in range(-count):
                if top <= 0:
                    break
                top = self.source.prev_line_start(top, width)
        else:
            last = self._last_top()
            for _ in range(count):
                if top >= last:
                    break
                row = self.source.line(top, width, max_cols=1)
                if row is None:
                    break
                top = row.next
        self.top = top

    def to_start(self) -> None:
        self.top = self.x_delta = 0
        self.cursor = 0

    def to_end(self) -> None:
        """DN's ``SeekEOF``: the last screenful."""
        if self.mode == "text":
            self.top = self._last_top()
        else:
            self.top = self._last_top()
            self.cursor = max(0, self.size - 1)

    def _keep_cursor(self) -> None:
        """Pull the hex cursor back into the rows that show."""
        if self.size == 0:
            self.cursor = 0
            return
        last = min(self.size - 1, self.top + self.height * self.row_bytes() - 1)
        self.cursor = min(max(self.cursor, self.top), max(self.top, last))

    def move_cursor(self, delta: int) -> None:
        """Move the hex cursor *delta* bytes, and the view after it."""
        if self.size == 0:
            return
        cursor = min(max(self.cursor + delta, 0), self.size - 1)
        self.cursor = cursor
        self.follow_cursor()

    def follow_cursor(self) -> None:
        """Scroll whole rows until the hex cursor is on screen."""
        per = self.row_bytes()
        rows = max(1, self.height)
        top = self.top
        if self.cursor < top:
            top -= -(-(top - self.cursor) // per) * per
        elif self.cursor >= top + rows * per:
            top += ((self.cursor - top) // per - rows + 1) * per
        self.top = max(0, top)

    def cycle_mode(self) -> None:
        """F4: text, hex, dump."""
        self.set_mode(MODES[(MODES.index(self.mode) + 1) % len(MODES)])

    def set_mode(self, mode: str) -> None:
        """Show the file in *mode*.  The offset shown on top stays on top."""
        if mode not in MODES:
            raise ValueError(f"{mode!r} is not a viewer mode; they are {', '.join(MODES)}")
        if mode == self.mode:
            return
        offset = self.top
        self.mode = mode
        if mode == "hex":
            # DN's cursor starts where the view does.
            self.cursor = offset
        elif mode == "text":
            self.x_delta = 0
            self.seek(offset)

    def toggle_wrap(self) -> None:
        """F2.  The row on top stays on top, cut where the new width cuts it."""
        self.wrap = not self.wrap
        self.x_delta = 0
        if self.source is not None and self.mode == "text":
            self.top = self.source.line_start(self.top, self.wrap_width)

    def cycle_filter(self) -> None:
        """F6: no filter, ``{ASCII}``, ``{Printable}``."""
        self.set_filter((self.filter + 1) % len(FILTER_TAGS))

    def set_encoding(self, codec: str) -> None:
        """Read the file in *codec* from now on: ``SetXlatFile``.  The row at
        the top stays the row at the top, found again in the new widths."""
        if codec not in dict(ENCODINGS):
            raise ValueError(f"{codec} is not one of the viewer's encodings")
        self.encoding = codec
        if self.source is not None:
            self.source.table = byte_table(codec)
            if self.mode == "text":
                self.top = min(self.source.line_start(self.top, self.wrap_width), self._last_top())
        self.invalidate()

    def set_filter(self, filter: int) -> None:
        if not 0 <= filter < len(FILTER_TAGS):
            raise ValueError(f"{filter} is not a viewer filter; there are {len(FILTER_TAGS)}")
        self.filter = filter

    def show_hit(self, offset: int, length: int) -> None:
        """Put a search hit on screen and mark it.

        DN's ``ContinueSearch``: the hit's row goes to the top unless it is
        already showing, and sideways the text is scrolled to centre it when
        it is off the edge.
        """
        self.hit = (offset, length)
        if self.source is None:
            return
        if self.mode != "text":
            self.cursor = offset
            per = self.row_bytes()
            if not self.top <= offset < self.top + self.height * per:
                self.top = max(0, offset - (offset - self.top) % per)
            return
        rows = self._text_rows(self.height, max_cols=1)
        if not any(r.start <= offset < r.next for r in rows):
            self.top = self.source.line_start(offset, self.wrap_width)
        if self.wrap_width is None:
            row = self.source.line(self.source.line_start(offset), None,
                                   filter=self.filter)
            column = next((i for i, (_, at) in enumerate(row.cells) if at >= offset), 0) if row else 0
            if not self.x_delta <= column < self.x_delta + self.width:
                self.x_delta = max(0, column - self.width // 2)

    # -- keys ------------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if self.source is None:
            return False
        name = event.name
        rows = max(1, self.height - 1)
        if name in ("ctrl+pageup",):
            self.to_start()
        elif name in ("ctrl+pagedown",):
            self.to_end()
        elif self.mode == "text":
            return self._text_key(name, rows)
        else:
            return self._hex_key(name, rows)
        return True

    def _text_key(self, name: str, rows: int) -> bool:
        if name == "up":
            self.scroll_rows(-1)
        elif name == "down":
            self.scroll_rows(1)
        elif name == "pageup":
            self.scroll_rows(-rows)
        elif name == "pagedown":
            self.scroll_rows(rows)
        elif name == "ctrl+home":
            self.to_start()
        elif name == "ctrl+end":
            self.to_end()
        elif self.wrap and name in ("left", "right", "ctrl+left", "ctrl+right", "home", "end"):
            # Nothing is off the side of a wrapped row.
            pass
        elif name == "left":
            self.x_delta = max(0, self.x_delta - 1)
        elif name == "right":
            self.x_delta += 1
        elif name == "ctrl+left":
            self.x_delta = max(0, self.x_delta - BIG_STEP)
        elif name == "ctrl+right":
            self.x_delta += BIG_STEP
        elif name == "home":
            self.x_delta = 0
        elif name == "end":
            # CM_END: far enough to show the end of the longest row showing.
            longest = max((len(r.cells) for r in self._text_rows(self.height)), default=0)
            self.x_delta = max(0, longest - self.width)
        else:
            return False
        return True

    def _hex_key(self, name: str, rows: int) -> bool:
        per = self.row_bytes()
        if name == "up":
            if self.cursor >= per:
                self.move_cursor(-per)
        elif name == "down":
            if self.cursor + per < self.size:
                self.move_cursor(per)
        elif name == "pageup":
            self.scroll_rows(-rows)
            if self.cursor >= rows * per:
                self.move_cursor(-rows * per)
            self._keep_cursor()
        elif name == "pagedown":
            self.scroll_rows(rows)
            self.move_cursor(rows * per)
            self._keep_cursor()
        elif name == "left":
            self.move_cursor(-1)
        elif name == "right":
            self.move_cursor(1)
        elif name == "ctrl+left":
            # Shift the rows' start by a byte, as DN's did.
            if self.top > 0:
                self.top -= 1
            self._keep_cursor()
        elif name == "ctrl+right":
            if self.top + 1 < self.size:
                self.top += 1
            self._keep_cursor()
        elif name == "home":
            self.cursor = self.cursor - (self.cursor - self.top) % per
        elif name == "end":
            self.cursor = min(self.size - 1, self.cursor - (self.cursor - self.top) % per + per - 1)
        elif name == "ctrl+home":
            self.cursor = self.top + (self.cursor - self.top) % per
        elif name == "ctrl+end":
            column = (self.cursor - self.top) % per
            last_row = self.top + (max(1, self.height) - 1) * per
            while last_row + column >= self.size and last_row > self.top:
                last_row -= per
            self.cursor = min(self.size - 1, last_row + column)
        else:
            return False
        return True

    # -- the mouse -------------------------------------------------------------

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if self.source is None:
            return False
        if event.is_wheel:
            if event.button in ("wheel_up", "wheel_down"):
                step = -WHEEL_ROWS if event.button == "wheel_up" else WHEEL_ROWS
                self.scroll_rows(step)
                return True
            return False
        if event.action != "press" or event.button != "left":
            return False
        self.focus()
        # DN's viewer had no row to point at: the outer quarters are Left and
        # Right, and the rest is Up above the middle and Down below it.
        if event.x < self.width // 4:
            key = "left"
        elif event.x >= self.width - self.width // 4:
            key = "right"
        else:
            key = "up" if event.y < self.height // 2 else "down"
        await self.on_key(KeyEvent(key))
        return True

    # -- syntax highlight --------------------------------------------------------

    def rehighlight(self) -> None:
        """Forget the tokens: another file, another encoding, or ``highlight.ini`` saved."""
        stop = getattr(self, "_lex_stop", None)
        if stop is not None:
            stop.set()
        #: What the tokens were lexed for -- path, encoding, size -- and the
        #: bytes they cover, ``[start, end)``; the spans, and their starts for
        #: ``bisect``.
        self._lexed_for: Any = None
        self._covered = (0, 0)
        self._spans: list[highlight.Span] = []
        self._starts: list[int] = []
        #: The stop flag of the lexing in flight, else None.
        self._lex_stop: threading.Event | None = None
        #: The window last asked for: never asked twice, or a line longer
        #: than the window would have it lexed over and over.
        self._asked: tuple[int, int] | None = None
        #: No lexer for this file: plain text, until something changes.
        self._plain = False
        app = self.application
        if app is not None and app.is_running:
            self.invalidate()

    def _tokens(self, top: int, bottom: int) -> list[highlight.Span] | None:
        """The spans to paint ``[top, bottom)`` with, or None for plain text;
        a window around *top* is asked for when they do not cover it."""
        source = self.source
        if not self.syntax_highlight or source is None or self.size == 0:
            return None
        key = (str(source.path), self.encoding, self.size)
        if key != self._lexed_for:
            self.rehighlight()
            self._lexed_for = key
        if self._plain:
            return None
        start, end = self._covered
        if (top < start or (bottom > end and end < self.size)) and self._lex_stop is None:
            low, high = max(0, top - LEX_BACK), min(self.size, top + LEX_AHEAD)
            if (low, high) == self._asked:
                return self._spans
            self._asked = (low, high)
            stop = threading.Event()
            self._lex_stop = stop
            _LEXER.run(self, _lex_window, key[0], source._data, low, high, self.size,
                       self.encoding, stop, done=lambda outcome: self._lexed(outcome, stop))
        return self._spans

    def _lexed(self, outcome: Outcome, stop: threading.Event) -> None:
        if stop is not self._lex_stop:
            return  # forgotten by rehighlight meanwhile
        self._lex_stop = None
        try:
            answer = outcome.result()
        except Exception:
            # Unreadable now, or a lexer that fails on this text: plain.
            answer = False
        if answer is None:
            return
        if answer is False:
            self._plain, self._spans, self._starts = True, [], []
        else:
            start, end, spans = answer
            self._covered, self._spans = (start, end), spans
            self._starts = [span[0] for span in spans]
        app = self.application
        if app is not None and app.is_running:
            # Not when answered on the spot, from inside ``render``.
            self.invalidate()

    # -- painting --------------------------------------------------------------

    def cursor_position(self) -> tuple[int, int] | None:
        """The hardware cursor on the hex pair under ``cursor``, as DN put it."""
        if self.mode != "hex" or self.size == 0:
            return None
        per = self.row_bytes()
        index = self.cursor - self.top
        if not 0 <= index < self.height * per:
            return None
        return HEX_PAIRS_AT + (index % per) * 3, index // per

    def render(self, surface: Surface) -> None:
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        if self.source is None:
            return
        if self.mode == "text":
            self._render_text(surface)
        else:
            self._render_hex(surface)

    def _hit_covers(self, offset: int) -> bool:
        hit = self.hit
        return hit is not None and hit[0] <= offset < hit[0] + hit[1]

    def _render_text(self, surface: Surface) -> None:
        style, selected = self.style, self.part_style("selected")
        x_delta = 0 if self.wrap else self.x_delta
        limit = x_delta + self.width
        rows = self._text_rows(self.height, max_cols=limit)
        spans = self._tokens(self.top, rows[-1].next) if rows else None
        starts = self._starts if spans else None
        looks: dict[tuple[str, ...], Any] = {}
        for y, row in enumerate(rows):
            cells = row.cells
            token = 0
            if starts:
                token = max(0, bisect.bisect_right(starts, cells[min(x_delta, len(cells) - 1)][1]) - 1) if cells else 0
            for x in range(self.width):
                column = x + x_delta
                if column >= len(cells):
                    break
                char, at = cells[column]
                if self._hit_covers(at):
                    look = selected
                else:
                    look = style
                    if spans:
                        # The cells' offsets only grow along a row: one pointer will do.
                        while token < len(spans) and spans[token][1] <= at:
                            token += 1
                        if token < len(spans) and spans[token][0] <= at:
                            classes = spans[token][2]
                            look = looks.get(classes)
                            if look is None:
                                look = looks[classes] = self.part_style("token", classes=classes)
                if char == "":
                    if x == 0:
                        surface.set_cell(x, y, " ", look)
                    continue
                if x == self.width - 1 and column + 1 < len(cells) and cells[column + 1][0] == "":
                    # Half a wide character would spill past the edge.
                    surface.set_cell(x, y, " ", look)
                    continue
                surface.set_cell(x, y, char, look)

    def _render_hex(self, surface: Surface) -> None:
        style, selected = self.style, self.part_style("selected")
        per = self.row_bytes()
        source = self.source
        hex_mode = self.mode == "hex"
        for y in range(self.height):
            address = self.top + y * per
            if address >= self.size:
                break
            data = source.read(address, per)
            if hex_mode:
                surface.draw_text(0, y, hex_row(data, address, per, self.filter, self.source.table), style)
            else:
                surface.draw_text(0, y, dump_row(data, address, self.filter, self.source.table), style)
            if self.hit is None:
                continue
            chars_at = hex_chars_at(per) if hex_mode else DUMP_CHARS_AT
            for index, byte in enumerate(data):
                if not self._hit_covers(address + index):
                    continue
                if hex_mode:
                    surface.draw_text(HEX_PAIRS_AT + index * 3, y, f"{byte:02X}", selected)
                    char = hex_row(data[index:index + 1], 0, 1, self.filter, self.source.table)[-1]
                else:
                    char = dump_row(data[index:index + 1], 0, self.filter, self.source.table)[-1]
                surface.set_cell(chars_at + index, y, char, selected)
