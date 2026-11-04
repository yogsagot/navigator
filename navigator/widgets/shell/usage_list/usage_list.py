"""The list inside Disk > Directory sizes: what a directory holds, biggest first.

A :class:`~navml.widgets.dialog.list_viewer.ListViewer` over
:class:`navigator.lib.file_ops.dirusage.UsageNode` items, laid out as
:class:`~navigator.widgets.shell.volume_list.VolumeList` is: titles in the band
under the top edge, a ``│`` between columns, the cursor bar across them.
*Size* (or *Used*, the room on the disk), the share of the directory it is,
a bar against the biggest beside it, as ``ncdu`` draws one, how many entries
are under it, and the name, with the rest of the width.  Sizes are
``human_size``'s, as the panel's size column gives them.

A mark before the name says what ``ncdu``'s column of flags says: ``>``
another file system, not entered; ``!`` a directory that could not be read;
``H`` a hard link counted under another name; ``@`` a symbolic link.  A
directory's name ends in ``/``.  Below the scanned directory a ``..`` row
comes first, which goes up.
"""

from __future__ import annotations

from typing import Any

from navkit import glyphs as glyphs_module
from navkit.bidi import display_width, pad_cells
from navkit.i18n import tr
from navkit.events import KeyEvent
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tree_view import ChosenEvent

from navigator.lib.file_ops.dirusage import UsageNode
from navigator.widgets.manager.panel.panel import fit_text, human_size

#: The fixed columns' widths; the name has the rest.
SIZE_WIDTH = 9
SHARE_WIDTH = 8
BAR_WIDTH = 12
ITEMS_WIDTH = 9


class Up:
    """The ``..`` row: the directory above the one listed."""

    name = ".."


#: The one ``..`` row every list shares.
UP = Up()


def mark(node: UsageNode) -> str:
    """The flag shown before *node*'s name; a blank for none."""
    if node.other_fs:
        return ">"
    if node.unreadable:
        return "!"
    if node.hardlink:
        return "H"
    if node.is_link:
        return "@"
    return " "


#: How far Ctrl+Left and Ctrl+Right scroll the *Name* column.
BIG_STEP = 20


