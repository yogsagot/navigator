---
name: navigator-file-ops
description: File operations -- F5 copy and F6 rename/move (navigator/filecopy.py, CopyDialog, CopyProgress, OverwriteQuery), Shift+F5 symlinks (filelink.py, LinkDialog), F8/Del erase (fileerase.py, DeleteDialog, EraseQuery, DeleteProgress), Alt+E file attributes (fileattr.py, AttrDialog), F7 mkdir, the Job worker contract (navigator/job.py) and Manager._watch_job. Use when changing any operation over selected files.
---

# File operations

All live under `navigator/widgets/file_ops/` (dialogs, progress boxes, queries; commands in its `commands.py`), with
models in `navigator/`. Operations run on a thread through **`navigator/job.py`'s `Job`**, the worker contract
`CopyJob`, `EraseJob` and `AttrJob` share; **`Manager._watch_job`** is the loop that watches one. Progress boxes are
DN's `TWhileView` with the library's `ProgressBar`. Copied/erased entries are untagged and both panels re-read.

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

DN's `cmSetFAttr` read for Linux (a departure: DN edited four DOS bits). `navigator/fileattr.py` (`survey`,
`AttrRequest`, `AttrJob`/`run` on a thread, never through a link under recursion). `AttrDialog` is one dialog over every
tagged file, as `dlgFilesAttr` was: a twelve-bit grid with an octal line (a base-8 `MaskedField`, each digit setting its
three boxes), *User*/*Group* `ChoiceField`s, DN's *Date*/*Time* (`DateField`/`TimeField`), and *Recurse*. DN's Set/Clear
columns became **tri-state `CheckBoxes`**. **Only bits the user pressed are applied.** `Dialog.valid()` keeps it up over
an unreadable value.

## Make directory (F7)

The first dialog wired into the application; `Field(history_id="mkdir")`.

## Read when

| Reference | Read when |
|---|---|
| `reference/copying.md` | copy/move model, dialog, progress and overwrite queries |
| `reference/symlinks.md` | symbolic links |
| `reference/deleting.md` | erase model, queries, recursion |
| `reference/file-attributes.md` | the attributes dialog and model |
