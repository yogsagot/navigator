---
name: navigator-panels
description: The file manager window and its panels -- Manager (manager.nml/manager.py), Panel and DirEntry, view modes (Ctrl+Y simple/detailed/list), name scrolling, tagging (Insert, Space, Gray +/-/*, Select/Unselect group, SelectDialog), Ctrl+S quick search, Ctrl+H hidden files, type marks and icons, Backspace to parent, re-read keeping the cursor, Ctrl+F1/Ctrl+F2/Ctrl+P hiding sides, switch_view, active/passive panel. Use when changing how files are listed, selected or navigated.
---

# The file manager and its panels

`navigator/widgets/manager/`: the `manager/` window, `panel/` (whose `panel.py` carries `DirEntry` beside `Panel`), and
`select_dialog/`. **`manager.py` is the worked example of a converted screen**: the document holds the tree and
geometry; Python holds the keys, `active_panel` and the paths markup may not bind (`left.path`, `right.path` are seeded
after `super().__init__()` -- see `navml-markup`). `Panel` assigns `path` and lets listing, cursor and scroll follow.
`Manager.passive_panel` names the other panel. `manager.nml` holds Tab, Alt+R/Ctrl+R and F2-F8. Commands live in
`navigator/widgets/manager/commands.py`.

## Movement and reading

- Arrows/PgUp/PgDn/Home/End move, Enter descends, Ctrl+R/Alt+R re-reads. **A re-read keeps the cursor on its entry**
  (`Panel.reload`, DN's `RereadDir`); only a change of directory starts at the top.
- **A directory is read on a thread** (`scan_directory`, on `panel._SCANNER`). `_rescan`, the effect, takes the
  cursor notes (`_return_to`, `_keep`) into a `_ScanRequest`, waits `SCAN_GRACE` (50 ms) and applies inline if the
  read is done -- nearly always, so a frame never shows a half state -- else spawns `_await_scan`, which applies only
  if no later read was asked for (`_generation`). **With no application running it waits for the read**, so model
  tests' `reload()` + `settle()` still see the listing at once (and so does Navigator's first listing, before the loop
  starts). Meanwhile a re-read of the same directory keeps its rows; a new directory shows *Reading directory...*
  (`scanning`) with no rows, so nothing acts on the last directory's entries. Departure: DN blocked until the read was
  done, so keys typed meanwhile acted on the new listing; here they act on the empty one.
- `Panel.on_double_click` enters the clicked row (a directory or `..`) -- the press already moved the cursor. What needs
  the desktop (activating the other panel on a press, the wheel, console scrollback) stays on
  `Navigator.on_mouse_click`, which returns False while `app.modal` is set.
- **Backspace goes to the parent** (`GoParent(by_key=True)`, DN's `kbBack` under `fmoBackGoesBack`, `Panel.go_up`,
  cursor on the directory left) while the line is empty; Ctrl+PgUp (`_CtrlPgUp`) and Shift+Backspace whatever it holds.
- **Enter on an executable runs it**; Ctrl+Enter inserts the name (see `console-command-line`).

## View modes (Ctrl+Y, DN's `cmToggleShowMode`)

Per panel: `Panel.view_mode`, `cycle_view_mode`, and *Panel > View mode* (a menu entry DN never had).
- *simple*: name and size.
- *detailed*: Name taking the rest │ Size │ Attr `rwxr-xr-x` │ Owner `user:group` │ Date (**modification** time,
  `DD-MM-YYYY hh:mm`, since Linux has no portable creation time; the four-digit year is a departure). Owner is a departure, 5-17 cells as the longest listed
  (`DirEntry.display_owner`, names cached, a number where there is none). Owner, then Attr, then Date drop when the name
  would fall under 12 cells.
- *list*: names alone in columns, each as wide as its longest name capped at half the panel; Left/Right move a column as DN's `kbLeft`/`kbRight` did.
- A too-long name ends in `...` (`fit_text`, in cells) and starts with one while scrolled (`window_text`). In simple and
  detailed, Left/Right scroll every name a cell (`ScrollNames`, `Panel.name_scroll`, clamped, reset by directory or mode
  change) -- disabled while the command line has text, so the caret moves.
- **Drag-and-drop** (File Manager Setup's box, `panel/drag.py`): a left press on a row captures the mouse; the first
  move with the button held makes a `DragLabel` overlay (` name ` or ` N selected files `, `$30`, shadow) that follows
  it -- the tagged files if the row is tagged, else the row's own, never `..`. The release finds the target with
  `drop_target` (a panel's directory row or its directory, its own panel only on a directory row; a tree's node) and
  the panel emits `Dropped`, which its `Manager.on_dropped` turns into `copy_entries` -- Shift at the release moves,
  Confirmations' *Drag and drop* asks with the Copy dialog first, and a directory is never dropped into itself.
- **Left, Right, Home and End go to a command line with text** under File Manager Setup's *Use arrows* (on, DN's
  default), and Shift+ them to the panel; off, the other way round (`Panel.arrows_to_line`, `Panel.LINE_KEYS`;
  `Manager.enables(ScrollNames)`, `Shell.enables(CommandLineHome/End)`, and `Shell._panel_keeps` stopping a plain one
  a panel declined from reaching the line, as DN's `TSpecScroll` did).
- Non-simple modes have a heading row in *Column title* `[165]` (`Panel::heading`) and single `│` rules in the frame's
  colours (`Panel::divider` on `$panel-fg`/`$panel-bg`, a departure from DN's `[86]`), meeting the frame in the tee
  `Widget.box_joins()` gives (`┬┴`/`╤╧`) wherever title/footer does not stand.
- *Totals* and *Free space* (`navigator-settings`) are lines between the listing and the bottom frame, under the *Info
  divider*: `Panel.rows` is computed less `info_height`, so the list, scroll bar and list-mode columns shrink, and the
  column rules end in `┴` on the divider rather than on the frame. Tests that pin a listing down to the frame turn
  `free_space` off; anything painting a real directory headless pins `free_space_text` (the golden test, screenshot).
- Every mode keeps a gutter left of the name: the Nerd tier's two-cell icon, or one cell of mc's type mark
  (`DirEntry.type_mark`: `/ * @ ~ ! = - + |`). A bookmarked directory (`Panel.is_bookmarked`) gets its own glyph in
  either -- see `colours-themes-glyphs` -- and a tag still wins over both. Rows are coloured by file type -- see `colours-themes-glyphs`.

## Directory history (Alt+Backspace) and quick directories (Alt+1..9)

- **Panel > Change drive** is `ChangeDrive` (Alt+C's bookmarks box, `navigator-bookmarks`).
- **`DirHistory`** (Alt+Backspace, Panel > History of directories), DN's `cmDirHistory` -> `DirHistoryMenu`: every
  directory a panel comes to (a new listing, not a re-read or a *Find:* listing) goes first into navml's `HISTORY`
  list `directories` (`Panel._remember_directory`, DN's `AddToDirectoryHistory`) while Interface's *Track
  directories* is on (on by default, a departure; off, Alt+Backspace says DN's `dlSetDirHistory`).
  `DirHistoryDialog` (`dlgDirectoryHistory`): *Go to* (Enter, a double click), *Delete record* (stays open), Cancel.
- **Quick directories are the bookmarks** (a merge, a departure: DN's nine `DirsToChange` slots and its drive
  letters' box were two things; Navigator's bookmarks already replaced the letters with directories). Alt+1..9
  `QuickChange(slot)` go to the *N*-th bookmark with no box (none that far: nothing); Alt+Shift+1..9
  `StoreQuickDir(slot)` ask DN's `dlPromptForQDir` (*as bookmark N*) and `place_bookmark` the panel's directory at
  place *N*, moving it if already bookmarked (disabled in a listing); Alt+Shift+0 / Panel > Quick dirs `ListOfDirs`
  is the bookmarks box (`choose_bookmark`). These keys sit in `Manager.keys` (Python) because a terminal without the
  kitty protocol sends Alt with the *shifted* character -- `alt+!`..`alt+(` and `alt+)` are bound beside
  `alt+shift+N` for a US layout. A directory gone is said, not entered (`Manager._go_to`).

## Advanced filter (Alt+Del)

`AdvancedFilter`, `Manager.advanced_filter`, DN's `cmAdvFilter` -> `CM_AdvancedFilter`: `FilterDialog`
(`dlgAdvancedFilter`) over a `FilterList` (DN's `TSelectList`: Space/Ins mark and step, `+`/`-`/`*` all/none/invert,
right click) of `advfilter.extensions` -- `*` and each `*.ext` of the directory read again on a thread whatever the
mask hides (a listing's own entries in a *Find:* listing). *Show*/*Hide* take the marked masks, or the one at the
cursor, into `Panel.file_mask` through `advfilter.combine` (DN's intent without its string surgery: `*` sets the
whole mask; from show-all, *Show* narrows to the chosen and *Hide* excludes them; otherwise a chosen pattern replaces
what the mask said of it, appended so it decides) and `Panel.set_file_mask` (re-read, cursor kept). The box comes back
on the same mask after each, until *Close*.

## Columns Setup (Alt+K)

`SetupColumns`, `Manager.setup_columns`, DN's `cmSetupColumns` -> `CM_SetShowParms` (also Panel > Setup columns):
`ColumnsDialog` (`dlgDiskParms`; `dlgFindParms`'s *Path* box only in a *Find:* listing) over
**`Panel.shown_columns`**, the detailed mode's columns per panel (DN's `ShowFlags`): size, attributes, owner, date,
and `path` (`display_path`, measured like owner up to `MAX_PATH_WIDTH`, cut from its start), shown only where entries
are from elsewhere. OK shows the detailed mode with those -- none ticked is the list mode, DN's brief; *Brief* is the
list mode; *Full* every column. `DROP_ORDER` still drops columns (owner, attributes, path, date) to keep the name
`MIN_NAME_WIDTH`.

A *Find:* listing was a drive of its own in DN, with its own `ShowFlags`, so a panel holds two sets:
`Panel.columns` over a directory and `Panel.find_columns` over a listing; `shown_columns` reads and writes whichever
is showing. **Options > File Manager > Column defaults** (`ColumnDefaults`, `dlgColumnsDefaults`,
`[column_defaults]`) seeds them: `columns` when a panel is made, `find_columns` by every `show_found` (DN's
`TFindDrive.Init`). Only `columns` goes into the saved desktop.

## Hidden files (Ctrl+H)

`ToggleHidden`, `Panel.show_hidden`, `toggle_hidden`, per panel, shown by default -- our key (it took DN's *Directory
Branch*, whose caption was dropped), where DN's `ossShowHidden` was a system option. The re-read keeps the cursor; a tag
on a name it hides is dropped. *Panel > Show/hide hidden files* is **ticked** while the active panel shows them. Every
directory tree follows it (see `navigator-trees`). Ctrl+H decoding: `navkit-terminal`.

## Sorting (Alt+B)

`Panel.sort_mode`, one of `SORT_MODES` (name, extension, size, time, type, unsorted -- `PanelDefaultsData.SORT_BY`), is
DN's per-panel `SortMode`, seeded from *New Manager defaults* > *Sort by*. `order_entries` is `TFilesCollection.Compare`
and runs on the scan thread: `..` first; directories first except by *Type* (DN's *Group*: directory, executable,
archive, the `filetypes.CATEGORIES` after it, the rest -- `filetypes.GROUPS`); size and time largest/newest first;
names case-folded. *Executables first*/*Archives first* lead the files except by size and time, read at each read (not
followed). *Unsorted* is `scandir`'s order, without the two flags (DN's compare was no order there). Alt+B and *Panel >
Sort by* are `Manager.choose_sort`: `CM_SortBy`'s `PopupMenu`, centred on the panel (DN put it at the panel's top left), on the current mode, captions
`SORT_CAPTIONS` (*Type* is T~y~pe). `Panel.sort_by(mode)` re-reads keeping the cursor on its entry.

## Tagging

- **Insert tags** (`ToggleMark`, DN's `kbIns`): the entry joins `Panel.marked` (names, never `..`), cursor steps down,
  the gutter shows `√` (`+` in ASCII) in *Selected text* `[87]` / *Selected cursor* `[89]`; footer reads `N bytes in M
  selected files`. A re-read keeps tags; a change of directory drops them. **Space tags too while the command line is
  empty** (`ToggleMarkBySpace`, DN's `fmoSpaceToggle`, gated by `Shell`, which owns the line).
- **Gray `+`/`-` are *Select*/*Unselect group*** (`SelectGroup`/`UnselectGroup`, `cmPanelSelect`, on Panel's menu):
  `SelectDialog` asks for a mask -- `;`-separated shell patterns matched as a POSIX glob (`filetypes.matches`: case
  counts and `*.*` needs a dot, a departure from DN's `InMask`) -- seeded from `HISTORY["select"]` or `*`, *Except mask* ticked by Shift. Selecting passes directories over,
  unselecting does not (`Panel.select_group`).
- **Gray `*` inverts** (`InvertSelection`, `cmPanelInvertSel`, `Panel.invert_marks`): files flip, directories keep their
  tag; Ctrl+Gray `*` (`kbCtrlGAst`) flips directories too.
- **With text on the command line the Gray keys type instead** (a departure): bound in `manager.py` as `by_key=True`
  instances that `Manager.enables` disables while the line has text; the menu's instances are unaffected. **The plain
  `+`, `-`, `*` are bound the same way** (mc's rule), because VTE and PyCharm send Gray `+` as bare `+`.

## Quick search (Ctrl+S)

mc's quick search (`QuickSearch`, `Panel.quick_search`, *Panel > Quick search*): typing moves the cursor to the first
name from it that begins so (case folded, `*`/`?`, `..` never found); a character naming nothing is refused, Backspace
drops one, Ctrl+S again finds the next, wrapping. Shows as ` Search: … ` on the footer with the caret. Enter/Esc end it;
any other key ends it and does its job, as do a click, a directory change and losing the keyboard. While it runs
`edits_text` is True. Matching rules: `navml/quick_search.py`.

## Hiding sides and replacing a side

- **Ctrl+F1/Ctrl+F2 are `cmHideLeft`/`cmHideRight`** (`Manager.toggle_side`, `hidden_side`): a side (`side_view` -- the
  panel or the tree/quick view in its place) is hidden and **the window shrinks** to the other side's rectangle, so the
  console shows through (`SwitchLeft`'s `Locate`). Again restores the old rectangle (zoomed if it was, or grows by the
  share lost). Hiding the only side left shows the console (`cmShowOutput`), and the key from the console brings the
  manager back with that side alone (`cmPostHideLeft`, `Shell.show_manager_side`) -- both keys are on the application's
  table. Tab is disabled while a side is hidden; Ctrl+T/Ctrl+Q show it first.
- **Ctrl+P is `cmSwitchOther`** (`toggle_inactive_side`, on `manager.nml`'s table): the side without the keyboard; it
  never falls back to the console.
- `Manager.switch_view` is DN's `SwitchView`, shared by Ctrl+T (tree) and Ctrl+Q (quick view): `replaced`/`replacement`;
  `tree_replaces` is a computed over them.

## Find file (Alt+F7) and the *Find:* listing

`FindFile`, `Manager.find_file`, DN's `FindFile`/`FindFiles` (also Disk > Find...): `FindFileDialog` (`dlgFileFind`,
own OK / *Advanced...* / Cancel row, session-kept answers, opening on *Recursive* + *Current directory*) and
`AdvancedSearchDialog` (`dlgAdvanceSearch`: ISO dates, sizes, POSIX kinds, *Clear all*) give a `FindRequest`;
`navigator/filefind.search` walks on a thread (mask via `in_filter`, text by chunked regex, never through a symlink,
one file system for *Entire disk* / *All drives*) under `FindProgress` through `_watch_job(..., abort="Cancel
search?")`. **Results are a `FindListing` in `Panel.found`** (DN's `TFindDrive`): the panel lists its entries -- live
while searching, re-`stat`ed by `restat_found` on a re-read, gone ones dropped -- under a `..` that leads back
(`leave_found`, cursor where it was); title `Find: mask`, footer the entry's whole path. Enter / Ctrl+PgUp on `..`
leave; Enter on an entry `go_to_entry` (its directory, cursor on it); Shift+Enter `ChangeInactive` sends the other
panel there. A listing belongs to the path it was shown at: going elsewhere drops it. Nothing found: *No files found*,
the panel untouched. F7 and Compare are disabled in a listing.

**Panel > Directory Branch** (`DirBranch`, `Manager.directory_branch`, DN's `CM_Branch`/`OpenDirectory`): every
file below the panel's directory, directories left out (`FindRequest(directories=False)`), searched through the same
`_search_into` as Alt+F7 into a listing titled `Branch: <dir>`. Menu only: DN's Ctrl+H is Navigator's hidden-files
key. Disabled in a listing, as `CM_Branch` acted on a disk alone.

**Alt+V, Panel > Read file list** (`ReadFileList`, `Manager.read_file_list`, DN's `cmPanelMakeList` ->
`TFindDrive.InitList`): the list file at the cursor read on a thread by `filefind.read_list` -- a line a name (whole,
blanks included: a departure, DN cut at the first blank), relative to the panel's directory, `~` expanded, masks
globbed as a shell does (no dot-files for `*`), missing names skipped, each file once -- into a `FindListing` titled
with the list's path. Nothing there: *No files found*. Enabled on a file only.

**Entries can live elsewhere**: `DirEntry.directory` (None in a directory listing), **`DirEntry.path_in(here)`** for
its path -- never `here / entry.name` -- and **`DirEntry.key`** (name, or whole path when elsewhere) for tags,
`marked`, `_keep` and `reload(key=...)`. Untag through `Panel.untag(entries)` / `untag_paths(paths)`.

## Make list (Alt+L)

`MakeList`, `Manager.make_list`, DN's `CM_MakeList` -> `MakeListFile` (also Panel > Make list file): nothing tagged,
`SelectDialog` first; then `MakeListDialog` (`dlgMakeList`: file name, history `make_list`, opened on its last entry
or `makelist.DEFAULT_NAME` `dnlist.txt` -- DN's `DNLIST.BAT` -- and *Action*, history `command`, opened on the last
command run; *Store path names* / *Autodetermine*, kept for the session in `Manager.make_list_options`, where DN kept
them in its configuration). `navigator/makelist.py`: one line per file, or per file per `;` template (`;;` a `;`) with
`! .! !\ !/ !: !!`, values shell-quoted, a template without macros followed by the quoted file; *Autodetermine* adds
paths for files outside the list's directory and puts `!\` before a bare name macro. An existing file asks Yes /
A~p~pend / Cancel. Written files are untagged and `FileSaved` re-reads the panels showing the list's directory.

## Fast rename (Alt+F6)

`FastRename`, `Manager.fast_rename`, DN's `CM_RenameSingle`: `fast_rename.FastRenameLine`, an `InputLine` run as a
modal overlay over `Panel.name_cell()` (one cell further left, for its scroll arrow), the name all selected. Enter
renames; Up, Down, Left at the start and Right at the end rename and then are posted to the panel (DN's `PutEvent`);
Esc cancels (a departure: DN's renamed); a click outside cancels; `/` is not typed. Never `..`. A name already taken
is refused (DOS's rename refused it, POSIX's replaces). The tag follows the file; `Panel.reload(name=new)` keeps the
cursor on it; `FileSaved` re-reads the other panels.

## Panel Options (Alt+S)

`PanelSetup`, `Manager.panel_setup`, DN's `cmPanelSetup` -> `Setup` (also Panel > Setup Panel): `PanelSetupDialog`
(`dlgPanelSetup`, laid out as `FMDefaultsDialog` plus *File mask*, history `file_mask`) opens on the panel's own
values and OK is `Panel.set_options(sort, display, mask)`: one re-read keeping the cursor. **`Panel.display`** is None
while the panel follows the *New Manager defaults* live and a frozenset of `PanelDefaultsData.DISPLAY` names once set;
ask `Panel.shows(option)`, never `SETTINGS.panel_defaults` directly. **`Panel.file_mask`** (DN's `FileMask`, `*` for
all) filters files, never directories, in `scan_directory` through `filetypes.in_filter` (`InFilter`: `;` patterns,
`-` excludes, the last match decides, nothing matching is out; case counts). A mask other than `*` follows the path in the
title, `/src [*;-*.bak]` (`title_text`; the path is cut first) -- a departure: DN's panel said nothing of it. *Directory length*, *Totals* and *Free space* are stored but not drawn yet.

## Directory length (Alt+G)

`CountLength`, `Manager.count_length`, DN's `cmCountLen` (also Panel > Count directory length): the directory at the
cursor (`..` counts the one listed) and every tagged directory get the bytes beneath them, counted on a thread by
`navigator/dirlength.py` (`CountDirLen`: dot-files count, symlinks count as themselves and are never followed, unreadable
directories count as nothing) under `run_with_progress`'s *Counting directory length* box; Esc keeps what was counted.
The entry gets `size` and `counted` (DN's `Attr or $80`), its size column shows the size where `DIR` was, the tagged
total includes it, and a re-read forgets it (new entries), as DN's did. `panel_defaults.directory_length` (count every
directory at each read, `fmiDirLen`) is not written yet.

## Information panel (Ctrl+L)

`DiskInfo`, `Manager.on_disk_info`, DN's `cmDiskInfo` -> `SwitchView(dtInfo)` (also Panel > Info): `InfoPanel`
(`manager/info_panel`, Python-only, framed like the quick view, `::highlight` for DN's `~` runs) takes the passive
panel's place as the tree and quick view do. `Manager._info_follows_panel` (an effect on the active panel's path,
items and `reload_token`; not while it shows a *Find:* listing) calls `InfoPanel.show`, which reads the disk and the
machine on a thread (`navigator/diskinfo.gather`: `disk_usage`, the longest mount in `/proc/self/mounts`, a
`/dev/disk/by-label` label, `/proc/meminfo`, the resident set, `DirInfo` else `File_ID.DIZ` in any case) and keeps
the last answer up meanwhile. `diskinfo.lines` lays them out as `TDiskInfo.Draw`, each behind a `[drive_info]` box;
totals come from the listing (entries counted as `CountDirLen` counted them, bytes the files'). DN's EMS/XMS lines
are left out; its memory three are read for POSIX.

## Comparing directories (Panel menu)

`CompareDir`, `Manager.compare_directories`, DN's `cmCompareDir` -> `CM_CompareDirs`, from Panel > Compare directories
only -- DN's Ctrl+C is left unbound, kept for a clipboard copy still to be designed:
`CompareDialog` (`dlgCompareDirs`: size, time, attributes, contents; Select/Unselect; opens on size+time+Select every
time, as `DT` was reset) then `navigator/dircompare.py` on each panel against the other. A file matches one of the
same name (exact case) passing every check: same size, **this one no newer** (to the second), same permission bits,
same bytes. *Select* tags exactly what has no match (directories never), *Unselect* only untags it -- so Select tags
what a copy across would bring up to date. Only *contents* reads the disk, on a thread under *Comparing files*; Esc
leaves the tags. A panel that moved meanwhile is left alone.

## Swapping panels (Ctrl+U)

`SwapPanels`, `Manager.swap_panels`, DN's `cmSwapPanels` (also Manager > Swap panels): the two panel objects change
places in the `panels` row, whole, and **`Manager.left`/`right` are swapped with them** -- they name sides, not panels,
so Alt+F1, Ctrl+F1 and the rest act on whatever is on that side now. A tree or quick view goes beside the panel it
stands in for; the keyboard stays with its panel. A hidden side is shown first (DN's code ended that way too). The row
is re-`arrange()`d by hand: reordering `children` in place is not something its layout follows.

## Read when

No DESIGN reference of its own; panel-related library notes are in
`.claude/skills/navml-library/reference/widget-library.md` (*What the library took from `Panel`*).
