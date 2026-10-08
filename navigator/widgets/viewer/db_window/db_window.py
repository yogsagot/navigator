"""The dBase viewer's behaviour: the indicator, and F2, F3, F4 and F7
(:mod:`navigator.dbf` reads and writes the file)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.i18n import tr
from navkit.reactive import effect
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.window import Window

from navigator import dbf
from navigator.widgets.viewer.commands import ContinueSearch, EditDbField, SearchAgain, SearchFor, ShowFields, ShowMemo


class DBWindow(Window):
    """``TDBWindow``: one ``.dbf``, its records a cell at a time."""

    def __init__(self, db: dbf.DBFile | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.db = db
        self.viewer.db = db
        self._search: dict[str, Any] | None = None
        if db is not None:
            # ``TWindow.Init(R, FName, 0)`` -- ``cmGetName``'s *dBase View - *
            # is the window list's.
            self.title = str(db.path)

    def mounted(self) -> None:
        super().mounted()
        effect(self, DBWindow._follow_cursor)
        self.viewer.focus()

    def _follow_cursor(self) -> None:
        """``TDBIndicator``: ``record/records``."""
        count = self.db.count if self.db is not None else 0
        self.indicator.text = f"{self.viewer.record + 1}/{count}"

    def list_name(self) -> str:
        """Window > List's line: ``dlDBViewName``, *dBase View - * and the name."""
        return tr("dBase View - {path}").format(path=self.db.path if self.db is not None else "")

    def close(self) -> None:
        if self.db is not None:
            self.db.close()
        super().close()

    async def _say(self, prompt: str, title: str | None = None) -> None:
        await Dialog(title=tr("Error") if title is None else title, prompt=prompt, buttons="ok").execute(self.application)

    # -- F2, F3 ----------------------------------------------------------------------

    async def on_show_fields(self, event: ShowFields) -> bool:
        self.spawn(show_structure(self.application, self.db, tr("Structure of {name}")))
        return True

    async def on_show_memo(self, event: ShowMemo) -> bool:
        self.spawn(self.show_memo())
        return True

    async def show_memo(self) -> None:
        """``ViewMemo``: the memo at the cursor in *Memo view* -- nothing for a
        field that is not one, or is empty."""
        from navigator.widgets.viewer.db_list_dialog import DBListDialog

        db, viewer = self.db, self.viewer
        record = db.record(viewer.record) if db is not None else None
        if record is None:
            return
        try:
            text = db.memo(record, db.fields[viewer.field])
        except FileNotFoundError:
            await self._say(tr("Could not find MEMO file"))
            return
        except OSError as error:
            await self._say(f"{error.strerror or error}")
            return
        if text is None:
            return
        lines = [line for chunk in text.replace("\r\n", "\n").split("\n") for line in _wrapped(chunk, 64)]
        await DBListDialog(lines=lines, title=tr("Memo view"), modal_width=69, modal_height=19).execute(self.application)
        viewer.focus()

    # -- F4 --------------------------------------------------------------------------

    async def on_edit_db_field(self, event: EditDbField) -> bool:
        self.spawn(self.edit_field())
        return True

    async def edit_field(self) -> None:
        """``EditField``: the cell at the cursor changed and written back --
        a logical one flipped between ``T`` and ``F``, a date typed day
        first, a number right-aligned to its decimals; a memo is not edited."""
        from navigator.widgets.shell.edit_line_dialog import EditLineDialog

        db, viewer = self.db, self.viewer
        record = db.record(viewer.record) if db is not None else None
        if record is None:
            return
        field = db.fields[viewer.field]
        if field.kind == "M":
            return
        import os

        if not os.access(db.path, os.W_OK):
            await self._say(tr("Could not edit field - file is write-protected"))
            return
        value = db.raw(record, field)
        if field.kind == "L":
            stored = "F" if value.strip().upper() == "T" else "T"
        else:
            shown = dbf.date_shown(value) if field.kind == "D" else value if field.kind == "C" else value.lstrip()
            box = EditLineDialog(shown.rstrip() if field.kind != "C" else shown, history="edit_dbf", caption=tr("~V~alue"))
            box.title = tr("Edit field")
            answer = await box.execute(self.application)
            viewer.focus()
            if answer is None:
                return
            if field.kind == "D":
                stored = dbf.date_stored(answer)
            elif field.kind in ("N", "F"):
                stored = dbf.number_stored(answer, field)
            else:
                stored = answer
            if stored is None:
                return
        try:
            db.write_field(viewer.record, field, stored)
        except OSError as error:
            await self._say(tr("Could not edit field - {error}").format(error=error.strerror or error))
            return
        viewer.invalidate()

    # -- F7, Shift+F7 ----------------------------------------------------------------

    async def on_search_for(self, event: SearchFor) -> bool:
        self.spawn(self.search_for())
        return True

    async def on_continue_search(self, event: ContinueSearch) -> bool:
        self.spawn(self.search_again())
        return True

    async def on_search_again(self, event: SearchAgain) -> bool:
        self.spawn(self.search_again())
        return True

    async def search_for(self) -> None:
        """``StartSearch``: *Search*, then forward from the next record,
        backward from the one before, or the whole file from its start."""
        from navigator.widgets.viewer.db_search_dialog import DBSearchDialog

        answer = await DBSearchDialog().execute(self.application)
        self.viewer.focus()
        if answer is None:
            return
        self._search = answer
        start = -1 if answer["direction"] == 2 else self.viewer.record
        await self._find(answer, start)

    async def search_again(self) -> None:
        """Shift+F7 and Ctrl+L: the last search on from the cursor."""
        from navigator.widgets.viewer.db_search_dialog.db_search_dialog import LAST

        answer = self._search or (dict(LAST) if LAST["text"] else None)
        if answer is None:
            await self.search_for()
            return
        await self._find(answer, self.viewer.record)

    async def _find(self, answer: dict[str, Any], start: int) -> None:
        viewer = self.viewer
        hit = dbf.find(self.db, answer["text"], case=answer["case"], all_fields=answer["all_fields"],
                       backward=answer["direction"] == 1, record=start, field=viewer.field)
        if hit is None:
            await self._say(tr("Search string not found"))
            viewer.focus()
            return
        viewer.go(record=hit[0], field=hit[1])


