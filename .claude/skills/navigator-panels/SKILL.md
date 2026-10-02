---
name: navigator-panels
description: The file manager window and its panels -- Manager (manager.nml/manager.py), Panel and DirEntry, view modes (Ctrl+Y simple/detailed/list), name scrolling, tagging (Insert, Space, Gray +/-/*, Select/Unselect group, SelectDialog), Ctrl+S quick search, Ctrl+H hidden files, type marks and icons, Backspace to parent, re-read keeping the cursor, Ctrl+F1/Ctrl+F2/Ctrl+P hiding sides, switch_view, active/passive panel. Use when changing how files are listed, selected or navigated.
---

# The file manager and its panels

`navigator/widgets/manager/`: the `manager/` window, `panel/` (whose `panel.py` carries `DirEntry` beside `Panel`), and
`select_dialog/`. **`manager.py` is the worked example of a converted screen**: the document holds the tree and
geometry; Python holds the keys, `active_panel` and the paths markup may not bind (`left.path`, `right.path` are seeded
after `super().__init__()` -- see `navml-markup`). `Panel` assigns `path` and lets listing, cursor and scroll follow.
`Manager.passive_panel` names the other panel. `manager.nml` holds Tab, Alt+R/Ctrl+R and F2-F8. Commands live in
`navigator/widgets/manager/commands.py`.

## Movement and reading

- Arrows/PgUp/PgDn/Home/End move, Enter descends, Ctrl+R/Alt+R re-reads. **A re-read keeps the cursor on its entry**
  (`Panel.reload`, DN's `RereadDir`); only a change of directory starts at the top.
- `Panel.on_double_click` enters the clicked row (a directory or `..`) -- the press already moved the cursor. What needs
  the desktop (activating the other panel on a press, the wheel, console scrollback) stays on
  `Navigator.on_mouse_click`, which returns False while `app.modal` is set.
- **Backspace goes to the parent** (`GoParent(by_key=True)`, DN's `kbBack` under `fmoBackGoesBack`, `Panel.go_up`,
  cursor on the directory left) while the line is empty; Ctrl+PgUp (`_CtrlPgUp`) and Shift+Backspace whatever it holds.
- **Enter on an executable runs it**; Ctrl+Enter inserts the name (see `console-command-line`).

## View modes (Ctrl+Y, DN's `cmToggleShowMode`)

Per panel: `Panel.view_mode`, `cycle_view_mode`, and *Panel > View mode* (a menu entry DN never had).
- *simple*: name and size.
- *detailed*: Name taking the rest │ Size │ Attr `rwxr-xr-x` │ Owner `user:group` │ Date (**modification** time,
  `DD-MM-YY hh:mm`, since Linux has no portable creation time). Owner is a departure, 5-17 cells as the longest listed
  (`DirEntry.display_owner`, names cached, a number where there is none). Owner, then Attr, then Date drop when the name
  would fall under 12 cells.
- *list*: names alone in columns, each as wide as its longest name capped at half the panel; Left/Right move a column as DN's `kbLeft`/`kbRight` did.
- A too-long name ends in `...` (`fit_text`, in cells) and starts with one while scrolled (`window_text`). In simple and
  detailed, Left/Right scroll every name a cell (`ScrollNames`, `Panel.name_scroll`, clamped, reset by directory or mode
  change) -- disabled while the command line has text, so the caret moves.
- Non-simple modes have a heading row in *Column title* `[165]` (`Panel::heading`) and single `│` rules in the frame's
  colours (`Panel::divider` on `$panel-fg`/`$panel-bg`, a departure from DN's `[86]`), meeting the frame in the tee
  `Widget.box_joins()` gives (`┬┴`/`╤╧`) wherever title/footer does not stand.
- Every mode keeps a gutter left of the name: the Nerd tier's two-cell icon, or one cell of mc's type mark
  (`DirEntry.type_mark`: `/ * @ ~ ! = - + |`). Rows are coloured by file type -- see `colours-themes-glyphs`.

## Hidden files (Ctrl+H)

`ToggleHidden`, `Panel.show_hidden`, `toggle_hidden`, per panel, shown by default -- our key (it took DN's *Directory
Branch*, whose caption was dropped), where DN's `ossShowHidden` was a system option. The re-read keeps the cursor; a tag
on a name it hides is dropped. *Panel > Show/hide hidden files* is **ticked** while the active panel shows them. Every
directory tree follows it (see `navigator-trees`). Ctrl+H decoding: `navkit-terminal`.

## Tagging

- **Insert tags** (`ToggleMark`, DN's `kbIns`): the entry joins `Panel.marked` (names, never `..`), cursor steps down,
  the gutter shows `√` (`+` in ASCII) in *Selected text* `[87]` / *Selected cursor* `[89]`; footer reads `N bytes in M
  selected files`. A re-read keeps tags; a change of directory drops them. **Space tags too while the command line is
  empty** (`ToggleMarkBySpace`, DN's `fmoSpaceToggle`, gated by `Shell`, which owns the line).
- **Gray `+`/`-` are *Select*/*Unselect group*** (`SelectGroup`/`UnselectGroup`, `cmPanelSelect`, on Panel's menu):
  `SelectDialog` asks for a mask -- `;`-separated shell patterns, case folded, `x.*` matching a dotless name as DOS did --
  seeded from `HISTORY["select"]` or `*.*`, *Except mask* ticked by Shift. Selecting passes directories over,
  unselecting does not (`Panel.select_group`).
- **Gray `*` inverts** (`InvertSelection`, `cmPanelInvertSel`, `Panel.invert_marks`): files flip, directories keep their
  tag; Ctrl+Gray `*` (`kbCtrlGAst`) flips directories too.
- **With text on the command line the Gray keys type instead** (a departure): bound in `manager.py` as `by_key=True`
  instances that `Manager.enables` disables while the line has text; the menu's instances are unaffected. **The plain
  `+`, `-`, `*` are bound the same way** (mc's rule), because VTE and PyCharm send Gray `+` as bare `+`.

## Quick search (Ctrl+S)

mc's quick search (`QuickSearch`, `Panel.quick_search`, *Panel > Quick search*): typing moves the cursor to the first
name from it that begins so (case folded, `*`/`?`, `..` never found); a character naming nothing is refused, Backspace
drops one, Ctrl+S again finds the next, wrapping. Shows as ` Search: … ` on the footer with the caret. Enter/Esc end it;
any other key ends it and does its job, as do a click, a directory change and losing the keyboard. While it runs
`edits_text` is True. Matching rules: `navml/quick_search.py`.

## Hiding sides and replacing a side

- **Ctrl+F1/Ctrl+F2 are `cmHideLeft`/`cmHideRight`** (`Manager.toggle_side`, `hidden_side`): a side (`side_view` -- the
  panel or the tree/quick view in its place) is hidden and **the window shrinks** to the other side's rectangle, so the
  console shows through (`SwitchLeft`'s `Locate`). Again restores the old rectangle (zoomed if it was, or grows by the
  share lost). Hiding the only side left shows the console (`cmShowOutput`), and the key from the console brings the
  manager back with that side alone (`cmPostHideLeft`, `Shell.show_manager_side`) -- both keys are on the application's
  table. Tab is disabled while a side is hidden; Ctrl+T/Ctrl+Q show it first.
- **Ctrl+P is `cmSwitchOther`** (`toggle_inactive_side`, on `manager.nml`'s table): the side without the keyboard; it
  never falls back to the console.
- `Manager.switch_view` is DN's `SwitchView`, shared by Ctrl+T (tree) and Ctrl+Q (quick view): `replaced`/`replacement`;
  `tree_replaces` is a computed over them.

## Read when

No DESIGN reference of its own; panel-related library notes are in
`.claude/skills/navml-library/reference/widget-library.md` (*What the library took from `Panel`*).
