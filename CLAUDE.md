# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. It holds what
every task needs. **Everything about one subsystem is a project skill** under `.claude/skills/`, loaded when the task
touches it: the skill's `SKILL.md` has the rules and gotchas, and its `reference/` holds the design rationale that used
to be `navml/DESIGN.md` and `navkit/DESIGN.md` (both now indexes of their old headings, so a citation such as
*Section* in `navml/DESIGN.md` is found by searching the index).

## What this is

Navigator is a faithful recreation of the DOS Navigator two-panel file manager for modern POSIX terminals: a desktop of
overlapping windows over an always-present console (Ctrl+O), DN's menu, panels, viewer (F3), editor (F4), copy/move/
link/erase/attributes, trees, history and dialogs, transcribed from the original Pascal source and its palettes. It is
layered in three parts, each depending only on the one below:

- **`navkit/`** -- the application core: the one asyncio loop, the tty, the screen buffer and diffing renderer,
  reactive attributes, `Widget`, focus/events/commands, the `.nss` stylesheet engine, and the console that runs child
  programs on a pty it owns. No knowledge of a widget library.
- **`navml/`** -- the `.nml` markup language (QML's architecture, Kivy's syntax), its parser and code generator
  (`python -m navml build`), and a Turbo Vision-style widget library (`navml/widgets/`: dialogs, layouts, menus,
  windows, trees, history).
- **`navigator/`** (command `nav`) -- the file manager. `navigator/__main__.py` is the command line and the `Navigator`
  application; `navigator/widgets/` the screens, grouped by purpose (`shell/`, `manager/`, `file_ops/`, `tree/`,
  `viewer/`, `editor/`, `about_dialog/`); `navigator/scheme.py` the stylesheet loader; `navigator/styles/` the `.nss`
  assets. Models sit beside them (`viewer.py`, `editor/`, `filecopy.py`, `fileerase.py`, `fileattr.py`, `filelink.py`,
  `job.py`, `subshell.py`, `filetypes.py`, `about.py`).

**The widgets are not in `__main__.py`** because that module is already in `sys.modules` as `__main__`, and
`from navigator.__main__ import Panel` would import a second copy with a second `Panel` class. A widget a document
names has to be importable by its own name.

Still to come (README sketches it): pluggable filesystem handlers (ssh, smb, archives), a plugin system, the rest of the
editor's phases, DN's TETRIS easter egg.

## Environment and commands

- Python 3.12, virtualenv at `venv/` (not tracked): `source venv/bin/activate`
- One run-time dependency, `pyte`, and it is load-bearing: it is the VT emulator behind `navkit/console.py`, which is
  what makes Ctrl+O possible at all — install it with `./venv/bin/pip install -r requirements.txt`. Everything else is
  stdlib. Test tooling lives in `requirements-dev.txt`: `./venv/bin/pip install -r requirements-dev.txt`
