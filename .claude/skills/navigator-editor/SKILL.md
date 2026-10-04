---
name: navigator-editor
description: The internal editor (F4, DN's MICROED.PAS) -- navigator/editor/ (Document, columns, EditBuffer with undo, save), FileEditor and EditWindow, byte-for-byte round-tripping, editor commands named after DN's cm*, closing with must_ask, and the Editor menu. Use when changing the editor.
---

# The editor

- **F4 is DN's internal editor** (`MICROED.PAS`), being built in phases toward everything DN's editor had.
  `navigator/editor/` is the model (`Document`, `columns`, `EditBuffer` with undo, `save`); `FileEditor` is `TFileEditor`
  and `EditWindow` is `TEditWindow`, zoomed on the desktop with `TInfoLine` over the bottom frame.
- **A file round-trips byte for byte** -- tabs, each line's own terminator, non-UTF-8 bytes (`surrogateescape`) -- a
  departure from DN's rewriting. Saving renames a new file over the old one.
- **Every key is a command named after DN's `cm*`** in `FileEditor.keys` (`navigator/widgets/editor/commands.py`).
  `Widget.edits_text` makes the command line's Enter/Home/End/Tab and pastes step aside.
- **Stream blocks and the clipboard.** Shift with any movement marks (`_marking` wraps the movement handlers; the
  block grows from the cursor, or from its other end when the cursor stood on one). `FileEditor.block` is
  `(start, end)` in `Pos`, start first, or None; it persists while the cursor moves under *Persistent blocks* (DN's
  default). Off: a movement without Shift unmarks, typing/Enter/Tab/paste replace the block in one undo group
  (`_begin_replacing`), and Backspace/Del delete the block alone (`_deleting_block`). Either way it follows every edit, undo's included, through
  `EditBuffer.listeners` and `document.shifted` -- text inserted at the block's end stays outside it. Painted with
  `FileEditor::selected`. Ctrl+Ins (`ClipboardCopy`, `cmCopy`), Shift+Del (`ClipboardCut`), Shift+Ins
  (`ClipboardPaste`, which asks the application and types the `PasteEvent` that comes back), Ctrl+Del (`Clear`,
  `cmClear`); also Editor > Edit. Copies hand out plain `\n` breaks, pastes take the file's own. Not `Cut`/`Copy`/`Paste`:
  F5's `Copy` and `on_paste` (the paste event) already own those handler names. Ctrl+C/Ctrl+V stay WordStar's.
  The ^K/^Q commands are named after their `cm*` in `DN.DNR`'s `EDITOR COMMANDS` table (`BlockStart`, `Clear`,
  `UpcaseBlock`, `MoveBlockStart`, `BlockRead`...); the clipboard four keep their own names (above). Every ^K/^Q
  command in the table is here.
