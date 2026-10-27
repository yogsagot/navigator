"""Miller columns (Alt+F12, Manager > Miller columns): the file manager's other layout.

A departure, asked for: DOS Navigator had two panels and nothing else.  The
columns are Finder's: one per directory from the root down to the one being
browsed, each as wide as File Manager Setup's *Miller column width*
(``[file_manager] miller_width``), the leftmost scrolling off when they do
not fit, and after them a preview of what the cursor is on -- the directory's
listing, or the file through the Ctrl+Q quick view.

**Every column is a** :class:`~navigator.widgets.manager.panel.Panel`, so the
file manager's commands need nothing new: ``Manager.active_panel`` is the
column being browsed, the last of :attr:`MillerView.chain`, and F3, F4, F7,
F8, tagging, Ctrl+C/Ctrl+V, Alt+F6 and the rest act on it as on a panel.
Right and Enter on a directory step into it (:meth:`MillerView.step_in`),
Left and Backspace step back (:meth:`MillerView.step_out`).  Anything else
that moves the column -- a ``cd`` in the shell, a bookmark, Alt+T, Enter on
an archive -- moves the panel as it always did, and the chain is built again
around where it went (:meth:`MillerView._follow_moves`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit import glyphs as glyphs_module
from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import bind, computed, effect, reactive, untracked
from navkit.screen import Surface
from navkit.widget import Widget

from navigator.lib.drives import DriveGone, Location, drive_of
from navigator.settings import SETTINGS
from navigator.widgets.manager.panel import Panel
from navigator.widgets.manager.panel.panel import DirEntry
from navigator.widgets.viewer.quick_viewer import QuickViewer

#: The narrowest a column is made, whatever the setting says: a gutter, a few
#: letters of a name and the directory sign between two frame edges.
MIN_WIDTH = 12

#: How many directories up a chain is followed, against a drive whose
#: ``change_up`` never comes to an end.
MAX_DEPTH = 256

#: Columns kept clear at each end of the top edge, under the window's close
#: and zoom icons, as the panels' ``title_margin: 5``.
ICON_MARGIN = 5


def _up(location: Location) -> tuple[Location, str] | None:
    """Where ``..`` from *location* goes, and the name the cursor goes to there:
    ``Panel.go_up``'s answer, or None at the top."""
    if not location.is_root:
        return location.parent, location.name
    if location.is_local:
        return None
    try:
        return drive_of(location).change_up(location)
    except DriveGone:
        return None


def _absolute(location: Location) -> Location:
    if location.is_local and not location.local.is_absolute():
        return Location.of(Path(location.local).absolute())
    return location


