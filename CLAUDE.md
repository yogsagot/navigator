# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

Early. `navkit` has its event loop, terminal layer, screen buffer, reactive attributes and widget base; `navigator/__main__.py` is a working shell (menu bar, two live directory panels, key bar) that exercises them and is already written in the declarative style — its panels bind their geometry to the desktop and derive their listing from a path rather than being placed and refreshed by hand. `navml/` holds no code yet — the markup language, its parser, the code generator and the widget library are all unwritten. The README sketches them. Decisions taken ahead of the code live in two design notes, and are where the next one belongs: `navml/DESIGN.md` for the markup language, `navkit/DESIGN.md` for the one unbuilt part of the core, the stylesheet and its lookup engine.

There is no lint tooling configured yet. When adding one, record the command here. Packaging is setuptools via `pyproject.toml`: `./venv/bin/python -m build --wheel` (needs `pip install build`).

The application lives in the `navigator/` package: `navigator/__main__.py` is the whole of it, and `navigator/styles/` holds the assets it loads. Assets are found through `importlib.resources` rather than relative to `__file__`, and `navigator/styles/*.nss` is declared as package data — a new asset directory needs a matching `[tool.setuptools.package-data]` entry or it will work from a checkout and vanish on install. `navigator/styles/themes/` is the second such directory and carries its own `__init__.py` and package-data entry for that reason.

Colour is split from structure and neither half is authored by hand. `navigator/styles/navigator.nss` holds the rules and defines no variable, so it does not parse alone; `navigator/styles/themes/*.nss` define every variable and no rule, and one is always loaded after it (`load_scheme("norton")`, `python -m navigator --theme norton`). The themes are generated: each is a DOS Navigator 1.51 `COLORS/*.PAL` palette decoded by `tools/palconv.py`, which documents the file format and — the part that took the work — which of the 228 attribute bytes means what, by composing the Turbo Vision palette strings along each view chain. Re-derive rather than hand-edit a theme; the tool's docstring cites the Pascal for every slot.

## Environment and commands

- Python 3.12, virtualenv at `venv/` (not tracked): `source venv/bin/activate`
- Stdlib only at runtime — `requirements.txt` is deliberately empty. Test tooling lives in `requirements-dev.txt`: `./venv/bin/pip install -r requirements-dev.txt`
- Run the file manager: `./venv/bin/python -m navigator [LEFT_DIR] [RIGHT_DIR]` (Tab switches panels, arrows/PgUp/PgDn/Home/End move, Enter descends, Ctrl+R rescans, F10 or Ctrl+Q quits). `--theme NAME` picks a colour scheme, `--list-themes` names them
- Regenerate the colour schemes from a DOS Navigator distribution: `./venv/bin/python tools/palconv.py path/to/DN/COLORS --out navigator/styles/themes`; `--dump ONE.PAL` prints one palette's decoded slots instead
- Run the tests: `./venv/bin/python -m pytest`; one file with `... -m pytest tests/test_screen.py`; one test with `... -m pytest tests/test_screen.py::test_only_changed_cells_are_emitted` or `-k <substring>`
- pytest config lives in `pyproject.toml`; `pythonpath = ["."]` is what lets tests import `navkit` and `navigator` from the repo root

## Testing

`tests/conftest.py` carries the three things every application test needs:

- `FakeTerminal` — stands in for the tty (`is_tty` false, so no reader or raw mode is installed) and records one `frames` entry per flush. `len(frames)` is therefore the number of repaints that produced actual output, while a widget's own render counter is the number of render passes; an unchanged frame renders but writes nothing, so assert on whichever of the two you actually mean.
- `run_app(app, actions)` — runs the app to completion on `asyncio.run`, applying each action (an event to post, or a callable taking the app) once the loop is live, and exiting afterwards if the app has not already stopped. Everything is wrapped in a timeout so a stuck loop fails instead of hanging the suite.
- `settle()` — runs the queued reactive effects, which is what the event loop does between dispatching a batch and painting. A test that drives a widget's model directly (`panel.enter()`, `panel.reload()`, `panel.cursor = 99`) has no loop draining the scheduler, so it must call this between acting and asserting. Tests going through `run_app` never need it. An autouse fixture clears the shared scheduler around every test so one test's queued work cannot leak into the next.

Tests drive the loop through `Application.post_event()` and read `Application.is_running`; both exist so tests never have to reach into the private queue. Actions posted in a single callback land in one batch, which is how the "one frame per batch" behaviour is asserted.

