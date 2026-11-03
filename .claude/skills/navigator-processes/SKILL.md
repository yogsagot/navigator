---
name: navigator-processes
description: Utilities > Process list, FAR Manager's process panel and a departure from DN (DOS ran one program at a time) -- navigator/lib/system/processes.py (read/gather from /proc with no psutil, parse_stat's last-")" split, Process and Row, Sampler's top-style CPU %, ordered/tree, details, SIGNALS, protected/send/still/signal_process), the root helper's kill op, ProcessList (columns, tree glyphs, header-click SortChosen, type-to-search), ProcessWindow (refresh timer, cursor kept by PID, sorts Ctrl+P/U/E/L/Z/N, Ctrl+T tree, Ctrl+H mine only, F3 details, F7 signal box, F8/Del SIGTERM, As root), and [processes] refresh. Use when changing the process list or anything that signals a process.
---

# Process list

**Not DOS Navigator's.** DOS ran one program at a time and DN had nothing to list, so the whole window is a departure.
It is recorded in the module docstring of `navigator/lib/system/processes.py`, the `#:` comment above Utilities >
*Process list* in `main_menu.nml`, and the window's markup. It is FAR Manager's process panel, built in a window the way
Disk > Volumes is built.

## The model (`navigator/lib/system/processes.py`)

- It reads `/proc/<pid>/stat`, `status` (for `Uid:`) and `cmdline` directly. **No psutil**: the run-time
  dependencies stay pure Python. `available()` is false without `/proc`, and `Shell.refusal` then greys out the menu
  entry with the reason.
- **`comm` may hold spaces and `)`**, so `parse_stat` splits at the *last* `)`. A kernel thread has an empty
  `cmdline`, so its command is `[comm]` (`Process.kernel_thread`). A process that ends while it is being read is left
  out silently.
- `Sampler` is called on the reading thread. It gives each process its CPU % since the last call, top-style: ticks
  over `/proc/stat`'s machine ticks, times the CPU count, so one busy thread reads 100%. A process is keyed by
  `(pid, started)`, so a reused pid starts again at 0. The first read is all zeros.
- `ordered(items, by, descending)` sorts with the pid breaking ties. `tree()` gives `Row`s depth first. A process
  whose parent is not in the list is a root. Each `Row` carries `rails` (for each level above it, whether that level
  has more to come) and `last`, from which `ProcessList.branch` draws `│ `, `├─` and `└─` (ASCII tiers through
  `glyphs.charset`/`joins`).
- **A signal goes to the process that was read, not to its number.** `signal_process` calls `still()`, which reads the
  process again and raises `ProcessLookupError` if its start time changed. `send()` refuses pid ≤ 1 and Navigator's own
  pid (`protected()`).

## As root

`roothelper._Helper.kill(pid, signal)` is an op. `OPS` is built from the public methods, so defining the method is
enough. It refuses pid ≤ 1, the helper's own pid and its parent's (sudo or pkexec). The window offers it when `send`
raises EPERM/EACCES (`elevate.refused`) and `ELEVATION.available()` is true, through `as_root.ask_as_root`. It then
runs `still()` and `ELEVATION.call("kill", ...)` on a thread, with `ELEVATION.release()` in a `finally`. `call`
re-raises a plain `OSError`, so test `.errno`, not the subclass.

## The window (`navigator/widgets/shell/process_window/`, `process_list/`)

- `ProcessList` is Python only, copying `VolumeList`: fixed columns plus a flexible *Command* column, the dividers
  painted in `render_header`, and ▲/▼ (`glyphs.scrollbar`) on the sorted column. **A press on the header row emits
  `SortChosen(by)`** (the only header-click sort in Navigator). Row classes `.mine`, `.root`, `.kernel`, `.zombie`,
  `.stopped`, `.running` and `.waiting` are styled in `navigator.nss`.
- Quick search lives in the list: Ctrl+S, or typing a printable character other than Space. It matches the start of
  `comm`, the program's basename, the command or the pid (`navml.quick_search.name_pattern`). The window's status line
  shows `Search: …` while it runs (an effect on `search`). `edits_text` is true while searching.
- `ProcessWindow` reads through `Background("nav-processes", workers=1)` with a read counter, so only the newest read
  is shown. It starts in `mounted()`. A `call_every([processes] refresh)` timer (0 turns it off) skips a tick while a
  read is in flight or `app.modal` is set. It is cancelled in `unmounting()`. `_show()` peeks the items and the cursor
  and puts the cursor back **by pid**.
- Sorting keys: Ctrl+P (pid), Ctrl+U (user), Ctrl+E (state), Ctrl+L (CPU load), Ctrl+Z (memory size) and Ctrl+N
  (command name). They are not the Ctrl+F keys FAR uses, because the desktop and the global table hold those. Pressing
  the same key again reverses the order. CPU and memory sort biggest first (`DESCENDING_FIRST`).
- Other keys:
  - Ctrl+T ticks *Tree* and Ctrl+H ticks *Mine only*. These are check boxes followed by an effect.
  - F3, Enter and *Details* open the `details()` lines in an ok `Dialog`. **`on_chosen` is handled by the window**, or
    `Shell.on_chosen` would take the row for a volume or directory.
  - F7 and *Signal* open a `PopupMenu` of `SendSignal(n)` entries.
  - F8 and Del ask yes/no, then send SIGTERM.
  - Every signal path is spawned, never awaited in a handler, and the window re-reads afterwards.
- Key tables: `process_window` and `process_list` in `keybindings.TABLES`. Regenerate the default set after a binding
  changes.

## Tests

`tests/test_processes.py` covers:
- the model, over a fake `/proc` in `tmp_path`
- real signals to a child `sleep`
- the window, with `processes.gather` monkeypatched and `[processes] refresh` set to 0 so no timer races the test
- the helper's `kill` op directly
- one As root run through the unprivileged test helper (`ELEVATION.command = [python, -I, -c, elevate._BOOT]`)
