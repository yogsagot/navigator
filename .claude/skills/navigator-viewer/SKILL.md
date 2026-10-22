---
name: navigator-viewer
description: The internal file viewer (F3, DN's FVIEWER.PAS) -- navigator/lib/viewer/__init__.py (ViewSource, pread chunks), FileViewer in FileWindow, text/hex/dump modes, wrap, filters, Shift+F6 encodings (DN's XLT) and Shift+F5 Save as, the dBase viewer (dbf.py, DBWindow, As DataBase), bytes-regex search on a thread with SearchJob and SearchProgress, go to address, the View menu, and Ctrl+Q QuickViewer. Use when changing the viewer or quick view.
---

# The file viewer

- **F3 is DN's internal viewer** (`FVIEWER.PAS`). `navigator/lib/viewer/__init__.py` is the model: `ViewSource` uses `pread` into
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
  threads). A file read across a network (`ChunkedSource`) is lexed too, a window of `REMOTE_LEX_BACK`/`AHEAD`
  (128 KiB, two chunks) each way, read on the thread through `ChunkedSource.read_blocking` (one read at a time
  with the fetchers, under the source's `_reader_lock`) and keyed on the origin's URL; cells carry byte offsets, so a row finds its spans by `bisect` and wrapped rows need nothing more.
  View > *File type* picks the lexer by hand (`SetFileType`, `FileViewer.file_type`, `ViewRecord.file_type`; the
  editor skill has the rules), text mode only. A file of 256 KiB or less is lexed whole and exactly; deeper into a bigger one, a comment or string opened more than
  `LEX_BACK` above is not known to be open -- the documented limit. The window is keyed on path, encoding, size and file type
  (Shift+F6 re-lexes) and never asked for twice, so a line longer than it cannot loop.
- **Markup view: Markdown, reStructuredText, HTML and PDF rendered**, a departure (DN's viewer had none): Shift+F4, View > *Markup view*
  (`SwitchRendered`, handled by `FileWindow` and by `QuickViewer`, ticked; the strip's last item,
  `MD`, `RST` or `HTML` (`M↓`, `rST`, `</>` as symbols), dropped first from a short frame) renders the file rather than showing its source, in text mode only.
  `FileViewer.rendered` is the switch; `format_by_name` says `html` (`[viewer] render_html` + `html_masks`), `rst`
  (`render_rst` + `rst_masks`) or `markdown` (`render_markdown` + `markdown_masks`) or "", which seeds it in `open()`; `render_format` is that, else
  `markdown` (a `.txt` switched on reads as Markdown). `{Markdown}`/`{reST}`/`{HTML}` follows the info line (`md_mark`,
  `render_mark`): plain while on, struck through (`Style.strike`, SGR 9) while off for a file the masks name, absent
  otherwise; a press on it switches (`FileWindow.on_mouse_click`). Styled by class (`StaticText.rendered`, `.off`
  struck), in the info line's (`name: "info"`) frame colours. No checkboxes (the Editor/Viewer page has no rows for
  them). Kept as `ViewRecord.rendered` (`on`/`off`, empty for the masks' say).
  **The model is five modules.** `navigator/lib/viewer/layout.py` is the format-free part: `Row`/`Layout`, `_wrap`,
  and `Builder`, whose block methods (`heading`, `paragraph`, `code`, `table`, `rule`, `quote`, `push`/`pop`) make
  the rows. `markdown.py` walks markdown-it-py's tokens into it (CommonMark plus GFM tables and strikethrough).
  `rst.py` walks docutils' document tree into it: sections as headings by depth (a
  title's `line` is its underline's, so one back), lists of every enumerator kind, admonitions as a quote under their
  name, definition and field lists indented, grid and simple tables, `code-block`s lexed here (`syntax_highlight:
  none`) -- docutils puts a directive's `line` after it, so `code_line` finds the first line's text near it.
  `include` and `raw` are off and every warning is quiet (`report_level`/`halt_level` 5): nothing outside the file is
  read, and a document with errors renders what it can. `html.py` walks the stdlib `html.parser` into it, as `lynx -dump` reads a page: `<title>` first,
  `head`/`script`/`style` hidden (`head` ends at the first body element, closed or not), blanks run together, lists
  with unclosed `<li>`, `pre` coloured by its `language-*` class, tables gathered then drawn, `a href` as links, `img`
  as `[alt]`; an end tag closes its own element wherever it is open, so broken HTML degrades. `pdf.py` reads a PDF
  with pypdf (`[viewer] render_pdf` + `pdf_masks`, `{PDF}`): each page a `Page N of M` heading, its `extract_text()`
  in paragraphs (lines joined between blank lines, reflowed), a rule between pages; pictures are not shown, a
  password other than the empty one raises (source shown). Its rows' `src` are **synthetic** -- each page an even
  share of the file, its paragraphs spread across it -- since the text sits in compressed streams; so F7, which
  searches the source bytes, does not find rendered PDF text. Its limit is `PDF_LIMIT` (64 MiB), not
  `RENDER_LIMIT`. Every reader reads the
  **whole** file, so one over `RENDER_LIMIT` (4 MiB) stays source. The layout is made on a thread (`_RENDERER`,
  `_lay_out` dispatching through `RENDERERS`, reading across a network through `read_blocking`), keyed on where,
  encoding, size, width, glyph tier and format, never asked for twice; until one lands the source (first time) or the
  last layout is painted. **Rendered rows are not byte ranges**: each carries `src`, the offset of its block's source
  line (a code or table row, its own line; in HTML, the line of the tag the block began at), and `block`.
  `render_row` is the row on top and `top` follows it at that row's `src`, so the scroll bar, the view history and
  switching back (`toggle_rendered`, `seek(top)`) keep their place by block. Paragraphs reflow to the width, so Wrap
  and ¶ are greyed while it renders and nothing scrolls sideways. A search still runs over the source bytes;
  `show_hit` goes to the block holding the hit, and `_render_marks` marks the hit's text found again (blanks run
  together, case aside) among that block's rows -- unmarked if the markup split it. Cells are classes on
  `FileViewer::md` (`heading h1..h6`, `strong`, `emph`, `strike`, `code`, `code block`, `link` with an OSC 8 URL,
  `image`, `bullet`, `quote`, `rule`, `table`, `th`, `html`), styled in `navigator.nss` from existing theme
  variables only so every theme has them; a code block's tokens are `token` classes, the highlight's foreground
  over `md.code`.
