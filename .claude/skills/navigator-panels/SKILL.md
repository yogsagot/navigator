---
name: navigator-panels
description: The file manager window and its panels -- Manager (manager.nml/manager.py), Panel and DirEntry, view modes (Ctrl+Y simple/detailed/list), name scrolling, tagging (Insert, Space, Gray +/-/*, Select/Unselect group, SelectDialog), Ctrl+S quick search, Ctrl+H hidden files, type marks and icons, Backspace to parent, re-read keeping the cursor, Ctrl+F1/Ctrl+F2/Ctrl+P hiding sides, the draggable divider between the sides (Alt+Left/Alt+Right), switch_view, active/passive panel. Use when changing how files are listed, selected or navigated.
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
  A departure: at the root, where DN did nothing, all three move the cursor to the top, as Home does.
  A departure: the Backspace held or tapped to clear the line does not go on climbing once it is empty --
  `Manager.on_go_parent` swallows it while `CommandLine.holds_backspace()` says it is within `BACKSPACE_RUN` (0.6 s)
  of the last one the line took or swallowed; each swallowed one restarts the wait, so a held key never gets through.
- **Enter on an executable runs it**; Ctrl+Enter inserts the name (see `console-command-line`).

## Auto refresh (`[file_manager] auto_refresh`)

- **A panel watches the directory it shows** and re-reads it when that changes on disk. It is on by default, and is the
  ninth Behavior item in Options > File Manager > Setup. **A departure**: DN re-read a panel only on the `cmRereadDir`
  that whatever changed the directory broadcast (`RereadDirectory`), so another program's file waited for Ctrl+R.
- `navigator/lib/system/dirwatch.py` puts one `watchdog` observer behind the whole process, with one **non-recursive**
  watch per directory however many panels show it (refcounted; the last `Watch.cancel()` unschedules). Only created,
  deleted, moved and modified pass; watchdog's opened/closed are dropped, or F3 opening a file would re-read its panel.
  A directory that cannot be watched (the inotify limit, a gone directory, a filesystem with no events) gets an inert
  `Watch`, and its panel is what it was before.
- **The notify runs on the observer's thread**, and only calls `Application.call_from_thread(panel._changed_on_disk)`,
  which queues on the loop and wakes it, and drops the call while no loop runs. **Only the first change after a
  re-read is handed over** (`Panel._heard`, set on the thread, cleared by `_refresh_now` just before it reads): a copy
  into the directory shown is a change per block written, and handing each one to the loop cost a quarter of a core. `_changed_on_disk` arms one
  `call_later(REFRESH_DELAY)` (0.3 s), so a burst is a single re-read. `_refresh_now` calls `reload()`, which keeps the
  cursor, tags and quick search, and it waits again while a slow read is `_pending`.
- `Panel._watch_directory` is an effect on `path`, `found` and the setting: turning the setting off, or showing a
  *Find:* listing, stops the watch. With no application it watches nothing, so model tests stay deterministic.
  `Panel.unmounting()` cancels the watch, `Navigator.on_stop` calls `dirwatch.shutdown()`, and so does an autouse
  fixture in `tests/conftest.py`, because each watch holds an inotify instance and a user gets 128 of them.

## Git status (`[file_manager] git_status`)

A departure (asked for): DN knew no git. In a work tree, each row ends in a letter, and the title names the branch.
- **The letters** are `M` modified, `A` added, `D` deleted, `R` renamed or copied, `?` untracked, `!` ignored and `U`
  unmerged. A directory takes the strongest letter beneath it (`gitstatus.PRIORITY`, `U M D R A ?`). An ignored file
  inside says nothing of its directory.
- **Where the letter goes**: it sits in the middle of `Panel.GIT_CELLS` (3: a blank, the letter, a blank keeping it
  off the column divider) at the end of the name's cells, in every view mode (`_draw_name`). `name_room` and `list_columns` give those cells up while `git` is
  set.
- **Colours**: the letter is coloured by `Panel::git.<class>` (`gitstatus.CLASSES`), the `git-*` `DERIVED` entries.
  Under the cursor bar it takes the row's own colours.
- **The title** reads `path [mask]  branch ↑N↓M` (`git_text`; `^`/`v` at the ASCII tier). A detached HEAD shows a
  7-character commit. The branch is dropped before the path would be cut under `MIN_NAME_WIDTH` cells.
- **How it is read**: `navigator/lib/system/gitstatus.py`'s `read` runs `git rev-parse` and then
  `git status --porcelain=v2 -z --branch --ignored=matching -- .` on `_SCANNER`. The result is `Panel.git`, a
  `GitState`, or None.
  - It runs with **`GIT_OPTIONAL_LOCKS=0`**, so a read never writes the index. Without it, a read would take the
    user's `index.lock`, and its own write would set off the `.git` watch below, for ever.
- **When it is read**:
  - **After a listing lands, never inside the scan**: `_follow_git` is an effect on `items`, `error`, `found`,
    `location`, `scanning` and the setting. This way a slow `git status` never holds up a listing.
  - It runs only for the local disk outside an archive, and never for a *Find:* listing. With no application it
    reads nothing; before the loop runs it waits for the read, as the first listing does.
  - A change of directory clears `git` in `_apply`, so the last directory's letters never land on new names.
- **The `.git` watch**: `git add`/`commit`/`checkout` change the git directory and not the directory shown.
  `_watch_git` therefore watches `GitState.git_dir` (non-recursive: index and HEAD) under *Auto refresh panels*, and
  reads git again after `REFRESH_DELAY`. It uses the same one-shot hop to the loop as the directory watch.
  An edit in a subdirectory the panel does not show is heard only by Ctrl+R or the next listing.
- **The setting** is File Manager Setup's sixth *Display* box. The README screenshot turns it off.

## View modes (Ctrl+Y, DN's `cmToggleShowMode`)

Per panel: `Panel.view_mode`, `cycle_view_mode`, and *Panel > View mode* (a menu entry DN never had).
- *simple*: name and size.
- *detailed*: Name taking the rest │ Size │ Attr `rwxr-xr-x` │ Owner `user:group` │ Date (**modification** time,
  `DD-MM-YYYY hh:mm`, since Linux has no portable creation time; the four-digit year is a departure). Owner is a departure, 5-17 cells as the longest listed
  (`DirEntry.display_owner`, names cached, a number where there is none). Owner, then Attr, then Date drop when the name
  would fall under 12 cells.
- *list*: names alone in columns, each as wide as its longest name capped at half the panel; Left/Right move a column as DN's `kbLeft`/`kbRight` did.
- A too-long name ends in `…` (`fit_text`, in cells) and starts with one while scrolled (`window_text`); `...` at the
  ASCII tier (`Panel.ellipsis`, `glyphs.ellipsis`), and the title, footer path and path column cut their start with the
  same marker. In simple and detailed, Left/Right scroll every name a cell (`ScrollNames`, `Panel.name_scroll`, clamped, reset by directory or mode
  change) -- disabled while the command line has text, so the caret moves.
- **Drag-and-drop** (File Manager Setup's box, **on by default** -- a departure, DN's `fmoDragAndDrop` was off;
  `panel/drag.py`): a left press on a row captures the mouse; the first
  move with the button held makes a `DragLabel` overlay (` name ` or ` N selected files `, `$30`, shadow) that follows
  it -- the tagged files if the row is tagged, else the row's own, never `..`. The release finds the target with
  `drop_target` (a panel's directory row or its directory, its own panel only on a directory row; a tree's node) and
  the panel emits `Dropped` (with the drop's screen `x`, `y`). `Manager.on_dropped` puts up `_drop_menu`, a
  `PopupMenu` at the drop titled with the drag label and with `To <directory>` in its bottom frame (`footer`, home as `~` by `title.tilde`, the
  path's start cut to keep the box on the screen): *Copy here* / *Move here* / *Symlink here* / *Relative symlink
  here* / *Cancel*, into `copy_entries` or `link_entries` (Shift+F5's body, shared). A departure: DN copied at once
  and Shift moved; here Shift only opens the menu on *Move*. Confirmations' *Drag and drop* puts up the Copy or Create
  symlink dialog after the choice (`LinkDialog(relative=...)` ticks its box), and a directory is never dropped into
  itself.
- **The trash can** (≡ > Trashcan on/off, `ToggleTrashCan`, DN's `TTrashCan`/`cmHideShowTools`, ticked while shown):
  `widgets/shell/trash_can.py`, a `Shell` child over the desktop bound to the desktop's bottom right corner by
  `gap_x`/`gap_y` (so a resize keeps it there, `gfGrowAll`), dragged by the mouse, `TrashCan:dragging` in the frame
  icons' colour. A drop on it is `Dropped(trash=True)` (`drag.TRASH`): `Manager._drop_on_trash` asks a Yes/No
  *Do you wish to delete NAME?* (a departure: DN erased at once), then `erase_entries(dialog=False, quiet=...)` --
  *quiet* (Yes to non-empty and read-only) unless Confirmations' *Drag and drop* is ticked, as DN set
  `Confirms := 0`. Shown and placed are saved with the desktop (`desktop_state`'s `trash`). DN's double click
  ran the *Reanimator* undelete, which has nothing to do here.
- **Left, Right, Home and End go to a command line with text** under File Manager Setup's *Use arrows* (on, DN's
  default), and Shift+ them to the panel; off, the other way round (`Panel.arrows_to_line`, `Panel.LINE_KEYS`;
  `Manager.enables(ScrollNames)`, `Shell.enables(CommandLineHome/End)`, and `Shell._panel_keeps` stopping a plain one
  a panel declined from reaching the line, as DN's `TSpecScroll` did).
- Non-simple modes have a heading row in *Column title* `[165]` (`Panel::heading`) and single `│` rules in the frame's
  colours (`Panel::divider` on `$panel-fg`/`$panel-bg`, a departure from DN's `[86]`), meeting the frame in the tee
  `Widget.box_joins()` gives (`┬┴`/`╤╧`) wherever title/footer does not stand.
- **A column title's tooltip** is `Panel.column_description(key)` and the order a click sorts by next
  (`next_column_sort`, which `sort_by_column` applies, so the tooltip cannot promise another). A new column needs a
  description there.
- **An info line's tooltip** says whole what the line cut or rounded (`info_line_at`, `_info_tooltip`): *Current file*
  the name, every byte, the date and a link's target; the line under it the whole directory/origin/target; *Free
  space* the exact bytes; any other its text while wider than the panel. A new kind of line decides its own there.
- **A row's tooltip** (`_row_tooltip_at`): over the name, the whole name while cut or scrolled (`_name_room`, the
  room `_draw_name` gives it, in every mode) and a link's `-> target`; over the detailed mode's owner and path, their
  whole text while cut; nothing over `..`, sizes, dates or attributes.
- **The title's tooltip** (`_title_tooltip`, over the title's own cells): the whole path where its start was cut,
  the mask in words with Alt+Del's key, the git branch (or detached HEAD) and ahead/behind spelled out -- even where
  a narrow title dropped the branch. A title that says it all has none.
- **The divider's tooltip** is `Manager.tooltip_at`, over exactly what `divider_hit` grabs: drag, Alt+Left/Right (read
  off the key table) and the double click that evens the split. A panel's frame has none, so the lookup climbs to it.
- **Shift+F11 on a panel** shows its cursor row's tooltip (`Panel.tooltip_anchor`: the name, the list mode's
  column too). A greyed panel command says why: `Manager.refusal`, which `enables` is derived from -- give a new
  veto a reason there, not a bare `False`.
- **Miller columns inherit both** -- a `MillerColumn` is a `Panel`: a row's whole name while cut (`_name_room`
  reads the column's own `name_width`), and the title, its directory's name alone, gives the whole path. No code of
  their own; `tests/test_miller.py` holds it.
- **The info lines are DN's `TInfoView`**, between the listing and the bottom frame under the *Info divider*, in its
  order, each behind its *Display* box (`Panel.info_lines`, `(text, part)`: the computed `_info_lines` with the
  current file's text filled in as it is read, because the gutter it follows is not reactive):
  - *Current file* (`::current-file`, `[119]`): **laid out on `detail_columns` in every mode** -- the columns *Columns
    Setup* (Alt+K) shows, at their places and widths, a blank where each divider stands, the name past the rows'
    gutter. DN's `GetDown` was always name, size, date, time; following the columns is Navigator's. The size is
    `DirEntry.info_size` (every digit, or `UP--DIR`/`SUB-DIR`), right-aligned on its column's edge and taking cells
    from the name where wider. Drawn as it is, never split on `~` (`PLAIN_INFO`).
  - a second line under it: a *Find:* entry's directory (DN's find drive) unless the path column shows it, or
    `-> target` on a symlink under `[file_manager] link_line` (Navigator's; File Manager Setup's *Display* boxes). It is **kept while the listing could need it** -- always on a *Find:*
    listing, while the listing holds a symlink otherwise -- so the listing never changes height as the cursor moves.
  - *Selected files* (`::selected-files`, `[120]`/`[121]`): `No files selected`, or `~X bytes in N~ selected files`.
    With files tagged and the box off, the selection takes *Current file*'s line, as DN's `Goto 1` did.
  - *Totals* and *Free space* (`navigator-settings`), centred as the selection is.
  The bottom frame carries only the quick search now. `Panel.rows` is computed less `info_height`, so the list, scroll
  bar and list-mode columns shrink, and the column rules end in `┴` on the divider rather than on the frame. Tests
  that pin a listing down to the frame turn `free_space`, `current_file` and `selected_files` off; anything painting a
  real directory headless pins `free_space_of` and the date and time (the golden test, screenshot). An entry's size
  changing where it stands (Alt+G) bumps `Panel.sizes_token`: the same list of the same entries is no change to
  `items`.
  **Alt+I hides that footer** -- divider and lines -- per panel (`ToggleInfoLines`, `Panel.show_info`/`toggle_info`,
  *Panel > Show/hide footer*, ticked while shown, kept with the desktop); a departure, DN had only the *Display* boxes.
  The command has no `title`, so the Alt key bar keeps *Z Zoom*.
- **The option strip** (a departure, as the editor's and viewer's): each panel's bottom frame carries navml's
  `OptionStrip` (`Panel.options`, added in Python in `Panel.__init__` -- Panel has no markup), right-aligned 3 cells
  before the corner: `[Hid]` (Ctrl+H) and `[Info]` (Alt+I) lit while on, then the view mode and the order
  (`Name↑`), never lit, a click doing Ctrl+Y / Alt+B (`panel/option_items.py`'s `panel_items`; word / symbol / Nerd
  icon by `option_label`). **Lit is read off the strip's own panel** (`lit=`), not `Manager.checks`, which answers
  for the active panel. `PanelOptionStrip` focuses its panel on a press before running the command, so Manager's
  handlers -- which act on `active_panel` -- switch the panel clicked. A quick search's centred label wins: the strip's
  `room` ends before it (`Panel._options_room`) and items drop from the last. File Manager Setup's *Option flags*
  (`[file_manager] show_options`) shows it. The golden desktop fixture and the README screenshot carry it.
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

**Hidden files, the footer, the view mode and the order are remembered per side** (a departure): the effect
`Manager._keep_panel_state` writes a side to the `PanelState` model (one row a side,
`navigator/lib/config/panel_state.py`'s `remember`) whenever one of the five changes there -- by key, menu, Alt+S, a
column title or Ctrl+U -- its first run only noting them, so opening a file manager writes nothing. `Manager.__init__`
seeds both panels of every new file manager from it (`recall`). A side with no row follows System Setup's *Show hidden
files*, shows its footer and takes *New Manager defaults*' view mode and order; a restored desktop is seeded after, so
it wins.

## Sorting (Alt+B)

`Panel.sort_mode`, one of `SORT_MODES` (name, extension, size, time, attributes, owner, type, unsorted -- `PanelDefaultsData.SORT_BY`), is
DN's per-panel `SortMode`, seeded from *New Manager defaults* > *Sort by*. `order_entries` is `TFilesCollection.Compare`
and runs on the scan thread: `..` first; directories first except by *Type* (DN's *Group*: directory, executable,
archive, the `filetypes.CATEGORIES` after it, the rest -- `filetypes.GROUPS`); size and time largest/newest first;
*Attributes* by the permission bits (`S_IMODE`, fewest first) and *Owner* by `display_owner` case-folded, both
then name (departures: DN sorted by neither);
names case-folded. *Executables first*/*Archives first* lead the files except by size, time, attributes and owner, read at each read (not
followed). *Unsorted* is `scandir`'s order, without the two flags (DN's compare was no order there). Alt+B and *Panel >
Sort by* are `Manager.choose_sort`: `CM_SortBy`'s `PopupMenu`, centred on the panel (DN put it at the panel's top left), on the current order, captions
`sort_captions()` (*Type* is T~y~pe). **Each mode is in it twice** (`sort_orders()`: its own direction, then reversed;
*Unsorted* once), the own direction plain and the reversed one with its arrow in the key column
(`Panel.direction_arrow`, as Alt+S's captions with *Reverse order* ticked), the reversed caption without its hot key
(`sort_order_captions()`) so the letter picks the own direction, and the panel's order ticked (`MenuItem.ticked`). *Sort by*'s radio group in Alt+S and *New Manager defaults* is three rows of
three columns, so the Russian and Latvian captions fit 52 columns. `Panel.sort_by(mode, reverse=False)` re-reads keeping the cursor on its entry.

**Clicking a column title sorts by it** (a departure: DN had no descending order nor clickable titles):
`Panel.heading_at` finds the column on the heading row and `sort_by_column` steps through its `COLUMN_SORTS` modes,
each up then reversed (`Panel.sort_reverse`), wrapping: Name is name ↑ → name ↓ → extension ↑ → extension ↓ (there
being no extension column), Size, Attr, Owner and Date (time) just flip; the others sort nothing. From another column's order a
click starts at the first step.
`order_entries(reverse=True)` turns only the order *within* each group: `..`, directories before files and the
*Executables/Archives first* flags stay put; *Unsorted* ignores it. The sorted column's title ends in `↑` (ascending)
or `↓` (`^`/`v` at the ASCII tier), Name's with a `.` before it while the extension sorts (`Name.↑`) -- `Panel.sort_arrow`, with `SORT_ASCENDS` saying size and time run descending
unreversed. Alt+S's *Panel Options* has *Reverse order* (`PanelSetupDialog.reverse`, on the *Sort by* caption's row): ticked,
each order's caption ends in the arrow of the way it then runs, unticked they are plain (`sort_radio_captions()`,
bound to that box); *New Manager defaults*
has the same box and arrows, as `[panel_defaults] sort_reverse`, which seeds `Panel.sort_reverse` with `sort_by`; both
dialogs share `sort_radio_captions()` (manager.py) and are 56 columns, for those arrows in Russian and Latvian.
`set_options` takes the direction with the mode; `direction_arrow()` and `SORT_ASCENDS` are module-level in panel.py. `sort_reverse` is kept with the desktop.