- Run the file manager: `./venv/bin/python -m navigator [LEFT_DIR] [RIGHT_DIR]` (Tab switches panels,
  arrows/PgUp/PgDn/Home/End move, Enter descends, typing goes to the command line and Enter runs it there, Ctrl+E/Ctrl+X
  recall commands, Ctrl+R rescans, Ctrl+O shows the console and Shift+PgUp/PgDn scrolls
  it back, F10 opens DOS Navigator's menu, Alt+X quits). `--theme NAME` picks a colour scheme, `--list-themes` names them, `--palette terminal`
  gives the terminal's own scheme back the sixteen colour names, `--glyphs {auto,ascii,unicode,nerd}` overrides what the
  terminal's font is assumed to draw, `--no-dim-modal` stops what is behind a dialog being painted faint
- Regenerate the colour schemes from a DOS Navigator distribution:
  `./venv/bin/python tools/palconv.py path/to/DN/COLORS --out navigator/styles/themes`; `--dump ONE.PAL` prints one
  palette's decoded slots instead
- See what a terminal sends while it is in Navigator's modes (raw, mouse, bracketed paste, kitty flags):
  `./venv/bin/python tools/keyprobe.py [--legacy] [--no-mouse]`, `q` twice or Ctrl+C quits -- the way to find out whether a key
  the terminal binds for itself (Ctrl+Shift+V) arrives as a paste or as a key
- Regenerate the README screenshot: `./venv/bin/python tools/screenshot.py` paints the desktop headless (pinned
  directory, clock and console) and writes `docs/screenshot.svg` plus the text copy between the README's
  `<!-- screenshot:begin/end -->` markers; `--check` exits 1 when either is stale, `--theme`/`--size` pick the scene.
  The README links the SVG by absolute `raw.githubusercontent.com` URL because PyPI renders the same README
- Regenerate a component's Python from its markup: **`./venv/bin/python -m navml build navml navigator`** — both
  component packages, and naming them is necessary because the no-argument form builds the installed `navml` package
  alone, which is the edit-in-site-packages workflow rather than this repository's. `--check` reports markup that no
  longer matches its generated half and exits 1, which is what to run after editing any `.nml`; a generated file is
  only ever overwritten if its first line is `# navml: generated`
- Run the tests: `./venv/bin/python -m pytest`; one file with `... -m pytest tests/test_screen.py`; one test with
  `... -m pytest tests/test_screen.py::test_only_changed_cells_are_emitted` or `-k <substring>`
- pytest config lives in `pyproject.toml`; `pythonpath = ["."]` is what lets tests import `navkit` and `navigator` from
  the repo root

## Testing

`tests/conftest.py` carries the three things every application test needs:

- `FakeTerminal` — stands in for the tty (`is_tty` false, so no reader or raw mode is installed) and records one
  `frames` entry per flush. `len(frames)` is therefore the number of repaints that produced actual output, while a
  widget's own render counter is the number of render passes; an unchanged frame renders but writes nothing, so assert
  on whichever of the two you actually mean.
- `run_app(app, actions)` — runs the app to completion on `asyncio.run`, applying each action (an event to post, or a
  callable taking the app) once the loop is live, and exiting afterwards if the app has not already stopped. Everything
  is wrapped in a timeout so a stuck loop fails instead of hanging the suite.
- `settle()` — runs the queued reactive effects, which is what the event loop does between dispatching a batch and
  painting. A test that drives a widget's model directly (`panel.enter()`, `panel.reload()`, `panel.cursor = 99`) has no
  loop draining the scheduler, so it must call this between acting and asserting. Tests going through `run_app` never
  need it. An autouse fixture clears the shared scheduler around every test so one test's queued work cannot leak into
  the next.

Tests drive the loop through `Application.post_event()` and read `Application.is_running`; both exist so tests never
have to reach into the private queue. Actions posted in a single callback land in one batch, which is how the "one frame
per batch" behaviour is asserted.

For the parts a fake terminal cannot cover — raw mode, real escape output, `SIGWINCH` — run `python -m navigator` on a
pty (`pty.fork`, set the window size with `TIOCSWINSZ`, write key bytes to the master fd, read back what it paints).
This is a manual check, not part of the suite.

## Rules every change risks breaking

Each was found by running something, not by reasoning; the owning skill has the detail.

- **Every `on_*` handler is `async def`**; navkit refuses a synchronous one. A hook that cannot be awaited where it is
  called (`mounted()`, `unmounting()`) gets no `on_*` name.
- **A handler starts a dialog; it does not wait for one** -- `self.spawn(self._work())`, never `await dialog.execute()`
  inside a handler, which deadlocks the frame loop.
- **Effects belong in `mounted()`, not `__init__`**, for any widget that can be removed and put back; `remove()` disposes
  a subtree's effects.
- **A dialog's geometry must be bound, not assigned**, or `overlay()` makes it full-screen.
- **A property a widget navigates cannot be bound** (`Panel.path`): seed it after `super().__init__()`.
- **Assigning a value over a live binding raises**; `unbind()` first. **A collection must be replaced** to count as
  changed. **A computed may not write.** A widget's `style` is computed -- author `inline_style`/`merge_style()`.
- **The application's own `on_key`/`on_mouse_click` step aside while `app.modal` is set.**
- **Focus moves in the same call that changes what is shown, never from an effect** (an effect runs after the batch).
- **After editing any `.nml`**, run `./venv/bin/python -m navml build navml navigator` and check with `--check`.
- **A sheet cannot be parsed before the widgets it styles are imported** (`load_scheme()` imports `Panel` first).
- **Assets go through `importlib.resources`**, and a new asset directory needs a `[tool.setuptools.package-data]` entry.

## Working conventions

- Keep `navkit` free of any dependency on `navml` or the application; keep `navml` free of any dependency on the file
  manager. The dependency direction is strictly one-way.
- Prefer recreating original DOS Navigator behaviour over inventing modern alternatives when the two conflict --
  fidelity is the point of the project. A departure is recorded where it is made, with its reason. The **one standing
  exception** is the Nerd Font icon gutter in `Panel`; don't re-litigate it, and don't read it as licence for the next
  modern flourish. The `dn-porting` skill has the method.
- **Where notes go**: a feature's rules go in its skill's `SKILL.md`; longer rationale goes in that skill's
  `reference/`, with its heading added to the index in `navml/DESIGN.md` or `navkit/DESIGN.md`. A new subsystem gets a
  new skill. Keep this file to what every task needs.
- There is no lint tooling configured yet. When adding one, record the command here.

## Skills

| Skill | Covers |
|---|---|
| `navml-markup` | writing `.nml`: imports, ids, properties, aliases, events, expressions, `style:`/`keys:`, handlers |
| `navml-components` | two halves, component directories and groups, the merge/finder, parser and generator internals |
| `navml-library` | dialogs and controls, layouts, history, the four dialog rules, About |
| `navml-windows-menus` | desktop, windows, modal stacking, window list/tile/cascade, menus and their API |
| `navkit-reactive` | `reactive`/`computed`/`effect`/`bind`, type checks, binding rules |
| `navkit-stylesheet` | `.nss` language, cascade, parts, `StyleProperty` |
| `navkit-widgets-input` | loop and frame order, render tree, focus, emit, lifecycle, modal, cursor, mouse, timers, commands and key tables, key bar |
| `navkit-terminal` | tty, input parser, kitty protocol, key decoding, capabilities, OSC 8, clipboard, keyprobe |
| `colours-themes-glyphs` | palconv and themes, palette pinning, glyph tiers, icons, file-type colours |
| `console-command-line` | console/pyte/pty, subshell, Ctrl+O, the command line, completion, history, atuin |
| `navigator-panels` | Manager and Panel: view modes, tagging, quick search, hidden files, hiding sides |
| `navigator-trees` | TreeView, DirectoryTree, Alt+T, the tree window |
| `navigator-viewer` | F3 viewer and Ctrl+Q quick view |
| `navigator-editor` | F4 editor |
| `navigator-file-ops` | copy, move, symlink, erase, attributes, mkdir, jobs |
| `release-packaging` | PyPI, version, `.deb`/`.rpm`, repositories, GPG, release workflow |
| `dn-porting` | finding DN's source, naming after it, recording departures |

P.S. NEVER suggest to commit code, unless you are explicitly asked to do so.
