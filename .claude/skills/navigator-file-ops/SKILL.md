---
name: navigator-file-ops
description: File operations -- F5 copy and F6 rename/move (navigator/lib/file_ops/filecopy.py, CopyDialog, CopyProgress, OverwriteQuery), Shift+F5 symlinks (filelink.py, LinkDialog), F8/Del erase (fileerase.py, DeleteDialog, EraseQuery, DeleteProgress) and the optional freedesktop Trash (trash.py, Restore, Empty Trash), Alt+E file attributes (fileattr.py, AttrDialog; its ACL, Xattrs and Flags tabs: acl.py, fsflags.py, AclEntryDialog, XattrEntryDialog), F7 mkdir, Ctrl+F7/Ctrl+F8 UU encode/decode (uucode.py), File > Checksums (checksum.py, CalculateChecksumsDialog, ChecksumProgress, ChecksumReport), the Job worker contract (navigator/lib/system/job.py) and Manager._watch_job. Use when changing any operation over selected files.
---

# File operations

All live under `navigator/widgets/file_ops/` (dialogs, progress boxes, queries; commands in its `commands.py`), with
models in `navigator/`. Operations run on a thread through **`navigator/lib/system/job.py`'s `Job`**, the worker contract
`CopyJob`, `EraseJob` and `AttrJob` share; **`Manager._watch_job`** is the loop that watches one. Progress boxes are
DN's `TWhileView` with the library's `ProgressBar`. Copied/erased entries are untagged and both panels re-read.
A refused step offers **As root** (copy, move, erase; `navigator-elevation` skill).

**Nothing that can wait on a disk runs on the loop.** A job that asks questions goes through `_watch_job`; one that
only reads or writes goes through **`navigator/lib/system/progress.py`'s `run_with_progress(app, func, job, make_box, refresh)`**
(the viewer's search, the editor's reads and saves, F3's open, Alt+E's survey): the box after a delay
(`PROGRESS_DELAY`, or `SLOW_PROGRESS_DELAY` for file reads and writes, which use `WriteWin`), and the job stopped if the
task ends unfinished. Small reads a widget paints from (tree probes and counts, the quick view, the file dialog) use
`navml.background.Background`, one pool per kind so a dead mount cannot starve another. **What stays on the loop, on
purpose**: F7's mkdir, Shift+F5's symlink, Shift+F4's `is_dir` checks and ^K W's existence/chmod -- one syscall each on
a path the user has just named, where a thread hop would only reorder the dialogs around it.

## Copy and move (F5, F6)

DN's `FILECOPY.PAS`. `navigator/lib/file_ops/filecopy.py` is the model (`CopyRequest`, `CopyJob`, `run` on a thread; DN's five copy
modes, `MkName` masks, rename-first moves with an `EXDEV` fallback, `resolve_target`). `CopyDialog` is
`dlgCopyDialog`/`dlgRenameDialog` in one document, seeded with the passive panel's directory, F10/*Tree* picking it from
a tree, mode and options remembered for the session. `Manager.copy_files` puts up `CopyProgress` (*Stop* asks *Abort
operation?* with the copy paused) and `OverwriteQuery` (`dlgOverwriteQuery`) as the worker asks. **The check boxes are a
departure**: *Preserve attributes* and *Follow symlinks* stand where DN's *Verify disk writes* and *Copy descriptions*
stood, in the same bits. `Cluster`'s columns fit the four boxes in two rows.
**So is `CopyProgress`' speed row** (*Speed 9.5MB/s, 0:42 left*, the box 14 rows where DN's was 13): `_watch_copy`
feeds `navigator.lib.system.progress.Rate` the job's `done_bytes` every tick, and the speed is the growth over the last
`RATE_WINDOW` (5 s), so a pause behind a question drops out; the time left is the bytes still to go at that speed.
`DeleteProgress` has the same row in entries a second (*Speed 1,200 files/s, 0:42 left*, 11 rows where it was 10),
fed by the erase's refresh; the time left waits for `EraseJob.measuring` to end. *File attributes* shares the box and
leaves the row blank.

