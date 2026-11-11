## Copying files

F5 and F6 are DOS Navigator's copy (`FILECOPY.PAS`). There are three layers, the viewer's and the editor's again:

- **`navigator/lib/file_ops/filecopy.py`** is the model. It imports no widget, and `run(request, job, cwd)` is the worker.
- **`CopyDialog`** (`navigator/widgets/file_ops/copy_dialog/`) is `dlgCopyDialog` and `dlgRenameDialog` in one document,
  titled by `move`, as `SelectDialog` is two resources in one.
- **`Manager.copy_files`** asks, runs the worker through `asyncio.to_thread`, and puts up `CopyProgress` (DN's
  `TWhileView`) and `OverwriteQuery` (`dlgOverwriteQuery`) as they are needed.

**The dialog is seeded as `CopyDialog` seeded it:**

- The prompt names what is copied: `Copy file NAME to`, `Copy Directory NAME to`, `Copy 3 files to`, or
  `Rename or move …` for F6.
- The line opens on the passive panel's directory (`cmPushFirstName`), with a single file's name after it.
- F6 on one entry with nowhere else to go opens on the bare name, which renames the entry in place.
- The copy mode and options are what the last accepted dialog said (`ccCopyMode`/`ccCopyOpt`), for this session
  only. *Remove source* is always F6's and never F5's.
- F10 and *Tree* open *Choose Directory* (`cmTree`), and the line becomes where the tree points.

**The prompt marks the name, and that took two library changes.**

- DN drew the name highlighted by switching `MoveCStr`'s toggle character to `#0`. Here `draw_caption` highlights
  every `~run~`, which is what Turbo Vision's `MoveCStr` did; only the first run is the shortcut.
- `caption_runs` and `parse_shortcut` share one reading, in which `~~` is a literal tilde inside a marked run as well
  as outside one. `escape_caption` doubles a name's tildes, so `a~b` is shown as itself.
- Along the way, DN's Copy prompt lost its `Alt+C`: the `#0` trick replaced the `~` that `dlFCCopyTo` spelled. Here
  `~C~opy` is the shortcut its string asked for, and Cancel carries no letter, as the resource's did not.

**The gauges are a `ProgressBar`** (`navml/widgets/progress_bar/`), taken from Textual's list when the copy needed
it: Textual's model (`value` out of `total`, and `percent`), DOS Navigator's look.

- **Why a widget.** `StrGrd` built its gauge as a string, and so did the first `SearchProgress` and `CopyProgress`: a
  `StaticText` holding thirty `█`/`▒`, fixed by a `GAUGE` constant. A string has a length where a widget has a width,
  so a box made wider kept its thirty-column gauge. A bar is as wide as whatever places it says.
- **What it is.** It is Python alone, like `CheckBoxes`: it declares values and paints.
- **Its glyphs** are navkit's `GAUGES` (`dos`, degraded to `#.` on an ASCII terminal), chosen by a `chars` sheet
  property, as a scroll bar's are.
- **Its colour** is `[38]` *Label normal*, which is what `TWhileView` drew it in: `GetColor(7)` of `CDialog`, and
  `CGrayDialog` maps entry 7 to 38, not to *Static text*'s 37. In `default` that is black on light grey: `█` black,
  and `▒` a black shade that reads as dark grey. The library carries no colour, so without the `navigator.nss` rule
  the bar inherited the dialog frame's white. The part done is a `done` part, so a sheet may colour it apart; DN
  never did.
- **What it leaves out.** The percentage and the byte count are for whoever places the bar, as `TWhileView`'s lines
  were.

**A cluster runs into columns**, as `TCluster.Column`/`Row` laid it out: a cluster shorter than its items runs down
one column and on into the next. That is how DN's four check boxes sat in two rows.

- A column is as wide as its longest caption, and the next starts two cells after it.
- Left and Right move a column. Radio buttons choose as they move, as Up and Down already did.
- Home and End go to the first item and the last, and radio buttons choose there too. Turbo Vision's `TCluster`
  had neither key; a dialog's other controls all take them.
- A cluster as tall as its items paints exactly as before.

**The worker and the loop share a `CopyJob` and nothing else:**

