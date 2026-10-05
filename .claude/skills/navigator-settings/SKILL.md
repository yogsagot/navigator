---
name: navigator-settings
description: Navigator's settings -- navigator/settings.py (SETTINGS, Section, Setting, the DN-record sections), navigator.ini under $XDG_CONFIG_HOME/navigator, load_settings and --config in __main__.py, flag/env/ini/default precedence, saving one section through navml's Coder, and the Options setup dialogs in navigator/widgets/setup/ (System, Startup, Interface, Confirmations, Editor/Viewer, File Manager Setup, New Manager defaults). Use when adding a setting, reading one from a widget, or changing a setup dialog.
---

# Settings and navigator.ini

`navigator/settings.py` holds **`SETTINGS`**, the one `Settings` instance, a module singleton like `navml.history.HISTORY`.
It is a container of sections, `SETTINGS.interface.clock`, `SETTINGS.confirmations.erase_single`, and so on.

## The file

- **Where it lives.** `$XDG_CONFIG_HOME/navigator/navigator.ini`, or `~/.config/navigator/navigator.ini`; a relative
  `XDG_CONFIG_HOME` is ignored. `--config PATH` overrides both.
- **Startup.** `main()` calls `load_settings()`:
  - a missing file is written with every default, then read
  - a value that will not parse keeps its default, with a stderr warning before the screen is taken
  - a file that is not ini at all, or cannot be written, means defaults for the session
- **No disk in `Navigator.__init__`.** Loading happens only in `main()`, so tests that build `Navigator` directly never
  touch the disk.
- **An ini file is a departure.** DN kept a binary `DN.CFG` of tagged records (`DNUTIL.PAS` `WriteConfig`). The module
  docstring records why.
- **Writing.** `Settings.render()` writes through `navml.coder.Coder("ini")`, and `save()` writes it atomically
  (`mkstemp` in the same directory, then `os.replace`).
- **`save(section=name)` re-reads the file first** and replaces only that section. A hand edit made while nav runs
  survives a dialog's OK.
- **What survives a save, and what doesn't.** Unknown keys and sections are kept verbatim (`Settings.extras`). Comments
  written by hand are not: the generated ones replace them.
- **Layout.** A section's comment goes on the line right under its `[section]` header. An option's comment goes on the
  option's own line, starting at `COMMENT_COLUMN` (44), or two spaces after a longer `key = value`.
- **No ` #` or ` ;` inside a value.** The parser is built with `inline_comment_prefixes=("#", ";")` so that those
  comments are stripped when reading. That also means everything from ` #` or ` ;` on is read as comment.

## Precedence

For `[appearance]`, the order is **flag > `NAVKIT_*` environment variable > ini > built-in default**.

- The argparse defaults for `--theme`, `--palette`, `--glyphs` and `--dim-modal` are `None`, so the code can tell
  whether a flag was given.
- The ini's palette and glyphs go into `TerminalInfo.detect()` as its defaults, which lets `NAVKIT_PALETTE` and
  `NAVKIT_GLYPHS` still override them.
- A flag is applied over that result. It is session-only and never saved.
- An unknown theme in the ini warns and falls back to `default`. An unknown `--theme` is still an argparse error.

## Declaring a setting

- **Declare it as a field.** A section is a `Section` subclass whose fields are `Setting(default, doc=...,
  choices=..., honoured=...)`, a `navkit.reactive.Reactive` subclass. The schema comes from the class:
  - the attribute name is the ini key
  - the default's type (bool, int or str) is how the value parses
  - `choices` limits a string
  - `doc` is the comment written above the key
- **A setting nothing reads yet is `honoured=False`.** The ini comment then says "stored, not yet honoured". When you
  wire one up, drop the flag.
- **Field order matters.** Fields keep DN's dialog order. Tuples on the class (`OPTIONS`, `BEHAVIOR`, `DISPLAY`, ...)
  list a `CheckBoxes`' items in bit order. `to_bits(names)` and `from_bits(names, value)` convert between those fields
  and `CheckBoxes.value`.
- **Sections are named after DN's records**, the dialogs after DN's `dlg*` resources, and the commands after DN's `cm*`:

| Section | Class (DN record) | Dialog (`navigator/widgets/setup/`) | Command |
|---|---|---|---|
| `[appearance]` | `AppearanceData` (the flags) | none | none |
| `[system]` | `SystemData` | `SystemSetupDialog` (`dlgSystemSetup`) | `SystemSetup` |
| `[startup]` | `StartupData` | `StartupDialog` (`dlgStartupSetup`) | `StartupSetup` (`cmStartup`) |
| `[interface]` | `InterfaceData` | `InterfaceDialog` (`dlgInterfaceSetup`) | `InterfaceSetup` |
| `[confirmations]` | `ConfirmsData` | `ConfirmationsDialog` (`dlgConfirmations`) | `SetupConfirmation` |
| `[editor]` + `[viewer]` | `EditorDefaultsData`, `ViewerDefaultsData` | `EditorDefaultsDialog` (`dlgEditorDefaults`) | `EditorDefaults` |
| `[file_manager]` | `FMSetupData` | `FMSetupDialog` (`dlgFMSetup`) | `FileManagerSetup` (`cmFMSetup`) |
| `[panel_defaults]` | `PanelDefaultsData` | `FMDefaultsDialog` (`dlgFMDefaults`) | `FileManagerDefaults` (`cmFMDefaults`) |

