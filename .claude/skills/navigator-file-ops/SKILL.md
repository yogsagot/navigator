---
name: navigator-file-ops
description: File operations -- F5 copy and F6 rename/move (navigator/lib/file_ops/filecopy.py, CopyDialog, CopyProgress, OverwriteQuery), Shift+F5 symbolic and hard links (filelink.py, LinkDialog), Show hard links (hardlinks.py), F8/Del erase (fileerase.py, DeleteDialog, EraseQuery, DeleteProgress) and the optional freedesktop Trash (trash.py, Restore, Empty Trash), Alt+E file attributes (fileattr.py, AttrDialog; its ACL, Xattrs and Flags tabs: acl.py, fsflags.py, AclEntryDialog, XattrEntryDialog), F7 mkdir, Ctrl+Z Undo of copies, moves, renames, Trash and mkdir (undo.py, uncopy.py, Manager.undo), Ctrl+F7/Ctrl+F8 UU encode/decode (uucode.py), File > Encoding > Checksums (checksum.py, CalculateChecksumsDialog, ChecksumProgress, ChecksumReport), File > Encoding > Encryption (encrypt.py over gpg/age, EncryptDialog), File > Encoding > Convert text (textconv.py, ConvertTextDialog), the Job worker contract (navigator/lib/system/job.py) and Manager._watch_job. Use when changing any operation over selected files.
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
- **Into an archive** (`CopyRequest.archive`, File > Archive > *Create archive...*'s `ArchiveOptions`; `navigator-drives`,
  *Shift+F1*): after the last file the copier packs (`job.packing`, `CopyProgress.packing` says *Packing* NAME *into*
  the archive, `_watch_copy` restarting the speed); Stop there leaves the archive as it was and moves nothing, and a
  move's sources are deleted only once the archive is written (`_Copier._held`).
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
- **Clean up names** (the 4th option, bit 8; `Rule.cleanup`/`codepage`, the *Code page* choice from the viewer's
  `ENCODINGS` minus UTF-8, greyed unless ticked) is step 0, before the masks: `clean()` re-decodes each run of
  `surrogateescape` bytes in the code page (only those runs, so a mixed name keeps its UTF-8; undefined bytes -> `_`),
  NFC, every `Cc` -> `_`. Then `plan` -> `_number_clashes` numbers names equal under `fold()` (NFC + casefold) per
  place: a name on disk not among the items wins, then unchanged rows, then item order; the rest get ` (2)`, ` (3)`
  before the extension (`numbered`). It runs before `leaving` is computed, since it can change an unchanged row.
  File > Rename tools > *Select bad names* (`SelectBadNames`, `Manager.bad_names`/`select_bad_names`, greyed when
  none) tags what it would change: `faults()` (BAD_UTF8/NFD/CONTROL) or `case_clashes()` per `entry.directory`.
  All asked for (convmv-style re-decoding, numbering, `_` for controls).
- **Order** (`steps`): a row whose new name is another row's old one goes through `.navrename-<n>-<old>` first, so
  swaps and cycles work. `run` (a `RenameJob` on a thread, through `_run_renames` -> `_watch_job`) re-checks
  `lexists` before each rename (never replaces), asks `filecopy.Failure` -> Skip/Cancel on an error, puts a stranded
  temporary back **only if its old name is still free**, else leaves it and says so.
- **Bookkeeping** is `Manager._after_renames(panel, [(place, old, new)], at=)`, shared with `_rename_entry` (Alt+F6,
  Shift+F6): listing entries renamed, tags follow, `FileSaved`, reload, the other panel re-read if it shows the place.
- **Undo** is File > Undo's (Ctrl+Z, *Undo* below): a batch goes on its history as one `undo.Renamed`, taken back
  through the same `run`. *Undo multi-rename* and `Manager.last_renames` are gone. File > *Rename tools* nests Quick
  rename and Multi-rename so File fits 80x25 with Undo.

## Undo (Ctrl+Z, File > Undo file operation)

