---
name: navml-components
description: How a navml component is put together and built -- the markup half and hand-written half, `*_nml.py` / `.pyi` generated artefacts, component directories and groups, `navml/_merge.py`'s splice and finder, `navml.register`, lazy re-exports, `navml.component.Component`, and the parser/generator modules (parser.py, expression.py, sibling.py, resolve.py, checks.py, generator.py, stubs.py, build.py, coder.py). Use when adding or moving a component, or changing the toolchain.
---

# navml components and the toolchain

## Four files, two optional halves

`button.nml` is the markup; `button_nml.py` is what the generator emits from it (tracked and shipped); `button.py` is
the hand-written handlers; `button.pyi` the generated stub. Markup alone, Python alone, and both are three peer shapes,
and `from navml.widgets.dialog.button import Button` is the same line for all three.

- **A component that paints has two halves by construction.** Markup declares and places; Python paints (`Label` gained
  a `label.py` for this; `field.nml` is the markup-only example). Conversely `CheckBoxes`/`RadioButtons` lost their
  markup halves: a document holding nothing but a head says only what its `class` statement says.
- **The merge is one line**, `handwritten.__bases__ = (generated,)`; the generated class is always the base, so a
  hand-written `__init__` calls `super().__init__()` and finds every id live.
- **The hand-written half never names the generated class** -- `class Button(Widget)` is what a Python-only component
  says too. The loader refuses the pair if its base disagrees with the markup's (CPython would drop it silently).
  A class based only on `object` cannot be spliced (`deallocator differs from 'object'`).
- The generated class always names `navml.component.Component` (`class Label(_Component)`,
  `class FramedButton(Button, _Component)`), which holds the `layout()` override, `__navml_source__`, and the
  keyword-property constructor. **`Component { }` is a live `.nss` selector** matching every markup-built widget (type
  selectors match by class *name*); it reads *built from markup*, never *is a component* (`spacer.py` is a component and does not match).
- **The generated class constructs children inline in `__init__`**, not a `_build()` method (a derived component's would
  override it). **A derived component's own children land after its base's** -- `Dialog.focusable()` moves its buttons
  to the end for this.

## A component is a directory; components come in groups

- The files live in `navml/widgets/dialog/button/` beside an `__init__.py` re-exporting the class (and any event it
  declares). **Files repeat the directory's name** (`packaging/linux/build.sh` finds siblings by stripping `_nml.py`).
  **Every component gets a directory**, Python-only ones too. The flat shape stays legal (`tests/test_nml_build.py`'s
  `package` fixture is flat on purpose).
- Groups: layouts under `navml/widgets/layout/`, the *Dialogs* components under `navml/widgets/dialog/`, menus under
  `menu/`; `Window`, `Desktop`, `Timer`, `Spacer` at the top. Navigator groups the same way (`shell/`, `manager/`,
  `file_ops/`, `tree/`, `viewer/`, `editor/`). A group's `__init__.py` is a docstring and never re-exports;
  `_COMPONENTS` (navml) / `_WIDGETS` (navigator) map a name to its dotted path (`"dialog.button"`), so
  `from navml.widgets import Button` is unchanged.
- **The library registers, not the component**: `navml.register("navml.widgets")` once; `_registered()` walks up the
  dotted name. A component package registers itself in its `__init__.py` (not a `.pth`: the `.deb`/`.rpm` use
  `PYTHONPATH`).
- **A package `__init__.py` must not re-export eagerly** -- generating a component imports the ones it uses, so eager
  re-export would import everything. `navml/widgets/__init__.py` uses a PEP 562 `__getattr__` with a `TYPE_CHECKING`
  block.
- Silent failure modes fixed once: `build.order()` keys its graph on the directory name as well as the module's, and
  `build._forget()` evicts the component's package with its module.

## The finder

- **It keys on `button_nml.py`, never `button.nml`**, so both halves are ordinary `.py` files that reach a wheel. The
  markup ships anyway via one `"*" = ["*.nml", "*.pyi"]` entry in `[tool.setuptools.package-data]`.
- **A component is a module, never a package**; the finder refuses to claim a package (a stale flat `button_nml.py`
  beside a `button/` directory would otherwise splice onto an old base).
- **A component module must never be a test module, `conftest.py` or pytest plugin** -- pytest's assertion rewriter
  bypasses `sys.meta_path`, so the splice would not happen.

## The parser and the generator

- **The parser imports nothing the document names.** Every check a document can fail alone is `navml/parser.py`'s
  (structure, identifiers, reserved words, self-collisions); every check needing a live class is the generator's.
  `parse(text)` / `parse_file(path)` return a `Document`; `imports_of(path)` reads only the import block, which orders a
  cold build without executing anything. `navml/errors.py`'s `MarkupError` is the one exception both raise.
- **The generator is seven modules in a one-way chain**: `expression.py` compiles an expression or handler body by
  rewriting free names on the syntax tree; `sibling.py` reads the hand-written `.py` **without importing it**;
  `resolve.py` is the only module importing what a document names; `checks.py` refuses what a live class reveals;
  `generator.py` and `stubs.py` emit the two artefacts; `build.py` orders a directory by import graph and writes.
  `navml/_alias.py` is run-time support beside `component.py`.
- **Anything emitting code goes through `navml/coder.py`'s `Coder`** (line buffer, logical indents, trailing comments),
  never string assembly or whole-module `ast.unparse` -- `ast` carries no comments and the source map *is* comments
  (`# button.nml:12`).
- The generated file never reads the sibling `.py` to decide what to emit, so there is no `--check` drift.
- navkit grew for navml: a public `Declaration`, `Binding.owned_by(owner)`,
  `stylesheet.check_declarations(text, *, line, filename)`.

## Read when

| Reference | Read when |
|---|---|
| `reference/overview.md` | where navml's inspiration comes from (QML, Kivy) |
| `reference/two-halves.md` | the two halves, directories, groups, deriving, the import machinery, shipping markup |
| `reference/shared-base.md` | `Component`, how a value gets in, no required ctor args, navigated properties, a component's sheet |
| `reference/parser.md` | the parser: comments, continuation, root id, node graph |
| `reference/generator.md` | what the generator emits, source mapping, converting `Manager`, what writing it settled |
| `reference/still-open.md` | open questions for the language/toolchain |
| `reference/appendix-transformer.md` | the expression transformer prototype |
