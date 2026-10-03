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
  `UpcaseBlock`, `MoveBlockStart`, `BlockRead`...); the clipboard four keep their own names (above). Still in the table
  and not yet here: `cmHideBlock`'s second key Alt+H, `cmSwitchBlock` (^B^V, column blocks on and off),
  `cmPlaceMarker`/`cmGotoMarker` (^K1-9/^Q1-9), `cmSortBlock`, `cmCalcBlock`, `cmPrintBlock`, `cmBracketPair`.
- **WordStar's ^K and ^Q** are navkit chords, each letter bound plain and with Ctrl (`_wordstar`): ^K B/K mark the
  start/end (with no block, the first waits for the other -- `_half_mark`, dropped by any edit), H unmarks, C copies
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
- **^Q D/T** insert the date/time (`fileattr.DATE_FORMAT`/`TIME_FORMAT`, DN's D-M-Y and H:M:S, as the attributes
  dialog writes them; inserted even in overwrite; `_now` is the test hook). Column blocks take all the ^K commands.
  A pending chord shows as `^K` at the info line's end (a departure).
- **Column blocks** under `vertical_blocks` (Editor setup's *Vertical blocks*, seeded per editor and kept in the edit
  history; Editor > Options > *Vertical blocks* switches it, ticked through `FileEditor.checks`, and unmarks).
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
