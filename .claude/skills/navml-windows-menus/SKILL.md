---
name: navml-windows-menus
description: Overlapping windows and menus -- navml's Window, Desktop, Modal stacking, raising, dragging/resizing/zooming, shadows, Window > List (Windows Manager), Tile/Cascade/Close all, `must_ask`/`ask_to_close`, and MenuBar/MenuBox/SubMenu/MenuItem/MenuLine, the MenuContainer API, menu ticks, and a window's own menu joining the bar (`MenuBar.context`). Use when touching the desktop, a window, or Navigator's main menu.
---

# Windows, the desktop and menus

## The desktop

The root is `navigator/widgets/shell/shell/` -- menu bar, `Console`, navml's `Desktop` over it, key bar -- and
`Manager` is a frameless `Window` on that desktop, opened zoomed, which the user can drag, resize from its corner, zoom
with `[↕]`/`[↑]`, close with `[■]`, and bring forward by clicking. **The console is the background and is always
showing**; Ctrl+O hides the desktop (one `visible` binding). `Modal` is the old framed window (fixed, centred, bound
geometry, `modal = True`); `Dialog` derives from it.

Four rules from building it:
- **A window's rectangle is state, never bound** -- drag, resize and zoom assign it.
- **Raising is `Widget.raise_child`, a reorder** -- `add()` would unmount.
- **A shadow is `Widget.shadow`**, painted by `render_tree` into the parent's surface before the widget, after a
  modal's dim (on for `Window`, `Modal`, `MenuBox`, `HistoryList`).
- **The application's own `on_key`/`on_mouse_click` must step aside while `app.modal` is set**, because they run before
  navkit's modal routing (the application's *key table* does this by itself).

navkit grew `raise_child`/`lower_child`, `Application.capture_mouse` and `Widget.render_after` for it (see
`navkit-widgets-input`).

- Closing the last window (`Desktop` raises `EmptiedEvent`) leaves the console showing and focused; opening any window
  (`OpenedEvent`) hides the console again -- no command that opens one checks `console_visible` itself.
- **Closing asks** through `Window.must_ask`/`ask_to_close` (`Valid(cmClose)`), which `request_close`, Close all and
  Alt+X all go through.
- **Window > List (Alt+0) is DN's *Windows Manager*** (`cmWindowManager`, `dlgWindowManager`;
  `navml/widgets/window_manager/` and `window_list/`): windows top first, named by `Window.list_name()` (`cmGetName`; a
  file manager is its active panel's directory); OK switches, Close closes while the dialog stays up.
- **Tile, Cascade, Close all** are DN's `TDesktop.Tile`/`Cascade` and `cmClearDesktop` from `DNAPP.PAS`; every window is
  arranged unless it says `tileable: False` (on by default, where DN's `ofTileable` was opt-in).
- `Desktop.keys` holds the window keys; `navml/commands.py` holds the window command set `Desktop` runs.
- With several file managers open, **`Shell.active_manager`** (nearest the top) is "the file manager";
  `shell.manager`/`app.manager` stay the first one. Manager > New (Ctrl+F3, `cmCreatePanel`) opens another zoomed
  `Manager` on the active panel's directory; Ctrl+F3 is on the application's table so it works with none open.

## Menus

`navml/widgets/menu/` (slots `[2-7]`): `MenuBar`, `MenuBox`, and `SubMenu`/`MenuItem`/`MenuLine` blocks -- invisible
data widgets; the tree is markup. An open menu is a modal layer. Navigator's menu is DN 1.51's `dlgMainMenu`,
transcribed into `navigator/widgets/shell/main_menu/main_menu.nml`, with every entry whose feature does not exist
greyed. F10 opens it (`OpenMenu`, `navml/widgets/menu/commands.py`).

- **Every submenu has an id** (`app.shell.menu.file`, `menu.file_view`). `MenuBar`/`SubMenu` share `MenuContainer`'s
  Python API for plugins: `add_item`/`add_submenu`/`add_line` with `before=`/`after=` anchors (an entry, a caption, or
  a command), `remove_entry`, `move_entry`, `entry`, `item_for(command)`, plus reactive `hidden`/`disabled` on every
  entry.
- **A menu tick** is navkit's `Widget.checks(command)` (True/False/None), asked of the same widget `enables` is
  (`Application.command_checked`); `MenuBox` paints `√` (`+` in ASCII) in the blank column left of the caption, so a
  tick costs no width.
- **A window's own menu joins the bar while it is in use**: `SubMenu` children of a window join through
  `MenuBar.context`, which `shell.nml` binds to the desktop's active window, each placing itself with `before:`/`after:`.
  The viewer's *View* and the editor's *Editor* menus go after *File*.
- **Panel is the file manager's own menu** (`manager.nml`, `manager.panel_menu`, after *Utilities* only while a file
  manager is active); *Directory tree*, *Info* and *Quick view* moved into it from *Manager* -- a departure; *Manager*
  stays global for *New*.
- **A popup menu** is `PopupMenu` (`TMenuPopup`): one `MenuBox` anywhere, run like a dialog -- spawn
  `execute(app)`, which answers the `MenuItem` chosen or None; a command-less item is a choice, not greyed. `keys=`
  adds keys that close it on the selected entry (enabled or not), setting `pressed` and `selected`, for a caller that
  acts and reopens. The bookmarks box is its first user (`navigator-bookmarks`). A `SubMenu` entry opens a nested
  box beside it (Enter/Right/click; Esc/Left closes the top one), `MenuSession`'s way; `box` stays the first box,
  `boxes` is the stack, and the answer is the item chosen at any depth (`navigator-user-menu`).
- **A `MenuBox` opened shorter than `measure()` scrolls** (a departure; TV boxes never outgrew the screen): `top` is
  the first entry shown, a plain attribute `scroll()` derives from `current` while painting and in `entry_at` -- never
  assign it. `▲`/`▼` on the frame mark hidden entries. `move(n)`/`page(n)` move without wrapping, unlike `step`.
  Only `PopupMenu` opens one short (cut to the screen, PgUp/PgDn, wheel); the bar's boxes keep their measured height.

## Read when

| Reference | Read when |
|---|---|
| `reference/windows-desktop-modal.md` | window/desktop/modal design, tile/cascade, window list |
| `reference/menus.md` | menu geometry, the modal layer, ids and the Python API, context menus |
