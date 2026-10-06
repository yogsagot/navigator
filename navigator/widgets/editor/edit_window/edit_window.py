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

from navigator.editor.document import Document, encode, encode_lines, read_text
from navigator.editor.lock import refuse_if_locked
from navigator.editor.save import write_file
from navigator.file_history import place_window, window_values
from navigator.models.edit_record import EditRecord
from navigator.commands import PrintFile
from navigator.settings import SETTINGS
from navigator.widgets.editor.commands import (
    AsciiTable,
    SetMargins,
    ContSearch,
    Replace,
    ReverseSearch,
    StartSearch,
    BlockRead,
    BlockWrite,
    GotoLineNumber,
    LoadText,
    PrintBlock,
    SaveAll,
    SaveText,
    SaveTextAs,
)


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
    Given the *document*, already read from *path* on a thread
    (``navigator.widgets.editor.loading``), the window reads nothing itself.
    """

    emits = (FileSaved,)

    def __init__(
        self, path: Path | str, *, document: Document | None = None, new: bool = False,
        smartpad: bool = False, **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        #: SmartPad's window (``navigator.smartpad``): its own title, no edit
        #: history, and saved without a question on the way out.
        self.smartpad = smartpad
        #: One save at a time: a second F2, or *Yes* to *Save?* while one is
        #: still writing, waits for it and then writes what the text is then.
        self._saving = asyncio.Lock()
        if document is None:
            self.editor.open(path, new=new)
        else:
            self.editor.use_document(path, document)
        self.title = self._title()

    def _title(self) -> str:
        """``dlEditTitle`` -- ``Edit - `` and the whole name -- or SmartPad's own."""
        prefix = "SmartPad(TM) - " if self.smartpad else "Edit - "
        return f"{prefix}{self.editor.path}"

    def take_keyboard(self) -> None:
        # Not from ``mounted()``: that runs inside ``Desktop.open``'s ``add()``,
        # before ``activate`` has saved which panel the window below had, so
        # closing this one would hand the keyboard to the left panel.
        self.editor.focus()

    def list_name(self) -> str:
        """Window > List's line: the title, which already says ``Edit - ``."""
        return self._title()

    # -- the File Edit History -------------------------------------------------

    def remember_history(self) -> None:
        """``StoreEditInfo``: this file's record, as the editor is now -- never
        SmartPad's (``not SmartPad and ... StoreEditInfo``)."""
        editor = self.editor
        if self.smartpad or not SETTINGS.interface.track_editing or editor.path is None:
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
        self.editor.unlock_file()
        super().close()

    # -- saving ------------------------------------------------------------------

    async def on_save_text(self, event: SaveText) -> bool:
        """F2: ``cmSaveText``.  A failure is said, and the text stays changed."""
        self.spawn(self.save())
        return True

    async def save(self) -> bool:
        """Write the file; say why not if it cannot be.  True when written."""
        path = self.editor.path
        try:
            if path is None:
                raise OSError("no file name")
            written = await self._write(path, backup=SETTINGS.editor.create_backup)
        except OSError as error:
            await Dialog(
                title="Error",
                prompt=f"Cannot write {path}: {error.strerror or error}",
                buttons="ok",
            ).execute(self.application)
            return False
        if written and not self.smartpad and self.parent is not None:
            # ``FileChanged``, which SmartPad's own file never set off.
            await self.emit(FileSaved(path))
        return written

    async def _write(self, path: Path, backup: bool = False) -> bool:
        """The text to *path*, on a thread: DN's ``SaveFile`` behind ``WriteMsg``.

        The text is taken as it is when the write starts; what is typed while
        it runs is not in the file, and leaves the text changed.  *Writing
        file* comes up if it takes a while, and *Cancel* there leaves the file
        as it was.  True once written, False if cancelled; raises ``OSError``.
        *backup* keeps the old file as ``NAME.bak``: only F2 asks for one, as
        only ``SaveFile`` made one (``CheckForOver``'s, behind Save as and
        ^K W, ran when the file did not exist, and so never had one to make).
        """
        from navigator.widgets.editor.loading import write_in_background

        async with self._saving:
            lines, endings, point = self.editor.snapshot()
            try:
                written = await write_in_background(
                    self.application,
                    lambda job: write_file(path, encode_lines(lines, endings, job), job, backup),
                    total=len(lines),
                )
            finally:
                # ``LockFile`` again, written or not: a save renames a new
                # file over the one locked, and the lock goes with that.
                self.editor.lock_file()
            if written:
                self.editor.saved(point)
            return written

    # -- ^K R and ^K W -------------------------------------------------------------

    def enables(self, command: Any) -> bool:
        if isinstance(command, (BlockWrite, PrintBlock)):
            return self.editor.has_block
        return super().enables(command)

    async def _ask_file(
        self, title: str, label: str, history_id: str, ok_text: str | None = None,
    ) -> Path | None:
        """``GetFileNameDialog``: DN's file dialog, with OK (or *ok_text*) and Help.

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
            title=title, label=label, history_id=history_id, ok_text=ok_text,
            directory=directory, hidden=SETTINGS.system.show_hidden,
        )
        name = await dialog.execute(self.application)
        return Path(name) if name else None

    async def _block_file(self, title: str, label: str) -> Path | None:
        """^K R and ^K W's name, in the history they shared, ``hsEditPasteFrom``."""
        return await self._ask_file(title, label, "edit_paste_from")

    async def _check_for_over(self, path: Path, *, append: bool) -> tuple[bool, int | None] | None:
        """``CheckForOver``: whether *path* may be written, and how.

        Nothing to ask for a file that is not there.  One that is, is *OK to
        overwrite it?* -- with *Append* beside Yes where *append* allows it --
        and a read-only one *Modify it anyway?* as well, its mode lifted for
        the write and handed back to be put back after.  Answers ``(append,
        mode)``, or None for Cancel.
        """
        if not path.exists():
            return False, None
        query = Dialog(
            title="Warning",
            prompt=f"File {path.name}\nalready exists.\nOK to overwrite it?",
            buttons="yes-no-cancel" if append else "yes-no",
        )
        if append:
            query.no.text = "A~p~pend"
        else:
            query.no.text = "Cancel"
        answer = await query.execute(self.application)
        if answer is None or (answer is False and not append):
            return None
        appending = answer is False
        restore: int | None = None
        if not os.access(path, os.W_OK):
            modify = await Dialog(
                title="Warning",
                prompt=f"File {path.name}\nis marked as Read-Only.\nModify it anyway?",
                buttons="ok-cancel",
            ).execute(self.application)
            if modify is not True:
                return None
            try:
                restore = path.stat().st_mode
                path.chmod(restore | stat.S_IWUSR)
            except OSError as error:
                await self._say(f"Cannot write {path}: {error.strerror or error}")
                return None
        return appending, restore

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
        answer = await self._check_for_over(path, append=True)
        if answer is None:
            return
        append, restore = answer

        def write(job: Any) -> None:
            if append:
                job.cancellable = False  # one write: all of it, or none
                refuse_if_locked(path)
                with open(path, "ab") as file:
                    file.write(data)
            else:
                write_file(path, data, job)

        from navigator.widgets.editor.loading import write_in_background

        try:
            written = await write_in_background(self.application, write)
        except OSError as error:
            await self._say(f"Cannot write {path}: {error.strerror or error}")
            return
        finally:
            if restore is not None:
                try:
                    path.chmod(stat.S_IMODE(restore))
                except OSError:
                    pass
        if not written:
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
        from navigator.widgets.editor.loading import read_in_background

        try:
            text = await read_in_background(
                self.application, lambda job, budget: read_text(path, job, budget=budget))
        except OSError as error:
            await self._say(f"Cannot read {path}: {error.strerror or error}")
            return
        if text is None:
            return
        self.editor.read_block(text)

    # -- F7: find and replace ------------------------------------------------------------

    #: ``ReplaceAll``: whether the last Replace was *Change all*, which Shift+F7 keeps.
    _replace_all = False

    async def on_start_search(self, event: StartSearch) -> bool:
        self.spawn(self.start_search(replace=False))
        return True

    async def on_replace(self, event: Replace) -> bool:
        self.spawn(self.start_search(replace=True))
        return True

    async def on_cont_search(self, event: ContSearch) -> bool:
        self.spawn(self.search())
        return True

    async def on_reverse_search(self, event: ReverseSearch) -> bool:
        self.spawn(self.search(reverse=True))
        return True

    async def start_search(self, *, replace: bool) -> None:
        """``StartSearch``: *Find* or *Replace*, then the search from where *Origin* says.

        *Entire scope* starts from the text's start, or its end searching
        backward, and the cursor goes back where it was if nothing is found.
        """
        from navigator.editor import search
        from navigator.editor.document import Pos
        from navigator.widgets.editor.find_dialog import FindDialog

        editor = self.editor
        answer = await FindDialog(
            word=editor.word_at_cursor(), replace=replace,
        ).execute(self.application)
        if answer is None:
            return
        self._replace_all = replace and answer == "all"
        at = None
        if not search.SEARCH.from_cursor:
            at = editor.document.end if search.SEARCH.backward else Pos(0, 0)
        await self.search(at=at)

    async def search(self, *, reverse: bool = False, at: Any = None) -> bool:
        """``TFileEditor.Search``: from *at* (else the cursor), with :data:`SEARCH`.

        A plain search stops at the first match.  A replacement asks each time
        while *Prompt on replace* is ticked -- *All* stops the asking -- and
        goes on only for *Change all*.  Nothing found says so; replacements made
        unasked are counted.  True when something was found.
        """
        from navigator.editor import search
        from navigator.widgets.editor.replace_query import ReplaceQuery

        data, editor = search.SEARCH, self.editor
        backward = data.backward != reverse
        if not data.text or (data.selected and not editor.has_block):
            return False
        here = editor._mark_pos()
        if at is None:
            at = here
            # ``if SearchOnDisplay then Search``: with the last match still lit,
            # a search the other way starts from its far side, not into it.
            shown = editor.found_on_display()
            if shown is not None:
                at = shown[0] if backward else shown[1]
        replace_all, prompt = self._replace_all, data.prompt
        found_any, made = False, 0
        while True:
            found = editor.find(at, data, backward=backward)
            if found is None:
                break
            found_any = True
            editor.show_found(found, backward=backward)
            if data.new is None:
                return True
            choice = "yes"
            if prompt:
                choice = await ReplaceQuery().execute(self.application)
                if choice == "all":
                    choice, replace_all, prompt = "yes", True, False
            if choice is None:
                return True
            if choice == "yes":
                end = editor.replace_found(found, data.new)
                at = found[0] if backward else end
                editor._go(at)
                if not prompt:
                    made += 1
            else:
                at = found[0] if backward else found[1]
            if not replace_all:
                break
        if not found_any:
            editor._go_column(here.line, editor._column(here))
            await Dialog(title="Error", prompt="Search string not found", buttons="ok").execute(
                self.application,
            )
            return False
        if made:
            await Dialog(
                title="Information", prompt=f"{made} replaces made", buttons="ok",
            ).execute(self.application)
        return True

    # -- Paragraph > Margins -------------------------------------------------------------

    async def on_set_margins(self, event: SetMargins) -> bool:
        self.spawn(self.set_margins())
        return True

    async def set_margins(self) -> None:
        """``SetFormat``: *Format Margins* for this editor's margins and indent."""
        from navigator.widgets.editor.margins_dialog import MarginsDialog

        margins = await MarginsDialog(self.editor.margins).execute(self.application)
        if margins is not None:
            self.editor.margins = margins

    # -- Alt+G -------------------------------------------------------------------------

    async def on_goto_line_number(self, event: GotoLineNumber) -> bool:
        self.spawn(self.goto_line())
        return True

    async def goto_line(self) -> None:
        """``GotoLine``: *Goto Line*, then the cursor to the line given, if one was."""
        from navigator.widgets.editor.goto_line_dialog import GotoLineDialog

        number = await GotoLineDialog().execute(self.application)
        if number is not None:
            self.editor.go_to_line(number)

    # -- Ctrl+P: the character table --------------------------------------------------

    async def on_ascii_table(self, event: AsciiTable) -> bool:
        self.spawn(self.ascii_table())
        return True

    async def ascii_table(self) -> None:
        """``ASCIITable``, then ``InputChar``: the character picked typed at the cursor.

        Typed as the chart shows it -- the VGA's glyph, ``│`` for 179 and ``☺``
        for 1 -- the text being Unicode where DN's was bytes; 0, whose glyph
        is a blank, is a NUL.
        """
        from navigator.widgets.shell.ascii_chart import AsciiChart
        from navigator.widgets.shell.char_table.char_table import glyph

        code = await AsciiChart().execute(self.application)
        if code is None:
            return
        self.editor.focus()
        self.editor.type_text("\x00" if code == 0 else glyph(code))

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

    # -- Ctrl+F2 ------------------------------------------------------------------------

    async def on_save_all(self, event: SaveAll) -> bool:
        self.spawn(self.save_all())
        return True

    async def save_all(self) -> None:
        """``cmSaveAll``: ``GlobalMessage(evCommand, cmSaveText)``, every editor saving.

        Every editor window on the desktop, this one first and the rest front
        to back, each saving as F2 does and saying why if it cannot -- the
        others go on.  A departure: only a text that has changed is written,
        where DN's ``SaveFile`` rewrote every one, unchanged or not, and moved
        each file's time for nothing.
        """
        desktop = self.parent
        windows = [self] + [
            window for window in reversed(desktop.windows() if desktop is not None else [])
            if isinstance(window, EditWindow) and window is not self
        ]
        for window in windows:
            if window.editor.modified:
                await window.save()

    # -- F3 and Shift+F2 ----------------------------------------------------------------

    async def on_load_text(self, event: LoadText) -> bool:
        self.spawn(self.load_text())
        return True

    async def load_text(self) -> None:
        """``cmLoadText``: another file into this window, DN's ``OpenFile``.

        A changed text is offered a save first (``AskSave``: Cancel keeps
        everything as it is).  Then *Open a File*, with *Open* for its OK, in
        the ``hsEditOpen`` history.  The file being left has its record kept,
        and the one opened comes back as it was last left.  A departure: a
        file that will not open is said and the window keeps its text, where
        DN closed the window.
        """
        if self.editor.modified:
            name = self.editor.path.name if self.editor.path else "Untitled"
            answer = await Dialog(
                title="Warning", prompt=f"File {name} was modified. Save?",
                buttons="yes-no-cancel",
            ).execute(self.application)
            if answer is None or (answer is True and not await self.save()):
                return
        path = await self._ask_file("Open a File", "~N~ame", "edit_open", ok_text="~O~pen")
        if path is None:
            return
        from navigator.widgets.editor.loading import load_document

        try:
            document = await load_document(self.application, path)
        except OSError as error:
            await self._say(f"Cannot open {path}: {error.strerror or error}")
            return
        if document is None:
            # Cancelled, or too large -- said already: the text stays.
            return
        self.remember_history()
        self.editor.use_document(path, document)
        self.title = self._title()
        self.recall_history()
        self.editor.focus()

    async def on_save_text_as(self, event: SaveTextAs) -> bool:
        self.spawn(self.save_as())
        return True

    async def save_as(self) -> None:
        """``SaveFileAs``: the text under a name asked in *Save File As*, ``hsEditSave``.

        An existing file is asked about first (``CheckForOver``) -- without the
        *Append* DN offered, a departure: appending the whole text to another
        file and then editing that file under its name left an editor showing
        less than was on disk, for the next F2 to throw away.  The window takes
        the new name and its title, and the text counts as saved.
        """
        path = await self._ask_file("Save File As", "~S~ave File As", "edit_save")
        if path is None:
            return
        answer = await self._check_for_over(path, append=False)
        if answer is None:
            return
        _, restore = answer
        try:
            written = await self._write(path)
        except OSError as error:
            await self._say(f"Cannot write {path}: {error.strerror or error}")
            return
        finally:
            if restore is not None:
                try:
                    path.chmod(stat.S_IMODE(restore))
                except OSError:
                    pass
        if not written:
            return
        self.editor.path = path
        self.editor.lock_file()
        self.title = self._title()
        if self.parent is not None:
            await self.emit(FileSaved(path))

    # -- closing -----------------------------------------------------------------

    def must_ask(self) -> bool:
        return self.editor.modified

    async def ask_to_close(self) -> bool:
        """``dlQueryModified``: save, lose, or stay open -- SmartPad saves unasked."""
        if self.smartpad:
            return await self.save()
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