- **The option strip and Hidden characters** -- see `navigator-editor`, which has both; the viewer's strip is
  `option_items.viewer_items`: the mode (`HexMode`, cycles), Wrap (`Unwrap`), Hi, ¶ (`SwitchHiddenChars`, handled
  and ticked by `FileWindow`), the encoding (`ChooseEncoding`), the file type and MD/HTML (`SwitchRendered`); Wrap, Hi, ¶ and the type are text
  mode only, greyed in hex/dump. *Hidden characters* (View > *Sh~o~w hidden characters*, the editor's caption, its `o` the one letter free; Ctrl+Shift+8) marks text mode only:
  `FileViewer._hidden_row` reads each row's shown bytes and its last two (the ending) at paint time; the decoders
  are untouched, and the filter's `·` is told from a blank's by being faint. `[viewer] show_options`/`show_hidden`.
- **While a viewer window is active the bar has a *View* menu after *File*** (modes, filters and wrap ticked, search, go
  to, close) -- see `navml-windows-menus` for how a window's menu joins the bar.
- A search still running after two ticks shows DN's *Search Progress* box (`TWhileView`: gauge, percentage, Stop), fed
  through a `SearchJob` the thread writes and the loop reads. It uses the library's `ProgressBar`. It runs through
  `navigator.lib.system.progress.run_with_progress`, which **stops the job whenever the task ends with the work unfinished** --
  a viewer closed or Navigator quitting mid-search used to leave the thread reading to EOF, and `asyncio.run` waited.
- **Opening is on a thread too**: `open_viewer` is async, building the `ViewSource` (stat, open, `/proc`'s
  read-whole) through `run_with_progress` and handing it to `FileWindow(source=...)`/`FileViewer.open(source=...)`;
  *Reading file* after `SLOW_PROGRESS_DELAY`, Cancel opens nothing. The quick view opens its file through
  `navml.background.Background` and shows only what the cursor is still on when it lands.
- **Ctrl+Q is DN's quick view** (`QuickViewer`, a framed `FileViewer`), standing in the passive panel's place through
  `Manager.switch_view`; it follows the active panel's cursor, and Tab moves the keyboard in and out. Its right-click
  menu is its own (`QuickViewer.context_menu`, set over the viewer's; a departure, asked for): *~V~iew* (the panel's
  F3, on the same file), *~M~arkup view*, *~C~lose quick view* (Ctrl+Q) -- the F3 window's greyed nearly all of itself
  here, and its *Close* closed the file manager. `context_focus` is off, so the keyboard stays with the panel: closing
  the view while it holds the keyboard gives it to the panel put back (DN's `SwitchView`), and the next Ctrl+Q then
  stands on the other side.
- **File View History (Alt+PgDn)**: DN's `TViewRecord`. Each file's window rectangle (scaled to the desktop, as
  `AdjustToDesktopSize` did), mode, wrap, filter, `top`, `x_delta` and hex `cursor` are written to the `ViewRecord`
  model. That happens when a viewer opens on a file with no record, and when it closes by any route, Alt+X included
  (`Navigator.on_stop`). The record is restored by `FileWindow.recall_history()` once the window is on its desktop.
  **Open viewers through `navigator.lib.config.file_history.open_viewer`**, never `desktop.open(FileWindow(...))`, or nothing is
  restored. As Text / As Hex pass a mode, which wins over the record's. Gated on Interface's *Track viewing history*; the rectangle, `top`, `x_delta` and `cursor` come
  back only under *Store viewer position* as well.
  The dialog and the list are `FileHistoryDialog`/`FileRecordList` (`shell/`). The key bar names the list's own keys,
  *Space Pin*, *Shift+↑↓ Move*, *←→ Pinned* (`FileHistoryDialog.key_hints`; a departure, asked for). The Ctrl+Q quick viewer records nothing.
- **The dBase viewer** (File > View > As DataBase, `ViewAsDataBase`; F3 on a `.dbf`, DN's `ViewFile` `XT = '.DBF'`):
  `navigator/lib/viewer/dbf.py` is `TDBFile` -- header, fields, records by `pread` through a cache, memos from `.fpt`/`.dbt`,
  cp437 text, a file whose fields do not add up refused (`DBFError`; F3 then falls back to the text viewer, As
  DataBase says so). `DBWindow`/`DBViewer` (`viewer/db_window/`) are `TDBWindow`/`TDBViewer`: field names over the
  records, the delete flag first, a cell the cursor (`Delta`), whole fields scrolled across (`Pos`), dates
  `DD-MM-YYYY` as the panels', `record/records` over the bottom frame; Enter/arrows/Home/End/PgUp/PgDn/Ctrl+PgUp/PgDn,
  mouse quadrants. F2 *Structure of*, F3 *Memo view* (`DBListDialog`), F4 edits the cell in place (`EditLineDialog`,
  history `edit_dbf`; L flips T/F; refused write-protected), F7 *Search* (`DBSearchDialog`, `dlgDbFind`; DN looked
  at one field a record by a slip, every one in scope is looked at here), Shift+F7/Ctrl+L again. A file with no
  records shows *Empty database* and opens nothing. Colours are the dBase group [166]-[171]. Not kept in a desktop.
  Its own *View* menu joins the bar after *File* while it is active (a departure, asked for: DN's had the key bar
  alone): *Fields...* F2, *Memo view* F3 (greyed off a memo field, `DBWindow.enables`), *Edit field...* F4,
  *Search...* F7, *Search again* Shift+F7, *Close*. The grid's right-click menu (`DBViewer.context_menu`) is the same six; a
  right click on a cell first makes it the cursor's (`cell_at`, `prepare_context`).
- Commands: `navigator/widgets/viewer/commands.py`.

- **Every bound key is on the View menu** (a departure, asked for): F4 and F6, which cycle, are *He~x~/Text/Dump*
  (`HexMode`) and *Fi~l~ter* (`AddFilter`) above the entries that pick one mode or filter, on the context menu too.
  Only Ctrl+L (`SearchAgain`, *Search again*'s second key) and F3 (`CloseViewer`) stay uncaptioned, as DN and MC had them.

## Read when

| Reference | Read when |
|---|---|
| `reference/file-viewer.md` | the full design and what is deferred |
