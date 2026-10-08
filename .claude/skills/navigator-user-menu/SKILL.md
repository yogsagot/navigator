---
name: navigator-user-menu
description: F2's user menu -- DOS Navigator's dn.mnu (USERMENU.PAS ExecUserMenu): navigator/usermenu.py (parse, find_menu local/global, the ! $ macros and %0-%9, quoting, script_text), Shell.user_menu/run_menu_item/edit_menu_file, the Menu Parameters box, F2/F4 inside the box, Options > Global/Local menu definition, navigator/tempdir.py (system.temp_dir, the private directory) and nested PopupMenu boxes; also navigator/associations.py -- extensions.ini (Enter on a file), viewers.ini/editors.ini (F3/F4, Alt+F3/Alt+F4) and quickrun.ini (Ctrl+Shift+F1..F10), DN's DN.EXT/DN.VWR/DN.EDT/DN.XRN. Use when changing the user menu, the .ini associations, or how their commands run.
---

# The user menu (F2)

- **F2** (`UserMenu`, bound in `manager.nml`; also Utilities > User menu) is handled by `Shell.on_user_menu` ->
  `user_menu()`: `find_menu` on a thread -- `dn.mnu` in the active panel's directory or the nearest above it (*local*),
  else `config_dir()/dn.mnu` (*global*, beside `navigator.ini`, not moved by `--config`); neither says DN's
  *File dn.mnu not found*. The menu is a `PopupMenu` centred on the screen, nested by `>N` (submenus open beside their
  entry). In the box **F2 switches local/global, F4 edits the menu shown**; a caption starting `F1 `..`F12 ` is chosen
  by that key from any depth and outranks both (TV's menu took keys before the status line).
- **Options > Global menu definition / Local menu definition** (`MenuFileEdit`, `LocalMenuFileEdit`) open the global
  file, or `dn.mnu` in the active panel's directory, with `open_editor(..., new=True)`.
- **The format and macros** are `navigator/usermenu.py`'s docstring: `>N Caption`, `>>N` read as `>N`, a bare `>N` a
  line, `<Title` / `<=default` and any `%3`..`%9` ask *Menu Parameters* (`MenuParamsDialog`, history `menu_params`;
  Cancel runs nothing), `;` lines and blank lines dropped. `! .! !\ !/ !:` and the `$` forms; `!!`/`$$` literal;
  `%0` script, `%1`/`%2` list files, `%3`..`%9` parameter words, `%%` -- **one regex pass**, so what a macro puts in
  is never re-read.
- **Departures**: in what runs, every value is `shlex.quote`d where it needs it (so a macro wants no quotes round it);
  names keep their case; the lines are written to `usermenu.sh` and **sourced** (`. script`) in the console's shell
  through `Shell.run_command(..., typed=False)` (no history, the line kept), so they are that shell's language and a
  `cd` stays -- and `$` reaches the shell only as `$$`, as in DN.
- **The files**: `active.lst`/`passive.lst` (tagged names, or the one at the cursor; `-` for a passive side not
  showing, DN's `GetUserParams`) and `usermenu.sh` under fixed names in `tempdir.private_dir()` --
  `<temp_root>/navigator-<uid>`, 0700, refused if not this user's alone. `temp_root()` is *System > Temporary
  directory* (`system.temp_dir`), else `$TMPDIR`; the subshell's rc directory goes there too.

## extensions.ini, viewers.ini, editors.ini, quickrun.ini

`navigator/associations.py` (its docstring has the format): DN's `DN.EXT`, `DN.VWR`, `DN.EDT` and `DN.XRN` as **`.ini`
files of Navigator's own design, beside `navigator.ini`** -- a departure the user asked for, DN's formats not kept. A
section is a mask (`;`-separated patterns, case aside, first match wins) or a key (`[F1]`..`[F10]`); each key in it
is a caption, its value the commands (indented continuation lines), read by **`usermenu.commands_of`** so `<Title`,
`<=default`, `%3`..`%9` and every macro work. The parser keeps captions' case, splits on `=` only and has no inline
comments (`;`/`#` are the shell's). One entry runs at once; **several are offered in a centred `PopupMenu`** -- what
DN's Alt+Enter `[ ]` menu became, since Alt+Enter stays *Insert name*; DN's Shift+Enter `( )` variant has no key.

- **Enter** on a non-executable file: `Panel.choose` emits `OpenFile` (beside `ExecuteFile`) -> `Shell.on_open_file`
  -> `run_associated(EXTENSIONS, name)`; no entry, nothing happens. Not in a *Find:* listing (Enter goes to the file).
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

