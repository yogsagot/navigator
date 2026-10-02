## Menus

`navml/widgets/menu/` is Turbo Vision's `TMenuBar` and `TMenuBox`, and **every measurement is `MENUS.PAS`'s**, read
from DOS Navigator 1.51's source rather than remembered:

- The bar paints its entries from column 1, each caption with a space on either side, and the selected entry in
  the *Selected* slot across all three cells.
- A box is framed one column in, with the line shapes `' ┌─┐ '`, `' │ │ '`, `' ├─┤ '` and `' └─┘ '`.
- An entry's colour fills the row from frame to frame. The caption starts at column 3, and the key is right-aligned
  three columns in from the far edge; a submenu shows `►` in that place.
- A box's width is its widest caption plus 6, plus the key and two spaces or plus 3 for a submenu, and never less
  than 10.
- A box drops one column to the left of its caption on the bar. A nested box opens two columns in from its parent
  and one row below the entry that opened it.
- The shadow is Turbo Vision's constant `ShadowAttr`, dark grey on black, which is a constant rather than a
  palette slot. It covers two columns down the right side and one row along the bottom.

The six colours are the Colors dialog's *Menus* group, slots [2] to [7], shared with the status line exactly as the
original shares them.

**Navigator's menu is DOS Navigator 1.51's own.** `navigator/widgets/shell/main_menu/main_menu.nml` transcribes
`dlgMainMenu` from `DN.DNR`: `≡ File Disk Utilities Panel Manager Options Window`, with all 140 entries in the
original's order. It replaced a `Left Files Commands Options Right` bar with F9 PullDn and F10 Quit, which is
Norton Commander's and not DOS Navigator's. In the original, F10 is `cmMenu` and Exit is Alt+X, and the key bar
reads the file panel's status line, `StatusDef hcFilePanel`: `F1 Help F2 User F3 View F4 Edit F5 Copy F6 Ren
F7 MkDir F8 Del F10 Menu`. Ctrl+Q stopped quitting, because it is the original's Quick view.

### The tree is markup, and its entries are widgets that are never shown

A menu is written as blocks, `SubMenu:`, `MenuItem:` and `MenuLine:`, and a block is a widget, so the entries are
widgets. They are *data*: invisible from the constructor on, with no rectangle, and painted as rows by the bar and
the boxes it opens. The rule recorded for listings is that rows are painted rather than being widgets, and it is kept
where it matters. No row is a live widget taking part in painting, hit-testing or focus, and a menu is a few static
entries rather than a recycled pool. What the markup form buys is the component story unchanged: a menu is a
document, `--check` covers it, and giving a feature its entry is one `command:` line.

- **An entry with no `command` is disabled**, which is the same rule as a command nobody handles. The transcription
  names a command only where the feature exists: MkDir, Exit, Re-read, Output window, the window commands, and View,
  Edit, Copy, Rename/Move, Delete and User menu, which have classes but no handlers yet. Everything else is greyed.
- **An entry's key is read off the key tables**, through `navkit.commands.key_for`. `key:` holds the original's
  caption and is shown only while nothing binds the command. So Make directory shows `F7` because F7 asks for it,
  and Window › Next shows `F9` where the original's menu said `Alt-Tab`, because F9 is what asks for it here.

### An open menu is a modal layer

Turbo Vision ran a menu in a nested event loop. navkit has one loop, so `MenuBar.open()` overlays a `MenuSession`
over the whole screen. The session is modal, paints the boxes over their shadows, and answers every key and click
by `TMenuView.Execute`'s rules:

- F10 highlights the bar without dropping a box; Alt+letter and a click drop one.
- Left and Right move along the bar, or out of and into a nested box.
- Up and Down skip lines and wrap round.
- Enter or a marked letter chooses an entry.
- Esc closes the top box, and from the first box closes the whole menu.
- A release over an entry chooses it, and a press outside everything closes the menu.

- **Choosing closes the menu first and asks for the command second.** Removing the modal gives the keyboard back,
  so the command starts from exactly the widget its key would have started from.
- **Enabled is judged from behind the menu.** While the session is up it *is* the focus, so the questions *could
  MkDir run?* and *which key asks for it?* are asked from the widget that had the keyboard before. That is why
  `navkit.commands`' queries take a `start` widget.
- **A box's shadow is painted just before that box**, not all shadows before all boxes, so a nested box shades its
  parent as the original's did.
- **F10 is handled by `Shell`**, the ancestor both the focus and the bar share, since the bar is nowhere near the
  focus. Alt+letter reaches `Shell.on_key` only after everything nearer the keyboard has declined it, so a dialog's
  shortcut walk and the console's child both come first. The letters are read off the captions, so they cannot be a
  key table.

### Every menu has an id, and Python can change it

Every `SubMenu` in `main_menu.nml` carries an `id`. An id is an attribute of the document's class, so a plugin
reaches a menu the same way the hand-written half reaches a child: `app.shell.menu.file`. The generated stub types
it, so `menu.file.` completes. A nested submenu's id joins its parent's to its own, as in `file_view` or
`options_configuration`, because an id is unique across the whole document.

`MenuBar` and `SubMenu` share `MenuContainer` (`navml/widgets/menu/sub_menu/sub_menu.py`), which is what a program
changes a menu through:

```python
menu.file.add_item("~Z~ip...", ZipFiles, key="Alt-Z", after=MakeDirectory)
plugins = menu.add_submenu("~P~lugins", before="Window")
menu.options.add_line(before="Colors...")
menu.file.remove_entry("Print");  menu.file.move_entry("Delete", after="Copy...")
menu.item_for(MakeDirectory).disabled = True
```

- **An anchor** is what `before=`, `after=`, `entry()`, `remove_entry()` and `move_entry()` take. It is an entry,
  its caption (tildes and case ignored), or a command class or instance, which names the item asking for it. An
  anchor that names nothing raises `LookupError` listing what the menu does hold. A plugin placing its entry beside
  one that has since moved should hear about it rather than land at the end.
- **`hidden` and `disabled` are reactive flags on every entry.** `hidden` leaves an entry out of its menu: not
  shown, not counted, not reachable by its letter. `disabled` is `Widget`'s own and greys an entry whatever its
  command says, on the bar as well as in a box. Toggling either repaints an open menu. `visible` is not the way to
  hide one, since every node is invisible already.
- **Adding, removing and reordering are not reactive**, because a widget's children never are. They take effect
  the next time a box opens, and an open box keeps the size it was measured at. A plugin changes menus when it is
  loaded, not while one is open, so this costs nothing yet.
- **`item_for(command)` searches every submenu**, which is how a plugin finds an entry it did not put there.

### A window's own menu joins the bar while it is in use

A window can declare menus of its own as `SubMenu` children in its document. Navigator's viewer does this in
`file_window.nml`. While that window is the one in use, its menus appear on the main bar beside the bar's own entries.
DOS Navigator had nothing like it for its viewer. Its editor did something nearby: `TEditWindow.Init` put a whole
`dlgEditorMenu` bar *inside* its window, on the row under the frame. Merging into the one bar keeps the screen's
single menu row and keeps F10 meaning one thing.

- **`MenuBar.context` is a widget, and its `SubMenu` children are the contributed menus.** The bar's owner binds it.
  `shell.nml` has `context: None if parent.console_visible else desktop.active_window`, so F9, a click, a close and
  Ctrl+O all take a window's menu off the bar by changing one of those two inputs, and no command has to remember
  to. `context` is reactive, so the bar repaints when it changes.
- **Each contributed submenu places itself**, with `before:` or `after:` naming a caption on the bar
  (`after: 'File'`), or at the end with neither. There is no fixed slot. An anchor that names nothing raises, as an
  `add_*` anchor does.
- **Only `entries()` carries the contributed menus.** `all_entries()`, `entry()` and every `add_*`/`remove_*` call
  stay the bar's own, so a plugin can neither anchor on a window's menu nor remove it by accident. Painting,
  Alt+letter, the mouse and a `MenuSession` all read `entries()` already, so they needed nothing.
- **A `SubMenu` as a window's child is safe** because a `MenuNode` is invisible and lays out nowhere. Painting,
  hit-testing and focus all skip it.
- **The commands route as every menu command does**, from the focus the menu was opened over. That is inside the
  window, so the window's own key table names the keys and its `enables`/`checks` grey and tick the entries.
  `SetViewMode(mode)` and `SetViewFilter(filter)` exist so the modes and filters F4/F6 cycle can each be one ticked
  entry.
- **Panel is the file manager's own menu.** Every entry in it acts on a file manager's panels, and from a viewer or
  an editor every one was greyed. So the block moved from `main_menu.nml` to `manager.nml` with `after:
  'Utilities'`, which is where DN had it. Each file manager carries its own copy, and `context` shows the active
  one's. A plugin reaches it as `manager.panel_menu`. *Manager* stays on the main bar because *New* (Ctrl+F3) has to
  be reachable with no file manager open. Its *Directory tree*, *Info* and *Quick view* moved to Panel, a departure
  from `dlgMainMenu`: each puts something in the passive panel's place, which is a panel's business. They have new
  letters (y, n, k) because d, i and q were taken in that box.
- **The editor's menu is one entry with DN's bar nested in it.** `dlgEditorMenu` is seven menus (File, Edit,
  Search, Paragraph, Block, Misc, Options), and DN gave it a row of its own inside the window. Beside the main
  bar's eight they would not fit in 80 columns, and *File*, *Options* and the letters F, P, M and O are the main
  bar's already. So `edit_window.nml` has one *Editor* entry after *File*, and the seven are submenus in it, each
  with the original's entries, captions and keys. *Main menu* (F10) is left out, because the menu it would open is
  the one it sits in. An entry names a command once the editor can do it and is greyed until then. DN showed each
  option's `Off`/`On` in the key column, and a tick will say that here once the option exists.

What is not here yet: the status line has nothing to show while a menu is open, where the original showed the
menu's help-context hints. The menu's own key shortcuts are not bound either: `TMenuBar` answered every item's key
itself, whereas here a key is a key table's, and the menu only reads it.

