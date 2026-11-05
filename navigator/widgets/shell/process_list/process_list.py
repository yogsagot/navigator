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

**Typing filters**: the list keeps no search of its own.  A character typed
on it (Space aside), or Backspace, goes to the window's *Filter* line
(:attr:`ProcessList.filter_line`), and the keyboard with it, as htop's F4
takes it; Esc on the list empties a filter that holds something.  Ctrl+S is
left to the window, which gives the keyboard to the line.  ``ProcessFilter``
is that line: Enter, Down, Up, PgDn and PgUp hand the keyboard back to the
list, and Esc empties it -- an empty one lets Esc close the window.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit import glyphs as glyphs_module
from navkit.bidi import display_width, pad_cells
from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navkit.style import Style
from navml.widgets.dialog.commands import QuickSearch
from navml.widgets.dialog.input_line import InputLine
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


#: How far Ctrl+Left and Ctrl+Right scroll the *Command* column, as the viewer's.
BIG_STEP = 20


class ColumnList(ListViewer):
    """A row per item under column titles, as Process list's and Services'
    lists are: the fixed columns of :attr:`WIDTHS` and one flexible one
    (``None``) taking what is left, a ``│`` between, the sorted column's
    title marked, a press on a title emitting :class:`SortChosen` with its
    :attr:`SORTS` key, and typing given to :attr:`filter_line`.  A subclass
    says :meth:`titles` and :meth:`cells`."""

    #: Each column's width, ``None`` for the one that takes the rest.
    WIDTHS: tuple[int | None, ...] = ()
    #: Each column's sort key, in the columns' order.
    SORTS: tuple[str, ...] = ()

    #: The sort in force and its way round, for the title's mark.
    sort: str = reactive("")
    descending: bool = reactive(False)

    emits = (ChosenEvent, SortChosen)

    parts = ListViewer.parts + ("heading",)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.header = 1
        #: The window's *Filter* line, which typing on the list goes to.
        self.filter_line: InputLine | None = None

    @property
    def ellipsis(self) -> str:
        return glyphs_module.ellipsis(self.glyphs)

    @property
    def divider_glyph(self) -> str:
        """``│`` between columns, single whatever the frame, as a panel's."""
        return glyphs_module.charset("single", self.glyphs)[5]

    def columns(self) -> list[tuple[int, int]]:
        """``(x, width)`` of each column, a divider's cell between two."""
        fixed = self.WIDTHS
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
        raise NotImplementedError

    def cells(self, row: Any) -> list[tuple[str, bool]]:
        """*row*'s text in each column, and whether it is right-aligned."""
        raise NotImplementedError

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
            if self.SORTS[index] == self.sort:
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
                await self.emit(SortChosen(self.SORTS[column]))
                return True
        return await super().on_mouse_click(event)

    # -- typing goes to the filter -----------------------------------------------------

    def list_key(self, event: KeyEvent) -> bool:
        """A key of the subclass's own, after the filter's and before the
        list's movement: True when it was taken."""
        return False

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert:
            return False
        line = self.filter_line
        if line is not None:
            typed = event.is_printable and event.char and not (event.alt or event.ctrl) and event.char != " "
            if typed or (event.matches("backspace") and line.value):
                line.focus()
                line.anchor = None
                line.cursor = len(line.value)
                return await line.on_key(event)
            if event.matches("escape") and line.value:
                line.value = ""
                line.cursor = 0
                return True
        if self.list_key(event):
            return True
        return await super().on_key(event)


class ProcessList(ColumnList):
    """Processes: number, owner, state, CPU share, resident memory and command."""

    WIDTHS = (PID_WIDTH, USER_WIDTH, STATE_WIDTH, CPU_WIDTH, MEMORY_WIDTH, None)
    SORTS = COLUMN_SORTS

    #: Each row is drawn under its parent's.
    tree: bool = reactive(False)
    #: The sort in force and its way round, for the title's mark.
    sort: str = reactive("pid")
    descending: bool = reactive(False)
    #: The user whose rows are ``.mine``.
    uid: int = reactive(-1)
    #: Columns the *Command* column is scrolled to the left, by Left and
    #: Right: a departure, asked for, as the viewer's sideways scroll -- FAR's
    #: process panel cut a command where its column ended.
    x_delta: int = reactive(0)

    keys = {"ctrl+s": QuickSearch}

    def titles(self) -> tuple[str, ...]:
        return (tr("PID"), tr("User"), tr("S"), tr("CPU %"), tr("Memory"), tr("Command"))

    def cells(self, row: processes.Row) -> list[tuple[str, bool]]:
        """*row*'s text in each column, and whether it is right-aligned; the
        command scrolled ``x_delta`` columns to the left."""
        process = row.process
        return [
            (str(process.pid), True), (process.user, False), (process.state, False),
            (f"{process.cpu:.1f}", True), (human_size(process.rss), True),
            (self.command_text(row)[self.x_delta:], False),
        ]

    def command_text(self, row: processes.Row) -> str:
        """*row*'s *Command* cell whole: its branch in the tree, then the command."""
        return self.branch(row) + row.process.command

    # -- the Command column sideways (a departure, asked for) ------------------

    @computed
    def command_x(self) -> int:
        """Where the *Command* column starts, in the list's columns."""
        return self.columns()[-1][0]

    @computed
    def command_room(self) -> int:
        """How many columns of a command show: its column less a blank each side."""
        return max(1, self.columns()[-1][1] - 2)

    @computed
    def command_span(self) -> int:
        """The widest command on screen, in columns: the bottom bar's range."""
        items, start = self.items, self.scroll
        rows = items[start:start + max(1, self.rows)]
        return max((display_width(self.command_text(row)) for row in rows), default=0)

    @computed
    def overflows_across(self) -> bool:
        """Whether a command on screen is cut, or the column is scrolled: the bottom bar."""
        return self.x_delta > 0 or self.command_span > self.command_room

    def scroll_command(self, columns: int) -> None:
        """The *Command* column *columns* further right (left, negative), no
        further than the widest command on screen ends."""
        furthest = max(0, self.command_span - self.command_room, self.x_delta if columns < 0 else 0)
        self.x_delta = max(0, min(self.x_delta + columns, furthest))

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
        if item.context:
            classes.append("context")
        state = _STATE_CLASSES.get(process.state)
        if state:
            classes.append(state)
        return self.part_style("row", classes=tuple(classes), selected=self.row_selected(index))

    def list_key(self, event: KeyEvent) -> bool:
        """Left and Right scroll the *Command* column, Ctrl by ``BIG_STEP``."""
        steps = {"left": -1, "right": 1, "ctrl+left": -BIG_STEP, "ctrl+right": BIG_STEP}
        if event.name in steps:
            self.scroll_command(steps[event.name])
            return True
        return False


class ProcessFilter(InputLine):
    """The window's *Filter* line: what is typed narrows the list
    (:func:`navigator.lib.system.processes.matches`).  Enter and the list's
    movement keys give the keyboard back to :attr:`rows`, the movement made
    there; Esc empties the line, and an empty line leaves Esc to the window."""

    #: A command line's Enter, Home, End and Tab step aside for it.
    edits_text = True

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.rows: ColumnList | None = None

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert:
            return False
        rows = self.rows
        if event.matches("escape") and self.value:
            self.value = ""
            self.cursor = 0
            return True
        if rows is not None and event.matches("enter", "down", "up", "pagedown", "pageup"):
            rows.focus()
            if not event.matches("enter"):
                await rows.on_key(event)
            return True
        return await super().on_key(event)
