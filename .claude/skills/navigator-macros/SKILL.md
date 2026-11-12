---
name: navigator-macros
description: Macros -- DOS Navigator's key macros (DN.PAS KeyMacroses: Ctrl+J R 1..9 records every key and paste typed, anywhere, into a slot, any Ctrl+J R N stops; Ctrl+J 1..9 plays a slot) and its editor macros (MACRO.PAS TEditMacros, DN.HGL's MACRO blocks, here macros.ini, Ctrl+J 0 in the editor). navigator/lib/config/macros.py (Recorder, encode/decode, load/store, keys_of, settle, tokens/parse/parse_step, macros_for, read, resolve and DN_NAMES, editor_entries, play_steps), the KeyMacro model, RecordMacro/PlayMacro in navigator/commands.py and Navigator's handlers, SelectMacro in the editor, MacroMark (>MACRO<), Options > Macro file edit, navkit's Application.input_tap and Widget.takes_raw_keys, and 0x0A decoded as Ctrl+J. Use when changing either kind of macro.
---

# Macros

DOS Navigator had two kinds; Navigator has both (asked for), in `navigator/lib/config/macros.py`.

## Key macros (DN's `KeyMacroses`)

- **Keys**: `Ctrl+J R 1`..`9` records into slot N, and `Ctrl+J 1`..`9` plays it (`RecordMacro`/`PlayMacro` on
  `Navigator.keys`, the `global` table).
  - DN used Alt+Shift+N and Alt+N. That is a departure: Alt+digits are the file manager's quick directories (DN's
    own later bindings), and xfce4-terminal takes Alt+digit.
  - While recording, **any** `Ctrl+J R N` stops, as any Alt+Shift+digit stopped DN's.
- **Recording**: `Recorder.start` sets navkit's **`Application.input_tap`**, which sees every key and paste before
  anything handles it, anywhere. That includes dialogs (the app's table stands aside for a modal, so a chord can't
  start or stop recording inside one).
  - `_tap` notes where a chord may begin: a key arriving with no `app.chord` pending.
  - `stop`/`drop_chord` cut from there. However the chord is rebound, its keys are never in the recording.
  - Playing while recording records what is played, not the chord that played it, as DN recorded what its feed
    gave.
- **Playing**: `Recorder.play` posts each event and **`settle`s** between them (`not app.busy`, then a few loop
  turns, `SETTLE_LIMIT` at most). So a key that opens a dialog has the dialog take the next key, as DN's `GetEvent`
  feed did. A play started while one is running is refused (DN's `MacroPlaying`). `Navigator.macros` is the one
  recorder.
- **Kept in the database**: the `KeyMacro` model (`navigator/models/key_macro/`), `slot` unique and `keys` as JSON
  (`encode`/`decode`: key, char, ctrl/alt/shift/super_, or `{"paste": text}`). DN's lasted as long as its desktop.
- **`>MACRO<`** (`navigator/widgets/shell/macro_mark.py`, `MacroMark.slot`) is DN's clock word. It sits beside the
  clock rather than over it, before *ROOT*, in the bar's key colours, and the window strip ends before it. Its
  tooltip names the slot and the chord that stops recording.
- **Ctrl+J on a legacy terminal**: navkit decodes 0x0A as Ctrl+J (Enter is CR in raw mode; `navkit-terminal`).
- **Ctrl+J is a program's while one runs**: `Widget.takes_raw_keys()` is True for the console and a terminal window
  while busy, and then no chord starts (`navkit-widgets-input`).

## Editor macros (DN's `TEditMacros`)

- **Where they live**: DN read `MACRO name … ENDMACRO` blocks from `DN.HGL`'s file-type sections. Here they are in
  **`macros.ini`** beside `navigator.ini`.
  - It is `associations.MACROS`, seeded from `navigator/assets/macros.ini`, a commented template with examples.
  - Options > Configuration > *Macro file edit...* (`EditMacros`) opens it, as *Highlight file edit* does.
  - `[masks]` sections are separated by `;`, and `[*]` covers every file (DN's `DEFAULT`). `macros_for` gives every
    matching section's macros, in file order.
- **Line syntax** (`parse_step`, after DN's `Token`):
  - `'…'` strings, with `''` for a quote; outside quotes, `^X` is a control character and `#NN` a character code.
  - `PRINT text, n` is typed **as keys** (`keys_of`; DN's `TMacroString` sent key presses, so `^M` is Enter and
    goes through autoindent).
  - `GOTOXY x, y`, `GOTOX`, `GOTOY` count from 0 (DN's `ScrollTo`), through `FileEditor._go_column`.
  - `MARK n`/`GOTO n` set or jump to `FileEditor.markers`.
  - Anything else is a command with a repeat count.
  - `parse` reports a line it can't read or one outside a block, and leaves it out.
- **Command names** (`resolve`): `keybindings.ini`'s editor and edit-window names (`editor_entries`), DN's
  `MakeIDs` names (CamelCase, which `snake` turns into those, plus `DN_NAMES` for the irregular ones: `PgUp`,
  `DelChar`, `CtrlHome`, `UpBlock`…), or an editor command class constructible without arguments
  (`SwitchIndent`; DN's macro-only `LJustify`/`LRight`/`LLeft`/`LCenter` and the setters
  `InsertOn`/`InsertOff`/`IndentOn`/`IndentOff` are found this way), or `DN_COMMANDS`' other class name
  (`SpecChar` is `AsciiTable`). An unknown name is passed over, and the box says which.
  - Every one of `MACRO.PAS`'s 78 names resolves except `GoToMarker` (DN's macros passed no marker number) and
    `Center` (nothing in DN handled it); `tests/test_macros.py` holds the list.
- **Playing**: in the editor, **Ctrl+J 0** (`SelectMacro`, DN's `cmSelectMacro`, whose body was empty) lists the
  file's macros in a `PopupMenu`. `play_steps` runs them: a command through `app.run_command(binding, editor)`,
  settling between steps.
  - DN played them with Ctrl+J 1..9, which play key macros now.
  - There is no single undo group: each step undoes as typed.
