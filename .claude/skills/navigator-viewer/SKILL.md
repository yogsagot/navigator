---
name: navigator-viewer
description: The internal file viewer (F3, DN's FVIEWER.PAS) -- navigator/viewer.py (ViewSource, pread chunks), FileViewer in FileWindow, text/hex/dump modes, wrap, filters, Shift+F6 encodings (DN's XLT) and Shift+F5 Save as, the dBase viewer (dbf.py, DBWindow, As DataBase), bytes-regex search on a thread with SearchJob and SearchProgress, go to address, the View menu, and Ctrl+Q QuickViewer. Use when changing the viewer or quick view.
---

# The file viewer

- **F3 is DN's internal viewer** (`FVIEWER.PAS`). `navigator/viewer.py` is the model: `ViewSource` uses `pread` into
  cached chunks, **never `mmap`**, so a truncated log cannot `SIGBUS` Navigator. `FileViewer` inside `FileWindow` is
  `TFileViewer` inside `TFileWindow`; it opens zoomed on the desktop with the scroll bar on the frame and `TViewInfo` over
  the bottom edge.
- **Positions are byte offsets and nothing counts lines**, so a gigabyte opens at once. Text is UTF-8; an undecodable byte
  or a control is its CP437 glyph.
- Keys: F4 cycles text/hex/dump, F2 wraps, F6 filters, F7/Shift+F7/Ctrl+F7 search (a bytes regex, on a thread), F5 goes
  to a hex address. Esc closes, and so does F3, uncaptioned (mc's key, a departure). File > View > As Text / As Hex open
  it in either mode. Read-only for now, so Shift+F2's *Store* (DN's hex-edit `WriteModify`) stays greyed.
- **Shift+F6, File > Encoding** is DN's `cmLoadXlatTable`: instead of an `XLT\*.XLT` table, a `PopupMenu` of one-byte
  code pages (`viewer.ENCODINGS`, *UTF-8* first and meaning none). `FileViewer.set_encoding` puts `byte_table(codec)` on
  `ViewSource.table`, which `line()` (and so wrapping and scrolling), the hex and dump rows and `compile_search(...,
  encoding=)` all go through; the info line ends `{CP866}`. Controls stay the VGA's glyphs. Not kept in the view record.
- **Shift+F5, File > Save as** is `cmSaveAll`: DN's *Save File As* file dialog (history `edit_save`, the editor's), and
  `viewer.save_as` writes the file through a temporary beside it -- as it is, or read in the chosen code page and
  written in UTF-8, as DN wrote through its `Xlat`; `FileSaved` then re-reads the panels.
- **Syntax highlight**, a departure (DN's viewer had none): the editor's highlighting (`navigator-editor` has the
  rules, `highlight.ini` and the `::token` part) in text mode only, `FileViewer::token` taking the editor's highlight
  foregrounds over the viewer's own background -- the quick view's too. `viewer.syntax_highlight` (on), View >
  *Syntax highlight* (the editor's `SwitchHighLight`, handled by `FileWindow`, ticked), `ViewRecord.highlight`.
  Nothing counts lines, so a thread reads and lexes a byte window, from the first whole line after `top - LEX_BACK`
  to `top + LEX_AHEAD` (256 KiB each way, `_lex_window`, its own `open` -- `ViewSource`'s chunk cache is not for
  threads); cells carry byte offsets, so a row finds its spans by `bisect` and wrapped rows need nothing more.
  View > *File type* picks the lexer by hand (`SetFileType`, `FileViewer.file_type`, `ViewRecord.file_type`; the
  editor skill has the rules), text mode only. A file of 256 KiB or less is lexed whole and exactly; deeper into a bigger one, a comment or string opened more than
  `LEX_BACK` above is not known to be open -- the documented limit. The window is keyed on path, encoding, size and file type
  (Shift+F6 re-lexes) and never asked for twice, so a line longer than it cannot loop.
- **While a viewer window is active the bar has a *View* menu after *File*** (modes, filters and wrap ticked, search, go
  to, close) -- see `navml-windows-menus` for how a window's menu joins the bar.
- A search still running after two ticks shows DN's *Search Progress* box (`TWhileView`: gauge, percentage, Stop), fed
  through a `SearchJob` the thread writes and the loop reads. It uses the library's `ProgressBar`. It runs through
  `navigator.progress.run_with_progress`, which **stops the job whenever the task ends with the work unfinished** --
  a viewer closed or Navigator quitting mid-search used to leave the thread reading to EOF, and `asyncio.run` waited.
- **Opening is on a thread too**: `open_viewer` is async, building the `ViewSource` (stat, open, `/proc`'s
  read-whole) through `run_with_progress` and handing it to `FileWindow(source=...)`/`FileViewer.open(source=...)`;
  *Reading file* after `SLOW_PROGRESS_DELAY`, Cancel opens nothing. The quick view opens its file through
  `navml.background.Background` and shows only what the cursor is still on when it lands.
- **Ctrl+Q is DN's quick view** (`QuickViewer`, a framed `FileViewer`), standing in the passive panel's place through
  `Manager.switch_view`; it follows the active panel's cursor, and Tab moves the keyboard in and out.
- **File View History (Alt+PgDn)**: DN's `TViewRecord`. Each file's window rectangle (scaled to the desktop, as
  `AdjustToDesktopSize` did), mode, wrap, filter, `top`, `x_delta` and hex `cursor` are written to the `ViewRecord`
  model. That happens when a viewer opens on a file with no record, and when it closes by any route, Alt+X included
  (`Navigator.on_stop`). The record is restored by `FileWindow.recall_history()` once the window is on its desktop.
  **Open viewers through `navigator.file_history.open_viewer`**, never `desktop.open(FileWindow(...))`, or nothing is
  restored. As Text / As Hex pass a mode, which wins over the record's. Gated on Interface's *Track viewing history*; the rectangle, `top`, `x_delta` and `cursor` come
  back only under *Store viewer position* as well.
  The dialog and the list are `FileHistoryDialog`/`FileRecordList` (`shell/`). The Ctrl+Q quick viewer records nothing.
- **The dBase viewer** (File > View > As DataBase, `ViewAsDataBase`; F3 on a `.dbf`, DN's `ViewFile` `XT = '.DBF'`):
  `navigator/dbf.py` is `TDBFile` -- header, fields, records by `pread` through a cache, memos from `.fpt`/`.dbt`,
  cp437 text, a file whose fields do not add up refused (`DBFError`; F3 then falls back to the text viewer, As
  DataBase says so). `DBWindow`/`DBViewer` (`viewer/db_window/`) are `TDBWindow`/`TDBViewer`: field names over the
  records, the delete flag first, a cell the cursor (`Delta`), whole fields scrolled across (`Pos`), dates
  `DD-MM-YYYY` as the panels', `record/records` over the bottom frame; Enter/arrows/Home/End/PgUp/PgDn/Ctrl+PgUp/PgDn,
  mouse quadrants. F2 *Structure of*, F3 *Memo view* (`DBListDialog`), F4 edits the cell in place (`EditLineDialog`,
  history `edit_dbf`; L flips T/F; refused write-protected), F7 *Search* (`DBSearchDialog`, `dlgDbFind`; DN looked
  at one field a record by a slip, every one in scope is looked at here), Shift+F7/Ctrl+L again. A file with no
  records shows *Empty database* and opens nothing. Colours are the dBase group [166]-[171]. Not kept in a desktop.
- Commands: `navigator/widgets/viewer/commands.py`.

## Read when

| Reference | Read when |
|---|---|
| `reference/file-viewer.md` | the full design and what is deferred |
