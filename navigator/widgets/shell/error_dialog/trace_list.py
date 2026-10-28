"""The error box's traceback: a list whose rows are syntax highlighted."""

from __future__ import annotations

from typing import Any

from navkit.screen import Surface
from navml.widgets.dialog.list_viewer import ListViewer

from navigator.lib.highlight import Span


class TraceList(ListViewer):
    """A :class:`ListViewer` painting :attr:`spans` through ``::token``.

    ``::token`` is the part the editor and the viewer colour code with, its
    classes the Pygments token type's pieces (``navigator.lib.highlight``);
    ``::token:selected`` is a token on the cursor's row.  :attr:`spans` is set
    with :attr:`items` and parallel to it: each row's ``(start, end,
    classes)``, in characters of its text.
    """

    parts = ("token",)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: Each row's spans; a row past its end is plain.  Plain, not
        #: reactive: it is only ever assigned together with ``items``, whose
        #: write is what asks for the frame.
        self.spans: list[list[Span]] = []

    def row_tooltip(self, index: int, item: Any) -> str:
        """The whole line while it is cut: the rows are ``row_text`` coloured."""
        return self.cut_text(index, item)

    def render_row(self, surface: Surface, y: int, index: int, item: Any) -> None:
        super().render_row(surface, y, index, item)
        if index >= len(self.spans):
            return
        text = self.row_text(index, item)
        selected = self.row_selected(index)
        width = self.inner_width
        for start, end, classes in self.spans[index]:
            if start >= width:
                break
            look = self.part_style("token", classes=classes, selected=selected)
            surface.draw_text(self.inset + start, y, text[start:end], look, min(end, width) - start)
