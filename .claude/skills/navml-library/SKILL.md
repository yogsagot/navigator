---
name: navml-library
description: navml's widget library outside windows and menus -- Control, Cluster, StaticText, Label, Button, InputLine, CheckBoxes, RadioButtons, ScrollBar, ListViewer, Modal, Dialog, Field, Spacer, Timer, ProgressBar, MaskedLine/MaskedField, DateField/TimeField/Calendar/TimePicker, ChoiceField, History/HistoryList, the layouts (Horizontal/Vertical/Grid/Dock/Stack), and building a dialog (including Navigator's About dialog). Use when writing or changing a dialog or a control.
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
- `Cluster` lays out in columns as `TCluster` did. **Tri-state `CheckBoxes`**: `mixed` draws `[?]`, `tristate` lets a
  bit cycle back to it.
- `ListViewer` hooks: `capacity`, `index_at`, `render_items`, overridable `_follow_cursor`; `framed = False` drops the
  frame; it claims only a *bare* Enter.
- `StaticText.links` marks the `http(s)://` runs it paints (OSC 8, see `navkit-terminal`).
- **`ProgressBar`** (`navml/widgets/progress_bar/`): `value`/`total`/`percent`, as wide as placed, `█▒` from navkit's
  `GAUGES`.
- **`MaskedLine`/`MaskedField`**: digits typed into fixed places; Left/Right, Home/End, Backspace/Delete blank a digit;
  a base-8 `MaskedField` takes 0-7 only. **`DateField`/`TimeField`** are masked lines with a `Calendar` (TVDEMO's
  `TCalendarView` with a cursor; month/year picked from lists by click, `M`/`Y`, or Tab) or a `TimePicker` dropped by
  `▐↓▌` or Alt+Down; Up/Down step by the place under the caret, PgUp/PgDn by ten times that, carrying.
- **`ChoiceField`** is a `ChoiceLine` (an `InputLine` never typed into: every key but Tab/Shift+Tab/Esc/Alt+letter/
  Up/Down drops its list, Enter included; Up/Down step between the dialog's lines) over **`History.choices`**, a fixed
  list that records nothing and that typing quick-searches by the panel's rule.
- **Every `InputLine`** selects with a drag or double click (a finished selection is the primary selection) and takes
  Ctrl+Ins (copy; the whole line with no selection), Shift+Del, Shift+Ins, Ctrl+C (only with a selection), Ctrl+V;
  middle click pastes the primary selection. A paste walks the focus path when `Application.on_paste` declines it.

## History

`navml/history.py`'s `HistoryStore`/`HISTORY` is DOS Navigator's `HistList`: per-id lists, newest first, 20 each,
pinned entries kept. The `History` button drops a `HistoryList`, which `Field(history_id=...)` places after its line.
Ids in use: `"mkdir"`, `"select"`, `"command"`, ... Slots `[53-56]`.

## Four rules from building dialogs (each found by running something)

- **A handler starts a dialog; it does not wait for one.** `await dialog.execute(app)` inside `on_key` mounts it and
  never paints it: `_main_loop` awaits `_handle` before rendering and is the queue's only consumer. Use
  `self.spawn(self._work())` and return. `Dialog.execute` raises rather than hanging.
- **A dialog's geometry must be bound, not assigned.** `add()` lays a child out into its parent and `Component.layout`
  steps around a side only when it carries a binding, so a literal size becomes full-screen the moment `overlay()` adds
  it. Route the size through a declared property the base binds from.
- **A derived component's own children land after its base's** (`super().__init__()` is the generated constructor's
  first line); `Dialog.focusable()` moves its buttons to the end, or every derived dialog opens with focus on OK.
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