- **Without path names** (`CopyRequest.flatten`, *Extract files*' box unticked): a directory copied puts every file
  under it straight into the target (`_Copier._flattened`), no directory made; Extract to and Shift+F2 use it
  (`navigator-drives`, *Extract to, Test, Shift+F2*).
- **Pairs** (`CopyRequest.pairs`, Navigator's own): each source with its exact target, no target line read; measured
  once, every drive touched finished. *Synchronize* copies both ways in one job with it (`navigator-compare`), and
  erases through `Manager._run_erase`, the worker half of `erase_entries`.

- **A paste (Ctrl+V) is `copy_entries` with `here`**: the entries' directory as it was clipped
  (`navigator.lib.file_ops.clip.CLIP.here`), not the source panel's now, so sources are right after it navigated.
  `copy_entries` returns whether the copy ran and was not stopped; `paste_files` forgets a moved clip then. A
  directory is never pasted into itself (`_into_itself`, shared with drag and drop); a cut pasted where it came from
  does nothing. The keys and cue are `navigator-panels`'.

## Quick rename (Shift+F6)

A departure, asked for: `QuickRename` (Shift+F6, Midnight Commander's rename key; Ctrl+F6 stays DN's Calculator), `Manager.quick_rename` -> `RenameDialog` (`file_ops/rename_dialog`),
the old name in the line, its stem selected (`os.path.splitext`; a directory whole), so typing keeps the extension. Enabled only when the selection is one entry (`_rename_candidate`: the one
tagged, else the cursor's, never `..`). The rename itself is `Manager._rename_entry`, shared with Alt+F6's in-place
`fast_rename`: beside itself only (a `/` is refused, no moving), a taken name refused, on a thread, cursor and tag follow.

## Multi-rename (Alt+A)

A departure, asked for: Total Commander's *Multi-Rename Tool* (its Ctrl+M is Enter in a terminal, and Alt+M/Alt+O
are the menu bar's *Manager*/*Options*, so Alt+A); DN's group rename stays F6's `*`/`?` mask (`apply_mask`).
`MultiRename` -> `Manager.multi_rename`: the selection (tags, else the cursor's; works in a *Find:* listing, each
entry in its own directory) as `multirename.Item`s, the names already in each place read on a thread, then
`MultiRenameDialog` (`file_ops/multi_rename_dialog`; masks, search/replace, case, counter, the rule kept for the
session) whose `_follow_rule` effect re-plans on every change into the `RenamePreview` list (`!` marks a row that
cannot be done, the footer says why). OK is refused (`valid()`) while the rule does not read, nothing changes or a row
has a problem.
- **The language and checks are `navigator/lib/file_ops/multirename.py`'s docstring** -- pure, no I/O:
  `new_names`, `plan` (empty, `/`, `.`/`..`, two rows one name, a name taken by a file not renamed away).
- **Order** (`steps`): a row whose new name is another row's old one goes through `.navrename-<n>-<old>` first, so
  swaps and cycles work. `run` (a `RenameJob` on a thread, through `_run_renames` -> `_watch_job`) re-checks
  `lexists` before each rename (never replaces), asks `filecopy.Failure` -> Skip/Cancel on an error, puts a stranded
  temporary back **only if its old name is still free**, else leaves it and says so.
- **Bookkeeping** is `Manager._after_renames(panel, [(place, old, new)], at=)`, shared with `_rename_entry` (Alt+F6,
  Shift+F6): listing entries renamed, tags follow, `FileSaved`, reload, the other panel re-read if it shows the place.
- **Undo multi-rename** (Panel menu, no key) reverses `Manager.last_renames` (`multirename.Batch`, session only, one
  batch) through the same `run`; disabled when there is none.

## Symlinks (Shift+F5)

*File > Create symlink…*, a departure: DN had no links, and the key was Split/combine's (`cmPanelLongCopy`), which is
dropped. `navigator/lib/file_ops/filelink.py` is the model, reading the target with `filecopy.resolve_target`. `LinkDialog` is Copy's
dialog cut down, with one session-remembered *Relative link* box. `Manager.make_links` works with no worker thread and
shares Copy's *Skip* box.

## Erase (F8, Del)

DN's `ERASER.PAS`. `navigator/lib/file_ops/fileerase.py` (`EraseRequest`, `EraseJob`, `run` on a thread, depth first, **never through
a link**). `DeleteDialog` asks `Do you wish to delete` with a **Recursive delete** box (a departure, off by default,
remembered for the session). `EraseQuery` puts DN's *not empty* (No/Yes/All/Cancel) and *read-only* -- meaning not
writable -- (Yes/No/All) questions. `DeleteProgress` has a gauge and *Cancel*, which asks *Abort operation?*. Del and
Shift+Del are `by_key`, stepping aside while the command line has text; Shift+F8/Shift+Del (`DeleteSingle`) take the
cursor's entry whatever is tagged.

## The Trash (F8 with *F8 moves to Trash*)

Not DN's, and **off by default** (`[file_manager] use_trash`, File Manager Setup's *F8 moves to Trash*). The
freedesktop.org Trash spec 1.0, so GNOME/KDE/`gio trash` see the same items. `navigator/lib/file_ops/trash.py` is the
model: `home_trash()` (`$XDG_DATA_HOME/Trash`), `trash_for` (home trash on its own file system, else the mount's
`$top/.Trash/$uid` -- sticky, not a link -- or `$top/.Trash-$uid`), `move` (info file reserved with `O_EXCL`, then
`os.rename`; **never copied across file systems** -- `EXDEV`), `items`, `restore` (never over anything), `forget`,
`restore_all`/`RestoreJob` on a thread. `directorysizes` is not kept (optional in the spec).
- **One eraser**: `EraseRequest.trash`; `_Eraser._to_trash` moves a local source whole (measured as 1, no read-only
  question, no *As root*). On `EXDEV`, `desktop.trash` (`gio trash` or `kioclient move … trash:/`) is tried first where a backend is
  (`navigator-gio`/`navigator-kio` skills; not listed
  in `trash:///`). Where it cannot, `NoTrash` asks No/Yes/All/Cancel (`EraseQuery`, No first) -- asked even
  from the quiet trash-can drop, since Yes loses the file. `Manager._trashes(panel, entries)` decides (setting on,
  every entry on the disk); the drop's prompt says *move ... to the Trash* then.
- **The Delete dialog's second box**, *Move to Trash* (`TRASH` bit), shown and ticked only when `_trashes` is true;
  unticked it erases, so there is no bypass key. The first line follows the box; the dialog is a row taller.
- **Ways in**: Disk > *Trash* (`OpenTrash`), the trash can's double click (where DN's *Reanimator* was), the
  bookmarks box's `~T~rash` (so `t` left `BOOKMARK_KEYS`), and `trash:///` anywhere a place is typed; `..` or Backspace at its root goes back where the panel was. Disk > *Empty
  Trash* (`EmptyTrash` -> `Manager.empty_trash`, through `_run_erase`); File > *Restore from Trash* (after Delete; **hidden**, not greyed, unless the active panel is the Trash's root:
  `Shell.__init__` binds the item's `hidden` to `Manager.shows_trash` of the bar's context) and the context
  menu (`RestoreTrash` -> `Manager.restore_trash`, root items only). The drive is `navigator-drives`'.
