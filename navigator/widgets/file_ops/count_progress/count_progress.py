"""What Alt+G's counting box writes, and what its one button means."""

from __future__ import annotations

from typing import Any

from navkit.bidi import display_width, pad_cells
from navkit.i18n import tr
from navkit.reactive import unbind

from navml.widgets.dialog.button import Button
from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.file_ops.copy_progress.copy_progress import fit_path
from navigator.widgets.manager.panel.panel import human_size

#: The least room between one column and the next.
GAP = 2

#: The box's narrowest, with one directory and with several -- the second
#: leaving the path being counted some room.
NARROWEST = 50
NARROWEST_SEVERAL = 60


class CountProgress(Dialog):
    """*Counting directory length*: where it is, what it has met there and in
    all, and *Cancel*."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        unbind(self.ok, Button.text)
        self.ok.text = tr("~C~ancel")

    def box_width(self, screen: int, several: bool, *counts: int) -> int:
        """As wide as the table needs, and no narrower than :data:`NARROWEST`:
        the box grows as the counts gain digits -- up to *screen*, the width
        it is shown on (0 before it is), where a row loses its label instead."""
        narrowest = NARROWEST_SEVERAL if several else NARROWEST
        width = max(narrowest, self.table_width(several, *counts) + 6)
        return min(width, screen) if screen > 0 else width

    def fit(self, path: str) -> str:
        """*path*, cut from the left to fit the row."""
        return fit_path("", path, self.width - 8)

    def table_width(self, several: bool, here_size: int, size: int, here_files: int,
                    files: int, here_directories: int, directories: int) -> int:
        """How wide the table is with nothing to spare, which the box grows to."""
        rows, here_width, total_width = self._rows(several, here_size, size, here_files, files,
                                                   here_directories, directories)
        label_width = max(display_width(label) for label, _, _ in rows) + GAP
        return label_width + (here_width + GAP if several else 0) + total_width

    def counts(self, width: int, several: bool, here_size: int, size: int, here_files: int,
               files: int, here_directories: int, directories: int) -> str:
        """The table, *width* cells to a row: a heading and *This directory*
        beside *Total* when there are *several*, else the total alone (the
        two are one).  Bytes also say it short, ``9,876,543 (9.4M)``."""
        rows, here_width, total_width = self._rows(several, here_size, size, here_files, files,
                                                   here_directories, directories)
        counts = (here_width + GAP if several else 0) + total_width
        lines = []
        for label, here, total in rows:
            line = pad_cells(label, max(display_width(label) + GAP, width - counts))
            if several:
                line += pad_cells(here, here_width, "right") + " " * GAP
            line += pad_cells(total, total_width, "right")
            while display_width(line) > max(0, width):
                line = line[1:]
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def _rows(several: bool, here_size: int, size: int, here_files: int, files: int,
              here_directories: int, directories: int) -> tuple[list[tuple[str, str, str]], int, int]:
        """The table's rows as (label, this directory, total), and how wide
        each count column has to be."""
        rows = [
            (tr("Bytes"), byte_count(here_size), byte_count(size)),
            (tr("Files"), f"{here_files:,}", f"{files:,}"),
            (tr("Directories"), f"{here_directories:,}", f"{directories:,}"),
        ]
        if several:
            rows.insert(0, ("", tr("This directory"), tr("Total")))
        else:
            rows = [(label, "", total) for label, _, total in rows]
        here_width = max(display_width(here) for _, here, _ in rows)
        total_width = max(display_width(total) for _, _, total in rows)
        return rows, here_width, total_width

    def accept(self) -> Any:
        """*Cancel* answers what Esc does: nothing, which stops the count."""
        return None


def byte_count(size: int) -> str:
    """*size* in bytes, and in brackets as the panel's free space says it."""
    if size < 1024:
        return f"{size:,}"
    return f"{size:,} ({human_size(size)})"