class MillerColumn(Panel):
    """One column: a directory, listed by name alone.

    Simple mode drawn narrow -- the gutter, the name and ``▸`` after a
    directory -- with no footer, no option strip, no ``..`` (the column to
    the left is the parent) and no git letters, which would take a quarter of
    it.  Only the column being browsed adds its directory to Alt+Backspace's
    history and offers *As root*; the preview moves with every cursor step,
    and neither belongs to a step.
    """

    #: Whether the row under the cursor is drawn as the way to the column to
    #: the right, while another column has the keyboard (``Panel::row.trail``).
    trail: bool = reactive(False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.view_mode = "simple"
        self.options.visible = bind(lambda s: False)
        #: Where the view last put the column: a location other than this is
        #: one the column went to by itself.
        self.home: Location | None = None
        #: Whether the column is the one being browsed, the chain's last.
        self.current = False

    @property
    def view(self) -> MillerView | None:
        parent = self.parent
        return parent if isinstance(parent, MillerView) else None

    # -- what is listed --------------------------------------------------------

    def _apply(self, request: Any, entries: list[DirEntry], error: str | None,
               free: tuple[int, str] | None = None) -> None:
        super()._apply(request, [entry for entry in entries if entry.name != ".."], error, free)

    def _remember_directory(self, path: Location) -> None:
        """Not each column: :meth:`MillerView.step_in` remembers a step."""

    def _offer_root(self, path: Location) -> None:
        if self.current:
            super()._offer_root(path)

    def _read_git(self) -> None:
        self._git_generation += 1
        self.git = None

    def point_at(self, name: str | None) -> None:
        """The cursor on *name*, now if it is listed, else once the read lands."""
        if name is None:
            return
        index = next((i for i, item in enumerate(self.items) if item.name == name), None)
        if index is not None and not self.scanning:
            self.cursor = index
        else:
            self._return_to = name

    # -- navigating --------------------------------------------------------------

    def enter(self) -> None:
        entry = self.selected
        view = self.view
        if view is not None and self.found is None and entry is not None and entry.is_dir:
            view.step_in()
            return
        super().enter()

    def go_up(self) -> None:
        view = self.view
        if view is not None and self.found is None and view.step_out(self):
            return
        super().go_up()

    def toggle_hidden(self) -> None:
        """Ctrl+H: every column at once, so the chain lists alike."""
        view = self.view
        if view is None:
            super().toggle_hidden()
            return
        hidden = not self.show_hidden
        for column in view.columns():
            if column.show_hidden != hidden:
                Panel.toggle_hidden(column)

    def sort_by(self, mode: str, reverse: bool = False) -> None:
        """Alt+B and a column title: every column at once, as Ctrl+H."""
        view = self.view
        for column in view.columns() if view is not None else (self,):
            Panel.sort_by(column, mode, reverse)

    async def on_key(self, event: KeyEvent) -> bool:
        """Right steps into the directory at the cursor, Left back to the
        parent column -- unless a quick search is on, or *Use arrows* gives
        them to a command line with text."""
        view = self.view
        if (view is not None and event.key in ("left", "right") and not (event.ctrl or event.alt or event.shift)
                and self.quick_search is None and not self.inert and not self.arrows_to_line(event)):
            if event.key == "right":
                view.step_in()
            else:
                view.step_out(self)
            return True
        return await super().on_key(event)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        view = self.view
        if view is not None and event.action == "press" and not event.is_wheel:
            # Before the press moves the cursor: the columns right of this one
            # go, and the preview becomes a column.
            view.column_pressed(self)
        return await super().on_mouse_click(event)

    # -- painting ------------------------------------------------------------

    @computed
    def name_width(self) -> int:
        """The cells left of the directory sign."""
        return max(1, self.inner_width - 2)

    @computed
    def _info_lines(self) -> tuple[tuple[str | None, str], ...]:
        return ()

    @property
    def branch_sign(self) -> str:
        """What follows a directory's name: there is more to the right."""
        return ">" if self.glyphs <= glyphs_module.GLYPHS_ASCII else "▸"

    def title_text(self) -> str:
        """The directory's own name -- its path is the columns to the left."""
        location = self.location
        name = location.name
        if not name and location.outer is not None:
            name = location.outer.name
        name = name or self.title_location
        room = max(1, self.width - 4 - 2 * self.title_margin)
        return f" {self._cut_start(name, room)} "

    def row_classes(self, index: int, item: DirEntry) -> tuple[str, ...]:
        return ("trail",) if self._is_trail(index) else ()

    def _is_trail(self, index: int) -> bool:
        return self.trail and index == self.cursor and not self.focused

    def render_row(self, surface: Surface, y: int, index: int, item: DirEntry) -> None:
        style = self.row_style(index, item)
        left, width = self.inset, self.inner_width
        if self._is_trail(index):
            surface.fill(left, y, width, 1, " ", style)
        self._draw_name(surface, left, y, max(1, self.name_width), item, style, self.name_offset,
                        self.row_selected(index))
        if item.is_dir and width > 2:
            surface.draw_text(left + width - 1, y, self.branch_sign, style, 1)


class MillerView(Widget):
    """The columns, and the preview after them.

    Hidden in the file manager's row until Alt+F12, when it takes the two
    panels' place (``Manager.toggle_miller``).  Empty while hidden: the
    columns are made by :meth:`open_at` and dropped by :meth:`close`, so no
    directory is read or watched for a layout nobody is looking at.
    """

    #: The columns from the root down to the one being browsed, which is last
    #: and is the file manager's active panel.  Empty while the panels show.
    chain: tuple[MillerColumn, ...] = reactive(())
    #: What the preview shows: ``"directory"`` (:attr:`preview_dir`), ``"file"``
    #: (:attr:`preview_file`) or ``"none"`` (the quick view, empty).
    preview: str = reactive("none")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: The column after the chain, listing the directory at the cursor;
        #: made by :meth:`open_at`, and becoming the chain's last on a step in.
        self.preview_dir: MillerColumn | None = None
        self.preview_file: QuickViewer = self.add(QuickViewer())
        self.preview_file.visible = False

    def mounted(self) -> None:
        super().mounted()
        effect(self, MillerView._follow_moves)
        effect(self, MillerView._follow_cursor)
        effect(self, MillerView._place)

    def columns(self) -> list[MillerColumn]:
        """Every column there is: the chain's and the preview's."""
        return [*self.chain, *([self.preview_dir] if self.preview_dir is not None else [])]

    @property
    def current(self) -> MillerColumn | None:
        """The column being browsed, or None while the panels show."""
        return self.chain[-1] if self.chain else None

    # -- the chain -------------------------------------------------------------

    def open_at(self, location: Location, cursor: str | None = None, like: Panel | None = None) -> None:
        """Columns from the root down to *location*, its cursor on *cursor*;
        each takes *like*'s hidden files and order.  The keyboard goes to it."""
        location = _absolute(location)
        column = self.add(self._column(location, cursor, like))
        if self.preview_dir is None:
            self.preview_dir = self.add(self._column(location, None, column))
        self._rebuild(column)
        column.focus()

    def close(self) -> None:
        """Every column gone: the panels are back."""
        for column in self.columns():
            self.remove(column)
        self.preview_dir = None
        self.chain = ()
        self.preview = "none"
        self.preview_file.show(None)

    def _column(self, location: Location, cursor: str | None, like: Panel | None) -> MillerColumn:
        column = MillerColumn()
        if like is not None:
            column.show_hidden = like.show_hidden
            column.sort_mode = like.sort_mode
            column.sort_reverse = like.sort_reverse
        column._return_to = cursor
        column.location = location
        column.home = location
        return column

    def _set_chain(self, chain: list[MillerColumn]) -> None:
        for column in chain:
            column.trail = True
            column.current = False
        if chain:
            chain[-1].current = True
        if self.preview_dir is not None:
            self.preview_dir.trail = False
            self.preview_dir.current = False
        self.chain = tuple(chain)

    def _rebuild(self, column: MillerColumn) -> None:
        """The chain again, ending in *column* wherever it is now.

        Columns already showing the directories above it are kept, their
        cursors put on the way down; the rest are made.
        """
        column.home = column.location
        ups: list[tuple[Location, str]] = []
        where = column.location
        for _ in range(MAX_DEPTH):
            up = _up(where)
            if up is None:
                break
            ups.append(up)
            where = up[0]
        ups.reverse()
        old = [each for each in self.chain if each is not column]
        keep: list[MillerColumn] = []
        for (location, child), each in zip(ups, old):
            if each.location != location:
                break
            each.point_at(child)
            keep.append(each)
        for each in old[len(keep):]:
            self.remove(each)
        made = [self.add(self._column(location, child, column)) for location, child in ups[len(keep):]]
        self._set_chain([*keep, *made, column])
        self._remember(column.location)

    @staticmethod
    def _remember(location: Location) -> None:
        if location.outer is None:
            Panel._remember_directory(location)

    def step_in(self) -> bool:
        """Right, Enter: the directory at the cursor becomes the column being
        browsed -- the preview column, which lists it already."""
        current = self.current
        entry = current.selected if current is not None else None
        if entry is None or not entry.is_dir:
            return False
        target = current.entry_location(entry)
        step = self.preview_dir
        if step is None:
            step = self.add(self._column(target, None, current))
        elif step.home != target:
            step._return_to = step._keep = None
            step.location = step.home = target
        self.preview_dir = self.add(self._column(target, None, current))
        self._set_chain([*self.chain, step])
        step.focus()
        self._remember(target)
        return True

    def step_out(self, column: MillerColumn) -> bool:
        """Left, Backspace: back to the parent column, *column* becoming the
        preview again with its cursor where it was.  False at the root."""
        chain = list(self.chain)
        if len(chain) < 2 or column is not chain[-1]:
            return False
        parent = chain[-2]
        parent.focus()
        old, self.preview_dir = self.preview_dir, column
        if old is not None:
            self.remove(old)
        self._set_chain(chain[:-1])
        return True

    def column_pressed(self, column: MillerColumn) -> None:
        """A press on *column*: the preview column is stepped into, a column
        to the left becomes the one browsed, the ones after it going."""
        if column is self.preview_dir:
            self.step_in()
            return
        chain = list(self.chain)
        if column not in chain or column is chain[-1]:
            return
        index = chain.index(column)
        column.focus()
        old, self.preview_dir = self.preview_dir, chain[index + 1]
        for each in [*chain[index + 2:], *([old] if old is not None else [])]:
            self.remove(each)
        self._set_chain(chain[:index + 1])

    def switch_focus(self) -> None:
        """Tab: into the file previewed, and back to the column."""
        current = self.current
        if current is None:
            return
        if self.preview_file.focus_within or self.preview != "file":
            current.focus()
        else:
            self.preview_file.viewer.focus()

    # -- effects ---------------------------------------------------------------

    def _follow_moves(self) -> None:
        """The column being browsed went somewhere by itself: the chain
        follows it there."""
        current = self.current
        if current is None:
            return
        location = current.location
        with untracked():
            if location != current.home:
                self._rebuild(current)

    def _follow_cursor(self) -> None:
        """The preview shows what the cursor is on: a directory in the column
        after the chain, a file in the quick view."""
        current = self.current
        if current is None:
            return
        entry = current.selected
        _ = current.location, current.scanning
        with untracked():
            if entry is None or current.scanning:
                self.preview_file.show(None)
                self.preview = "none"
            elif entry.is_dir:
                target = current.entry_location(entry)
                step = self.preview_dir
                if step is not None and step.home != target:
                    step._return_to = step._keep = None
                    step.location = step.home = target
                self.preview_file.show(None)
                self.preview = "directory" if step is not None else "none"
            else:
                self.preview_file.show(current.entry_location(entry))
                self.preview = "file"

    def _place(self) -> None:
        """Lay the columns out from the left, as many as leave the preview a
        column's width, the leftmost giving way; the preview takes the rest."""
        chain = self.chain
        preview = self.preview
        width, height = self.width, self.height
        wanted = SETTINGS.file_manager.miller_width
        with untracked():
            column_width = max(MIN_WIDTH, wanted)
            shown = max(1, min(len(chain), (width - column_width) // column_width)) if chain else 0
            visible = chain[len(chain) - shown:]
            x = 0
            for column in chain:
                column.visible = column in visible
                column.title_margin = 0
            for column in visible:
                span = min(column_width, max(0, width - x))
                column.x, column.y, column.width, column.height = x, 0, span, height
                x += span
            if visible:
                visible[0].title_margin = ICON_MARGIN
            for kind, widget in (("directory", self.preview_dir), ("file", self.preview_file)):
                if widget is None:
                    continue
                on = bool(chain) and (preview == kind or (kind == "file" and preview == "none"))
                widget.visible = on
                widget.title_margin = ICON_MARGIN
                if on:
                    widget.x, widget.y, widget.width, widget.height = x, 0, max(0, width - x), height