- plain fields the thread writes (the file in hand, bytes done, the total);
- an `Event` for *Stop*, and a second one that *Abort operation?* clears. DN's copy loop was the one asking, so
  nothing was copied while the question was up, and the same holds here.
- one question at a time, handed across as a `concurrent.futures.Future`. The worker blocks on it, polling
  `stopped` so that a Navigator quitting with a question up does not leave a thread waiting.

The loop side polls in a spawned task and paints through a `call_every` tick, as `FileWindow`'s search does. The
progress box appears after DN's two ticks (`PROGRESS_DELAY`, 2/18.2 s, `navigator/lib/system/progress.py`).

- **A box is cancelled, not closed.** A copy that ends between creating the box and its `execute` starting would
  otherwise mount the box afterwards and wait for ever. Found by a test, not by reasoning.

**The rules are DN's:**

- **The five modes** are the radio buttons' order: Overwrite, Append, Ask, Skip, and Refresh, which copies only
  over something older.
- ***Ask*'s answer can stand for every later file** for Overwrite, Append or Skip, and never for Rename. Rename asks
  in DN's `InputBox`, opened on the whole destination path (`P^.NewName`): a path typed there sends the file
  elsewhere, a bare name keeps it in the same directory, and a taken one asks again. Abandoned or left empty, the
  file is skipped (DN's `DoSkip`). The query's *File* line is that whole path, its middle cut to 40 (`Cut(NName,
  40)`).
- **A read-only target is written anyway** (DN's `TrySetArch`). For an Overwrite or an Append onto the user's own
  file whose owner write bit is clear, `_lift_read_only` sets the bit, the write goes ahead, and the old mode is put
  back: always for an Append (DN's `$FE`), and for an Overwrite unless *Preserve attributes* then gives the file the
  source's mode (DN's `$FF`). The overwrite question, or the mode chosen, is the confirmation. Somebody else's file
  cannot be changed, so its open is refused and *As root* is offered. A move renames over the file, which POSIX
  allows anyway.
- **An Append keeps the target's own time, mode and owner** (DN's `$FD`/`$FE`, which skipped `SetFTime` and the
  source's attributes), *Preserve attributes* or not: the file is the target's, written to now.
- **A failure removes only what that attempt wrote** (`_copy_bytes`' `wrote`): a half-written copy, as DN did. An
  open that failed leaves the target alone, so Skip never deletes the user's file.
- **A copy onto itself and a directory into itself are refused.** So is a file over a directory
  (`dlFCNotOverDir`). **A move onto itself is passed over without a word** (DN's `Exit` for `S1 = S2`,
  `FILECOPY.PAS:1809`), a file or a directory. A directory pasted or dropped into itself says so in an *Error* box
  (`erIntoItself`, `Manager._say_into_itself`).
- **A failure names its step**, as DN's boxes did, with the place and then the system's reason
  (`filecopy.step_failure`): *Could not open the file*, *read source file*, *create the file*, *write to file*,
  *Disk full* (`ENOSPC`/`EDQUOT`), *Could not rename file A / to B*, *create the directory*, *erase the file*,
  *delete the directory*, and Navigator's own *Could not read the directory*. A `stat` or an archive's finish
  keeps `name: reason`. *Not enough room* is DN's `erNotDiskSpace1`, titled *Error*, naming the target's mount
  point (or server) where DN named the drive letter (`NoRoom.drive`).
- **F6 to a bare mask in a *Find:* listing renames each file where it is** (DN's SoftMode, `cpoDirEmpty` with
  `cpoMove+cpoFromTemp`, `FILECOPY.PAS:2333, 1799`). `copy_entries` sets `CopyRequest.from_listing`, and
  `in_place_name` decides: no `/`, not an existing directory, a mask, or a plain name for one file. The listing takes
  the new names (`_rename_found`, as DN's `PFileRec(Own)^.Name`). F5 still copies into the origin, as DN's did.
  Undo puts the files back, but the listing drops them on its next re-read.
- **A move renames first.** On `EXDEV` it copies and then deletes, and stops trying to rename the directories
  beneath.
- **The target is read as `CopyDialog` read it:**
  - an existing directory, or a name ending in `/`, is where the files go;
  - a name with `*` or `?` is a rename mask (`MkName`, name and extension masked separately; a mask with no dot
    masks the whole name, a departure below);
  - otherwise it is a single file's new name, or for several a directory to create (a departure, below), asked about
    first (`dlQueryCreateDir`) only when Confirmations' *Create non-existing dir* is ticked, off by default.
- **What went is untagged; what was skipped keeps its tag.** Once the copy ends, and after Stop for what went
  whole; a directory only when all of it went. Both panels re-read afterwards.
- **A stopped file is removed** rather than left half-written.

**Departures:**

- **Tags clear when the copy ends, not one by one** as DN's `cmCopyUnselect` cleared them (`FILECOPY.PAS:1373,
  1635, 1769, 2174`). The end state is DN's, and a directory with a file skipped inside stays tagged, to be copied
  again.
- ***Flush buffers* `fsync`s each file as it is written** (`CopyRequest.flush`), before it counts and before a move
  across drives deletes its source. DN flushed once, at the end (`int 21h` `0Dh` under *Flushing buffers...*,
  `FILECOPY.PAS:2395-2424`), after `__Remove` had already deleted the sources.
- **A failure asks Skip / Cancel (and *As root*), and the copy goes on.** Every error ended DN's operation with one
  OK box.
- **The overwrite question comes before the room check**, and the check is made only where bytes will be written
  (item 1's rule). DN's `MaxWrite` ran first (`FILECOPY.PAS:1407-1418`), so a file then skipped had already been
  asked about.
- **A mask with no dot masks the whole name** (`apply_mask`), so `*` keeps `report.txt`. DN's `MkName` worked on
  `Norm12`'s 8.3 form, where a dotless mask had a blank extension: `*` stripped every extension and cut the stem to
  8. The `*` stays DN's positional one: it takes the source from its own position and ignores what follows it
  (`bak_*` on `report.txt` is `bak_rt.txt`).
- **Several files to a plain name that is not there make a directory of it.** DN split the line (`FSplit`,
  `FILECOPY.PAS:2509`) and kept a name that was no existing directory as the mask (`Mask := Nm+Xt`), so every file
  was copied to that one name, each over the last, and a copy of N files left one.
- *Verify disk writes* is *Preserve attributes*, and *Copy descriptions* is *Follow symlinks*. The bits keep DN's
  positions, so *Remove source* is still `$08`. This was the user's call:
  - the kernel verifies writes, and `descript.ion` is not a Linux convention;
  - preserving means `copystat`, plus the owner when running as root;
  - without *Follow symlinks* a link is recreated as a link, and a loop through a followed one is refused.
- *Preserve attributes* starts ticked. A Linux copy that loses its time stamps surprises, and DN's default of
  nothing ticked never had that option to weigh.
- `CopyProgress` shows the file and where it goes, the file's gauge, and the whole copy's gauge. DN's box read and
  then wrote in two passes and had a gauge for each; one pass needs one per file. DN's lines are kept: *Checking
  directories...* in the first row while the sources are counted (`job.measuring`), *File exists - skipped*, *Older
  file - skipped* and *Deleting source file...* over the speed row while they apply (`CopyJob.note`), and
  `dlFC_Total`, *Total N bytes*, on the bottom frame (`StaticText#frame-total`, the frame's colours). The row under
  the total gauge is the bytes done. A rename reads *Moving FROM / to TO*, DN's `DoRename` three lines in two.
- Not ported: `TEMP:` and `LINK:` targets, and DOS devices (`PRN`, `NUL`...). Ported: drag-and-drop
  (`Manager.on_dropped`, `_drop_menu`, *Drag-and-drop* in Confirmations), *Beep after copy*
  (`[file_manager] beep_after_copy`, rung by `_run_copy`), and a target inside an archive (`_open_target_archive`,
  the archive packed at the end, `job.packing`).
- **Split/combine is back**, keyless, as File > *Split/combine* (SKILL.md *Split / combine*), splitting by a size
  asked for. DN's `FBB.PAS` `LongCopy` (`cmPanelLongCopy`) spread a file too big for one floppy across diskettes;
  its key, Shift+F5, and its old menu slot are *Create symlink*'s.

