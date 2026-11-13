"""What the Panel's mixins share: module-level helpers of
:mod:`navigator.widgets.manager.panel.panel`, which re-exports the public ones.
"""

from __future__ import annotations

import concurrent.futures
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from navkit.bidi import display_width
from navkit.events import Event
from navkit import glyphs as glyphs_module
from navkit.screen import char_width

from navigator.lib.appearance import filetypes
from navigator.lib.drives import Location, drive_of
from navigator.lib.drives.listing import DirEntry
from navigator.settings import PanelDefaultsData


@dataclass(frozen=True, slots=True)
class ExecuteFile(Event):
    """Enter on an executable: run it.

    Raised by the panel, which knows the file and not the shell, and taken by
    whoever runs commands -- ``Shell``, in Navigator.  DOS Navigator ran an
    ``.EXE``, ``.COM`` or ``.BAT`` the same way, through ``cmExecString``;
    here "executable" is what the file system says.
    """

    path: Path | Location


@dataclass(frozen=True, slots=True)
class OpenFile(Event):
    """Enter on a file that is not itself a program: whatever its name says
    to run, which ``Shell`` reads from ``extensions.ini`` -- DOS Navigator's
    ``_GotoExt``, ``cmExecFile`` and ``DN.EXT``."""

    path: Path | Location


#: What ends a name cut short to fit its column, by default -- three dots, the
#: ASCII tier's; a panel passes its own (``Panel.ellipsis``), ``…`` above it.
ELLIPSIS = "..."


def text_width(text: str) -> int:
    """The cells *text* takes on the terminal (an Arabic lam-alef one)."""
    return display_width(text)


def skip_cells(text: str, cells: int) -> str:
    """*text* less its first *cells* cells; half a wide character is a blank."""
    if cells <= 0:
        return text
    skipped = 0
    for index, char in enumerate(text):
        if skipped >= cells:
            return text[index:]
        skipped += char_width(char)
        if skipped > cells:
            return " " + text[index + 1 :]
    return ""


def fit_text(text: str, room: int, marker: str = ELLIPSIS) -> str:
    """*text* in *room* cells, ending in *marker* if it had to be cut.

    With no room for the marker and a character beside it, just cut.
    """
    if text_width(text) <= room:
        return text
    size = text_width(marker)
    keep = room - size if room > size else room
    used = 0
    for index, char in enumerate(text):
        used += char_width(char)
        if used > keep:
            head = text[:index]
            break
    else:
        head = text
    return head + marker if room > size else head


def window_text(text: str, offset: int, room: int, marker: str = ELLIPSIS) -> str:
    """Cells *offset* to *offset* + *room* of *text*, marked where it is cut.

    Scrolled at all, the first cells of the window are *marker*
    rather than a marker pushed in front, so the window does not move -- a
    name shows its end exactly when it would have without the marker.  A
    name scrolled wholly out of the window leaves the marker alone, saying
    there is a name there.  With no room for the marker and a character
    beside it, the text is just cut.
    """
    size = text_width(marker)
    if offset <= 0 or room <= size:
        return fit_text(skip_cells(text, offset), room, marker)
    return marker + fit_text(skip_cells(text, offset + size), room - size, marker)

#: The threads directories are read on.  More than one, so a read stuck on a
#: dead mount does not hold up the other panel's.
_SCANNER = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="nav-scan")

#: The threads other drives are read on: their own, so a server that stops
#: answering holds up none of the local panels' reads.
_REMOTE_SCANNER = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="nav-scan-remote")


def _scanner_for(location: Location) -> concurrent.futures.ThreadPoolExecutor:
    return _SCANNER if location.is_local else _REMOTE_SCANNER


