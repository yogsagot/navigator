## Tooltip backlog

Possible next tooltips, and changes to how tooltips work, collected after the first round (October 2026). Nothing
here is decided; each entry says what it would show, why it is worth it, and where it would go. The rules every
entry should keep are in `hover.md` (*Tooltips: hover that waits*) and the skills' tooltip notes: a tooltip says
what the screen leaves out -- a whole text that was cut, an exact figure that was rounded, a key, a meaning -- never
the caption again; user-visible text goes through `tr()`; a widget that paints several things answers per position
through `tooltip_at`.

**Already done**, for reference: option strips, window frame icons, the key bar, the clock, the window strip, menu
bar captions, 97 menu items, dialog buttons, settings-backed check boxes, radio groups and fields, input lines
(whole text while cut), list rows (whole text while cut), drop-down buttons, tabs, the panel's column titles and info
lines, the panel's rows (whole name while cut or scrolled, a link's target, a cut owner or path), the panel's title, F2's user menu items (what each will run), the bookmarks box, the character tables (Unicode and ASCII), the root mark, the panel divider, the remaining dialogs' check boxes (the unclear
items only), the directory trees, Miller columns (inherited from the panel). Scroll bars
deliberately have none (`tooltip_passes = False`).

### Ways of working (infrastructure)

| Idea | Why | Where |
|---|---|---|
| **A key that shows the focused widget's tooltip** (Shift+F1, say), at the caret, until the next key | A terminal without mode 1003 never reports a resting pointer, so it gets no tooltips at all; the keyboard user gets none either | `navkit/application.py` beside `_show_tooltip`; ask `tooltip_at` at the widget's `cursor_position()` |
| **Menu tooltips on the key bar while a menu is open** -- the highlighted item's, as Turbo Vision's `THintStatusLine` did | Keyboard navigation of the menus then shows the 97 item tooltips too; close to DN's own look (a hint line) | `navml/widgets/menu/menu_bar/menu_session.py` publishing the current entry; `KeyBar` drawing it |
| **Why a command is disabled** -- a `disabled_reason` next to `enables()`, shown on a greyed menu item, key bar item or button | "Greyed" says nothing about *what to do*: no selection, not on a remote drive (`Manager._LOCAL_ONLY`), nothing to undo | `navkit/commands.py`; `Manager.enables` in `navigator/widgets/manager/manager/manager.py` |
| **Instant follow-on tooltips**: once one is showing, moving onto the next item shows its tooltip without the full delay (for, say, 2 s) | Sweeping across the key bar or a menu currently restarts the wait at every item | `Application._drop_tooltip` / plain-motion branch |
| **Styled tooltips**: a key in the key bar's key colour, `~bright~` runs as the info lines use | `Close (Ctrl-F4)` reads better with the key set apart | `navkit/tooltip.py` rendering runs; a `Tooltip::key` part |
| **A test sweep**: every menu bar caption and every settings-page control has a tooltip; every `tooltips:` list matches its items | The alignment test covers the Settings pages only; a new page or menu could silently lack one | `tests/test_tooltip.py` |

### High value

| Where | Tooltip | Why | Pointer |
|---|---|---|---|

### Medium

| Where | Tooltip | Pointer |
|---|---|---|
| **Synchronize window** | What a row's action mark means (copy right/left, delete, skip) and why the comparison chose it | `navigator/widgets/manager/sync_list` |
| **Volumes** | The whole mount point and device; the file system's options | `navigator/widgets/shell/volume_list` |
| **Key bindings dialog** | The command's description, every key bound to it | `navigator/widgets/setup/key_bindings_dialog/binding_list.py` |
| **Viewer and editor info lines** | The whole path; on the editor's line:column, *Go to line (Alt-G)*, which a click already does | `navigator/widgets/viewer/file_viewer`, `navigator/widgets/editor/file_editor` |
| **Hex and dump view** | The byte under the pointer: offset, hex, decimal, character | `navigator/widgets/viewer/file_viewer` |
| **Compare files** | A changed line's counterpart's line number; the change's kind | `navigator/widgets/viewer/diff_view` |
| **File Attributes** | The permission grid's Set UID / Set GID / Sticky explained; each *Flags* entry (*No COW*, *Top dir*) explained | `navigator/widgets/file_ops/attr_dialog` |
| **Colors dialog** | A palette entry's DN slot and what it colours; a colour cell's name | `navigator/widgets/setup/colors_dialog` |
| **Calendar** | A day's weekday and ISO week number | `navigator/widgets/shell/calendar_window` |
| **Info panel** (Ctrl+L) | Whole values where cut; exact bytes where rounded | `navigator/widgets/manager/info_panel` |
| **Command line** | The whole current directory where the prompt cuts it | `navigator/widgets/shell/command_line` |

### Low

| Where | Tooltip | Pointer |
|---|---|---|
| Calculator keys | The function behind the terse ones (`MR`, `M+`, `±`) | `navigator/widgets/shell/calculator_window` |
| The game | Score rules beside the score; the next figure's name | `navigator/widgets/game` |
| Progress boxes | Exact bytes done and to go where the bar rounds; an estimate of the time left | `navigator/lib/system/progress.py` and its boxes |
| History boxes (commands, files viewed/edited) | When an entry was last used | `navigator/widgets/shell/file_record_list`, `command_history_dialog` |
| Trash can (≡ > Trashcan) | What dropping on it does | `navigator/widgets/shell/trash_can.py` |
| A window's title | *Double-click to zoom, drag to move* | `navml/widgets/window/window.py` (`Window.tooltip_at`, the `move` hit) |
| Standalone labels | Their linked control's tooltip, where the label is not inside a field | `navml/widgets/dialog/label` |
