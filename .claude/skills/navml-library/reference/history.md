## History

An input line's history is two parts, and DOS Navigator's sources hold only one of them. `HISTLIST.PAS` is
Borland's `HistList` rewritten, and the three views — `THistory`, `THistoryWindow`, `THistoryViewer` — are Turbo
Vision's stock `Dialogs` unit, which is not in the dump. So the store follows DOS Navigator and the views follow
Borland.

**`navml/history.py` is the store**, `HistoryStore`, with one shared instance, `HISTORY`, where the original had one
`HistoryBlock`. It keeps a list of strings per *history id*: `"mkdir"` where DOS Navigator had `hsMakeDir`, a string
rather than a byte. Its rules are `HistoryAdd`'s:

- Newest first.
- A repeat moves to the front.
- An empty string is never recorded.
- **Twenty entries** (`MaxHistorySize`), the oldest unpinned one going first.

**Pinning** is DOS Navigator's addition. Every stored string carried a trailing `' '` or `'+'`; a `'+'` entry is
never evicted, and a string added again keeps its flag. The store saves to and loads from plain data
(`to_data` / `load_data`), so whoever owns a configuration file decides where it lives. Navigator does not persist
it yet.

**`History` is the button** (`navml/widgets/dialog/history/`), and every measurement is Turbo Vision's:

- It is three cells, `▐↓▌`, placed straight after its line, as a dialog script placed `History 44, 2, hsMakeDir`
  after `InputLine 2, 2, 44, 3`. The arrow uses slot [53] and the half-blocks [54]. An ASCII terminal gets `[v]`.
- A click, or Down in the linked line, **records what the line holds and then drops the list**. The list is one
  column wider than the line on either side, starts on the row above it, is eight rows tall, and is clipped to the
  modal the line is in. It opens on the **second** entry, because Turbo Vision's viewer did so unconditionally: the
  first is normally the text just recorded. With an empty line nothing was recorded, and the focus lands one entry
  older. That is Borland's behaviour, kept.
- Enter or a double click puts the entry into the line, selected whole so that typing replaces it. Esc leaves the
  line alone.
- **Down reaches the line, not the button**, because the line holds the keyboard and the button is not on the way
  up from it. So the button registers itself as `InputLine.history` when it mounts. That plain attribute is the
  one coupling, and the line imports nothing for it.

**The dropped list is a `ListViewer`** (`HistoryList`), made modal and overlaid. Turbo Vision composed a window, a
viewer and a scroll bar, and a `ListViewer` is all three already: its frame, its rows, and a bar on its right edge.
It is coloured as `CHistoryWindow` coloured it: frame and rows in the input line's own [50], the selected row
[51], and its scroll bar [55]/[56]. Turbo Vision's close icon on its frame is not drawn.

**Accepting a dialog records every line in it that has a history**, which is what Turbo Vision's `cmRecordHistory`
broadcast did: `Dialog.on_ok_click` walks the dialog for `History` buttons before it closes. Cancelling records
nothing. `Field` takes a `history_id` and puts the button after its line when one is given, which is how
Make directory got DOS Navigator's `hsMakeDir`.

**A button given `choices` drops those instead** (`History.choices`, aliased as `Field.choices`). Turbo Vision's
did not have this. It is for a fixed list the program hands in, such as the users and groups File Attributes offers.
It records nothing, because a list of choices is not a history. It opens on the entry the line already names,
rather than on the second one. Either `history_id` or `choices` shows the button. A history would not do: it is
capped at twenty, shared by id, and saved, and none of that suits a list read from `/etc/group`.

**Typing in a list of choices searches it** (`HistoryList.type_to_search`, set when the button has `choices`). It
uses the panel's quick-search rule (`navml/quick_search.py`): the row beginning with what was typed, case folded,
with `*` and `?` as wildcards. A new search looks from the top and a longer one from where it stands. A character
that would name nothing is refused, and Backspace takes one back. ` Search: … ` shows on the list's bottom edge with
the caret after it. Any other key ends the search and does its job. A history list does not search, as Turbo
Vision's did not.

**`ChoiceField` is the line that is chosen into and never typed into.** It is `Field`'s shape with a
**`ChoiceLine`** where the `InputLine` was: markup alone, a caption, the line and an always-shown `▐↓▌`, with
`choices` aliased onto the button. `ChoiceLine` is an `InputLine` underneath, so it looks, focuses and links like
one, but:

- every key it is offered drops the list, Enter included;
- the dialog keeps Tab, Shift+Tab, Esc, Alt+letter, and Up and Down, for a dialog that steps between its lines
  with them;
- a printable key also starts the list's search with itself;
- a click drops the list, a paste is refused, and there is no caret and no selection.

It is not Turbo Vision's, whose dialogs had only the input line and its history. It is the third shape a dialog
needs once a value must be one of a fixed list: a typo cannot happen, rather than being reported on OK.

