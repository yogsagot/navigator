# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

Early. `navkit` has its event loop, terminal layer, screen buffer, reactive attributes, widget base, and a console layer
that runs child programs on a pty it owns; `navigator/__main__.py` is a working shell (menu bar, two live directory
panels, key bar, Ctrl+O console) that exercises them and is already written in the declarative style — its panels bind
their geometry to the desktop and derive their listing from a path rather than being placed and refreshed by hand.
`navml/` holds no code yet — the markup language, its parser, the code generator and the widget library are all
unwritten. The README sketches them. `navkit` itself is complete for what it does, the stylesheet and its lookup engine
included. What it does *not* have is the interaction layer a widget library needs — there is no focus notion, no signal
or custom-event mechanism, no mount/unmount lifecycle and no modal or overlay support — and each of those blocks buttons
and dialogs rather than the markup language. Decisions taken ahead of the code live in two design notes, and are where
the next one belongs: `navml/DESIGN.md` for the markup language, `navkit/DESIGN.md` for the core, whose *Still open*
section names what is left.

There is no lint tooling configured yet. When adding one, record the command here. Packaging is setuptools via
`pyproject.toml`: `./venv/bin/python -m build` (needs `pip install build`, and setuptools 77+ for the PEP 639
`license = "MIT"` expression the metadata uses).

The **distribution** name is `navigator-fm`; the **import** names stay `navigator`, `navkit`, `navml` and the command
stays `nav`. Plain `navigator` and `nav` were taken on PyPI before this project existed. Installation folds only runs of
`-`, `_` and `.` into one separator, but *registration* is stricter -- PyPI refuses a new name that collides with an
existing one once those characters are deleted outright, so `navigator-fm` reserves `navigatorfm` against everybody,
this project included; see below. Versions are placeholders in the 0.0.x series until the first real release, which
keeps 0.1.0; PyPI never lets a version number be re-used, so a botched upload costs a version rather than being
replaceable.

**The version is written in exactly one place**, `navigator/__init__.py`'s `__version__`. `pyproject.toml` declares
`dynamic = ["version"]` and reads it through `[tool.setuptools.dynamic]`, which setuptools resolves by parsing the
syntax tree rather than importing the package -- so it must stay a plain string literal, and the build needs none of
the run-time dependencies to find it. `packaging/navfm/pyproject.toml` deliberately does *not* track it: the alias
depends on `navigator-fm` unpinned, so it is re-uploaded approximately never.

Verify a build with
`./venv/bin/python -m twine check dist/*` and by installing the wheel into a throwaway venv and running `nav
--list-themes` from *outside* the checkout -- that is what proves the `importlib.resources` asset lookup survives
installation, which a run from the repository root cannot.

`nav --version` prints the version, the directory the running copy was imported from, and the interpreter, in
`pip --version`'s format. The path is the point: Navigator can be installed as a system package, a pipx copy and a
checkout at once, and `~/.local/bin` precedes `/usr/bin` on most PATHs, so the copy that runs is often not the one
that was just installed. `version_banner()` prefers `importlib.metadata` over `__version__` because the two diverge
exactly when a checkout has been edited since it was installed.

`packaging/navfm/` holds the one near-miss name worth holding, as its own project with its own `pyproject.toml`,
`README.md` and a copy of the root `LICENSE` (setuptools will not follow `license-files` out of a project directory).
It is an **alias, not a build of this code**: `packages = []` makes it a metadata-only distribution whose sole
dependency is `navigator-fm`, unpinned, so `pip install navfm` resolves to the current real release and never has to be
re-uploaded alongside it. Adding a module to it would defeat the point.

```
./venv/bin/python -m build -o dist .
./venv/bin/python -m build -o dist packaging/navfm
./venv/bin/python -m twine check dist/*
```

`navigator-fm` has to reach PyPI before the alias is installable, so upload it first. The alias chain is verified by
`pip install --find-links dist navfm` into a throwaway venv: it must pull `navigator-fm` and `pyte` in behind it and
leave a working `nav`.

`packaging/linux/` builds the `.deb` and the `.rpm`, both from one `nfpm.yaml`:
`NFPM=/path/to/nfpm PYTHON=./venv/bin/python ./packaging/linux/build.sh` after a `python -m build`. Output lands in
`build/pkg/` (gitignored). Three things about it are load-bearing:

