---
name: navml-library
description: navml's widget library outside windows and menus -- Control, Cluster, StaticText, Label, Button, InputLine, CheckBoxes, RadioButtons, ScrollBar, ListViewer, Modal, Dialog, Field, Spacer, Timer, ProgressBar, Spinner, navml.background, MaskedLine/MaskedField, DateField/TimeField/Calendar/TimePicker, ChoiceField, History/HistoryList, the layouts (Horizontal/Vertical/Grid/Dock/Stack), and building a dialog (including Navigator's About dialog). Use when writing or changing a dialog or a control.
---

# The widget library: dialogs, controls, layouts, history

**None of it was designed**: DOS Navigator's Colors dialog names the widgets and their states, `tools/palconv.py`
transcribed all 144 slots into every theme, and the *Dialogs* group is the specification. `navigator/styles/navigator.nss`
binds the components to the `$dialog-*` variables. Windows, the desktop and menus are the `navml-windows-menus` skill.

## The components

- **First tier** (`navml/widgets/dialog/`): `Control`, `Cluster`, `StaticText`, `Label`, `Button`, `InputLine`,
  `CheckBoxes`, `RadioButtons`, `ScrollBar`, `ListViewer`, `Modal`, `Dialog`, `Field`; plus `Spacer` and `Timer` at the
  top. `Timer` paints nothing and emits `TimerEvent` every `interval` ms; Navigator's `Clock`
  (`navigator/widgets/shell/clock/`, `HH:MM`, blinking colon, *Timer* slot `[1]`) is built on it.
- `Modal` is the framed, fixed, centred window (bound geometry, `modal = True`) and `Dialog` derives from it.
  `Dialog.buttons` has `ok`, `yes-no-cancel`, ...; `Dialog.valid()` (`Valid(cmOK)`) keeps a dialog up over a value it
  cannot read. F7 Mkdir was the first dialog wired into the application.
- `Button` emits `ClickEvent`; mouse and Space both go through one `press()`. Clicks act on release.
- **Arrows walk buttons** (a departure: `TButton` ignored them). Left/Up to the previous, Right/Down to the next,
  no wrap. The group is the unbroken run of buttons around the focused one in the dialog's tab order
  (`Button._row`), not a container -- most dialogs place buttons by `x`/`y` -- so keep a button row together in
  tree order, and any other control between buttons splits the run.
- `Cluster` lays out in columns as `TCluster` did. **Tri-state `CheckBoxes`**: `mixed` draws `[?]`, `tristate` lets a
  bit cycle back to it.
- `ListViewer` hooks: `capacity`, `index_at`, `render_items`, overridable `_follow_cursor`; `framed = False` drops the
  frame; it claims only a *bare* Enter.