- Tests: `tests/test_trash.py`; `conftest` points `XDG_DATA_HOME` into each test's directory, so nothing reaches the
  user's Trash.

## File attributes (Alt+E)

DN's `cmSetFAttr` read for Linux (a departure: DN edited four DOS bits). What the dialog shows is gathered first on a
thread (`attr_dialog.gather`: every `stat`, and the user/group lists NSS may fetch from a directory server), under
*Reading file attributes* if slow, and passed in as `facts`. `navigator/lib/file_ops/fileattr.py` (`survey`,
`AttrRequest`, `AttrJob`/`run` on a thread, never through a link under recursion). `AttrDialog` is one dialog over every
tagged file, as `dlgFilesAttr` was: a twelve-bit grid with an octal line (a base-8 `MaskedField`, each digit setting its
three boxes), *User*/*Group* `ChoiceField`s, DN's *Date*/*Time* (`DateField`/`TimeField`), and *Recurse*. DN's Set/Clear
columns became **tri-state `CheckBoxes`**. **Only bits the user pressed are applied.** `Dialog.valid()` keeps it up over
an unreadable value. In the grid R, W and X tick *Read*/*Write*/*Exec* in the cursor's column
(`_on_bits_key`, `ROW_KEYS`, Latin in every language), which the key bar says while the grid has the keyboard
(`AttrDialog.key_hints`; a departure, asked for).