**`DateField` and `TimeField` are lines with a picker behind the `▐↓▌`.** Both are markup alone, `Field`'s shape
with a `DateButton` or a `TimeButton` (each a `History`) where the history was. The line is a **`MaskedLine`**:
digits in fixed places, typed over. The button reads the line by its `date_format`/`time_format` (`strftime`'s spelling, `%d-%m-%Y` and `%H:%M:%S` unless
told), opens on that value or on now, and writes the choice back in the same spelling.

- **A click or Alt+Down drops the picker.** Down does not, because in a `MaskedLine` Up and Down step a digit.
  `InputLine` drops any button's list on Alt+Down as well as Down, Alt+Down being the drop-down key most toolkits
  since have used.
- **`MaskedLine` is an `InputLine` whose `mask` fixes its shape.** In the mask, `9` is a place for a digit and
  anything else is a literal. `mask_for` derives the mask from a `strftime` format of numbers, so `%d-%m-%Y` gives
  `99-99-9999`.
  - **`base` says which digits a place takes**: ten by default, eight for a file mode. The line then refuses `8`
    and `9`, and its plain stepping carries in that base.
  - A place may hold something else the program put there, such as `?` for *not known*. It is typed over like a
    blank and reads as 0 when stepped.
  - **`MaskedField`** is a caption and a `MaskedLine`: `Field`'s shape without the history button, markup alone.
  - A digit overwrites the place under the caret, and the caret moves to the next place, staying on the last.
  - Left and Right move between the places, and Home and End jump to the first and the last.
  - **Up and Down step the whole number** by the value of the place under the caret: one on the units, ten on
    the tens. **PgUp and PgDn step by ten times that.** The caret stays put, and the line's button decides what
    the step means.
    - **`DateButton.step` carries as a calendar does**: a day, a month (the day clamped to the month's last) or a
      year, or ten or more of them. `31-10` plus a day is `01-11`, `31-01` plus a month is `28-02`, and a step
      past year 9999 is refused.
    - **`TimeButton.step` carries as a clock does**, wrapping round the day: `23:59:30` plus a minute is
      `00:00:30`.
    - A line that does not read as a date or a time yet starts from today or now.
    - A `MaskedLine` without such a button treats the run of digits as a plain number, carrying within it and
      wrapping: `99` steps to `00`.
    - The line finds the button through `InputLine.history`, as Down finds a history. `masked_line.spans` says
      which directive covers a place.
  - Backspace and Delete blank the place under the caret. Delete leaves the caret there, and Backspace then steps
    it back a place, so held down it clears the line backwards. Blanking the last digit empties the line
    again, which is how *leave it* is said once something has been typed.
  - **Every other key is refused**, letters and pastes included.
  - The exceptions are the dialog's keys (Tab, Shift+Tab, Esc, Enter, Alt+letter), and Alt+Down, which drops the
    picker.
  - An empty line stays empty, showing only its separators, so *leave it* can still be said. The first digit
    fills the rest with blanks, and a reader of `value` refuses those as incomplete.
  - A click puts the caret on the nearest place, and there is no selection.
  - It is not Turbo Vision's: its input line took any text, and a validator judged it on OK.
- **`History.popup_origin`** places a fixed-size popup under the line, or over it when the screen has no room
  below, and pushes it in from the screen's edges. It is not clipped to the dialog as the history list is, because
  a calendar cut short would lose its weeks.
- **`Calendar`** is TVDEMO's `TCalendarView`, with a cursor added because the demo's only looked:
  - the layout: the month and year between `◄`/`►`, the weekday names, and six weeks;
  - keys: the arrows move a day or a week, PgUp/PgDn a month and Ctrl+PgUp/PgDn a year, Home/End go to the month's
    ends and `T` to today;
  - the mouse: a click on a day chooses it, and the arrows or the wheel turn the month;
  - **the month and the year are picked too**, which TVDEMO's could not do. A click on either name in the top row,
    or `M`/`Y`, drops a list over it: the twelve months, or two hundred years around the one shown. It is a
    `HistoryList` with `type_to_search`, so `19` finds the 1900s. Tab and Shift+Tab move the keys between the
    days, the month and the year. On the month or the year, Left and Right step it, Enter or Down drops its
    list, and Home and End go to January and December (on the year, to its first and last day). A pick puts the keys back on the days, so the next Enter chooses the day;
  - weeks start on Monday (`first_weekday`), where TVDEMO's started on Sunday.
- **`TimePicker`** is its companion and has no ancestor:
  - hours, minutes and seconds, with `▲▲`/`▼▼` over and under the number picked;
  - keys: Left/Right/Tab pick a number, Up/Down step it by one and PgUp/PgDn by ten, wrapping. Two digits set it and
    move on, and `N` is now;
  - the mouse: a click picks a number or steps it by its arrow, and the wheel steps the number under it;
  - a format without `%S` drops the seconds.
- Both are coloured as the history list is: [50] for the frame and values, [51] for the cursor, and [52] *Input
  arrow* for the month, the arrows, the weekdays and today.

