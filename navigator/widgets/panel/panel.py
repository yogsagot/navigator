"""The file listing panel, and the entries it lists.

Everything here is about *files*.  Everything about *a list* -- the cursor,
the scroll, the two invariants that keep them honest, the framed container,
the row painting and the keys that move through it -- is
:class:`~navml.widgets.dialog.list_viewer.ListViewer`'s, which was extracted from
this file because this file was the only place in the repository that had it.

What is left is the four things a file manager adds to a list: where it is
(``path``), how it reads a directory (``_rescan``), what it does when you
press Enter on one (``enter``), and how a row of it looks -- the gutter (an
icon, or Midnight Commander's type mark), the name, and the size column the
original draws on the right.
"""

from __future__ import annotations

import fnmatch
import os
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit import glyphs as glyphs_module
from navkit.glyphs import GLYPHS_NERD
from navkit.reactive import computed, effect, peek, reactive
from navkit.screen import Surface
from navkit.style import Style
from navkit.stylesheet import StyleProperty

from navml.widgets.dialog.list_viewer import ListViewer

# Imported under another name because ``Panel`` declares an ``icons`` style
# property: inside a method the global still wins, but two ``icons`` a few
# lines apart meaning a module and a keyword is a trap rather than a saving.
from navigator import icons as icon_glyphs


@dataclass(frozen=True, slots=True)
class ExecuteFile(Event):
    """Enter on an executable: run it.

    Raised by the panel, which knows the file and not the shell, and taken by
    whoever runs commands -- ``Shell``, in Navigator.  DOS Navigator ran an
    ``.EXE``, ``.COM`` or ``.BAT`` the same way, through ``cmExecString``;
    here "executable" is what the file system says.
    """

    path: Path


class DirEntry:
    """One line in a panel: a name, whether it is a directory, its size, its
    permission bits, when it was last modified and whether it is a symlink.

    ``mode`` is the link's *target*'s, except for a link pointing nowhere,
    where there is no target to describe and it is the link's own.
    """

    __slots__ = ("name", "is_dir", "size", "mode", "mtime", "is_link")

    def __init__(self, name: str, is_dir: bool, size: int, mode: int = 0, mtime: float = 0.0,
                 is_link: bool = False):
        self.name = name
        self.is_dir = is_dir
        self.size = size
        self.mode = mode
        self.mtime = mtime
        self.is_link = is_link

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

    @property
    def display_attributes(self) -> str:
        """``rwxr-xr-x``: ``ls -l``'s permission string, less the type letter.

        DOS Navigator showed the four DOS attributes here; a POSIX file has
        permissions instead, and the type is already the size column's.
        """
        return stat.filemode(self.mode)[1:]

    @property
    def type_mark(self) -> str:
        """Midnight Commander's one-character file type, for the gutter
        without an icon: ``/`` directory, ``*`` executable, ``@`` symlink,
        ``~`` symlink to a directory, ``!`` stale symlink, ``=`` socket, ``-``
        character device, ``+`` block device, ``|`` FIFO, and a blank for a
        plain file.

        Read off the mode bits rather than ``os.access``, so painting a row
        costs no system call.
        """
        mode = self.mode
        if self.is_link:
            if stat.S_ISLNK(mode):
                return "!"
            return "~" if self.is_dir else "@"
        if self.is_dir:
            return "/"
        if stat.S_ISSOCK(mode):
            return "="
        if stat.S_ISCHR(mode):
            return "-"
        if stat.S_ISBLK(mode):
            return "+"
        if stat.S_ISFIFO(mode):
            return "|"
        if stat.S_ISREG(mode) and mode & 0o111:
            return "*"
        return " "

    @property
    def display_date(self) -> str:
        """The modification time, ``DD-MM-YY hh:mm`` as DN's default country drew it.

        Modification, not creation: a DOS directory entry held one date, and
        Linux cannot report a creation time portably.
        """
        return time.strftime("%d-%m-%y %H:%M", time.localtime(self.mtime))


