---
name: navigator-gio
description: The desktop's GIO through the `gio` command -- navigator/lib/system/gio.py (program(), [system] use_gio, graphical(), run() and its reasons, parse_mount_list for `gio mount -li`, volumes/mount_device/unmount/eject, open_file/content_type/applications/launch, GVFS_SCHEMES/gvfs_schemes, mount_uri and its prompts, local_path/uri_of, trash), Disk > Volumes' Mount/Unmount/Eject and unmounted rows (volumes.merge, gather_all), Enter's fallback to the desktop's application ([file_manager] open_unassociated, Shell.open_on_desktop) and File > Open with (OpenWith, Shell.open_with), GVfs drives (navigator/lib/drives/gvfs.py: GvfsDrive over the FUSE bridge, mtp://, dav://, google-drive://..., Utilities > GVfs link, sessions.module_name/is_connection), and the `gio trash` fallback in fileerase. Use when touching any of these, or adding another thing GIO could do.
---

# GIO (the `gio` command)

**Not DOS Navigator's**: four departures, each recorded where it is made. Navigator drives GLib's **`gio` command-line
tool**, not GLib itself -- PyGObject is compiled, and every run-time dependency is pure Python -- the way archives drive
7-Zip's. `navigator/lib/system/gio.py` is the one module that runs it.

## Rules

- **`gio.program()` is the gate.** None when `gio` is not on `PATH` *or* `[system] use_gio` is off (ini-only: the
  System Setup page has no room). Every command or menu item that needs GIO greys out through it (`enables()`), and the
  Enter fallback and the `gio trash` fallback check it before trying. `shutil.which` is looked up at the call, as
  `printing.print_command` does, so a test can replace it.
- **Every call but `program()` and `graphical()` blocks**: run it with `asyncio.to_thread`, on a
  `Background`, or inside a `Job`. `MOUNT_TIMEOUT` (60 s) bounds mounts; `TIMEOUT` (15 s) the rest.
- **A failure is `OSError` carrying gio's own words** (`_reason`: its last stderr line, less `gio: ` and the URI).
  Callers put `strerror` in a box.
- **A desktop application is detached** (`launch_detached`: `start_new_session`, all three streams to `/dev/null`),
  or it would paint over the screen. `gio open` itself returns once the application has been asked, so it is run to its
  end and its error is shown.
- **`graphical()`** (`$DISPLAY` or `$WAYLAND_DISPLAY`) gates opening and launching: over SSH there is nowhere to open
  a window.
- **The test suite runs with `use_gio` off** (`tests/conftest.py`), so this machine's mounts never leak into a test.
  `tests/test_gio.py` switches it back on and puts a fake `gio` (a Python script) first on `PATH`.

## Volumes (Disk > Volumes)

- `gio.parse_mount_list` reads `gio mount -li`'s indented Drive/Volume/Mount tree. It lists every **Volume** and every
  **Mount without a volume** (a GVfs share, a phone), but no Drives. A volume's mount gives it its `uri` and
  `can_unmount`. A mount line is `Mount(0): name -> uri`.
- `volumes.gather_all()` (the window's read) is `gather()` plus `merge()` with gio's list:
  - a mounted volume gets its flags, matched by mount point;
  - a volume that is not mounted becomes a row with `mount=""`, `mounted=False`, listed after the others;
  - a GVfs mount becomes a row at its FUSE path (`local_path(uri)`). Without a FUSE path it is not listed.
- `Volume.target` is what Unmount/Eject are given: the gio URI, else the mount point.
- **Mount** (F5, Ctrl+N), **Unmount** (F6, Ctrl+U) and **Eject** (F7, Ctrl+E) are `MountVolume`/`UnmountVolume`/
  `EjectVolume`: in the window's menu, its right-click menu, and **buttons** on *Go* and *Close*'s row where the window
  is 82 columns or wider, else right-aligned in a row over them (the list two rows shorter then). The **F-keys put them on the key bar**, greyed as `enables` says. Ctrl letters show
  there only while Ctrl is held. `VolumesWindow.allows(action)` follows gio's `can_*` flags; `enables` and the
  buttons' bound `disabled` both read it. Each action runs on a thread, says a failure in a box, then reloads.
- `mount_device` mounts by device or UUID (`gio mount -d`), or through `activation_root` (a phone).
- **Enter/Go on a row that is not mounted**: `VolumesWindow.on_chosen` stops the event, and `_mount_and_choose`
  mounts it, reads again, finds the same volume by `ident` or name, and emits `ChosenEvent` with the mounted one.
  `Shell.on_chosen` never sees an empty mount point.
- The unmounted row says *(not mounted)* and has no numbers (`VolumeList.cells`).

## Enter and *Open with*

- `Shell.on_open_file` → `_open_here`: `extensions.ini` first (`run_associated`); nothing there →
  `open_on_desktop(path)` (`gio open`).
- `desktop_opens()` requires all three: `[file_manager] open_unassociated` on (File Manager Setup's *Pass other files
  to desktop*, default on), `gio`, and a display. Otherwise nothing happens, as in DN.
- **A file on another drive** (`_open_elsewhere`): the `UseFile` copy is opened and **left in place**. Nothing waits
  for a desktop application, so nothing is sent back. The private temp dir goes at exit.
- **File > Open with** and the panel's right-click *Open with* (`OpenWith`, `Manager.on_open_with` →
  `Shell.open_with`):
  1. `content_type` (`gio info -a standard::content-type`) gives the file's type;
  2. `applications(mime)` (`gio mime`: the default, then registered, then recommended, each once; `Name=` from the
     `.desktop` file in the XDG data dirs, `a-b.desktop` also tried as `a/b.desktop`) lists the programs;
  3. a centred `PopupMenu` offers them;
  4. `gio launch DESKTOP-FILE FILE` opens the one chosen.
  5. Or **Command...**, last, under a line: `Shell.open_with_command` asks a command line in an `EditLineDialog`
     whose history is the extension's own (`open_with_history`: `open_with.png`, `open_with` with none). It is run
     in the console as an `extensions.ini` entry is (`run_commands`), so the user menu's macros work. With no `!`
     in it, ` !.!` goes on the end (`open_with_line`). A remote file is fetched there and sent back when the
     command ends. A GUI program holds the console unless the line ends with `&` (the user's choice over detaching).

  A remote file is typed by its name (`mimetypes`) and fetched only once an application is chosen.

  `Manager.enables` greys it for a directory, `..`, no gio or no display.

## GVfs drives (`navigator/lib/drives/gvfs.py`)

- **Schemes**: `gio.GVFS_SCHEMES` maps each URI scheme GVfs reaches but Navigator does not (mtp, gphoto2, afc, dav,
  davs, afp, nfs, google-drive, onedrive, cdda) to its backend's `*.mount` file. It is written out because a backend's
  `Type=` names *mount* types (`smb-share`), not URI schemes. `gvfs_schemes()` keeps those whose file is installed.
- **Not in `sessions.SCHEMES`**: that dict holds Navigator's own protocols. `sessions.module_name(scheme)` answers
  either kind; `is_connection(scheme)` is what Disconnect (Alt+H) and its enabling use. `PROTOCOLS` has each GVfs
  scheme's sign (`MTP`, `DAV`, `GDRIVE`...).
- **The host keeps its case** for a GVfs scheme (`location._host`): an MTP device name is not a DNS name. Every other
  scheme stays lower case.
- **`connect(site, answers)`**:
  1. `local_path(uri)` already resolves → the mount is someone else's (`ours=False`), used as it is and never unmounted.
  2. Otherwise `mount_uri` runs `gio mount URI` on pipes and answers its prompts (`User [default]: `, `Domain`,
     `Password`) from the site and `Answers`.
  3. A missing password, or a **second** `Password` prompt (GVfs asks again after a wrong one), raises
     `Prompted(again=...)`, which becomes `NeedPassword(wrong=again)` for `Shell.reach`'s box. Any other unanswered
     prompt is an `EACCES` with gio's message.
  4. The keyring box is not offered (`can_keep` false): GVfs keeps its own passwords.
- **Where the mount starts**: the asked place's FUSE path; `bridge_top` is the first name under the `gvfs` directory.
  The *prefix* is the part of the asked path that the top stands for (`/` for a phone, `/remote.php/webdav` for a
  WebDAV share there). It is the drive's `home`. A place above it is `ENOENT` (`OUTSIDE`).
- **`GvfsDrive`**: every step is `LOCAL`'s on the translated FUSE path, as `TrashDrive` does.
  - `is_local` stays false, so the one copier and `UseFile` treat it as remote.
  - No `WATCH`: FUSE tells nothing.
  - `close()` runs `gio mount -u` only when `ours`.
  - Idle reaping and Disconnect therefore unmount what Navigator mounted.
- **Ways in**:
  - `nav mtp://Device/`, a typed URL, history, profiles and saved desktops all go through `Shell.reach`;
  - Utilities > *GVfs link* (`GvfsLink`, `Shell.gvfs_link`): an `EditLineDialog` for the URI, history `gvfs_link`;
  - the Alt+F1/F2 box's Link part, *New GVfs link*, which `navy_link(scheme="gvfs")` redirects to.
- Volumes' GVfs rows go to the FUSE path as a local directory. They are not this drive's, and are not Navigator's to
  disconnect.

## `gio trash`

`fileerase._Eraser._to_trash`: when `trash.move` raises **`EXDEV`** (no trash directory the spec allows) and gio is
there, `gio trash` is tried before the `NoTrash` question; its failure's reason is the question's.

- GIO's daemon VFS maps a FUSE path back to its backend, so a GVfs mount's own trash is used.
- What goes there is **not listed in `trash:///`**, which reads only the spec's directories.

## Tests

`tests/test_gio.py`:

- the parsers on canned text;
- the prompt protocol against the fake `gio` (re-asking after a wrong password, as GVfs does);
- `GvfsDrive` mounted, read, written and unmounted through `SESSIONS`, and a mount found there already left mounted;
- the Volumes window with `gather_all` and `gio.mount_device`/`eject` replaced;
- Enter and *Open with* with `gio.open_file`/`applications`/`launch` replaced;
- the eraser's fallback, through the fake's `trash`.
