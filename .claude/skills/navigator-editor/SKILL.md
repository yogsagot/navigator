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
  `(start, end)` in `Pos`, start first, or None; it persists while the cursor moves (DN's *Persistent blocks*, the
  default; the setting itself is still unread) and follows every edit, undo's included, through
  `EditBuffer.listeners` and `document.shifted` -- text inserted at the block's end stays outside it. Painted with
  `FileEditor::selected`. Ctrl+Ins (`ClipboardCopy`, `cmCopy`), Shift+Del (`ClipboardCut`), Shift+Ins
  (`ClipboardPaste`, which asks the application and types the `PasteEvent` that comes back), Ctrl+Del (`ClearBlock`,
  `cmClear`); also Editor > Edit. Copies hand out plain `\n` breaks, pastes take the file's own. Not `Cut`/`Copy`/`Paste`:
  F5's `Copy` and `on_paste` (the paste event) already own those handler names. Ctrl+C/Ctrl+V stay WordStar's. Still
  to come: column blocks (`vertical_blocks`), the `^K` block commands, unmarking (`^K H`), mouse marking.
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