- `StaticText.links` marks the `http(s)://` runs it paints (OSC 8, see `navkit-terminal`).
- **`OptionStrip`** (`navml/widgets/option_strip/`, Python only, not DN's): a window's *options* in a row, each an
  `OptionItem(command, label, lit=None)`. Lit is the command's `checks` (or `lit()`), greyed its `enables`, both asked
  of `target` (the widget whose options they are) through `navkit.commands` while painting -- any reactive write
  repaints, as for `KeyBar`. A left press on an enabled item runs `commands.run(app, command, target)`; every press is
  the strip's. Each item is drawn `[label]`, a cell apart, and nothing between: on a frame the border shows
  through (`═[⌶]═[§]═`). `spans`/`used_width` are computed from the labels' display width; bind `width: self.used_width` and give
  it `room` -- items that would pass it drop from the last. Part `item` with `:checked`/`:disabled`. Actions do not
  belong on it: those stay on menus and keys.
- **`ProgressBar`** (`navml/widgets/progress_bar/`): `value`/`total`/`percent`, as wide as placed, `█▒` from navkit's
  `GAUGES`. **`Spinner`** (`navml/widgets/spinner/`): one cell turning through navkit's `SPINNERS` every `interval` ms
  while mounted (`call_every`, as `Timer`); `frame` counts up. Navigator's `WriteWin` puts one beside its message.
- **`navml/background.py`'s `Background`**: a widget's slow read on a pool of threads, answered on the loop with an
  `Outcome` and the application woken to paint it; with no application running it answers on the spot. One pool per
  kind of read. `TreeView.probe_in_background` and `FileDialog.read_directory` use it.
- **`MaskedLine`/`MaskedField`**: digits typed into fixed places; Left/Right, Home/End, Backspace/Delete blank a digit;
  a base-8 `MaskedField` takes 0-7 only. **`DateField`/`TimeField`** are masked lines with a `Calendar` (TVDEMO's
  `TCalendarView` with a cursor; month/year picked from lists by click, `M`/`Y`, or Tab) or a `TimePicker` dropped by
  `▐↓▌` or Alt+Down; Up/Down step by the place under the caret, PgUp/PgDn by ten times that, carrying.
- **`CalendarView`** is the month without the drop-down: `Calendar` is `CalendarView` + `DropDown` with `inset = 1`
  (its frame) and `picked()` choosing; the view alone (`inset = 0`) answers `False` for keys it does not use, so Esc
  reaches its window. Styles name `CalendarView`, which matches both. Utilities > Calendar (`CalendarWindow`,
  TVDEMO's `TCalendarWindow`, a departure: DN 1.51 had no calendar) is one in a window.
- **`ChoiceField`** is a `ChoiceLine` (an `InputLine` never typed into: every key but Tab/Shift+Tab/Esc/Alt+letter/
  Up/Down drops its list, Enter included; Up/Down step between the dialog's lines) over **`History.choices`**, a fixed
  list that records nothing and that typing quick-searches by the panel's rule.
- **Every `InputLine`** selects with a drag or double click (a finished selection is the primary selection) and takes
  Ctrl+Ins (copy; the whole line with no selection), Shift+Del, Shift+Ins, Ctrl+C (only with a selection), Ctrl+V;
  middle click pastes the primary selection. A paste walks the focus path when `Application.on_paste` declines it.

- **`FileDialog`** (`navml/widgets/dialog/file_dialog/`, DN's `TFileDialog` from `DNSTDDLG.PAS`, every rectangle
  `TFileDialog.Init`'s): `FileDialog(title=, label=, history_id=, directory=, wildcard="*", hidden=, ok_text=)` (*ok_text* `"~O~pen"` is
  DN's `fdOpenButton`), `execute()`
  answering a full path or None. OK is `Valid(cmFileOpen)` (`valid()`): a wildcard or a directory re-lists and stays
  up, a name in an existing directory closes, anything else says *Invalid drive or directory.*/*Invalid file name.*
  An effect stands for `cmFileFocused`: the focused list fills the name line (a directory as `dir/` + wildcard) and
  `FileInfoPane`. Left/Right move between controls outside the name line; Tab skips an empty *Files* list; Enter or a
  double click in a list is OK; the history records the full path. `FileList` (`dialog/file_list/`, `TFileList` and
  `TDirectoryList` in one) types to search as `TSortedListBox` did; `scan()` is navml's own directory reader (navml
  may not import Navigator's). Departures: no drives, no 8.3 completion, `*` for `*.*`. Styled `FileInfoPane` in
  `navigator.nss` (the Information pane, [61]).

- **`ColorSelector`** and **`ColorDisplay`** (`navml/widgets/dialog/color_selector/`, Python alone): TV's
  `TColorSelector` -- `color` an index into `COLORS` (the attribute byte's sixteen, by name), `-1` for none, swatches
  of blanks on the colour with TV's `◘` mark (`*` on ASCII), arrows wrapping as `TColorSelector.HandleEvent` did; no
  event, the owner follows `color` -- and `TColorDisplay`, `text` repeated in `sample` (a `Style`).
- **`GroupBox`** (`navml/widgets/dialog/group_box/`): Turbo Vision's `ofFramed` view with a `TLabel` on its frame
  line -- a single frame (the sheet's `border`), `title` two cells in on the top edge with a blank either side (`~A~`
  in `::shortcut`), children placed inside in its own coordinates (the frame is the outer row and column). It never
  takes the keyboard. System Information's four boxes are the first users.

## History

`navml/history.py`'s `HistoryStore`/`HISTORY` is DOS Navigator's `HistList`: per-id lists, newest first, `limit` each (DN's 20; Navigator sets it from `interface.history_size`, default 50),
pinned entries kept (`HistoryStore.limit`). The `History` button drops a `HistoryList`, which `Field(history_id=...)` places after its line.
Ids in use: `"mkdir"`, `"select"`, `"command"`, ... Slots `[53-56]`. The lists persist: they are rows of the `history`
table (`navml/models/history_entry/`, DN's rules in its `.py` half's `remember()`), written as each change is made
(see `navkit-database`). Tests get an empty `:memory:` database each.

## Four rules from building dialogs (each found by running something)

- **A handler starts a dialog; it does not wait for one.** `await dialog.execute(app)` inside `on_key` mounts it and
  never paints it: `_main_loop` awaits `_handle` before rendering and is the queue's only consumer. Use
  `self.spawn(self._work())` and return. `Dialog.execute` raises rather than hanging.
- **A dialog's geometry must be bound, not assigned.** `add()` lays a child out into its parent and `Component.layout`
  steps around a side only when it carries a binding, so a literal size becomes full-screen the moment `overlay()` adds
  it. Route the size through a declared property the base binds from.
- **A derived component's own children land after its base's** (`super().__init__()` is the generated constructor's
  first line); `Dialog.focusable()` moves its buttons to the end, or every derived dialog opens with focus on OK, and
  `Dialog.activate_shortcut()` asks them last, or ~C~ancel takes Alt+C from *Compare ~c~ontents* (TV gave a shared
  letter to the control inserted first, and resources inserted buttons last).
- **Effects belong in `mounted()`, not `__init__`**, for any widget that can be removed and put back -- every widget in
  a dialog. `remove()` disposes a subtree's effects.

## Layouts

`HorizontalLayout`, `VerticalLayout`, `GridLayout`, `DockLayout`, `StackLayout` (`navml/widgets/layout/`), on a
Python-only `Layout` that paints nothing, replaced every container's placement arithmetic. A child asks for room with
**style hints the layout reads off the child** -- `basis`, `grow` (default 1, so silent siblings share evenly), `dock`
-- so a `style:` block or a sheet rule says it. A layout re-arranges from an effect on its own size, its children's
`visible` and hints, so a child's geometry is navigated and its markup says nothing about it. `Field` is
`Field(HorizontalLayout)`, `Shell` is `Shell(DockLayout)`, and `Dialog`'s buttons and `Manager`'s panels sit in an id'd
`HorizontalLayout`. All conversions paint `cmp`-identically on a pty.

## The About dialog

≡ > About is DN's `MessageBoxAbout` (`navigator/widgets/about_dialog/`): `Dialog` with `buttons: "ok"` and `message`
centred. Its facts are never written twice: `navigator/about.py`'s `project_info()` reads `pyproject.toml`'s
`[project]` in a checkout and the installed `METADATA` otherwise. The README screenshot shows it open, so a version bump
makes `tools/screenshot.py --check` stale. The home page is an OSC 8 hyperlink.

## Read when

| Reference | Read when |
|---|---|
| `reference/widget-library.md` | button drawing, `disabled`/`inert`, shortcuts, rows-are-not-widgets, the dialog rules in full, what came from `Panel`, where colours live, `Timer` |
| `reference/layouts.md` | layout hints and rules |
| `reference/history.md` | `HistoryStore`, `HistoryList`, `History.choices` |
| `reference/from-textual.md` | what the library takes from Textual |
