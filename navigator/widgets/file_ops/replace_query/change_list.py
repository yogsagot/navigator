"""The lines a replacement changes, each as it is over what it will be."""

from __future__ import annotations

from typing import Any

from navkit.screen import Surface
from navml.widgets.dialog.list_viewer import ListViewer

from navigator.lib.file_ops.filereplace import Change


def rows_of(changes: tuple[Change, ...]) -> list[tuple[str, str, str]]:
    """The list's rows for *changes*: ``(number, kind, text)``, *kind*
    ``"removed"`` or ``"added"``, the number on a change's first row only."""
    rows: list[tuple[str, str, str]] = []
    for change in changes:
        for offset, text in enumerate(change.old):
            rows.append((str(change.line + offset), "removed", text))
        for text in change.new:
            rows.append(("", "added", text))
    return rows


class ChangeList(ListViewer):
    """A :class:`ListViewer` of :func:`rows_of`'s rows: the line number,
    ``-`` or ``+``, the line -- coloured through ``::line.removed`` and
    ``::line.added``, as File > Compare files colours its own."""

    parts = ("line",)

    def row_text(self, index: int, item: Any) -> str:
        number, kind, text = item
        return f"{number:>6} {'-' if kind == 'removed' else '+'} {text}"

    def row_tooltip(self, index: int, item: Any) -> str:
        """The whole line while it is cut: rows are painted in their own colours."""
        return self.cut_text(index, item)

    def render_row(self, surface: Surface, y: int, index: int, item: Any) -> None:
        look = self.part_style("line", classes=(item[1],), selected=self.row_selected(index))
        surface.draw_text(self.inset, y, self.row_text(index, item), look, self.inner_width)
