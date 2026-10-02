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
  `self.clock.visible = bind(lambda w: SETTINGS.interface.clock)`, as `Shell.__init__` does for the clock and key bar.
- **A per-widget value is seeded, not bound**, for example `Panel.show_hidden` (Ctrl+H toggles it) and
  `FileEditor.tab_size`. Read it in `__init__` after `super().__init__()`.
- **An operation reads the setting when it runs.** For example, `Manager.delete_files` reads `confirmations.erase_*`,
  and `Navigator.on_quit` reads `confirmations.exit`.

## Honoured now

| Setting | Effect |
|---|---|
| `system.internal_viewer` / `internal_editor` | Off: F3/F4 run `$PAGER` (default `less`) / `$EDITOR` (default `vi`) on the console |
| `system.show_hidden` | A new panel's `show_hidden` |
| `interface.clock`, `interface.hide_status_line` | Clock and key bar visibility |
| `confirmations.erase_single` / `erase_multiple` | Off: no Delete dialog, and so no *Recursive delete* |
| `confirmations.erase_non_empty_dir` / `erase_read_only` | Off: the eraser's question is answered Yes |
| `confirmations.create_dir` | Off: copy and link create a missing target directory without asking |
| `confirmations.exit` | On: Alt+X asks DN's `dlQueryExit` first |
| `editor.tab_size`, `editor.vertical_blocks` | Seed a new editor |
| `viewer.hex_mode`, `viewer.wrap_lines` | Seed F3's viewer |

Everything else is `honoured=False`.

## Tests

`tests/conftest.py`'s autouse `_default_settings` resets `SETTINGS` and points `XDG_CONFIG_HOME` into `tmp_path`, so
no test reads or writes the real file. Open a dialog in a test with `lambda a: a.spawn(a.run_command(InterfaceSetup))`.
Posting the command as an event does not reach the Shell.
