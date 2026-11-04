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

from navkit.bidi import display_width, pad_cells
from navkit import glyphs as glyphs_module
from navkit.i18n import tr
from navkit.events import KeyEvent
from navkit.reactive import computed, reactive
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


#: How far Ctrl+Left and Ctrl+Right scroll the *Mount point* column.
BIG_STEP = 20


class VolumeList(ListViewer):
    """Mounted volumes: name, type, mount point, used (or free) share, free space and size."""

    #: The share column shows the free share instead of the used one.
    show_free: bool = reactive(False)
    #: How many columns of each mount point are held back at its end: what
    #: Left scrolls the *Mount point* column by, Right taking it back.  A
    #: departure, asked for: the column showed the end alone (``_cut_start``),
    #: and still opens so, its scroll bar's thumb on the right.
    back: int = reactive(0)

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

    # -- the Mount point column sideways (a departure, asked for) ---------------

    @computed
    def mount_x(self) -> int:
        return self.columns()[2][0]

    @computed
    def mount_width(self) -> int:
        return self.columns()[2][1]

    @computed
    def mount_room(self) -> int:
        """How many columns of a mount point show: its column less a blank each side."""
        return max(1, self.mount_width - 2)

    @computed
    def mount_span(self) -> int:
        """The widest mount point on screen: the bottom bar's range."""
        rows = self.items[self.scroll:self.scroll + max(1, self.rows)]
        return max((display_width(self.cells(item)[2][0]) for item in rows), default=0)

    @computed
    def mount_reach(self) -> int:
        """How far the column scrolls: the widest mount point less what shows."""
        return max(0, self.mount_span - self.mount_room)

    @computed
    def overflows_across(self) -> bool:
        """Whether a mount point on screen is cut, or the column is scrolled."""
        return self.back > 0 or self.mount_span > self.mount_room

    def scroll_mount(self, columns: int) -> None:
        """The column *columns* further right -- towards the mount points'
        ends, where it opens -- or left, negative, towards their starts."""
        self.back = max(0, min(self.back - columns, max(self.mount_reach, self.back)))

    async def on_key(self, event: KeyEvent) -> bool:
        """Left and Right scroll the *Mount point* column, Ctrl by ``BIG_STEP``."""
        steps = {"left": -1, "right": 1, "ctrl+left": -BIG_STEP, "ctrl+right": BIG_STEP}
        if not self.inert and event.name in steps:
            self.scroll_mount(steps[event.name])
            return True
        return await super().on_key(event)

    def cells(self, item: Any) -> list[tuple[str, bool]]:
        """*item*'s text in each column, and whether it is right-aligned.
        One ``gio`` knows but nothing has mounted has no mount point, nor sizes."""
        if not getattr(item, "mounted", True):
            return [(item.name, False), (item.fs_type, False), (tr("(not mounted)"), False),
                    ("", True), ("", True), ("", True)]
        return [
            (item.name, False), (item.fs_type, False), (item.mount, False),
            (_percent(item.free, item.total, self.show_free), True), (_size(item.free), True), (_size(item.total), True),
        ]

    def row_text(self, index: int, item: Any) -> str:
        return item.mount

    def row_tooltip(self, index: int, item: Any) -> str:
        """What the row leaves out: the whole mount point and device, how it
        is mounted, and the sizes in exact bytes."""
        lines = []
        if item.mount:
            lines.append(tr("Mounted on {mount}").format(mount=item.mount))
        if item.device:
            lines.append(tr("Device {device}").format(device=item.device))
        if item.options:
            lines.append(tr("Options {options}").format(options=item.options))
        if item.total is not None and item.free is not None:
            lines.append(tr("{free} bytes free of {total}").format(free=f"{item.free:,}", total=f"{item.total:,}"))
        return "\n".join(lines)

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
            surface.draw_text(x + (shown - display_width(title)) // 2, top, title, heading, shown)
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
                if self.back:
                    text = text[:max(0, len(text) - self.back)]
                text = self._cut_start(text, room)
            else:
                text = fit_text(text, room, self.ellipsis)
            if flush_right:
                text = pad_cells(text, room, "right")
            surface.draw_text(x + 1, y, text, style, room)

    async def choose(self) -> bool:
        if self.selected is None:
            return False
        await self.emit(ChosenEvent(self.selected))
        return True
