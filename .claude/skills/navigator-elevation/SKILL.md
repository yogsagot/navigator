---
name: navigator-elevation
description: As root -- doing a step refused permission (EACCES/EPERM) again as root, a departure (DOS refused no one). navigator/lib/system/elevate.py (ELEVATION, sudo -S with Navigator's own password box or pkexec's polkit agent, begin/answer/call, release and root_timeout, close at exit, ELEVATION.command for tests), navigator/lib/system/roothelper.py (the helper process, its framed JSON protocol and closed OPS list), navigator/lib/drives/root.py (RootDrive, LocalDrive's steps through the helper, write_file for the editor), filecopy's Elevated mixin and AS_ROOT (copy, move, erase, Alt+E attributes), F7 mkdir, Shift+F5 links, Alt+A multi-rename and Alt+F6/Shift+F6 rename, navigator/widgets/file_ops/as_root.py (ask_skip, ask_as_root, open_root), the editor's F2 save, Save as, ^K W and ^K R, F3's viewer, Ctrl+Q quick view and F4's read through the helper (hold/unhold), As DataBase on a copy fetched as root (usefile's TempCopy.drive), Ctrl+F7/F8 UU encode/decode, Alt+L's list file, archives on the disk (Enter, Shift+F2, a refused rewrite), and [system] elevate / root_timeout in System Setup. Use when touching any of these or wiring another operation to offer As root.
---

# As root

