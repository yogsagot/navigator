---
name: navigator-help
description: F1 Help -- HelpWindow and HelpViewer (navigator/widgets/help/, DN's THelpWindow: Tab/Enter/Alt+F1 over links, the back stack, the $help-* colours), Navigator.on_help and help_topic, and its content: the Markdown pages under docs/ (docs/en/ canonical, one directory a language with the same tree, docs/en/README.md the contents page), the Markdown subset GitHub and Navigator both render, links and topic ids, and screenshots written twice by tools/screenshot.py (SCENES, Scene, cropped, as_ansi) as shots/NAME.svg for GitHub and shots/NAME.ans for the help window, read by navigator/lib/help/ansi.py. A departure from DN's .hlp files, asked for. Use when writing or moving a help page, adding a screenshot scene, giving a dialog its help, or changing the help window.
---

# Help (F1): the pages and their pictures

**F1 opens `HelpWindow`** (`navigator/widgets/help/`, DN's `THelpWindow`) from the main screen, on the contents
page. **Not yet**: F1 inside a dialog (the application's key table stands aside under a modal, so `Dialog` needs
the key), a `help_topic` on any dialog or window, and the thirty-odd dialogs' Help buttons -- *What is left* below.

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

## What is left

- **F1 inside a dialog.** The application's table is not consulted under a modal, so `Dialog` (navml) needs
  `f1` bound to a `Help` command navml owns (Navigator's `Help` then being that class), bubbling to
  `Navigator.on_help`; the default key set is regenerated then (`tools/keymap_default.py`).
- **The topic**: `Navigator.help_topic()` already walks up from the focused widget for a `help_topic` string
  (`"file-operations.md#copy"`, DN's `HELPCTX`, `GetHelpCtx`), but no widget declares one: `Modal` and `Window`
  need the property, and a test that every `help_topic` resolves.
- **The Help buttons**: each dialog's back as its page is written (`dn-porting` has the grep that finds them).
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