@dataclass(frozen=True)
class ListingFacts:
    """What a panel's footer says of its whole listing -- made in one walk
    when the listing changes (``Panel._listing_facts``), so a cursor move
    reads them rather than walking a hundred thousand entries again.  A
    file's size never changes in place (only a counted directory's does, and
    *Totals* counts files), so the listing alone is what they follow."""

    has_entries: bool = False
    files: int = 0
    file_bytes: int = 0
    any_trashed: bool = False
    any_link: bool = False

    @classmethod
    def of(cls, items: Iterable[DirEntry]) -> ListingFacts:
        has_entries = any_trashed = any_link = False
        files = file_bytes = 0
        for item in items:
            if item.name != "..":
                has_entries = True
            if not item.is_dir:
                files += 1
                file_bytes += item.size
            if item.trashed is not None:
                any_trashed = True
            if item.is_link:
                any_link = True
        return cls(has_entries, files, file_bytes, any_trashed, any_link)


def _answers_here(location: Location) -> bool:
    """Whether *location*'s drive lists without a round trip
    (``Drive.quick_listing``), so a read is worth the panel's grace wait."""
    try:
        return drive_of(location).quick_listing
    except OSError:  # DriveGone: the read will say so, at once
        return False


def _is_read_only(location: Location) -> bool:
    """Whether *location* is on the disk, on a file system mounted read-only:
    a disk image Enter mounted, a CD, a ``ro`` mount.  Its title says so, so
    that a refused edit or copy into it is no surprise.  Another drive's
    directories are its own to refuse."""
    if not location.is_local:
        return False
    try:
        return bool(os.statvfs(location.local).f_flag & os.ST_RDONLY)
    except OSError:
        return False

#: How long a change on disk waits for the ones after it before the panel
#: re-reads (*Auto refresh panels*): a copy of a thousand files is a handful
#: of re-reads, not a thousand, and one file is still there at once.
REFRESH_DELAY = 0.3


#: DN's sort modes (``psm*``, ``SortMode``), named as the *New Manager
#: defaults* name them; "type" is DN's *Group*.
SORT_MODES: tuple[str, ...] = PanelDefaultsData.SORT_BY

#: Which way each sort mode runs unreversed: ``True`` ascending.  Size and
#: time go largest and newest first (:func:`order_entries`); *Unsorted* has
#: no direction.
SORT_ASCENDS = {"name": True, "extension": True, "size": False, "time": False,
                "attributes": True, "owner": True, "type": True}


def _archive_file(entry: Any) -> bool:
    """A file Shift+F2 extracts -- the *archive* file type's -- as the
    right-click menu offers *Extract archive* on it (``Manager`` decides)."""
    return (entry is not None and not entry.is_dir and entry.name != ".."
            and filetypes.group_of(entry.name) == "archive")


def direction_arrow(mode: str, reverse: bool, glyphs: int) -> str:
    """``↑`` where *mode* (*reverse* or not) runs ascending, ``↓`` descending
    -- ``^``/``v`` at the ASCII *glyphs* tier -- and nothing for *Unsorted*."""
    if mode not in SORT_ASCENDS:
        return ""
    ascending = SORT_ASCENDS[mode] != reverse
    if glyphs <= glyphs_module.GLYPHS_ASCII:
        return "^" if ascending else "v"
    return "\u2191" if ascending else "\u2193"


def command_line_text(widget: Any) -> str:
    """What the command line of the screen *widget* is on holds; ``""`` with none."""
    while widget is not None:
        line = getattr(widget, "command_line", None)
        if line is not None:
            return line.value
        widget = widget.parent
    return ""


def human_size(size: int) -> str:
    """*size* bytes as ``df -h`` puts them: ``977K``, ``9.5G``, ``384G`` --
    one decimal below ten, the size column's K/M/G/T, powers of 1024.  Bytes
    under a kilobyte keep their digits."""
    value = float(size)
    for unit in ("", "K", "M", "G", "T"):
        if value < 1023.5 or unit == "T":
            break
        value /= 1024
    if not unit:
        return f"{size:,}"
    return f"{value:.1f}{unit}" if value < 9.95 else f"{value:.0f}{unit}"
