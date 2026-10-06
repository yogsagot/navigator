---
name: navigator-user-menu
description: F2's user menu -- DOS Navigator's dn.mnu (USERMENU.PAS ExecUserMenu): navigator/usermenu.py (parse, find_menu local/global, the ! $ macros and %0-%9, quoting, script_text), Shell.user_menu/run_menu_item/edit_menu_file, the Menu Parameters box, F2/F4 inside the box, Options > Global/Local menu definition, navigator/tempdir.py (system.temp_dir, the private directory) and nested PopupMenu boxes. Use when changing the user menu or how its items run.
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
