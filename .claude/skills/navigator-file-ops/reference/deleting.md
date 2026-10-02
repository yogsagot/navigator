### Deleting files

F8 and Del, *File > Delete*, port DOS Navigator's erase (`ERASER.PAS`, reached through `CM_EraseFiles`). The
three layers are Copy's.

- **The worker plumbing is shared.** `navigator/job.py`'s `Job` is what `CopyJob` used to be below its progress
  fields: the Stop `Event`, the pause `Event` that *Abort operation?* clears, one question at a time as a
  `Future`, and the `asker=` hook tests answer through. `CopyJob` and `EraseJob` add only the fields their boxes
  read, and `filecopy` still exports `Stopped` and `POLL`. On the loop side, `Manager._watch_job` is the old
  `_watch_copy` with the box, its refresh and the question answerer passed in. `_watch_copy` is now a call to it.
- **`navigator/fileerase.py`** is the model: `EraseRequest(sources, recursive)`, `EraseJob`, and `run` on a thread.
  It counts the entries first for the gauge, then removes depth first and never follows a link. A link to a
  directory is unlinked.
- **DN's rules are kept.**
  - An empty directory goes unasked.
  - A non-empty one asks `dlEraseDirNotEmpty` with **No / Yes / All / Cancel**, focus on No.
  - A file asks `dlEraseRO` with **Yes / No / All**.
  - *All* is one flag (`DeleteAllFiles`), so it silences both questions.
  - Cancel, or Esc on either question, stops the run.
  - What went is untagged and what was kept keeps its tag. Both panels re-read.
- **`DeleteDialog`** is `ValidErase`'s message boxes as one dialog: `Do you wish to delete` / `file NAME?`,
  `directory NAME?` or `these N files?`, with *Yes* and *No* (the base's OK and Cancel, relabelled). The focus
  opens on *Yes*. `EraseQuery` asks the two questions, placing its buttons with `slot()` because each kind puts a
  different one first. `DeleteProgress` is the `TWhileView` titled *Erase*.
- **Del and Shift+Del are bound `by_key`**, like Backspace's `GoParent`. They step aside while the command line
  has text, so Del deletes a character there and Shift+Del cuts. Shift+F8 and Shift+Del are `DeleteSingle`
  (`cmSingleDel`): the cursor's entry, whatever is tagged.

Departures:

- **One dialog, not two boxes.** DN asked `these files?` and then `OK to delete N files ?` (under
  `cfMultiErase`). The dialog carries the count, and it holds what a message box could not hold:
- **the *Recursive delete* check box.** It answers *All* to every *not empty* question before one is asked, but
  not the read-only question. It is off at the start and remembered for the session, as Copy's options are.
- **Read-only means the user cannot write the file**, since Linux has no attribute. This is also what makes `rm`
  ask about a *write-protected* file. DN asked only about the files it was handed. This asks inside a tree too,
  because a tree is where such a file hides.
- **A failure offers *Skip* / *Cancel*** (Copy's `_ask_skip`). DN showed an OK box for a file and gave up the whole
  run for a directory. A directory with something kept inside it is left alone without a second complaint.
- **The progress box has a gauge**, `N of M (P%)` over the counted entries, and its button says *Cancel*
  where DN's said *Stop*. It still asks *Abort operation?* before anything stops.
- **Not ported:** the direct FAT path, `.DIZ` descriptions, *Flush disk buffers*, and the `Confirms` word itself.
  Every confirmation is always on, which was DN's default.

