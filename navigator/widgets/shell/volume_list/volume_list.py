"""The list inside Disk > Volumes: a row per mounted volume, under column titles.

A :class:`~navml.widgets.dialog.list_viewer.ListViewer` over
:class:`navigator.lib.system.volumes.Volume` items, laid out as a detailed file panel is:
the titles centred in the band under the top edge, a ``│`` between columns
from the titles down to the last row, the cursor bar across them.  *Name*,
*Type*, *Use %* (or *Free %*), *Free* and *Size* keep their widths; *Mount point* takes what is left
and is cut at its start, so the end of the path -- the part that tells two
mounts apart -- stays in sight.  Sizes are ``sysinfo.size_text``'s, as System
Information gives a disk's.  The share column is ``df``'s *Use%* unless
:attr:`VolumeList.show_free` turns it into the free share.
"""

from __future__ import annotations

from typing import Any

from navkit import glyphs as glyphs_module
from navkit.i18n import tr
from navkit.reactive import reactive
from navkit.screen import Surface
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tree_view import ChosenEvent

from navigator.lib.system.sysinfo import size_text
from navigator.widgets.manager.panel.panel import fit_text

#: The fixed columns' widths; the mount point has the rest.
NAME_WIDTH = 14
TYPE_WIDTH = 12
SIZE_WIDTH = 9
PERCENT_WIDTH = 7


def _size(value: int | None) -> str:
    return size_text(value) if value is not None else "?"


def _percent(free: int | None, total: int | None, show_free: bool) -> str:
    """The used share of *total* (the free one if *show_free*), as a whole
    percentage; ``?`` when either is unknown."""
    if free is None or not total:
        return "?"
    share = free if show_free else total - free
    return f"{round(share * 100 / total)}%"


class VolumeList(ListViewer):
    """Mounted volumes: name, type, mount point, used (or free) share, free space and size."""

    #: The share column shows the free share instead of the used one.
    show_free: bool = reactive(False)

    #: Enter or a double click, carrying the volume as its ``node``: the
    #: tree's event, as Window > List's is, since a row was chosen and that is
    #: all ``ChosenEvent`` says.
    emits = (ChosenEvent,)

    parts = ListViewer.parts + ("heading",)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.header = 1

    @property
    def ellipsis(self) -> str:
        return glyphs_module.ellipsis(self.glyphs)

    @property
    def divider_glyph(self) -> str:
        """``│`` between columns, single whatever the frame, as a panel's."""
        return glyphs_module.charset("single", self.glyphs)[5]

    def columns(self) -> list[tuple[int, int]]:
        """``(x, width)`` of each column, a divider's cell between two."""
        fixed = (NAME_WIDTH, TYPE_WIDTH, None, PERCENT_WIDTH, SIZE_WIDTH, SIZE_WIDTH)
        rest = max(0, self.inner_width - sum(width for width in fixed if width) - (len(fixed) - 1))
        spans: list[tuple[int, int]] = []
        x = self.inset
        for width in fixed:
            width = rest if width is None else width
            spans.append((x, width))
            x += width + 1
        return spans

    def cells(self, item: Any) -> list[tuple[str, bool]]:
        """*item*'s text in each column, and whether it is right-aligned."""
        return [
            (item.name, False), (item.fs_type, False), (item.mount, False),
            (_percent(item.free, item.total, self.show_free), True), (_size(item.free), True), (_size(item.total), True),
        ]

    def row_text(self, index: int, item: Any) -> str:
        return item.mount

    def _cut_start(self, text: str, room: int) -> str:
        """*text* in *room* cells, its start cut and marked if it must be."""
        if len(text) <= room:
            return text
        marker = self.ellipsis
        if room > len(marker):
            return marker + text[-(room - len(marker)):]
        return text[-room:] if room > 0 else ""

    def render_header(self, surface: Surface) -> None:
        """The column titles, and the dividers from them down to the last row.

        Drawn before the rows, so the cursor bar covers a divider it crosses,
        as a panel's does.
        """
        share = tr("Free %") if self.show_free else tr("Use %")
        titles = (tr("Name"), tr("Type"), tr("Mount point"), share, tr("Free"), tr("Size"))
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
            # A blank on each side of the text, as a panel's columns have.
            room = min(width, right - x) - 2
            if room <= 0:
                continue
            if column == 2:
                text = self._cut_start(text, room)
            else:
                text = fit_text(text, room, self.ellipsis)
            if flush_right:
                text = text.rjust(room)
            surface.draw_text(x + 1, y, text, style, room)

    async def choose(self) -> bool:
        if self.selected is None:
            return False
        await self.emit(ChosenEvent(self.selected))
        return True
