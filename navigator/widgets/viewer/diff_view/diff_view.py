"""The inside of a *Compare files* window: two files side by side.

**A departure**: DOS Navigator had no such view (:mod:`navigator.lib.file_ops.filediff`
says what it took instead).  Written in Python alone, as ``FileViewer`` is,
because everything in it is painted.

**One widget paints both sides**, so that they cannot scroll apart: ``top``
is the row on top of both, ``x_delta`` how far both are scrolled sideways.
The paths head the two columns, a ``│`` between them, and every row begins
with a mark column -- ``-`` on the left for a line removed or changed, ``+``
on the right for one added or changed -- so a difference reads without
colour too.  A line one side lacks faces a filler row there.

The keys that move are this widget's own, in ``on_key``, as the viewer's are
(``FileViewer._text_key``); the ones that jump between differences are the
window's, in its key table.
"""

from __future__ import annotations

from typing import Any

from navkit import glyphs as glyphs_module
from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
from navkit.i18n import tr
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navkit.widget import Widget

from navigator.lib.file_ops.filediff import DELETE, EQUAL, INSERT, REPLACE
from navigator.lib.viewer import decode_cells

#: How far Ctrl+Left and Ctrl+Right scroll sideways, as the viewer's.
BIG_STEP = 20
#: Rows a turn of the wheel scrolls.
WHEEL_ROWS = 3
#: Rows kept above a difference brought into view, so it is seen in context.
CONTEXT = 2

#: How a row's kind reads on each side: the class its line is styled by.
_LEFT_CLASS = {REPLACE: "changed", DELETE: "removed"}
_RIGHT_CLASS = {REPLACE: "changed", INSERT: "added"}


