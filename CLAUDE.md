# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

Early. `navkit` has its event loop, terminal layer, screen buffer and widget base; `nav.py` is a working shell (menu bar, two live directory panels, key bar) that exercises them. `navml/` is still empty — the markup language, its parser, the code generator and the widget library are all unwritten, and the README is the design document for them.

There is no lint or build tooling configured yet. When adding one, record the command here.

## Environment and commands

- Python 3.12, virtualenv at `venv/` (not tracked): `source venv/bin/activate`
- Stdlib only at runtime — `requirements.txt` is deliberately empty. Test tooling lives in `requirements-dev.txt`: `./venv/bin/pip install -r requirements-dev.txt`
- Run the file manager: `./venv/bin/python nav.py [LEFT_DIR] [RIGHT_DIR]` (Tab switches panels, arrows/PgUp/PgDn/Home/End move, Enter descends, Ctrl+R rescans, F10 or Ctrl+Q quits)
- Run the tests: `./venv/bin/python -m pytest`; one file with `... -m pytest tests/test_screen.py`; one test with `... -m pytest tests/test_screen.py::test_only_changed_cells_are_emitted` or `-k <substring>`
- pytest config lives in `pyproject.toml`; `pythonpath = ["."]` is what lets tests import `navkit` and `nav` from the repo root

## Testing

`tests/conftest.py` carries the two things every application test needs:

- `FakeTerminal` — stands in for the tty (`is_tty` false, so no reader or raw mode is installed) and records one `frames` entry per flush. `len(frames)` is therefore the number of repaints that produced actual output, while a widget's own render counter is the number of render passes; an unchanged frame renders but writes nothing, so assert on whichever of the two you actually mean.
- `run_app(app, actions)` — runs the app to completion on `asyncio.run`, applying each action (an event to post, or a callable taking the app) once the loop is live, and exiting afterwards if the app has not already stopped. Everything is wrapped in a timeout so a stuck loop fails instead of hanging the suite.

Tests drive the loop through `Application.post_event()` and read `Application.is_running`; both exist so tests never have to reach into the private queue. Actions posted in a single callback land in one batch, which is how the "one frame per batch" behaviour is asserted.

For the parts a fake terminal cannot cover — raw mode, real escape output, `SIGWINCH` — run `nav.py` on a pty (`pty.fork`, set the window size with `TIOCSWINSZ`, write key bytes to the master fd, read back what it paints). This is a manual check, not part of the suite.

## Intended architecture

Navigator is a faithful recreation of the DOS Navigator two-panel file manager for modern POSIX terminals. It is layered in three parts, each depending only on the one below it:

### `navkit/` — application core (lowest layer, no widget library knowledge)

Written, and the pieces fit together like this:

- `application.py` — `Application` owns the only asyncio loop. Terminal input arrives through a `loop.add_reader` callback that feeds `InputParser` and queues the resulting events; the loop dispatches a whole batch of queued events and *then* paints one frame, so a paste or a mouse drag costs a single repaint. `SIGWINCH` becomes a `ResizeEvent`; events reach the `Application.on_*` hooks first and the widget tree second.
- `terminal.py` — `Terminal` owns the tty (raw mode, alternate screen, mouse tracking, bracketed paste, autowrap off) and restores it in `Application`'s `finally`. `InputParser` is fed incrementally and keeps undecodable tails, so sequences split across reads still decode. A lone `ESC` is inherently ambiguous: the parser reports `pending_escape` and the application resolves it with an `ESCAPE_TIMEOUT` timer.
- `screen.py` — `ScreenBuffer` is the only thing widgets paint into; drawing clips silently, and double-width characters occupy a cell plus an empty continuation cell. `render_diff()` emits only the escapes needed to turn the last flushed buffer into the new one, and repaints fully when the size changed.
- `style.py` — `Style` is an immutable cell appearance that knows its own SGR sequence. Nothing else writes colour codes.
- `widget.py` — `Widget` has geometry, children, `render(buffer)`, `layout(width, height)` (called on the root at every resize) and `dispatch_key`/`dispatch_mouse`, which offer events to the topmost child first.

Still to build here:

- Observable widget attributes: changing one triggers recomputation of every attribute that references it (reactive binding, the mechanism `navml` markup relies on). Widgets currently repaint by calling `invalidate()` by hand.
- A CSS-like stylesheet library and style lookup engine, resolving to the `Style` values `style.py` already defines

### `navml/` — markup language + widget library

- `*.nml` markup language inspired by QML and Kivy
- Parser translating `.nml` into a node graph
- Code generator traversing that node graph to emit a Python class
- The generated class is silently merged with a hand-written Python module holding the event handlers; Python's import machinery is overridden so a single `import` yields the merged class. This import hook is the crux of the layer — `.nml` files and their sibling `.py` handler modules are two halves of one class.
- Rich widget library (windows, buttons, menus, labels, standard event handlers) modelled on Borland's TurboVision

### `navigator` / `nav` — the file manager application

`nav.py` currently holds the whole application: `Manager` (the desktop), `MenuBar`, `Panel`, `KeyBar` and the `Navigator` application subclass, all painting by hand. These screens move into `*.nml` markup once navml exists, leaving only event handlers behind — so treat the widget code here as scaffolding, not as the eventual home of the UI.

- `Manager` window with two file-listing panels
- View and Edit file windows
- File operations over the selected files
- Pluggable filesystem handlers so operations work over ssh, smb, inside zip archives, etc.
- Plugin system for third-party extensions
- Look and feel carefully recreated from Ritlabs' classic DOS Navigator (including its TETRIS easter egg)

## Working conventions

- Keep `navkit` free of any dependency on `navml` or the application; keep `navml` free of any dependency on the file manager. The dependency direction is strictly one-way.
- Prefer recreating original DOS Navigator behaviour over inventing modern alternatives when the two conflict — fidelity is the point of the project.