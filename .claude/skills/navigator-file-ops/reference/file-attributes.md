### File attributes

Alt+E, *File > File Attributes…*, is DOS Navigator's `cmSetFAttr`, and **a departure in what it edits**. DN's
`dlgFileAttr`/`dlgFilesAttr` set the four DOS bits (Archive, Hidden, Read-Only, System) and a date and time. None of
the four bits means anything on Linux. Here it edits the twelve mode bits, the owner and the group (in the spirit of
Midnight Commander's *Advanced chown*), and DN's own modification time. `CM_SetAttributes` itself is not in the 1.51
dump, so what DN's loop did is read off its two dialogs and their help.

- **`navigator/fileattr.py`** is the model:
  - `survey(paths)` works out what a selection has in common: the bits every file has, the bits they disagree on
    (`mixed`), and the owner, group and mtime where they agree.
  - `AttrRequest` holds `set_bits`/`clear_bits`, where a bit in neither is left alone. The owner, group and mtime
    are `None` to leave them, and `recurse` is `none`/`files`/`dirs`/`all`.
  - `AttrJob` and `run` work on a thread through `Manager._watch_job`. Failures go to Copy's *Skip*/*Cancel*, and
    the progress box is `DeleteProgress` retitled *Attributes*, which shows only for a long recursion.
- **One dialog over every tagged file**, as `dlgFilesAttr` was. DN gave each bit a *Set* column and a *Clear*
  column, and left a bit ticked in neither alone. Here that is one box with a third state: **`CheckBoxes.mixed`**
  draws `[?]`, and a bit in `tristate` cycles `?` → `X` → blank → `?`. This is Turbo Vision's `TMultiCheckBoxes`
  idea, and it lives in the library: `Cluster` asks `mark_char`/`mark_states`, so the `?` and a `:mixed` mark state
  are `CheckBoxes`' alone.
- **`AttrDialog`** (`navigator/widgets/file_ops/attr_dialog/`) lays out as follows:
  - the name and info rows;
  - one twelve-item `CheckBoxes`, three tall, which `Cluster` lays out as four columns (owner, group, others,
    special);
  - an *Octal* line with the `ls -l` spelling beside it;
  - *User* and *Group* as `ChoiceField`s the dialog's full width, chosen from the passwd and group
    databases and never typed into: any key drops the list, and typing searches it;
  - DN's *Date* and *Time*, as a `DateField` and a `TimeField`: typed, or picked from a calendar and a clock face
    (click the `▐↓▌`, or Alt+Down in the line), with Up and Down stepping the date or time with carry;
  - *Recurse*, disabled unless a directory is tagged.
- **Only what the user pressed is applied.** A bit counts once pressed, even when pressed back. An octal digit that
  changes anything claims all three of its bits, so `0644` typed means 644 on every file it reaches. Without this,
  a directory's `755` shown in the grid would give every file under a recursion an execute bit.
- **The octal line is a `MaskedField`**: a `MaskedLine` of four places in base 8, so it takes 0 to 7 and nothing
  else, and Up/Down/PgUp/PgDn step the mode as an octal number, carrying in eights.
  - **It reaches the grid a digit at a time.** A digit sets the three boxes it stands for and clears their `[?]`.
    A `?` or a blank place leaves them as they are.
  - Pressing a box rewrites the line, unless the line has the keyboard. In that case it is tidied when the keyboard
    leaves, so a place just blanked is not filled back in mid-edit.
- **Up and Down move between the lines**: Octal, User, Group, Date and Time, in that order. A disabled line is
  passed over, and at either end the key stays put. Octal, Date and Time keep the keys for themselves, so they move
  only from User and Group: on those three they step the mode, the date or the time, with carry. The grid and *Recurse* keep their own arrows. For this,
  `InputLine` now claims Down only when its button actually drops a list. A `Field` with no `history_id` still
  links its hidden button, and that had swallowed Down.
- **A click on a letter of the `rwxr-xr-x` beside the octal line presses its box.** Its nine letters are the
  grid's first nine items in the same order, so a click does what Space on that box would, `?` cycling included.
  The special bits show in the execute letters (`s`, `t`) but are pressed in the grid, and a click there presses
  the execute bit.
- **R, W and X press a box in the cursor's column**: that column's Read, Write or Exec, with the cursor moving to
  it, as `r`/`w`/`x` did in MC's *Advanced chown*. Shift does not matter, Alt stays the dialog's shortcuts, and
  in the special column the three do nothing. `AttrDialog` puts the handler in front of the grid's own
  (`bits.on_key`), so the arrows and Space are unchanged.
- **`Dialog.valid()`** is Turbo Vision's `Valid(cmOK)`. It was new here, and `on_ok_click` asks it before closing.
  An unknown user, a bad mode or a date that is not one shows an error and leaves the dialog up with the text in it.
- **Dismissing a changed dialog asks** *Changes will be lost. Are you sure?*, and only *Yes* lets it go. This is a
  departure, since DN dropped the dialog without asking. `Dialog` now has `Window`'s three halves:
  `must_ask()`, `ask_to_close()` and `request_close()`. Esc, the close icon (which goes through
  `Modal.request_close`) and a click outside go through `request_close()`. OK and the Cancel button never do:
  pressing Cancel already answers the question, so asking it again would be asking twice, and it closes at once.
  `AttrDialog.must_ask` compares every value against a snapshot taken when the dialog opened. So a box pressed
  and pressed back counts as no change, unlike `touched`, which counts it.
- **The question is the first `Dialog.buttons: "yes-no"`** (`mfYesButton + mfNoButton`): *Yes* and *No* with no
  Cancel. *Yes* answers True and *No* False, and Esc still answers `None`.
- **The rules:**
  - The owner goes first, because `chown` clears set-user-ID and set-group-ID, and the mode written after it puts
    back what was asked for.
  - A tagged link is followed, as the panel shows its target's mode.
  - Under a recursed directory a link is never followed and never changed.
  - A directory is changed after its contents, unless it cannot be read into now. Then it is changed first, because
    the change is presumably what lets it be read.
  - Untouched values mean *leave it*. A time equal to the one shown also means *leave it*, so OK on an untouched
    dialog does not round a nanosecond stamp to the second.
- **Only root may give a file to another user**, so *User* is disabled for anyone else, and greyed. DN's palette has
  no disabled slot for a label, a line or a cluster, so `navigator.nss` greys every disabled one in [44] *Button
  disabled*, the dialog's grey with dark text. *Group* offers all groups to
  root and the user's own groups to everyone else, which is all the kernel allows.
- **On the key bar as *Attr***, a departure: `StatusDef hcFilePanel`'s Alt row never carried Alt+E. At 80 columns
  the row now closes before *Exit*, as the Ctrl row closes before *Show*. Alt+X still quits; it is only uncaptioned
  there.

Not ported: `cmSingleAttr` (no key reached it in 1.51), F4 on a directory opening the dialog, and DN's single-file
`dlgFileAttr` as a separate shape. With one entry, the same dialog simply has nothing mixed in it.

