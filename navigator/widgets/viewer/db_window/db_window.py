"""The dBase viewer's behaviour: the indicator, and F2, F3, F4 and F7
(:mod:`navigator.lib.viewer.dbf` reads and writes the file).

**It shows a SQLite file too** (a departure; :mod:`navigator.lib.viewer.sqlite`):
a table at a time, F5 choosing another and F6 a query, read-only -- F4 is
refused.  The grid asks either source the same few questions (``fields``,
``count``, ``record``, ``shown``, ``raw``, ``memo``, ``flag``)."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any

from navkit.bidi import display_width
from navkit.i18n import tr, tr_n
from navkit.reactive import effect
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.window import Window

from navigator.lib.viewer import dbf
from navigator.widgets.viewer.commands import (
    ChooseTable,
    ContinueSearch,
    EditDbField,
    RunQuery,
    SearchAgain,
    SearchFor,
    ShowFields,
    ShowMemo,
)


class DBWindow(Window):
    """``TDBWindow``: one ``.dbf``, its records a cell at a time."""

    def __init__(self, db: Any = None, *, sqlite: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.db = db
        #: The SQLite file *db* is a table of, if it is one
        #: (``navigator.lib.viewer.sqlite.SQLiteFile``): closed with the window.
        self.sqlite = sqlite
        self._place: str | None = None
        self.viewer.db = db
        self._search: dict[str, Any] | None = None
        #: The copy of a file from another drive this window shows, if it
        #: does (``UseFile``): a field edited goes back there, the copy with
        #: the window.
        self.use_set: Any = None
        #: Whether *use_set* was fetched as root, the helper held open for the
        #: fields put back; ``close()`` lets go (a departure;
        #: :mod:`navigator.lib.system.elevate`).
        self.root_held = False
        if db is not None:
            # ``TWindow.Init(R, FName, 0)`` -- ``cmGetName``'s *dBase View - *
            # is the window list's.
            self.title = self._title_of(db)

    @property
    def place(self) -> str:
        """Where the file is: its path, or -- for a copy fetched from another
        drive or as root -- the original's, which the title shows."""
        if self._place is not None:
            return self._place
        return str(self.db.path) if self.db is not None else ""

    @place.setter
    def place(self, value: str) -> None:
        self._place = value
        if self.db is not None:
            self.title = self._title_of(self.db)

    def _title_of(self, db: Any) -> str:
        """The file -- and, for SQLite, the table or *Query* after it."""
        place = self._place if self._place is not None else str(db.path)
        if self.sqlite is None:
            return place
        return f"{place} - {db.name or tr('Query')}"

    def mounted(self) -> None:
        super().mounted()
        effect(self, DBWindow._follow_cursor)
        self.viewer.focus()

    def _follow_cursor(self) -> None:
        """``TDBIndicator``: ``record/records``."""
        count = self.db.count if self.db is not None else 0
        text = f"{self.viewer.record + 1}/{count}"
        if getattr(self.db, "truncated", False):
            # A view or a query read whole, cut at its first ROW_LIMIT rows.
            text += "+"
        self.indicator.text = text

    def list_name(self) -> str:
        """Window > List's line: ``dlDBViewName``, *dBase View - * and the name."""
        path = self.place
        if self.sqlite is not None:
            return tr("SQLite View - {path}").format(path=path)
        return tr("dBase View - {path}").format(path=path)

    def short_name(self) -> str:
        """The window strip's: the file's name alone."""
        return PurePosixPath(str(self.db.path)).name if self.db is not None else ""

    def close(self) -> None:
        if self.db is not None:
            self.db.close()
        if self.sqlite is not None:
            self.sqlite.close()
        super().close()
        if self.use_set is not None:
            import asyncio

            from navigator.lib.drives import usefile

            use, self.use_set = self.use_set, None
            asyncio.get_running_loop().run_in_executor(None, usefile.discard, use)
        if self.root_held:
            import asyncio

            from navigator.lib.system.elevate import ELEVATION

            self.root_held = False
            ELEVATION.unhold()
            asyncio.get_running_loop().run_in_executor(None, ELEVATION.release)

    def refusal(self, command: Any) -> str:
        """*Memo view* only on a memo field -- off one, F3 does nothing; in a
        SQLite table, on text or a blob.  A SQLite file is read-only, and
        F5 and F6 are for one alone."""
        if isinstance(command, ShowMemo):
            fields = self.db.fields if self.db is not None else []
            if 0 <= self.viewer.field < len(fields) and fields[self.viewer.field].kind in self.db.memo_kinds:
                return ""
            if self.sqlite is not None:
                return tr("The cursor is not on text or a blob")
            return tr("The cursor is not on a memo field")
        if isinstance(command, EditDbField) and self.db is not None and not self.db.editable:
            return tr("The database is opened read-only")
        if isinstance(command, (ChooseTable, RunQuery)) and self.sqlite is None:
            return tr("Only in a SQLite file")
        return super().refusal(command)

    async def _say(self, prompt: str, title: str | None = None) -> None:
        await Dialog(title=tr("Error") if title is None else title, prompt=prompt, buttons="ok").execute(self.application)

    # -- F2, F3 ----------------------------------------------------------------------

    async def on_show_fields(self, event: ShowFields) -> bool:
        if self.sqlite is not None:
            self.spawn(self.show_schema())
        else:
            self.spawn(show_structure(self.application, self.db, tr("Structure of {name}")))
        return True

    async def show_schema(self) -> None:
        """F2 on a SQLite table: its columns -- name, declared type, ``PK``,
        ``NOT NULL`` -- then its row count, its indexes and its ``CREATE``
        (a departure, as SQLite is); a query's result, its columns alone."""
        import asyncio

        from navigator.widgets.viewer.db_list_dialog import DBListDialog

        db = self.db
        flags = {True: "PK"}
        lines = [_table_row(f.name, f.declared or "", " ".join(
            word for word in (flags.get(f.primary, ""), "NOT NULL" if f.not_null else "") if word), "")
                 for f in db.fields]
        if db.name:
            try:
                schema = await asyncio.to_thread(self.sqlite.schema, db.name)
            except Exception as error:  # noqa: BLE001 - a broken file is said, not raised
                schema = {"sql": str(error), "indexes": [], "count": db.count}
            lines += ["", " " + tr_n("{count} row", "{count} rows", schema["count"], count=f"{schema['count']:,}")]
            for name, unique, columns in schema["indexes"]:
                kind = tr("Unique index") if unique else tr("Index")
                lines.append(f" {kind} {name} ({', '.join(columns)})")
            lines.append("")
            for line in schema["sql"].splitlines():
                lines += [" " + part for part in _wrapped(line, 60)]
        heading = _table_row(tr("Name"), tr("Type"), tr("Constraints"), "")
        name = db.name or tr("Query")
        await DBListDialog(heading=heading, lines=lines, title=tr("Structure of {name}").format(name=name),
                           modal_width=69, modal_height=19).execute(self.application)
        self.viewer.focus()

    # -- F5, F6: SQLite -----------------------------------------------------------------

    async def on_choose_table(self, event: ChooseTable) -> bool:
        self.spawn(self.choose_table())
        return True

    async def choose_table(self) -> None:
        """F5: the tables and views in a box; the one chosen shown."""
        current = self.db.name if self.db is not None else None
        name = await choose_object(self.application, self.sqlite, self, current)
        if name is None or name == current:
            self.viewer.focus()
            return
        await self._show_table(lambda work: self.sqlite.table(name, work))

    async def on_run_query(self, event: RunQuery) -> bool:
        self.spawn(self.run_query())
        return True

    async def run_query(self) -> None:
        """F6: a query typed, its result shown -- or what SQLite said of it."""
        from navigator.widgets.viewer.query_dialog import QueryDialog

        sql = await QueryDialog().execute(self.application)
        self.viewer.focus()
        if not sql:
            return
        await self._show_table(lambda work: self.sqlite.query(sql, work))

    async def _show_table(self, read: Any) -> None:
        """*read* (a table, or a query) on a thread, under *Reading* if it
        takes a while; shown from its first row."""
        from navigator.lib.system.progress import run_with_progress
        from navigator.lib.viewer import sqlite, table
        from navigator.widgets.editor.loading import progress_box, refresh_box

        work = table.Work()
        try:
            db = await run_with_progress(self.application, lambda: read(work), work,
                                         lambda: progress_box(work, tr("Reading")), refresh_box(work))
        except sqlite.SQLiteError as error:
            if not work.stopped:
                await self._say(str(error))
            self.viewer.focus()
            return
        self.db = self.viewer.db = db
        self.viewer.record = self.viewer.field = 0
        self.viewer.first_field = self.viewer.top = 0
        self.title = self._title_of(db)
        self.viewer.invalidate()
        self.viewer.focus()

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

        writable = os.access(db.path, os.W_OK)
        if self.use_set is not None:
            from navigator.lib.drives import DriveGone, drive_of

            try:
                writable = drive_of(self.use_set.copies[0].origin).can("write")
            except DriveGone:
                writable = False
        if not writable and self.use_set is None and not await self._edit_as_root():
            await self._say(tr("Could not edit field - file is write-protected"))
            return
        db = self.db
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
        if self.use_set is not None:
            # From another drive: the field goes back there at once, as it
            # went into the file on the disk.
            from navigator.widgets.drives.use_file import put_back

            await put_back(self.application, self.use_set, ask=False)
        viewer.invalidate()

    async def _edit_as_root(self) -> bool:
        """A field of a file on the disk the user may not write: *As root*
        offered, and the window moved onto a copy fetched through the root
        helper, each field put back through it (a departure;
        :mod:`navigator.lib.system.elevate`).  True once it is."""
        import asyncio

        from navigator.lib.system.elevate import ELEVATION
        from navigator.widgets.file_ops.as_root import ask_as_root, fetch_database

        if not await asyncio.to_thread(ELEVATION.available):
            return False
        path = self.db.path
        if not await ask_as_root(self.application, tr("Could not edit field - file is write-protected")):
            return False
        use = await fetch_database(self.application, path)
        if use is None:
            return False
        from navigator.lib.drives.location import Location

        try:
            db = await asyncio.to_thread(dbf.DBFile, use.local_for(Location.of(path)))
        except (OSError, dbf.DBFError):
            from navigator.lib.drives import usefile

            usefile.discard(use)
            ELEVATION.unhold()
            await asyncio.to_thread(ELEVATION.release)
            raise
        self.db.close()
        self.db = self.viewer.db = db
        self.use_set, self.root_held = use, True
        return True

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
        """On a thread, under *Searching* if it takes a while -- a SQLite
        table may be millions of rows; Stop leaves the cursor where it is."""
        from navigator.lib.system.progress import run_with_progress
        from navigator.lib.viewer.table import Work
        from navigator.widgets.editor.loading import progress_box, refresh_box

        viewer, db = self.viewer, self.db
        work = Work(db.count)
        field = viewer.field
        hit = await run_with_progress(
            self.application,
            lambda: dbf.find(db, answer["text"], case=answer["case"], all_fields=answer["all_fields"],
                             backward=answer["direction"] == 1, record=start, field=field, work=work),
            work, lambda: progress_box(work, tr("Searching")), refresh_box(work))
        if work.stopped:
            return
        if hit is None:
            await self._say(tr("Search string not found"))
            viewer.focus()
            return
        viewer.go(record=hit[0], field=hit[1])


