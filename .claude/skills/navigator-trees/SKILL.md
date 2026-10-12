---
name: navigator-trees
description: Directory trees -- navml's TreeView/TreeNode, Navigator's DirectoryTree (Ctrl+T in the passive panel), Alt+T Choose Directory (TTreeDialog, change_dir_dialog), Disk > Directory tree window (TTreeWindow, tree_window), Disk > Volumes (VolumesWindow, VolumeList, navigator/volumes.py), tree quick search (Ctrl+S, path-based), and hidden-file handling in trees. Use when working on any tree view.
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
  column titles in its `header` band (Name, Type, Mount point, Free, Size; sizes by `sysinfo.size_text`). The mounts
  are `navigator/volumes.py`'s `gather()` over `/proc/self/mounts`, read on a thread (`Background`) from `mounted()`,
  never `__init__` -- a stale network mount holds `statvfs`, and one that raises is skipped. Only *real* volumes show
  (`is_real`: a `/dev` device not a loop, a network or user FUSE mount); the *Show all mounts* box under the list (or
  Ctrl+H, which ticks it) shows the kernel's own too, without re-reading -- an effect on the box's `value`, which
  peeks the list so a cursor move does not wake it. Enter's `ChosenEvent` carries the `Volume` up to
  `Shell.on_chosen`, which sends the active panel to its mount point, and the window stays; *Go* (default, Alt+G) does
  the same and closes it; *Close* closes. Tab walks the controls and Alt+letter takes one, as the calculator
  window does. The window is kept by a saved desktop (`kind="volumes"`, with the box).
- **Nothing a tree paints waits on the disk.** `TreeView.probe_in_background` (on for `DirectoryTree`) asks an
  unopened node's probe on a thread (`navml.background`), drawing `[+]` until it answers and refreshing then; the
  info band's `count_files` runs on its own pool when the cursor stops, the line blank until it is in. Without a
  running application both answer at once, as before. Opening a branch (`children()`) and `show_path` still read on the
  loop: the panel has just listed the same directories, and a branch the user opens is one at a time.
- **Hidden files**: Ctrl+T's tree tracks the active panel's `show_hidden` (`DirectoryTree.set_show_hidden`); Alt+T and
  the tree window take it when opened (`hidden=`). Nodes carry it as `TreeNode.show_hidden`, and `show_path` grafts in a
  dot-directory the path goes through, so a panel inside `~/.config` still has a tree that finds it.

## Read when

| Reference | Read when |
|---|---|
| `reference/trees.md` | the full design: TreeView, lazy loading, quick search, the dialogs, the tree window choice |
