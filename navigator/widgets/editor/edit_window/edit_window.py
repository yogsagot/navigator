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

import asyncio
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from navkit.events import Event
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.scroll_bar import ScrollEvent
from navml.widgets.window import Window

from navigator.editor.document import decode, encode
from navigator.editor.save import write_file
from navigator.file_history import place_window, window_values
from navigator.models.edit_record import EditRecord
from navigator.commands import PrintFile
from navigator.settings import SETTINGS
from navigator.widgets.editor.commands import BlockRead, BlockWrite, PrintBlock, SaveText


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
            marks=editor.markers_text(),
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
        # The markers are the text's, not the window's place: back whatever
        # *Store editor position* says, as ``fMarks`` came back.
        editor.restore_markers(record.marks)
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

    # -- ^K R and ^K W -------------------------------------------------------------

    def enables(self, command: Any) -> bool:
        if isinstance(command, (BlockWrite, PrintBlock)):
            return self.editor.has_block
        return super().enables(command)

    async def _block_file(self, title: str, label: str) -> Path | None:
        """``GetFileNameDialog``: DN's file dialog, with OK and Help.

        The history is the one DN's ^K R and ^K W shared, ``hsEditPasteFrom``.
        It lists the active panel's directory first, which was DN's current
        one; without a file manager, the edited file's.
        """
        from navml.widgets.dialog.file_dialog import FileDialog

        directory = self.editor.path.parent if self.editor.path is not None else None
        shell = getattr(self.application, "shell", None)
        manager = getattr(shell, "active_manager", None)
        if manager is not None:
            directory = manager.active_panel.path
        dialog = FileDialog(
            title=title, label=label, history_id="edit_paste_from",
            directory=directory, hidden=SETTINGS.system.show_hidden,
        )
        name = await dialog.execute(self.application)
        return Path(name) if name else None

    async def _say(self, message: str) -> None:
        await Dialog(title="Error", prompt=message, buttons="ok").execute(self.application)

    async def on_block_write(self, event: BlockWrite) -> bool:
        self.spawn(self.write_block())
        return True

    async def write_block(self) -> None:
        """^K W, ``BlockWrite``: the block to a file.

        An existing file is ``CheckForOver``'s question -- *Yes* replaces it,
        *Append* adds to its end, *Cancel* writes nothing -- and a read-only
        one is asked about again before it is changed.  The directory written
        to is re-read in every panel showing it (``cmRereadDir``).
        """
        data = encode(self.editor.block_file_text())
        path = await self._block_file("Copy block to", "File ~N~ame")
        if path is None:
            return
        append = False
        #: A read-only file's mode, put back once written, as ``SetFileAttr`` did.
        restore: int | None = None
        if path.exists():
            query = Dialog(
                title="Warning",
                prompt=f"File {path.name}\nalready exists.\nOK to overwrite it?",
                buttons="yes-no-cancel",
            )
            query.no.text = "A~p~pend"
            answer = await query.execute(self.application)
            if answer is None:
                return
            append = answer is False
            if not os.access(path, os.W_OK):
                modify = await Dialog(
                    title="Warning",
                    prompt=f"File {path.name}\nis marked as Read-Only.\nModify it anyway?",
                    buttons="ok-cancel",
                ).execute(self.application)
                if modify is not True:
                    return
                try:
                    restore = path.stat().st_mode
                    path.chmod(restore | stat.S_IWUSR)
                except OSError as error:
                    await self._say(f"Cannot write {path}: {error.strerror or error}")
                    return
        try:
            if append:
                with open(path, "ab") as file:
                    file.write(data)
            else:
                write_file(path, data)
            if restore is not None:
                path.chmod(stat.S_IMODE(restore))
        except OSError as error:
            await self._say(f"Cannot write {path}: {error.strerror or error}")
            return
        await self.emit(FileSaved(path))

    async def on_block_read(self, event: BlockRead) -> bool:
        self.spawn(self.read_block())
        return True

    async def read_block(self) -> None:
        """^K R, ``BlockRead``: a file's text at the cursor, which the editor marks."""
        path = await self._block_file("Paste from File", "~P~aste from")
        if path is None:
            return
        try:
            data = path.read_bytes()
        except OSError as error:
            await self._say(f"Cannot read {path}: {error.strerror or error}")
            return
        self.editor.read_block(decode(data))

    # -- ^K P / Shift+F8 ------------------------------------------------------------

    async def on_print_block(self, event: PrintBlock) -> bool:
        self.spawn(self.print_block())
        return True

    async def print_block(self) -> None:
        """``Print(On)`` (``EDITOR.PAS``): the block, as ``GetSelection`` gave it."""
        await self.print_lines(self.editor.block_lines())

    async def on_print_file(self, event: PrintFile) -> bool:
        self.spawn(self.print_file())
        return True

    async def print_file(self) -> None:
        """``Print(Off)``, F8: the whole text as it stands, saved or not -- what the
        editor holds, ``FileLines``, not what is on disk.  A text ending in a line
        break has no empty line after it to print."""
        lines = list(self.editor.document.lines)
        if len(lines) > 1 and lines[-1] == "":
            lines.pop()
        await self.print_lines(lines)

    async def print_lines(self, lines: list[str]) -> None:
        """``Print``: *Print N lines?* (``dlED_PrintQuery``), then *lines* to the printer.

        The spooler stands for DN's print manager (:mod:`navigator.printing`);
        a line ends in LF rather than DN's CR LF, which is what it expects.
        A spooler that refuses -- no printer, no default destination -- says
        why.
        """
        from navigator.printing import spool

        if not lines:
            return
        count = len(lines)
        answer = await Dialog(
            title="Confirmation",
            prompt=f"Print {count} line{'s' if count != 1 else ''}?",
            buttons="yes-no",
        ).execute(self.application)
        if answer is not True:
            return
        loop = asyncio.get_running_loop()
        problem = await loop.run_in_executor(None, spool, "\n".join(lines) + "\n")
        if problem is not None:
            await self._say(f"Cannot print: {problem}")

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