def _wrapped(text: str, width: int) -> list[str]:
    """*text* cut into lines of *width*, a blank line kept."""
    return [text[i:i + width] for i in range(0, len(text), width)] or [""]


def _type_names() -> dict[str, str]:
    """:data:`navigator.lib.viewer.dbf.TYPES` as the structure box shows them."""
    return {"N": tr("Numeric"), "C": tr("Character"), "M": tr("Memo"), "L": tr("Logical"), "D": tr("Date"),
            "F": tr("Float"), "P": tr("Picture")}


async def show_structure(app: Any, db: dbf.DBFile, what: str) -> None:
    """``GetInfo``: *Structure of* (or *Empty database*) and the file's
    name -- *what*, with ``{name}`` for it -- a line a field: name, type,
    length, decimals."""
    from navigator.widgets.viewer.db_list_dialog import DBListDialog

    name = db.path.name if len(db.path.name) <= 20 else "..." + db.path.name[-17:]
    types = _type_names()
    lines = [_table_row(f.name, types.get(f.kind, f.kind), str(f.length),
                        str(f.decimals) if f.kind in ("N", "F") else "") for f in db.fields]
    heading = _table_row(tr("Name"), tr("Type"), tr("Length"), tr("Decimals"))
    await DBListDialog(heading=heading, lines=lines, title=what.format(name=name)).execute(app)


