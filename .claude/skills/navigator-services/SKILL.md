---
name: navigator-services
description: Utilities > Services, a departure from DN (DOS had no service manager) -- navigator/lib/system/services/ (the Backend interface in common.py with Unit, run/failure, Journal/LogFile/EditPlan, Follower; __init__.py's BACKENDS, current() and [services] manager, the dispatchers gather/act/details/log/edit_plan/after_edit, ordered/matches; systemd.py merging systemctl list-units and list-unit-files, drop-in overrides, daemon-reload, journalctl; openrc.py with rc-status --servicelist, rc-update show --verbose, rc-service, the own or filtered system log, /etc/conf.d), the root helper's service/after_edit/journal_follow/journal_stop ops, ServiceList (a ColumnList), ServiceWindow (greying what a backend has not, F3/F4/F5-F8, Ctrl+E/Ctrl+D, As root), F3's JournalWindow and log-file viewer, and [services] manager/refresh/journal_lines. Use when changing the Services window, adding a service manager, or changing what one runs.
---

# Services

**Not DOS Navigator's.** DOS had no service manager, so the whole window is a departure, asked for. It is recorded in
the docstring of `navigator/lib/system/services/__init__.py`, the `#:` comment above Utilities > *Services* in
`main_menu.nml`, and the window's markup. It is Process list's sibling and is built the same way
(`navigator-processes`).

## The interface (`navigator/lib/system/services/`)

- **One `Backend` per service manager** (`common.py`): `name`, `title`, a closed `verbs` tuple, capability flags
  (`user_scope`, `all_types`, `reload_after_edit`, `restart_after_edit`) and the methods `refusal`, `valid_name`,
  `installed`, `gather`, `act`, `details`, `log` (a `Journal(argv, readable)` or `LogFile(path, pattern)`),
  `edit_plan` (an `EditPlan(path, seed, line)`) and `after_edit`. Each module (`systemd.py`, `openrc.py`) keeps its
  work in module functions and a thin class over them, so **tests patch the module function** (`systemd.unit_file`,
  `openrc.INIT_D`) and the class picks it up.
- **Every command goes through `common.run(argv)`** (`LANG=C`, `EINFO_COLOR=NO`, a timeout, no stdin) -- one patch
  point for every backend. `common.failure()` reads a refusal (polkit's *Access denied*, OpenRC's *superuser access
  required*, *Permission denied*...) as `OSError(EPERM)`, which `elevate.refused()` takes for *As root*; anything else
  is `EIO` with what was said.
- `Unit` has `backend` (the name of the one that read it) and `startup` (systemd's file state, or OpenRC's runlevels
  joined, `disabled` for none). `running`/`failed` cover both managers' words.
- `__init__.py`: `BACKENDS`, `current()` (`[services] manager` names one, else the first whose `refusal()` is empty:
  systemd, then OpenRC), `refusal_reason()` for the menu's grey, and the dispatchers the window calls --
  `gather` (on `current()`, dropping `user`/`all_types` it cannot do), and `act`/`details`/`log`/`edit_plan`/
  `after_edit` on `backend_of(unit)`. **The window calls only these**, so a window test patches `services.gather`,
  `services.act`.
- **Adding a manager**: a module with a `Backend` subclass and `BACKEND`, an entry in `BACKENDS`, its name in
  `ServicesData.MANAGERS` (settings.py writes the tuple out: it is read before the backends can be imported), and
  its verbs' refusal words in `common.REFUSALS` if new.

## systemd (`systemd.py`)

- `gather(user, all_types)` merges `list-units --all` (load, active, sub, description) with `list-unit-files` (the
  file's state). A unit installed but never loaded is only in the second and is shown `inactive/dead`. An instance
  takes its template's state; **a template (`getty@.service`) is left out**. `--output=json` first, the plain
  columns when it is refused (systemd < 246).
- `VERBS` (8, mask/unmask included) and `valid_unit()` (systemd's characters, never a leading `-`, a dot required).
  `act()` runs `systemctl [--user] --no-ask-password VERB -- NAME`: **`--no-ask-password` keeps polkit off the
  terminal Navigator draws on**.
- `details()` is `systemctl status --lines=0 --full` (exit 3 for a stopped unit is no failure).
- F3: `Journal(journal_argv(...), can_read_journal(unit))` -- a user unit, root, or a member of
  `systemd-journal`/`adm`/`wheel` reads it all.
- F4 (`edit_plan`): **a masked unit is refused** by `unit_file()` (systemd may still report the package's file as its
  `FragmentPath`). `edit_target()` opens the fragment itself when it is the administrator's own (under `admin_dir()`,
  **compared after `realpath`**, so a link in `/etc` to a package's file is still the package's), else the drop-in
  `<admin_dir>/<unit>.d/override.conf`, seeded by `override_text()` with the package's file commented out.
  `after_edit` is `daemon-reload`.

## OpenRC (`openrc.py`)

- `gather()` runs two commands, never one per service: `rc-status --servicelist` (name and the first word in the
  brackets -- newer OpenRC prints an uptime after it) and `rc-update show --verbose` (`name | runlevels`, empty for
  none). The description is the script's `description=` line, read from the first 64 KiB of `/etc/init.d/<name>`.
- `VERBS`: start/stop/restart/reload through `rc-service NAME VERB`; enable is `rc-update add NAME default`;
  **disable reads `rc-update show` again and deletes it from every runlevel** (boot too) -- again, because the root
  helper gets only the name. No mask, no user services, no other kinds: the window greys them.
- `valid_service()`: a script's file name, never a leading `-`, never a `/`. **`installed()`** (a script by that name
  in `/etc/init.d`) is what the root helper checks beyond it.
- F3 (`log`): the service's own `output_log=`/`error_log=` (a plain path, no variable, in `/etc/conf.d/<name>` first,
  then the script) when the file is there; else the first of `SYSTEM_LOGS` with `pattern` = its name -- the viewer
  shows only the lines holding it, approximate, and the title says so; else `ENOENT`.