class UsageList(ListViewer):
    """A directory's entries with their sizes, shares, bars and counts."""

    #: The sizes shown are the bytes files say they hold, not the room on the disk.
    apparent: bool = reactive(False)

    #: What the listed directory adds up to, in the size shown: the 100% of
    #: the share column.  The window sets it with the items.
    whole: int = reactive(0)

    #: Columns the *Name* column is scrolled to the left: a departure, asked
    #: for, as the process list's *Command*.  Shift+Left/Right move it a
    #: column, Ctrl+Left/Right ``BIG_STEP`` -- Left and Right are ``ncdu``'s
    #: up and down the tree here (``UsageWindow.on_key``).
    x_delta: int = reactive(0)

    #: Enter or a double click, carrying the node (or :data:`UP`) as its ``node``.
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
        fixed = (SIZE_WIDTH, SHARE_WIDTH, BAR_WIDTH, ITEMS_WIDTH, None)
        rest = max(0, self.inner_width - sum(width for width in fixed if width) - (len(fixed) - 1))
        spans: list[tuple[int, int]] = []
        x = self.inset
        for width in fixed:
            width = rest if width is None else width
            spans.append((x, width))
            x += width + 1
        return spans

    def _largest(self) -> int:
        return max((item.amount(self.apparent) for item in self.items if isinstance(item, UsageNode)), default=0)

    def cells(self, item: Any, largest: int, room: int) -> list[tuple[str, bool]]:
        """*item*'s text in each column, and whether it is right-aligned;
        *largest* is the biggest beside it, *room* the bar's cells."""
        if not isinstance(item, UsageNode):
            return [("", True), ("", True), ("", False), ("", True), (self.name_text(item)[self.x_delta:], False)]
        amount = item.amount(self.apparent)
        share = f"{amount * 100 / self.whole:.1f}%" if self.whole > 0 else ""
        cells = round(amount * room / largest) if largest > 0 else 0
        bar = glyphs_module.gauge("dos", self.glyphs)[0] * cells
        items = f"{item.items:,}" if item.is_dir else ""
        return [(human_size(amount), True), (share, True), (bar, False), (items, True),
                (self.name_text(item)[self.x_delta:], False)]

    def row_text(self, index: int, item: Any) -> str:
        return item.name

    # -- the Name column sideways (a departure, asked for) -----------------------

    def name_text(self, item: Any) -> str:
        """*item*'s *Name* cell whole: its mark and name, a directory's ``/``."""
        if not isinstance(item, UsageNode):
            return "  .."
        return f"{mark(item)} {item.name}" + ("/" if item.is_dir else "")

    @computed
    def name_x(self) -> int:
        return self.columns()[-1][0]

    @computed
    def name_room(self) -> int:
        """How many columns of a name show: its column less a blank each side."""
        return max(1, self.columns()[-1][1] - 2)

    @computed
    def name_span(self) -> int:
        """The widest name on screen: the bottom bar's range."""
        rows = self.items[self.scroll:self.scroll + max(1, self.rows)]
        return max((display_width(self.name_text(item)) for item in rows), default=0)

    @computed
    def overflows_across(self) -> bool:
        """Whether a name on screen is cut, or the column is scrolled."""
        return self.x_delta > 0 or self.name_span > self.name_room

    def scroll_names(self, columns: int) -> None:
        """The *Name* column *columns* further right (left, negative), no
        further than the widest name on screen ends."""
        furthest = max(0, self.name_span - self.name_room, self.x_delta if columns < 0 else 0)
        self.x_delta = max(0, min(self.x_delta + columns, furthest))

    async def on_key(self, event: KeyEvent) -> bool:
        steps = {"shift+left": -1, "shift+right": 1, "ctrl+left": -BIG_STEP, "ctrl+right": BIG_STEP}
        if not self.inert and event.name in steps:
            self.scroll_names(steps[event.name])
            return True
        return await super().on_key(event)

    def row_tooltip(self, index: int, item: Any) -> str:
        """What the row leaves out: both sizes in exact bytes, and what its mark means."""
        if not isinstance(item, UsageNode):
            return ""
        lines = [item.name,
                 tr("{size} bytes, {used} bytes on the disk").format(size=f"{item.size:,}", used=f"{item.usage:,}")]
        if item.is_dir:
            lines.append(tr("{count} entries beneath it").format(count=f"{item.items:,}"))
        if item.other_fs:
            lines.append(tr("On another file system: not counted"))
        if item.unreadable:
            lines.append(tr("Could not be read"))
        if item.hardlink:
            lines.append(tr("A hard link already counted under another name"))
        if item.is_link:
            lines.append(tr("A symbolic link, counted as itself"))
        return "\n".join(lines)

    def render_header(self, surface: Surface) -> None:
        """The column titles, and the dividers from them down to the last row,
        drawn before the rows so the cursor bar covers a divider it crosses."""
        titles = (tr("Size") if self.apparent else tr("Used"), tr("Share"), "", tr("Entries"), tr("Name"))
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
        spans = self.columns()
        bar_room = max(0, min(spans[2][1], right - spans[2][0]) - 2)
        for (text, flush_right), (x, width) in zip(self.cells(item, self._largest(), bar_room), spans):
            # A blank on each side of the text, as a panel's columns have.
            room = min(width, right - x) - 2
            if room <= 0:
                continue
            text = fit_text(text, room, self.ellipsis)
            if flush_right:
                text = pad_cells(text, room, "right")
            surface.draw_text(x + 1, y, text, style, room)

    async def choose(self) -> bool:
        if self.selected is None:
            return False
        await self.emit(ChosenEvent(self.selected))
        return True
