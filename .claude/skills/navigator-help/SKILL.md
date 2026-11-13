---
name: navigator-help
description: F1 Help's content -- the Markdown pages under docs/ (docs/en/ canonical, one directory a language with the same tree, docs/en/README.md the contents page), the Markdown subset GitHub and Navigator both render, links and topic ids, and screenshots written twice by tools/screenshot.py (SCENES, Scene, cropped, as_ansi) as shots/NAME.svg for GitHub and shots/NAME.ans for the help window, read by navigator/lib/help/ansi.py. A departure from DN's .hlp files, asked for. Use when writing or moving a help page, adding a screenshot scene, or designing the help window.
---

# Help (F1): the pages and their pictures

**The window does not exist yet.** `Help` (`navigator/commands.py`) has no handler, so F1 is disabled and some thirty
dialogs leave their Help button out or greyed. What is fixed is the content, below; *Still to design* lists the rest.

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

## The window (designed, not built)

DN's is `HELPFILE.PAS`: `THelpWindow`, 72 by 20, centred, titled *Help*, run modally (`DNUTIL.PAS` `cmHelp`,
`ExecView`), a `THelpViewer` with both scroll bars inside; `StatusDef hcHelp` names its keys. Decided:

- **Modal, as DN's.** `HelpWindow` is an overlay, so F1 works inside a dialog and Esc goes back to it. Alt+Z zooms,
  Ctrl+F5 resizes, as DN's status line had them.
- **`HelpViewer` is its own widget, not a `FileViewer`** (byte sources, hex, search and editing are none of its
  business). It calls `markdown.render` and paints the `Layout`'s rows.
- **Keys are `hcHelp`'s**: Tab / Shift+Tab the next / previous link, Enter follows, Alt+F1 goes back (`PrevTopic`,
  `MaxUndo` 200), F1 *Help on help* (`docs/en/help.md`), Shift+F1 *Index* (`README.md`), Esc closes.
- **No text cursor, a departure**: DN's `TScroller` had one, and a reference was selected when the cursor stood on
  it. Here the arrows, PgUp/PgDn, Home/End scroll and Tab picks links: pages are reflowed Markdown, laid out for
  bidi, and the mouse does the pointing.
- **A single click follows a link, a departure, asked for**: DN's click placed the cursor and a double click
  followed.
- **Colours are DN's help palette** (`CHelpWindow` = application slots 139-146 and 163; `CHelpColor`'s defaults:
  frame `$37`/`$3F`, text `$30` black on cyan, keyword `$3E`, selected keyword `$1E`, highlight `$3F`), named in
  `tools/palconv.py` -- they are not among the 144 the Colors dialog exposes -- default theme first. Headings and
  strong text take the highlight, links the keyword. A code block is one plain colour: the syntax colours were not
  chosen for cyan. A picture keeps its own colours.
- **The topic**: a `help_topic` string on a dialog or window (`"file-operations.md#copy"`, DN's `HELPCTX`). F1 walks
  up from the focused widget to the first one set (`GetHelpCtx`), else the contents page. A dialog's *Help* button
  sends the same `Help` command. A test checks every `help_topic` resolves.
- **F1 while a child program runs in the console goes to the child**, as it does today with `Help` disabled.
- **`layout.py` has, built** (F3's Markup view is unchanged; `tests/test_help_layout.py`):
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
- **Following**: a relative link loads the page (the language's, else `docs/en/`'s; shots the same) and scrolls to
  the anchor. The back stack keeps the page, the block on top and the selected link, so it survives a resize. A
  link to another site stays OSC 8 only and Tab passes over it (an in-app opener was declined).
- **Loading** is on a thread (`navml.background.Background`): read, render, and again on a resize.
- **Shipping**: `docs/` stays at the top of the repository and is installed as `navigator/docs/`. `setup.py` says
  so (`package_dir={"navigator.docs": "docs"}`, and therefore lists the packages, which `pyproject.toml`'s
  `packages.find` cannot do for a directory it does not find); package-data takes `**/*.md` and `**/*.ans`, so no
  SVG is shipped. **No symbolic link**: a clone without them (Windows) gets a text file. `pages.root()` reads
  `navigator/docs` through `importlib.resources` when installed and `docs/` beside the package in a checkout.
- **Order**: the layout additions and the page loader; the window, keys and colours; `help.md` and F1; then each
  dialog's Help button back as its page is written (`dn-porting` has the grep that finds them).