**Behind tabs: *Mode* | *ACL* | *Xattrs* | *Flags*** (a departure, asked for). The pages are `TabPage`s inline in
`attr_dialog.nml`, so every id is still the dialog's; the name rows and *Recurse* stand outside them, since every
page obeys *Recurse*. The tabs are simple ones (`TabView.side: "simple"`, bare captions over a rule), so the box is
64 by 21. All three new pages are **deltas**: `survey` shares what every file has (`None` -- shown `???`,
`<differs>`, `[?]` -- where they disagree or only some have it), and `build()` puts only rows added, changed or
removed (flags pressed, `flags_touched`) in the request, so one edit reaches files whose ACLs otherwise differ.
- **ACL** (`navigator/lib/file_ops/acl.py`, pure): the `system.posix_acl_access`/`_default` xattrs read and written in
  the kernel's binary form (no libacl, no `setfacl`). The owner/group/other entries are the mode's and not listed;
  the mask is worked out as `setfacl` does unless set by hand (the row says *auto* while it will be), and an ACL
  left minimal is removed (`setfacl -b`), the mask going back into the group bits. Rows are keyed
  `(default, kind, id)`; default rows only for directories. Ins/Enter/Del and *Add*/*Edit*/*Delete*/*Clear*;
  `AclEntryDialog` (`file_ops/acl_entry_dialog`) picks whom from **all** users or groups (an ACL may name anyone,
  unlike chown), the list swapping with *Type*; editing keeps whom and whether default.
- **Xattrs**: every readable name but the two ACL ones; `XattrEntryDialog` takes `getfattr`'s spellings
  (`fileattr.spell_value`/`parse_value`: text, quoted when it would read otherwise, `0x` hex, `0s` base64); a name
  must be `user.`/`trusted.`/`security.` (`check_xattr_name`).
- **Flags** (`navigator/lib/file_ops/fsflags.py`): `FS_IOC_GETFLAGS`/`SETFLAGS` on the file held open, **regular
  files and directories only** (a device is never opened); twelve editable flags in the grid, the rest only in the
  `lsattr` line. An unsupporting file system (`ENOTTY`...) leaves the page inert with a note, as another drive does
  (`XATTR`/`FSFLAGS` capabilities: the disk and `root:` alone).
- **`apply_one`'s order**: `i`/`a` cleared, chown, ACLs (then re-stat: the mask is the group bits), chmod (touched
  group bits become the mask), xattrs, utime, flags set -- `+i` last, `-i` first. One generic path over a drive
  (`LOCAL`, `ROOT_DRIVE` once elevated, or another drive with links skipped), so a refusal offers *As root* as before.

## Make directory (F7)

The first dialog wired into the application; `Field(history_id="mkdir")`.

## Printing (Ctrl+F9)

`Manager.print_files`, DN's `CM_Print` -> `PrintFiles` (`FLTOOLS.PAS`, `GAUGES.PAS`): the selection
(`Manager.selection`, DN's `GetSelection`) less its directories -- nothing at all if that leaves nothing -- after
DN's *Print file NAME?* / *Print N files?* (N counting the directories, as DN's did). Each file goes to the spooler by
name (`navigator/lib/system/printing.py`'s `spool_file`: `lp`, else `lpr`, given the absolute path), standing for DN's print manager,
and is untagged once queued (`cmCopyUnselect`); a refusal stops the run, says why, and leaves the rest tagged.
`PrintFile` is the editor's F8 command too, so it lives in `navigator/commands.py`. File > Print sends it.

## UU Encode / UU Decode (Ctrl+F7, Ctrl+F8)

`navigator/lib/file_ops/uucode.py`, DN's `UUCODE.PAS`/`UUE2INC.ASM`, on the file at the cursor (`UuEncode`/`UuDecode`, enabled on
a file only); `Manager.uu_encode`/`uu_decode` -> `_run_uucode` (a `FileJob` under `WriteWin`, `_watch_job`, questions
by `_answer_uu_question`: `ExistsQuery` Yes/No/All/Cancel, errors as *Error* boxes).
- **Encode** is transcribed: `plan()` is `CalcLSsize`; one file a section (`NAME.uue`, else `.uu1`.. `.u10`.. `.100`);
  `section N of M of file NAME  < uuencode by Navigator >`; statistics, `filetime` (DOS packed time), `table`,
  `begin 644`; `UUXLT` with a backquote for 0; checksum levels cumulative -- entire `sum -r/size`, per-section
  `sum -r/size` over the counted lines plus `\n`, a check character per line (`GetLnCrc`), DN's `crc64`
  (`CRC64_START`, add-and-rotate). Every answer is kept in `[uucode]` and saved when it changes.
- **Onto another drive**: encoded or decoded into a staging directory, then up through `usefile.put_files`, whose
  `ask` hook puts the same `FileExists` question (a `Location` then) of the files already there, before anything is
  written (`ask_over_encoded`, `ask_over_decoded`; `navigator-drives` has it).
- **Decode** reads one file holding any files and sections in any order (a state machine, not a transcription of DN's):
  section headers, `table`, `filetime`, `begin`/`end`, `sum -r/size` checked, anything else passed over. A severe
  error breaks a file, written only with *Save broken files*; *Check existing files* asks; *Display error messages*
  shows each. Departures: names keep case and length; a blank line also ends the data; `crc64` is not checked.

## Checksums (File > Checksums)

`navigator/lib/file_ops/checksum.py`, **a departure, asked for** -- DN had no checksums, so the commands
(`CalculateChecksums`, `VerifyChecksums`) are named for what they do and are in `Manager.keyless_commands` (no default key).
- **Format** is GNU coreutils' `*sum`: `hex␣␣name` (text mode), names relative to the list's directory; a name holding
  `\`, LF or CR gets a leading `\` and those escaped. Reading also takes `*name` (binary) and BSD's `TAG (name) = hex`.
  `sha256sum -c` checks what Calculate writes (a test runs it when coreutils is there).
- **Algorithm**: MD5, SHA-1, SHA-256 (default), SHA-512, BLAKE2b, extensions `.md5sum`..`.b2sum`. Verify tells a list's by
  its name (`SUFFIXES`, `WHOLE_NAMES` such as `SHA256SUMS`), else by its first digest's length; 128 hex digits without
  a `b2` name are SHA-512. The last choice and mode are kept in `[checksum]` (`Manager._keep_section`).
- **Calculate** works on `Manager.selection` (tagged, else the cursor's); a tagged directory is walked to the bottom
  (`walk`, `_count_on_drive`'s walk: a link to a directory is not followed, one to a file is hashed). *One list* writes
  through `_write_list` (so *As root* on the disk) after Alt+L's Yes/Append/Cancel (`_ask_over_list`), leaving the list
  itself out; *Each file* writes `name.<ext>` beside each as it goes (`write_each`, a Stop keeps what was written),
  skipping files that are lists, after one *overwrite them?* question. Entries done are untagged; unreadable files are
  said in one Error box (eight lines, then *and N more*).
- **Verify** takes the tagged lists (by name), else every tagged file or the cursor's, untags them, tags the failed and
  unreadable files in `all_panels` (`Panel.tag_paths`), and shows `ChecksumReport` (counts, and a `ListViewer` of the
  bad ones). Missing is `FileNotFoundError`; a list with no lines is in `lists_unreadable`.
- **Every read goes through `drive_of(...).open_read`/`children`**, so both work on any drive; all of it runs on a
  thread through `run_with_progress` (`ChecksumProgress`), asking nothing mid-work.

## Read when

| Reference | Read when |
|---|---|
| `reference/copying.md` | copy/move model, dialog, progress and overwrite queries |
| `reference/symlinks.md` | symbolic links |
| `reference/deleting.md` | erase model, queries, recursion |
| `reference/file-attributes.md` | the attributes dialog and model |