- **WordStar's ^K and ^Q** are navkit chords, each letter bound plain and with Ctrl (`_wordstar`): ^K B/K mark the
  start/end (with no block, the first waits for the other -- `_half_mark`, dropped by any edit), H (and Alt+H) hides the block or shows it again, C copies
  the block to the cursor and marks the copy, V moves it (refused with the cursor inside it), Y deletes it, I/U
  indent/unindent its lines by one blank (a column block at its left column; a leading tab gives way to spaces), `[`
  `]` `\` upper/lower/capitalise it, T marks the word, L the line; ^Q B/K go to its ends, ^Q Y deletes to the line's
  end, ^Q L undoes.
- **^K R / ^K W are DN's `BlockRead`/`BlockWrite`** (`MICROED.PAS`), also Editor > Edit's *Paste from...*/*Copy
  to...*, handled by `EditWindow` (dialogs and I/O; `FileEditor.block_file_text`/`read_block` are the text). The name
  comes from navml's `FileDialog` (`GetFileNameDialog`: titles *Copy block to*/*Paste from File*, labels *File
  ~N~ame*/*~P~aste from*, the shared `hsEditPasteFrom` history `edit_paste_from`), listing the active panel's
  directory. Writing joins lines with the Editor setup's *Line divisor* and ends without one; a column block, or a
  one-line block, writes its columns unpadded. An existing file is `CheckForOver`'s Yes/A~p~pend/Cancel (`Dialog`
  `yes-no-cancel` with `no` relabelled), a read-only one asks *Modify it anyway?* and gets its mode back afterwards;
  the write emits `FileSaved` (`cmRereadDir`). Reading turns column blocks off (`VertBlock := Off`) and marks what it
  put in.
- **Sort, ^K S / Alt+T** (`SortBlock`, DN's `SortBlock` in `EDITOR.PAS`, also Block > Sort): the lines a *column*
  block spans, ordered by its columns' text as plain strings (case-sensitive, as Pascal's `<`); a stream block gets
  `dlED_VertNeed`, "Vertical blocks need for this operation", word for word. Each line keeps the ending of the place it
  lands in. Departures: stable (DN's quicksort was not) and one undo step (DN dropped its undo record).
- **Calculate sum, Alt+Ins** (`CalcBlock`, DN's `CalcBlock`, also Block > *Calculate sum*): the numbers in a column
  block's columns, each with its blanks removed (`DelSpaces`) and read as `Val` would (a non-number counts 0),
  added up and put on the clipboard (`cmPutInClipboard`); the text is untouched and nothing is shown. Written as
  `Str(R:0:20)` less trailing zeros, but summed with `Decimal` (a departure: DN's `Real` printed binary error).
  DN's table also gave ^K^U to it, but `cmUnindentBlock` had ^K^U first and the menu shows Unindent there, so ^K U
  stays Unindent. A stream block gets `dlED_VertNeed`.
- **Print block, ^K P / Shift+F8** (`PrintBlock`, DN's `Print(On)` in `EDITOR.PAS`, also Editor > File > *Print
  block*): *Print N lines?* (`dlED_PrintQuery`), then the block's lines (`FileEditor.block_lines`, DN's
  `GetSelection`) to `navigator/printing.py`, which hands them to `lp` (else `lpr`) in an executor -- the system
  spooler standing for DN's `.PRN` file and print manager. LF line ends, no closing form feed. A refusal (no
  printer, no default destination) is shown as the spooler's own words.
- **Print file, F8** (`PrintFile`, DN's `Print(Off)`, also Editor > File > *Print*): the whole text the editor holds,
  saved or not (DN printed `FileLines`), less the empty line after a final break; same question and spooler as
  Print block (`EditWindow.print_lines`). `PrintFile` is one command, as `cmPrintFile` was: it lives in
  `navigator/commands.py` (re-exported by `manager/commands.py`) because the file manager's Ctrl+F9 answers it too
  (`navigator-file-ops`).
- **Bracket pair, Alt+Left / Alt+Right / ^Q[ / ^Q^]** (`BracketPair`, DN's `cmBracketPair`, `SearchFwd`/`SearchBwd`
  in `EDITOR.PAS`): on `(` `[` `{` the cursor goes forward to the matching close, on `)` `]` `}` back to the opener,
  across lines, counting only brackets of the same kind and blind to strings and comments, as DN was; no bracket under
  the cursor or no pair, and it stays. ^Q[ and ^Q^] are bound only in the forms the table gives.
- **The info line is `InfoLine`** (DN's `TInfoLine`, a `StaticText` beside `FileEditor`, styled by
  `EditWindow StaticText#info`): a left click on its block indicator runs `SwitchBlock` and one on its line:column
  `GotoLineNumber`, as `TInfoLine.HandleEvent` turned them into `cmSwitchBlock`/`cmGotoLineNumber`.
  `FileEditor.block_indicator()`/`place_indicator()` say where they stand, worked out from the text since the code
  may outgrow three digits; `code_indicator()` is its third place, `[nnn]` (`cmSpecChar`), which opens the
  character table. Every press on the line is the line's, so none reaches the frame.
