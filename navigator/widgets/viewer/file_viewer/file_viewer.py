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

from pathlib import Path

from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navkit.widget import Widget

from navigator.viewer import (
    DUMP_CHARS_AT,
    FILTER_TAGS,
    HEX_PAIRS_AT,
    ViewSource,
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


class FileViewer(Widget):
    """The inside of a viewer window: a file's rows, and the keys that move them."""

    #: A search hit, drawn in *Selected text* [118].
    parts = ("selected",)

    #: The file, once :meth:`open` has read it.  Reactive so that the window's
    #: title can follow it; assigned only by :meth:`open`.
    path: Path | None = reactive(None)

    #: How many bytes the file had when it was opened.
    size: int = reactive(0)

    mode: str = reactive("text")
    wrap: bool = reactive(False)
    filter: int = reactive(0)

    #: The offset of the first row shown.
    top: int = reactive(0)

    #: Columns the text is scrolled to the left, in text mode.
    x_delta: int = reactive(0)

    #: The byte the hex cursor is on, in hex mode.
    cursor: int = reactive(0)

    #: The last search's hit, as ``(offset, length)``, drawn until the next.
    hit: tuple[int, int] | None = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source: ViewSource | None = None
        # In __init__, not the class body: a plain class attribute would
        # shadow the reactive descriptor, as `Console` learned.
        self.can_focus = True

    def open(self, path: Path | str) -> None:
        """Show *path* from its start.  Raises ``OSError`` if it cannot be read."""
        source = ViewSource(path)
        if self.source is not None:
            self.source.close()
        self.source = source
        self.path = source.path
        self.size = source.size
        self.top = self.x_delta = self.cursor = 0
        self.hit = None

    def close_file(self) -> None:
        """Show nothing: what a quick view shows for a directory."""
        if self.source is not None:
            self.source.close()
        self.source = None
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
            text += f"{self.percent()}% of {group_digits(self.size)} Bytes"
        return text + "]" + FILTER_TAGS[self.filter]

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
        """F4: text, hex, dump.  The offset shown on top stays on top."""
        mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]
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
        self.filter = (self.filter + 1) % len(FILTER_TAGS)

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
        for y, row in enumerate(self._text_rows(self.height, max_cols=limit)):
            cells = row.cells
            for x in range(self.width):
                column = x + x_delta
                if column >= len(cells):
                    break
                char, at = cells[column]
                look = selected if self._hit_covers(at) else style
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
                surface.draw_text(0, y, hex_row(data, address, per, self.filter), style)
            else:
                surface.draw_text(0, y, dump_row(data, address, self.filter), style)
            if self.hit is None:
                continue
            chars_at = hex_chars_at(per) if hex_mode else DUMP_CHARS_AT
            for index, byte in enumerate(data):
                if not self._hit_covers(address + index):
                    continue
                if hex_mode:
                    surface.draw_text(HEX_PAIRS_AT + index * 3, y, f"{byte:02X}", selected)
                    char = hex_row(data[index:index + 1], 0, 1, self.filter)[-1]
                else:
                    char = dump_row(data[index:index + 1], 0, self.filter)[-1]
                surface.set_cell(chars_at + index, y, char, selected)