def _wrapped(text: str, width: int) -> list[str]:
    """*text* cut into lines of *width*, a blank line kept."""
    return [text[i:i + width] for i in range(0, len(text), width)] or [""]


def _type_names() -> dict[str, str]:
    """:data:`navigator.dbf.TYPES` as the structure box shows them."""
    return {"N": tr("Numeric"), "C": tr("Character"), "M": tr("Memo"), "L": tr("Logical"), "D": tr("Date"),
            "F": tr("Float"), "P": tr("Picture")}


async def show_structure(app: Any, db: dbf.DBFile, what: str) -> None:
    """``GetInfo``: *Structure of* (or *Empty database*) and the file's
    name -- *what*, with ``{name}`` for it -- a line a field: name, type,
    length, decimals."""
    from navigator.widgets.viewer.db_list_dialog import DBListDialog

    name = db.path.name if len(db.path.name) <= 20 else "..." + db.path.name[-17:]
    types = _type_names()
    lines = [f" {f.name:<12}{types.get(f.kind, f.kind):<13}{f.length:<11}"
             f"{f.decimals if f.kind in ('N', 'F') else '':<8}" for f in db.fields]
    await DBListDialog(heading=tr("Name          Type       Length   Decimals"), lines=lines,
                       title=what.format(name=name)).execute(app)


async def open_database(desktop: Any, path: Path) -> Any:
    """``New(PDBWindow, Init(FileName))``: the file's window, zoomed and given
    the keyboard -- or, for a file with no records, its structure under
    *Empty database*, and no window.  ``OSError`` and ``dbf.DBFError`` are
    the caller's."""
    import asyncio

    db = await asyncio.to_thread(dbf.DBFile, path)
    if db.count == 0:
        await show_structure(desktop.application, db, tr("Empty database {name}"))
        db.close()
        return None
    window = desktop.open(DBWindow(db))
    window.viewer.focus()
    return window
