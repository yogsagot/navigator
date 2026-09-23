"""The file listing panel, and the entries it lists.

One of the screens that will move into ``*.nml`` markup: its geometry is
already assigned by the desktop as bindings and its listing already follows its
``path`` rather than being refreshed by hand, so what is left to convert is the
placement rather than the model.
"""

from __future__ import annotations

import os
from pathlib import Path

from navkit.events import MouseClickEvent
from navkit.glyphs import GLYPHS_NERD
from navkit.reactive import computed, effect, peek, reactive
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget

# Imported under another name because ``Panel`` declares an ``icons`` style
# property: inside a method the global still wins, but two ``icons`` a few
# lines apart meaning a module and a keyword is a trap rather than a saving.
from navigator import icons as icon_glyphs


class DirEntry:
    """One line in a panel: a name, whether it is a directory, and its size."""

    __slots__ = ("name", "is_dir", "size")

    def __init__(self, name: str, is_dir: bool, size: int):
        self.name = name
        self.is_dir = is_dir
        self.size = size

    @property
    def sort_key(self) -> tuple:
        # ".." first, then directories, then files -- as in the original.
        return (self.name != "..", not self.is_dir, self.name.lower())

    @property
    def display_size(self) -> str:
        if self.name == "..":
            return " UP--DIR"
        if self.is_dir:
            return "     DIR"
        size = float(self.size)
        for unit in ("", "K", "M", "G", "T"):
            if size < 1024 or unit == "T":
                return f"{self.size:>8}" if not unit else f"{size:>7.0f}{unit}"
            size /= 1024
        return f"{self.size:>8}"