- **The character table, Ctrl+P** (`AsciiTable`, DN's `cmASCIITable`/`cmSpecChar`, also Editor > Misc > *Character
  table* and the info line's code): `AsciiChart` (`shell/ascii_chart`, DN's `TASCIIChart`, 34 by 12) around
  `CharTable` (`shell/char_table`, `TTable`: 32 by 8 CP437 glyphs from `viewer.cp437`, block caret) and a report line
  (`TReport`). Arrows/Home/End move, a press or drag picks, Esc cancels, Enter/Ctrl+B/Ctrl+P or a double click take;
  a character typed that code page 437 has is taken at once. It reopens on the code last taken (`p` at first). The
  editor types what the chart shows -- the glyph, `│` for 179, the text being Unicode -- and a NUL for 0. Departure:
  centred, where DN reopened it where it was left. `AsciiTable` lives in `navigator/commands.py`: the shell answers
  it too (`console-command-line`), and an editor's ^B^V chord keeps Ctrl+B in the editor, as DN's table did.
- **Open, F3, and Save as, Shift+F2** (`LoadText`/`SaveTextAs`, DN's `cmLoadText`/`cmSaveTextAs`, `OpenFile` and
  `SaveFileAs`; also Editor > File): the name from navml's `FileDialog` via `EditWindow._ask_file` -- *Open a File*,
  *~N~ame*, an *~O~pen* button (`fdOpenButton`), history `edit_open`; *Save File As*, *~S~ave File As*, OK,
  `edit_save` -- listing the active panel's directory. Open offers a changed text a save first (Cancel keeps all),
  records the file being left, loads the new one into the same window and brings its record back; a file that will
  not open is said and the text stays (DN closed the window). Save as asks `_check_for_over`'s question without
  *Append* (a departure: appending the whole text elsewhere and then editing that file under its name lost what was on
  disk at the next F2), puts a read-only file's mode back, and the window takes the new name; `FileSaved` re-reads
  panels. `_check_for_over` is shared with ^K W, which keeps *Append*.
