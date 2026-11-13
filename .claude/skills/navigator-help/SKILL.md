---
name: navigator-help
description: F1 Help -- HelpWindow and HelpViewer (navigator/widgets/help/, DN's THelpWindow: Tab/Enter/Alt+F1 over links, the back stack, the $help-* colours), Navigator.on_help and help_topic, and its content: the Markdown pages under docs/ (docs/en/ canonical, one directory a language with the same tree, docs/en/README.md the contents page), the Markdown subset GitHub and Navigator both render, links and topic ids, and screenshots written twice by tools/screenshot.py (SCENES, Scene, cropped, as_ansi) as shots/NAME.svg for GitHub and shots/NAME.ans for the help window, read by navigator/lib/help/ansi.py. A departure from DN's .hlp files, asked for. Use when writing or moving a help page, adding a screenshot scene, giving a dialog its help, or changing the help window.
---

# Help (F1): the pages and their pictures

**F1 opens `HelpWindow`** (`navigator/widgets/help/`, DN's `THelpWindow`) anywhere, a dialog included, on the
topic the keyboard's dialog or window names, else on the contents page. **Not yet**: any dialog or window naming a
topic (no page is written for one), and the thirty-odd dialogs' Help buttons -- *What is left* below.

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

- **Alt text is mandatory and says what is shown**: it is what a window too narrow for the picture, or a missing
  `.ans`, displays.
- **Cropped to what it explains, at most 72 columns**: a dialog with its shadow, a menu, one panel. Wider does not
  fit a help window on an 80-column terminal; a whole-desktop picture is allowed, for GitHub and the website alone.
- **Nothing volatile in a scene**: no version, no date or free space that is not pinned, or `--check` goes stale
  with every release (the README's scene does, by decision: it shows About).
- **A picture is a picture**: the default theme and the language it was painted in, whatever the user runs; and its
  block must not mirror on a right-to-left screen, being laid out already (`Widget.mirrors`, `navkit-bidi`).
- Never edited by hand. `./venv/bin/python tools/screenshot.py` writes all, `--only NAME` one, `--check` exits 1 when
  any is stale, `--language CODE` writes `docs/CODE/shots/`. `tests/test_screenshot.py` runs `--check --no-readme`:
  Help's pictures only, since the README's goes stale with the version and the release workflow runs the suite.

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
  `HelpWindow(topic).execute(app)`. 72 by 20 or the screen if smaller; **Alt+Z** (`ZoomWindow`, the `zoomed`
  property) makes it the screen less the menu bar and key bar. The scroll bar is on the right frame, shown only
  while the page is longer than the window (as the viewer's). Departures: no bottom bar (a page wraps to the width),
  no dragging and no Ctrl+F5 resize -- navml's `Modal` is a fixed, centred box.
- **`HelpViewer`** (`help_viewer.py`, Python alone) is its own widget, not a `FileViewer`. `show(topic)`, `follow()`,
  `back()`, `step(by)`, `scroll_to(row)`; reactive `page`, `layout`, `top`, `total`, `selected`, `problem`; plain
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

- **Not covered yet**: bookmarks beyond a paragraph, the link managers' own boxes (connections, passwords, host
  keys), the smaller dialogs (select group, columns, quick and multi-rename, checksums, encryption, convert
  text, the viewer's and editor's own small boxes), the calendar, the character table, SmartPad, macros. They
  open their window's or menu's page, or the contents. *≡* names no page. The console names none.
- **The help window's keys are not in `keybindings.ini`** (no section in `keybindings.TABLES`).
- A code block wider than the window is cut: there is no sideways scroll.
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
    False when wider than the room: never wrapped or cut.
  - `markdown.render(..., pictures=)`: a callable from an image's `src` to cells (Help passes
    `pages.shot` bound to the page and language). Only an image that is a paragraph alone is drawn; among text,
    unknown, or too wide it is `[alt]` as before.
- **Shipping**: `docs/` stays at the top of the repository and is installed as `navigator/docs/`. `setup.py` says
  so (`package_dir={"navigator.docs": "docs"}`, and therefore lists the packages, which `pyproject.toml`'s
  `packages.find` cannot do for a directory it does not find); package-data takes `**/*.md` and `**/*.ans`, so no
  SVG is shipped. **No symbolic link**: a clone without them (Windows) gets a text file. `pages.root()` reads
  `navigator/docs` through `importlib.resources` when installed and `docs/` beside the package in a checkout.