`FMSetup` would be handled by `on_f_m_setup`, which is why those two commands are spelled out.

**DOS-only items are left out** of both the ini and the dialogs:

- XMS/EMS
- the video modes
- overlays
- Int28
- the CD player
- the per-drive list
- *"Fast" command execution* and *Advanced copy*
- *Enable blinking* and the *Timeslicing* group
- the *Drive line*, *Alt/Ctrl difference*, the *Quick search* key, and `descript.ion` descriptions

The keys an older `navigator.ini` may still hold are listed in `settings.OBSOLETE`. `Settings.load()` drops them
without a warning, so the next save leaves them out of the file. Unknown keys, by contrast, are kept as extras. A
choice that was renamed (`sort_by = group`, `left_panel = drive`) is mapped by `Setting(aliases=...)` and written
back under its new word.
- *Restore screen mode*
- the VGA palette boxes
- *OS-dependent disk access*
- *Clear read-only from CD*

Screen savers, Printer, Country, Mouse, Communications and Terminal stay greyed in the menu.

**Defaults are DN's** (`STARTUP.PAS`) except where Navigator already behaved otherwise. Each exception carries a `#:`
note:

| Setting | Default here | DN's default |
|---|---|---|
| `show_hidden` | on | off |
| `hide_menu_bar` | off | on |
| `bs_upper_dir` | on | off |
| `sort_by` | name | extension |
| `line_divisor` | lf | crlf |

## The dialogs

- **What a dialog does.** Each is a two-half component. `__init__` seeds the controls from its section (an optional
  section argument, else `SETTINGS.<name>`). `accept()` returns `{key: value}`. `EditorDefaultsDialog` covers two
  sections and returns `{"editor": {...}, "viewer": {...}}`.
- **What OK does.** `Shell.setup(dialog, *sections)` spawns the dialog, assigns the answer onto `SETTINGS` (reactive,
  so bindings repaint), then calls `SETTINGS.save(section=...)`. An `OSError` shows an *Error* box, and the values stay
  applied for the session.
- **Numbers are three-digit `MaskedField`s.** Width is the label plus 5: three digits and the line's two columns.

## Reading a setting from a widget

- **Markup cannot bind to `SETTINGS`.** navml evaluates a property line once if it reads nothing of its widget, so
  `visible: SETTINGS.interface.clock` would be read at construction and never again. Bind in Python instead:
  `self.clock.visible = bind(lambda w: SETTINGS.interface.clock)`, as `Shell.__init__` does for the clock, the key bar,
  the command line and the menu bar.
- **The menu bar comes after the desktop in `shell.nml`** so a floating bar paints over it. Its `width`/`height` are
  bound to the top row, which docked or floating it keeps; `Shell.__init__` binds its `inline_style` (`dock: top` or
  `dock: none`) and its `visible` (`not hide_menu_bar or current >= 0`).
- **A per-widget value is seeded, not bound**, for example `Panel.show_hidden` (Ctrl+H toggles it) and
  `FileEditor.tab_size`. Read it in `__init__` after `super().__init__()`.
- **An operation reads the setting when it runs.** For example, `Manager.delete_files` reads `confirmations.erase_*`,
  and `Navigator.on_quit` reads `confirmations.exit`.

## Honoured now

