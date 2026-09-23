"""The file listing panel, and the entries it lists.

Everything here is about *files*.  Everything about *a list* -- the cursor,
the scroll, the two invariants that keep them honest, the framed container,
the row painting and the keys that move through it -- is
:class:`~navml.widgets.list_viewer.ListViewer`'s, which was extracted from
this file because this file was the only place in the repository that had it.

What is left is the four things a file manager adds to a list: where it is
(``path``), how it reads a directory (``_rescan``), what it does when you
press Enter on one (``enter``), and how a row of it looks -- the icon gutter,
the name, and the size column the original draws on the right.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from navkit.glyphs import GLYPHS_NERD
from navkit.reactive import computed, effect, reactive
from navkit.screen import Surface
from navkit.style import Style
from navkit.stylesheet import StyleProperty

from navml.widgets.list_viewer import ListViewer

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


class Panel(ListViewer):
    """One side of the desktop: a directory, listed.

    The model is the one :class:`ListViewer` defines -- assign ``path`` and
    the listing, the cursor and the scroll all follow -- with one effect of
    its own in front of the two it inherits: re-read the directory.  The
    ordering matters and is guaranteed: ``Effect.order`` is stamped when
    ``effect()`` is called and the scheduler sorts on it, so a rescan runs,
    then the cursor is clamped onto the new listing, then the scroll follows
    it.
    """

    #: Whether a listing shows a Nerd Font glyph beside each name.  ``auto``
    #: means "whenever the terminal can draw one" and ``none`` refuses even
    #: then, which is what a sheet aiming at strict DOS fidelity sets.  The
    #: application's to declare rather than the kit's: navkit draws box frames
    #: and knows nothing about icons.
    icons = StyleProperty("auto", values=("auto", "none"))

    path: Path = reactive(Path("."))
    #: Bumped to re-read a directory whose path has not changed.
    reload_token: int = reactive(0)
    #: Columns kept clear at each end of the top edge, so the path never runs
    #: under a window icon painted there -- the file manager's close and zoom
    #: icons sit on its panels' frames.  Kept at both ends because the title
    #: is centred.
    title_margin: int = reactive(0)

    def __init__(self, path: Path | None = None, **kwargs: Any):
        """*path* is optional because a widget markup constructs must be.

        It is also *seeded* rather than bound, which is the rule a panel is
        the reason for: ``enter()`` assigns ``path`` on every descent, and an
        attribute carrying a binding is read-only until something unbinds it.
        """
        super().__init__(**kwargs)
        #: Set by :meth:`enter` for the rescan that is about to happen, so the
        #: cursor can land on the directory we just climbed out of.
        self._return_to: str | None = None
        if path is not None:
            self.path = path

    def mounted(self) -> None:
        # Before ListViewer's two, because a rescan replaces the very list
        # they are about to clamp a cursor onto.
        effect(self, Panel._rescan)
        super().mounted()

    # -- the listing ---------------------------------------------------------

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

        self.items = entries
        self.error = error
        target, self._return_to = self._return_to, None
        self.cursor = next(
            (index for index, item in enumerate(entries) if item.name == target), 0
        )
        self.scroll = 0

    def reload(self) -> None:
        """Re-read the directory this panel shows."""
        self.reload_token += 1

    def enter(self) -> None:
        """Descend into the selected directory."""
        entry = self.selected
        if entry is None or not entry.is_dir:
            return
        # The rescan is deferred, so the cursor we want afterwards has to be
        # left behind as a note rather than applied on the next line.
        self._return_to = self.path.name if entry.name == ".." else None
        self.path = (self.path / entry.name).resolve()

    async def choose(self) -> bool:
        """What Enter and a double click mean here: descend."""
        self.enter()
        return True

    # -- painting ------------------------------------------------------------

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
        cell but the plain build does not, and the difference is invisible
        until a name starts one column late on somebody else's terminal.
        """
        return 2 if self.show_icons else 0

    @computed
    def name_width(self) -> int:
        """How much of a listing line is left once the size column is taken."""
        return max(1, self.width - 12)

    def title_text(self) -> str:
        """The path across the top frame, clipped to fit."""
        title = str(self.path)
        room = max(4, self.width - 4 - 2 * self.title_margin)
        if len(title) > room:
            title = "..." + title[-(room - 3) :]
        return f" {title} "

    def footer_text(self) -> str:
        """The selected name, or an item count when there is nothing to name."""
        entry = self.selected
        summary = f" {entry.name} " if entry else f" {len(self.items)} items "
        room = max(1, self.width - 4)
        return summary[: room - 1] + " " if len(summary) > room else summary

    def row_style(self, index: int, item: DirEntry) -> Style:
        return self.part_style(
            "row",
            classes=("directory",) if item.is_dir else (),
            selected=self.row_selected(index),
        )

    def render_row(self, surface: Surface, y: int, index: int, item: DirEntry) -> None:
        style = self.row_style(index, item)
        gutter = self.gutter
        # Still an explicit limit: the name stops where the size column
        # begins, which is nearer than the edge the surface would clip at.
        name_width = max(1, self.name_width - gutter)
        if gutter:
            icon = icon_glyphs.icon_for(item.name, item.is_dir)
            surface.draw_text(1, y, icon, style, gutter)
        surface.draw_text(1 + gutter, y, item.name, style, name_width)
        surface.draw_text(self.width - 9, y, item.display_size, style, 8)