- **The tree is staged by `pip install --target`, not by copying directories**, so the files that reach the package
  are exactly the ones the wheel declares -- `navigator/styles/*.nss` included. `build.sh` then asserts the stylesheet
  and all eleven themes are present, because losing them yields an application that starts and *then* fails to theme.
- **One `arch: all` / `noarch` package serves every interpreter from 3.12 up**, because every dependency is pure
  Python. A venv could not: it bakes its minor version into `lib/python3.N/site-packages` and into `pyvenv.cfg`, so it
  would need one build per distro. `build.sh` fails the build if a `.so` ever appears in the staged tree, since that
  is the moment the claim stops being true.
- **`/usr/bin/nav` runs `python3 -sP`, and the `-P` is not hygiene.** A file manager is launched inside arbitrary
  directories, and without it a directory that merely *contains* an `icons.py` or a `pyte.py` shadows the real module,
  so Navigator dies on startup in that one directory and nowhere else. This is verified, not assumed: dropping a
  decoy `pyte.py` into the working directory crashes `-s` and leaves `-sP` untouched.

`packaging/linux/repo/` publishes the two repositories, and `.github/workflows/release.yml` drives the whole release
from a `v*` tag: tests, then PyPI, then the packages, then the site. Four things there are not obvious:

- **The repository scripts add to a published site, they do not build one.** apt indexes by scanning the pool and
  `createrepo_c` by scanning the directory, so the previously released files have to be *present* or the new index
  silently forgets them and every pinned or older install breaks. The workflow checks out `gh-pages` first for that
  reason, and passes `EXPECT_AT_LEAST` -- the count read off the live site -- so the scripts refuse to publish an index
  smaller than reality. Comparing before with after inside one run cannot catch this: a run that started from an empty
  directory has nothing to lose, which is exactly the failing case.
- **`GPG_KEY_ID` must be the *signing subkey's* 16-hex-digit long key id**, and each half of that sentence was paid
  for. nfpm parses it as a 64-bit integer, so a 40-character fingerprint is `value out of range` -- and so is a
  17-character one, which is what `make-signing-key.sh` printed until it stopped slicing the id off the end of the
  fingerprint. Given the *primary's* id nfpm fails differently and far less helpfully, with `no valid signing keys`:
  CI holds an `--export-secret-subkeys` export, so the primary is a stub with no private key, and it is certify-only
  besides. `ghaction-import-gpg` has the same blind spot from the other side -- without its `fingerprint` input it
  presets the passphrase against the stub primary's keygrip and dies on gpg-agent error 67108891 (source 4,
  code 27, `NOT_FOUND`) before nfpm is ever reached. gpg itself is the relaxed one: `--local-user` takes a subkey id
  without complaint, which is why the repository scripts never noticed the question. `release.yml`'s
  published-key check therefore matches `GPG_KEY_ID` against **both** the `pub` and `sub` records of the committed
  keyring; matching `pub` alone rejected precisely the value that works.
- **The two ecosystems verify different things.** apt verifies the *index* (`InRelease`/`Release.gpg`) and takes
  per-package integrity from the SHA256 in `Packages` -- it does not check per-package signatures at all. dnf is the
  reverse: `gpgcheck=1` verifies a signature inside each `.rpm`, which nfpm has to write at *build* time, and
  `repo_gpgcheck=1` verifies `repomd.xml.asc`. Signing only one half of either leaves a repository that warns or
  refuses.
- **CI signs with a subkey.** `make-signing-key.sh` exports `--export-secret-subkeys`, so the certifying primary never
  leaves the maintainer's machine and a leaked CI secret can be revoked without users having to trust a new key.

The apt half is verified end to end without Docker: point the real `apt-get` at a private `Dir::State`/`Dir::Cache` and
a `file://` source, and it accepts the signed repository, lists both published versions and refuses the same repository
under a different key (exit 100, `NO_PUBKEY`). The rpm half has no such local check -- `createrepo_c` and `rpm` are not
installed here -- and is exercised only in CI.

`native_version.py` maps a PEP 440 version onto the Debian and RPM spelling, and `tests/test_packaging.py` checks the
result against `dpkg --compare-versions` rather than against a table -- what matters is the ordering, not the string.
A pre-release takes `~` so it sorts *below* its release; `.devN` takes **two**, because past a single tilde `a` < `d`
would put `~dev5` after `~a1` and invert PEP 440. That inversion is asserted in the tests so the reason cannot be
optimised away.

