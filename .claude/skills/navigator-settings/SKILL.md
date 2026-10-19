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
  and `CheckBoxes.value`. A departure's checkbox goes last, so the original options' bits stay put:
  `[editor] show_options` / `[viewer] show_options` (the option strip, on by default, bound live by the windows'
  markup as `SETTINGS.editor.show_options`). `show_hidden` in both sections has no checkbox (as `syntax_highlight`);
  it seeds each new editor/viewer, which Editor > Options / View switch.
- **Sections are named after DN's records**, the dialogs after DN's `dlg*` resources, and the commands after DN's `cm*`:

| Section | Class (DN record) | Page (`navigator/widgets/setup/`, DN's dialog) | Command (opens that page) |
|---|---|---|---|
| `[appearance]` | `AppearanceData` (the flags) | none | none |
| `[system]` | `SystemData` | `SystemSetupPage` (`dlgSystemSetup`) | `SystemSetup` |
| `[startup]` | `StartupData` | `StartupPage` (`dlgStartupSetup`) | `StartupSetup` (`cmStartup`) |
| `[interface]` | `InterfaceData` | `InterfacePage` (`dlgInterfaceSetup`) | `InterfaceSetup` |
| `[confirmations]` | `ConfirmsData` | `ConfirmationsPage` (`dlgConfirmations`) | `SetupConfirmation` |
| `[editor]` + `[viewer]` | `EditorDefaultsData`, `ViewerDefaultsData` | `EditorDefaultsPage` (`dlgEditorDefaults`) | `EditorDefaults` |
| `[file_manager]` | `FMSetupData` | `FMSetupPage` (`dlgFMSetup`) | `FileManagerSetup` (`cmFMSetup`) |
| `[panel_defaults]` | `PanelDefaultsData` | `FMDefaultsPage` (`dlgFMDefaults`) | `FileManagerDefaults` (`cmFMDefaults`) |
| `[drive_info]` | `DriveInfoData` | `DriveInfoPage` (`dlgDriveInfoSetup`) | `DriveInfoSetup` |
| `[column_defaults]` | `ColumnDefaultsData` (`ColumnsDefaults`) | `ColumnDefaultsPage` (`dlgColumnsDefaults`) | `ColumnDefaults` (`cmColumnDefaults`) |
| `[savers]` | `SaversData` (`TSaversData`) | `SaversPage` (`TSaversDialog`, built in code in DN) | `SaversSetup` (`cmSaversSetup`); ≡ > Screen rest is `ScreenRest` |
| `[uucode]` | `UUCodeData` (`TUUEncodeData`, `UUDecodeOptions`) | `UUEncodeDialog`, `UUDecodeDialog` (`dlgUUEncode`, `dlgUUDecode`, under `file_ops/`) | `UuEncode`, `UuDecode` -- saved by `Manager._keep_uucode`, not `Shell.setup` |
| `[highlight_groups]` | `HighlightGroupsData` (`CustomMask1`..`5`) | `HighlightPage` (`dlgHighlightGroups`) | `HighlightGroups` (`cmHighlightGroups`) |

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

- **One dialog, a page per section.** Options > Settings (`SettingsDialog`, `navigator/widgets/setup/settings_dialog/`,
  command `Settings`) holds the eleven setup pages behind navml's `TabView`. Each menu item under Options >
  Configuration and Options > File Manager, and its command, still exists and opens it on its own page
  (`Shell.settings(tab)`). This is a departure: DN had a resource to each. Colors and Key bindings stay dialogs of
  their own.
- **What a page does.** Each is a two-half component on a plain `Widget` (`*_page/`, `XPage`), laid out as the dialog
  it was, from `y: 1` (row 0 is the tab rule). `__init__` seeds the controls from its section (an optional section
  argument, else `SETTINGS.<name>`). `accept()` returns `{key: value}`. `EditorDefaultsPage` covers two sections and
  returns `{"editor": {...}, "viewer": {...}}`. Its tab caption (`title`) is given by `settings_dialog.nml`, where a
  literal is translated live.
- **Pages by id.** `settings_dialog.PAGES` maps each page id (`interface`, `editor_viewer`, ...) to its sections, and
  `SECTIONS` lists them all. Reach a page's controls as `dialog.interface.options` or `dialog.page("interface")`.
- **Size.** It is 76 by 24, so it fits an 80x24 terminal: one scrolled row of tabs over the tallest page (*Panel
  defaults*). With `interface.settings_tabs = left` it is 80 by 24: a column of at most 20 for the tabs, and 57 left
  for a page, which every page fits (*File panels*' second column is the tightest). There the tabs' rule runs the
  frame's whole height into its tees (`TabView.joins_frame`), and OK and Cancel are centred under the pages
  (`SettingsDialog._buttons_under_pages`, the base's `row` rebound).
  The Screen savers page keeps *Time* under its lists, as DN had it, with the lists three rows shorter to stay that
  short.
- **What OK does.** `Shell.setup(dialog, *sections)` spawns the dialog. For a multi-section answer it keeps only the
  sections whose values changed. It assigns those onto `SETTINGS` (reactive, so bindings repaint), then calls
  `SETTINGS.save(section=...)` for each. An `OSError` shows an *Error* box, and the values stay applied for the
  session. A changed `interface.language` is applied after (`Shell.settings`).
- **Tests.** Open the dialog with `lambda a: a.spawn(a.run_command(InterfaceSetup))`, then reach the page through
  `a.modal.interface`. Build a page alone (`InterfacePage(section=...)`) to test its seeding and `accept()`.
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
| `system.internal_viewer` / `internal_editor` | Off: F3/F4 run `viewers.ini`/`editors.ini`'s entry for the file, else `$PAGER` (default `less`) / `$EDITOR` (default `vi`) on the console; Alt+F3/Alt+F4 do the other (`navigator-user-menu`) |
| `system.show_hidden` | A new panel's `show_hidden` |
| `system.temp_dir` | `navigator.lib.system.tempdir.temp_root()`, read each time: the user menu's private directory and the subshell's rc files; empty is `$TMPDIR` |
| `system.system_clipboard` | On (a departure: DN's default was off): copies go to OSC 52 and the desktop's tool, pastes read them. Off: `Application.system_clipboard` false, a clipboard private to Navigator (`Shell._choose_clipboard`, an effect) |
| `system.flush_buffers` | Copy and a cross-device move `fsync` each file written (`CopyRequest.flush`, set by `CopyDialog.accept`) before it counts as done or a move deletes its source; a sync error fails that file like a write error. `EINVAL`/`ENOTSUP` (a file system with nothing to sync) is not an error. A rename-move writes nothing, so syncs nothing |
| `system.internal_terminal` | Off: Ctrl+O hands the real terminal to the shell, as Midnight Commander does, and commands from the line run there (a departure: not DN's; `console-command-line` has the mechanism). Also a System Setup box, *Use internal terminal* |
| `system.on_error` | `dialog` (default): an unexpected exception opens `ErrorDialog` (`navigator/widgets/shell/error_dialog/`) with the traceback, *Continue*, *Copy* (the whole traceback to the clipboard) and *Quit*. `crash`: Navigator quits, printing the traceback once the terminal is restored, and exits with status 1. `--on-error` overrides it for the session. Either way, `Navigator.log_error` appends the failure to `errors.log` beside the database (`navigator/lib/system/errorlog.py`, opened by `main()`, which also points `faulthandler` at it). A second failure while the box is up quits. A departure: DN had Turbo Pascal's *Runtime error*. Shown in System Setup as *Unexpected failures*. Tests run with `crash` (conftest) |
| `system.stall_report` | Seconds (default 2, 0 off) the frame loop may stay on one batch before `errorlog.Watchdog` writes a `STALL` entry to `errors.log` (`navkit-widgets-input`, *Failures*). A departure, not DN's. The watchdog thread reads a plain `threshold`, which `Navigator._follow_stall_report` (an effect) keeps in step, so a change applies at once. System Setup's *Report a stall after*, a three-digit `MaskedField` |
| `interface.clock`, `interface.hide_status_line` | Clock and key bar visibility |
| `interface.hide_menu_bar` | The desktop takes the top row; the bar floats over it only while a menu is open |
| `interface.hide_command_line` | The desktop takes its row; it takes no keys, and its commands (Enter, Home, End, Tab, Ctrl+Enter) are disabled so those keys go to the panel |
| `interface.auto_hide_command_line` | The line shows only while it holds text; typing still goes to it and brings it back (DN 1.51 never read this bit -- transcribed from `CheckSize`/`ToggleCmdLine`) |
| `interface.esc_user_screen` | Esc with an empty command line toggles the console (Ctrl+O), DN's `cmShowUserScreen`; Esc on a line with text clears it, and does nothing with the line hidden |
| `interface.block_insert_cursor` | The command line's caret is a block (`Shell:block_insert { caret: block }` in `navigator.nss`; on `Shell` because it answers `cursor_position` for the line). Unticked, the terminal's own shape |
| `interface.track_viewing` / `track_editing` | On (a departure: on by default): viewers/editors are recorded and restored, and Alt+PgDn / Alt+PgUp list them; off, the lists say DN's `dlSetViewHistory`/`dlSetEditHistory` (`navigator-viewer`, `navigator-editor`) |
| `interface.store_viewer_position` / `store_editor_position` | On (a departure, as the Track pair): a tracked file reopens at its recorded window rectangle, scroll and cursor. Off, it is still recorded and listed, and its mode/wrap/filter (viewer) or insert mode/vertical blocks (editor) still come back, but it opens at the top in a fresh window. Without Track there is no record, so nothing to restore |
| `interface.track_directories` | On (a departure, as the Track pair): each directory a panel comes to goes first into the `directories` history, Alt+Backspace's list; off, Alt+Backspace says DN's `dlSetDirHistory` (`navigator-panels`) |
| `startup.autosave_desktop` | Off by default: on, the desktop is saved on exit and restored at the next start (`navigator-desktop`); DN restored it at every start |
| `startup.auto_user_menu` | F2's user menu opens once the start's desktop is in place (`Navigator.on_start`, DN's `RunMenu`) |
| `startup.clear_history` | `main()` calls `clear_histories()` before the screen is taken: every unpinned input-line, command and directory history entry and view/edit record goes; pinned ones stay (`ClearHistories`) |
| `startup.inactivity_exit` | An hour with no key, click or paste (`Navigator.idle_exit_after`, looked at every `idle_check_every`) exits without asking, or runs `$DNIDLE` instead when it is set (`ExecExit`). Not while a command runs on the console, and (a departure) not while an editor holds a changed text. Pointer motion alone does not count, as it never reaches `on_event` |
| `startup.preserve_directory` | Off (DN's): after a command the active panel follows the shell's directory (`Shell._follow_shell`), and a restored desktop's topmost manager opens its active panel in the current directory -- the start one, or the panel's for Load desktop (`desktop_state.restore(here=)`). On: it keeps its own. DN decided at `Store`; here at restore, so the saved desktop loses nothing |
| `interface.settings_tabs` | `top` (default) or `left`: where *Settings* puts its tabs (`TabView.side`), read as it opens. `left` widens the box to 80 (`settings_dialog.LEFT_WIDTH`) so a page keeps its width beside the column. Not DN's. Interface's *Settings tabs* radio buttons |
| `interface.history_size` | 50 (a departure: DN fixed 20): entries kept per history list -- `HISTORY.limit` (set by `Shell._size_histories`) and `FileRecord.store`. A `MaskedField` under Interface Setup's boxes |
| `confirmations.erase_single` / `erase_multiple` | Off: no Delete dialog, and so no *Recursive delete* |
| `confirmations.erase_non_empty_dir` / `erase_read_only` | Off: the eraser's question is answered Yes |
| `confirmations.create_dir` | Off: copy and link create a missing target directory without asking |
| `confirmations.exit` | On: Alt+X asks DN's `dlQueryExit` first |
| `editor.tab_size`, `editor.vertical_blocks` | Seed a new editor |
| `editor.highlight_line` / `highlight_column` | Seed a new editor's current line and column highlight (Editor > Options switches one editor's) |
| `editor.optimal_fill` | Seeds a new editor's *Optimal fill* (Editor > Options switches one editor's): blanks written as tabs on save and ^K W |
| `editor.auto_brackets` | Seeds a new editor's *AutoBrackets* (Editor > Options switches one editor's) |
| `editor.autowrap` / `justify_on_wrap` | Seed a new editor's *Auto wrap* and *Justify on wrap* (Editor > Options switches one editor's) |
| `editor.left_margin` / `right_margin` / `paragraph` | Seed a new editor's `margins` for paragraph formatting (Alt+J/R/L/C); *Format Margins* changes one editor's alone |
| `viewer.hex_mode`, `viewer.wrap_lines` | Seed F3's viewer |
| `editor.line_divisor` | The terminator a text with no line break yet takes (`FileEditor.open` sets `Document.newline` from `document.NEWLINES`): a new file, an empty one, a single line. A file with breaks keeps its most common one |
| `editor.persistent_blocks` | On (DN's default): the block stays as the cursor moves and edits go round it. Off: a movement without Shift, typing, Enter, Backspace and Del unmark it (`BlockOff`) |
| `editor.overwrite_blocks` | Only with *Persistent blocks* off (DN's `(ebfPbl + ebfObl) = ebfObl`): typing and pastes replace the block (one undo), Del deletes it alone; Backspace never does |
| `editor.create_backup` | F2 (and saving on close, Ctrl+F2) keeps the old file as `NAME.bak` (`save.backup_of`); Save as and ^K W never back up, as DN's never did |
| `editor.lock_file` | Read at each `LockFile`: an editor holds its file with an exclusive advisory `flock` (`navigator/lib/editor/lock.py`) from open to close, re-taken after every save. A write to a file another program holds is refused whatever this says |
| `editor.auto_indent` | Seeds a new editor's *Autoindent* (`FileEditor.auto_indent`; Editor > Options switches one editor's): Enter's `MakeEnter` rules (`navigator-editor`) |
| `editor.backspace_unindents` | Seeds a new editor's *Backspace indents* (`FileEditor.back_indent`; Editor > Options switches one editor's): `MakeBack`'s `BackIndent` (`navigator-editor`) |
| `file_manager.drag_drop_columns` | DN's *Drag-and-drop* (`fmoDragAndDrop`, off as DN's): files can be dragged out of a panel with the mouse (`navigator-panels`) |
| `confirmations.drag_and_drop` | DN's `cfMouseConfirm`: a drop puts up the Copy dialog aimed at it; off, it copies at once in the dialog's session mode |
| `file_manager.use_arrows` | On: Left/Right/Home/End edit a command line with text, Shift+ them the panel; off, reversed (`navigator-panels`) |
| `file_manager.auto_change_dir` | On: a cursor resting in the manager's tree takes the active panel there (`Manager._panel_follows_tree`); off, only Enter does |
| `file_manager.beep_after_copy` | A copy or move that was not aborted rings the terminal's bell (`Application.bell`, BEL; DN's `BeepAfterCopy`) |
| `file_manager.space_toggles_selection` / `bs_upper_dir` / `del_erases` | Space tags, Backspace goes up, Del erases while the command line is empty; off, the command is disabled in `Shell.enables`/`Manager.enables` so the key falls through to the line. Shift+Backspace/Ctrl+PgUp and F8 are unaffected |
| `file_manager.column_titles` | The detailed and list modes' heading row (`Panel._follow_column_titles`, an effect, so it applies at once); the dividers stay |
| `file_manager.tag_character` / `tag_sign` | The tagged row's gutter mark: `tag_sign`'s first character (empty: `√`; `+` on the ASCII tier when it is not ASCII); off, the colour alone |
| `drive_info.*` | Each line of Ctrl+L's information panel (`diskinfo.lines`), read at every paint. The field is `directory_title`, not `title`: a field named `title` would hide the section's own `title` |
| `column_defaults.*` | A new panel's `columns` (*Disk Drive*) and each *Find:* listing's `find_columns` (*File find*), `ColumnDefaultsData.columns(listing)`. *TEMP:* and *TDR View* are left out as DOS-only, *Archives* until archive handlers; every box defaults on (DN's were 0, its brief panel) |
| `savers.*` | `selected` (names, commas: `star_flight`, `flash_light`, `clock`, `blackness`, or a program in `savers/` beside `navigator.ini`), `time` and `mouse`: `Navigator._check_saver` (every `saver_check_every`) calls `Shell.rest` after *Time* idle or when the pointer comes into the top right corner, never with it in the bottom right, nor while the console runs a command. Empty by default, as DN's list was; Screen rest with none selected is *Star flight* (a departure). `navigator/lib/appearance/savers.py`, `widgets/shell/screen_saver.py` |
| `uucode.*` | What UU Encode and UU Decode open on and run with (`navigator-file-ops`); `line_ends` defaults to `lf` (a departure: DN's was DOS's CR+LF) |
| `highlight_groups.*` | The five custom file-type masks (`filetypes.use_masks`, from `Shell._use_highlight_groups`): row colours and *Group* order; a change re-reads every panel. The lines are named after Navigator's groups, not DN's *Custom 1*..*5*; a mask is kept with blanks and empty patterns dropped (`DelSpaces`) |
| `panel_defaults.sort_by` | Seeds each new panel's `sort_mode` (Alt+B changes one panel's) |
| `panel_defaults.view_mode` | Seeds each new panel's `view_mode`: `simple`, `detailed` (the default) or `list` (Ctrl+Y changes one panel's). Not DN's -- *Panel mode* closes *New Manager defaults*. `conftest`'s `_default_settings` pins `simple`, which the panel tests were written against, and `tools/screenshot.py` pins it too: the README screenshot stays in the simple layout by decision, whatever the default |
| `panel_defaults.executables_first` / `archives_first` | Read at each panel read (`Panel._rescan`, untracked): those files lead by name, extension and type |
| `panel_defaults.files_highlight` | File-type row colours (`Panel.row_style`) |
| `panel_defaults.current_file` / `selected_files` | What the panel's info line (its footer) may show; neither, it is empty |
| `panel_defaults.totals` / `free_space` | DN's `TInfoView` lines under the listing (`Panel.info_lines`, parts `totals`/`free-space` and their `-numbers` on `[122]`-`[125]`): *Total: N files with B bytes* (files only, `CalcTotalInfo`) and *SIZE free on MOUNT* (read with the directory, `free_space_of`; not over a *Find:* listing). SIZE is `human_size`'s `df -h` form, `977K`/`9.5G`/`384G` (a departure: DN gave every digit); under a kilobyte it stays *B free bytes*. Free space is on by default, as DN's was |
| `file_manager.info_divider` | A `─` row over those lines, `┴` where a column divider comes down (`Panel.render_info`); the frame then takes no bottom tee. No lines, no divider |
| `panel_defaults.directory_length` | Every read counts each directory's bytes into its size (`scan_directory(dir_length=)`, `..` the one listed), on the scan thread; Esc while *Reading directory...* stops it and turns the box off for that panel, as DN's `Abort` did |
| `panel_defaults.left_panel` | `Manager.apply_left_panel`, run for Ctrl+F3's manager and the start's own (not a restored one): the right panel takes the keys and the information panel or tree stands in the left's place, or the left side is hidden (`TDoubleWindow.Init`) |

The `panel_defaults` *Display* boxes above are read live by every panel (`Panel.shows`) **until Alt+S's *Panel
Options* gives that panel its own** (`Panel.display`), a departure: DN copied *New Manager defaults* into each
manager it made.

Everything else is `honoured=False`.

## Tests

`tests/conftest.py`'s autouse `_default_settings` resets `SETTINGS` and points `XDG_CONFIG_HOME` into `tmp_path`, so
no test reads or writes the real file. Open a dialog in a test with `lambda a: a.spawn(a.run_command(InterfaceSetup))`.
Posting the command as an event does not reach the Shell.