- **Save all, Ctrl+F2** (`SaveAll`, DN's `cmSaveAll`, a `GlobalMessage` of `cmSaveText`; also Editor > File): every
  editor window, this one first and the rest front to back, saved as F2 saves, each failure said and the rest going
  on. A departure: only changed texts are written, where DN's `SaveFile` rewrote every one. The application's Ctrl+F2
  (Hide right) is disabled with no console showing a file manager, so the key reaches the editor window.
- **Go to line, Alt+G** (`GotoLineNumber`, DN's `GotoLine`, also Editor > Search > *Go to line number...* and the
  info line): `GotoLineDialog` (`dlgGotoLine`'s *Goto Line*, a row taller like the viewer's *Goto Address*, history
  `goto_line`) opens with the number last typed, as `GotoLine`'s `const S` kept it; a number above 0 puts the cursor
  on that line at the same column (`FileEditor.go_to_line`, `ScrollTo(Delta.X, I-1)`), past the end on the last;
  anything else does nothing. DN shared its history with *Goto Address* (`hsdbSearch`); here each has its own.
- **A hidden block** (`block_hidden`, DN's `not BlockVisible`; ^K H / Alt+H toggle it): still marked (`marked`) and
  still following edits, but not painted and not acted on -- `has_block`, which the block commands' `enables` read,
  is DN's `BlockVisible and ValidBlock`. Marking anew shows it (`_set_block`/`_set_ordered`, `read_block`, `_unmark`).
- **Markers, ^K1-9 / ^Q1-9** (`PlaceMarker(n)`/`GotoMarker(n)`, DN's `cmPlaceMarker`/`cmGotoMarker` over `MarkPos`):
  `FileEditor.markers`, nine fixed `(line, col)` -- not moved by edits, as DN's were not. Going to one centres it
  (`Pos := Delta - Size div 2`) and, being a movement, unmarks under *Persistent blocks* off; an unset one does
  nothing. Kept in the edit history as `EditRecord.marks` (`fMarks`), `line:col` nine times comma-separated, and
  brought back whatever *Store editor position* says. The digit is bound alone, as the table has it.
- **^Q D/T** insert the date/time (`fileattr.DATE_FORMAT`/`TIME_FORMAT`, DN's D-M-Y and H:M:S, as the attributes
  dialog writes them; inserted even in overwrite; `_now` is the test hook). Column blocks take all the ^K commands.
  A pending chord shows as `^K` at the info line's end (a departure).
- **Column blocks** under `vertical_blocks` (Editor setup's *Vertical blocks*, seeded per editor and kept in the edit
  history; `SwitchBlock`, DN's `cmSwitchBlock`, switches it -- ^B^V and Editor > Options > *Vertical blocks*,
  ticked through `FileEditor.checks`. DN's block was two points either way, so the switch keeps it and reads it the
  other way: a stream block becomes the rectangle between its ends, a rectangle the stream from top-left to
  bottom-right; one enclosing nothing goes).
  `FileEditor.column_block` is two corner *cells* `(line, col)` -- columns, not indices, since a rectangle runs past
  short lines and across tabs -- and `rectangle` is `(top, left, bottom, right)`, right exclusive. Only one of
  `block`/`column_block` is ever set; marking code speaks of "ends" (`_here`, `_block_ends`, `_set_block`) so keys,
  Shift+click, drags and double-clicks serve both. A character belongs to the column it starts in
  (`columns.span`), so a tab straddling the left edge stays out. A copy hands out each line's piece without padding
  blanks, and remembers the padded pieces in `_COLUMN_CLIP` (newest only): pasting exactly that text back inserts a
  rectangle (`_insert_rectangle`: short lines padded to the column, lines added past the end, the cursor left at the
  top-left). A column block keeps its columns through edits and moves only by whole lines.
- **The mouse marks too.** A left press puts the cursor there and unmarks; a drag (captured) marks from the press,
  scrolling a line at a time past the top or bottom row; Shift+click extends the block as Shift+movement does; a
  double-click marks the word between `BREAK_CHARS`. A block marked by the mouse becomes the primary selection on
  release (`copy_to_clipboard(primary=True)`), and a middle click pastes the primary selection -- what the console and
  the input lines do. Ctrl+Ins still copies the block to the clipboard. Checked on a pty with SGR mouse bytes and
  `xclip -o`, not only with posted events.
- **Closing asks** through `Window.must_ask`/`ask_to_close` (`Valid(cmClose)`), which `request_close`, Close all and
  Alt+X all go through; `Dialog.buttons` has `yes-no-cancel`.
- **Shift+F4, *Edit new file*** (`cmXEditFile`, `EditNamed`, also File > Edit > Edit new file): `EditFileDialog` asks for a
  name (history `editfile`), relative to the active panel, `~` expanded; `Manager.edit_named` opens it with
  `open_editor(..., new=True)`, so a name that does not exist is an empty text saving creates. A directory or a missing
  parent directory is refused up front. With *Internal editor* off it goes to `$EDITOR`. DN's own dialog was not to
  hand; this one is shaped as F7's.
- **File Edit History (Alt+PgUp)**: DN's `TEditRecord`, the `EditRecord` model. It holds the window rectangle, cursor
  (`line`, `col`), scroll (`top`, `left`), `overwrite` and `vertical_blocks`, and is stored and restored as the
  viewer's is (see `navigator-viewer`); the rectangle, cursor and scroll only under *Store editor position*. **Open editors through `navigator.file_history.open_editor`.** DN's marks,
  block, highlighting, auto-indent and margins get columns when the editor has them: add the `field` lines to
  `edit_record.nml`, rebuild, and the table migrates itself.
- **While an editor window is active the bar has an *Editor* menu after *File***: DN's `dlgEditorMenu`, its seven menus
  nested as submenus, greyed where the feature is still to come.

## Read when

| Reference | Read when |
|---|---|
| `reference/editor.md` | the full design and the phases left |
