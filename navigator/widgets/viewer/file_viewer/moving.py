"""The modes' geometry, and moving through the file: seeking, scrolling, the hex cursor, the
mode, wrap, filter and encoding switches.

A mixin of :class:`FileViewer` (``navkit.widget.Mixin``): methods only; its state,
keys and the file are in ``file_viewer.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from navigator.lib.viewer import FILTER_TAGS, byte_table, ENCODINGS, dump_row_bytes, hex_row_bytes
from navigator.widgets.viewer.file_viewer.helpers import MODES, _when_here

if TYPE_CHECKING:
    from navigator.widgets.viewer.file_viewer.file_viewer import FileViewer as _Base
else:
    from navkit.widget import Mixin as _Base


class Moving(_Base):
    """The modes' geometry, and moving through the file: seeking, scrolling, the hex cursor, the"""

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

    # -- moving ----------------------------------------------------------------

    @_when_here
    def seek(self, offset: int) -> None:
        """Show the row holding *offset* at the top, as far as the end allows.

        What the scroll bar and a goto both call: DN's ``Seek`` followed by
        the ``CountUp`` that snaps it to a line start.
        """
        if self.source is None:
            return
        offset = max(0, min(offset, self.size))
        if offset < self.top:
            self.follow = False
        if self.rendering:
            self._render_go(self.render_layout.row_for(offset))
            return
        if self.mode == "text":
            self.top = min(self.source.line_start(offset, self.wrap_width), self._last_top())
            return
        per = self.row_bytes()
        self.top = max(0, offset - (offset - self.top) % per)
        self.top = min(self.top, max(0, self._last_top()))
        self._keep_cursor()

    @_when_here
    def scroll_rows(self, count: int) -> None:
        """Move the view *count* rows, down for positive; the ends stop it."""
        if self.source is None:
            return
        if count < 0:
            # Scrolled back up: *Follow end* lets go, as ``less``'s F does.
            self.follow = False
        if self.rendering:
            self._render_go(self.render_row + count)
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
        self.follow = False
        self.top = self.x_delta = self.render_row = 0
        self.cursor = 0

    @_when_here
    def to_end(self) -> None:
        """DN's ``SeekEOF``: the last screenful."""
        if self.rendering:
            self._render_go(self._render_last_row())
        elif self.mode == "text":
            self.top = self._last_top()
        else:
            self.top = self._last_top()
            self.cursor = self.top if self.mode == "dump" else max(0, self.size - 1)

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
        if delta < 0:
            self.follow = False
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
            # DN's cursor starts where the view does, in the pairs.
            self.cursor = offset
            self.nibble, self.in_chars = 0, False
        elif mode == "text":
            self.x_delta = 0
            self.seek(offset)

    def toggle_wrap(self) -> None:
        """F2.  The row on top stays on top, cut where the new width cuts it."""
        self.wrap = not self.wrap
        self.x_delta = 0
        self._snap_top()

    @_when_here
    def _snap_top(self, clamp: bool = False) -> None:
        """``top`` back on the start of the row holding it, in the widths in
        force -- and, *clamp*, no further than the last screenful."""
        if self.source is not None and self.mode == "text":
            top = self.source.line_start(self.top, self.wrap_width)
            self.top = min(top, self._last_top()) if clamp else top

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
            self._snap_top(clamp=True)
        self.invalidate()

    def set_filter(self, filter: int) -> None:
        if not 0 <= filter < len(FILTER_TAGS):
            raise ValueError(f"{filter} is not a viewer filter; there are {len(FILTER_TAGS)}")
        self.filter = filter
