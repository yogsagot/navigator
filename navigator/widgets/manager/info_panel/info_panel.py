"""Ctrl+L: what DOS Navigator's ``TDiskInfo`` showed in the passive panel's place.

The lines are :func:`navigator.lib.system.diskinfo.lines`; the disk and the machine are
read on a thread (:func:`navigator.lib.system.diskinfo.gather`) whenever the directory
it describes changes or is re-read (``cmRereadInfo``), and what was read last
stays up meanwhile.  The entry under the active panel's cursor is followed
apart (:meth:`InfoPanel.show_file`), its stat read on the same thread, so
moving the cursor never reads the disk's facts again; a media file's
details follow as a second read (:mod:`navigator.lib.system.mediainfo`).  A line is centred, as
``Wrt`` centred it, but for the information file's, which start at the left
(the current file's are a table, padded to one width to centre as a block);
``~`` runs are drawn in the ``highlight`` part, and the rules across the
frame's colour.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from navkit.bidi import display_width, fit_cells
from navkit import glyphs as glyphs_module
from navkit.glyphs import BOX_CHARSETS
from navkit.i18n import tr, tr_n
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget

from navml.background import Background, Outcome

from navigator.lib.system import diskinfo, mediainfo
from navigator.settings import SETTINGS

#: Where a box charset keeps its horizontal line.
HORIZONTAL = 4

#: Where the panel reads the disk and the machine.
_READER = Background("nav-info", workers=1)


class InfoPanel(Widget):
    """Ctrl+L: the active panel's directory, its file system and the machine."""

    border = StyleProperty("single", values=tuple(BOX_CHARSETS))
    parts = ("title", "highlight")

    #: The directory described, and the entries it lists (for the totals).
    directory: Any = reactive(None)
    entries: Any = reactive(())
    #: What the last read found (:class:`navigator.lib.system.diskinfo.DiskFacts`).
    facts: Any = reactive(None)
    #: The entry under the active panel's cursor, and what its stat found
    #: (:class:`navigator.lib.system.diskinfo.FileFacts`, None until read).
    entry: Any = reactive(None)
    file_facts: Any = reactive(None)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.can_focus = True
        #: Columns left clear at each end of the top frame, as a panel's.
        self.title_margin = 0
        self._wanted: Path | None = None
        self._wanted_file: Any = None

    #: For a place on another drive: what its drive says of itself
    #: (``Drive.describe``), shown in place of the disk's and the memory's.
    described: Any = reactive(None)

    def show(self, directory: Any, entries: Any, *, reread: bool = True) -> None:
        """Describe *directory*, listing *entries*; *reread* reads the disk
        again even if it is the one already described.  A
        :class:`~navigator.lib.drives.Location` on another drive is described
        by its drive, on a thread."""
        from navigator.lib.drives import Location

        if isinstance(directory, Location) and not directory.is_local:
            self._show_elsewhere(directory, entries)
            return
        if isinstance(directory, Location):
            directory = directory.local
        self.described = None
        directory = Path(directory)
        same = directory == self.directory
        self.entries = tuple(entries)
        if same and not reread:
            return
        self.directory = directory
        self._wanted = directory
        _READER.run(self, diskinfo.gather, directory,
                    done=lambda outcome, d=directory: self._read(d, outcome))

    def show_file(self, entry: Any, location: Any) -> None:
        """Describe *entry*, the file under the cursor, found at *location*
        (a :class:`~navigator.lib.drives.Location`, or None for no entry):
        its stat is read on a thread for a local one, its type guessed from
        its name for any."""
        if entry is self.entry and location == self._wanted_file:
            return
        self.entry, self.file_facts = entry, None
        self._wanted_file = location
        if entry is None or entry.name == "..":
            return
        path = Path(location.local) if location is not None and location.is_local else None

        def current() -> bool:
            return self._wanted_file == location and self.entry is entry

        def described(facts: diskinfo.FileFacts, outcome: Outcome) -> None:
            if not current():
                return
            try:
                media = outcome.result()
            except Exception:
                media = None
            if media is not None:
                self.file_facts = dataclasses.replace(facts, media=media)

        def answered(outcome: Outcome) -> None:
            if not current():
                return
            try:
                facts = outcome.result()
            except OSError:
                facts = diskinfo.FileFacts()
            self.file_facts = facts
            # A media file's details next, apart: the table does not wait
            # for ffprobe, and a file the cursor has left is not read.
            if path is not None and SETTINGS.drive_info.media_info and mediainfo.kind(facts.mime):
                _READER.run(self, mediainfo.read, path, facts.mime, current,
                            done=lambda outcome: described(facts, outcome))

        _READER.run(self, diskinfo.stat_file, path, entry.name, done=answered)

    def _show_elsewhere(self, location: Any, entries: Any) -> None:
        from navigator.lib.drives import drive_of

        self.entries = tuple(entries)
        self._wanted = location

        def ask() -> tuple[str, list[tuple[str, str]]]:
            drive = drive_of(location)
            return drive.get_dir(location), drive.describe()

        def answered(outcome: Outcome) -> None:
            if self._wanted != location:
                return
            try:
                name, described = outcome.result()
            except OSError:
                name, described = str(location), []
            self.directory, self.facts, self.described = name, diskinfo.DiskFacts(), described

        _READER.run(self, ask, done=answered)

    def _read(self, directory: Path, outcome: Outcome) -> None:
        if self._wanted != directory:
            return
        try:
            self.facts = outcome.result()
        except OSError:
            self.facts = diskinfo.DiskFacts()

    def lines(self) -> list[tuple[str, bool]]:
        if self.directory is None:
            return []
        out = diskinfo.lines(self.directory, self.entries, self.facts, SETTINGS.drive_info,
                             self.entry, self.file_facts)
        if self.described:
            if out:
                out.append(("", True))
            out.append(("\0" + tr("Connection"), False))
            out += [(f"{tr(what)}: ~{value}~", False) for what, value in self.described]
        return out

    def tooltip_at(self, x: int, y: int) -> str:
        """A line's whole text where the panel cut it, and the memory's exact
        bytes where the line rounds them to K -- what ``TDiskInfo`` left out."""
        lines = self.lines()[: max(0, self.height - 2)]
        row = y - 1
        if not 0 < x < self.width - 1 or not 0 <= row < len(lines):
            return super().tooltip_at(x, y)
        text, _centred = lines[row]
        if text.startswith("\0"):
            text = text[1:]
        facts = self.facts
        if facts is not None and facts.memory_total is not None and \
                text == tr("~{n:,}~K bytes total memory").format(n=facts.memory_total >> 10):
            return tr_n("{count} byte of memory in all", "{count} bytes of memory in all",
                        facts.memory_total, count=f"{facts.memory_total:,}")
        plain = text.replace("~", "").rstrip()
        return plain if len(plain) > self.width - 2 else super().tooltip_at(x, y)

    def render(self, surface: Surface) -> None:
        if self.width < 2 or self.height < 2:
            return
        surface.draw_box(0, 0, self.width, self.height, self.style,
                         charset=self.box_charset(), fill=" ")
        title = f" {tr('Information')} "
        if display_width(title) <= self.width - 4 - 2 * self.title_margin:
            surface.draw_text((self.width - display_width(title)) // 2, 0, title, self.part_style("title"))
        inner = self.width - 2
        for row, (text, centred) in enumerate(self.lines()[: self.height - 2]):
            y = row + 1
            if text.startswith("\0"):
                name = f" {text[1:]} " if text[1:] else ""
                line = glyphs_module.charset("single", self.glyphs)[HORIZONTAL] * inner
                start = max(0, (inner - display_width(name)) // 2)
                line = line[:start] + name + line[start + display_width(name):inner]
                surface.draw_text(1, y, line, self.style, inner)
                # Joined to the frame at both ends, ``├``/``┤`` (``╟``/``╢``
                # on a double one), as a panel's info divider is.
                left_tee, right_tee = self.box_joins()[:2]
                surface.set_cell(0, y, left_tee, self.style)
                surface.set_cell(self.width - 1, y, right_tee, self.style)
                continue
            plain = text.replace("~", "")
            x = 1 + max(0, (inner - display_width(plain)) // 2) if centred else 1
            bright = False
            for piece in text.split("~"):
                if piece:
                    style = self.part_style("highlight") if bright else self.style
                    room = 1 + inner - x
                    if room <= 0:
                        break
                    piece = fit_cells(piece, room)
                    surface.draw_text(x, y, piece, style, room)
                    x += display_width(piece)
                bright = not bright
