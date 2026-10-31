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

from navkit.reactive import effect, unbind

from navml.background import Background, Outcome
from navml.widgets.dialog.file_dialog import FileDialog

#: Where the palette under the cursor is read.
_READER = Background("navigator-palette-preview", workers=1)

#: The dialog's size: small enough to leave the previewed screen in sight.
_SIZE = (59, 20)
#: The columns the base's controls take, as its own are laid out --
#: *Directories* left of *Files* -- but fixed: the *Files* list holds a
#: theme's name, the buttons stand right of the lists.
_DIRS = (3, 17)
_FILES = (22, 25)
_BUTTONS = 47


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _place(widget: Any, **values: Any) -> None:
    """*values* given to *widget*'s attributes, each binding the base gave it taken back first."""
    for name, value in values.items():
        unbind(widget, getattr(type(widget), name))
        setattr(widget, name, value)


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
        width, height = _SIZE
        _place(self, modal_width=width, modal_height=height)
        _place(self.dirs, x=_DIRS[0], width=_DIRS[1], height=9)
        _place(self.dirs_caption, x=_DIRS[0] - 1, width=_DIRS[1])
        _place(self.files, x=_FILES[0], width=_FILES[1], height=9)
        _place(self.files_caption, x=_FILES[0] - 1, width=_FILES[1])
        _place(self.target, width=_BUTTONS - 4)
        _place(self.caption, width=_BUTTONS - 6)
        for button in self.buttons_row:
            _place(button, x=_BUTTONS)
        _place(self.info, y=17, width=width - 2)

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
