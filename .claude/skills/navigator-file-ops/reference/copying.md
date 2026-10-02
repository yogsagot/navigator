## Copying files

F5 and F6 are DOS Navigator's copy (`FILECOPY.PAS`). There are three layers, the viewer's and the editor's again:

- **`navigator/filecopy.py`** is the model. It imports no widget, and `run(request, job, cwd)` is the worker.
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
progress box appears after DN's two ticks.

- **A box is cancelled, not closed.** A copy that ends between creating the box and its `execute` starting would
  otherwise mount the box afterwards and wait for ever. Found by a test, not by reasoning.

**The rules are DN's:**

- **The five modes** are the radio buttons' order: Overwrite, Append, Ask, Skip, and Refresh, which copies only
  over something older.
- ***Ask*'s answer can stand for every later file** for Overwrite, Append or Skip, and never for Rename. Rename asks
  for the name in DN's `InputBox` and asks again if that name is taken too.
- **A copy onto itself and a directory into itself are refused.** So is a file over a directory
  (`dlFCNotOverDir`).
- **A move renames first.** On `EXDEV` it copies and then deletes, and stops trying to rename the directories
  beneath.
- **The target is read as `CopyDialog` read it:**
  - an existing directory, or a name ending in `/`, is where the files go;
  - a name with `*` or `?` is a rename mask (`MkName`, name and extension masked separately);
  - otherwise it is a single file's new name, or a directory to create for several (`dlQueryCreateDir`, always
    asked).
- **What went is untagged; what was skipped keeps its tag.** Both panels re-read afterwards.
- **A stopped file is removed** rather than left half-written.

**Departures:**

- *Verify disk writes* is *Preserve attributes*, and *Copy descriptions* is *Follow symlinks*. The bits keep DN's
  positions, so *Remove source* is still `$08`. This was the user's call:
  - the kernel verifies writes, and `descript.ion` is not a Linux convention;
  - preserving means `copystat`, plus the owner when running as root;
  - without *Follow symlinks* a link is recreated as a link, and a loop through a followed one is refused.
- *Preserve attributes* starts ticked. A Linux copy that loses its time stamps surprises, and DN's default of
  nothing ticked never had that option to weigh.
- `CopyProgress` shows the file and where it goes, the file's gauge, and the whole copy's gauge. DN's box read and
  then wrote in two passes and had a gauge for each; one pass needs one per file.
- Not ported: `TEMP:`, `LINK:`, archive and device targets; the drag-and-drop route; and *Beep after copy*.
- **Split/combine is dropped**, not deferred. It was `FBB.PAS`'s `LongCopy` (`cmPanelLongCopy`), which spread a file
  too big for one floppy across several diskettes and asked for each one. Linux has `split` and `cat` for what is
  left of that job. Its key, Shift+F5, and its File menu slot went to *Create symlink*.