class DiffView(Widget):
    """Two texts' aligned rows (a :class:`~navigator.lib.file_ops.filediff.TextDiff`),
    and the keys that scroll them."""

    #: The paths over the columns, a line by what it is (``added``,
    #: ``removed``, ``changed``), the ``-``/``+`` marks (``current`` in the
    #: difference last gone to), a filler row, and the ``│`` between.
    parts = ("heading", "line", "mark", "filler", "divider")

    #: The comparison shown; set by the window.
    model: Any = reactive(None)
    left_title: str = reactive("")
    right_title: str = reactive("")
    #: The row on top of both columns.
    top: int = reactive(0)
    #: Columns both sides are scrolled to the left.
    x_delta: int = reactive(0)
    #: The difference last gone to (an index into ``model.hunks``), -1 for none.
    current: int = reactive(-1)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.can_focus = True

    # -- the model -----------------------------------------------------------

    @computed
    def total(self) -> int:
        """How many rows there are."""
        return 0 if self.model is None else self.model.rows

    @computed
    def page(self) -> int:
        """How many rows are on show: all but the headings."""
        return max(1, self.height - 1)

    @computed
    def last_top(self) -> int:
        """The furthest ``top`` goes: the last row at the bottom."""
        return max(0, self.total - self.page)

    @computed
    def info_text(self) -> str:
        """The bottom frame's: which difference, of how many, and what they come to."""
        model = self.model
        if model is None:
            return ""
        count = len(model.hunks)
        if not count:
            return " " + tr("No differences") + " "
        totals = f"+{model.added} -{model.removed} ~{model.changed}"
        if self.current < 0:
            where = tr("{count} differences").format(count=count)
        else:
            where = tr("Difference {number} of {count}").format(number=self.current + 1, count=count)
        return f" {where}  {totals} "

    def scroll_to(self, top: int) -> None:
        """Put row *top* on top, as near as the rows allow."""
        self.top = min(max(0, top), self.last_top)

    def scroll_rows(self, count: int) -> None:
        self.scroll_to(self.top + count)

    def go_to(self, index: int) -> None:
        """Difference *index* brought into view, a few rows below the top."""
        model = self.model
        if model is None or not 0 <= index < len(model.hunks):
            return
        self.current = index
        self.scroll_to(model.hunks[index] - CONTEXT)

    def _anchor(self) -> int | None:
        """The row the next and previous differences are counted from: the
        current one's while it is on show, else none (counted from the view)."""
        model = self.model
        if model is not None and 0 <= self.current < len(model.hunks):
            row = model.hunks[self.current]
            if self.top <= row < self.top + self.page:
                return row
        return None

    def next_difference(self) -> bool:
        """To the difference after the current one -- or after the top of the
        view, when the current one is out of it.  False when there is none."""
        model = self.model
        if model is None:
            return False
        anchor = self._anchor()
        index = model.next_hunk(self.top - 1 if anchor is None else anchor)
        if index is None:
            return False
        self.go_to(index)
        return True

    def previous_difference(self) -> bool:
        model = self.model
        if model is None:
            return False
        anchor = self._anchor()
        index = model.previous_hunk(self.top if anchor is None else anchor)
        if index is None:
            return False
        self.go_to(index)
        return True

    def _longest(self) -> int:
        """The longest line on show, in bytes: as far as End scrolls."""
        model, longest = self.model, 0
        if model is None:
            return 0
        for row in range(self.top, min(self.total, self.top + self.page)):
            for side in ("left", "right"):
                line = model.line(side, row)
                if line is not None:
                    longest = max(longest, len(line.expandtabs()))
        return longest

    # -- keys ------------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if self.model is None:
            return False
        name = event.name
        moves = {"up": -1, "down": 1, "pageup": -self.page, "pagedown": self.page}
        if name in moves:
            self.scroll_rows(moves[name])
        elif name in ("ctrl+home", "ctrl+pageup"):
            self.scroll_to(0)
        elif name in ("ctrl+end", "ctrl+pagedown"):
            self.scroll_to(self.last_top)
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
            room = max(1, (self.width - 1) // 2 - 1)
            self.x_delta = max(0, self._longest() - room)
        else:
            return False
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if event.is_wheel:
            if event.button in ("wheel_up", "wheel_down"):
                self.scroll_rows(-WHEEL_ROWS if event.button == "wheel_up" else WHEEL_ROWS)
                return True
            return False
        if event.action == "press" and event.button == "left":
            self.focus()
            return True
        return False

    # -- painting ----------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        if self.width < 3 or self.height < 1:
            return
        left_width = (self.width - 1) // 2
        right_x = left_width + 1
        right_width = self.width - right_x
        divider = self.part_style("divider")
        bar = glyphs_module.charset("single", self.glyphs)[5]
        for y in range(self.height):
            surface.set_cell(left_width, y, bar, divider)
        heading = self.part_style("heading")
        for x, width, title in ((0, left_width, self.left_title), (right_x, right_width, self.right_title)):
            surface.fill(x, 0, width, 1, " ", heading)
            surface.draw_text(x + 1, 0, self._cut_start(title, width - 1), heading, max(0, width - 1))
        model = self.model
        if model is None:
            return
        looks: dict[tuple[str, str], Any] = {}

        def look(part: str, kind: str) -> Any:
            found = looks.get((part, kind))
            if found is None:
                found = looks[(part, kind)] = self.part_style(part, classes=(kind,) if kind else ())
            return found

        filler_char = "░" if self.glyphs >= GLYPHS_UNICODE else "."
        current = (model.hunks[self.current], model.hunk_end(self.current)) \
            if 0 <= self.current < len(model.hunks) else (0, 0)
        for y in range(1, self.height):
            row = self.top + y - 1
            if row >= model.rows:
                break
            kind = model.kinds[row]
            in_current = current[0] <= row < current[1]
            for side, x, width, classes, mark in (("left", 0, left_width, _LEFT_CLASS, "-"),
                                                   ("right", right_x, right_width, _RIGHT_CLASS, "+")):
                line = model.line(side, row)
                if line is None:
                    surface.fill(x, y, width, 1, filler_char, look("filler", ""))
                    continue
                klass = classes.get(kind, "") if kind != EQUAL else ""
                line_look = look("line", klass) if klass else style
                if klass:
                    surface.fill(x, y, width, 1, " ", line_look)
                    mark_look = look("mark", "current") if in_current else line_look
                    surface.set_cell(x, y, mark, mark_look)
                self._paint_line(surface, x + 1, y, width - 1, line, line_look)

    def _paint_line(self, surface: Surface, x: int, y: int, width: int, line: bytes, look: Any) -> None:
        """*line* from column ``x_delta``, in *width* cells from *x*."""
        if width <= 0:
            return
        cells: list[tuple[str, int]] = []
        decode_cells(line, 0, cells, max_cols=self.x_delta + width)
        for offset in range(width):
            column = offset + self.x_delta
            if column >= len(cells):
                break
            char = cells[column][0]
            if char == "":
                if offset == 0:
                    surface.set_cell(x, y, " ", look)
                continue
            if offset == width - 1 and column + 1 < len(cells) and cells[column + 1][0] == "":
                surface.set_cell(x + offset, y, " ", look)  # half a wide character
                continue
            surface.set_cell(x + offset, y, char, look)

    def _cut_start(self, text: str, room: int) -> str:
        """*text* in *room* cells, its start cut and marked if it must be:
        the end of a path is what tells two apart."""
        if room <= 0:
            return ""
        if len(text) <= room:
            return text
        marker = glyphs_module.ellipsis(self.glyphs)
        if room > len(marker):
            return marker + text[-(room - len(marker)):]
        return text[-room:]
