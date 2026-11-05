---
name: navigator-services
description: Utilities > Services, a departure from DN (DOS had no service manager) -- navigator/lib/system/services.py (gather merging systemctl list-units and list-unit-files, JSON with a plain fallback, templates left out, Unit, ordered/matches, VERBS and valid_unit, act with --no-ask-password and polkit's refusal as EPERM, details, journal_argv, can_read_journal, Follower), the root helper's systemctl/journal_follow/journal_stop ops, ServiceList (a ColumnList), ServiceWindow (User units, All types, F5/F6/F7/F8, Ctrl+E/Ctrl+D, mask/unmask, As root), F3's JournalWindow following journalctl in the viewer, and [services] refresh/journal_lines. Use when changing the Services window, its systemctl calls or the journal it follows.
---

# Services

**Not DOS Navigator's.** DOS had no service manager, so the whole window is a departure, asked for. It is recorded in
the module docstring of `navigator/lib/system/services.py`, the `#:` comment above Utilities > *Services* in
`main_menu.nml`, and the window's markup. It is Process list's sibling and is built the same way
(`navigator-processes`).

## The model (`navigator/lib/system/services.py`)

- **Every command goes through `_run(argv)`** (`LANG=C` so a refusal can be read, a timeout, no stdin). Tests
  monkeypatch that one function, or `gather`/`act`/`details`/`journal_argv` above it.
- `gather(user, all_types)` merges `list-units --all` (load, active, sub, description) with `list-unit-files` (the
  file's state). A unit installed but never loaded is only in the second and is shown `inactive/dead`. An instance
  (`getty@tty1.service`) takes its template's file state; **a template (`getty@.service`) is left out** (it can be
  neither started nor followed). `--output=json` first, the `--plain --no-legend` columns when it is refused
  (systemd < 246).
- **What may be done is closed**: `VERBS` (start, stop, restart, reload, enable, disable, mask, unmask) and
  `valid_unit()` (systemd's characters, never a leading `-`, a dot required). `act()` runs
  `systemctl [--user] --no-ask-password VERB -- NAME`. **`--no-ask-password` keeps polkit off the terminal Navigator
  draws on**; its *Access denied* / *Interactive authentication required* becomes `OSError(EPERM)`, which
  `elevate.refused()` takes for a step to offer *As root*. Anything else is `EIO` with what systemctl said.
- `details()` is `systemctl status --lines=0 --full` (exit 3 for a stopped unit is no failure).
- `unit_file()` is `systemctl show --property=FragmentPath --value`; empty or `/dev/null` (masked) is `ENOENT`.
  `daemon_reload(user)` is `systemctl [--user] --no-ask-password daemon-reload`, failing as `act` does.
- `can_read_journal()`: a user unit, root, or a member of `systemd-journal`/`adm`/`wheel`.

## As root

`roothelper._Helper` has three ops (OPS is built from public methods):
- `systemctl(verb, unit)` checks both again and calls `services.act` on a system unit. A user unit is never offered
  root: its manager is the user's own.
- `journal_follow(unit, path, lines)` writes `journalctl --follow` into **an existing file of the asking user's**,
  opened through `_pinned` without following a link and never created, and keeps the `Popen` in `self.journals`.
- `daemon_reload()` runs the system manager's daemon-reload, after a unit file was saved as root.
- `journal_stop(pid)` stops only a pid in that table. `serve()` stops every journal in a `finally`, so a helper
  that ends (root_timeout, Navigator quitting) leaves no `journalctl` behind.

## The window (`navigator/widgets/shell/service_window/`, `service_list/`)

- `ServiceList` is a `ColumnList` (in `process_list.py`, shared with `ProcessList`): `WIDTHS`/`SORTS` declare the
  columns, the base draws the titles and dividers, emits `SortChosen` on a title press and gives typing to
  `filter_line`. The window reuses `ProcessFilter` for its *Filter* line.
- Rows are `.running`, `.inactive` (dim), `.failed` (bold and underlined: **a colour of its own failed
  `test_no_theme_draws_an_unreadable_pair`** on some themes) and `.masked` (italic).
- `ServiceWindow` reads through `Background("nav-services")` with a read counter. **There is no read in `mounted()`**:
  the `_follow_view` effect's first run reads, because `_read_for` is None; afterwards it reads only when *User
  units* or *All types* changed, and only re-shows for the filter. `call_every([services] refresh)` skips a tick while
  reading or modal. The cursor is kept by unit name.
- Keys: F3 journal, F4 edit the unit file (**not Filter, as Process list's F4 is**: F4 is Edit everywhere else), Enter/double click details (`on_chosen` handled here), F5 start, F6 restart, F7 reload, F8/Del
  stop (asks), Ctrl+E enable, Ctrl+D disable, Ctrl+U user units, Ctrl+A all types, Ctrl+N/Ctrl+L sort, Ctrl+S/Alt+F
  filter, Ctrl+R re-read. Mask (asks) and Unmask are in the menu only.
- **Every verb command subclasses `ServiceVerb`**, but navkit delivers a command to `on_<its own class name>`, so the
  window aliases each handler name to `on_service_verb`.
- Every action is spawned; a refused one, for a system unit with elevation available, goes through
  `as_root.ask_as_root` and `ELEVATION.call("systemctl", ...)` with `release()` in a `finally`. The window re-reads
  afterwards either way.

## F4: the unit file

- **A masked unit is refused** by `unit_file()` (*unmask it first*): its file is not what systemd uses, and systemd may
  still report the package's file as its `FragmentPath`.
- `edit_target()` decides what opens. The fragment itself when it is the administrator's own (under `admin_dir()`:
  `/etc/systemd/system`, or `$XDG_CONFIG_HOME/systemd/user` for a user unit, **compared after `realpath`**, so a
  link in `/etc` to a package's file still counts as the package's). Otherwise the drop-in
  `<admin_dir>/<unit>.d/override.conf`, `systemctl edit`'s name: a package's file is overwritten by its next upgrade,
  a drop-in is not.
- `_edit()` makes the `<unit>.d` directory first (`_override_dir`: as the user, or the helper's `makedirs` after *As
  root*), because the editor's save does not create directories. A drop-in that does not exist yet opens as a new
  document seeded with `override_text()` -- a header, a blank line at `OVERRIDE_LINE` where the cursor is put, then
  the package's file commented out -- comments only, so saving it unchanged changes nothing.
- **A `<unit>.d` made by this F4 is removed when the editor closes with the override never written** (and nothing
  else put there): `EditWindow.after_close` calls `_discard_unused`, which works on a thread -- as the user, else
  through the helper's `rmdir` only while root access is still open. It never asks for root again just to tidy up;
  with `root_timeout` 0 the empty directory stays. A directory that was there before F4 is never removed.
- The file is read as the user (unit files are everyone's to read); a save refused permission is the editor's own *As
  root*.
- **The window learns of a save through `Shell.on_file_saved`**, which calls `unit_file_saved(path)` on every window
  that has it (the editor's `FileSaved` bubbles to the shell, never to this window). A path F4 opened from here
  (`_editing`) runs `daemon_reload`; refused, it goes straight to the helper when root access is already open (the
  file was most likely just saved through it), else after *As root*. Then the list is read again.

## F3: the journal (`journal_window.py`)

- `open_journal()` makes an empty 0600 file in `tempdir.private_dir()`, starts the follower (as the user, or
  `journal_follow` as root after *As root* was accepted, with `ELEVATION.hold()`), waits up to `FIRST_LINES` for the
  first bytes, opens `ViewSource` on a thread and puts a `JournalWindow` (a `FileWindow`) on the desktop, then turns
  *Follow end* on through `on_follow_end`. The viewer's own tick watches the file; nothing else reads it.
- `JournalWindow.unmounting()` stops the follower and deletes the file **on a thread** (`stopping`, which tests join).
  The stopper runs once, and an `atexit` hook stops any still live when Navigator quits.
- It keeps no File View History record (`remember_history`/`recall_history` are no-ops): its file is gone once it
  closes.

## Tests

`tests/test_services.py`: the merge (JSON, plain, user, all types, templates), sorting and names, `act`'s refusal, the
helper's ops (no process for a bad verb or name; a follower into the user's file stopped by pid), and the window with
`services.gather` monkeypatched and `[services] refresh` 0 -- the filter, the cursor by name, re-reads for the boxes,
F5/F8/Ctrl+E, As root with `ELEVATION.call` faked (**pass every other op through**: a root drive another test left
mounted calls `children`), and F3 with `journal_argv` swapped for a Python loop printing lines.
