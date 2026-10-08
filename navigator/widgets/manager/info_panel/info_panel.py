"""Ctrl+L: what DOS Navigator's ``TDiskInfo`` showed in the passive panel's place.

The lines are :func:`navigator.diskinfo.lines`; the disk and the machine are
read on a thread (:func:`navigator.diskinfo.gather`) whenever the directory
it describes changes or is re-read (``cmRereadInfo``), and what was read last
stays up meanwhile.  A line is centred, as ``Wrt`` centred it, but for the
information file's, which start at the left; ``~`` runs are drawn in the
``highlight`` part, and the file's rule across the frame's colour.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit import glyphs as glyphs_module
from navkit.glyphs import BOX_CHARSETS
from navkit.i18n import tr
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget

from navml.background import Background, Outcome

from navigator import diskinfo
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
    #: What the last read found (:class:`navigator.diskinfo.DiskFacts`).
    facts: Any = reactive(None)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.can_focus = True
        #: Columns left clear at each end of the top frame, as a panel's.
        self.title_margin = 0
        self._wanted: Path | None = None

    def show(self, directory: Path, entries: Any, *, reread: bool = True) -> None:
        """Describe *directory*, listing *entries*; *reread* reads the disk
        again even if it is the one already described."""
        directory = Path(directory)
        same = directory == self.directory
        self.entries = tuple(entries)
        if same and not reread:
            return
        self.directory = directory
        self._wanted = directory
        _READER.run(self, diskinfo.gather, directory,
                    done=lambda outcome, d=directory: self._read(d, outcome))

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
        return diskinfo.lines(self.directory, self.entries, self.facts, SETTINGS.drive_info)

    def render(self, surface: Surface) -> None:
        if self.width < 2 or self.height < 2:
            return
        surface.draw_box(0, 0, self.width, self.height, self.style,
                         charset=self.box_charset(), fill=" ")
        title = f" {tr('Information')} "
        if len(title) <= self.width - 4 - 2 * self.title_margin:
            surface.draw_text((self.width - len(title)) // 2, 0, title, self.part_style("title"))
        inner = self.width - 2
        for row, (text, centred) in enumerate(self.lines()[: self.height - 2]):
            y = row + 1
            if text.startswith("\0"):
                name = f" {text[1:]} "
                line = glyphs_module.charset("single", self.glyphs)[HORIZONTAL] * inner
                start = max(0, (inner - len(name)) // 2)
                line = (line[:start] + name + line[start + len(name):])[:inner]
                surface.draw_text(1, y, line, self.style, inner)
                continue
            plain = text.replace("~", "")
            x = 1 + max(0, (inner - len(plain)) // 2) if centred else 1
            bright = False
            for piece in text.split("~"):
                if piece:
                    style = self.part_style("highlight") if bright else self.style
                    room = 1 + inner - x
                    if room <= 0:
                        break
                    surface.draw_text(x, y, piece[:room], style, room)
                    x += len(piece[:room])
                bright = not bright