## Tagging

- **Insert tags** (`ToggleMark`, DN's `kbIns`): the entry joins `Panel.marked` (names, never `..`), cursor steps down,
  the gutter shows `√` (`+` in ASCII) in *Selected text* `[87]` / *Selected cursor* `[89]`; the *Selected files* info line
  reads `N bytes in M selected files`. A re-read keeps tags; a change of directory drops them. **Space tags too while the command line is
  empty** (`ToggleMarkBySpace`, DN's `fmoSpaceToggle`, gated by `Shell`, which owns the line).
- **Gray `+`/`-` are *Select*/*Unselect group*** (`SelectGroup`/`UnselectGroup`, `cmPanelSelect`, on Panel's menu):
  `SelectDialog` asks for a mask -- `;`-separated shell patterns matched as a POSIX glob (`filetypes.matches`: case
  counts and `*.*` needs a dot, a departure from DN's `InMask`) -- seeded from `HISTORY["select"]` or `*`, *Except mask* ticked by Shift. Selecting passes directories over,
  unselecting does not (`Panel.select_group`).
- **Gray `*` inverts** (`InvertSelection`, `cmPanelInvertSel`, `Panel.invert_marks`): files flip, directories keep their
  tag; Ctrl+Gray `*` (`kbCtrlGAst`) flips directories too -- bound as `ctrl+*` as well, which is how a terminal
  may report it with Num Lock on.
- **Ctrl+A selects all** (`SelectAll`, `Panel.select_all`, Panel > *Select all files* and the context menu, no hot key --
  only `j` is free there): every file and directory, never `..`, whatever was tagged. A departure, asked for: DN had
  none, and Ctrl+Gray `*` inverts (untagging what was tagged) and needs a terminal that reports the keypad.
- **With text on the command line the Gray keys type instead** (a departure): bound in `manager.py` as `by_key=True`
  instances that `Manager.enables` disables while the line has text; the menu's instances are unaffected. **The plain
  `+`, `-`, `*` are bound the same way** (mc's rule), because VTE and PyCharm send Gray `+` as bare `+`.

- **The right button** follows File Manager Setup's *Right button* (`[file_manager] right_button`, a departure).
  `menu`, the default, opens the panel's context menu (`Panel.context_menu`, built from DN's `GetSelection`). `select`
  is DN's own (`FLPANELX.PAS`): a press toggles the row's tag and captures the mouse, and a drag gives every row it
  passes the same tag, scrolling past either end (`Panel._right_marking`). The Menu key and Shift+F10 open the menu
  under either setting.

## Copy, cut and paste through the clipboard (Ctrl+C/Ctrl+X/Ctrl+V)

A departure, asked for -- only Ctrl+Ins is DN's (`FLPANELX.PAS` `_CtrlIns`, `cmPutInClipboard`: the names, nothing
kept). DN's panel Ctrl+Del (take entries off the listing) was never ported, so it is *cut* here.

- **Ctrl+C/Ctrl+Ins** (`PutInClipboard`) and **Ctrl+X/Ctrl+Del** (`CutToClipboard`) put the selection's full paths on
  the clipboard, one a line (`Manager.clip_files`), and keep the entries in the app-wide
  `navigator.lib.file_ops.clip.CLIP` (where they were listed, `here`, and `move`). Tags stay.
  **Ctrl+V/Shift+Ins** (`PasteFromClipboard`) runs F5's or F6's dialog on them into the active panel
  (`Manager.paste_files`, see `navigator-file-ops`). **Esc** (`ClearClipboard`) forgets them.
- **All four are `by_key=True` and step aside while the command line has text** (the `fmoDelErase` rule), so the line
  keeps copy/paste, and Ctrl+X still walks the history (a recall always puts text on the line). Paste and Esc are
  disabled with no clip, so Shift+Ins pastes text and Esc does what it did.
- **Any other copy forgets the clip** (`Navigator.copy_to_clipboard` compares with `CLIP.text`), so the next paste is
  that text; a paste that moved forgets it too, a copy can be pasted again.
- **The cue**: rows get `clip-cut` (dim) / `clip-copy` (italic) classes, after `.marked` in `navigator.nss`, the cursor
  bar keeping its colours; the gutter shows `Panel.CLIP_MARKS` per glyph tier (`✂`/`❐`, nerd `md-content_cut/copy`,
  ASCII `x`/`c`) below a tag's sign; every panel's info lines add *Clipboard: N files to move/copy*. The context menu
  offers the three.

## Quick search (Ctrl+S)

mc's quick search (`QuickSearch`, `Panel.quick_search`, *Panel > Quick search*): typing moves the cursor to the first
name from it that begins so (case folded, `*`/`?`, `..` never found); a character naming nothing is refused, Backspace
drops one, Ctrl+S again finds the next, wrapping. Shows as ` Search: … ` on the footer with the caret; with text
typed the key bar leads with *Ctrl+S Next* (`Panel.key_hints`; a departure, asked for). Esc ends it;
any other key ends it and does its job -- Enter descends into (or runs) what was found in one press -- as do a click, a
directory change and losing the keyboard. While it runs `edits_text` is True. Matching rules: `navml/quick_search.py`.

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
`navigator/lib/file_ops/filefind.py`'s `search` walks on a thread (mask via `in_filter`, text by chunked regex, never through a symlink,
one file system for *Entire disk* / *All drives*) under `FindProgress` through `_watch_job(..., abort="Cancel
search?")`. **Results are a `FindListing` in `Panel.found`** (DN's `TFindDrive`): the panel lists its entries -- live
while searching, re-`stat`ed by `restat_found` on a re-read, gone ones dropped -- under a `..` that leads back
(`leave_found`, cursor where it was); title `Find: mask`, the info line under *Current file* the entry's directory. Enter / Ctrl+PgUp on `..`
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

**Alt+Y, Panel > Panelize command** (`Panelize`, `Manager.panelize`; a departure, MC's *External panelize*):
`PanelizeDialog` (history `panelize`, seeded with `Manager.last_panelized`), then `navigator/lib/file_ops/panelize.py`'s
`capture` runs `$SHELL -c command` in the panel's directory on a thread -- off the console's pty, stdin `/dev/null`,
its own session so *Cancel* (`FindProgress` retitled, the count row hidden) kills the group -- and
`filefind.list_from_lines` (Alt+V's reading, split out of `read_list`) turns the lines (NUL-split when the output has
a NUL: `find -print0`) into a `FindListing(command=...)` titled `Panel: <command>`. Nothing listed: *No files found*,
with the first stderr line when the command failed. **Ctrl+R in such a listing runs the command again** (`on_rescan`),
columns and cursor kept. Enabled only on the local disk. Two more ways in: a command line starting `|`
(`console-command-line`) and a user-menu item with a `<|` line (`navigator-user-menu`).

**Entries can live elsewhere**: `DirEntry.directory` (None in a directory listing), **`DirEntry.path_in(here)`** for
its path -- never `here / entry.name` -- and **`DirEntry.key`** (name, or whole path when elsewhere) for tags,
`marked`, `_keep` and `reload(key=...)`. Untag through `Panel.untag(entries)` / `untag_paths(paths)`; `tag_paths(locations)` tags (Verify checksums' failures).

## Make list (Alt+L)

`MakeList`, `Manager.make_list`, DN's `CM_MakeList` -> `MakeListFile` (also Panel > Make list file): nothing tagged,
`SelectDialog` first; then `MakeListDialog` (`dlgMakeList`: file name, history `make_list`, opened on its last entry
or `makelist.DEFAULT_NAME` `dnlist.txt` -- DN's `DNLIST.BAT` -- and *Action*, history `command`, opened on the last
command run; *Store path names* / *Autodetermine*, kept for the session in `Manager.make_list_options`, where DN kept
them in its configuration). `navigator/lib/file_ops/makelist.py`: one line per file, or per file per `;` template (`;;` a `;`) with
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
(`dlgPanelSetup`, laid out as `FMDefaultsPage` plus *File mask*, history `file_mask`) opens on the panel's own
values and OK is `Panel.set_options(sort, display, mask)`: one re-read keeping the cursor. **`Panel.display`** is None
while the panel follows the *New Manager defaults* live and a frozenset of `PanelDefaultsData.DISPLAY` names once set;
ask `Panel.shows(option)`, never `SETTINGS.panel_defaults` directly. **`Panel.file_mask`** (DN's `FileMask`, `*` for
all) filters files, never directories, in `scan_directory` through `filetypes.in_filter` (`InFilter`: `;` patterns,
`-` excludes, the last match decides, nothing matching is out; case counts). A mask other than `*` follows the path in the
title, `/src [*;-*.bak]` (`title_text`; the path is cut first) -- a departure: DN's panel said nothing of it. *Directory length*, *Totals* and *Free space* are stored but not drawn yet.

## Directory length (Alt+G)

`CountLength`, `Manager.count_length`, DN's `cmCountLen` (also Panel > Count directory length): the directory at the
cursor (`..` counts the one listed) and every tagged directory get the bytes beneath them, counted on a thread by
`navigator/lib/file_ops/dirlength.py` (`CountDirLen`: dot-files count, symlinks count as themselves and are never followed, unreadable
directories count as nothing) under `run_with_progress`'s *Counting directory length* box; Esc keeps what was counted.
That box is `navigator/widgets/file_ops/count_progress/` (`CountProgress`, a departure from DN's bare wait box): bytes,
files and directories met so far, summed over every target through one `CountJob` that `count_dir_length` adds to
(any other job, such as the panel scan's, only stops it). With more than one target it also names the directory being
counted and shows a *This directory* column (`CountJob.here_*`, restarted per target) beside *Total*. The counts are
one unwrapped `StaticText` (`CountProgress.counts`): columns as wide as their longest entry, the total against the right
edge, so a size gaining a digit (99G -> 100G) widens its column instead of pushing past the frame. `modal_width` is
bound to `box_width` -- the table's natural width plus the frame, at least 50 (one directory) or 60 (several) -- so the
box grows, re-centred, as the counts gain digits, capped at `parent.width` (the screen, once overlaid); a row too long
for that loses its label, never its end.
The entry gets `size` and `counted` (DN's `Attr or $80`), its size column shows the size where `DIR` was, the tagged
total includes it, and *Size* sorts by it. **A re-read keeps the counts** (a departure, asked for: DN's went with the
old entries, so sorting by size -- itself a re-read -- lost them): `Panel._apply` hands a re-read of the directory
listed to `_keep_counts`, which copies each counted directory's bytes onto the new entry by `key` and re-orders when
the order is by size. A change of directory forgets them. Alt+G's answer goes through `Panel.set_lengths`, which,
sorting by size, re-orders the listing at once with the cursor on its entry (on its screen row); otherwise bumps
`sizes_token`. `panel_defaults.directory_length` (count every
directory at each read, `fmiDirLen`) is not written yet.

## Information panel (Ctrl+L)

`DiskInfo`, `Manager.on_disk_info`, DN's `cmDiskInfo` -> `SwitchView(dtInfo)` (also Panel > Info): `InfoPanel`
(`manager/info_panel`, Python-only, framed like the quick view, `::highlight` for DN's `~` runs) takes the passive
panel's place as the tree and quick view do. `Manager._info_follows_panel` (an effect on the active panel's path,
items and `reload_token`; not while it shows a *Find:* listing) calls `InfoPanel.show`, which reads the disk and the
machine on a thread (`navigator/lib/system/diskinfo.py`'s `gather`: `disk_usage`, the longest mount in `/proc/self/mounts`, a
`/dev/disk/by-label` label, `/proc/meminfo`, the resident set, `DirInfo` else `File_ID.DIZ` in any case) and keeps
the last answer up meanwhile. `diskinfo.lines` lays them out as `TDiskInfo.Draw`, each behind a `[drive_info]` box;
totals come from the listing (entries counted as `CountDirLen` counted them, bytes the files'). DN's EMS/XMS lines
are left out; its memory three are read for POSIX.

**A departure**: a *Current file* section (rule, then `Label: ~value~` lines, left-aligned) follows the directory
block, behind the `current_file` box (*File under the cursor*). DN's `TDiskInfo` described the directory alone.
`Manager._info_follows_cursor` is a separate effect on the active panel's `selected` and calls `InfoPanel.show_file`,
so a cursor move never re-runs `gather`. Name, type, size, mtime, attributes (+ octal), owner and link target come
from the `DirEntry`. `diskinfo.stat_file` on the same thread adds the MIME guess (stdlib `mimetypes`, whose table is
read on first use, hence the thread) and, for a local entry only, the `lstat`'s atime, ctime, links and inode.
Nothing for `..`.

## Comparing directories (Panel menu)

Panel > Compare directories (DN's `cmCompareDir`), its *Window, recursive* Synchronize window and File > Compare
files are the `navigator-compare` skill.

## Same directory in other panel (Alt+=)

`EqualizePanels`, `Manager.equalize_panels`, Panel > Same directory in other panel: the passive panel goes to the
active panel's directory, and the keyboard stays. **A departure**: DN 1.51 had no such command; it is Midnight
Commander's *Sync panels*. MC's Alt+I is the footer here and every Alt+letter can be a menu-bar accelerator (Alt+O
opens *Options*), hence Alt+=. The passive side is brought as Alt+F1/F2 bring theirs (`bring_side`: a hidden side is
shown, the tree or quick view gives way) and leaves a *Find:* listing; greyed while the active panel is one.

## Miller columns (Alt+F12)

`ToggleMiller`, `Manager.toggle_miller`, Manager > *Miller columns* (ticked while on). **A departure, asked for**:
DN had two panels and nothing else; this is Finder's column browser. `navigator/widgets/manager/miller/miller_view.py`.

- **`MillerView`** (Python-only, `id: miller`, hidden in the `panels` row) takes both panels' place; a hidden side or a
  tree/quick/info view is put back first. **Empty while off**: `open_at` makes the columns, `close` removes them, so
  nothing is read or watched for a layout not showing. Off again, the side that was active (`_miller_side`) goes to
  the directory browsed, the cursor on its entry; the other side is untouched.
- **Every column is a `MillerColumn(Panel)`**, so commands need nothing new: **`Manager.active_panel` is
  `miller.current`** (the chain's last), and **`passive_panel` is the active one too** -- F5/F6 offer the directory
  browsed, Ctrl+C/Ctrl+V go between two. `Manager.miller_mode` is the flag; `_NOT_IN_MILLER` greys what needs two
  panels (swap, hide sides, tree/quick/info, divider, Ctrl+Y, Alt+I, Alt+K, *Find:*-style listings). `bring_side`
  (Alt+F1/F2) answers the column, `show_only` does nothing (Ctrl+F1/F2 fall through to `Shell`). Anything that must
  reach every panel -- a re-read after a copy, a drive closing, *FileSaved* -- loops over **`Manager.all_panels`**,
  never `(left, right)`.
- **The chain** (`MillerView.chain`, root first, replaced to change) comes from `_up` -- `Location.parent`, and at a
  drive's root its `change_up`, as `Panel.go_up`. `_rebuild` keeps columns already on the way and makes the rest.
  Right/Enter on a directory `step_in` (the **preview column becomes the chain's last**, a new preview is made);
  Left/Backspace `step_out` (the last column becomes the preview, cursor kept). A press on an earlier column drops the
  ones after it (`column_pressed`). **Any other move of the current column** -- a shell `cd`, a bookmark, Alt+T, Enter
  on an archive -- moves the panel as it always did, and `_follow_moves` rebuilds the chain around it (`home` is
  where the view last put a column).
- **The preview** (`_follow_cursor`): a directory in `preview_dir`, a file in the view's own `QuickViewer`
  (`preview_file`), or the quick view empty. Tab moves the keyboard into the file and back (`switch_focus`).
  `_aside_focused` counts it with the tree and quick view.
- **Layout** (`_place`): columns `[file_manager] miller_width` wide (File Manager Setup's *Miller column width*,
  at least `MIN_WIDTH` 12), as many as leave the preview a column's width, the leftmost giving way; the preview takes
  the rest. The first visible column and the preview keep `title_margin` 5 for the window icons.
- **A column's look**: simple mode drawn narrow -- gutter, name, `▸` (`>` in ASCII) after a directory; title the
  directory's own name; no footer, option strip, `..` (filtered in `_apply`) or git letters (`_read_git`). The entry
  the next column lists is `Panel::row.trail` (`reverse`) while another column has the keyboard, via the
  `Panel.row_classes` hook. Ctrl+H and the order apply to every column at once.
- **Only the column browsed** offers *As root* (`_offer_root`) and goes into Alt+Backspace's history (columns'
  `_remember_directory` is a no-op; `step_in`/`_rebuild` remember) -- the preview moves with every cursor step.
- Kept with the desktop as the window's `miller` (path, cursor, side), on the local disk only.

## Swapping panels (Ctrl+U)

`SwapPanels`, `Manager.swap_panels`, DN's `cmSwapPanels` (also Manager > Swap panels): the two panel objects change
places in the `panels` row, whole, and **`Manager.left`/`right` are swapped with them** -- they name sides, not panels,
so Alt+F1, Ctrl+F1 and the rest act on whatever is on that side now. A tree or quick view goes beside the panel it
stands in for; the keyboard stays with its panel. A hidden side is shown first (DN's code ended that way too). The row
is re-`arrange()`d by hand: reordering `children` in place is not something its layout follows.

## The divider between the sides

DN's `TSeparator` (FLPANEL.PAS, `TDoubleWindow.HandleCommand` in DBLWND.PAS). These are the two columns where the
sides meet: the left side's right frame edge and the right side's left one. Dragging them with the mouse moves the
divider. Alt+Left and Alt+Right (`MoveSeparator(step)`, DN's `kbAltLeft`/`kbAltRight`) move it one column.

- **The split is a proportion.** `Manager.split` is the first side's share of the row, or `None` for the even split.
  It is DN's `OldX/OldW`, so resizing or zooming keeps it. `MIN_SIDE` (3) is the narrowest a side can go.
- **It is applied as a layout hint.** `place_divider()` is an effect that reads the split, the row's width and which
  views are showing. It gives the first *showing* view `basis: N; grow: 0`, and every other view the defaults.
  - The hint therefore follows the side, not the panel object: it lands on a tree or quick view that stands in, and
    after Ctrl+U it moves to the panel that is now on the left.
  - `swap_panels` calls `place_divider()` itself, because reordering children is not reactive.
  - With one side hidden, no view gets a hint.
- **It is hit-tested before the chrome and the children** (`Manager.dispatch_mouse`, `divider_hit`). A panel claims
  a press anywhere in its rectangle, frame included. The left side's edge column counts only where its `bar` is not
  showing; on the scroll bar's rows a press there scrolls the list. The drag captures the mouse onto the Manager and
  is handled in `on_mouse_click`, ahead of `Window`'s own move and resize.
- **A double click on the divider resets the split to `None` (the even split).** This is a departure: DN had no way
  back except dragging. The second press has already taken hold of the divider and captured the mouse, so the
  `DoubleClickEvent` reaches `Manager.on_double_click`. It lets go of the divider and clears the split. A double click
  anywhere else falls through to `Window` (zoom on the title).
- **While held, the divider is drawn with single lines** (DN's `sfDragging` look). `Manager.render_after` runs after
  the sides have painted. It swaps each double-vertical box character on the two divider columns for its single one,
  so junctions keep their shape and scroll bar cells are left alone.
- **`Panel.on_key` in list mode leaves Alt+Left and Alt+Right alone.** Its bare `left`/`right` check would otherwise
  take them.
- A saved desktop keeps `split` (`desktop_state`).

- **Every feature key is on a menu** (departures, asked for): Panel > *Move divider left/right* (`MoveSeparator(step=∓1)`,
  Alt+Left/Right; no hotkeys, `j` being the only free letter), and the panel's right-click menu ends with *Insert name*
  / *Insert path* (`InsertName`/`InsertPath`, Ctrl+Enter / Ctrl+Shift+Enter, answered by the shell). Left off on
  purpose: Alt+1..9 / Alt+Shift+1..9 (the bookmarks box has them), Alt+F6 (*Quick rename* is its menu form),
  Shift+Enter (a *Find:* listing's), Ctrl+Shift+F1..F10 (user-defined), and navigation. F1 (`Help`) is bound but has no
  handler yet. In an archive the right-click menu adds *Extract to...*/*Test archive* (`navigator-drives`).
  In a *Find:* listing it starts with *Go to ~f~ile* (`GoToFile`, Enter's `go_to_entry`, a command only for the menu --
  Enter stays `Panel.choose`) and *Show in ~o~ther panel* (`ChangeInactive`, Shift+Enter), which is also Panel >
  *Show in other panel*, enabled only in a listing.
  *Select group*, *Unselect group* and *Invert selection* pass their keypad keys as static keys (`key_label("kp_plus")`
  ...): their bindings are the `by_key=True` commands, which the menu's plain ones are not equal to, so no live key is
  found -- the Panel menu's static `Gray "+"` is the same fallback.

## Read when

No DESIGN reference of its own; panel-related library notes are in
`.claude/skills/navml-library/reference/widget-library.md` (*What the library took from `Panel`*).