def _matches(name: str, patterns: list[str]) -> bool:
    """Whether *name* matches any of *patterns*, as :meth:`Panel.select_group` reads them."""
    name = name.lower()
    for pattern in patterns:
        pattern = pattern.lower()
        if fnmatch.fnmatchcase(name, pattern):
            return True
        if pattern.endswith(".*") and "." not in name and fnmatch.fnmatchcase(name, pattern[:-2]):
            return True
    return False


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

    #: Enter on an executable, going up to whoever runs commands.
    emits = (ExecuteFile,)

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
    #: How the listing is laid out -- one of :data:`VIEW_MODES`, and Ctrl+Y
    #: (``cmToggleShowMode``) steps through them.  Per panel, as DN's
    #: ``ShowFlags`` were.
    view_mode: str = reactive("simple")
    #: Whether names starting with ``.`` are listed.  Ctrl+H flips it, per
    #: panel like ``view_mode``; ``..`` is always listed.
    show_hidden: bool = reactive(True)
    #: The names tagged with Insert -- DN's ``TFileRec.Selected``, held here
    #: rather than on the entry because a rescan builds new entries.  Kept
    #: across a re-read of the same directory, less the names that went, and
    #: cleared by a change of directory.
    marked: frozenset[str] = reactive(frozenset())

    #: ``simple``: name and size.  ``detailed``: name, size, permissions and
    #: date in columns.  ``list``: names alone, in as many columns as fit.
    VIEW_MODES = ("simple", "detailed", "list")

    #: ``heading`` is the column-titles row the detailed and list modes draw.
    parts = ListViewer.parts + ("heading",)

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
        #: Set by :meth:`reload`: the directory, the entry under the cursor,
        #: the cursor and the scroll, for a re-read of *that* directory to put
        #: back.  Ignored if the panel has gone somewhere else meanwhile.
        self._keep: tuple[Path, str, int, int] | None = None
        #: The directory the last rescan read, which tells a re-read (keep
        #: the tags) from a move (drop them).
        self._listed: Path | None = None
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
        show_hidden = self.show_hidden
        entries: list[DirEntry] = []
        error: str | None = None
        if path != path.parent:
            try:
                info = path.parent.stat()
                entries.append(DirEntry("..", True, 0, info.st_mode, info.st_mtime))
            except OSError:
                entries.append(DirEntry("..", True, 0))
        try:
            with os.scandir(path) as scan:
                for item in scan:
                    if not show_hidden and item.name.startswith("."):
                        continue
                    try:
                        info = item.stat()
                    except OSError:
                        # A dangling link: describe the link itself.
                        try:
                            info = item.stat(follow_symlinks=False)
                        except OSError:
                            info = None
                    try:
                        is_link = item.is_symlink()
                    except OSError:
                        is_link = False
                    if info is None:
                        entries.append(DirEntry(item.name, False, 0, is_link=is_link))
                        continue
                    is_dir = stat.S_ISDIR(info.st_mode)
                    size = 0 if is_dir else info.st_size
                    entries.append(DirEntry(item.name, is_dir, size, info.st_mode, info.st_mtime, is_link))
        except OSError as exc:
            error = exc.strerror or str(exc)
        entries.sort(key=lambda entry: entry.sort_key)

        self.items = entries
        self.error = error
        # Peeked, not read: the rescan must not depend on the tags, or every
        # Insert would re-read the directory.
        marked = peek(self, Panel.marked)
        if path != self._listed:
            marked = frozenset()
        elif marked:
            marked &= {entry.name for entry in entries}
        self.marked = marked
        self._listed = path
        target, self._return_to = self._return_to, None
        keep, self._keep = self._keep, None
        if keep is not None and keep[0] == path and target is None:
            # A re-read of the same directory: the cursor stays on its entry,
            # or where the entry was if it went, and the view does not jump.
            _, name, cursor, scroll = keep
            found = next((i for i, item in enumerate(entries) if item.name == name), None)
            self.cursor = found if found is not None else min(cursor, max(0, len(entries) - 1))
            self.scroll = scroll
            return
        self.cursor = next(
            (index for index, item in enumerate(entries) if item.name == target), 0
        )
        self.scroll = 0

    def reload(self) -> None:
        """Re-read the directory this panel shows, keeping the cursor on its entry.

        DOS Navigator's re-read after a command left the cursor where it was;
        this one used to send it back to the top, so the file just run, or
        just renamed by a command, was lost.
        """
        entry = self.selected
        if entry is not None:
            self._keep = (self.path, entry.name, self.cursor, self.scroll)
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

    def go_up(self) -> None:
        """Go to the parent directory, the cursor on the one just left.

        DN's ``_CtrlPgUp``: what choosing ``..`` does, from anywhere in the
        listing.  At the root there is nowhere to go and nothing happens.
        """
        parent = (self.path / "..").resolve()
        if parent == self.path:
            return
        self._return_to = self.path.name
        self.path = parent

    # -- tagging -------------------------------------------------------------

    def is_marked(self, item: DirEntry) -> bool:
        return item.name in self.marked

    def toggle_mark(self) -> None:
        """Insert: tag or untag the entry under the cursor, and step down.

        DN's ``kbIns`` in ``TFilePanel.HandleEvent``: ``..`` is never tagged
        -- DN refused any name starting with a dot, which in DOS meant only
        ``.`` and ``..`` -- and the cursor moves down one either way, so
        holding Insert tags a run.
        """
        entry = self.selected
        if entry is None:
            return
        if entry.name != "..":
            self.marked = self.marked ^ {entry.name}
        self.move_cursor(1)

    def select_group(self, mask: str, *, select: bool = True, invert: bool = False) -> None:
        """Gray ``+`` and ``-``: tag, or untag, every entry *mask* matches.

        DN's ``SelectFiles``: selecting passes directories over and
        unselecting does not, *invert* is *Except mask* (the entries the mask
        does **not** match), and ``..`` is never tagged.  *mask* is one or
        more shell patterns joined by ``;``, matched without regard to case as
        DN's ``InMask`` matched upper-cased names, and a pattern ending ``.*``
        also matches a name with no dot at all, as DOS's ``*.*`` did.
        """
        patterns = [pattern.strip() for pattern in mask.split(";") if pattern.strip()]
        if not patterns:
            return
        matched = {
            item.name
            for item in self.items
            if item.name != ".."
            and (select is False or not item.is_dir)
            and _matches(item.name, patterns) != invert
        }
        self.marked = (self.marked | matched) if select else (self.marked - matched)

    def invert_marks(self, *, directories: bool = False) -> None:
        """Gray ``*``: DN's ``InvertSelection``.

        Every file's tag flips; a directory's flips only with *directories*
        (Ctrl+Gray ``*``) and otherwise keeps whatever it had.  ``..`` is
        never tagged.
        """
        flipped = {
            item.name
            for item in self.items
            if item.name != ".." and (directories or not item.is_dir)
        }
        self.marked = self.marked ^ flipped

    @property
    def marked_entries(self) -> list[DirEntry]:
        """The tagged entries, in listing order."""
        marked = self.marked
        return [item for item in self.items if item.name in marked]

    async def choose(self) -> bool:
        """What Enter and a double click mean here: descend, or run.

        A directory is descended into.  A file the user may execute is run --
        :class:`ExecuteFile`, emitted up to whoever runs commands.  Anything
        else is left alone.
        """
        entry = self.selected
        if entry is not None and not entry.is_dir:
            path = self.path / entry.name
            if path.is_file() and os.access(path, os.X_OK):
                await self.emit(ExecuteFile(path))
            return True
        self.enter()
        return True

    async def on_double_click(self, event: MouseClickEvent) -> bool:
        """Ctrl+double click is Ctrl+Enter, as in DOS Navigator; a plain one opens."""
        if event.ctrl and event.button == "left" and self.index_at(event.x, event.y) is not None:
            from navigator.commands import InsertName, InsertPath

            await self.emit(InsertPath() if event.shift else InsertName())
            return True
        return await super().on_double_click(event)

    # -- show modes ----------------------------------------------------------

    def cycle_view_mode(self) -> None:
        """Ctrl+Y: the next of :data:`VIEW_MODES`, the last wrapping to the first.

        The heading row comes and goes with it: the simple mode is the panel
        as it always was, and the other two title their columns.
        """
        modes = self.VIEW_MODES
        mode = modes[(modes.index(self.view_mode) + 1) % len(modes)]
        self.view_mode = mode
        self.header = 0 if mode == "simple" else 1

    def toggle_hidden(self) -> None:
        """Ctrl+H: hide the dot-files, or show them again.

        A re-read like :meth:`reload`'s, so the cursor stays on its entry, or
        where it was if that entry is the one just hidden.  A tag on a name
        that goes is dropped with it, so nothing unseen stays selected.
        """
        entry = self.selected
        if entry is not None:
            self._keep = (self.path, entry.name, self.cursor, self.scroll)
        self.show_hidden = not self.show_hidden

    async def on_key(self, event: KeyEvent) -> bool:
        """In the list mode Left and Right move a column, as DN's did.

        Otherwise they are declined, and reach the command line.
        """
        if self.view_mode == "list" and not self.inert and self.rows:
            if event.key == "left":
                self.move_cursor(-min(self.rows, self.cursor))
                return True
            if event.key == "right":
                self.move_cursor(min(self.rows, len(self.items) - 1 - self.cursor))
                return True
        return await super().on_key(event)

    #: The detailed mode's columns after the name: heading, width, and the
    #: ``DirEntry`` property that fills it.  Dropped from the end of
    #: :data:`DROP_ORDER` first when the name would get too narrow.
    DETAIL_COLUMNS = {
        "size": ("Size", 8, "display_size"),
        "attributes": ("Attr", 9, "display_attributes"),
        "date": ("Date", 14, "display_date"),
    }
    DETAIL_ORDER = ("size", "attributes", "date")
    DROP_ORDER = ("attributes", "date")
    #: The narrowest the detailed mode lets the name column get before it
    #: gives up a column to widen it.
    MIN_NAME_WIDTH = 12

    @computed
    def detail_columns(self) -> tuple[tuple[str, int, int], ...]:
        """``(key, x, width)`` for every detailed-mode column, the name's first.

        Each column after the name has a divider in the cell before it.  The
        name takes whatever is left; when that is under
        :data:`MIN_NAME_WIDTH`, the attributes go, and then the date.
        """
        inset, inner = self.inset, self.inner_width
        shown = list(self.DETAIL_ORDER)

        def rest() -> int:
            return inner - sum(self.DETAIL_COLUMNS[key][1] + 1 for key in shown)

        for key in self.DROP_ORDER:
            if rest() >= self.MIN_NAME_WIDTH:
                break
            shown.remove(key)
        name_width = max(1, rest())
        columns = [("name", inset, name_width)]
        x = inset + name_width + 1
        for key in shown:
            width = self.DETAIL_COLUMNS[key][1]
            columns.append((key, x, width))
            x += width + 1
        return tuple(columns)

    @computed
    def list_columns(self) -> tuple[tuple[int, int, int], ...]:
        """``(first index, x, width)`` for every list-mode column on show.

        Columns hold ``rows`` items each, from ``scroll``; each is as wide as
        its longest name (and the icon gutter), capped at half the panel so
        that a long name cannot push the second column off it.  The last may
        run past the right edge and be clipped.
        """
        rows, inner, inset = self.rows, self.inner_width, self.inset
        items, gutter = self.items, self.gutter
        if not rows or inner <= 0:
            return ()
        cap = inner if len(items) - self.scroll <= rows else max(1, (inner - 1) // 2)
        columns = []
        first, x = self.scroll, inset
        while first < len(items) and x < inset + inner:
            longest = max(len(item.name) for item in items[first : first + rows])
            width = min(cap, gutter + max(1, longest))
            columns.append((first, x, width))
            first += rows
            x += width + 1
        return tuple(columns)

    @computed
    def capacity(self) -> int:
        """In the list mode, the items in every column shown whole."""
        if self.view_mode != "list":
            return self.rows
        right = self.inset + self.inner_width
        whole = [c for c in self.list_columns if c[1] + c[2] <= right]
        return self.rows * max(1, len(whole))

    def _follow_cursor(self) -> None:
        """In the list mode, scroll a whole column at a time.

        ``scroll`` stays a multiple of ``rows``, so a column's contents -- and
        so its width -- do not change as the cursor moves through it.
        """
        if self.view_mode != "list":
            super()._follow_cursor()
            return
        rows = self.rows
        if not rows:
            return
        cursor = self.cursor
        scroll = peek(self, ListViewer.scroll)
        scroll -= scroll % rows
        if cursor < scroll:
            scroll = cursor - cursor % rows
        # Advance a column at a time until the cursor's is shown whole.  The
        # columns depend on the scroll, so each step lays them out again.
        while True:
            self.scroll = scroll
            columns = self.list_columns
            right = self.inset + self.inner_width
            if not columns or any(
                first <= cursor < first + rows and x + width <= right
                for first, x, width in columns
            ) or (columns and columns[0][0] <= cursor < columns[0][0] + rows):
                break
            scroll += rows

    def page(self) -> int:
        if self.view_mode == "list":
            return max(1, self.capacity)
        return super().page()

    def index_at(self, x: int, y: int) -> int | None:
        if self.view_mode != "list":
            return super().index_at(x, y)
        row = y - self.inset - self.header
        if not 0 <= row < self.rows:
            return None
        for first, left, width in self.list_columns:
            if left <= x < left + width:
                index = first + row
                return index if index < len(self.items) else None
        return None

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
        """Columns held back at the left of a row, for the icon or the type mark.

        Two with an icon, not one.  A Nerd Font *Mono* build patches its icons
        to a single cell but the plain build does not, and the difference is
        invisible until a name starts one column late on somebody else's
        terminal.  Without one it is a single cell holding
        :attr:`DirEntry.type_mark` -- and always kept, because a tagged
        entry's :attr:`tag_char` is drawn there too.
        """
        return 2 if self.show_icons else 1

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
        marked = self.marked_entries
        if marked:
            # DN's info line: ``dlBytesIn`` and ``dlSelectedFiles``.
            size = sum(item.size for item in marked)
            summary = f" {size:,} bytes in {len(marked)} selected files "
        else:
            entry = self.selected
            summary = f" {entry.name} " if entry else f" {len(self.items)} items "
        room = max(1, self.width - 4)
        return summary[: room - 1] + " " if len(summary) > room else summary

    def row_style(self, index: int, item: DirEntry) -> Style:
        classes = ("directory",) if item.is_dir else ()
        if self.is_marked(item):
            classes += ("marked",)
        return self.part_style("row", classes=classes, selected=self.row_selected(index))

    @property
    def divider_glyph(self) -> str:
        """``│`` between columns -- always single, whatever the frame, as DN's were."""
        return glyphs_module.charset("single", self.glyphs)[5]

    #: What stands in the gutter of a tagged entry: DN's default
    #: ``FMSetup.TagChar``, CP437's ``$FB``, and a plain ``+`` where the
    #: terminal draws ASCII only.
    TAG_CHAR = "√"
    TAG_CHAR_ASCII = "+"

    @property
    def tag_char(self) -> str:
        return self.TAG_CHAR if self.glyphs > glyphs_module.GLYPHS_ASCII else self.TAG_CHAR_ASCII

    def _draw_name(self, surface: Surface, x: int, y: int, width: int,
                   item: DirEntry, style: Style) -> None:
        """The tag, the icon or the type mark, and the name, in *width* cells.

        A tag takes the gutter over whichever of the other two it would hold:
        the colour says *tagged* too, but not on a monochrome terminal.
        """
        gutter = min(self.gutter, width)
        if gutter:
            if self.is_marked(item):
                mark = self.tag_char
            elif self.show_icons:
                mark = icon_glyphs.icon_for(item.name, item.is_dir, item.type_mark)
            else:
                mark = item.type_mark
            surface.draw_text(x, y, mark, style, gutter)
        if width > gutter:
            surface.draw_text(x + gutter, y, item.name, style, width - gutter)

    def render_row(self, surface: Surface, y: int, index: int, item: DirEntry) -> None:
        style = self.row_style(index, item)
        if self.view_mode == "detailed":
            selected = self.row_selected(index)
            for key, x, width in self.detail_columns:
                if key == "name":
                    self._draw_name(surface, x, y, width, item, style)
                    continue
                if selected:
                    # The cursor bar covers the dividers; draw them back in it.
                    surface.draw_text(x - 1, y, self.divider_glyph, style, 1)
                text = getattr(item, self.DETAIL_COLUMNS[key][2])
                surface.draw_text(x, y, text[:width], style, width)
            return
        # Still an explicit limit: the name stops where the size column
        # begins, which is nearer than the edge the surface would clip at.
        self._draw_name(surface, 1, y, max(1, self.name_width), item, style)
        surface.draw_text(self.width - 9, y, item.display_size, style, 8)

    def render_items(self, surface: Surface) -> None:
        if self.view_mode != "list":
            super().render_items(surface)
            return
        top = self.inset + self.header
        items = self.items
        for first, x, width in self.list_columns:
            for row in range(self.rows):
                index = first + row
                if index >= len(items):
                    break
                item = items[index]
                style = self.row_style(index, item)
                if self.row_selected(index):
                    surface.fill(x, top + row, width, 1, " ", style)
                self._draw_name(surface, x, top + row, width, item, style)

    def _column_spans(self) -> list[tuple[str, int, int]]:
        """``(heading, x, width)`` for the columns of the current mode."""
        if self.view_mode == "detailed":
            return [
                ("Name" if key == "name" else self.DETAIL_COLUMNS[key][0], x, width)
                for key, x, width in self.detail_columns
            ]
        if self.view_mode == "list":
            columns = self.list_columns
            if not columns:
                return [("Name", self.inset, self.inner_width)]
            return [("Name", x, width) for _, x, width in columns]
        return []

    def render_header(self, surface: Surface) -> None:
        """The column titles, and the dividers from them down to the last row.

        Drawn before the rows, so the cursor bar covers a divider it crosses
        -- DN's did.  Nothing in the simple mode, and nothing over an error.
        """
        if self.view_mode == "simple" or self.error is not None:
            return
        top = self.inset
        bottom = top + self.header + self.rows
        right = self.inset + self.inner_width
        glyph = self.divider_glyph
        heading = self.part_style("heading")
        divider = self.part_style("divider")
        for index, (text, x, width) in enumerate(self._column_spans()):
            shown = min(width, right - x)
            if shown <= 0:
                break
            text = text[:shown]
            surface.draw_text(x + (shown - len(text)) // 2, top, text, heading, shown)
            edge = x + width
            if edge < right:
                for y in range(top, bottom):
                    surface.draw_text(edge, y, glyph, divider, 1)
