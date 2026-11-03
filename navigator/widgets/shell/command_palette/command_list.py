"""The palette's rows: a command's title, the letters typed lit in it, and its key.

A :class:`~navml.widgets.dialog.list_viewer.ListViewer` over
:class:`~navigator.widgets.shell.command_palette.command_palette.Found`
rows.  The title is one :meth:`~navkit.screen.Surface.draw_runs` call, so a
lit letter keeps its colour in a right-to-left caption; the key sits against
the right edge, and a command that cannot run here is greyed whole, as a
menu greys its item.
"""

from __future__ import annotations

from typing import Any

from navkit.bidi import display_width
from navkit.screen import Surface
from navml.widgets.dialog.list_viewer import ListViewer


class CommandList(ListViewer):
    """``Found`` rows: :attr:`Found.entry` and where the typed letters fell."""

    #: The typed letters in a title, and the key column.
    parts = ("match", "key")

    def row_selected(self, index: int) -> bool:
        """The cursor shows while the line above has the keyboard too: the
        list is moved from there, as a menu's bar is."""
        dialog = self.parent
        return index == self.cursor and (self.focused or (dialog is not None and dialog.focus_within))

    def row_text(self, index: int, item: Any) -> str:
        return item.entry.title

    def row_tooltip(self, index: int, item: Any) -> str:
        """The whole title while it is cut: rows are painted in their own colours."""
        return self.cut_text(index, item)

    async def choose(self) -> bool:
        """Enter or a double click: the palette's answer, if it can run."""
        dialog = self.parent
        return dialog is not None and dialog.take()

    def render_row(self, surface: Surface, y: int, index: int, item: Any) -> None:
        entry = item.entry
        selected = self.row_selected(index)
        classes = () if entry.enabled else ("disabled",)
        look = self.part_style("row", classes=classes, selected=selected)
        lit = look if not entry.enabled else self.part_style("match", selected=selected)
        width = self.inner_width
        key = entry.key
        key_width = min(display_width(key), max(0, width // 2))
        left = max(0, width - key_width - (1 if key_width else 0))
        title = entry.title
        places = set(item.places)
        runs: list[tuple[str, Any]] = []
        for at, char in enumerate(title):
            style = lit if at in places else look
            if runs and runs[-1][1] is style:
                runs[-1] = (runs[-1][0] + char, style)
            else:
                runs.append((char, style))
        # The row's whole width first, so the cursor bar runs under the gap.
        surface.draw_text(self.inset, y, " " * width, look, width)
        surface.draw_runs(self.inset, y, runs, left)
        if key_width:
            keys = look if not entry.enabled else self.part_style("key", selected=selected)
            surface.draw_text(self.inset + width - key_width, y, key, keys, key_width)