**Do not add a `packaging/navigatorfm/` back.** It was tried and PyPI answered `400 Bad Request`. PyPI "ultranormalises"
a proposed new name -- separators deleted rather than folded, and confusable characters such as `l`/`1`/`i` and `0`/`o`
run together -- and refuses it if the result matches an existing project. `navigator-fm` ultranormalises to
`navigatorfm`, so that spelling is already reserved against everyone and is unregisterable by us for the same reason.
The 400 carries no explanation (warehouse#17375), which is what makes this worth writing down. The same rule is why
`navfm` is a separate name and does have to be held deliberately.

The application lives in the `navigator/` package: `navigator/__main__.py` is the whole of it, and `navigator/styles/`
holds the assets it loads. Assets are found through `importlib.resources` rather than relative to `__file__`, and
`navigator/styles/*.nss` is declared as package data — a new asset directory needs a matching
`[tool.setuptools.package-data]` entry or it will work from a checkout and vanish on install. `navigator/styles/themes/`
is the second such directory and carries its own `__init__.py` and package-data entry for that reason.

Colour is split from structure and neither half is authored by hand. `navigator/styles/navigator.nss` holds the rules
and defines no variable, so it does not parse alone; `navigator/styles/themes/*.nss` define every variable and no rule,
and one is always loaded after it (`load_scheme("norton")`, `python -m navigator --theme norton`). The themes are
generated: each is a DOS Navigator `COLORS/*.PAL` palette decoded by `tools/palconv.py`, which documents the file format
in full and — the part that took the work — which of the 228 attribute bytes means what. Re-derive rather than hand-edit
a theme.

The slot table comes from `RESOURCE/ENGLISH/DN.DNR` in the DOS Navigator source — the script the resource compiler turns
into the `dlgColors` resource — which names all 144 entries the Colors dialog exposes, in 20 nested groups, as
`COLORITEM <name>, <index>` lines. Every theme carries all 144, so a `.nss` is a full transcription of its `.PAL`;
`navigator.nss` reads eight of them today and the rest are marked `>`-less and inert.
`palconv.py --names path/to/DN.DNR` regenerates the table. Twenty-three entries also carry the Turbo Vision
palette-string chain that independently arrives at the same index; the two routes were worked out separately and agree
everywhere, which is what makes the other 121 trustworthy. Group names repeat across the tree (two `Tree`s, two
`Highlight`s, two `Menu`s), so variables are stemmed by group *path*, and a published variable name is API —
`HAND_NAMED` pins the ones `navigator.nss` uses.

The 84 entries `DN.DNR` does not name are ones DOS Navigator never let the user set, and are not carried.

## Environment and commands

- Python 3.12, virtualenv at `venv/` (not tracked): `source venv/bin/activate`
- One run-time dependency, `pyte`, and it is load-bearing: it is the VT emulator behind `navkit/console.py`, which is
  what makes Ctrl+O possible at all — install it with `./venv/bin/pip install -r requirements.txt`. Everything else is
  stdlib. Test tooling lives in `requirements-dev.txt`: `./venv/bin/pip install -r requirements-dev.txt`
- Run the file manager: `./venv/bin/python -m navigator [LEFT_DIR] [RIGHT_DIR]` (Tab switches panels,
  arrows/PgUp/PgDn/Home/End move, Enter descends, Ctrl+R rescans, Ctrl+O shows the console and Shift+PgUp/PgDn scrolls
  it back, F10 or Ctrl+Q quits). `--theme NAME` picks a colour scheme, `--list-themes` names them, `--palette terminal`
  gives the terminal's own scheme back the sixteen colour names, `--glyphs {auto,ascii,unicode,nerd}` overrides what the
  terminal's font is assumed to draw
- Regenerate the colour schemes from a DOS Navigator distribution:
  `./venv/bin/python tools/palconv.py path/to/DN/COLORS --out navigator/styles/themes`; `--dump ONE.PAL` prints one
  palette's decoded slots instead
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

## Intended architecture

Navigator is a faithful recreation of the DOS Navigator two-panel file manager for modern POSIX terminals. It is layered
in three parts, each depending only on the one below it:

### `navkit/` — application core (lowest layer, no widget library knowledge)

Written, and the pieces fit together like this:

- `application.py` — `Application` owns the only asyncio loop. Terminal input arrives through a `loop.add_reader`
  callback that feeds `InputParser` and queues the resulting events. The order in one turn is fixed: **dispatch the
  whole batch, flush the reactive effects it queued, then paint one frame** — so a paste or a mouse drag costs a single
  repaint, and nothing reactive runs during the paint. `SIGWINCH` becomes a `ResizeEvent`; events reach the
  `Application.on_*` hooks first and the widget tree second.
- `terminal.py` — `Terminal` owns the tty (raw mode, alternate screen, mouse tracking, bracketed paste, autowrap off)
  and restores it in `Application`'s `finally`. `InputParser` is fed incrementally and keeps undecodable tails, so
  sequences split across reads still decode. A lone `ESC` is inherently ambiguous: the parser reports `pending_escape`
  and the application resolves it with an `ESCAPE_TIMEOUT` timer.
- `screen.py` — `Surface` is what widgets paint into. `ScreenBuffer` is the one that owns cells;
  `surface.view(x, y, w, h)` returns a shifted, clipped window onto another surface that owns nothing and forwards.
  `render_tree` hands each widget a view of its own area, so **widgets paint from `0, 0` in their own size and cannot
  draw outside themselves** — no `self.x +` arithmetic, no manual bounds checks, and a wide character at a widget's
  right edge degrades to a blank instead of spilling onto its neighbour. Drawing still clips silently, and double-width
  characters occupy a cell plus an empty continuation cell. `render_diff()` emits only the escapes needed to turn the
  last flushed buffer into the new one, comparing each row whole before walking its cells, and repaints fully when the
  size changed.
- `glyphs.py` — the character sets a frame is drawn from (`single`, `double`, `round`, `ascii`) and the tiers that
  govern them. Imports nothing, which is what lets `screen.py` keep having no runtime import of `capabilities.py`:
  `draw_box` takes the six characters themselves, never a name for them, so the buffer never learns that a tier exists.
  A widget resolves the two halves with `Widget.box_charset()` — the sheet says which set is *wanted*, the tier says
  which can be *shown*, and either vetoes.
- `style.py` — `Style` is an immutable cell appearance that knows its own SGR sequence. Nothing else writes colour
  codes.
- `capabilities.py` — `TerminalInfo` is what the terminal supports (`colors`, `alt_screen`, `mouse`, `bracketed_paste`,
  `title`), what a palette index *means* (`palette`), and the decisions that follow. `Terminal` detects one at
  construction and gates its escapes on it; `render_diff(previous, current, info)` is where a colour the terminal cannot
  name is quantised to one it can. **That is the only place the question is asked** — a widget asks for the colour it
  wants and a sheet records the colour the original asked for, so nothing upstream degrades anything. A palette *index*
  is passed through untouched **unless a palette is pinned**: with `TerminalInfo.palette` unset — navkit's default —
  `blue` stays whatever the user's terminal theme paints, and with `VGA_PALETTE` set it means the register value the DOS
  original asked for. `navigator` pins by default, because a theme that names a colour is transcribing a `.PAL` that
  left the VGA registers alone; `--palette terminal` hands the question back. Pinning is a no-op below 256 colours — an
  index resolved through the palette quantises straight back to itself — so only a terminal that can do better sees a
  difference, and `--reprogram-palette` (OSC 4, reset with OSC 104) is the opt-in that reaches the ones that cannot.
  Detection is conservative — sixteen colours unless `COLORTERM` says otherwise — and `NAVKIT_COLORS` (`truecolor`,
  `256`, `16`, `8`, `mono`, or a number) overrides it, outranking `NO_COLOR`; `NAVKIT_PALETTE` (`dos`/`vga`, `terminal`/
  `none`/`off`) does the same for the palette, and `--palette` outranks it.
  `TerminalInfo.glyphs` is the same question asked about *characters* — `GLYPHS_ASCII` < `GLYPHS_UNICODE` <
  `GLYPHS_NERD`, `NAVKIT_GLYPHS` overriding and `--glyphs` outranking that. **A font cannot be detected**: no escape
  sequence reports one, and the cursor-position probe measures the terminal's width table rather than the font's
  coverage. So the Nerd tier is granted only to emulators that *bundle* a Nerd Font fallback (kitty, WezTerm, Ghostty)
  or to a session that says so itself; a multiplexer hides all of it and needs the override. Guessing too high costs a
  replacement box on every line, so a non-UTF-8 locale gets ASCII rather than the benefit of the doubt.
- `reactive.py` — observable attributes and the bindings between them; the mechanism `navml` markup relies on.
  `reactive()` declares a source, `computed()` a derived value, and assigning `obj.attr = bind(expression)` attaches an
  expression to *one instance* — which is what markup compiles to. `bind()` only wraps the expression in a `Binding`;
  the descriptor recognises one on assignment and installs it instead of storing a value, so the target is named by a
  real attribute reference rather than by a string. The three calls that have to name an attribute without assigning to
  it — `unbind(obj, Widget.width)`, `is_bound()`, `peek()` — take the class attribute itself, which is the declaration
  object. Dependencies are discovered by running the expression and noting what it read, so a conditional subscribes
  only to the branch it took. Propagation is push-pull: a write eagerly marks dependents stale, values are recomputed
  lazily on read and memoised. That makes it glitch-free (a diamond recomputes once, from inputs that are all final) and
  mirrors the frame loop one layer up. `effect()` is the only eager node, for reactions that must happen whether or not
  anybody reads a value.
- `widget.py` — `Widget` has children, `render(surface)`, `layout(width, height)` (called on the root at every resize)
  and `dispatch_key`/`dispatch_mouse`, which offer events to the topmost child first. Its geometry, `visible`, `style`
  and `parent` are reactive, so assigning one asks for a repaint on its own; `layout()` steps around any size that
  carries a binding. **All coordinates are relative to the parent** — `x`/`y`, `contains()`, and the position a
  `MouseEvent` carries, which `dispatch_mouse` shifts as it descends. Only the root sits in screen coordinates, and it
  sits at the origin.

- `console.py` — the screen a *child program* paints on, and the mirror image of `terminal.py`: there, bytes from the
  user become events; here, bytes from a program Navigator started become cells. The emulation is `pyte`; what lives
  here is the translation. **A terminal will not give its cells back** — no escape sequence returns screen contents, and
  `navkit/DESIGN.md` records every route that was surveyed and rejected — so the only way to show a program's output
  behind the panels, as the DOS original did by reading video memory, is to have been the one who received it.
  `ConsoleScreen` keeps a `ScreenBuffer` mirror in step with pyte's sparse grid, converting only the rows pyte marks
  dirty; `seed_from_host` makes a best-effort grab of whatever was on screen *before* Navigator started, from tmux,
  kitty or `/dev/vcsa`, and usually fails, which is expected.
- `process.py` — `PtyProcess` runs a child on a pty this application owns, reading it through `loop.add_reader` and
  sizing it with `TIOCSWINSZ` on the master (the kernel raises `SIGWINCH` on the child itself, so nothing signals it by
  hand). `run_on_terminal` is the escape hatch for a program that needs the real terminal, and its output is *not*
  captured — which is the trade the whole module exists to avoid.

Things to know before touching this layer:

- **Assigning a *value* over a live binding raises**, deliberately: call `unbind()` to take an attribute back by hand.
  Assigning another `bind()` expression is fine and replaces the old one. This is why `Widget.layout()` checks
  `is_bound()` — without it the first `SIGWINCH` would take down every declaratively-sized widget in the tree.
- **A `bind()` expression assigned to a non-reactive attribute is silently stored**, because there is no descriptor to
  notice it. A `computed` target raises, and an unknown `Widget()` keyword raises, so what is left is a typo on a plain
  attribute; the `Binding` repr (`<unassigned binding ...>`) is what gives it away.
- **A computed may not write.** The write path refuses if any frame on the tracking stack is a computed, which is what
  makes it safe to pull a stale value in the middle of composing a frame. Use an `effect` for anything impure.
- **A collection has to be replaced to count as changed.** `entries.append(x)` followed by `self.entries = entries`
  propagates nothing, because the equality guard sees the same object. Build a new list.
- An object carrying reactive attributes needs a `__dict__`, so slotted value types (`Style`, `DirEntry`) cannot host
  them.
- **A console screen is not reactive and cannot be.** It is a great deal of mutable state that changes together, so
  `Console.revision` is one counter standing in for all of it: `render()` reads it for the dependency and the output
  callback bumps it. Anything mutating the screen behind the widget's back — scrollback, a reset — has to bump it too.

- `stylesheet.py` — the `.nss` language and its lookup engine. CSS in shape (selectors, brace-delimited declarations, a
  cascade ordered by specificity) and not in scope: every declaration either names a `Style` field or names a property
  the widget interprets. `parse()` reads one sheet, `load()` merges several in order so a theme can redefine another's
  variables. Selectors are `Panel` (by class *name*, subclasses included), `.tag`, `:state` (any truthy attribute),
  `#name` and `Panel::part`, with descendant and child combinators. Specificity is CSS's
  `(names, classes + states, types)`, ties break on source order, and there is no `!important`.

Things to know before touching the style layer:

- **A widget's `style` is a `computed`, not a value you assign.** It cascades in four levels: the parent's resolved
  style (so appearance inherits), then matching `.nss` rules, then `inline_style`, then whatever `render()` passes
  straight to a drawing primitive. Assigning `widget.style` raises; author through `inline_style` or `merge_style()`.
- **`inline_style` is partial.** `"bg: red"` overlays one property and leaves the rest inheriting; it is not a whole
  `Style`. A `Style` is accepted and becomes the seven declarations it makes.
- **`classes` is a `frozenset` and `inline_style` is replaced, never mutated** — the reactive layer only counts a change
  when a collection is replaced. Use `add_class` / `remove_class` / `merge_style`.
- **Only a *reactive* attribute restyles.** `:state` matches any truthy attribute, but a plain one is read outside the
  dependency graph: it matches the first time and never invalidates afterwards.
- **Widget properties do not inherit**, only `Style` fields do. `border: double` on a panel does not give its children a
  frame. Register a non-`Style` declaration name with `stylesheet.register_property()` or the parser rejects it.
- `navkit/DESIGN.md` records why each of these went the way it did, including the parts that were measured rather than
  argued. Add to it rather than re-deciding.

- A widget may carry its own sheet in `_stylesheet`, governing the subtree under it; the nearest one wins and the search
  ends at the application's. `Manager` uses this, so the desktop is styled with or without an application around it.

### `navml/` — markup language + widget library

- `*.nml` markup language: QML for the architecture (a declarative tree, `id`s, properties that are re-evaluated
  expressions), Kivy for the syntax (blocks made by indentation, no braces, no semicolons, one property per line)
- Parser translating `.nml` into a node graph
- Code generator traversing that node graph to emit a Python class
- The generated class is silently merged with a hand-written Python module holding the event handlers; Python's import
  machinery is overridden so a single `import` yields the merged class. This import hook is the crux of the layer —
  `.nml` files and their sibling `.py` handler modules are two halves of one class.
- Rich widget library (windows, buttons, menus, labels, standard event handlers) modelled on Borland's TurboVision

Nothing here is written yet, but `navml/DESIGN.md` records the decisions already made — currently how a property
expression (`width: parent.width // 2`) is compiled into the one-argument lambda `bind()` expects, by rewriting the
expression's free names on the syntax tree rather than by formatting strings. Read it before starting the parser or the
generator, and add to it rather than re-deciding.

### `navigator` / `nav` — the file manager application

`navigator/__main__.py` currently holds the whole application: `Manager` (the desktop), `MenuBar`, `Panel`, `KeyBar` and
the `Navigator` application subclass, all painting by hand. These screens move into `*.nml` markup once navml exists,
leaving only event handlers behind — so treat the widget code here as scaffolding, not as the eventual home of the UI.
`Manager._place()` and `Panel`'s effects are written the way markup will compile, and are the closest thing in the repo
to a worked example: `Manager` has no `layout()` at all, and `Panel` assigns `path` and lets the listing, cursor and
scroll follow.

- `Manager` window with two file-listing panels, and a `Console` covering the band they share. Ctrl+O swaps them, which
  is one reactive flag that three `visible` bindings read; the menu bar and key bar are simply left alone, which is why
  they stay painted over the output and why this is DOS Navigator's Ctrl+O rather than Midnight Commander's
- View and Edit file windows
- File operations over the selected files
- Pluggable filesystem handlers so operations work over ssh, smb, inside zip archives, etc.
- Plugin system for third-party extensions
- Look and feel carefully recreated from Ritlabs' classic DOS Navigator (including its TETRIS easter egg)

## Working conventions

- Keep `navkit` free of any dependency on `navml` or the application; keep `navml` free of any dependency on the file
  manager. The dependency direction is strictly one-way.
- Prefer recreating original DOS Navigator behaviour over inventing modern alternatives when the two conflict — fidelity
  is the point of the project. The **one standing exception** is the Nerd Font icon gutter in `Panel`, which the
  original had no glyphs for; it was taken deliberately, is on only where the font is known to exist, and is reversible
  with `icons: none` or `--glyphs unicode`. `navkit/DESIGN.md` records the argument — don't re-litigate it, and don't
  read it as licence for the next modern flourish.

P.S. NEVER suggest to commit code, unless you are explicitly asked to do so.