---
name: navigator-file-ops
description: File operations -- F5 copy and F6 rename/move (navigator/filecopy.py, CopyDialog, CopyProgress, OverwriteQuery), Shift+F5 symlinks (filelink.py, LinkDialog), F8/Del erase (fileerase.py, DeleteDialog, EraseQuery, DeleteProgress), Alt+E file attributes (fileattr.py, AttrDialog), F7 mkdir, Ctrl+F7/Ctrl+F8 UU encode/decode (uucode.py), the Job worker contract (navigator/job.py) and Manager._watch_job. Use when changing any operation over selected files.
---

# File operations

All live under `navigator/widgets/file_ops/` (dialogs, progress boxes, queries; commands in its `commands.py`), with
models in `navigator/`. Operations run on a thread through **`navigator/job.py`'s `Job`**, the worker contract
`CopyJob`, `EraseJob` and `AttrJob` share; **`Manager._watch_job`** is the loop that watches one. Progress boxes are
DN's `TWhileView` with the library's `ProgressBar`. Copied/erased entries are untagged and both panels re-read.

**Nothing that can wait on a disk runs on the loop.** A job that asks questions goes through `_watch_job`; one that
only reads or writes goes through **`navigator/progress.py`'s `run_with_progress(app, func, job, make_box, refresh)`**
(the viewer's search, the editor's reads and saves, F3's open, Alt+E's survey): the box after a delay
(`PROGRESS_DELAY`, or `SLOW_PROGRESS_DELAY` for file reads and writes, which use `WriteWin`), and the job stopped if the
task ends unfinished. Small reads a widget paints from (tree probes and counts, the quick view, the file dialog) use
`navml.background.Background`, one pool per kind so a dead mount cannot starve another. **What stays on the loop, on
purpose**: F7's mkdir, Shift+F5's symlink, Shift+F4's `is_dir` checks and ^K W's existence/chmod -- one syscall each on
a path the user has just named, where a thread hop would only reorder the dialogs around it.

## Copy and move (F5, F6)

DN's `FILECOPY.PAS`. `navigator/filecopy.py` is the model (`CopyRequest`, `CopyJob`, `run` on a thread; DN's five copy
modes, `MkName` masks, rename-first moves with an `EXDEV` fallback, `resolve_target`). `CopyDialog` is
`dlgCopyDialog`/`dlgRenameDialog` in one document, seeded with the passive panel's directory, F10/*Tree* picking it from
a tree, mode and options remembered for the session. `Manager.copy_files` puts up `CopyProgress` (*Stop* asks *Abort
operation?* with the copy paused) and `OverwriteQuery` (`dlgOverwriteQuery`) as the worker asks. **The check boxes are a
departure**: *Preserve attributes* and *Follow symlinks* stand where DN's *Verify disk writes* and *Copy descriptions*
stood, in the same bits. `Cluster`'s columns fit the four boxes in two rows.

## Symlinks (Shift+F5)

*File > Create symlink…*, a departure: DN had no links, and the key was Split/combine's (`cmPanelLongCopy`), which is
dropped. `navigator/filelink.py` is the model, reading the target with `filecopy.resolve_target`. `LinkDialog` is Copy's
dialog cut down, with one session-remembered *Relative link* box. `Manager.make_links` works with no worker thread and
shares Copy's *Skip* box.

## Erase (F8, Del)

DN's `ERASER.PAS`. `navigator/fileerase.py` (`EraseRequest`, `EraseJob`, `run` on a thread, depth first, **never through
a link**). `DeleteDialog` asks `Do you wish to delete` with a **Recursive delete** box (a departure, off by default,
remembered for the session). `EraseQuery` puts DN's *not empty* (No/Yes/All/Cancel) and *read-only* -- meaning not
writable -- (Yes/No/All) questions. `DeleteProgress` has a gauge and *Cancel*, which asks *Abort operation?*. Del and
Shift+Del are `by_key`, stepping aside while the command line has text; Shift+F8/Shift+Del (`DeleteSingle`) take the
cursor's entry whatever is tagged.

## File attributes (Alt+E)

DN's `cmSetFAttr` read for Linux (a departure: DN edited four DOS bits). What the dialog shows is gathered first on a
thread (`attr_dialog.gather`: every `stat`, and the user/group lists NSS may fetch from a directory server), under
*Reading file attributes* if slow, and passed in as `facts`. `navigator/fileattr.py` (`survey`,
`AttrRequest`, `AttrJob`/`run` on a thread, never through a link under recursion). `AttrDialog` is one dialog over every
tagged file, as `dlgFilesAttr` was: a twelve-bit grid with an octal line (a base-8 `MaskedField`, each digit setting its
three boxes), *User*/*Group* `ChoiceField`s, DN's *Date*/*Time* (`DateField`/`TimeField`), and *Recurse*. DN's Set/Clear
columns became **tri-state `CheckBoxes`**. **Only bits the user pressed are applied.** `Dialog.valid()` keeps it up over
an unreadable value.

## Make directory (F7)

The first dialog wired into the application; `Field(history_id="mkdir")`.

## Printing (Ctrl+F9)

`Manager.print_files`, DN's `CM_Print` -> `PrintFiles` (`FLTOOLS.PAS`, `GAUGES.PAS`): the selection
(`Manager.selection`, DN's `GetSelection`) less its directories -- nothing at all if that leaves nothing -- after
DN's *Print file NAME?* / *Print N files?* (N counting the directories, as DN's did). Each file goes to the spooler by
name (`navigator/printing.spool_file`: `lp`, else `lpr`, given the absolute path), standing for DN's print manager,
and is untagged once queued (`cmCopyUnselect`); a refusal stops the run, says why, and leaves the rest tagged.
`PrintFile` is the editor's F8 command too, so it lives in `navigator/commands.py`. File > Print sends it.

## UU Encode / UU Decode (Ctrl+F7, Ctrl+F8)

`navigator/uucode.py`, DN's `UUCODE.PAS`/`UUE2INC.ASM`, on the file at the cursor (`UuEncode`/`UuDecode`, enabled on
a file only); `Manager.uu_encode`/`uu_decode` -> `_run_uucode` (a `FileJob` under `WriteWin`, `_watch_job`, questions
by `_answer_uu_question`: `ExistsQuery` Yes/No/All/Cancel, errors as *Error* boxes).
- **Encode** is transcribed: `plan()` is `CalcLSsize`; one file a section (`NAME.uue`, else `.uu1`.. `.u10`.. `.100`);
  `section N of M of file NAME  < uuencode by Navigator >`; statistics, `filetime` (DOS packed time), `table`,
  `begin 644`; `UUXLT` with a backquote for 0; checksum levels cumulative -- entire `sum -r/size`, per-section
  `sum -r/size` over the counted lines plus `\n`, a check character per line (`GetLnCrc`), DN's `crc64`
  (`CRC64_START`, add-and-rotate). Every answer is kept in `[uucode]` and saved when it changes.
- **Decode** reads one file holding any files and sections in any order (a state machine, not a transcription of DN's):
  section headers, `table`, `filetime`, `begin`/`end`, `sum -r/size` checked, anything else passed over. A severe
  error breaks a file, written only with *Save broken files*; *Check existing files* asks; *Display error messages*
  shows each. Departures: names keep case and length; a blank line also ends the data; `crc64` is not checked.

## Read when

| Reference | Read when |
|---|---|
| `reference/copying.md` | copy/move model, dialog, progress and overwrite queries |
| `reference/symlinks.md` | symbolic links |
| `reference/deleting.md` | erase model, queries, recursion |
| `reference/file-attributes.md` | the attributes dialog and model |
