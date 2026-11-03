"""The list inside Utilities > Process list: a row per process, under column titles.

A :class:`~navml.widgets.dialog.list_viewer.ListViewer` over
:class:`navigator.lib.system.processes.Row` items, laid out as Disk > Volumes'
list is: the titles centred in the band under the top edge, a ``│`` between
columns from the titles down to the last row, the cursor bar across them.
*PID*, *User*, *S* (the state letter), *CPU %* and *Memory* keep their
widths; *Command* takes what is left.  In a tree the command is drawn under
its parent's with the box characters ``ps -H``'s forest has.

**A click on a column's title sorts by it** -- a departure, as the whole
window is: nothing else in Navigator sorts from its header.  The list does
not sort; it says which column was clicked (:class:`SortChosen`) and the
window, which keeps the order, does it.  The sorted column's title carries
▲ or ▼ (``^``/``v`` on an ASCII terminal), the scroll bar's arrows.

**Ctrl+S, or typing, searches** as a tree does (``navml.quick_search``): what
has been typed is the start of a process's name, its command or its number,
and the cursor goes to the first such row from where it is.  Ctrl+S again
finds the next; Esc, or any key the search has no use for, ends it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit import glyphs as glyphs_module
from navkit.bidi import display_width, pad_cells
from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import effect, peek, reactive
from navkit.screen import Surface
from navkit.style import Style
from navml.quick_search import name_pattern
from navml.widgets.dialog.commands import QuickSearch
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tree_view import ChosenEvent

from navigator.lib.system import processes
from navigator.widgets.manager.panel.panel import fit_text, human_size

#: The fixed columns' widths; the command has the rest.
PID_WIDTH = 9
USER_WIDTH = 12
STATE_WIDTH = 3
CPU_WIDTH = 7
MEMORY_WIDTH = 8

#: Each column's sort key, in the columns' order.
COLUMN_SORTS = ("pid", "user", "state", "cpu", "memory", "command")

#: The state letters a row is coloured by, as a class on its ``row`` part.
_STATE_CLASSES = {"Z": "zombie", "T": "stopped", "t": "stopped", "R": "running", "D": "waiting"}


@dataclass(frozen=True, slots=True)
class SortChosen(Event):
    """A click on a column's title: sort by *by*.  Reaches the window's ``on_sort_chosen``."""

    by: str = "pid"


class ProcessList(ListViewer):
    """Processes: number, owner, state, CPU share, resident memory and command."""

    #: Each row is drawn under its parent's.
    tree: bool = reactive(False)
    #: The sort in force and its way round, for the title's mark.
    sort: str = reactive("pid")
    descending: bool = reactive(False)
    #: The user whose rows are ``.mine``.
    uid: int = reactive(-1)
    #: What has been typed of the quick search, or None while it is off.
    search: str | None = reactive(None)

    emits = (ChosenEvent, SortChosen)
    keys = {"ctrl+s": QuickSearch}

    parts = ListViewer.parts + ("heading",)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.header = 1

    def mounted(self) -> None:
        super().mounted()
        effect(self, ProcessList._end_search_unfocused)

    @property
    def ellipsis(self) -> str:
        return glyphs_module.ellipsis(self.glyphs)

    @property
    def divider_glyph(self) -> str:
        """``│`` between columns, single whatever the frame, as a panel's."""
        return glyphs_module.charset("single", self.glyphs)[5]

    def columns(self) -> list[tuple[int, int]]:
        """``(x, width)`` of each column, a divider's cell between two."""
        fixed = (PID_WIDTH, USER_WIDTH, STATE_WIDTH, CPU_WIDTH, MEMORY_WIDTH, None)
        rest = max(0, self.inner_width - sum(width for width in fixed if width) - (len(fixed) - 1))
        spans: list[tuple[int, int]] = []
        x = self.inset
        for width in fixed:
            width = rest if width is None else width
            spans.append((x, width))
            x += width + 1
        return spans

    def column_at(self, x: int) -> int | None:
        """Which column *x* is in, a divider's cell counted to the column it closes."""
        for index, (left, width) in enumerate(self.columns()):
            if left <= x <= left + width:
                return index
        return None

    def titles(self) -> tuple[str, ...]:
        return (tr("PID"), tr("User"), tr("S"), tr("CPU %"), tr("Memory"), tr("Command"))

    def cells(self, row: processes.Row) -> list[tuple[str, bool]]:
        """*row*'s text in each column, and whether it is right-aligned."""
        process = row.process
        return [
            (str(process.pid), True), (process.user, False), (process.state, False),
            (f"{process.cpu:.1f}", True), (human_size(process.rss), True),
            (self.branch(row) + process.command, False),
        ]

    def branch(self, row: processes.Row) -> str:
        """The box characters before a command in the tree: ``│ `` for each
        level above with more to come, then ``├─`` or ``└─``."""
        if not self.tree or row.depth == 0:
            return ""
        box = glyphs_module.charset("single", self.glyphs)
        join = glyphs_module.joins("single", self.glyphs)[0]
        rails = "".join((box[5] if more else " ") + " " for more in row.rails)
        return rails + (box[2] if row.last else join) + box[4]

    def row_text(self, index: int, item: Any) -> str:
        return item.process.command

    def row_tooltip(self, index: int, item: Any) -> str:
        """The whole command, and the state in words."""
        process = item.process
        words = processes.state_words(process.state)
        state = f"{process.state} ({words})" if words else process.state
        return "\n".join((process.command, tr("State {state}, {threads} threads").format(
            state=state, threads=process.threads)))

    def row_style(self, index: int, item: Any) -> Style:
        process = item.process
        classes = []
        if process.uid == self.uid:
            classes.append("mine")
        elif process.uid == 0:
            classes.append("root")
        if process.kernel_thread:
            classes.append("kernel")
        state = _STATE_CLASSES.get(process.state)
        if state:
            classes.append(state)
        return self.part_style("row", classes=tuple(classes), selected=self.row_selected(index))

    def render_header(self, surface: Surface) -> None:
        """The column titles, the sorted one marked, and the dividers from
        them down to the last row -- drawn before the rows, so the cursor bar
        covers a divider it crosses, as a panel's does."""
        arrows = glyphs_module.scrollbar("dos", self.glyphs)
        mark = arrows[1] if self.descending else arrows[0]
        top = self.inset
        bottom = top + self.header + self.rows
        right = self.inset + self.inner_width
        heading, divider = self.part_style("heading"), self.part_style("divider")
        spans = self.columns()
        for index, (title, (x, width)) in enumerate(zip(self.titles(), spans)):
            shown = min(width, right - x)
            if shown <= 0:
                break
            if COLUMN_SORTS[index] == self.sort:
                title = f"{title}{mark}"
            title = fit_text(title, shown, self.ellipsis)
            surface.draw_text(x + (shown - display_width(title)) // 2, top, title, heading, shown)
            edge = x + width
            if index < len(spans) - 1 and edge < right:
                for y in range(top, bottom):
                    surface.draw_text(edge, y, self.divider_glyph, divider, 1)

    def render_row(self, surface: Surface, y: int, index: int, item: Any) -> None:
        style = self.row_style(index, item)
        right = self.inset + self.inner_width
        for (text, flush_right), (x, width) in zip(self.cells(item), self.columns()):
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

    # -- the header ---------------------------------------------------------------------

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A press on a column's title sorts by that column; anywhere else, as a list."""
        if (not self.inert and event.button == "left" and event.action == "press"
                and self.inset <= event.y < self.inset + self.header):
            column = self.column_at(event.x)
            if column is not None:
                await self.emit(SortChosen(COLUMN_SORTS[column]))
                return True
        return await super().on_mouse_click(event)

    # -- the quick search -----------------------------------------------------------------

    @property
    def edits_text(self) -> bool:
        """True while searching, so a command line's Enter, Home, End and Tab
        step aside and reach the search, which ends on them."""
        return self.search is not None

    def _end_search_unfocused(self) -> None:
        if not self.focus_within and peek(self, ProcessList.search) is not None:
            self.search = None

    def find(self, text: str, start: int) -> int | None:
        """The first row from *start* on, wrapping, whose process's name,
        command, or command's program, *text* begins -- or whose number it does."""
        pattern = name_pattern(text)
        rows = self.items
        for step in range(len(rows)):
            index = (start + step) % len(rows)
            process = rows[index].process
            program = process.command.split(" ", 1)[0].rsplit("/", 1)[-1]
            if any(pattern.match(each) for each in (process.name, program, process.command, str(process.pid))):
                return index
        return None

    async def on_quick_search(self, event: QuickSearch) -> bool:
        """Ctrl+S starts the search, and while one is on finds the next match."""
        if self.search is None:
            self.search = ""
        elif self.search:
            found = self.find(self.search, self.cursor + 1)
            if found is not None:
                self.cursor = found
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert:
            return False
        if self.search is not None:
            if event.is_printable and event.char:
                text = self.search + event.char
                found = self.find(text, self.cursor)
                if found is not None:
                    self.cursor = found
                    self.search = text
                return True
            if event.matches("backspace"):
                self.search = self.search[:-1]
                return True
            self.search = None
            if event.matches("escape"):
                return True
        elif event.is_printable and event.char and not (event.alt or event.ctrl) and event.char != " ":
            self.search = ""
            return await self.on_key(event)
        return await super().on_key(event)