A departure: DN never met a permission. When a step on the local disk fails with `EACCES`/`EPERM`, the error box
offers **As root** beside Skip/Cancel; answered, the step is done again through a root helper, and **every later step
of that operation goes through it without asking again** (DN's *All*).

## The pieces

- **`navigator/lib/system/elevate.py`** -- `ELEVATION`, the one helper. `begin()` starts it and answers `READY_STATE`,
  `Asked(prompt, wrong)` or `Refused(reason)`; `answer(password | None)` continues. **Everything blocks: call on a
  thread** (`asyncio.to_thread`), never the loop.
  - sudo runs as `sudo -S -p MARKER -- python -I -c BOOT` in a new session with no terminal of ours: its prompt
    comes through stderr and is recognised by `MARKER`; *Sorry* before it means `wrong`. The password goes to sudo's
    stdin and is never kept. pkexec's polkit agent asks for itself, so `begin` may wait (`START_TIMEOUT`).
  - `[system] elevate` (`auto` = sudo else pkexec, `sudo`, `pkexec`, `off`); `available()` is false when already
    root, off, or no tool installed -- then As root is not offered at all.
  - `release()` at the end of every operation closes the helper when `[system] root_timeout` is 0; otherwise the
    reaper closes it that many idle minutes after its last step. `Navigator.on_stop` closes it.
  - **`hold()`/`unhold()`**: a window that keeps a file open through the helper (F3's `_RootRandom`) holds it;
    neither `release()` nor the reaper closes a held helper. The handle's `close()` unholds and releases.
  - **`ELEVATION.command`** replaces the tool's argv: tests run the helper unprivileged with it (`tests/test_elevate.py`).
- **`navigator/lib/system/roothelper.py`** -- the root process. Messages are a 4-byte big-endian length, that much
  JSON, then `size` raw bytes. **Only names in `OPS` (the public methods of `_Helper`) may be asked**; an unknown op is
  `EINVAL`. Answers are `{"ok": ...}` or an `OSError` as `errno/strerror/filename`, re-raised as the same `OSError`
  subclass on our side. It says `READY` once and ends at end of input. Started with `-I`, the package path inserted
  explicitly, so nothing from the user's current directory or environment is imported as root.
- **`navigator/lib/drives/root.py`** -- `ROOT_DRIVE`, a `LocalDrive` whose every step is a helper request (files are
  `_RootFile`s read/written a `CHUNK` per request). `write_file` is the editor's `save.write_file` run in the
  helper; the text is gathered there first, so it is not stoppable part way.
  **The lock check is done here, not in the helper** (`check_lock=False` there): the editor's own `flock` would
  otherwise make the root process look like another program and refuse the save.

## Wiring an operation

- **Workers** subclass `filecopy.Elevated`: use `self._drive_of(location)` instead of `drive_of`, wrap a step in
  `self._try(path, step)` (or loop on `self._failed(path, error)`), and call `self._release()` in `run`'s `finally`.
  `Failure.elevate` is set only for a local path, a refusal errno, and a worker not yet elevated -- a step refused
  even as root is just Skip/Cancel. `is_root` turns true once elevated, so *Preserve attributes* sets owners.
  Copy/move (`_Copier`), erase (`_Eraser`) and Alt+E (`fileattr._Changer`, whose own `_stat`/`_children` go
  through the helper once elevated, and `apply_one(as_root=True)`) are wired.
- **The loop side** is `navigator/widgets/file_ops/as_root.py`: `ask_skip(app, message, elevate=)` (Skip / As root /
  Cancel; answers True, None or `AS_ROOT`), `ask_as_root(app, message)` (As root / Cancel), and `open_root(app)` (the
  `PasswordDialog` titled *Root access* until sudo accepts, an *Error* box on a refusal, silence on Cancel).
  `Manager._ask_skip` passes `question.elevate` through.
- **The editor**: `EditWindow._write_or_root` (F2's `save` and `save_as`) offers it on a refused write (not for a
  `UseFile` copy) and writes through `ROOT_DRIVE.write_file`, releasing after. `_check_for_over`'s lifting of a
  read-only mode is let pass when refused and root is available: the write is refused next and offers *As root*.
- **^K W / ^K R** (`write_block`, `read_block`): the same retry with `ask_as_root`; ^K W writes through
  `ROOT_DRIVE.write_file` (or `open_write(append=True)` for *Append*), ^K R reads with
  `document.read_text(as_root=True)` (`read_document` stats and opens through `ROOT_DRIVE`).
- **F3** (`Manager` on a local file, after `open_viewer` is refused): `ask_as_root`, then
  `as_root.view_as_root` opens a `viewer.ChunkedSource` on `ROOT_DRIVE.open_random` -- chunks fetched on a thread
  as a server file's are, never a helper round trip on the loop -- with `source.drive = ROOT_DRIVE` so the viewer's
  *Save as* reads through it too. The helper's `read_at` op is `os.pread` on the open handle.
- **Ctrl+Q quick view** (`QuickViewer._opened`): a refused open is read as root **only while
  `ELEVATION.running`** -- moving the cursor never asks for a password -- through `as_root.root_source` (a
  `ChunkedSource`, full path as its `path` so the "already showing" check holds), retried once, never again.
- **F4 opening** (`Manager.edit_file` -> `open_editor(as_root=True)` -> `load_document` -> `read_document(as_root=)`):
  the text read into memory through the helper, released after; the window's path is the original, so F2 is
  refused in its turn and offers *As root* again.
- **F3 As DataBase** (`.dbf`): `as_root.database_as_root` fetches it and its `.dbt`/`.fpt` with
  `usefile.fetch(..., drive=ROOT_DRIVE)` into the private directory, **owner-only (0600) whatever the original's mode**
  -- it may hold what only root could read. `TempCopy.drive` makes `conflicts`/`upload` go through it; `upload`
  through a drive with `write_file` (root's) writes in place of the original keeping owner and mode, never the
  usual new file renamed over (which root would own). `Manager._may_as_root` is the shared ask for F4/As DataBase.
- **Ctrl+F7/F8 UU** (`Manager._run_uucode(..., as_root=)`): a refusal (source unreadable, target refused) offers
  *As root* and runs the work again through `Manager._staged(..., as_root=True)`: the source fetched through
  `ROOT_DRIVE` into the private directory, encoded/decoded into staging, the files put on the disk with
  `usefile.put_files(..., drive=ROOT_DRIVE)` (asked about first, as for another drive). A target naming a directory
  is staged as one. New files are root's, as a copy made as root is.
- **Alt+L list file** (`Manager._write_list`, both the local and the elsewhere writer): a refused write to the disk
  offers *As root* and writes through `ROOT_DRIVE.makedirs`/`open_write(append=)`.
- **Archives on the disk** (`navigator/lib/drives/archive.py`): an unreadable one raises `PermissionError` from
  `open_archive` (before, `zipfile.is_zipfile` swallowed it and it was taken for *not an archive*, i.e. run as a
  program). `open_archive(as_root=True)` opens it the way an archive on another drive is opened: a private copy
  fetched with `usefile.fetch(..., drive=ROOT_DRIVE)`, every rewrite put back through root's `write_file` (owner
  and mode kept). `ArchiveDrive.as_root` drives **hold the helper** until `close()` (unhold + release), since a
  put-back can come at any time. `ArchiveDrive.go_root(job)` switches an open one whose rewrite was refused:
  staged members stay staged, the rewrite is made in the copy. `finish_drives(..., elevate=)` asks
  `Elevated._finish_as_root` first (copy/move, erase and Alt+E pass it; Alt+E's finish now runs inside `_Changer.run`). On the loop,
  `widgets/drives/archives.open_archive_or_root` (Enter, Shift+F2's *Extract*) asks `ask_as_root`.
- **The viewer's Save as** (`FileWindow.save_as`): a refused local target retries `viewer.save_as(..., as_root=True)`,
  written through `ROOT_DRIVE.write_file` (owner/mode kept), released after.
- **A write-protected `.dbf`** (`DBWindow._edit_as_root`): editing a field offers *As root*, then the window moves
  onto a copy from `as_root.fetch_database`; every field goes back through root. **A root-fetched dBase copy holds
  the helper** (`DBWindow.root_held`) until the window closes -- else, with `root_timeout` 0, the first put-back
  found it closed. `database_as_root` sets the same.
- **F7 and Alt+A inside an archive** whose rewrite is refused: F7's remote branch offers `_may_as_root` and finishes
  through `go_root`; `multirename._finish` asks a `Failure` (with `elevate` for a local archive) where the failure
  used to be passed over in silence -- the renames were shown and never written.
- **Remote drives are deliberately not offered it**: local root cannot get past a server's refusal (FTP, SMB, S3
  have no notion of it; SFTP would need the server's `sftp-server` under its own sudo -- a separate feature,
  declined for now).
- `Manager._may_as_root(error, message)` is the shared ask; `_as_root_declined` is only meaningful right after
  it was called -- guard a read of it with the same condition that called it.
- **Multi-rename** (`multirename.run`): a refused rename of a file still under its own name asks with `elevate`;
  `AS_ROOT` sets `RenameJob.elevated` and retries, every later rename on a local place going to `ROOT_DRIVE`. A file
  stranded under its `.navrename-` name keeps the old put-back path (no offer). **Alt+F6/Shift+F6**
  (`Manager._rename_entry`) asks `ask_as_root` and renames on `ROOT_DRIVE`.
- **On the loop** (F7, Shift+F5): the first step stays on the loop as before; **once elevated every step goes to a
  thread**, since a helper request blocks. F7 asks `ask_as_root` and makes the directory with `ROOT_DRIVE.mkdir`;
  `Manager.link_entries` asks `ask_skip(elevate=)` per refusal until answered, then `filelink.make_link(...,
  as_root=True)` and `ROOT_DRIVE.makedirs` for the rest, releasing in its `finally`.

## Not wired yet

Remote drives (see above); Shift+F4's new file in a
directory the user cannot write is offered at F2's save.
Each would follow the pattern above.
