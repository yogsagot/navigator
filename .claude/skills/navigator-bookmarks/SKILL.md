---
name: navigator-bookmarks
description: Bookmarks -- Alt+F1/Alt+F2 (cmChangeLeft/cmChangeRight) and Alt+C (cmChangeDrive) opening a box of bookmarked directories where DOS Navigator's SelectDrive listed drive letters; navigator/bookmarks.py (first set, seeding once, add/remove), the Bookmark and Marker models, navml's PopupMenu, Manager.choose_bookmark/bring_side/bookmark_menu, and System > Bookmarks left/right. Use when changing bookmarks or the box they are chosen from.
---

# Bookmarks

**A departure**: DN's `cmChangeLeft`/`cmChangeRight` (Alt+F1/Alt+F2) and the panel's `cmChangeDrive` (Alt+C) ran
`SelectDrive` -- a box of drive letters centred over the panel, one row under its top edge, the panel's drive
selected. POSIX has no drives, so the same box lists bookmarked directories. Its last entry is *Add this folder*, or
*Remove this folder* when the panel's directory is bookmarked already. The menu captions are *Bookmarks left/right*.

## Pieces

- **`navigator/bookmarks.py`**: `default_bookmarks()` (pure: takes home, config home, `/mnt`, `/media`, user),
  `seed_bookmarks()`, `bookmarks()`, `find_bookmark`/`add_bookmark`/`remove_bookmark`/`move_bookmark`/`label_bookmark`, `mounted_places()`. A path is stored absolute, case
  and all (`key_of`, as the file histories do). Added ones go last (`seq`).
- **The first set**: `~`; the desktop folders that exist, named by `$XDG_CONFIG_HOME/user-dirs.dirs` when it names them
  (localised `Dokumente`), else `Desktop Documents Downloads Music Pictures Videos`; a `user-dirs.dirs` entry pointing at
  `$HOME` itself means "none" and is skipped; every directory under `/mnt`; under `/media`, the children of
  `/media/$USER` (udisks' mounts) and any other entry as it is; the children of `/run/media/$USER` (udisks on
  Fedora/Arch) -- `_mount_directories`.
- **Seeded once**, from `main()` right after `open_database()`: a `Marker` row named `"bookmarks seeded"` records it, so
  an emptied list stays empty. Tests never seed (no `main()`); they call `add_bookmark` directly.
- **Models**: `navigator/models/bookmark/` (`bookmarks` table: `path` unique, `seq`, `label`) and `navigator/models/marker/`
  (`markers` table: a `name` whose presence is the fact). `Marker` is generic -- reuse it for the next do-once.
- **The box** is navml's `PopupMenu` (`navml/widgets/menu/popup_menu/`): Turbo Vision's `TMenuPopup`, one `MenuBox`
  on a full-screen modal layer, run like a dialog -- `await PopupMenu(menu, x, y, current=, behind=).execute(app)`
  returns the `MenuItem` chosen or None, so it is **spawned, never awaited in a handler**. Its `PopupBox` treats an
  item with no command as a choice (enabled unless `disabled`), unlike a bar's box, which greys it as unwritten.
- **`Manager`**: `on_change_left/right` call `bring_side(side)` first -- a side hidden by Ctrl+F1/F2 is shown, and the
  tree or quick view standing in its place gives way (`switch_view`) -- then spawn `choose_bookmark(panel)`.
  `on_change_drive` uses `active_panel`. `bookmark_menu(rows, bookmarked)` builds the entries: keys `1`-`9`, `0`, then
  letters skipping `a`/`r` (`BOOKMARK_KEYS`); the home directory shown as `~` and tildes escaped (`escape_caption`);
  a directory that no longer exists greyed.
- **Choosing** sets `panel.path` and focuses the panel. *Add* adds and closes; *Remove* removes and opens the box again.
- **Reordering**: Ctrl+Up/Ctrl+Down (`MOVE_BOOKMARK_KEYS`) move the selected bookmark one place -- `move_bookmark`
  swaps its `seq` with its neighbour's -- and the box opens again with it still selected. A greyed one moves too; on
  *Add*/*Remove* the keys do nothing. It works through `PopupMenu(keys=...)`: such a key closes the box on the selected
  entry, enabled or not, with `pressed` naming the key and `selected` its index.
- **Labels**: F2 (`LABEL_BOOKMARK_KEY`) opens `BookmarkLabelDialog` (`navigator/widgets/manager/bookmark_label_dialog/`)
  on the selected bookmark's label, and the box comes back. OK with an empty line clears it; Cancel answers None, which
  is why this is not `MkdirDialog` (whose empty OK is None too). A labelled entry's caption is the label, and its path
  goes in `MenuItem.key`, the column a menu shows keys in.
- **Mounts are read each time the box opens**: `mounted_places()` takes the direct children of `/mnt`, `/media`,
  `/media/$USER` and `/run/media/$USER` from `/proc/self/mounts` (octal escapes undone; deeper mounts ignored), or
  without `/proc` falls back to `_mount_directories`. Those not bookmarked follow the bookmarks after a line, keys
  continuing, stored nowhere -- an unplugged drive just goes. They are only places to go: Del, F2 and Ctrl+Up/Down
  pass them by (they act only on `selected < len(rows)`), and *Add this folder* from one bookmarks it.
  `choose_bookmark` maps an entry to its path through `places`, parallel to the entries. **App tests must pin
  `navigator.bookmarks.mounted_places`** (the `places` fixture does), or the machine's own drives join the box.
- **The panels mark bookmarked directories** in the gutter (`Panel.is_bookmarked`, glyphs in
  `colours-themes-glyphs`), asking `bookmarked_paths()` for every directory row it paints. That set is cached with the
  connection it was read from (so a test's fresh database never sees another's), cleared by add/remove/seed and
  refreshed by `bookmarks()`, which the box calls -- another Navigator's change shows once this one's box opens. Panel
  paths are resolved, so a bookmark through a symlinked path (`$HOME` via a link) is not marked.
- **Del** (`DELETE_BOOKMARK_KEY`) removes the selected bookmark, unasked as *Remove this folder* is, and the box opens
  again on the entry that took its place (the one before, for the last). On *Add*/*Remove* it does nothing.

## Gotchas

- `choose_bookmark` calls `self.panels.arrange()` before placing the box: the layout normally settles in the batch's
  effects, and a side just brought back must be where it will be before the box is centred on it.
- More bookmarks than screen rows: `PopupMenu` cuts the box to the screen and it scrolls (`navml-windows-menus`),
  PgUp/PgDn and the wheel included.
- Alt+F1/F2 are Manager keys, so from the console (Ctrl+O) the menu entries are greyed; DN's user screen behaviour for
  them was not ported.

## DN's quick directories

Alt+1..9 jump to bookmark 1..9 without the box, Alt+Shift+1..9 put the panel's directory at that place
(`bookmarks.place_bookmark`, moving or inserting and renumbering `seq`), Alt+Shift+0 opens the box: DN's
`DirsToChange`, merged into this list rather than kept as a second one (`navigator-panels`).
