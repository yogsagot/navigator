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

from navigator.file_history import place_window, window_values
from navigator.models.edit_record import EditRecord
from navigator.settings import SETTINGS
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

    # -- the File Edit History -------------------------------------------------

    def remember_history(self) -> None:
        """``StoreEditInfo``: this file's record, as the editor is now."""
        editor = self.editor
        if not SETTINGS.interface.track_editing or editor.path is None:
            return
        EditRecord.store(
            editor.path,
            **window_values(self),
            line=editor.line,
            col=editor.col,
            top=editor.top,
            left=editor.left,
            overwrite=editor.overwrite,
            vertical_blocks=editor.vertical_blocks,
        )

    def recall_history(self) -> None:
        """``EditFile``: put the window and the editor back as the record says.

        Called once the window is on its desktop.  A file with no record gets
        one now.  The rectangle, scroll and cursor come back only under
        *Store editor position*.  A cursor past the end of a text that has
        since got shorter lands on its last line, which ``ScrollTo`` and
        ``Pos`` clamped too.
        """
        editor = self.editor
        if not SETTINGS.interface.track_editing or editor.path is None:
            return
        record = EditRecord.find(editor.path)
        if record is None:
            self.remember_history()
            return
        editor.overwrite = record.overwrite
        editor.vertical_blocks = record.vertical_blocks
        # *Store editor position*: without it the cursor starts at the top, in
        # the window it was given.
        if not SETTINGS.interface.store_editor_position:
            return
        place_window(self, record)
        last = max(0, editor.line_count - 1)
        editor.top = min(max(0, record.top), last)
        editor.left = max(0, record.left)
        editor._go_column(record.line, record.col)

    def close(self) -> None:
        # ``TFileEditor.Valid(cmClose)``: the record is written once closing
        # has been agreed to, which is when this is called.
        if self.parent is not None:
            self.remember_history()
        super().close()

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
