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
- **Closing asks** through `Window.must_ask`/`ask_to_close` (`Valid(cmClose)`), which `request_close`, Close all and
  Alt+X all go through; `Dialog.buttons` has `yes-no-cancel`.
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