- F4 (`edit_plan`): `/etc/conf.d/<name>`, seeded when new by `conf_text()` with the script's `NAME=` lines commented
  out (not `depend()` or functions). No `after_edit`: `restart_after_edit`, so a save makes the window offer a
  restart of a running service.

## As root

`roothelper._Helper`'s ops (OPS is built from public methods):
- `service(manager, verb, unit)`: the manager must be in `BACKENDS`, the verb in **its** `verbs`, the name
  `valid_name` and `installed`; then `backend.act()` -- the command line is always the backend's. A user unit is
  never offered root: its manager is the user's own.
- `after_edit(manager)`: the backend's `after_edit` when `reload_after_edit`, else nothing.
- `journal_follow(unit, path, lines)` (systemd only) writes `journalctl --follow` into **an existing file of the
  asking user's**, opened through `_pinned` without following a link and never created; `journal_stop(pid)` stops
  only a pid it started, and `serve()` stops them all in a `finally`.

## The window (`navigator/widgets/shell/service_window/`, `service_list/`)

- `ServiceWindow.backend` is `services.current()` from `__init__`. A manager other than systemd is named in the title
  (*Services (OpenRC)*) and the first column says *Service*. **What the backend has not is greyed in `refusal()`**
  (*Not something OpenRC does*): a verb outside its `verbs`, *User units*, *All types* (whose boxes are also
  `disabled`, and their key does nothing).
- `ServiceList` is a `ColumnList` (in `process_list.py`, shared with `ProcessList`). Rows are `.running`, `.inactive`
  (dim), `.failed` (bold and underlined: **a colour of its own failed `test_no_theme_draws_an_unreadable_pair`**) and
  `.masked` (italic).
