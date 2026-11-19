---
name: navigator-help
description: F1 Help -- HelpWindow and HelpViewer (navigator/widgets/help/, DN's THelpWindow: Tab/Enter/Alt+F1 over links, the back stack, the $help-* colours), Navigator.on_help and help_topic, and its content: the Markdown pages under docs/ (docs/en/ canonical, one directory a language with the same tree, docs/en/README.md the contents page), the Markdown subset GitHub and Navigator both render, links and topic ids, and screenshots written twice by tools/screenshot.py (SCENES, Scene, cropped, as_ansi) as shots/NAME.svg for GitHub and shots/NAME.ans for the help window, read by navigator/lib/help/ansi.py. A departure from DN's .hlp files, asked for. Use when writing or moving a help page, adding a screenshot scene, giving a dialog its help, or changing the help window.
---

# Help (F1): the pages and their pictures

**F1 opens `HelpWindow`** (`navigator/widgets/help/`, DN's `THelpWindow`) anywhere, a dialog included, on the
topic the keyboard's dialog or window names, else on the contents page. Every dialog and window names one now;
*What is left* below has the rest.

**A departure from DN, asked for**: DN compiled `.hlp` files (`DN.HLP`, `hcXxx` contexts). Here help is Markdown under
`docs/`, because the same files are readable on GitHub, can become a website, and are rendered in-app by the
viewer's Markdown reading (`navigator/lib/viewer/markdown.py`, a pure `render(bytes, width) -> Layout`).

## Files

- **`docs/` holds language directories and nothing else of Help.** `docs/en/` is the canonical source;
  `docs/en/README.md` is the contents page (GitHub shows it for the folder, Help opens on it). The one file directly
  in `docs/` is `screenshot.svg` (and `screenshot-CODE.svg`): the README's picture, not Help's, and READMEs already
  published on PyPI link that URL.
- **Under a language**: pages with lower-case kebab names, in a feature subdirectory where a feature has several
  (`docs/en/editor/macros.md`), and one `shots/` with that language's pictures.
- **Every language has exactly `docs/en/`'s tree**: same subdirectories, same file names. Names are not translated, so
  a link works unchanged in every language. A page not translated yet is absent and Help falls back to English; a
  path under `docs/CODE/` that `docs/en/` lacks fails `tests/test_help_docs.py`.

## The Markdown

Only what `markdown.py` renders as GitHub does:

- CommonMark, GFM tables, strikethrough, task lists, fenced code with a language.
- **No raw HTML** -- in-app it is shown verbatim -- so no `<details>`, `<kbd>`, `<br>`. A `<!-- comment -->` is
  allowed: dropped in-app, hidden on GitHub.
- Keys as the key bar and menus caption them, in inline code: `` `Ctrl+O` ``, `` `Alt+F1` ``. Menu paths as
  *Utilities > Link > SSH*, the captions exactly.
- Links between pages are relative and stay inside the language's directory: `[Copying](file-operations.md#copy)`.
  Anchors are GitHub's heading slugs. **A topic id is `page.md#slug`**, which is how a dialog or a command will name
  its help (DN's help context).

`tests/test_help_docs.py` checks the tree, the HTML rule, that every relative link and anchor resolves, and that
every picture has alt text and both of its files.

## Screenshots

**Every picture is written twice from one `ScreenBuffer`**, by `tools/screenshot.py`:

- `shots/NAME.svg`, which the page names -- `![The Make directory box](shots/make-directory.svg)` -- and GitHub and a
  website show;
- `shots/NAME.ans`, the same cells as text with SGR colours. Nothing in Navigator can draw an SVG, so the help window
  swaps the suffix and blits these cells into the page. `cat` shows the file in any truecolor terminal, and it diffs
  as text.

Rules:

- **Alt text is mandatory and says what is shown**: it is what a missing `.ans` displays, and GitHub's for whoever
  cannot see the picture.
- **Cropped to what it explains**: a dialog with its shadow, a menu, one panel. One wider than the help window's
  page (68 columns on an 80-column terminal) is drawn all the same and scrolled to sideways (Left/Right, the
  bottom bar), so wide is for what cannot be narrower -- the four boxes of 76 to 78 columns, painted on an 84 by
  30 screen (`WIDE`) so the shadow is not cut at column 80.
- **Nothing volatile in a scene**: no version, no date or free space that is not pinned, or `--check` goes stale
  with every release (the README's scene does, by decision: it shows About).
- **A picture is a picture**: the default theme and the language it was painted in, whatever the user runs; and its
  block must not mirror on a right-to-left screen, being laid out already (`Widget.mirrors`, `navkit-bidi`).
- Never edited by hand. `./venv/bin/python tools/screenshot.py` writes all, `--only NAME` one, `--check` exits 1 when
  any is stale, `--language CODE` writes `docs/CODE/shots/`. `tests/test_screenshot.py` runs `--check --no-readme`:
  Help's pictures only, since the README's goes stale with the version and the release workflow runs the suite.

**The scenes** (ninety-two, each shown by one page):

| Page | Scenes |
|---|---|
| `README.md` | `file-menu` (an 80x34 screen: at 24 rows the File menu scrolls) |
| `panels.md` | `panel`, `panel-detailed`, `find-file`, `select-group`, `filter`, `make-list`, `columns-setup`, `info-panel` (80x30, so nothing scrolls), `miller`, `find-duplicates`, `panelize`, `directory-history` |
| `file-operations.md` | `copy`, `make-directory`, `multi-rename`, `erase`, `file-attributes`, `links`, `split`, `uu-encode`, `checksums`, `encryption`, `convert-text` |
| `archives.md`, `compare.md` | `create-archive`, `open-archive` (120x24, a zip the stage writes, detailed), `extract`; `compare-directories`, `synchronize`, `compare-files` |
| `viewer.md`, `editor.md` | `viewer`, `viewer-hex`, `viewer-find`, `markup-view`, `quick-view`, `filter-lines`, `data-tree`, `table-view`; `editor`, `editor-replace`, `margins`, `go-to-line` |
| `trees.md`, `drives.md`, `bookmarks.md` | `tree-panel`, `change-directory`, `directory-sizes`, `tree-window`; `volumes`, `trash` (120x24); `bookmarks` |
| `windows.md`, `dialogs.md`, `console.md`, `user-menu.md` | `window-list`, `command-palette`; `file-dialog`; `completion`, `console`, `command-window`, `command-history`; `user-menu` |
| `utilities.md`, `calculator.md`, `game.md` | `process-list`, `services`, `system-monitor`, `environment`, `system-information`, `calendar`, `character-table`; `calculator` (Simple) and `calculator-classic`, `-scientific`, `-programming`; `game` |
| `connections.md`, `settings.md`, `customizing.md` | `link-manager`, `connect`, `host-key`, `port-forwards`, `saved-links`; `settings` (Confirmations) and `settings-PAGE` for each other page; `key-bindings`, `colors` (80x30) |

`help.md` has `help-window`, on a page the scene writes (`HELP_PAGE`, `pages.root` pointed at it), so editing a
help page never makes it stale. `clipboard.md`, `macros.md`, `command-line.md` and `as-root.md` have none: nothing there is a screen worth showing.

- **A scene painted alone and one painted after the others are the same picture.** `paint()` starts each from
  `SETTINGS.reset()` and a fresh `:memory:` database, then lays its pins, and points `XDG_CONFIG_HOME` at an empty
  directory (`highlight.ini`, `menu.ini`, the viewers' and editors' lists are read from there). Without that the
  detailed-panel scene left every later one a detailed panel. A stage's own patch of a module function stays for
  the run, so it must be one no other scene minds. Check both ways: `--only NAME` writes it, a plain `--check`
  paints all fifty in order and must agree.
- **The scratch files that are opened hold real text** (`TEXTS`: `src/app.py`, `LICENSE`), padded or cut by
  `sized()` to the size `TREE` gives them, so no picture of a panel changed; modes are set (0644, 0755), not the
  umask's. A stage that writes more files (`_two_versions`, under `docs/`) dates them with `pinned()`.
- **What is read on a thread is waited for with `_until(condition)`**, never a longer sleep: the viewer's and
  editor's colouring (`_lex_stop is None`), a list's first rows, the tree's count. A window is opened with
  `desktop.open()` and put at a size with `_placed()` -- `PAGE` (66 by 18) fits an 80-column help page with its
  shadow; a zoomed one would be the whole screen.
- **A scene of what is the machine's replaces the function its test replaces**, with rows written out:
  `processes.Sampler.__call__`, `services.gather` (and `[services] manager`, before the window is made),
  `monitor.Monitor.__call__`, `volumes.gather_all` with `desktop.volume_program`, `dirusage.scan` (sizes on the
  disk are the file system's), `bookmarks.mounted_places`, `encrypt.available`, `AttrDialog`'s `facts`,
  `SystemFacts`, a dict for the environment. The game seeds `game.rng` and stops `tick`. The trees are rooted on
  the scratch directory as `/project` (`_pin_tree`: `directory_root` and `_walk_down`), not on `/`.
- **Which go stale with what**: `key-bindings` with `TABLES` or a global default key, `command-palette` with a
  menu command matching *copy*, `user-menu` with `navigator/assets/menu.ini`, `character-table` with a Python
  whose Unicode adds a block before *Spacing Modifier Letters* (none can), `file-menu` with the File menu.
- **What runs a program runs none**: `console` feeds `CONSOLE_OUTPUT` (two commands at `PROMPT` and their output)
  to the console's screen before Ctrl+O; `command-window` replaces `TerminalView.start` and feeds what `ssh` would
  have written. `info-panel` replaces `diskinfo.gather` and `diskinfo.stat_file`. `miller` opens two levels down
  (`src/navkit`, given files of text) and crops to the columns: from the scratch directory a column would list
  the machine's `/tmp` and be titled with its random name, and the command line's prompt is that path.
  The files a viewer scene opens (`notes.md`, `config.json`, `sales.csv`) are written by the stage.
- **The prompt in `completion` (and behind some boxes) is `PROMPT`'s**, the README picture's: a constant, not
  the machine's.
- **`trash` makes a Trash of nobody's**: `XDG_DATA_HOME` pointed at `.data` in the scene's scratch directory
  (gone with it; no later scene reads the variable), `trash._mounts` answering none, the info files dated by
  `PINNED_TIME`. `tree-window`, like `change-directory`, asks for `src` again once the window is up: the first
  walk's cursor is not kept.
- **A `settings-PAGE` scene shows the page's sections at their defaults** (`_settings_page`): it resets them,
  opens the box, then puts `paint()`'s pins back, so the panels behind are the other pictures'. Country's
  *Example* is now: the stage gives `country_page` a `time` answering the clock's pinned moment.
- **The wide four pin what is the machine's or the session's**: `multi-rename` its own `Rule` in the dialog
  module's `_session`; `link-manager` three made-up `Entry`s, never the database's, the first chosen
  (`_choose(0)`); `settings` the Confirmations page with `side="top"`, whatever `[interface] settings_tabs` says;
  `key-bindings` every section's `defaults()` as the assignments, not a `keybindings.ini`'s. **`key-bindings`
  goes stale when a section is added to `TABLES` or a global default changes**: regenerate it.
- **A scene's values are typed in by `stage`**, never the panel's: a target such as `/srv/backup/` where the
  dialog would offer the other panel's directory, which is the scratch directory's random path.
- **`stage` answers a widget anywhere in the tree** (`cropped()` adds its parents' places: an overlay, a window
  on the desktop, a panel), a rectangle `(x, y, width, height)` (the menu: the bar's row over the open box), or
  None.
- **Today is pinned too** (`_pin_today`): `datetime.date.today` cannot be patched, so the two modules that ask
  it (`date_button`, `calendar_window`) get a `datetime` whose `date` answers 2026-01-01 and passes every date
  for the reactive type check.
- **Every command is enabled in a scene** (`app.command_enabled` answers True), or a menu's greyed entries would
  differ with what is installed.
- **Check a new scene on a bare machine**: `env -i PATH=/nonexistent $PWD/venv/bin/python tools/screenshot.py
  --check --no-readme`. CI has no 7z, rar or zstd: *Create archive* greyed its password line there and failed
  the run (44286426522) after passing here with `PATH=/usr/bin:/bin`, which still had them. A scene pins what
  its dialog asks of the machine (`_create_archive`: `format_missing`, `can_encrypt`).

**Adding one**: a `Scene(name, stage)` in `SCENES`. `stage(app)` is async, opens what is shown over the pinned
desktop (`asyncio.create_task(dialog.execute(app))`, not the command) and answers the widget to crop to, or None for
the whole screen. `cropped()` takes the widget's rectangle and shadow, mirrored on a right-to-left screen; the widget
must be a child of the root (an overlay), its `x`/`y` being the screen's. The pins every scene shares (directory,
clock, free space, no shell, simple panels, the unicode glyph tier) are `paint()`'s.

### The `.ans` grammar

Small on purpose, so the reader (`navigator/lib/help/ansi.py`, `read(text) -> list[list[Cell]]`) is strict and raises
`ValueError` for anything else. It is not a terminal emulator; `navkit/console.py` is, and was not used because it
marks cells `terminal_palette` and takes colours by name.

- One line a screen row, ended `ESC[0m` and a newline. No cursor movement, no other escape.
- Each run of like cells is preceded by one `ESC[0;...m` saying its whole look (`Style.sgr()` starts with a reset).
- Both colours always, always `38;2;r;g;b` / `48;2;r;g;b`, resolved by the tool as the SVG's are -- the VGA palette,
  reverse and dim already applied -- so the file means the same in every terminal and theme. In-app, `render_diff`
  quantises RGB to the terminal's depth as it does any other cell.
- Attributes left to say: bold 1, italic 3, underline 4, strike 9.
- A wide character is written once and the reader gives its second cell (`""`) back; a mark or the second half of a
  flag joins the cell before it.

## The window

DN's is `HELPFILE.PAS`: `THelpWindow`, 72 by 20, centred, titled *Help*, run modally (`DNUTIL.PAS` `cmHelp`,
`ExecView`), a `THelpViewer` inside; `StatusDef hcHelp` names its keys.

- **`HelpWindow`** (`help_window/`, a `Dialog` with `buttons: "none"`) is modal, as DN's: `Navigator.on_help` spawns
  `HelpWindow(topic).execute(app)`. **Four fifths of a large screen, a departure, asked for**: 80% of the
  terminal's width and of its height (96 by 32 on 120 by 40), never smaller than DN's 72 by 20 where the screen
  has the room -- so 80 by 24 still gets 72 by 20, a page 68 wide; **Alt+Z** (`ZoomWindow`, the `zoomed`
  property) makes it the screen less the menu bar and key bar. The scroll bar is on the right frame, shown only
  while the page is longer than the window (as the viewer's); the bottom one (`hbar`) only while a row is wider
  than it, which only a code block's can be. No dragging with the mouse.
- **Ctrl+F5** (`SizeMoveWindow`, DN's `cmResize`) moves and sizes it with the keyboard, as `Window` does on the
  desktop: arrows move, Shift+arrows size (no smaller than 30 by 6), Enter keeps, Esc puts it back. A modal's
  geometry must stay bound, so the mode never assigns it: it writes the `placed` property (`x, y, width, height`,
  None until moved), which `modal_width`/`modal_height` and the `x`/`y` bindings `HelpWindow.__init__` lays over
  `Modal`'s centring read through `fit()` -- so a smaller terminal still shows all of it. Alt+Z zooms over
  `placed` and back to it; nothing is saved, the next F1 opens centred. **The mode's keys go through
  `HelpViewer.key_taker`**: the keyboard stays on the page, whose `on_key` is asked before the window's key table,
  and that is what keeps Enter, Tab and Esc from doing what the table says meanwhile.
- **`HelpViewer`** (`help_viewer.py`, Python alone) is its own widget, not a `FileViewer`. `show(topic)`, `follow()`,
  `back()`, `step(by)`, `scroll_to(row)`/`scroll_by(rows)`, `scroll_sideways_to(column)`/`scroll_sideways(by)`;
  reactive `page`, `layout`, `top`, `total`, `left`, `span`, `selected`, `problem`; plain
  `links` (the page's links that lead to a page of Help) and `history` (`Place(page, src, selected)`, 200 deep,
  DN's `MaxUndo`; `src` is the top row's source offset, so a place is the same at any width).
- **Keys are `hcHelp`'s**, in `help_window.nml`'s table over `Dialog`'s: Tab / Shift+Tab `NextTopic` /
  `PreviousTopic` (round the ends, the link scrolled into view), Enter `GoToReference`, Alt+F1 `GoBack` (refused on
  the first page), F1 `HelpOnHelp` (`help.md`), Shift+F1 `HelpIndex` (`README.md`), Esc closes (`Dialog`'s). Tab
  and Enter are on the key bar through `key_hints()`.
- **No text cursor, a departure**: DN's `TScroller` had one, and a reference was selected when the cursor stood on
  it. Here the arrows, PgUp/PgDn, Home/End scroll and Tab picks links: pages are reflowed Markdown, laid out for
  bidi, and the mouse does the pointing.
- **A single click follows a link, a departure, asked for**: DN's click placed the cursor and a double click
  followed. The wheel scrolls three rows.
- **Reading is on a thread** (`_READER`, a `Background`): `_load` reads the page (`pages.read`) and lays it out
  (`markdown.render` with `pictures=` bound to `pages.shot`). `render()` calls `_request()`, which asks again only
  when page, width, glyph tier or language differ from what was asked last -- how a zoom or a resize re-lays the page,
  from the bytes kept. An answer to anything but the last request is dropped. Until one lands the last page stays.
  **A test waits with `Until`** on `viewer.page` and `_wanted is None`, never a fixed number of steps.
- **A link on the page shown** (`#anchor`, or the page's own name with one) moves without reading again.
- **A page that is not there** leaves `layout` None and paints `problem` (*There is no help page NAME*); Alt+F1
  still goes back.
- **Colours are DN's help palette**, `CHelpWindow` (application slots 139-146 and 163), which the Colors dialog
  never listed, so no `.PAL` value is transcribed: five `DERIVED` pairs with `CHelpColor`'s defaults -- `help`
  (`$30`, text), `help-frame` (`$3F`, the frame and the highlights: headings, strong text, inline code, a table's
  head), `help-frame-icons` (`$3A`), `help-keyword` (`$3E`, a link), `help-selected` (`$1E`). Written into the
  eleven DOS themes by hand as palconv would, and into the modern ones by themegen (`text`/`text_strong`/`accent`
  on `surface`, `on_accent` on `accent`). A code block is the text's colour whole (`_look` drops a token's
  classes): the syntax colours were not chosen for this ground. A picture keeps its own colours.
- **A link out of Help** stays OSC 8 only and Tab passes over it (an in-app opener was declined); a link into
  Help is not given to the terminal.
- **`mirrors = False`**, as the viewer: rows are laid out already, and a picture must not be turned round.
- **F1 while a program has the keys is the program's**: `Navigator.refusal` refuses every application command then.
- **`Help` is navml's command** (`navml/widgets/dialog/commands.py`, `cmHelp`; `navigator.commands.Help` is the
  same class) because **`Dialog`'s key table binds F1** too: the application's table stands aside under a modal.
  The command bubbles to `Navigator.on_help`; in an application with no handler it is disabled and the key goes on.
  `HelpWindow` binds F1 over it (*Help on help*).
- **An open menu and a popup bind F1 too** (`MenuSession.keys`, `PopupMenu.keys`: both are modal layers and no
  `Dialog`), and each answers `help_topic` itself, as a property. Help opens over the menu, and Esc goes back to it
  still open. A caller's `PopupMenu(keys=("f1", ...))` loses to it.
  - **Every menu entry has `help_topic`** (`MenuNode`, so `MenuItem`, `SubMenu`; TV's per-item `HelpCtx`):
    `help_topic: "panels.md#sorting"` in markup. The highlighted entry's wins, else its submenu's, and so outwards
    (`help_topic_from(entry, stop)`): for a window's menu that joined the bar, as far as the window's own.
  - **The bar's menus do not fall back to what is behind them**: with nothing named, F1 shows the contents.
  - **A popup** asks the entry chain, then the topic it was opened with (`PopupMenu(help_topic=)`, kept in
    `topic`), then the widget it was opened for (`behind`) outwards -- a context menu is its widget's, so it shares
    that window's help.
- **The topic is `help_topic`**, a property of navml's `Modal` and `Window` (Turbo Vision's `HelpCtx`), a page and
  an optional heading: `help_topic: "file-operations.md#copy"` in markup. `Navigator.help_topic()` is DN's
  `GetHelpCtx`: from the widget with the keyboard outwards, the first non-empty one, else `pages.CONTENTS`. Any
  widget may carry the attribute; the nearest wins. `tests/test_help_docs.py` finds every `help_topic` literal in
  the three packages' `.nml` and `.py` and fails on a page or a heading that is not there -- so **write the page
  before naming it**.

## Giving a dialog its help

Written so far, each with its dialogs' topics and Help buttons: `file-operations.md` (Copy and move, Links, Split
and combine, UU), `archives.md`, `editor.md` (Find and replace, Go to a line, Margins), `panels.md` (File masks,
Panel options, Filter, Find file with Advanced search and Replace in files, Make a list file), `viewer.md` (Searching a table),
`utilities.md` (Edit the environment), `game.md` (keys, the Top Ten), `settings.md` (a section a page of
*Settings*, fifteen), `calculator.md` (the window's `help_topic`; Help on its Classic face, DN's row),
`windows.md` (Working with windows, Window list), `dialogs.md` (Keys in a dialog box, Choosing a file).

**General pages**, which no dialog names: `README.md` (Getting started, the contents by area), the first half of
`panels.md` (moving around, views, sorting, tagging, quick search, the clipboard, the other side), `viewer.md`'s
and `editor.md`'s keys, `console.md` (the command line and the console) and `drives.md` (archives, servers,
containers, volumes, the Trash, bookmarks). **Windows and menus that name a page**: `Manager` (`panels.md`),
`FileWindow` (`viewer.md`), `DBWindow`, `EditWindow` (`editor.md`), `CalculatorWindow`; the bar's *File*, *Disk*,
*Manager*, *Options* and *Window* menus and a few items (*Copy*, *Rename/Move*, *Calculator*, *Volumes*, *Trash*,
*List*), as `help_topic:` child lines in `main_menu.nml`. A window's own menus (*Panel*, *View*, *Editor*) reach
their window's. `tests/test_help_window.py`'s fixture clears the file manager's and the File menu's, its pages
being its own.

**The rest**: `file-operations.md` also has Make a directory, Erase and File attributes; `compare.md` (Compare
directories, Synchronize, Compare files); `trees.md` (the tree beside a panel, Change directory, Directory sizes);
`user-menu.md` (the user menu's file and macros, the four association files); `customizing.md` (Key bindings,
Colours); `utilities.md` (Process list, Services, System monitor, the environment). Named by `DeleteDialog`,
`AttrDialog`, `MkdirDialog`, `CompareDialog`, `ChangeDirDialog`, `KeyBindingsDialog`, `ColorsDialog` and the
windows `ProcessWindow`, `ServiceWindow`, `MonitorWindow`, `TreeWindow`, `UsageWindow`, `VolumesWindow`,
`SyncWindow`, `DiffWindow`; the bar's *Utilities* menu, *User menu*, *Links*, *Link* and *Remote shell*.
**A page's example must survive its own macros**: in a user menu `$` is the other panel's file, so `$EDITOR` in
an example would be wrong.

**navml's own boxes** cannot name a Navigator page, so the application gives theirs:
`navigator/lib/help/topics.py`'s `LIBRARY`, class name to topic (`WindowManagerDialog`, `FileDialog`), asked by
`Navigator.help_topic` through `library_topic(widget)` for a widget that names none -- its class or any it derives
from, so `PaletteFileDialog` shares the file dialog's unless it sets `help_topic` itself. Their *~H~elp* buttons
are `command: Help` in navml; in an application with no handler they do nothing (and are not greyed: a button is
not greyed for a disabled command). The topic test reads `LIBRARY` too.

**Settings**: each page names its section with `class help_topic: "settings.md#system"` (a class-level line, as
`section_name` is; `SettingsPage.help_topic`), which F1 on any of its controls finds. The dialog's own
`help_topic` is bound to the page in front's (`tabs.pages[tabs.current].help_topic`), for F1 on the tabs or a
button. Its third button is `Dialog`'s own (`buttons: "ok-cancel-help"`), `SettingsDialog.show_info` overridden to
run `Help` -- the one place that built-in button is used. A new page needs its section in `settings.md` and the
`class help_topic` line; a new setting, a line in its page's section.

1. **Write the section first**, under a heading whose slug the dialog will name; the topic test fails on a
   `help_topic` with no page or heading. Describe what the user sees, by the captions exactly (*Refresh old files*),
   and the keys as the menus caption them. Add the page to `docs/en/README.md`.
2. **`help_topic: "page.md#slug"`** in the root of the dialog's markup. F1 then works with no button.
3. **The button**, where DN's resource had `cmHelp`: `text: "Help"`, `command: Help` (from
   `navml.widgets.dialog.commands`), last in the row and in `buttons_row`. No `~H~`: the caption is already in the
   catalogues without one, and a hotkey would need checking against every dialog's letters in every language.
   **A dialog that used `Dialog`'s own `ok-cancel` row** needs a row of its own for the third button (`buttons:
   "none"`, a `ButtonRow` with `pick`, `abandon`, `helper`), and then `async def on_pick_click(self, event):
   return await self.on_ok_click(event)` in its Python half -- not `on_click: root.close(root.accept())`, which
   skips `valid()` and records no history. `Dialog`'s built-in `ok-cancel-help` is the library's markup example
   (its Help sets a prompt) and is not used. A dialog whose DN resource had no Help (Filter) gets the topic only.
4. **Where four of this library's buttons (eleven wide, two apart) pass the frame**, use DN's own row: `ButtonRow`
   with `justify: "start"`, `button_width: 10`, `spacing: 0` and `left:` at the resource's first column (`Button 8,
   9, 18, 11` is column 8). Extract, Split, Combine and UU Decode/Encode are so.
5. Take *Help is left out* out of the `#:` header.

## What is left

- **Every dialog and window names a topic** (the last batch, 2026-11-18): the rename, checksum, encryption and
  convert-text boxes, the copy and erase questions and progress boxes, ACL/xattr entries and link targets
  (`file-operations.md`); select group, columns, duplicates, panelize, directory history, remembered directories
  (`panels.md`); synchronize options (`compare.md#options`); the viewer's find, go to, filter lines, data tree and
  table boxes (`viewer.md`); the link managers' boxes (`connections.md`); bookmarks (`bookmarks.md`, the box
  through `PopupMenu(help_topic=)`); calendar, character table, SmartPad, system information and the `≡` menu
  (`utilities.md`); command windows, *Execute OS command* and the histories (`console.md`); the command palette
  (`windows.md`); key and editor macros (`macros.md`); the game's setup (`game.md`).
- **A widget that is no `Modal` or `Window` declares the property itself**: `property help_topic: "..."` in
  markup (`QuickViewer`, `FindBar`), a class attribute in a Python-only widget (`Console`).
- **Left without a topic on purpose**: `WriteWin` and `CountProgress` (shared by callers with pages of their own;
  a modal does not fall back to what is behind it, so F1 there shows the contents), models and controls.
- **Help buttons are complete against DN's source** (checked 2026-11-18: `DN.DNR` has 74 dialogs, 52 with
  `cmHelp`; no dialog built in Pascal has one). The last five got theirs then: `MkdirDialog` (`dlgMkDir`),
  `AdvancedSearchDialog` (`dlgAdvanceSearch`, widened to the resource's 55 columns for its four buttons),
  `CompareDialog` (`dlgCompareDirs`) and `GotoDialog` (`dlgGotoAddress`), both 34 wide and so on DN's ten-wide
  row, and `ViewerFindDialog` (`dlgViewerFind`). **Rightly without one**, DN's having none: Select/Unselect,
  Columns Setup, the directory, command and file histories, Filter, File attributes, the overwrite and replace
  questions, the game's setup and Top Ten -- and every box that is a departure. One parametrised test presses
  each of the five's Help and then its OK (`test_a_dn_dialog_s_help_button_opens_its_section_and_ok_still_answers`).
- **`tests/test_help_window.py`'s fixture clears the `≡` menu's topic too**: F10 opens on it, and the
  no-topic test needs a menu naming none.
- **Not read against real behaviour**: the pages were written from markup captions, docstrings and the skills.
- **Every key of the help window is in its table** (`help_window.nml`), the scrolling ones too (`ScrollLineUp`
  ... `ScrollRight` in `help/commands.py`, untitled): `HelpViewer` has no key of its own, so all of them are
  `keybindings.ini`'s `[help]` section (*Help window* in `keybindings.TABLES`). A new key goes in the table, not
  in an `on_key`.
- **A code block wider than the window is scrolled to, not wrapped**: Left/Right, Shift+wheel or a sideways wheel,
  and the bottom bar move `HelpViewer.left` up to `span - width` (`span` is the widest row); the whole page moves,
  as a `TScroller`'s. `left` goes back to 0 on another page and when Tab selects a link not wholly in view. **A
  picture wider than the page likewise**: drawn whole, never its alt text for width.
## The layout, and shipping

- **`layout.py` has** (F3's Markup view is unchanged; `tests/test_help_layout.py`):
  - `Layout.anchors`, each heading's anchor and first row, by `slug()` -- GitHub's, a repeat numbered `-1`, `-2`.
    Recorded by `Builder.heading`, so reST and HTML have them too; the docs test resolves links through it.
  - `Layout.links()`, every `Link(href, spans, image)` in reading order. A link wrapped over rows is one link with
    a span a row (same block only, so two list items linking one page stay two). Spans are positions in
    `Row.cells`, left to right: a right-to-left row is reordered when painted, and the painter maps them.
    `image` marks the `[alt]` of an image not drawn, whose `href` is the picture's file, not a page.
  - `Builder.picture(rows, src)`: rows carrying `Style` cells in `Row.picture` (`layout.Cell` is `(char,
    classes, link)`, not a `Style`), after the row's `lead`; `Row.cells` keeps the characters classed `picture`.
    Never wrapped or cut: wider than the room, its rows are wider than `Layout.width`. False only with no rows.
  - `markdown.render(..., pictures=)`: a callable from an image's `src` to cells (Help passes
    `pages.shot` bound to the page and language). Only an image that is a paragraph alone is drawn; among text
    or unknown it is `[alt]` as before.
- **Shipping**: `docs/` stays at the top of the repository and is installed as `navigator/docs/`. `setup.py` says
  so (`package_dir={"navigator.docs": "docs"}`, and therefore lists the packages, which `pyproject.toml`'s
  `packages.find` cannot do for a directory it does not find); package-data takes `**/*.md` and `**/*.ans`, so no
  SVG is shipped. **No symbolic link**: a clone without them (Windows) gets a text file. `pages.root()` reads
  `navigator/docs` through `importlib.resources` when installed and `docs/` beside the package in a checkout.
