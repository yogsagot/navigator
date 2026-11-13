"""Follow end, and Filter lines: only the lines that match, shown in place of the file.

A mixin of :class:`FileViewer` (``navkit.widget.Mixin``): methods only; its state,
keys and the file are in ``file_viewer.py``.
"""

from __future__ import annotations

import bisect
from typing import TYPE_CHECKING, Any

from navkit.glyphs import GLYPHS_UNICODE
from navkit.i18n import tr
from navkit.screen import Surface

from navigator.lib.viewer import cp437
from navigator.widgets.viewer.file_viewer.helpers import BIG_STEP

# The surface is a stub with no module of its own, by design (navml.surface).
# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from navigator.widgets.viewer.file_viewer.file_viewer_surface import FileViewer as _Base
else:
    from navkit.widget import Mixin as _Base


class Lines(_Base):
    """Follow end, and Filter lines: only the lines that match, shown in place of the file."""

    # -- Follow end ------------------------------------------------------------

    def resized(self, result: str) -> None:
        """The source found to have grown or shrunk (``ViewSource.refresh``):
        the size taken again, and -- following -- the end shown.  A file cut
        shorter is shown from where it now ends, and a filter reads it anew."""
        source = self.source
        if source is None or result == "same":
            return
        self.size = source.size
        if result == "shrank":
            if self.cursor >= self.size:
                self.cursor = max(0, self.size - 1)
            if self.top > self.size:
                self.top = 0
            self.hit = None
        self.invalidate()
        if self.follow and not self.filtering:
            self.to_end()

    # -- Filter lines ----------------------------------------------------------

    @property
    def filtering(self) -> bool:
        """Whether the rows shown are *Filter lines*': text mode, a scan in."""
        return self.lines is not None and self.mode == "text"

    def show_lines(self, scan: Any) -> None:
        """*scan*'s lines shown instead of the file, the cursor on the line
        the view's top is in -- or on the last one, following."""
        self.lines = scan
        self.hit = None
        self.lines_revision += 1
        self.lines_row = self.lines_cursor = 0
        if self.follow:
            self._lines_to(len(scan.shown) - 1)
            return
        index = self._lines_index(self.top, after=True)
        self._lines_to(index if index is not None else 0)

    def lines_grew(self) -> None:
        """The scan read on (*Follow end*): painted again, the last line in view."""
        self.lines_revision += 1
        self.invalidate()
        if self.follow and self.lines is not None:
            self._lines_to(len(self.lines.shown) - 1)

    def leave_lines(self, *, to_line: bool = False) -> None:
        """Back to the whole file -- at the cursor's line with *to_line*
        (Enter), else where it was."""
        scan = self.lines
        if scan is None:
            return
        shown = scan.shown
        target = shown[self.lines_cursor].start if to_line and 0 <= self.lines_cursor < len(shown) else None
        self.lines = None
        self.lines_row = self.lines_cursor = 0
        if target is not None:
            self.follow = False
            self.seek(target)
        elif self.follow:
            self.to_end()

    def _lines_index(self, offset: int, *, after: bool = False) -> int | None:
        """The shown row whose line holds *offset*; *after*, else the first
        row past it (the last when none is)."""
        shown = self.lines.shown
        starts = [hit.start for hit in shown]
        index = bisect.bisect_right(starts, offset) - 1
        if index >= 0 and shown[index].start <= offset <= shown[index].end:
            return index
        if not after or not shown:
            return None
        return min(index + 1, len(shown) - 1)

    def _lines_last_row(self) -> int:
        return max(0, len(self.lines.shown) - max(1, self.height)) if self.lines is not None else 0

    def _lines_to(self, index: int) -> None:
        """The cursor on row *index*, and the rows scrolled to show it."""
        shown = self.lines.shown
        if not shown:
            self.lines_cursor = self.lines_row = 0
            return
        index = max(0, min(index, len(shown) - 1))
        if index < self.lines_cursor:
            self.follow = False
        self.lines_cursor = index
        rows = max(1, self.height)
        if index < self.lines_row:
            self.lines_row = index
        elif index >= self.lines_row + rows:
            self.lines_row = index - rows + 1
        self.lines_row = max(0, min(self.lines_row, self._lines_last_row()))
        # The scroll bar and the view history go by the line's offset.
        self.top = shown[index].start

    def _lines_key(self, name: str, rows: int) -> bool:
        """The filtered rows' keys: a cursor up and down them, Enter to the
        line in the whole file, Esc back to it where it was."""
        moves = {"up": -1, "down": 1, "pageup": -rows, "pagedown": rows}
        last = len(self.lines.shown) - 1
        if name in moves:
            self._lines_to(self.lines_cursor + moves[name])
        elif name in ("ctrl+home", "ctrl+pageup"):
            self._lines_to(0)
            self.x_delta = 0
        elif name in ("ctrl+end", "ctrl+pagedown"):
            self._lines_to(last)
        elif name == "enter":
            self.leave_lines(to_line=True)
        elif name == "escape":
            self.leave_lines()
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
            self._lines_to(last)
        else:
            return False
        return True

    def _paint_lines(self, surface: Surface) -> None:
        """*Filter lines*' rows: each line's number in a gutter, then its text
        scrolled by ``x_delta``, what matched in it marked."""
        self.lines_revision  # repainted as the scan grows
        scan = self.lines
        shown = scan.shown
        if not shown:
            self._say(surface, tr("No lines match"))
            return
        style = self.style
        number = self.part_style("lines", classes=("number",))
        cursor = self.part_style("lines", classes=("cursor",))
        match = self.part_style("lines", classes=("match",))
        digits = len(str(shown[-1].number))
        bar = "│" if self.glyphs >= GLYPHS_UNICODE else "|"
        for y in range(self.height):
            index = self.lines_row + y
            if index >= len(shown):
                break
            hit = shown[index]
            text = "".join(cp437(ord(char)) if ord(char) < 0x20 else char
                           for char in hit.text.expandtabs(8))
            runs = [(f"{hit.number:>{digits}}", cursor if index == self.lines_cursor else number),
                    (bar, number)]
            visible = text[self.x_delta:]
            cut = len(text) - len(visible)
            at = 0
            for start, end in scan.spans(text):
                start, end = max(0, start - cut), max(0, end - cut)
                if end <= at:
                    continue
                if start > at:
                    runs.append((visible[at:start], style))
                runs.append((visible[max(at, start):end], match))
                at = end
            if at < len(visible):
                runs.append((visible[at:], style))
            surface.draw_runs(0, y, [run for run in runs if run[0]], max_width=self.width)