| Setting | Effect |
|---|---|
| `system.internal_viewer` / `internal_editor` | Off: F3/F4 run `$PAGER` (default `less`) / `$EDITOR` (default `vi`) on the console |
| `system.show_hidden` | A new panel's `show_hidden` |
| `system.system_clipboard` | On (a departure: DN's default was off): copies go to OSC 52 and the desktop's tool, pastes read them. Off: `Application.system_clipboard` false, a clipboard private to Navigator (`Shell._choose_clipboard`, an effect) |
| `system.flush_buffers` | Copy and a cross-device move `fsync` each file written (`CopyRequest.flush`, set by `CopyDialog.accept`) before it counts as done or a move deletes its source; a sync error fails that file like a write error. `EINVAL`/`ENOTSUP` (a file system with nothing to sync) is not an error. A rename-move writes nothing, so syncs nothing |
| `system.internal_terminal` | Off: Ctrl+O hands the real terminal to the shell, as Midnight Commander does, and commands from the line run there (a departure: not DN's; `console-command-line` has the mechanism). Also a System Setup box, *Use internal terminal* |
| `interface.clock`, `interface.hide_status_line` | Clock and key bar visibility |
| `interface.hide_menu_bar` | The desktop takes the top row; the bar floats over it only while a menu is open |
| `interface.hide_command_line` | The desktop takes its row; it takes no keys, and its commands (Enter, Home, End, Tab, Ctrl+Enter) are disabled so those keys go to the panel |
| `interface.auto_hide_command_line` | The line shows only while it holds text; typing still goes to it and brings it back (DN 1.51 never read this bit -- transcribed from `CheckSize`/`ToggleCmdLine`) |
| `interface.esc_user_screen` | Esc with an empty command line toggles the console (Ctrl+O), DN's `cmShowUserScreen`; Esc on a line with text clears it, and does nothing with the line hidden |
| `interface.block_insert_cursor` | The command line's caret is a block (`Shell:block_insert { caret: block }` in `navigator.nss`; on `Shell` because it answers `cursor_position` for the line). Unticked, the terminal's own shape |
| `interface.track_viewing` / `track_editing` | On (a departure: on by default): viewers/editors are recorded and restored, and Alt+PgDn / Alt+PgUp list them; off, the lists say DN's `dlSetViewHistory`/`dlSetEditHistory` (`navigator-viewer`, `navigator-editor`) |
| `interface.store_viewer_position` / `store_editor_position` | On (a departure, as the Track pair): a tracked file reopens at its recorded window rectangle, scroll and cursor. Off, it is still recorded and listed, and its mode/wrap/filter (viewer) or insert mode/vertical blocks (editor) still come back, but it opens at the top in a fresh window. Without Track there is no record, so nothing to restore |
| `interface.history_size` | 50 (a departure: DN fixed 20): entries kept per history list -- `HISTORY.limit` (set by `Shell._size_histories`) and `FileRecord.store`. A `MaskedField` under Interface Setup's boxes |
| `confirmations.erase_single` / `erase_multiple` | Off: no Delete dialog, and so no *Recursive delete* |
| `confirmations.erase_non_empty_dir` / `erase_read_only` | Off: the eraser's question is answered Yes |
| `confirmations.create_dir` | Off: copy and link create a missing target directory without asking |
| `confirmations.exit` | On: Alt+X asks DN's `dlQueryExit` first |
| `editor.tab_size`, `editor.vertical_blocks` | Seed a new editor |
| `editor.auto_brackets` | Seeds a new editor's *AutoBrackets* (Editor > Options switches one editor's) |
| `editor.autowrap` / `justify_on_wrap` | Seed a new editor's *Auto wrap* and *Justify on wrap* (Editor > Options switches one editor's) |
| `editor.left_margin` / `right_margin` / `paragraph` | Seed a new editor's `margins` for paragraph formatting (Alt+J/R/L/C); *Format Margins* changes one editor's alone |
| `viewer.hex_mode`, `viewer.wrap_lines` | Seed F3's viewer |
| `editor.line_divisor` | The terminator a text with no line break yet takes (`FileEditor.open` sets `Document.newline` from `document.NEWLINES`): a new file, an empty one, a single line. A file with breaks keeps its most common one |
| `editor.persistent_blocks` | On (DN's default): the block stays as the cursor moves and edits go round it. Off: a movement without Shift unmarks, typing, Enter, Tab and a paste replace the block (one undo), Backspace and Del delete it alone |
| `editor.auto_indent` | Enter indents the new line as the one it split (`on_new_line`, DN's `MakeEnter`) |
| `editor.backspace_unindents` | Backspace with only blanks before the cursor goes back to the indent of the nearest shallower line above (column 0 if none), deleting the blanks between, one undo step (`FileEditor._unindent`). The Borland IDEs' meaning, DN's source not being to hand. Inside a tab, or past the end of a line with text, it is the plain Backspace |
| `file_manager.space_toggles_selection` / `bs_upper_dir` / `del_erases` | Space tags, Backspace goes up, Del erases while the command line is empty; off, the command is disabled in `Shell.enables`/`Manager.enables` so the key falls through to the line. Shift+Backspace/Ctrl+PgUp and F8 are unaffected |
| `file_manager.column_titles` | The detailed and list modes' heading row (`Panel._follow_column_titles`, an effect, so it applies at once); the dividers stay |
| `file_manager.tag_character` / `tag_sign` | The tagged row's gutter mark: `tag_sign`'s first character (empty: `√`; `+` on the ASCII tier when it is not ASCII); off, the colour alone |
| `panel_defaults.files_highlight` | File-type row colours (`Panel.row_style`) |
| `panel_defaults.current_file` / `selected_files` | What the panel's info line (its footer) may show; neither, it is empty |

The `panel_defaults` above are read live by every panel, a departure: DN copied *New Manager defaults* into each
manager it made. `file_manager.info_divider` stays unhonoured because the info line is the frame's footer, with no
divider to drop.

Everything else is `honoured=False`.

## Tests

`tests/conftest.py`'s autouse `_default_settings` resets `SETTINGS` and points `XDG_CONFIG_HOME` into `tmp_path`, so
no test reads or writes the real file. Open a dialog in a test with `lambda a: a.spawn(a.run_command(InterfaceSetup))`.
Posting the command as an event does not reach the Shell.
