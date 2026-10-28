---
name: navigator-user-menu
description: F2's user menu -- menu.ini / .navigator-menu.ini, what was DOS Navigator's dn.mnu (USERMENU.PAS ExecUserMenu): navigator/lib/config/usermenu.py (the ini-shaped parse, the shipped navigator/assets/menu.ini, find_menu local/global, the ! $ macros and %0-%9, quoting, script_text), Shell.user_menu/run_menu_item/edit_menu_file, the Menu Parameters box, F2/F4 inside the box, Options > Global/Local menu definition, navigator/lib/system/tempdir.py (system.temp_dir, the private directory) and nested PopupMenu boxes; also navigator/lib/config/associations.py -- extensions.ini (Enter on a file), viewers.ini/editors.ini (F3/F4, Alt+F3/Alt+F4) and quickrun.ini (Ctrl+Shift+F1..F10), DN's DN.EXT/DN.VWR/DN.EDT/DN.XRN; highlight.ini (DN.HGL) is seeded here too but belongs to navigator-editor. Use when changing the user menu, the .ini associations, or how their commands run.
---

# The user menu (F2)

- **F2** (`UserMenu`, bound in `manager.nml`; also Utilities > User menu) is handled by `Shell.on_user_menu` ->
  `user_menu()`: `find_menu` on a thread -- `.navigator-menu.ini` in the active panel's directory or the nearest above
  it (*local*), else `config_dir()/menu.ini` (*global*, beside `navigator.ini`, not moved by `--config`); neither says
  *File <global path> not found*, and a file that will not parse says *Cannot read ...* with its line. The menu is a
  `PopupMenu` centred on the screen (submenus open beside their entry). In the box **F2 switches local/global, F4
  edits the menu shown**, said on the key bar as DN's status line said it (`hcLUserMenu`/`hcGUserMenu`, `PopupMenu(hints=)`), its
  title *User menu (local)*/*(global)* (a departure, asked for); a caption starting `F1 `..`F12 ` is chosen by that key from any depth and outranks both
  (TV's menu took keys before the status line).
- **Seeded**: `menu.ini` is `associations.MENU` in `associations.TEMPLATES`, its text `navigator/assets/menu.ini` (a
  Linux menu: Files, Archive, Git, Search, System), so `seed_all()` writes it at first start and Options > Global
  menu definition (`MenuFileEdit` -> `edit_associations(MENU)`) re-seeds it if gone. Options > Local menu definition
  (`LocalMenuFileEdit`) opens `.navigator-menu.ini` in the active panel's directory with `open_editor(..., new=True)`.
- **Departure, by request**: DN's `dn.mnu` notation (`>N Caption`, `>>N`) and name are gone; the contents shipped
  are Linux's, not DN's. The format is `.ini`-shaped but parsed line by line in `usermenu.parse` (configparser loses
  separators, repeated captions and order): `Caption = command` with indented continuation lines (a blank line ends
  them), `[A/B]` a submenu path (ancestors made, placed where the header first falls, repeating it adds to it, `[/]`
  the top), `-` a separator, `#`/`;` comments, empty submenus pruned. `Entry` carries its own `commands`.
- **The format and macros** are `navigator/lib/config/usermenu.py`'s docstring: `<Title` / `<=default` and any `%3`..`%9` ask *Menu Parameters*
  (`MenuParamsDialog`, history `menu_params`; Cancel runs nothing), `;` lines and blank lines dropped. `! .! !\ !/ !:` and the `$` forms; `!!`/`$$` literal;
  `%0` script, `%1`/`%2` list files, `%3`..`%9` parameter words, `%%` -- **one regex pass**, so what a macro puts in
  is never re-read. A line of only `<|` (`Commands.panelize`) has `Shell.run_commands` hand the sourced script to
  `Shell._panelize` -> `Manager.panelize` instead of the console: what it prints is the active panel's listing (a
  departure; `navigator-panels`, *Panelize command*). It works in the `.ini` associations too.
- **A `<&` line runs the item in a window of its own** (`Commands.window`, a `WindowMode`; a departure,
  `console-command-line`, *Commands in a window*). The words `zoomed`/`normal` and `modal`/`floating` after it
  override System Setup's *Command windows* (`<& normal modal`). `usermenu.window_mode` parses it before the
  `<Title` case, and **only when every word is one of those four**, so `<& Archive name` stays a title. `<|` wins
  over it. Such an item's script and lists are its own, `usermenu-N.sh`/`active-N.lst`/`passive-N.lst` (lowest free
  N), since the window may still be reading them when the next item writes the console's; they are removed when
  the window closes. The window is titled with the expanded lines joined by `; `, not the `. script` it runs. The
  shipped menu's *System > Top in a window* is the example; the `.ini` associations get `<&` for nothing.
  **A command line starting `&` does what a bare `<&` does** (the `&` taken off in `commands_of`, so it never
  reaches the shell, which would refuse it), as `&` does on the command line: `Run = &./!.!`. A `<&` line's words
  still say how the window opens. `!.!` is a bare name, which the shell looks up on `$PATH`; running the file at
  the cursor wants `./!.!`.
- **Departures**: in what runs, every value is `shlex.quote`d where it needs it (so a macro wants no quotes round it);
  names keep their case; the lines are written to `usermenu.sh` and **sourced** (`. script`) in the console's shell
  through `Shell.run_command(..., typed=False)` (no history, the line kept), so they are that shell's language and a
  `cd` stays -- and `$` reaches the shell only as `$$`, as in DN.
- **The files**: `active.lst`/`passive.lst` (tagged names, or the one at the cursor; `-` for a passive side not
  showing, DN's `GetUserParams`) and `usermenu.sh` under fixed names in `tempdir.private_dir()` --
  `<temp_root>/navigator-<uid>`, 0700, refused if not this user's alone. `temp_root()` is *System > Temporary
  directory* (`system.temp_dir`), else `$TMPDIR`; the subshell's rc directory goes there too.

## extensions.ini, viewers.ini, editors.ini, quickrun.ini

`navigator/lib/config/associations.py` (its docstring has the format): DN's `DN.EXT`, `DN.VWR`, `DN.EDT` and `DN.XRN` as **`.ini`
files of Navigator's own design, beside `navigator.ini`** -- a departure the user asked for, DN's formats not kept. A
section is a mask (`;`-separated patterns, case aside, first match wins) or a key (`[F1]`..`[F10]`); each key in it
is a caption, its value the commands (indented continuation lines), read by **`usermenu.commands_of`** so `<Title`,
`<=default`, `%3`..`%9` and every macro work. The parser keeps captions' case, splits on `=` only and has no inline
comments (`;`/`#` are the shell's). One entry runs at once; **several are offered in a centred `PopupMenu`** -- what
DN's Alt+Enter `[ ]` menu became, since Alt+Enter stays *Insert name*; DN's Shift+Enter `( )` variant has no key.

- **Enter** on a non-executable file: `Panel.choose` emits `OpenFile` (beside `ExecuteFile`) -> `Shell.on_open_file`
  -> `run_associated(EXTENSIONS, name)`; no entry, the desktop's application (`gio open` or `kioclient exec`, *Pass other files to
  desktop*, a departure) where `desktop.program()` and a display are, else nothing happens (`navigator-gio` skill). Not in a *Find:* listing (Enter goes to the file).
- **F3/F4 and Alt+F3/Alt+F4** (`AlternateView`/`AlternateEdit`, File > Alternate view/edit, DN's `cmIntFileView`/
  `cmIntFileEdit`): `Manager.view_file(intern)`/`edit_file(intern)` are DN's `ViewFile(Intern)`. The key agreeing with
  *Internal viewer/editor* opens the window; the other tries `viewers.ini`/`editors.ini`, falling back to
  `$PAGER`/`$EDITOR` for F3/F4 and to the window for Alt+F3/Alt+F4.
- **Ctrl+Shift+F1..F10** (`QuickRun(number)`, on `Navigator.keys` -- DN's code read Shift, its help said Alt):
  `quickrun.ini`'s section; none, nothing.
- **Options > Quick run file edit / Extension file edit / Viewers / Editors** (`EditQuickRun`, `ExtFileEdit`,
  `ExternalViewers`, `ExternalEditors`): `Shell.edit_associations` calls `associations.seed` first if the
  file is missing (exclusive create, on a thread), then edits it. `main()` already seeds all four after
  `load_settings` (`associations.seed_all`, complaints to stderr), so the templates' examples are live from the first
  start, as DN's files shipped filled in; only `main()` does, so an application a test builds never writes them. Global only: DN's local copies (Shift on the menu
  item, the current directory's file) are not read.
- All run through **`Shell.run_commands(commands)`**, the user menu's runner (`run_menu_item` calls it). `_menu_side`
  takes a *Find:* entry's own directory. A file that is not an `.ini` says *Cannot read ...* in an Error box.