For the parts a fake terminal cannot cover — raw mode, real escape output, `SIGWINCH` — run `python -m navigator` on a pty (`pty.fork`, set the window size with `TIOCSWINSZ`, write key bytes to the master fd, read back what it paints). This is a manual check, not part of the suite.

## Intended architecture

Navigator is a faithful recreation of the DOS Navigator two-panel file manager for modern POSIX terminals. It is layered in three parts, each depending only on the one below it:

### `navkit/` — application core (lowest layer, no widget library knowledge)

Written, and the pieces fit together like this:

- `application.py` — `Application` owns the only asyncio loop. Terminal input arrives through a `loop.add_reader` callback that feeds `InputParser` and queues the resulting events. The order in one turn is fixed: **dispatch the whole batch, flush the reactive effects it queued, then paint one frame** — so a paste or a mouse drag costs a single repaint, and nothing reactive runs during the paint. `SIGWINCH` becomes a `ResizeEvent`; events reach the `Application.on_*` hooks first and the widget tree second.
- `terminal.py` — `Terminal` owns the tty (raw mode, alternate screen, mouse tracking, bracketed paste, autowrap off) and restores it in `Application`'s `finally`. `InputParser` is fed incrementally and keeps undecodable tails, so sequences split across reads still decode. A lone `ESC` is inherently ambiguous: the parser reports `pending_escape` and the application resolves it with an `ESCAPE_TIMEOUT` timer.
- `screen.py` — `Surface` is what widgets paint into. `ScreenBuffer` is the one that owns cells; `surface.view(x, y, w, h)` returns a shifted, clipped window onto another surface that owns nothing and forwards. `render_tree` hands each widget a view of its own area, so **widgets paint from `0, 0` in their own size and cannot draw outside themselves** — no `self.x +` arithmetic, no manual bounds checks, and a wide character at a widget's right edge degrades to a blank instead of spilling onto its neighbour. Drawing still clips silently, and double-width characters occupy a cell plus an empty continuation cell. `render_diff()` emits only the escapes needed to turn the last flushed buffer into the new one, comparing each row whole before walking its cells, and repaints fully when the size changed.
- `style.py` — `Style` is an immutable cell appearance that knows its own SGR sequence. Nothing else writes colour codes.
- `reactive.py` — observable attributes and the bindings between them; the mechanism `navml` markup relies on. `reactive()` declares a source, `computed()` a derived value, and assigning `obj.attr = bind(expression)` attaches an expression to *one instance* — which is what markup compiles to. `bind()` only wraps the expression in a `Binding`; the descriptor recognises one on assignment and installs it instead of storing a value, so the target is named by a real attribute reference rather than by a string. The three calls that have to name an attribute without assigning to it — `unbind(obj, Widget.width)`, `is_bound()`, `peek()` — take the class attribute itself, which is the declaration object. Dependencies are discovered by running the expression and noting what it read, so a conditional subscribes only to the branch it took. Propagation is push-pull: a write eagerly marks dependents stale, values are recomputed lazily on read and memoised. That makes it glitch-free (a diamond recomputes once, from inputs that are all final) and mirrors the frame loop one layer up. `effect()` is the only eager node, for reactions that must happen whether or not anybody reads a value.
- `widget.py` — `Widget` has children, `render(surface)`, `layout(width, height)` (called on the root at every resize) and `dispatch_key`/`dispatch_mouse`, which offer events to the topmost child first. Its geometry, `visible`, `style` and `parent` are reactive, so assigning one asks for a repaint on its own; `layout()` steps around any size that carries a binding. **All coordinates are relative to the parent** — `x`/`y`, `contains()`, and the position a `MouseEvent` carries, which `dispatch_mouse` shifts as it descends. Only the root sits in screen coordinates, and it sits at the origin.

Things to know before touching this layer:

- **Assigning a *value* over a live binding raises**, deliberately: call `unbind()` to take an attribute back by hand. Assigning another `bind()` expression is fine and replaces the old one. This is why `Widget.layout()` checks `is_bound()` — without it the first `SIGWINCH` would take down every declaratively-sized widget in the tree.
- **A `bind()` expression assigned to a non-reactive attribute is silently stored**, because there is no descriptor to notice it. A `computed` target raises, and an unknown `Widget()` keyword raises, so what is left is a typo on a plain attribute; the `Binding` repr (`<unassigned binding ...>`) is what gives it away.
- **A computed may not write.** The write path refuses if any frame on the tracking stack is a computed, which is what makes it safe to pull a stale value in the middle of composing a frame. Use an `effect` for anything impure.
- **A collection has to be replaced to count as changed.** `entries.append(x)` followed by `self.entries = entries` propagates nothing, because the equality guard sees the same object. Build a new list.
- An object carrying reactive attributes needs a `__dict__`, so slotted value types (`Style`, `DirEntry`) cannot host them.

