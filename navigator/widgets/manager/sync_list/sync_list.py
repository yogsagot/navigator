"""The list inside the *Synchronize* window: a row per path that differs.

A :class:`~navml.widgets.dialog.list_viewer.ListViewer` over
:class:`navigator.lib.file_ops.dirsync.SyncRow` items, laid out as Disk >
Volumes' list is (``VolumeList``): titles in the band under the top edge, a
``│`` between columns, the cursor bar across them.  The columns:

- the **status**: ``>`` on the left alone, ``<`` on the right alone, ``≠``
  on both and different, ``=`` the same, ``!`` a conflict;
- the **action**: ``→`` copied right, ``←`` copied left, ``✕`` deleted,
  blank left alone (``->``, ``<-`` and ``x`` in ASCII).  The arrows are the
  Arrows block's, not ``◄──``: many fonts set the geometric triangles lower
  than the box-drawing line beside them;
- the **path** below the two directories, a directory's ending in ``/``, cut
  at its start when it must be;
- each side's **size** and **date**, the time of day left to the footer,
  which gives both sides' in full -- or says why a conflict is one.

A row is styled by its status (``SyncList::row.only``, ``.differs``,
``.same``, ``.conflict``).
"""

from __future__ import annotations

from typing import Any

from navkit import glyphs as glyphs_module
from navkit.glyphs import GLYPHS_UNICODE
from navkit.i18n import tr
from navkit.screen import Surface
from navkit.style import Style
from navml.widgets.dialog.list_viewer import ListViewer

from navigator.lib.config.country import date_text, stamp
from navigator.lib.file_ops import dirsync
from navigator.widgets.manager.panel.panel import fit_text, human_size

#: The fixed columns' widths; the path has the rest.
STATUS_WIDTH = 3
SIZE_WIDTH = 8
DATE_WIDTH = 12

_STATUS_MARK = {
    dirsync.LEFT_ONLY: ">", dirsync.RIGHT_ONLY: "<", dirsync.DIFFERS: "≠", dirsync.SAME: "=",
    dirsync.CONFLICT: "!",
}
_STATUS_CLASS = {
    dirsync.LEFT_ONLY: "only", dirsync.RIGHT_ONLY: "only", dirsync.DIFFERS: "differs", dirsync.SAME: "same",
    dirsync.CONFLICT: "conflict",
}
#: Each action's mark, in Unicode and in ASCII.
_ACTION_MARK = {
    dirsync.COPY_RIGHT: ("\u2192", "->"), dirsync.COPY_LEFT: ("\u2190", "<-"),
    dirsync.DELETE: ("✕", "x"), dirsync.SKIP: ("", ""),
}


class SyncList(ListViewer):
    """What differs between two trees, a row a path, with what is to be done with each."""

    parts = ListViewer.parts + ("heading",)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.header = 1

    @property
    def ellipsis(self) -> str:
        return glyphs_module.ellipsis(self.glyphs)

    @property
    def divider_glyph(self) -> str:
        return glyphs_module.charset("single", self.glyphs)[5]

    def columns(self) -> list[tuple[int, int]]:
        """``(x, width)`` of each column, a divider's cell between two."""
        fixed = (STATUS_WIDTH, self.action_width, None, SIZE_WIDTH, DATE_WIDTH, SIZE_WIDTH, DATE_WIDTH)
        rest = max(0, self.inner_width - sum(width for width in fixed if width) - (len(fixed) - 1))
        spans: list[tuple[int, int]] = []
        x = self.inset
        for width in fixed:
            width = rest if width is None else width
            spans.append((x, width))
            x += width + 1
        return spans

    @property
    def action_width(self) -> int:
        """The action column: as wide as its widest mark in this glyph tier, a blank each side."""
        return max(len(self._action_mark(action)) for action in _ACTION_MARK) + 2

    def _status_mark(self, status: str) -> str:
        mark = _STATUS_MARK[status]
        return "#" if mark == "≠" and self.glyphs < GLYPHS_UNICODE else mark

    def _action_mark(self, action: str) -> str:
        unicode, ascii = _ACTION_MARK[action]
        return unicode if self.glyphs >= GLYPHS_UNICODE else ascii

    @staticmethod
    def _side(side: dirsync.Side | None) -> tuple[str, str]:
        if side is None:
            return "", ""
        size = tr("DIR") if side.kind == "dir" else human_size(side.size)
        return size, date_text(side.mtime) if side.mtime else ""

    def cells(self, item: dirsync.SyncRow) -> list[tuple[str, bool]]:
        """*item*'s text in each column, and whether it is right-aligned."""
        path = str(item.path) + ("/" if item.is_dir else "")
        left_size, left_date = self._side(item.left)
        right_size, right_date = self._side(item.right)
        return [
            (self._status_mark(item.status), False), (self._action_mark(item.action), False), (path, False),
            (left_size, True), (left_date, False), (right_size, True), (right_date, False),
        ]

    def row_text(self, index: int, item: Any) -> str:
        return str(item.path)

    def row_style(self, index: int, item: Any) -> Style:
        return self.part_style("row", classes=(_STATUS_CLASS[item.status],),
                               selected=self.row_selected(index))

    def footer_text(self) -> str:
        """Why the row under the cursor is a conflict, or when each side was changed."""
        item = self.selected
        if item is None:
            return ""
        if item.error:
            return f" {item.error} "
        times = [stamp(side.mtime) if side is not None and side.mtime else "-" for side in (item.left, item.right)]
        return f" {times[0]}  |  {times[1]} "

    def _cut_start(self, text: str, room: int) -> str:
        if len(text) <= room:
            return text
        marker = self.ellipsis
        if room > len(marker):
            return marker + text[-(room - len(marker)):]
        return text[-room:] if room > 0 else ""

    def render_header(self, surface: Surface) -> None:
        """The column titles, and the dividers from them down to the last row."""
        titles = ("", "", tr("Path"), tr("Left"), "", tr("Right"), "")
        top = self.inset
        bottom = top + self.header + self.rows
        right = self.inset + self.inner_width
        heading, divider = self.part_style("heading"), self.part_style("divider")
        spans = self.columns()
        for index, (title, (x, width)) in enumerate(zip(titles, spans)):
            shown = min(width, right - x)
            if shown <= 0:
                break
            title = title[:shown]
            surface.draw_text(x + (shown - len(title)) // 2, top, title, heading, shown)
            edge = x + width
            if index < len(spans) - 1 and edge < right:
                for y in range(top, bottom):
                    surface.draw_text(edge, y, self.divider_glyph, divider, 1)

    def render_row(self, surface: Surface, y: int, index: int, item: Any) -> None:
        style = self.row_style(index, item)
        right = self.inset + self.inner_width
        for column, ((text, flush_right), (x, width)) in enumerate(zip(self.cells(item), self.columns())):
            room = min(width, right - x) - 2
            if room <= 0:
                continue
            text = self._cut_start(text, room) if column == 2 else fit_text(text, room, self.ellipsis)
            if flush_right:
                text = text.rjust(room)
            surface.draw_text(x + 1, y, text, style, room)
