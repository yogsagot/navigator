"""The spreadsheet window's behaviour: the indicator, the walk of a big file
followed, and F5, F6, F7, Enter, Shift+F4 and Shift+F6
(:mod:`navigator.lib.viewer.table` reads the file; nothing writes it)."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any

from navkit.i18n import tr
from navkit.reactive import effect
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.window import Window

from navigator.lib.viewer import table
from navigator.widgets.viewer.commands import (
    ChangeWidth,
    CloseViewer,
    ContinueSearch,
    FindCell,
    GotoCell,
    SearchAgain,
    ShowCell,
    SortColumn,
    TableFormat,
    ViewSheetAsText,
)

#: How often the indicator looks at a walk still going, in seconds.
TICK = 0.25


class SheetWindow(Window):
    """``TCalcWindow``: one CSV or TSV file, its cells a cursor at a time."""

    def __init__(self, source: table.TableSource | None = None, *, row: int = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.source = source
        #: The copy of a file from another drive this window shows, if it
        #: does (``UseFile``): let go with the window.
        self.use_set: Any = None
        self._ticker: Any = None
        self._search: table.CellSearch | None = None
        #: The last cell *Go to Cell Number* went to: its line's seed.
        self._last_goto = "A1"
        if source is not None:
            self.title = str(source.path)
            self.sheet.show(source, row)

    def mounted(self) -> None:
        super().mounted()
        effect(self, SheetWindow._follow_cursor)
        app = self.application
        if app is not None and self._ticker is None and self.source is not None and not self.source.complete:
            self._ticker = app.call_every(TICK, self._tick)
        self.sheet.focus()

    def unmounting(self) -> None:
        self._stop_ticking()
        super().unmounting()

    def _stop_ticking(self) -> None:
        if self._ticker is not None:
            self._ticker.cancel()
            self._ticker = None

    async def _tick(self) -> None:
        """The walk has found more rows: count and paint them."""
        source = self.source
        if source is None:
            self._stop_ticking()
            return
        if source.complete:
            self._stop_ticking()
        self.sheet.refresh()

    def _follow_cursor(self) -> None:
        """``row/rows`` -- ``rows+`` and the share walked while the file is
        still being walked -- and the sort in force (a departure)."""
        sheet = self.sheet
        sheet.generation  # noqa: B018 - read, so the walk's progress repaints this
        source = self.source
        if source is None:
            self.indicator.text = ""
            return
        count = f"{sheet.row + 1 if sheet.count else 0}/{source.count:,}"
        if not source.complete:
            count += f"+ {source.percent}%"
        if sheet.sort is not None:
            column, descending = sheet.sort
            count += f" {table.column_name(column)}{'↓' if descending else '↑'}"
        self.indicator.text = count

    def list_name(self) -> str:
        """Window > List's line: DN's ``cmGetName``, *Spreadsheet - * and the name."""
        return tr("Spreadsheet - {path}").format(path=self.title)

    def short_name(self) -> str:
        return PurePosixPath(str(self.title)).name

    def close(self) -> None:
        self._stop_ticking()
        if self.source is not None:
            self.source.close()
        super().close()
        if self.use_set is not None:
            import asyncio

            from navigator.lib.drives import usefile

            use, self.use_set = self.use_set, None
            asyncio.get_running_loop().run_in_executor(None, usefile.discard, use)

    async def on_close_viewer(self, event: CloseViewer) -> bool:
        """F3, as in the viewer: Midnight Commander's way out, beside Esc."""
        self.request_close()
        return True

    def refusal(self, command: Any) -> str:
        if isinstance(command, ContinueSearch | SearchAgain):
            from navigator.widgets.viewer.sheet_find_dialog import sheet_find_dialog

            return "" if (self._search or sheet_find_dialog.LAST) else tr("Nothing has been searched for yet")
        if isinstance(command, (SortColumn, ChangeWidth, ShowCell)) and not self.sheet.columns:
            return tr("The file has no cells")
        return super().refusal(command)

    async def _say(self, prompt: str, title: str | None = None) -> None:
        await Dialog(title=tr("Error") if title is None else title, prompt=prompt,
                     buttons="ok").execute(self.application)

    # -- Enter -----------------------------------------------------------------------

    async def on_show_cell(self, event: ShowCell) -> bool:
        self.spawn(self.show_cell())
        return True

    async def show_cell(self) -> None:
        """The cursor's cell, whole: its lines, wrapped as *Memo view* wraps."""
        from navigator.widgets.viewer.db_list_dialog import DBListDialog
        from navigator.widgets.viewer.db_window.db_window import _wrapped

        sheet = self.sheet
        if not sheet.count:
            return
        text = sheet.cell()
        lines = [line for chunk in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
                 for line in _wrapped(chunk, 64)]
        title = tr("Cell {name}").format(name=table.cell_name(sheet.col, sheet.row))
        await DBListDialog(lines=lines, title=title, modal_width=69, modal_height=19).execute(self.application)
        sheet.focus()

    # -- the width -------------------------------------------------------------------

    async def on_change_width(self, event: ChangeWidth) -> bool:
        """``cmChangeWidth``: Left and Right resize until Enter or Esc."""
        self.sheet.resizing = True
        self.sheet.focus()
        return True

    # -- F5 --------------------------------------------------------------------------

    async def on_sort_column(self, event: SortColumn) -> bool:
        self.spawn(self.sort())
        return True

    async def sort(self) -> None:
        """The cursor's column ascending, then descending, then the file's
        order again -- the rows shown, never the file.  On a thread: every
        row is read; *Sorting* if it takes a while, and Stop leaves it as it was."""
        from navigator.lib.system.progress import run_with_progress
        from navigator.widgets.editor.loading import progress_box, refresh_box

        sheet, source = self.sheet, self.source
        if source is None or not sheet.columns:
            return
        column = sheet.col
        current = sheet.sort
        if current is not None and current == (column, True):
            # Round to the file's order.
            shown = sheet.file_row(sheet.row)
            sheet.order, sheet.sort = None, None
            sheet.go(row=shown)
            sheet.refresh()
            return
        descending = current is not None and current == (column, False)
        work = table.Work()
        order = await run_with_progress(
            self.application, lambda: table.sort_order(source, column, descending, work), work,
            lambda: progress_box(work, tr("Sorting")), refresh_box(work),
        )
        if order is None or work.stopped:
            return
        shown = sheet.file_row(sheet.row)
        sheet.order, sheet.sort = order, (column, descending)
        # The cursor stays on its row, wherever the sort put it.
        sheet.go(row=list(order).index(shown) if shown < len(order) else 0)
        sheet.refresh()

    # -- F6 --------------------------------------------------------------------------

    async def on_goto_cell(self, event: GotoCell) -> bool:
        self.spawn(self.goto_cell())
        return True

    async def goto_cell(self) -> None:
        """``cmGotoCell``: *Go to Cell Number*, then there -- a row past the
        ones found waits for the walk."""
        from navigator.widgets.viewer.goto_cell_dialog import GotoCellDialog

        answer = await GotoCellDialog(cell=self._last_goto).execute(self.application)
        self.sheet.focus()
        if answer is None:
            return
        column, row = answer
        sheet = self.sheet
        self._last_goto = table.cell_name(column if column is not None else sheet.col,
                                          row if row is not None else sheet.row)
        sheet.go(col=column, row=row)

    # -- F7, Shift+F7 ----------------------------------------------------------------

    async def on_find_cell(self, event: FindCell) -> bool:
        self.spawn(self.find_cell())
        return True

    async def on_continue_search(self, event: ContinueSearch) -> bool:
        self.spawn(self.search_again())
        return True

    async def on_search_again(self, event: SearchAgain) -> bool:
        self.spawn(self.search_again())
        return True

    async def find_cell(self) -> None:
        """``cmFindCell``: *Find*, then from the top (DN's ``SearchPos``
        ``-1, 0``)."""
        from navigator.widgets.viewer.sheet_find_dialog import SheetFindDialog

        search = await SheetFindDialog().execute(self.application)
        self.sheet.focus()
        if search is None:
            return
        self._search = search
        await self._find(search, row=-1, column=0)

    async def search_again(self) -> None:
        """``cmSearchAgain``: on from the cursor's cell."""
        from navigator.widgets.viewer.sheet_find_dialog import sheet_find_dialog

        search = self._search or sheet_find_dialog.LAST
        if search is None:
            await self.find_cell()
            return
        await self._find(search, row=self.sheet.row, column=self.sheet.col)

    async def _find(self, search: table.CellSearch, *, row: int, column: int) -> None:
        from navigator.lib.system.progress import run_with_progress
        from navigator.widgets.editor.loading import progress_box, refresh_box

        sheet, source = self.sheet, self.source
        if source is None:
            return
        work = table.Work(source.count)
        order = sheet.order
        hit = await run_with_progress(
            self.application,
            lambda: table.find(source, search, order=order, row=row, column=column, work=work),
            work, lambda: progress_box(work, tr("Searching")), refresh_box(work),
        )
        if work.stopped:
            return
        if hit is None:
            await self._say(tr("Search string not found"), title=tr("Find"))
            sheet.focus()
            return
        sheet.go(row=hit[0], col=hit[1])

    # -- Shift+F6 --------------------------------------------------------------------

    async def on_table_format(self, event: TableFormat) -> bool:
        self.spawn(self.table_format())
        return True

    async def table_format(self) -> None:
        """*Format*: the file read again with the delimiter, header and
        encoding chosen, from its start."""
        import asyncio

        from navigator.widgets.viewer.table_format_dialog import TableFormatDialog

        source = self.source
        if source is None:
            return
        dialect = await TableFormatDialog(source.dialect).execute(self.application)
        self.sheet.focus()
        if dialect is None or dialect == source.dialect:
            return
        self._stop_ticking()
        try:
            fresh = await asyncio.to_thread(source.with_dialect, dialect)
        except OSError as error:
            await self._say(tr("Cannot read the file: {error}").format(error=error.strerror or error))
            return
        await asyncio.to_thread(_first_screen, fresh)
        self.source = fresh
        self.sheet.show(fresh)
        app = self.application
        if app is not None and not fresh.complete:
            self._ticker = app.call_every(TICK, self._tick)

    # -- Shift+F4 --------------------------------------------------------------------

    async def on_view_sheet_as_text(self, event: ViewSheetAsText) -> bool:
        self.spawn(self.as_text())
        return True

    async def as_text(self) -> None:
        """The same file in F3's text view, at the cursor's row, in this
        window's place (a departure, as *Markup view*'s Shift+F4)."""
        from navigator.lib.config.file_history import open_viewer

        source, desktop = self.source, self.desktop
        if source is None or desktop is None:
            return
        offset = source.row_offset(self.sheet.file_row(self.sheet.row)) if self.sheet.count else 0
        try:
            window = await open_viewer(desktop, source.path, "text")
        except OSError as error:
            await self._say(tr("Cannot read the file: {error}").format(error=error.strerror or error))
            return
        if window is None:
            return
        take_place(window, self)
        window.title = self.title
        window.use_set, self.use_set = self.use_set, None
        window.viewer.seek(offset)
        self.close()


