"""What ``palette_file_dialog.nml`` does: a file box that previews palettes.

While *Preview palette* is ticked, the file under the *Files* cursor is read
on a thread and handed to *preview* as ``(path, text)``; unticking it hands
over ``None``, which means the palette as it was.  What *preview* does with
it is the caller's -- Options > Load palette paints it, and puts the screen
back when the box is cancelled.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from navkit.reactive import effect

from navml.background import Background, Outcome
from navml.widgets.dialog.file_dialog import FileDialog

#: Where the palette under the cursor is read.
_READER = Background("navigator-palette-preview", workers=1)

#: The columns the base's controls take, widened: the *Files* list holds a
#: theme's name, the buttons move right of the wider lists.
_FILES = (3, 25)
_DIRS = (29, 17)
_BUTTONS = 47


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class PaletteFileDialog(FileDialog):
    """``FileDialog`` over palettes, *preview* told of the one under the cursor."""

    def __init__(self, *, preview: Callable[[tuple[Path, str] | None], None] | None = None,
                 **kwargs: Any) -> None:
        #: Counts the reads asked for, so one overtaken by another is dropped.
        self._previewing = 0
        #: Whether *preview* was last given a palette, so unticking says so once.
        self._shown = False
        super().__init__(**kwargs)
        self.preview_palette = preview
        self.files.x, self.files.width = _FILES
        self.files_caption.x, self.files_caption.width = _FILES[0] - 1, _FILES[1]
        self.dirs.x, self.dirs.width = _DIRS
        self.dirs_caption.x, self.dirs_caption.width = _DIRS[0] - 1, _DIRS[1]
        self.target.width = _BUTTONS - 4
        self.caption.width = _BUTTONS - 6
        for button in self.buttons_row:
            button.x = _BUTTONS
        self.info.y = 17
        self.info.width = self.modal_width - 2

    def mounted(self) -> None:
        super().mounted()
        effect(self, PaletteFileDialog._follow_cursor)

    def _follow_cursor(self) -> None:
        """The palette under the *Files* cursor, read and shown, while ticked."""
        ticked = self.preview.chosen(0)
        item = self.files.selected
        self._previewing += 1
        reading = self._previewing
        if self.preview_palette is None:
            return
        if not ticked or item is None or item.is_dir:
            if self._shown and not ticked:
                self._shown = False
                self.preview_palette(None)
            return
        path = self.directory / item.name

        def done(outcome: Outcome) -> None:
            if reading != self._previewing or self.preview_palette is None:
                return
            try:
                text = outcome.result()
            except (OSError, UnicodeError):
                return  # one that cannot be read is not shown: the last one stays
            self._shown = True
            self.preview_palette((path, text))

        _READER.run(self, _read, path, done=done)