#: The structure box's columns: a field's name, type, length and decimals.
_COLUMNS = (12, 13, 11, 8)


def _table_row(*cells: str) -> str:
    """One line of the structure box: *cells* padded to :data:`_COLUMNS` by
    their painted width, after a blank, each cell opened by an LRM -- the
    table is held left to right, a dBase field name being ASCII, and two
    Hebrew headings or a type name and its length never run together into
    one right-to-left stretch that turns the columns round."""
    padded = "".join(f"\u200e{cell}" + " " * max(1, width - display_width(cell))
                     for cell, width in zip(cells, _COLUMNS))
    return " " + padded.rstrip()


async def choose_object(app: Any, file: Any, near: Any, current: str | None = None) -> str | None:
    """*Tables*: a SQLite file's tables and views in a box over *near*, the
    *current* one selected; the name chosen, or None."""
    import asyncio

    from navml.widgets.menu.popup_menu import PopupMenu
    from navml.widgets.menu.sub_menu import SubMenu

    objects = await asyncio.to_thread(file.objects)
    menu = SubMenu()
    names = [name for name, _ in objects]
    items = [menu.add_item(f"{name}  ({tr('view') if kind == 'view' else tr('table')})".replace("~", "~~"))
             for name, kind in objects]
    title = tr("Tables")
    width, height = PopupMenu.measure(menu, app, near, title)
    ox, oy = near.offset()
    x = ox + near.x + max(0, (near.width - width) // 2)
    y = oy + near.y + max(0, (near.height - height) // 2)
    box = PopupMenu(menu, x, y, current=names.index(current) if current in names else -1, behind=near,
                    title=title)
    chosen = await box.execute(app)
    return None if chosen is None else names[items.index(chosen)]


async def open_sqlite(desktop: Any, path: Path) -> Any:
    """*As DataBase* on a SQLite file (a departure): opened read-only on a
    thread; with more than one table or view, *Tables* chooses which; with
    none, *Empty database*.  The window, or None.  ``dbf.DBFError`` for a
    file SQLite will not open, as for a ``.dbf`` that is not one."""
    import asyncio

    from navigator.lib.system.progress import run_with_progress
    from navigator.lib.viewer import sqlite, table
    from navigator.widgets.editor.loading import progress_box, refresh_box

    try:
        file = await asyncio.to_thread(sqlite.SQLiteFile, path)
    except sqlite.SQLiteError as error:
        raise dbf.DBFError(str(error)) from error
    try:
        objects = await asyncio.to_thread(file.objects)
    except Exception as error:  # noqa: BLE001 - sqlite3.DatabaseError: a damaged file
        file.close()
        raise dbf.DBFError(str(error)) from error
    if not objects:
        file.close()
        name = path.name if len(path.name) <= 20 else "..." + path.name[-17:]
        await Dialog(title=tr("Empty database {name}").format(name=name), prompt=tr("No tables"),
                     buttons="ok").execute(desktop.application)
        return None
    if len(objects) == 1:
        name = objects[0][0]
    else:
        name = await choose_object(desktop.application, file, desktop)
        if name is None:
            file.close()
            return None
    work = table.Work()
    try:
        db = await run_with_progress(desktop.application, lambda: file.table(name, work), work,
                                     lambda: progress_box(work, tr("Reading")), refresh_box(work))
    except sqlite.SQLiteError as error:
        file.close()
        if work.stopped:
            return None
        raise dbf.DBFError(str(error)) from error
    window = desktop.open(DBWindow(db, sqlite=file))
    window.viewer.focus()
    return window


async def open_database(desktop: Any, path: Path) -> Any:
    """``New(PDBWindow, Init(FileName))``: the file's window, zoomed and given
    the keyboard -- or, for a file with no records, its structure under
    *Empty database*, and no window.  A SQLite file (by its header) opens
    through :func:`open_sqlite`.  ``OSError`` and ``dbf.DBFError`` are the
    caller's."""
    import asyncio

    from navigator.lib.viewer.sqlite import is_sqlite

    if is_sqlite(path):
        return await open_sqlite(desktop, Path(path))
    db = await asyncio.to_thread(dbf.DBFile, path)
    if db.count == 0:
        await show_structure(desktop.application, db, tr("Empty database {name}"))
        db.close()
        return None
    window = desktop.open(DBWindow(db))
    window.viewer.focus()
    return window
