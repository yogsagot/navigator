"""The handlers behind ``edit_window.nml``: saving, and closing with a question.

The keys that *edit* are ``FileEditor``'s own and reach it first along the
focus path; what is here is what concerns the file as a whole.

**Closing asks about a changed text**, as ``TFileEditor.Valid`` did on
``cmClose``: *File %s was modified. Save?* with Yes, No and Cancel.  The
question is asked from :meth:`ask_to_close`, which the window's close runs as a
task -- a handler that waited on the dialog would hold the loop the dialog's
keys arrive on -- so Esc, Alt+F3, the close icon, Window > Close all and
Alt+X all ask it the same way.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from navkit.events import Event
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.scroll_bar import ScrollEvent
from navml.widgets.window import Window

from navigator.widgets.editor.commands import SaveText


@dataclass(frozen=True, slots=True)
class FileSaved(Event):
    """A file was written: the panels showing its directory re-read it.

    DN's ``FileChanged``, which broadcast ``cmRereadDir`` for the directory.
    """

    path: Path


class EditWindow(Window):
    """A file in an editor window: F4, and File > Edit.

    Raises ``OSError`` from the constructor if *path* cannot be read, so the
    caller can say so before a window that shows nothing is opened.  With
    *new*, a file that does not exist yet is an empty text that saving creates.
    """

    emits = (FileSaved,)

    def __init__(self, path: Path | str, *, new: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.editor.open(path, new=new)
        # `dlEditTitle': ``Edit - `` and the whole name.
        self.title = f"Edit - {self.editor.path}"

    def take_keyboard(self) -> None:
        # Not from ``mounted()``: that runs inside ``Desktop.open``'s ``add()``,
        # before ``activate`` has saved which panel the window below had, so
        # closing this one would hand the keyboard to the left panel.
        self.editor.focus()

    def list_name(self) -> str:
        """Window > List's line: the title, which already says ``Edit - ``."""
        return f"Edit - {self.editor.path}"

    # -- saving ------------------------------------------------------------------

    async def on_save_text(self, event: SaveText) -> bool:
        """F2: ``cmSaveText``.  A failure is said, and the text stays changed."""
        self.spawn(self.save())
        return True

    async def save(self) -> bool:
        """Write the file; say why not if it cannot be.  True when written."""
        try:
            self.editor.save()
        except OSError as error:
            await Dialog(
                title="Error",
                prompt=f"Cannot write {self.editor.path}: {error.strerror or error}",
                buttons="ok",
            ).execute(self.application)
            return False
        await self.emit(FileSaved(self.editor.path))
        return True

    # -- closing -----------------------------------------------------------------

    def must_ask(self) -> bool:
        return self.editor.modified

    async def ask_to_close(self) -> bool:
        """``dlQueryModified``: save, lose, or stay open."""
        name = self.editor.path.name if self.editor.path else "Untitled"
        answer = await Dialog(
            title="Warning",
            prompt=f"File {name} was modified. Save?",
            buttons="yes-no-cancel",
        ).execute(self.application)
        if answer is None:
            return False
        if answer is True:
            return await self.save()
        return True

    # -- the scroll bars -----------------------------------------------------------

    async def on_vbar_scroll(self, event: ScrollEvent) -> bool:
        """The vertical bar was worked: its value is the cursor's line."""
        editor = self.editor
        editor.buffer.seal()
        editor._go_column(event.value, editor.col)
        return True

    async def on_hbar_scroll(self, event: ScrollEvent) -> bool:
        editor = self.editor
        editor.buffer.seal()
        editor._go_column(editor.line, event.value)
        return True