- Reads go through `Background("nav-services")` with a read counter. **There is no read in `mounted()`**: the
  `_follow_view` effect's first run reads, because `_read_for` is None. The cursor is kept by name.
- Keys: F3 log, F4 edit (**not Filter, as Process list's F4 is**), Enter details, F5 start, F6 restart, F7 reload,
  F8/Del stop (asks), Ctrl+E enable, Ctrl+D disable, Ctrl+U user units, Ctrl+A all types, Ctrl+N/Ctrl+L sort,
  Ctrl+S/Alt+F filter, Ctrl+R re-read. Mask (asks) and Unmask are in the menu only.
- **Every verb command subclasses `ServiceVerb`**, but navkit delivers a command to `on_<its own class name>`, so the
  window aliases each handler name to `on_service_verb`.
- A refused action, for a system service with elevation available, goes through `ask_as_root` and
  `ELEVATION.call("service", manager=unit.backend, ...)` with `release()` in a `finally`.

## F4 in the window

- `_edit()` takes the `EditPlan`. A seeded (new) file first gets its directory (`_override_dir`: as the user, or the
  helper's `makedirs` after *As root*) because the editor's save does not create directories; it then opens as a
  new document with the seed inserted and the cursor on `plan.line`. Comments only, so saving it unchanged changes
  nothing.
- **A directory made by this F4 is removed when the editor closes with the file never written** (and nothing else
  there): `EditWindow.after_close` calls `_discard_unused` on a thread -- as the user, else through the helper's
  `rmdir` only while root access is still open. It never asks for root again just to tidy up.
- **The window learns of a save through `Shell.on_file_saved`**, which calls `unit_file_saved(path)` on every window
  that has it. A path from `_editing` then runs `services.after_edit` (systemd: daemon-reload; refused, straight to
  the helper's `after_edit` when root access is already open, else after *As root*) or, for a backend with
  `restart_after_edit`, asks to restart the service if it runs.

## F3 in the window (`journal_window.py`)

- `open_log()` asks `services.log` on a thread. A `Journal` goes to `open_journal()`: an empty 0600 file in
  `tempdir.private_dir()`, the follower (as the user, or `journal_follow` as root with `ELEVATION.hold()`), up to
  `FIRST_LINES` for the first bytes, then a `JournalWindow` (a `FileWindow`) with *Follow end* on. Its
  `unmounting()` stops the follower and deletes the file on a thread (`stopping`); an `atexit` hook stops any left.
  It keeps no File View History record.
- A `LogFile` goes to `open_log_file()`: a plain `FileWindow` on the file (`view_as_root` after *As root* when the
  user may not read it), `show_lines(LinePattern(pattern))` when there is a pattern, then *Follow end*. The title
  says *Log: <name>*, and *(its lines in <path>)* when filtered.

## Tests

- `tests/test_services.py` (systemd): the merge, sorting, names, `act`'s refusal, the helper's ops (no process for a
  bad manager, verb or name), and the window with `services.gather` patched, `[services] refresh` 0 and **`[services]
  manager` pinned to systemd** (`service_run`, so the host's own manager does not matter) -- filter, cursor, boxes,
  F5/F8/Ctrl+E, As root with `ELEVATION.call` faked (**pass every other op through**: a root drive another test left
  mounted calls `children`), F3's journal, F4's file and drop-in, and the unsaved drop-in's directory removed.
- `tests/test_services_openrc.py`: `rc-status`/`rc-update` parsing and merge, what each verb runs, refusals, details,
  F3's own/filtered/no log, F4's seed, `current()`'s choice, the helper's `installed` check, and the window with
  `manager = "openrc"` **and `openrc.refusal` patched to ""** (else the shell greys Services on a machine without
  OpenRC): greying, As root, F3 filtered, F4 then the restart offer. `/etc/init.d`, `/etc/conf.d` and the system logs
  are the `etc` fixture's, in `tmp_path`.
