"""What ``file_dialog.nml`` does: DOS Navigator's ``TFileDialog``.

``GetFileNameDialog`` (``DNSTDDLG.PAS``) is the whole contract: a title, what
the name line is called, a history, and back comes a full path or nothing.
:meth:`FileDialog.execute` answers the path as a string, or None.

**OK is ``Valid(cmFileOpen)``.**  The name line is read as ``GetFileName``
read it -- relative to the directory listed -- and then:

* a wildcard lists that directory through it, and the dialog stays up;
* a directory is listed, and the dialog stays up;
* a name in a directory that exists closes the dialog with it;
* anything else is said (``erInvalidDrive``, ``erInvalidFileName``).

**The lists drive the rest** -- ``cmFileFocused``, which DN broadcast and an
effect stands for here: whichever list holds the keyboard puts its entry in
the name line (a directory as itself, ``/`` and the wildcard) and in the info
pane.  The name line is left alone while it has the keyboard, as
``TFileInputLine`` ignored the broadcast while selected.

**Keys**: Left and Right move between the controls whenever the name line
does not have the keyboard, and Tab skips an empty *Files* list, as
``TFileDialog.HandleEvent`` arranged.  Enter or a double click in a list is
OK.  What is recorded in the history is the full path, as ``HistoryAdd``
recorded ``FExpand(S)``.

Departures: no drives, no DOS name-and-extension completion from the
wildcard, and ``*`` rather than ``*.*`` for "everything", which on POSIX
would ask for a dot.  The directory listed first is the caller's, where DN's
was its current one.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from navkit.events import Event, KeyEvent
from navkit.reactive import effect
from navkit.widget import Widget

from navml.history import HISTORY
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.file_list import scan

#: What lists everything: DN's ``x_x``, ``*.*``, less the dot.
EVERYTHING = "*"

INVALID_DIRECTORY = "Invalid drive or directory."
INVALID_FILE_NAME = "Invalid file name."


def is_wild(name: str) -> bool:
    """``IsWild``: whether *name* is a pattern rather than a name."""
    return any(char in name for char in "*?[")


class FileDialog(Dialog):
    """``TFileDialog``: a file's name, typed or picked from the directory it is in."""

    def __init__(
        self,
        *,
        title: str | None = None,
        label: str = "~N~ame",
        history_id: str = "",
        directory: Path | str | None = None,
        wildcard: str = EVERYTHING,
        hidden: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        # Dialog's bottom row and message are not in this layout.
        self.row.visible = False
        self.message.visible = False
        if title is not None:
            self.title = title
        self.caption.text = label
        self.target.history_id = history_id
        #: The history the full path is recorded in.
        self.history_id = history_id
        #: Whether dot-files are listed: DN's ``ossShowHidden``.
        self.hidden = hidden
        #: The directory listed, and the wildcard its files are listed through.
        self.directory = Path(os.path.abspath(directory or os.getcwd()))
        self.wildcard = wildcard
        # ``FileName^.Data^ := WildCard``, selected as a focused line's text
        # is, so a name typed replaces it.
        self.target.value = wildcard
        self.target.entry.select_all()
        self.read_directory()

    def mounted(self) -> None:
        super().mounted()
        effect(self, FileDialog._follow_lists)

    # -- the lists -----------------------------------------------------------------

    def read_directory(self) -> None:
        """``ReadDirectory``: both lists again, and the path in the info pane."""
        files, dirs = scan(self.directory, self.wildcard, self.hidden)
        self.files.show(files)
        self.dirs.show(dirs)
        self.info.path = os.path.join(str(self.directory), self.wildcard)

    def _follow_lists(self) -> None:
        """``cmFileFocused``: the focused list's entry, in the line and the pane."""
        for listing in (self.files, self.dirs):
            if listing.focused:
                item = listing.selected
                if item is not None:
                    self.info.item = item
                    self.target.value = (
                        f"{item.name}/{self.wildcard}" if item.is_dir else item.name
                    )
                return

    def focusable(self) -> list[Widget]:
        """The tab order, less an empty *Files* list, which ``Select`` refused."""
        return [w for w in super().focusable() if w is not self.files or self.files.items]

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.pick, self.abandon, self.helper)

    async def on_key(self, event: KeyEvent) -> bool:
        """Left and Right move between the controls, but not out of the name line."""
        app = self.application
        if (
            app is not None
            and not self.target.entry.focused
            and event.key in ("left", "right")
            and not (event.ctrl or event.alt or event.shift)
        ):
            app.focus_next(reverse=event.key == "left")
            return True
        return await super().on_key(event)

    # -- OK ------------------------------------------------------------------------

    def file_name(self) -> Path:
        """``GetFileName``: the name line as a full path, relative to the directory listed."""
        text = self.target.value.strip()
        return Path(os.path.normpath(self.directory / Path(text).expanduser()))

    def valid(self) -> bool:
        """``Valid(cmFileOpen)``: a file closes the dialog; a directory or a wildcard
        is listed instead, and the dialog stays up."""
        path = self.file_name()
        text = self.target.value.strip()
        if text and is_wild(path.name):
            if not path.parent.is_dir():
                self._say(INVALID_DIRECTORY)
                return False
            self._change_to(path.parent, path.name)
            return False
        if path.is_dir():
            self._change_to(path, self.wildcard)
            return False
        if path.parent.is_dir():
            return True
        self._say(INVALID_FILE_NAME)
        return False

    def _change_to(self, directory: Path, wildcard: str) -> None:
        """List *directory* through *wildcard*; the keyboard to the files, or kept
        on the directories if it was there or there are no files."""
        in_dirs = self.dirs.focused
        self.directory = directory
        self.wildcard = wildcard
        self.read_directory()
        if in_dirs or not self.files.items:
            if self.dirs.items:
                self.info.item = self.dirs.items[0]
        else:
            self.files.focus()

    def _say(self, message: str) -> None:
        """``ErrMsg``, and the name line to be typed again."""
        app = self.application
        self.target.entry.focus()
        if app is not None:
            self.spawn(Dialog(title="Error", prompt=message, buttons="ok").execute(app))

    def record_history(self) -> None:
        """``HistoryAdd(HistoryID, FExpand(S))``: the full path, not what was typed."""
        if self.history_id:
            HISTORY.add(self.history_id, str(self.file_name()))

    def accept(self) -> str:
        return str(self.file_name())

    async def on_pick_click(self, event: Event) -> bool:
        if not self.valid():
            return True
        self.record_history()
        self.close(self.accept())
        return True

    async def on_files_chosen(self, event: Any) -> bool:
        """Enter or a double click on a file: OK."""
        return await self.on_pick_click(event)

    async def on_dirs_chosen(self, event: Any) -> bool:
        """Enter or a double click on a directory: OK, which lists it."""
        return await self.on_pick_click(event)