- `stylesheet.py` — the `.nss` language and its lookup engine. CSS in shape (selectors, brace-delimited declarations, a cascade ordered by specificity) and not in scope: every declaration either names a `Style` field or names a property the widget interprets. `parse()` reads one sheet, `load()` merges several in order so a theme can redefine another's variables. Selectors are `Panel` (by class *name*, subclasses included), `.tag`, `:state` (any truthy attribute), `#name` and `Panel::part`, with descendant and child combinators. Specificity is CSS's `(names, classes + states, types)`, ties break on source order, and there is no `!important`.

Things to know before touching the style layer:

- **A widget's `style` is a `computed`, not a value you assign.** It cascades in four levels: the parent's resolved style (so appearance inherits), then matching `.nss` rules, then `inline_style`, then whatever `render()` passes straight to a drawing primitive. Assigning `widget.style` raises; author through `inline_style` or `merge_style()`.
- **`inline_style` is partial.** `"bg: red"` overlays one property and leaves the rest inheriting; it is not a whole `Style`. A `Style` is accepted and becomes the seven declarations it makes.
- **`classes` is a `frozenset` and `inline_style` is replaced, never mutated** — the reactive layer only counts a change when a collection is replaced. Use `add_class` / `remove_class` / `merge_style`.
- **Only a *reactive* attribute restyles.** `:state` matches any truthy attribute, but a plain one is read outside the dependency graph: it matches the first time and never invalidates afterwards.
- **Widget properties do not inherit**, only `Style` fields do. `border: double` on a panel does not give its children a frame. Register a non-`Style` declaration name with `stylesheet.register_property()` or the parser rejects it.
- `navkit/DESIGN.md` records why each of these went the way it did, including the parts that were measured rather than argued. Add to it rather than re-deciding.

- A widget may carry its own sheet in `_stylesheet`, governing the subtree under it; the nearest one wins and the search ends at the application's. `Manager` uses this, so the desktop is styled with or without an application around it.

### `navml/` — markup language + widget library

- `*.nml` markup language: QML for the architecture (a declarative tree, `id`s, properties that are re-evaluated expressions), Kivy for the syntax (blocks made by indentation, no braces, no semicolons, one property per line)
- Parser translating `.nml` into a node graph
- Code generator traversing that node graph to emit a Python class
- The generated class is silently merged with a hand-written Python module holding the event handlers; Python's import machinery is overridden so a single `import` yields the merged class. This import hook is the crux of the layer — `.nml` files and their sibling `.py` handler modules are two halves of one class.
- Rich widget library (windows, buttons, menus, labels, standard event handlers) modelled on Borland's TurboVision

Nothing here is written yet, but `navml/DESIGN.md` records the decisions already made — currently how a property expression (`width: parent.width // 2`) is compiled into the one-argument lambda `bind()` expects, by rewriting the expression's free names on the syntax tree rather than by formatting strings. Read it before starting the parser or the generator, and add to it rather than re-deciding.

### `navigator` / `nav` — the file manager application

`navigator/__main__.py` currently holds the whole application: `Manager` (the desktop), `MenuBar`, `Panel`, `KeyBar` and the `Navigator` application subclass, all painting by hand. These screens move into `*.nml` markup once navml exists, leaving only event handlers behind — so treat the widget code here as scaffolding, not as the eventual home of the UI. `Manager._place()` and `Panel`'s effects are written the way markup will compile, and are the closest thing in the repo to a worked example: `Manager` has no `layout()` at all, and `Panel` assigns `path` and lets the listing, cursor and scroll follow.

- `Manager` window with two file-listing panels
- View and Edit file windows
- File operations over the selected files
- Pluggable filesystem handlers so operations work over ssh, smb, inside zip archives, etc.
- Plugin system for third-party extensions
- Look and feel carefully recreated from Ritlabs' classic DOS Navigator (including its TETRIS easter egg)

## Working conventions

- Keep `navkit` free of any dependency on `navml` or the application; keep `navml` free of any dependency on the file manager. The dependency direction is strictly one-way.
- Prefer recreating original DOS Navigator behaviour over inventing modern alternatives when the two conflict — fidelity is the point of the project.

P.S. NEVER suggest to commit code, unless you are explicitly asked to do so.