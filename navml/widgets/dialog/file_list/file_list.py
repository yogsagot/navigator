"""A file dialog's lists: DOS Navigator's ``TFileList`` and ``TDirectoryList``.

``DNSTDDLG.PAS`` kept the two apart, each a ``TSortedListBox`` of
``TSearchRec``: the files matching the wildcard in one, and the directories in
the other, ``..`` first.  Here they are one class told which half it is, and
:func:`scan` reads a directory for both.  navml lists a directory itself
because it may not import the file manager that also does.

**Typing searches**, as ``TSortedListBox.HandleEvent`` did: each character
lengthens a prefix, the first entry it begins (in either case) takes the
cursor, a character nothing begins is ignored, and Backspace shortens it.
Moving the cursor any other way starts afresh.  The terminal cursor stands
after what has been typed, which was the whole of DN's display of it.

Departures: no drives (``[-C-]``) in the directory list, there being none, and
a directory's name ends in ``/``.  A directory whose name starts with a dot is
listed only with hidden files shown -- on DOS the only such names were ``.``
and ``..``, which DN left out by that test.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import time

from navkit.events import KeyEvent
from navkit.i18n import tr
from navkit.reactive import peek, reactive
from navkit.screen import Surface
from navkit.widget import Widget

from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tree_view import ChosenEvent


@dataclass(frozen=True, slots=True)
class FileItem:
    """``TSearchRec``: what the lists hold and the info pane shows."""

    name: str
    is_dir: bool
    size: int = 0
    mtime: float = 0.0


def _sort_key(item: FileItem) -> tuple[bool, str, str]:
    return (item.name != "..", item.name.lower(), item.name)


def scan(directory: Path, wildcard: str, hidden: bool) -> tuple[list[FileItem], list[FileItem]]:
    """The files in *directory* matching *wildcard*, and its directories.

    ``TFileList.ReadDirectory`` and ``TDirectoryList.ReadDirectory``: files
    by name, then ``..`` (unless *directory* is the root) and the directories
    by name.  A dot-file is left out unless *hidden*, as DN left out what
    ``ossShowHidden`` hid.  A link is listed as what it points to.
    """
    directory = Path(os.path.abspath(directory))
    files: list[FileItem] = []
    dirs: list[FileItem] = []
    try:
        entries = list(os.scandir(directory))
    except OSError:
        entries = []
    for entry in entries:
        if not hidden and entry.name.startswith("."):
            continue
        try:
            is_dir = entry.is_dir()
            info = entry.stat()
        except OSError:
            continue
        if is_dir:
            dirs.append(FileItem(entry.name, True, 0, info.st_mtime))
        elif fnmatch.fnmatchcase(entry.name, wildcard):
            files.append(FileItem(entry.name, False, info.st_size, info.st_mtime))
    if directory.parent != directory:
        try:
            mtime = directory.parent.stat().st_mtime
        except OSError:
            mtime = 0.0
        dirs.append(FileItem("..", True, 0, mtime))
    return sorted(files, key=_sort_key), sorted(dirs, key=_sort_key)


class FileList(ListViewer):
    """One of a file dialog's lists: its files, or its directories."""

    emits = (ChosenEvent,)

    #: What has been typed to search the list.
    search: str = reactive("")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: Where the cursor was when the search last moved it; any other
        #: position means the cursor was moved some other way.
        self._searched_at = -1

    def show(self, items: list[FileItem]) -> None:
        """List *items* from the top, a search starting afresh."""
        self.items = list(items)
        self.cursor = 0
        self.search = ""

    def row_text(self, index: int, item: Any) -> str:
        return " " + item.name + ("/" if item.is_dir else "")

    async def choose(self) -> bool:
        """Enter or a double click: DN's ``cmOK``, which the dialog takes."""
        if self.selected is None:
            return False
        await self.emit(ChosenEvent(self.selected))
        return True

    # -- the incremental search -------------------------------------------------

    def _current_search(self) -> str:
        """What has been typed, unless the cursor has since moved another way."""
        return self.search if peek(self, ListViewer.cursor) == self._searched_at else ""

    def search_for(self, text: str) -> bool:
        """Move to the first entry *text* begins; False, the cursor unmoved, if none."""
        wanted = text.lower()
        for index, item in enumerate(self.items):
            if self.row_text(index, item)[1:].lower().startswith(wanted):
                self.cursor = index
                self._searched_at = index
                self.search = text
                return True
        return False

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert:
            return False
        typed = self._current_search()
        if event.matches("backspace"):
            if not typed:
                return False
            self.search = typed[:-1]
            self._searched_at = self.cursor
            return True
        if event.is_printable and event.char and not event.ctrl and not event.alt:
            if not self.search_for(typed + event.char):
                # Nothing begins so: the character is ignored, the search kept.
                self.search = typed
                self._searched_at = self.cursor
            return True
        return await super().on_key(event)

    def cursor_position(self) -> tuple[int, int] | None:
        """``SetCursor``: after what has been typed, on the cursor's row."""
        if not self.focused or not self.items:
            return None
        y = self.inset + self.header + self.cursor - self.scroll
        if not 0 <= y - self.inset - self.header < self.rows:
            return None
        x = self.inset + 1 + len(self._current_search())
        return min(x, max(0, self.width - 2)), y


class FileInfoPane(Widget):
    """``TFileInfoPane``: the path being listed, and the entry last focused.

    Two lines, as ``TFileInfoPane.Draw`` wrote them: the directory with its
    wildcard, then ``' %-12s %-10s  %s'`` -- the name, the size or the word
    *Directory*, and the date and time in DN's ``MakeDate`` form, a two-digit
    year.  It keeps the last entry while the keyboard is elsewhere, as the
    pane kept the last ``cmFileFocused`` record.
    """

    #: The directory and wildcard, ``FExpand``-ed.
    path: str = reactive("")
    #: The entry last focused in either list, or None.
    item: FileItem | None = reactive(None)

    #: How the date and time are written.
    DATE_FORMAT = "%d-%m-%y %H:%M"

    def lines(self) -> tuple[str, str]:
        item = self.item
        if item is None:
            return " " + self.path, ""
        size = tr("Directory") if item.is_dir else str(item.size)
        when = time.strftime(self.DATE_FORMAT, time.localtime(item.mtime)) if item.mtime else ""
        return " " + self.path, f" {item.name:<12} {size:<10}  {when}"

    def render(self, surface: Surface) -> None:
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        for y, text in enumerate(self.lines()[: self.height]):
            surface.draw_text(0, y, text, style, self.width)
