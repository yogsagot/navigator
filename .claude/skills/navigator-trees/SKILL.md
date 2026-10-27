---
name: navigator-trees
description: Directory trees -- navml's TreeView/TreeNode, Navigator's DirectoryTree (Ctrl+T in the passive panel), Alt+T Choose Directory (TTreeDialog, change_dir_dialog), Disk > Directory tree window (TTreeWindow, tree_window), Disk > Volumes (VolumesWindow, VolumeList, navigator/lib/system/volumes.py), tree quick search (Ctrl+S, path-based), and hidden-file handling in trees. Use when working on any tree view.
---

# Trees

Slots `[94-101]`, `[104-110]`.

- The library's `TreeView` is a `ListViewer` of flattened, lazily loaded `TreeNode`s, drawn as `TTreeView.Draw` draws
  them. Navigator's `DirectoryTree` (`navigator/widgets/tree/`) is what **Ctrl+T** puts in the passive panel's place
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
  (`is_real`: a `/dev` device not a loop, a network or user FUSE mount); the *Show all mounts* box under the list (or
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
- **Nothing a tree paints waits on the disk.** `TreeView.probe_in_background` (on for `DirectoryTree`) asks an
  unopened node's probe on a thread (`navml.background`), drawing `[+]` until it answers and refreshing then; the
  info band's `count_files` runs on its own pool when the cursor stops, the line blank until it is in. Without a
  running application both answer at once, as before. On the disk, opening a branch (`children()`) and `show_path`
  still read on the loop: the panel has just listed the same directories, and a branch the user opens is one at a
  time. **On another drive** (`navigator-drives`) every read is a round trip: the tree is rooted on that drive
  (`DirectoryTree.use_drive_of`, `directory_root(at=)`), `TreeView.load_in_background` reads an opened branch on a
  thread (`children_of`: open and empty until it lands), and `show_elsewhere` walks the path on a thread and opens
  the branches when it is in. Alt+T's box sets the same on its plain `TreeView` (`ChangeDirDialog._show`).
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

## Read when

| Reference | Read when |
|---|---|
| `reference/trees.md` | the full design: TreeView, lazy loading, quick search, the dialogs, the tree window choice |
