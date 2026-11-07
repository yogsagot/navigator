---
name: navigator-trees
description: Directory trees -- navml's TreeView/TreeNode, Navigator's DirectoryTree (Ctrl+T in the passive panel), Alt+T Choose Directory (TTreeDialog, change_dir_dialog), Disk > Directory tree window (TTreeWindow, tree_window), Disk > Volumes (VolumesWindow, VolumeList, navigator/lib/system/volumes.py), Disk > Directory sizes (ncdu's view: UsageWindow, UsageList, navigator/lib/file_ops/dirusage.py), tree quick search (Ctrl+S, path-based), and hidden-file handling in trees. Use when working on any tree view.
---

# Trees

Slots `[94-101]`, `[104-110]`.

- The library's `TreeView` is a `ListViewer` of flattened, lazily loaded `TreeNode`s, drawn as `TTreeView.Draw` draws
  them. Its flatten effect is `type(self)._flatten`, so a subclass may put a node on several rows (F3's
  structured view wraps long values that way, `navigator-viewer`). Navigator's `DirectoryTree` (`navigator/widgets/tree/`) is what **Ctrl+T** puts in the passive panel's place
  (DBLWND.PAS's `SwitchView`, via `Manager.switch_view`): the tree follows the active panel, and Enter or a resting
  cursor sends the panel where the tree points -- the resting one only under File Manager Setup's *Auto change
  directory* (`fmoAutoChangeDir`, on by default); Enter always.
- **Every tree has Ctrl+S quick search, and it is a path** (DN's `SearchForMask`): the panel's matching rules
  (`navml/quick_search.py`), and `/` opens the branch matched and confines the search to its children, so a lazy tree
  never needs a branch nobody opened. Typing searches too, except in Ctrl+T's tree (`type_to_search: False`), where it
  belongs to the command line.
- **Alt+T is DN's *Choose Directory*** (`TTreeDialog`, `navigator/widgets/tree/change_dir_dialog/`): the tree frameless
  in a dialog (`ListViewer.framed = False`), the path under it, and OK / Drive (disabled: one root) / Re-read / MkDir /
  Cancel down the right; OK sends the active panel there.
- **Disk > Directory tree opens `TTreeWindow`** (`navigator/widgets/tree/tree_window/`): a *Directory Tree* window on the
  desktop in the dialog palette; Esc closes it, Enter sends the active panel there (the tree's `ChosenEvent` bubbles to
  `Shell`). DN 1.51 defined that window but never opened it (its menu entry opened a second file manager) -- taking the
  window was a choice.
- **Disk > Volumes is not DN's** (a departure, in the place and letter of its *Volume label*): `VolumesWindow`
  (`navigator/widgets/shell/volumes_window/`) is laid out as the tree window, its `VolumeList` a `ListViewer` with
  column titles in its `header` band (Name, Type, Mount point, Use %, Free, Size; sizes by `sysinfo.size_text`; the *Show free %* box under *Show all mounts* makes Use % -- `df`'s -- Free %, `VolumeList.show_free`). The mounts
  are `navigator/lib/system/volumes.py`'s `gather()` over `/proc/self/mounts`, read on a thread (`Background`) from `mounted()`,
  never `__init__` -- a stale network mount holds `statvfs`, and one that raises is skipped. Only *real* volumes show
  (`is_real`: a `/dev` device -- a loop only when mounted under `udisks.USER_MOUNTS`, a disk image the user
  mounted, never a snap's under `/snap` -- a network or user FUSE mount); the *Show all mounts* box under the list (or
  Ctrl+H, which ticks it) shows the kernel's own too, without re-reading -- an effect on the box's `value`, which
  peeks the list so a cursor move does not wake it. Enter's `ChosenEvent` carries the `Volume` up to
  `Shell.on_chosen`, which sends the active panel to its mount point, and the window stays; *Go* (default, Alt+G) does
  the same and closes it; *Close* closes. Tab walks the controls and Alt+letter takes one, as the calculator
  window does. The window is kept by a saved desktop (`kind="volumes"`, with both boxes).
- **Volumes with `gio`, Solid or udisks** (`navigator-gio`, `navigator-kio` skills; `Volume.native` is the backend's own
  volume, `Volume.target` its URI, UDI or device): unmounted volumes listed as *(not mounted)*, GVfs mounts at
  their FUSE path, and *Mount* (F5), *Unmount* (F6), *Eject* (F7) as buttons, key-bar items and menu entries; Enter/Go on an unmounted one mounts it
  first. The window reads `volumes.gather_all`, which tests replace through `volumes.gather` (`desktop_vfs` is off in tests, and `udisks.program` None).
- **Who is asked is `desktop.volume_backend()`**, not `backend()`: the desktop's backend where its volume command is
  installed (`gio`; KIO only with `solid-hardware6`), else **udisks2's own `udisksctl`**
  (`navigator/lib/system/udisks.py`) -- with `desktop_vfs = off` too, since udisks2 is the system's service, not the
  desktop's plumbing (a decision, no setting). `desktop.volume_program()` is the window's gate (`allows()`).
  `udisks.parse_dump` reads `udisksctl dump` (object → interface → property → values, `'/'` quoted is *none*, a bare
  `/` a mount point); `parse_volumes` keeps file-system blocks less loops, `HintIgnore` and unmounted `HintSystem`,
  finds an opened LUKS volume's drive through `CryptoBackingDevice`, and offers Unmount on a removable drive or under
  `/media/`, `/run/media/`, `/mnt/` (KIO's rule). Every call passes `--no-user-interaction`: a polkit refusal (an SSH
  session) is an error box at once. **Eject** unmounts every file system on the drive, then `busctl ... Drive Eject`
  for an `Ejectable` one (a disc: `udisksctl` has no eject) or `udisksctl power-off -p drives/...` otherwise.
- **Volumes' *Mount image...* and *Unmount image*** (its menu and right-click menu, no keys): the Disk menu's
  `MountImage`/`UnmountImage`, which `VolumesWindow` answers while it is active. Mount asks for the file in a
  `FileDialog` (history `mount_image`, started in the active panel's directory, its cursor's image named), then
  `disk_image.mount_image` (progress, box, toast) and the cursor to the new row (`_select_mount`); Unmount takes the
  row's image (`udisks.image_at(volume.mount)`) whole through `disk_image.unmount_image`, which the panel's command
  uses too -- every Manager's `all_panels` inside it out first, the busy retries -- then reads again. Refusals: *The
  cursor is on no disk image*, *udisksctl (udisks2) is not installed*.
- **Disk images** (`udisks.attach_image`, Enter's -- `navigator-panels`): `udisksctl loop-setup -r -f FILE`, always
  read-only (the answer's `Mapped file ... as /dev/loopN.` names the device), or the user's loop already on that
  `Loop.BackingFile` reused; the dump re-read every `PROBE_INTERVAL` up to `PROBE_TIMEOUT` until udev has probed it
  (`IdUsage`, or a `PartitionTable` whose partitions are there); every file system on it mounted, an *already mounted*
  refusal (GVfs automounting first) no failure; then `busctl ... Loop SetAutoclear true` so the loop goes when its last
  file system is unmounted (skipped without busctl). None to mount: `loop-delete` and `EINVAL`. `parse_volumes` lists
  **the user's own loops** and their partitions (`Loop.SetupByUID` == `os.getuid()`, never 0; `_loop_of` through
  `Partition.Table`), named by label else the image's file name, with `loop`, `size`, Unmount and Eject; root's and
  snaps' stay hidden. **Eject on one** unmounts its file systems and runs `udisksctl loop-delete`. Always udisks,
  whatever `desktop_vfs` says: neither `gio` nor Solid's command sets up a loop.
  `image_mounts`/`image_at` find a mounted image without udisks (`/proc/self/mounts` loop devices under the user
  mount places, sysfs `backing_file`, a partition through its parent, ` (deleted)` cut); Eject runs `loop-delete`
  only while the loop still has a `BackingFile`: autoclear detaches it as its last file system goes, and udisks
  keeps the loop device with that empty (`loop-delete` then fails *Cannot perform operation*).
- **Nothing a tree paints waits on the disk.** `TreeView.probe_in_background` (on for `DirectoryTree`) asks an
  unopened node's probe on a thread (`navml.background`), drawing `[+]` until it answers and refreshing then; the
  info band's `count_files` runs on its own pool when the cursor stops, the line blank until it is in. Without a
  running application both answer at once, as before. **Every read is on a thread, the disk's too** (a dead
  mount or a 100k-entry directory froze the screen before): `DirectoryTree.load_in_background` is on, so an opened
  branch is read in `children_of` (open and empty until it lands), and **`show_path` is one walk on `_PATHS` for
  any drive** (`_walk_down`: `resolve()`, each level's `_subdirectories`, the dot-directory graft check), the
  branches opened and the cursor put when it lands. `tree._show_generation` makes only the latest call's landing
  move the cursor. `DirectoryTree.show` records `asked`; `Manager._tree_follows_panel` compares the panel's place
  with that, never `resolve()`s on the loop. Another drive's tree is rooted there (`use_drive_of`,
  `directory_root(at=)`). Alt+T's box turns both flags on for its plain `TreeView` (`ChangeDirDialog._show`). With
  the loop running, the cursor lands a moment after `show` -- tests wait with an `Until`.
- **Hidden files**: Ctrl+T's tree tracks the active panel's `show_hidden` (`DirectoryTree.set_show_hidden`); Alt+T and
  the tree window take it when opened (`hidden=`). Nodes carry it as `TreeNode.show_hidden`, and `show_path` grafts in a
  dot-directory the path goes through, so a panel inside `~/.config` still has a tree that finds it.

- **Each window has its own menu** (departures, asked for: DN's had none, and the Panel menu holding *Re-read* is off
  the bar while either is active). Disk > Directory tree's *~T~ree* (`tree_menu`): *Re-read* Ctrl+R, *Quick search*
  Ctrl+S (`TreeWindow.on_quick_search` hands it to the tree), *Close*. Disk > Volumes' *~V~olumes* (`volumes_menu`):
  *Re-read*, *Show all mounts* Ctrl+H (ticked, `VolumesWindow.checks`), *Close*. Both windows are also their own
  right-click host -- `ContextMenuHost`'s hooks written out, as `InputLine`'s, a component's half having one base --
  a click on a row first moving the cursor there (`prepare_context`, `row_at`).

- **While a tree searches, the key bar says *Ctrl+S Next*** (`TreeView.key_hints`); its search label is the search alone.

- **The Ctrl+T tree's right-click menu** (a departure, asked for): `DirectoryTree` is a `ContextMenuHost` whose
  `menu` its holder sets -- `Manager._tree_menu` for Ctrl+T's: *~G~o to directory* (Enter, `GoToTreeDirectory` ->
  `tree.choose()`), *~R~e-read* (Alt-R, `Rescan`, which reloads the tree while it has the keyboard), *Quick s~e~arch*
  (Ctrl-S), *~C~lose tree* (Ctrl-T); a right click on a row moves the cursor there first. With no `menu` (the Tree
  window's tree, Alt+T's) it offers none and the click goes on out, so the Tree window's own menu still answers.
  The menu takes the keyboard (Quick search needs it), so *Close tree* hands it to the panel put back, DN's
  `SwitchView`. Tests aim at a row that is painted: the tree reads from `/`, and where it scrolls depends on /tmp.

- **Disk > Directory sizes** (`OpenUsageWindow`, `UsageWindow`, `UsageList`; a departure, asked for -- DN had Alt+G
  and the tree's info line, never a ranking) is `ncdu`'s view, laid out as Volumes. `dirusage.scan` walks the whole
  tree once into `UsageNode`s on `Background("nav-usage")`, a `call_every` timer showing the `UsageJob`'s counters;
  only the newest scan (`_scans`) lands, and closing or Ctrl+R stops the one under way. Rules beyond `dirlength`'s:
  a directory's own size counts, another `st_dev` is listed but not entered (`other_fs`, `ncdu -x`; remote drives say
  0 so never), a hard link counts once (`hardlink`). Both `size` (apparent) and `usage` (`st_blocks`*512) are kept;
  Ctrl+A or the box picks one. Enter/Right descend, Backspace/Left/`..` ascend, all in memory. Sorting is Ctrl+N/
  Ctrl+S/Ctrl+E (name/size/entries; again reverses) -- **not Ctrl+F3..F5**, which *New manager*, the desktop's close
  and size/move hold. F8/Del goes through `Manager.erase_located` (F8's dialog, Trash, questions, As root; factored
  out of `erase_entries`), then `dirusage.remove` takes it off the totals with no rescan; the window is given the
  manager as SyncWindow is. *Go* (`GoToUsage`) sends the active panel there (a file: `Panel.go_to_entry`) and closes;
  Enter on a file does it and stays. Its menu *~S~izes* ticks the sort and *Apparent size*; in lv, *~G~o to directory*
  and *~D~elete...* stand where *~G~o*/*~D~elete* would share a hotkey with *Re-read*/*Close*.

## Read when

| Reference | Read when |
|---|---|
| `reference/trees.md` | the full design: TreeView, lazy loading, quick search, the dialogs, the tree window choice |

## Tooltips

- `TreeView.row_tooltip`: a node's whole name while cut -- its start scrolled off by `shift`, or its end past the
  right edge -- placed as `render_row` places it.
- `DirectoryTree.row_tooltip`: every directory's whole path (`node.data`); the info lines name only the cursor's.
- `VolumeList.row_tooltip`: the whole mount point and device, the mount's options (`Volume.options`, the fourth
  field of `/proc/self/mounts` through `volumes.mount_options`) and the sizes in exact bytes. A greyed Mount,
  Unmount or Eject says why (`VolumesWindow.refusal`).
- **Directory sizes' *Name* column scrolls sideways** (a departure, asked for, as the process list's *Command*), from
  the left, since names are cut at their end. Left and Right are `ncdu`'s up and down the tree here
  (`UsageWindow.on_key` takes them only without a modifier), so **Shift+Left/Right** move it a column and
  **Ctrl+Left/Right** `BIG_STEP` (20) (`UsageList.on_key`, `x_delta`, applied to the whole cell, mark included).
  Going into or out of a directory starts it from the left again. **Its bar** (`UsageWindow.hbar`) is on the bottom
  frame under the column (`name_x`), shown only while a name on screen is cut or the column is scrolled
  (`overflows_across`, `name_span` against `name_room`). The right bar is the list's own, shown only while there are
  more entries than rows.
- **The *Mount point* column scrolls sideways** (a departure, asked for, as the process list's *Command*). It opens
  on the mount points' ends, as `_cut_start` cuts them, so it scrolls *from the right*: `VolumeList.back` is how
  many columns are held back at each end. Left adds one, Right takes one back, and Ctrl+Left/Right move by
  `BIG_STEP` (20), up to `mount_reach` (the widest mount point on screen less `mount_room`). **Its bar**
  (`VolumesWindow.hbar`) is on the bottom frame under the column (`mount_x`, `mount_width`) and shown only while a
  mount point on screen is cut or the column is scrolled (`overflows_across`). Its value is `mount_reach - back`, so
  the thumb starts on the right, and `on_hbar_scroll` turns it back into `back`. The right bar is the list's own,
  shown only while there are more volumes than rows.
