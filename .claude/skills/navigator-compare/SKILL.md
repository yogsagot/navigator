---
name: navigator-compare
description: Comparing -- Panel > Compare directories (DN's cmCompareDir, CompareDialog, navigator/lib/file_ops/dircompare.py: tagging by size/time/attributes/contents), its third mode *Window, recursive* (navigator/lib/file_ops/dirsync.py walk/plan/summary, SyncWindow with SyncList, CompareProgress, Manager.sync_directories and Manager.synchronize, CopyRequest.pairs), and File > Compare files (navigator/lib/file_ops/filediff.py compare/align, DiffWindow with DiffView, open_diff, DiffFiles, Manager._diff_pair). Use when changing any comparison of files or directories.
---

# Comparing files and directories

Three features share one dialog's checks and one model directory (`navigator/lib/file_ops/`):

| Feature | Model | Widgets | DN? |
|---|---|---|---|
| Panel > Compare directories, *Select*/*Unselect* | `dircompare.py` | `CompareDialog` | `cmCompareDir` -> `CM_CompareDirs` |
| ... *Window, recursive* | `dirsync.py` | `SyncWindow`, `SyncList`, `CompareProgress` | **a departure**: Total Commander's *Synchronize directories* |
| File > Compare files | `filediff.py` | `DiffWindow`, `DiffView` | **a departure**: `mcdiff`/meld; DN compared no files line by line |

## Compare directories: tagging (DN's)

`CompareDir`, `Manager.compare_directories`, from Panel > Compare directories only -- DN's Ctrl+C is left unbound,
kept for the clipboard; the command is in `Manager.keyless_commands` so Key bindings can give it one.
`CompareDialog` (`dlgCompareDirs`: size, time, attributes, contents; Select/Unselect/Window; opens on size+time+Select
every time, as `DT` was reset) then `dircompare.differing` on each panel against the other. A file matches one of the
same name (exact case) passing every check: same size, **this one no newer** (to the second), same permission bits,
same bytes. *Select* tags exactly what has no match (directories never), *Unselect* only untags it -- so Select tags
what a copy across would bring up to date. Only *contents* reads the disk, on a thread under *Comparing files*; Esc
leaves the tags. A panel that moved meanwhile is left alone. Disabled in a *Find:* listing and in Miller columns.

## Window, recursive: Synchronize (a departure)

The dialog's third radio sets `CompareRequest.window`; `compare_directories` hands over to `sync_directories`, which
refuses two panels on one place, walks on a thread (`sync_window.walk_trees` -> `dirsync.walk`, under
`CompareProgress` after `SLOW_PROGRESS_DELAY`, Cancel stops it) and opens `SyncWindow`. **The left panel's tree is
always the left column**, whichever panel is active. Dot-files are walked only when both panels show them.

- **`dirsync.walk`** lists directory pairs breadth-first through `Drive.children` (any drive). A path is
  `LEFT_ONLY`, `RIGHT_ONLY`, `DIFFERS`, `SAME` or `CONFLICT` (file against directory, a FIFO, an unlistable
  subdirectory -- its `error` shows on the list's footer). **A directory on one side alone is one row**, not walked
  into: copying it copies its tree, and so every row's target directory exists. Links are not followed; two are the
  same when `readlink` agrees. Files are compared by **`dircompare.same_file`, the symmetric twin of `_matches`**: a time
  differing either way differs (DN's tagging asks *this one no newer*), and differing sizes skip the contents read.
  The walk returns every row, `SAME` included; *Show identical* (Ctrl+H) only filters what is listed.
- **Nothing per row runs per frame.** `enables(Synchronize)` is asked at every key-bar repaint, so it reads
  `SyncWindow.totals` (`dirsync.summary`, kept by `_show`), never `plan()` -- which joins two paths a row (0.3 s for
  40k rows) and runs on F5 alone.
- **Actions** (`ALLOWED`, first is the default): one side alone -> copy across / skip / delete; differs -> the newer
  side's way, skip when the times are equal / copy either way / skip; same and conflict -> skip only.
  `with_action` refuses what a status does not allow and maps `"default"`. Keys (Total Commander's): Right, Left,
  Space, Del, Backspace (`SetSyncAction`), Ctrl+Right/Ctrl+Left/Ctrl+Backspace (`SetAllSyncActions`), Enter/F3 a
  `DiffWindow` on a pair of files, F5 Synchronize, Ctrl+R/Alt+R walk again. Those with arguments are in the class's
  `keys` dict, as markup cannot construct a command. Changing a row replaces it in a new `all_rows` list.
- **`Manager.synchronize(plan)`** confirms (`tr_n`), then runs **one** `CopyRequest(pairs=..., mode=OVERWRITE,
  options=PRESERVE)` through `_run_copy` -- the copy box, *As root*, `_watch_job` -- and the deletes through
  `_run_erase(EraseRequest(..., recursive=True))`. **`PRESERVE` is not optional**: without the times kept, the next
  walk finds every copied file different again. The window then walks again.
- **`CopyRequest.pairs`** (`filecopy.py`): each source with its exact target; `_Copier.run` skips `resolve_target`,
  measures all sources once and finishes every drive touched. Navigator's own, for two directions in one job.

## Compare files (a departure)

`DiffFiles` (File menu, *Compare files...*, no key; keyless in the Manager table), `Manager._diff_pair`: two tagged
files in the active panel; else the cursor file against its namesake in the other panel, or the other panel's cursor
file -- the left panel's file always on the left. Greyed when there is no pair (and in Miller columns or with a side
hidden, unless two are tagged). `open_diff(desktop, left, right)` runs `filediff.compare` on a thread under
*Comparing files*; identical files, binary ones (a NUL in the first 8 KiB) and ones over `TEXT_LIMIT` (16 MiB, byte
compare only) get a box with `DiffersAt`'s byte and line; files differing only in line endings get a box too.

- **`TextDiff`** keeps the aligned rows in arrays (`left_line`/`right_line`, -1 a filler; `kinds`), plus `hunks`
  (each run's first row). Lines are split on `\n` with one `\r` dropped. `_opcodes` trims each range's common
  head and tail; a range up to `MATCHER_LIMIT` (lines x lines, 1M) goes to `SequenceMatcher(autojunk=False)`, a
  larger one is first cut by **patience diff** (`_anchors`: lines unique to both sides, longest in-order run).
  **Never hand a large range to the matcher whole**: it is quadratic at worst -- 122 s for 50k lines with every
  third changed, 0.2 s cut at anchors. A large range with no unique line is one change. The matcher's
  `find_longest_match` raises `Stopped` for a stopped job -- `run_with_progress` awaits its thread, so an
  unstoppable alignment would hang Cancel.
- **`DiffView` is one widget painting both columns**, so the sides cannot scroll apart: `top`, `x_delta`, `current`
  are its own reactive state, the window's scroll bar binds to `top`/`last_top`. Movement keys are its `on_key`
  (not rebindable, as the viewer's); N/Alt+Down and P/Alt+Up (`NextDifference`, `PreviousDifference`), F3/Esc and
  Ctrl+R are the window's table (`diff_window`). Next/previous count from the current difference while it is on show,
  else from the view. `open_diff` calls `view.go_to(0)` after `desktop.open`, as the view's height is unknown before.
- Marks `-`/`+` begin every non-equal row, so the view reads in mono; the current difference's marks are
  `::mark.current`. Text is decoded by the viewer's `decode_cells` (UTF-8, CP437 fallback, tabs, wide characters).

## Colours

`DERIVED` aliases (`palette.py`), each with `DERIVED_ITEMS`, `attributes.nss`, `themegen.DERIVED_ROLES` and palconv's
`default` departures (git's colours): `diff-added/removed/changed` ([189]/[190]/[191], the viewer's syntax slots, on
the viewer's ground: rules set fg only), `sync-new/changed/same/conflict` ([176]/[177]/[85]/[180], on the panel's
ground). `SyncList` is dressed as a panel inside a dialog's frame; `DiffWindow` as `FileWindow`.

## Tests

`tests/test_filediff.py`, `tests/test_dirsync.py` (models and `pairs`), `tests/test_diff_window.py`,
`tests/test_compare_dirs.py` (tagging and the Synchronize window).