def take_place(window: Window, old: Window) -> None:
    """*window* where *old* is: zoomed as it is, or in its rectangle."""
    if old.zoomed == window.zoomed and old.zoomed:
        return
    if old.zoomed:
        window.toggle_zoom()
        return
    if window.zoomed:
        window.toggle_zoom()
    window.locate(old.x, old.y, old.width, old.height)
    if window.parent is not None:
        window.layout(window.parent.width, window.parent.height)


def _first_screen(source: table.TableSource) -> None:
    """The walk started, and waited on until a screenful is found -- or the
    file is done -- so the window opens with rows in it."""
    import time

    source.start()
    deadline = time.monotonic() + 2.0
    while not source.complete and source.records < 200 and time.monotonic() < deadline:
        time.sleep(0.005)


async def open_sheet(desktop: Any, path: Path, *, row: int = 0, dialect: table.Dialect | None = None) -> Any:
    """DN's ``New(PCalcWindow, Init(R, FileName))``: the file's window, zoomed
    and given the keyboard, at *row*.  The file is opened, guessed at and
    walked far enough for a screen on a thread; the rest of the walk goes on
    while the window is up.  ``OSError`` is the caller's."""
    import asyncio

    def opened() -> table.TableSource:
        source = table.TableSource(path, dialect)
        _first_screen(source)
        return source

    source = await asyncio.to_thread(opened)
    if row and not source.complete and source.records <= row:
        await asyncio.to_thread(source.wait)
    window = desktop.open(SheetWindow(source, row=row))
    window.sheet.focus()
    return window