class Panel(Widget):
    """A file listing panel with a frame, a header and a cursor.

    The model is declarative: ``path`` is the only thing a command really
    assigns, and the listing, the cursor and the scroll offset follow it.  So
    the invariants -- the cursor sits on a row that exists, the scroll keeps
    it visible -- hold no matter which path changed the state, including a
    terminal resize, which the old imperative version got wrong.
    """

    #: Whether a listing shows a Nerd Font glyph beside each name.  ``auto``
    #: means "whenever the terminal can draw one" and ``none`` refuses even
    #: then, which is what a sheet aiming at strict DOS fidelity sets.  The
    #: application's to declare rather than the kit's: navkit draws box frames
    #: and knows nothing about icons.
    icons = StyleProperty("auto", values=("auto", "none"))

    path: Path = reactive(Path("."))
    entries: list[DirEntry] = reactive(factory=list)
    error: str | None = reactive(None)
    cursor: int = reactive(0)
    scroll: int = reactive(0)
    active: bool = reactive(False)
    #: Bumped to re-read a directory whose path has not changed.
    reload_token: int = reactive(0)

    def __init__(self, path: Path | None = None, **kwargs):
        """*path* is optional because a widget markup constructs must be.

        A child block compiles to ``Panel(parent=self)`` and nothing else --
        markup sets every property *after* construction -- so a required
        positional argument is what would keep this widget out of a document
        altogether.  The reactive already defaults to ``Path(".")``, so the
        only thing this costs is one directory scan against that default
        before a bound ``path:`` arrives.
        """
        super().__init__(**kwargs)
        #: Set by :meth:`enter` for the rescan that is about to happen, so the
        #: cursor can land on the directory we just climbed out of.
        self._return_to: str | None = None
        if path is not None:
            self.path = path
        # Declaration order is flush order: rebuild the listing, put the
        # cursor somewhere real, then scroll to it.
        effect(self, Panel._rescan)
        effect(self, Panel._clamp_cursor)
        effect(self, Panel._follow_cursor)

    # -- model ---------------------------------------------------------------

    def _rescan(self) -> None:
        """Re-read the directory, whenever the path or the token changes."""
        _ = self.reload_token  # read for the dependency; this is what Ctrl+R moves
        path = self.path
        entries: list[DirEntry] = []
        error: str | None = None
        if path != path.parent:
            entries.append(DirEntry("..", True, 0))
        try:
            with os.scandir(path) as scan:
                for item in scan:
                    try:
                        is_dir = item.is_dir()
                        size = 0 if is_dir else item.stat().st_size
                    except OSError:
                        is_dir, size = False, 0
                    entries.append(DirEntry(item.name, is_dir, size))
        except OSError as exc:
            error = exc.strerror or str(exc)
        entries.sort(key=lambda entry: entry.sort_key)

        self.entries = entries
        self.error = error
        target, self._return_to = self._return_to, None
        self.cursor = next(
            (index for index, item in enumerate(entries) if item.name == target), 0
        )
        self.scroll = 0

    def _clamp_cursor(self) -> None:
        """Keep the cursor on a row that exists, however the listing changed.

        Assigning what it also reads is allowed here: an effect's own writes
        are part of the run it is in and do not wake it again.
        """
        last = len(self.entries) - 1
        self.cursor = min(max(self.cursor, 0), last) if last >= 0 else 0

    def _follow_cursor(self) -> None:
        """Scroll just far enough to keep the cursor on screen.

        ``scroll`` is read with :func:`~navkit.reactive.peek` because this is
        the effect that assigns it; subscribing to it would be a loop.
        """
        cursor, rows = self.cursor, self.rows
        scroll = peek(self, Panel.scroll)
        if cursor < scroll:
            self.scroll = cursor
        elif cursor >= scroll + rows:
            self.scroll = cursor - rows + 1

    def reload(self) -> None:
        """Re-read the directory this panel shows."""
        self.reload_token += 1

    @computed
    def rows(self) -> int:
        """How many listing lines fit between the top and bottom frame."""
        return max(0, self.height - 2)

    @computed
    def selected(self) -> DirEntry | None:
        """The entry the cursor is on, if the listing has one."""
        if 0 <= self.cursor < len(self.entries):
            return self.entries[self.cursor]
        return None

    def move_cursor(self, delta: int) -> None:
        if not self.entries:
            return
        # Deliberately unclamped: _clamp_cursor owns that invariant.
        self.cursor += delta

    def enter(self) -> None:
        """Descend into the selected directory."""
        entry = self.selected
        if entry is None or not entry.is_dir:
            return
        # The rescan is deferred, so the cursor we want afterwards has to be
        # left behind as a note rather than applied on the next line.
        self._return_to = self.path.name if entry.name == ".." else None
        self.path = (self.path / entry.name).resolve()

    async def on_double_click(self, event: MouseClickEvent) -> bool:
        """Open the row that was double-clicked: a directory, or ``..`` up.

        The original's mouse, and the panel's own rather than the
        application's -- this needs nothing but the panel it lands on, so it
        belongs to the panel, the way ``Manager.on_key`` holds the keys that
        need to know which panel is active and ``Console.on_key`` holds the
        scrollback.  Routing here is by position, so the event arrives in this
        panel's coordinates and the listing row is ``event.y - 1``, the 1
        being the top frame.

        It only has to enter.  navkit delivers the press that completed the
        double-click *as well*, and that press has already moved the cursor
        onto this row -- which is what the additive delivery is for.
        :meth:`enter` no-ops on a file and on a row with nothing on it, and
        treats ``..`` as the directory it is, so the guard here is only about
        rows inside the listing rather than the frame.
        """
        if event.button != "left":
            return False
        if 0 <= event.y - 1 < self.rows:
            self.enter()
        return True

    # -- painting ------------------------------------------------------------

    @computed
    def title_text(self) -> str:
        """The path across the top frame, clipped to fit."""
        title = str(self.path)
        room = max(1, self.width - 4)
        if len(title) > room:
            title = "..." + title[-(room - 3) :]
        return f" {title} "

    @computed
    def footer_text(self) -> str:
        """The selected name, or an item count when there is nothing to name."""
        entry = self.selected
        summary = f" {entry.name} " if entry else f" {len(self.entries)} items "
        room = max(1, self.width - 4)
        return summary[: room - 1] + " " if len(summary) > room else summary

    @property
    def show_icons(self) -> bool:
        """Whether to reserve the icon gutter.

        Both halves have to agree, the way a terminal's mouse support and the
        caller's wish for it do: the sheet says whether icons are wanted and
        the terminal says whether its font could draw one.
        """
        return self.icons != "none" and self.glyphs >= GLYPHS_NERD

    @property
    def gutter(self) -> int:
        """Columns held back at the left of a row for the icon.

        Two, not one.  A Nerd Font *Mono* build patches its icons to a single
        cell but the plain build does not, and no width table records which is
        installed; spending the second cell on a space means a glyph that comes
        out double-width covers it instead of shoving the name along.
        """
        return 2 if self.show_icons else 0

    @computed
    def name_width(self) -> int:
        """How much of a listing line is left once the size column is taken."""
        return max(1, self.width - 12)

    def render(self, surface: Surface) -> None:
        surface.draw_box(
            0,
            0,
            self.width,
            self.height,
            self.style,
            charset=self.box_charset(),
            fill=" ",
        )
        self._render_title(surface)
        self._render_entries(surface)
        self._render_footer(surface)

    def _render_title(self, surface: Surface) -> None:
        label = self.title_text
        style = self.part_style("title")
        surface.draw_text(max(1, (self.width - len(label)) // 2), 0, label, style)

    def _render_entries(self, surface: Surface) -> None:
        if self.error is not None:
            surface.draw_text(2, 2, self.error, self.part_style("error"), self.width - 4)
            return
        # Still an explicit limit: the name stops where the size column
        # begins, which is nearer than the edge the surface would clip at.
        gutter = self.gutter
        name_width = max(1, self.name_width - gutter)
        for row in range(self.rows):
            index = self.scroll + row
            if index >= len(self.entries):
                break
            entry = self.entries[index]
            # The cursor only shows on the panel that has focus, so the two
            # conditions are ANDed here rather than left to a ``:active``
            # selector: the row fill below is gated on the same answer.
            selected = index == self.cursor and self.active
            style = self.part_style(
                "row",
                classes=("directory",) if entry.is_dir else (),
                selected=selected,
            )
            y = 1 + row
            if selected:
                surface.fill(1, y, self.width - 2, 1, " ", style)
            if gutter:
                icon = icon_glyphs.icon_for(entry.name, entry.is_dir)
                surface.draw_text(1, y, icon, style, gutter)
            surface.draw_text(1 + gutter, y, entry.name, style, name_width)
            surface.draw_text(self.width - 9, y, entry.display_size, style, 8)

    def _render_footer(self, surface: Surface) -> None:
        summary = self.footer_text
        surface.draw_text(
            max(1, (self.width - len(summary)) // 2),
            self.height - 1,
            summary,
            self.part_style("footer"),
        )
