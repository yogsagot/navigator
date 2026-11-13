"""Tagging (Insert, Space, Gray +/-/*), and choosing an entry: Enter, an archive, an image, a
program run.

A mixin of :class:`Panel` (``navkit.widget.Mixin``): methods only; its state,
keys and the listing are in ``panel.py``.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

from navkit.events import MouseClickEvent

from navigator.lib.appearance import filetypes
from navigator.lib.drives import Location
from navigator.lib.drives.listing import DirEntry
from navigator.settings import SETTINGS
from navigator.widgets.manager.panel.helpers import ExecuteFile, OpenFile

if TYPE_CHECKING:
    from navigator.widgets.manager.panel.panel import Panel as _Base
else:
    from navkit.widget import Mixin as _Base


class Tagging(_Base):
    """Tagging (Insert, Space, Gray +/-/*), and choosing an entry: Enter, an archive, an image, a"""

    # -- tagging -------------------------------------------------------------

    def is_marked(self, item: DirEntry) -> bool:
        return item.key in self.marked

    def untag_paths(self, paths: Iterable[Path]) -> None:
        """Take the tags off the entries at *paths*: what a copy, a move or an
        erase leaves of the ones it finished."""
        done = {Location.of(path) for path in paths}
        if done:
            self.untag(item for item in self.items if self.entry_location(item) in done)

    def tag_paths(self, locations: Iterable[Location]) -> None:
        """Tag the entries at *locations* this panel lists: what Verify
        checksums leaves on the files that did not match."""
        def key(location: Location) -> Location:
            location = location.normalized()
            return Location.of(Path(location.path).absolute()) if location.is_local else location

        wanted = {key(location) for location in locations}
        if not wanted:
            return
        keys = {item.key for item in self.items
                if item.name != ".." and key(self.entry_location(item)) in wanted}
        if keys - self.marked:
            self.marked = self.marked | keys

    def untag(self, entries: Iterable[DirEntry]) -> None:
        """Take *entries*' tags off: what an operation done on them leaves."""
        keys = {entry.key for entry in entries}
        if keys & self.marked:
            self.marked = self.marked - keys

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
            self.marked = self.marked ^ {entry.key}
        self.move_cursor(1)

    def select_group(self, mask: str, *, select: bool = True, invert: bool = False) -> None:
        """Gray ``+`` and ``-``: tag, or untag, every entry *mask* matches.

        DN's ``SelectFiles``: selecting passes directories over and
        unselecting does not, *invert* is *Except mask* (the entries the mask
        does **not** match), and ``..`` is never tagged.  *mask* is one or
        more shell patterns joined by ``;``, matched as a POSIX glob -- case
        counting, and ``*.*`` needing a dot (:func:`filetypes.matches`).
        """
        patterns = filetypes.patterns(mask)
        if not patterns:
            return
        matched = {
            item.key
            for item in self.items
            if item.name != ".."
            and (select is False or not item.is_dir)
            and filetypes.matches(item.name, patterns) != invert
        }
        self.marked = (self.marked | matched) if select else (self.marked - matched)

    def select_similar(self, by: str, *, select: bool = True, invert: bool = False) -> None:
        """Alt/Ctrl + Gray ``+``/``-``: DN's ``SelectExt`` and ``SelecType`` --
        tag (or untag) every entry like the one at the cursor.

        *by* ``"name"`` compares the stem (``os.path.splitext``: one extension,
        as DN's 8.3 name had one; *invert*, those that differ), ``"extension"``
        the extension as it is, ``"type"`` the highlight group
        (:func:`filetypes.category_of`, DN's ``TType``).  Directories count, as
        ``Sel`` passed none over; ``..`` never does, nor does the cursor on it.
        """
        entry = self.selected
        if entry is None or entry.name == "..":
            return

        def key_of(item: DirEntry) -> Any:
            if by == "type":
                return filetypes.category_of(item.name, item.is_dir, item.type_mark)
            stem, extension = os.path.splitext(item.name)
            return extension if by == "extension" else stem

        wanted = key_of(entry)
        matched = {
            item.key
            for item in self.items
            if item.name != ".." and (key_of(item) == wanted) != invert
        }
        self.marked = (self.marked | matched) if select else (self.marked - matched)

    def invert_marks(self, *, directories: bool = False) -> None:
        """Gray ``*``: DN's ``InvertSelection``.

        Every file's tag flips; a directory's flips only with *directories*
        (Ctrl+Gray ``*``) and otherwise keeps whatever it had.  ``..`` is
        never tagged.
        """
        flipped = {
            item.key
            for item in self.items
            if item.name != ".." and (directories or not item.is_dir)
        }
        self.marked = self.marked ^ flipped

    def select_all(self) -> None:
        """Ctrl+A: every entry tagged, directories too; ``..`` never."""
        self.marked = frozenset(item.key for item in self.items if item.name != "..")

    @property
    def marked_entries(self) -> list[DirEntry]:
        """The tagged entries, in listing order -- a list of the caller's own,
        from :attr:`_marked_tuple`, so asking costs what is tagged, not what is
        listed (the key bar asks every frame)."""
        return list(self._marked_tuple)

    async def choose(self, *, archives: bool = True) -> bool:
        """What Enter and a double click mean here: descend, or run.

        A directory is descended into.  A file the user may execute is run --
        :class:`ExecuteFile`, emitted up to whoever runs commands -- and any
        other file is :class:`OpenFile`, for whoever knows what its name runs.
        Without *archives* (Shift+Enter, DN's ``ShiftState and 3 = 0`` test)
        an archive or a disk image is a file like any other, never entered.
        """
        entry = self.selected
        if self.found is not None:
            self.enter()
            return True
        if archives and entry is not None and not entry.is_dir and self._may_mount_image(entry):
            # Attached and mounted on a thread; without udisks it is entered
            # or run below, as before.
            self.spawn(self._mount_or_enter(entry))
            return True
        if archives and entry is not None and not entry.is_dir and self._may_enter_archive(entry):
            # Read on a thread: one that is no archive after all runs below.
            self.spawn(self._enter_or_run(entry))
            return True
        if entry is not None and not entry.is_dir:
            await self._run_file(entry)
            return True
        self.enter()
        return True

    def _may_enter_archive(self, entry: DirEntry) -> bool:
        """DN's ``fmoEnterArchives`` test: *Enter opens an archive* on, a file
        whose name the *archive* file type takes, and the panel not in an
        archive already -- DN opened none from inside another.  Whether it
        is one is the file's to say (:func:`navigator.lib.drives.archive.open_archive`),
        by what is in it, as ``ArcViewer`` read the signature."""
        return SETTINGS.file_manager.enter_opens_archive and self.archive_on_f3(entry)

    def archive_on_f3(self, entry: DirEntry) -> bool:
        """Whether F3 opens *entry* in the panel, DN's ``ArcViewer`` in
        ``ViewFile``: :meth:`_may_enter_archive` without the setting, which
        DN's F3 never asked."""
        return (self.found is None and self.location.outer is None
                and stat.S_ISREG(entry.mode) and filetypes.group_of(entry.name) == "archive")

    def _may_mount_image(self, entry: DirEntry) -> bool:
        """Whether Enter mounts *entry* as a disk image: *Enter mounts disc
        images* on, an ``.iso`` or ``.img`` on the disk -- not in an archive
        -- and ``udisksctl`` to attach it.  Not DN's, which had no loop devices
        (:func:`navigator.lib.system.udisks.attach_image`)."""
        from navigator.lib.system import udisks

        return (SETTINGS.file_manager.enter_mounts_images and self.location.is_local
                and self.location.outer is None and stat.S_ISREG(entry.mode)
                and udisks.is_image_name(entry.name) and udisks.program() is not None)

    async def _mount_or_enter(self, entry: DirEntry) -> None:
        from navigator.widgets.drives.disk_image import enter_image

        if await enter_image(self, entry.path_in(self.path)):
            return
        if self._may_enter_archive(entry):
            await self._enter_or_run(entry)
        else:
            await self._run_file(entry)

    async def _enter_or_run(self, entry: DirEntry) -> None:
        from navigator.widgets.drives.archives import enter_archive

        if not await enter_archive(self, self.entry_location(entry)):
            await self._run_file(entry)

    async def _run_file(self, entry: DirEntry) -> None:
        """Enter on a file: :class:`ExecuteFile` for one the user may run,
        :class:`OpenFile` for any other."""
        if not self.location.is_local:
            # Nothing on another drive can be run from here, so an executable
            # is opened as any file is: a departure DN never met, its link
            # drive having no programs of its own to run.
            if stat.S_ISREG(entry.mode):
                await self.emit(OpenFile(self.entry_location(entry)))
            return
        path = entry.path_in(self.path)
        if path.is_file() and os.access(path, os.X_OK):
            await self.emit(ExecuteFile(path))
        elif path.is_file():
            await self.emit(OpenFile(path))

    async def on_double_click(self, event: MouseClickEvent) -> bool:
        """Ctrl+double click is Ctrl+Enter, as in DOS Navigator; a plain one opens."""
        index = self.index_at(event.x, event.y)
        if event.ctrl and event.button == "left" and index is not None:
            from navigator.widgets.shell.commands import InsertName, InsertPath

            # The first press of the pair tagged a range (``_shift_select``):
            # a Ctrl+double click inserts the name and tags nothing.
            before = self._before_range
            if before is not None and before[0] == index:
                self.marked = before[1]
            self._before_range = None
            await self.emit(InsertPath() if event.shift else InsertName())
            return True
        return await super().on_double_click(event)
