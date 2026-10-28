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
- **Size/Move (Ctrl+F5) is `Window.begin_move`**, TV's `dmDragMove`: the window takes the keyboard, arrows move,
  Shift+arrows size, Enter keeps, Esc puts it back, every other key swallowed (`Window.on_key`, no key table). **While
  it lasts the key bar names those keys** (`Window.key_hints`; a departure, asked for: TV said nothing). A subclass's
  `render_after` must call `super()` (`Manager`'s does).
- **Closing asks** through `Window.must_ask`/`ask_to_close` (`Valid(cmClose)`), which `request_close`, Close all and
  Alt+X all go through.
- **Window > List (Alt+0) is DN's *Windows Manager*** (`cmWindowManager`, `dlgWindowManager`;
  `navml/widgets/window_manager/` and `window_list/`): windows top first, named by `Window.list_name()` (`cmGetName`; a
  file manager is its active panel's directory); OK switches, Close closes while the dialog stays up.
- **Tile, Cascade, Close all** are DN's `TDesktop.Tile`/`Cascade` and `cmClearDesktop` from `DNAPP.PAS`; every window is
  arranged unless it says `tileable: False` (on by default, where DN's `ofTileable` was opt-in).
- `Desktop.keys` holds the window keys; `navml/commands.py` holds the window command set `Desktop` runs.
- **Every window has a `number`** (TV's `TWindow.Number`): `Desktop.open()` gives the lowest of 1..9 free, kept while
  raised, 0 for a tenth and again once closed. A close renumbers the rest 1..n in order (`Desktop._renumber`, a
  departure: TV left the gap, which the window strip made read as a fault), a tenth taking the freed 9. **Win+1..9 is `SelectWindow(number)`** (TV's `cmSelectWindowNum`, whose
  Alt+digits DN commented out for its quick directories) and Win+0 the list, which prefixes each row with its number.
  Only a kitty-protocol terminal sends Super (Ghostty does; xfce4-terminal and other VTE ones never do), and desktops
  (GNOME, KDE) grab Super+digit for their dock by default -- so **Alt+Shift+F1..F9** are bound too, which every
  terminal sends, and **a digit in the Window list** (`WindowList.on_key`) chooses that window outright: Alt+0, 2.
- **`Desktop.open_windows`** is the reactive tuple of windows (the children list is not), replaced on open and close,
  not on raise -- what anything showing all the windows reads.
- **`WindowStrip`** (`navml/widgets/window_strip/`, Python alone) paints a desktop's numbered windows as chips, the top
  one `::chip:selected` (the number is `::number`), and a click activates (the wheel anywhere over it steps to the next/previous number, wrapping); `labels` adds `Window.short_name()`
  (`list_name()` unless a window says it shorter -- Manager its directory's last part, viewer/editor the file name),
  cut evenly when short of room, then the rest counted as `+k`; `align: "right"` keeps them to the far end. Nothing
  under two windows. Navigator's `Shell` floats it on the menu bar between the last menu and the clock, right-aligned
  against the clock, under Interface's *Window strip* (`interface.window_strip`: `off`/`numbers` (default)/`full`), hidden with *Hide menu bar* and under Ctrl+O. Not DN's: OSP put the number in `[■]`.
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
  entry. `path_to(command)` is the shown entries down to the item asking for it (the bar's spliced-in window menus
  included, hidden ones never; the exact instance first, then its class) -- what the key bar's tooltips read.
- **A bar caption's tooltip** is its entry's `tooltip` (markup `tooltip:`, translated) plus its `Alt-<letter>`
  (`MenuBar.tooltip_at`); a window menu joining the bar brings its own. Give a new top-level menu one.
- **A menu box row's tooltip** is its entry's `tooltip` (`MenuBox.tooltip_at`), shown over the open menu. Write one
  only where the caption does not explain itself (*Panelize command*, *Optimal fill*); most items have none.
- **A submenu can show a key**: `SubMenu.key_command` names a command that opens its entries some other way, and
  `MenuBox` paints that command's live key (`key_caption`, else `SubMenu.key`) just before the `►` -- a departure,
  TV's submenus had none. Display only; choosing the entry still opens the submenu.
- **A menu tick** is navkit's `Widget.checks(command)` (True/False/None), asked of the same widget `enables` is
  (`Application.command_checked`); `MenuBox` paints `√` (`+` in ASCII) in the blank column left of the caption, so a
  tick costs no width. A `MenuItem` with `ticked` set is ticked whatever its command says -- for a popup's choices,
  which have no command to ask (Alt+B's current order).
- **A window's own menu joins the bar while it is in use**: `SubMenu` children of a window join through
  `MenuBar.context`, which `shell.nml` binds to the desktop's active window, each placing itself with `before:`/`after:`.
  The viewer's *View* and the editor's *Editor* menus go after *File*.
- **Panel is the file manager's own menu** (`manager.nml`, `manager.panel_menu`, after *Utilities* only while a file
  manager is active); *Directory tree*, *Info* and *Quick view* moved into it from *Manager* -- a departure; *Manager*
  stays global for *New*.
- **A popup menu** is `PopupMenu` (`TMenuPopup`): one `MenuBox` anywhere, run like a dialog -- spawn
  `execute(app)`, which answers the `MenuItem` chosen or None; a command-less item is a choice, not greyed. `keys=`
  adds keys that close it on the selected entry (enabled or not), setting `pressed` and `selected`, for a caller that
  acts and reopens -- in a nested box the entry is that box's; `submenu=(index, current)` reopens with the first
  box's entry *index* dropped and *current* selected in it; a `SubMenu`'s own `footer` goes in the frame of the
  nested box it opens (a bar's boxes ignore it). `title=`/`footer=` go centred in the first box's top/bottom frame, widening it (`measure`
  takes both). The bookmarks box is its first user (`navigator-bookmarks`). A `SubMenu` entry opens a nested
  box beside it (Enter/Right/click; Esc/Left closes the top one), `MenuSession`'s way; `box` stays the first box,
  `boxes` is the stack, and the answer is the item chosen at any depth (`navigator-user-menu`).
- **A context menu** (right click, Menu key, Shift+F10; a departure, since DN had none) is a `ContextMenu` from a
  `ContextMenuHost`'s `context_menu()`, run in a `PopupMenu` at the pointer. Its choice runs with `start=host`. A
  right press is delivered first, then offered again as navkit's `ContextMenuEvent`, so a widget that uses the right
  button keeps it. A component (`InputLine`) cannot take the mixin and writes the handlers out. A `ContextMenu` never
  joins the bar. See `reference/menus.md`, *A widget's context menu opens where the user points*.
- **A `MenuBox` opened shorter than `measure()` scrolls** (a departure; TV boxes never outgrew the screen): `top` is
  the first entry shown, a plain attribute `scroll()` derives from `current` while painting and in `entry_at` -- never
  assign it. `▲`/`▼` on the frame mark hidden entries. `move(n)`/`page(n)` move without wrapping, unlike `step`.
  Only `PopupMenu` opens one short (cut to the screen, PgUp/PgDn, wheel); the bar's boxes keep their measured height.

## Read when

| Reference | Read when |
|---|---|
| `reference/windows-desktop-modal.md` | window/desktop/modal design, tile/cascade, window list |
| `reference/menus.md` | menu geometry, the modal layer, ids and the Python API, context menus |