A departure, asked for: DN had no undo outside its editors. `navigator/lib/file_ops/undo.py` is the model -- pure, no
I/O: `Renamed`, `Copied`, `Moved`, `Trashed`, `MadeDirectory` (each `question()` for the Yes/No, `undone()` for the toast) on
`UNDO`, the session's `History` (a stack, `LIMIT` 50, the oldest dropped; no Redo), shared by every Manager.
`conftest` clears it around each test.
- **What is recorded, where**: a copy or a move in `Manager._run_copy` from `CopyJob.copied`/`moved` (not into or
  out of an archive, so not Extract either, not Synchronize's `pairs`, not Undo's own copy -- `record=False`); Alt+F6/Shift+F6 in `_rename_entry`; Alt+A's
  batch in `multi_rename`; the Trash in `_run_erase` from `EraseJob.trashed` (the `trash.Item`s `_to_trash` got back);
  F7 in `make_directory`, every branch.
- **`CopyJob.moved` is the largest piece that went whole** (`_Copier._record`): a directory renamed, or made anew across
  devices and emptied (its children's pairs replaced by its own, from `mark`), is one pair; one merged into a
  directory already there leaves its children's. The destination is the one after an overwrite question's *Rename*.
  An append is never recorded; an overwrite counts in `job.replaced`, and the question says those cannot come back.
- **Undoing a copy removes only what is as it left it** (`navigator/lib/file_ops/uncopy.py`, reads only):
  `CopyJob.copied` is `(dest, fingerprint)`, a file's or link's type, size and mtime read after the copy, a directory
  made whole one record whose fingerprint lists everything under it (`collapse`, from its children's records; past
  `MANIFEST_LIMIT` none, and never taken back). A file copied over another counts in `overwritten`, an append is
  not recorded. `check` on a thread splits same/changed (gone is neither); the changed are said in one box (eight
  lines, *and N more*) and dropped; the same go through `_run_erase(record=False)`, `recursive`, to the Trash when
  on the disk whatever *F8 moves to Trash* says (`Copied.to_trash`; its *erase instead?* question where there is
  none), for good elsewhere -- the question says which.
- **Left out on purpose**: erases for good, attributes, links, archives, and what the desktop's
  `gio trash`/`kioclient` took (it names nothing back).
- **Undoing** (`Manager.undo`, spawned): asks, pops, then the worker that did it: `_run_renames`; the copier with
  `pairs` back, `MOVE`, `ASK`, `directories` for a source directory gone since; `trash.restore_all` (never over
  anything); `_undo_copy` above; `drive.rmdir` -- **only while empty**, Undo erases nothing (*NAME is not empty any more*, and dropped).
  What was skipped or stopped goes back on the history, smaller. Both panels reload, then a toast.
- **Ctrl+Z** is `Undo(by_key=True)` in `Manager.keys`, the command line's while it has text. Tests: `tests/test_undo.py`.

## Links (Shift+F5)

*File > Links > Create link…*, a departure: DN had no links, and the key was Split/combine's (`cmPanelLongCopy`), which is
back keyless (*Split / combine* below). `navigator/lib/file_ops/filelink.py` is the model, reading the target with `filecopy.resolve_target`. `LinkDialog` is Copy's
dialog cut down: a *Symbolic link* / *Hard link* radio (`kind`) beside one *Relative link* box, both remembered for the
session. `Manager.make_links` works with no worker thread and shares Copy's *Skip* box.

- **Hard links** (`LinkRequest.hard`, `filelink.make_hard_link`): `Drive.link(source, dest)`, `os.link(...,
  follow_symlinks=False)` -- `ln -P`, a symlink named is linked itself. Only where the drive `can("hardlink")`
  (`HARDLINK`: the disk, `root:`; the root helper's `link` op pins both paths); elsewhere *Hard link* is greyed
  (`can_hard`) and the model refuses `EOPNOTSUPP`. **A directory is refused with `EISDIR` before `link(2)` runs**: its
  `EPERM` would read as a refusal *As root* could get past (`refused()`), and root cannot either. `EXDEV` (another
  drive or file system) is put in words. *Relative link* is greyed while *Hard* is chosen (an effect on `kind`), and
  the prompt follows (`prompt_for(entries, hard)`, its hotkey `l`). SFTP (`hardlink@openssh.com`, not in paramiko)
  and the container drives (`ln`) could follow.
- **Show hard links** (`ShowHardLinks`, File > Links, keyless; the context menu on a file with `nlink > 1`):
  `navigator/lib/file_ops/hardlinks.py`'s `find_names` walks the file's file system from `filefind.mount_point` on a
  thread (`HardLinksJob`, `FindProgress` *Find hard links*, Stop), never entering another device, hidden names
  included, `DirEntry.inode()` compared before any `lstat`, **stopping once `st_nlink` names are found**. The names
  go into the panel as a *Links: NAME* `FindListing` (`keep_order`, the file's own first, the cursor on it through
  `show_found(at=)`); fewer found than `st_nlink` (an unreadable directory, a bind mount) is a toast. Refused off the
  disk, inside a listing, in Miller columns, on a directory and on a file with one name. A panel hiding dot-files
  hides those names too (`restat_found`). The *Links* column is `navigator-panels`'.

**Changing links already there** (File > *Links*, Create link's submenu now; no keys, all in
`Manager.keyless_commands`; *Edit link target* and the two *Make* also in the context menu when the selection holds a
link). A departure too. Enabled on links in `Manager.selected_links` (the selection's `is_link` entries) on a drive
that `can("symlink")` and `can("rename")`.
- **`filelink.retarget(drive, link, target)`**: a new link `.navlink-<n>` beside it, then `drive.replace` over it --
  never a moment without the name, a failure unlinks the temporary; refuses (`EINVAL`) a non-link. Every step on a
  thread (`Manager._retarget`), Skip/Cancel and *As root* as Shift+F5 has (`RootDrive.same_file` stats as root).
- **Edit link target** (`EditLinkTarget`): one link -> `LinkTargetDialog` (`file_ops/link_target_dialog`), the target
  in a line, *Relative link* rewriting the line in place (an effect on the box, the line `peek`ed); several ->
  `RelinkDialog` (`file_ops/relink_dialog`), *Search for*/*Replace with* over every target (`filelink.replaced`,
  pure), the `RelinkPreview` kept up by an effect, OK refused while nothing changes or a target comes out empty or
  with a NUL; the two lines kept for the session.
- **Make relative / Make absolute** (`LinkRelative`/`LinkAbsolute`): no box. `filelink.switched` reads from
  `link_base` -- the link's parent with links followed (`drive.realpath`), as the kernel reads a relative target, not
  the panel's path -- and rewrites by the letters; when the link reaches a file, the new target must reach **the same
  one** (`drive.same_file`, the new path joined with its `..` left in), else `NotTheSame` and it is left, said in one
  Error box (eight lines, then *and N more*). A broken link is rewritten by its letters alone. One already so is left
  silently. The changed and the already-so are untagged; the skipped keep their tags.
- **Broken links**: `DirEntry.is_stale_link` (link with its own `S_IFLNK` mode, what `!` shows). *Select broken
  links* (`SelectBrokenLinks`) adds their tags; Alt+F7's Advanced search has a fifth kind, *Broken link*
  (`filefind.KINDS`' `broken_link`; on another drive one `drive.exists` per link, asked only when the kind is
  wanted).

## In the background (copy, move, erase)

A departure, asked for: DN's `TWhileView` held the screen. `Manager._watch_job(..., background=, title=)` -- passed
by `_watch_copy` (bytes) and `_run_erase` (entries) only; Alt+E, UU, Test, Restore, multi-rename and Find stay modal.
- **The button** (`navigator/widgets/file_ops/background_button.py`): a box given `background` turns its `buttons` to
  `yes-no`, `ok` saying *Background* (the default: Enter sends it away) and `no` the old *Stop*/*Cancel*. `ok`
  answers the `BACKGROUND` sentinel; `no`'s False and Esc's None both mean Stop -> *Abort operation?*. (A derived
  half cannot define `on_no_click`: the generator refuses an `on_<id>_` for an id not in its own document.)
- **Away**, the box is gone and the job is a `Running` in `navigator/lib/system/background.py`'s `BACKGROUND` (loop
  only; `tick` copies `(done, total)` in). **A question waits**: taken from the worker and held, `asking` set, the
  worker blocked on its future, until `BACKGROUND.recall()` (the mark's click, Window > *Background operation*,
  `ShowBackground` -- with more than one away it opens `Shell.choose_background`, a `PopupMenu` of them numbered
  `~1~`.., the cursor on one waiting, else the newest) sets `recalled`; the box comes back up and then the question is put. Never a dialog over
  whatever the user is doing.
- **The mark** (`navigator/widgets/shell/job_mark.py`, `JobMark`): ` 42% `, one segment a job oldest first (` 10%|?20% `), each its own
  tooltip and click (`entry_at`, `BACKGROUND.recall(entry)`). The tooltip names the work by its `subject`
  (`job_subject`: *Copy photos to /mnt/backup*, *Erase 3 files*; fixed when it went away) and, indented under it, the
  file in hand (`current`, from *background*'s third value, `relative_to` the sources' directory) -- a snapshot,
  as every tooltip is read once when it appears; `?` and `JobMark::job:asking` mark a waiting question,
  right-aligned just before the window strip's first chip (`Shell.strip_start()`, from the strip's `chips()`/`hidden()`; with no chips or no strip,
  just before *ROOT*/the clock). The strip's `x` gives up the mark's width at its left while it shows, so the mark
  never reaches the menus.
- **The end**: only a job still away when it ends gets a toast, *title* over *Finished*/*Stopped* (`Shell.toast`,
  through `app.root`) -- not one that ended in its box (never sent away, or called back first), not after a failure,
  which has its own box, nor a cancelled watcher.
- **Desktop notification** (a departure, asked for; every `_watch_job`, background or not): once a box has been up,
  the end -- *Finished*/*Stopped*/*Failed: {subject}* under *title* (else the box's title) -- and each question taken
  from the worker (*Waiting for an answer*, once per question) go to `Shell.notify_away`, which sends only while
  `app.terminal_focused is False` and `[system] notifications` is not `off` (`navigator/lib/system/notify.py` maps the
  setting to navkit's way; `navkit-terminal`, *Focus reports and desktop notifications*). Not `run_with_progress`'s
  boxes. Tests: `tests/test_notifications.py`.
- **The window may be gone** when it ends (tasks are the application's): `_run_copy`/`erase_entries` reload only
  panels still mounted, and a question with no application is answered None (Esc).
- **Quitting** with anything away always asks (`_quit_asking`, in place of *Exit confirmation*); Yes is
  `BACKGROUND.stop_all()`. Tests: `tests/test_background_jobs.py`; `conftest` empties `BACKGROUND` around each.

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
  `main_menu.nml` binds the item's `hidden` to `Manager.shows_trash` of the bar's context) and the context
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

## Split / combine (File > Split/combine)

DN's `cmPanelLongCopy` (`FBB.PAS` `LongCopy`, `dlgSplitFile`/`dlgCombineFile`); `navigator/lib/file_ops/splitfile.py`
is the model, `SplitCombine` the command -- **keyless** (`Manager.keyless_commands`), since Shift+F5 is Create symlink's.
- **One command, the name decides** (DN's `Tuda`, `splitfile.mode_for`): `NAME.NNN` (three digits or more), or a
  `NAME.crc` beside its `NAME.001`, combines; anything else splits. Enabled as UU is: a file at the cursor.
- **Departures**: split by a size asked for (`parse_size`: `100M`, `1.44M`, `4G`, bytes; powers of 1024) where DN
  filled each floppy; headerless `NAME.001`, `.002`.. (`part_name`, `.1000` past 999) where DN wrote `.D01` behind a
  `Navigator Long Copy` header; and Total Commander's `NAME.crc` (`filename=`/`size=`/`crc32=`, `crc_text`/`read_crc`)
  where DN checked nothing -- so TC, Double Commander and 7-Zip combine what this splits and the other way. The dialog
  drops *Binary splitting only* and *Verify disk writes* for *Write checksum file*; size and box are `[split]`
  (`SplitData`), kept through `_keep_section`. Both dialogs share DN's `hsFBBCopy` history (`splitfile`).
- **Split** refuses a file no larger than one part; lists the target once and asks `uucode.FileExists`
  (Yes/No/All/Cancel; No or Cancel abandons before a byte is written) of each part or `.crc` there and of stale
  higher-numbered parts, which are removed once agreed. Parts take the source's mtime (`SetFTime(F2, OldDate)`).
- **Combine** reads `.001` on until a number is missing; with a `.crc` only the parts its `size` reaches (a stale
  later one is not read), *NAME is missing* when they fall short, an error when the size ends inside a part. The
  name is the `.crc`'s `filename`, else the base; the file takes the first part's mtime. **A CRC mismatch keeps the
  file** and says so; without a `.crc` nothing is checked.
- Stop or a failure removes what that run wrote (DN's `Erase(f2)`). Every read and write is `drive_of(...)`'s, so any
  drive works; `finish()` once. Run by `Manager._run_uucode` (`FileJob` under `WriteWin`, *Beep after copy* past
  20 s). *As root* is not offered yet. Tests: `tests/test_splitfile.py`.

## Checksums (File > Encoding > Checksums)

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

## Convert text (File > Encoding > Convert text)

`navigator/lib/file_ops/textconv.py`, **a departure, asked for** -- DN converted text only through the viewer's
XLT tables, so `ConvertText` is named for what it does and keyless, shaped as Encryption: `ConvertTextDialog`
(encoding or *Keep each file's*, *Read non-UTF-8 as*, line endings or *Keep*, *Keep file times*; the endings radio
has the first focus, Enter on a `ChoiceLine` dropping its list), `[text_conversion]` (`TextConversionData`),
`ChecksumProgress` through `Manager._run_checksums`, one summary box (`_say_conversion`: converted, already so, left
alone and why, failures). The encodings are the editor's (`navigator/lib/editor/encodings.py`: Unicode and every code page of
`navigator/lib/codepages.py`, CJK included), the line cut
`document.BREAK`.
- **What a file is read as** (`read_text`): its mark, else UTF-8 when it decodes strictly, else the chosen one-byte
  code page (strictly too) -- otherwise left alone as *undecodable*. A NUL in the first 8 KiB (not UTF-16) is
  *binary*; a character the target cannot write is *unencodable*, with its line:column; over `LIMIT` (256 MiB) *too
  large*. Output equal to the input is not written (*unchanged*), so its time stays.
- **Rewritten in place through its drive** (`_write`): `.NAME.navigator~` beside it, `chmod` to the old mode,
  `replace` over it, the temporary unlinked on any failure; a hard-linked file or one reached through a symlink is
  written into instead, so the links stay. *Keep file times* `utime`s the old times back. Every drive written to is
  `finish()`ed once at the end (an archive rewritten once). No Ctrl+Z undo yet.
- **As root** (`navigator-elevation`): a refusal on the disk is not an error but goes in `TextJob.refused`; after the
  pass `Manager._convert_as_root` asks `ask_as_root` once for all of them and runs `convert(..., as_root=True)` over
  those, every step through `ROOT_DRIVE`, releasing after. Declined or with no way to root they become failures.

## Encryption (File > Encoding > Encryption)

`navigator/lib/file_ops/encrypt.py`, **a departure, asked for** -- DN encrypted nothing, so `EncryptFiles` and
`DecryptFiles` are named for what they do and are keyless, like Checksums, whose shape it copies: `EncryptDialog`,
`[encryption]` (`EncryptionData`: tool, method, armor, delete_originals, recipients, age_identities -- never a
passphrase), `ChecksumProgress` through `Manager._run_checksums`, errors through `_say_checksum_errors(errors, heading)`.
- **Programs**: `gpg` and `age`, looked up with `shutil.which` at the call (`program`, `available`). A missing one is
  a greyed radio item with *install the gnupg/age package* in its tooltip; neither greys both commands
  (`Manager.refusal`). Decrypt is also refused when the selection holds no directory and no `.gpg`/`.pgp`/`.asc`/`.age`.
- **Names**: `name.gpg`, `name.asc` (gpg, armored), `name.age` (armored too); back to `name`, or `name.out` for a file
  with no such ending. A tagged directory is walked by `checksum.walk`; Encrypt skips files already encrypted.
  Decrypt confirms each file by its first bytes (`sniff`: age's magic or armor, PGP armor, an OpenPGP packet tag
  1/3/9/18/20) -- an `.asc` must hold a *message*, not a signature or a key.
- **Streaming, no temporary file**: `run_filter` feeds `drive_of(src).open_read` to the child's stdin on a thread
  and writes its stdout through `drive_of(dst).open_write`, so it works on any drive and leaves nothing in the clear
  in `/tmp`. `_drain` polls Stop with `select` every 0.1 s (age at a prompt writes nothing). Stop or failure kills
  the child's **process group** (each child leads a session: a helper holding the pipes would otherwise block) and
  unlinks the target. `_each` calls each target drive's `finish()` once, at the end (an archive is rewritten once).
- **A passphrase never goes in argv or the environment**, and no child can reach Navigator's terminal (each is
  started in a new session). gpg: `--batch --no-tty --pinentry-mode loopback --passphrase-fd N` (a pipe in
  `pass_fds`, written and closed before the start), `--no-symkey-cache` so a passphrase typed here does not go on
  unlocking files elsewhere; recipients get `--trust-model always` (the user picked them by name). age reads one
  only from `/dev/tty`: with `age-plugin-batchpass` (age 1.3) it is `-j batchpass` and `AGE_PASSPHRASE_FD`; without,
  age runs on a private pty made its controlling terminal (`_controlling`: `setsid` + `TIOCSCTTY` in `preexec_fn`) and
  `_Answerer` types the passphrase at each prompt. `navkit.process.PtyProcess` is the loop's and cannot be used there.
- **Decrypt asks only when it must**: every file is tried with no passphrase first (gpg's agent may hold the secret
  key; an age file to recipients uses `age_identities`, else `$XDG_CONFIG_HOME/age/keys.txt`). gpg's status lines
  decide: `NEED_PASSPHRASE*` with none given -> `job.needs_passphrase`, `BAD_PASSPHRASE` -> `job.bad_passphrase`; an
  age file is passphrase-encrypted when its header has an `scrypt` stanza (`age_wants_passphrase`). Then one
  `PasswordDialog` (*N files need a passphrase:*) for them all, retried with *The passphrase is wrong* up to three
  times. The encrypted files are kept.
- **Targets already there** are counted before anything runs (`existing_targets`) and asked about in one
  question. *Delete originals* (Encrypt only, off by default) unlinks each source whose copy was written in full.
- **The passphrase box's label is set after construction**: the markup's captions are yielding bindings, which
  give way to an assignment but override a keyword. `PasswordDialog` does this for its own `title=`.

## Replace in files (Alt+Shift+F7)

Find File's search with a replacing `match` (`navigator/lib/file_ops/filereplace.py`, `ReplaceQuery`); documented
with Find in the `navigator-panels` skill. Writes go through the editor's `save.write_file`, never in place.

## Read when

| Reference | Read when |
|---|---|
| `reference/copying.md` | copy/move model, dialog, progress and overwrite queries |
| `reference/symlinks.md` | symbolic and hard links, changing them, finding a file's names |
| `reference/deleting.md` | erase model, queries, recursion |
| `reference/file-attributes.md` | the attributes dialog and model |
