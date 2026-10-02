## The two halves of a component

A component is written as markup, as Python, or as both, and **either half may be absent**. All three reach the same
public module name, so nothing importing a component can tell which it is looking at:

| shape       | files in `navml/widgets/dialog/button/`                        | what backs `navml.widgets.dialog.button.button`              |
|-------------|---------------------------------------------------------|-------------------------------------------------------|
| Python only | `button.py`                                             | nothing of navml's — the stock `PathFinder`           |
| markup only | `button.nml` → `button_nml.py`, `button.pyi`            | the generated module, re-homed onto the public name   |
| both        | the above, plus `button.py`                             | `button.py`, with the generated class spliced beneath |

- **`button.nml`** — hand-written markup. It ships, and it is the one file in the set that nothing at run time reads;
  see *The markup ships* below.
- **`button_nml.py`** — generated, tracked, shipped. `class Button(_Component)`: the tree and the bindings. The
  `layout()` override moved onto the shared base once there was one — see *The shared base, and how a value gets in*.
- **`button.py`** — hand-written. `class Button(Widget)`: the handlers. **It never names the generated class**, which is
  the whole of *Why the hand-written half never names the base* below.
- **`button.pyi`** — generated, tracked, shipped. Emitted whenever `button_nml.py` is, because in the markup-only shape
  it is the only thing a type checker can see for that module name.

### A component is a directory

Four files per component in one flat package is 22 files in two directories before the widget library has been
started, and every widget it gains adds up to four more. So **each component lives in a directory of its own**, with
an `__init__.py` beside the four that re-exports the class:

```
navml/widgets/dialog/button/__init__.py      from navml.widgets.dialog.button.button import Button
navml/widgets/dialog/button/button.nml
navml/widgets/dialog/button/button.py
navml/widgets/dialog/button/button_nml.py
navml/widgets/dialog/button/button.pyi
```

When components first became directories, `from navml.widgets.button import Button` was unchanged, and so was
`from navml.widgets import Button`. The directory took the name the module had, so **no document, no hand-written half
and no call site was edited by that move.** Grouping them later did change the first line, as *Components come in
groups* below records. Four
things about it were decided rather than fallen into:

- **The files repeat the directory's name** rather than being `component.py`. Everything navml prints is a bare
  filename — `__navml_source__`, the `# button.nml:12` source map, `--check`'s `button_nml.py: stale from line 14`,
  `MarkupError`'s `button.nml:12:` — and a generic name would make every one of those ambiguous across components.
  `packaging/linux/build.sh` relies on it too: it finds a component's three other files by stripping `_nml.py`.
- **Every component gets one, including the ones written in Python alone.** `spacer/` holds a single `spacer.py`.
  The directory is what a component *is*, so gaining a markup half adds files instead of moving them — which is what
  keeps `spacer.py`'s own claim (*adding a `spacer.nml` later would not change one line of this file*) literally true.
- **The library registers, not the component.** `navml.register("navml.widgets")` is still the one call, and
  `_merge._registered` walks up the dotted name to find it. A component directory has no reason to know it is one —
  the same argument that keeps navml's mark off the class — so its `__init__.py` is a docstring, an import and an
  `__all__`, and there is no line to forget when a component is added.
- **The flat shape stays legal.** Nothing in the language or the loader requires a directory; a package whose
  component modules sit straight in it still works, and `tests/test_nml_build.py`'s `package` fixture is deliberately
  flat so that it keeps being exercised.

Two things had to change underneath, and both failed silently rather than loudly, which is why they are recorded here.
`build.order()` keyed its dependency graph on where a document's module really is (`navml.widgets.dialog.button.button`)
while every document imports the directory (`navml.widgets.dialog.label`) — so every edge vanished and the topological sort
fell back on the alphabet, which compiles `button.nml` before `label.nml` and breaks a cold build with a complaint
about an undeclared property. `_names_of` now yields both names. And `build._forget()` evicted the module it had just
rewritten but not the component's package, which holds a binding to the very class the write replaced — so a second
build in one process resolved later documents against the class from before it. Both have a regression test that was
checked to fail without its fix.

What a component *package* deliberately does not do is re-export lazily. It imports its own one module and nothing
else, so the laziness that matters — one component not dragging in the library — stays entirely `navml/widgets/
__init__.py`'s job. And an event a component declares is part of its surface, so it is re-exported too:
`navml/widgets/dialog/button/__init__.py` publishes `ClickEvent` beside `Button`.

### Components come in groups

A family of components shares a **group directory**, and each member is a component directory exactly as above.
There are two groups:
- `navml/widgets/layout/` holds `layout/` (the `Layout` base and `LinearLayout`), `horizontal_layout/`,
  `vertical_layout/`, `grid_layout/`, `dock_layout/` and `stack_layout/`.
- `navml/widgets/dialog/` holds the thirteen components the Colors dialog's *Dialogs* group names: `control/`,
  `cluster/`, `static_text/`, `label/`, `button/`, `input_line/`, `check_boxes/`, `radio_buttons/`, `scroll_bar/`,
  `list_viewer/`, `modal/`, `dialog/` and `field/`.

**The application's widgets follow the same rule.** `navigator/widgets/` groups its screens by what the user is
doing: `shell/` (the root `Shell`, `Console`, `KeyBar`, `MainMenu`, `Clock`, `CommandLine`, `CompletionList`),
`manager/` (`Manager`, `Panel`, `SelectDialog`), `file_ops/` (copy, move, link, mkdir and erase: dialogs, progress
boxes and queries), `tree/`, `viewer/` and `editor/`, with `about_dialog/` alone at the top. `shell` and `manager`
have a central component of the group's name; the other four, like `menu/`, do not. The group names do not collide
with the model packages `navigator.viewer` and `navigator.editor`, because every import is absolute.

`Window`, `Desktop`, `Timer` and `Spacer` belong to neither group and stay at the top. The import names one level deeper —
`from navml.widgets.layout.horizontal_layout import HorizontalLayout` — while `from navml.widgets import
HorizontalLayout` is unchanged, because `_COMPONENTS` maps a name to a dotted path under the library
(`"layout.horizontal_layout"`) and the lazy `__getattr__` imports whatever that path names.

- **A group's `__init__.py` is a docstring and nothing else.** It is not a component, and re-exporting its members
  would make importing one layout import all six — the eager re-export `navml/widgets/__init__.py` exists to avoid.
- **The base lives in the group as a component of its own**, `layout/layout/`, rather than as a loose `layout.py`
  beside the group's directories. Every component gets a directory, and the rule holds one level down. That spells
  the base's module `navml.widgets.layout.layout.layout`, which is ugly but not ambiguous, and nobody outside the
  group imports it by that name.
- **A group is named for its family, and the family's central component takes the same name one level down.** So
  `navml.widgets.dialog` is the group, and `Dialog` is `navml.widgets.dialog.dialog`, whose module is
  `navml.widgets.dialog.dialog.dialog`. `layout` works the same way. When a component moves into a group, every import
  of it changes, including a derived document's (`mkdir_dialog.nml` now says
  `from navml.widgets.dialog.dialog import Dialog`). `from navml.widgets import Dialog` does not change.
- **Nothing underneath had to learn about depth, and markup components prove it.** A cold build of a copy with every
  `_nml.py` and `.pyi` deleted regenerates all 28 files byte-identical to the tracked ones, with the markup halves of
  `dialog/` one level down. The tests' `shipped()` helpers find a component by name (`rglob`, with the parent
  directory matching the stem) rather than at a fixed depth.
- **Nothing underneath had to learn about depth.** Registration walks up the dotted name, which works at any depth.
  `build` finds documents with `rglob`. The every-package `"*"` key in `package-data` ships markup at any depth. And
  `build.sh` strips `_nml.py` from a bare filename.

The original sketch spelled the generated file `button.nml.py`. A dot makes it unimportable by name — `import
navml.widgets.dialog.button.nml` splits on the dots — so no checker, no IDE and no `pkgutil` ever sees the class the
hand-written half inherits from, which forecloses the id-annotation question in *Still open*. setuptools' `build_py`
also globs `*.py` and ships it as a module literally named `button.nml`.

**A component is not a kind of object, and the mark that is missing is the one on the *class*.** Registration exists,
twice over, and both times at the granularity the machinery actually asks at: `navml.register(__name__)` per package,
because the finder is per package, and `__navml_component__` per generated module, because the splice is per module.
Neither wants a class, and no class carries a navml base, a decorator or a metaclass. `navml/widgets/spacer/spacer.py` is the
proof: `navml/_merge.py` claims that module nowhere at all, an ordinary `navkit.Widget` subclass already *is* a
component, and giving it a `spacer.nml` later changes not one line of it.

The reason is *Why the hand-written half never names the base*, below, arriving one level up: the three shapes are
interchangeable only if the Python-only row needs nothing. A marker base would also reach outside this package —
`Manager`, `Panel` and `Console` in `navigator/__main__.py` would each have to import navml in order to be
*convertible*, and the plan under *What converting `Manager` needs and does not have* is to compile a `.nml` and check
the frames still match, with no edit to a class line.

**Two of the four mechanisms do not work, rather than having been declined**, and both were measured:

- **A metaclass is not run by the splice.** `__bases__` assignment does not re-create the class, so after
  `handwritten.__bases__ = (generated,)` with a metaclass on the generated side, `type(handwritten)` is still `type`,
  the metaclass's `__new__` never ran for it, and `isinstance(handwritten, Meta)` is **False**. A metaclass would be
  inert on exactly the half that most wants checking, and a metaclass-based componenthood test would answer *no* for
  every merged component.
- **A decorator on the hand-written half sees `(Widget,)`.** It runs at class creation, which is before
  `RebaseLoader.exec_module` assigns `__bases__` — so it cannot see the generated base, the ids or the markup, and
  could register a name and nothing else.

**What this does not close is provenance**, and that is now answered elsewhere. *Is this class a component?* and *was
this class built from markup, and from what?* are different questions, and only the first is refused here. The second
is answered by both of the shapes sketched here at once, which turned out not to be a choice: the **generated** half
alone declares a base (`_check_bases` passes on `issubclass(Component, Widget)`, and the merged MRO gains one entry),
and that base declares `__navml_source__`, which the generator fills with the document's name. See *The shared base,
and how a value gets in* below. Neither reaches the hand-written half, which no more names them than it names the
generated class. One thing has to be said wherever it lands: such a test is **asymmetric** — true for a markup component and
false for a Python-only one — so it answers *built from markup*, and may never be read as *is a component*.

### Why the generated half is the base

Forced, not chosen: the contract under *Ids* says a hand-written `__init__` calls `super().__init__()` and then finds
every id live, which only holds if the generated class is further along the MRO. The merge is therefore one line,
`handwritten.__bases__ = (generated,)`, and everything in `navml/_merge.py` exists to reach that line safely.

### Why the hand-written half never names the base

The reason is not taste, and it is not hiding for its own sake: **it is what makes the three shapes interchangeable.**
`class Button(Widget)` is exactly what the Python-only row says too, so adding a `.nml` to an existing Python component
requires no edit to its `.py`, and deleting one leaves a file that still works. Were the base named explicitly, the two
rows would need different source and every transition between them would be a hand edit.

Four ways to join the halves were measured. All work at run time; they differ entirely in what everything *else* sees:

| the hand-written half opens with            | mypy on that file                                  | loaded without the hook              |
|---------------------------------------------|-----------------------------------------------------|---------------------------------------|
| `class Button(_Button):`, base imported     | clean, ids included                                 | works                                 |
| `class Button(Widget):`, base spliced in    | `"Button" has no attribute "caption"`               | imports; `AttributeError` on first id |
| `class Button:`                             | also loses `width`, `add`, every `Widget` member    | **cannot be spliced at all**          |
| `class Button(Button):`, name injected      | `Cannot resolve name "Button" (possible cyclic …)`  | `NameError` at import                 |

The last row is the literal reading of "silently merges", and it is the worst: the file is not a valid Python module on
its own. The third is worse than it looks — CPython refuses `__bases__` assignment on a class whose only base is
`object`, because that is a different solid base from anything in the `Widget` lineage, and says so with
`deallocator differs from 'object'`. So **naming a real widget base is a mechanical requirement of the merge**, not a
style rule.

What the second row costs is completion on ids, and that cost is real — *Ids* chooses an attribute over a dict partly
because "the paired handler module writes `self.left` by hand and gets completion and a rename for it". `button.pyi` is
what buys it back without an import line. Two things follow from the stub rather than being chosen: it **replaces** its
module for a checker, so in the merged shape it has to carry the hand-written signatures as well as the generated
surface (`mypy.stubgen` produces that half; the generator injects the base, the ids and the `property` and `alias`
names) — and, measured, an error planted in `button.py` is then **not** reported even when mypy is pointed straight at
it. The implementation needs checking by some other route, and the note says so here rather than leaving it to be
discovered the day lint tooling is wired up.

### Deriving from another component

The root block carries the base when there is one to carry — `FramedButton(Button):` — and **a bare `Manager:` is how a
document says it extends `Widget`**, that being the only way it says so: see *A bare head, and why nothing is reserved*
above. This is the one block head in a document read as a *declaration* rather than as an instantiation: a child block
`Panel:` constructs an existing `Panel`, while the root block names the class being defined and what it extends. QML
splits the two across the filename and the root element; putting both on one line suits a language whose blocks are
already `Name:`.

**The hand-written half repeats the markup's base, and has to spell it either way** — `class FramedButton(Button)`, and
`class Button(Widget)` for a document whose head is bare. Markup's bare head has no equivalent in Python: a class
statement with no bases means `object`, which *cannot be spliced at all*, so the `.py` half names `Widget` where the
`.nml` says nothing. Between two *component* bases it is a convention rather than a rule — measured, `Widget` and
`Button` splice to an identical MRO — and it is the right convention because it keeps the shapes interchangeable
(above), because an editor resolves `self` from the class in the file being edited and `Widget` would hide every
`Button` member from whoever is writing the handlers, and because it is true.

**The loader checks the two agree, because CPython will not.** Measured: a hand-written `class FramedButton(Dialog)`
splices without complaint and the resulting MRO contains no `Dialog` at all — the declared base is discarded silently,
which is the worst shape this failure can take. So the loader captures `__bases__` before assigning and refuses unless
`issubclass(generated, declared)`. That is permissive enough to allow a loose ancestor such as `Widget`, and strict
enough to catch a real disagreement, and it names both files when it refuses.

**Which class to rebase** comes from the generated module, which declares `__navml_component__ = "FramedButton"`. The
loader looks that name up in the hand-written half rather than deriving a class name from a file name, so there is no
`snake_case`/`CamelCase` convention to get wrong and a handler module may define helper classes freely. A `button.py`
that exists and does not define the name is an error naming both files, not a silent fall back to the markup-only shape.

This is also what makes the third blocker under *What converting `Manager` needs and does not have* acute rather than
incidental: `FramedButton(Button):` names a type exactly as a child block does, so the generated module has to import
`Button` from somewhere and markup has no import spelling. Inheritance and child construction are one question.

### Building the tree

The generated `__init__` constructs the children itself, **inline, with no `_build()` method**, and that is a correction
to the earlier sketch rather than a detail. A method would be a single name shared down an inheritance chain, so a
derived component's would override its base's — and `Button.__init__`'s `self._build()` would then resolve to
`FramedButton._build`. Measured consequence: the base's children are never built at all and the derived component's are
built twice. `super().__init__()` chaining gives the right order for free, with nothing to name and nothing to collide.
Private name mangling would also fix it, and is not needed once there is no method.

Everything *Ids* says survives unchanged — ids are assigned before any binding is installed, before any hand-written
line runs, and an un-id'd widget still gets a local that dies when the constructor returns.

### The import machinery

`navml/_merge.py`, a `sys.meta_path` finder and two loaders. The merged shape is the interesting one, and it does as
little as possible:

- `ComponentFinder.find_spec` resolves the spec through `importlib.machinery.PathFinder` exactly as the import system
  would have, and **wraps only its loader**. `RebaseLoader` forwards `create_module`, `get_code`, `get_source` and
  everything else to the real `SourceFileLoader`, runs the ordinary execution of `button.py`, and then assigns
  `__bases__`.
- Delegating rather than executing two sources into one namespace is what keeps this cheap. The module has exactly one
  source file, so `__file__`, `__spec__.origin`, `get_source` and `get_code` are each about one file and each true, and
  `inspect`, `runpy`, `pydoc`, `linecache`, `pdb` and coverage all keep working. A two-source loader gives every one of
  those up: `inspect.findsource` resolves a class through `sys.modules[cls.__module__].__file__`, one slot for two
  files, so half the module becomes unsourceable or — when both halves define the same class name — silently returns the
  wrong body.
- **Markup only** takes the other branch. `GeneratedLoader` copies the generated module's public names across, points
  `__file__` at `button_nml.py` and re-homes the class with `__module__`. Both halves of that are load-bearing:
  `inspect` needs the public module's `__file__` to name the file the class really lives in. Re-homing has one cost
  that only shows on Python 3.13: a class carries its body's line in `__firstlineno__` there, `inspect` reads it rather
  than scanning, and `type.__setattr__` **deletes it when `__module__` is assigned** (CPython gh-118465) on the
  assumption that a re-homed class has moved. It has not — only its published name changed — so `_rehome()` puts the
  number back, and without that `inspect.getsource` on a markup-only component raises `OSError` on 3.13 while working
  on 3.12.
- **Keyed on `button_nml.py`, never on `button.nml`.** Both halves of a component are then ordinary `.py` files, which
  reach a wheel automatically inside a declared package, so the import path never depends on a file a `package-data`
  mistake can drop. Keying on the markup would invert that and repeat the failure `CLAUDE.md` records for
  `navigator/styles/*.nss`.
- **`navml.register(__name__)` in a component package's `__init__.py`** is the bootstrap. Importing anything inside a
  package is guaranteed to run that file first, so there is no ordering hole, and the finder — which sits on
  `sys.meta_path` and is therefore consulted for every import in the process — bails on a set lookup that fails. It is
  the *widget library* that registers: a component is a directory, so the package a component module lives in is the
  component's own and never the one anybody registered, and `_registered()` walks up the dotted name to find the
  library above it. `json` costs one failed lookup, `os.path` two. A
  `.pth` file would not do: those are executed only by `site.addsitedir()`, and `packaging/linux/` mounts its tree on
  `PYTHONPATH` rather than as a site directory, so a `.pth` would work under pip and pipx and silently not in the `.deb`
  and `.rpm` — the worst available difference.

Three things this costs, none of them fatal and all of them worth naming:

- **pytest's assertion rewriter calls `PathFinder.find_spec` directly**, bypassing the rest of `sys.meta_path`. Any
  module it rewrites is loaded raw, so a merged component would come up as a plain `Widget` subclass. It fails loudly —
  `AttributeError` on the first id — but the rule that follows is flat: **a component module must never be a test
  module, a `conftest.py` or a pytest plugin.**
- **A by-path load gets the same thing**, which is what `tests/test_navml.py` pins rather than leaves implicit.
- **A zipapp or one-file build is foreclosed** while the finder stats real paths. Nothing needs one — the `.deb` is a
  real directory staged by `pip install --target` — but it is a ceiling rather than an oversight.

### The markup ships

`.nml` files are in the wheel and in both native packages even though nothing loads them, for the reason an open-source
project keeps its sources beside its build products: somebody reading `button_nml.py` should be able to read what it was
generated *from*, and somebody who wants a different widget should be able to edit the markup and rebuild rather than
reverse-engineer the emitted code.

That makes `python -m navml build` a user-facing command rather than only a maintainer's. A pipx or venv install is
writable, so editing `button.nml` in site-packages and rerunning it regenerates `button_nml.py` and `button.pyi` in
place; `--check` reports markup that no longer matches its generated half. The `.deb`/`.rpm` tree is root-owned, so
there the same workflow means copying the package out first, which is the ordinary situation for a system package.

It costs one `[tool.setuptools.package-data]` entry, `"*" = ["*.nml", "*.pyi"]` — setuptools' every-package key, which
it merges with the exact keys beside it rather than replacing them. Naming the packages instead was what the entry used
to do, and a component being a directory is what ended it: markup and stubs now live one package deeper than the
library that holds them and these keys do not inherit, so the honest spelling would be one line per component and a
silent hole — working from a checkout, absent from a wheel — the first time somebody forgot one.
`packaging/linux/build.sh` still asserts all three extensions are staged, with the severities kept apart: a missing
`*_nml.py` or `*.pyi` is a broken install, a missing `*.nml` is a stripped one. That is now belt and braces rather than
the only defence — and its smoke import had to grow teeth for the same reason, because `import navml.widgets` imports
no component at all and would pass with every component directory missing.

### What this asks of navkit

Nothing. The merge is `__bases__` assignment, which is Python's; `declarations()` walks the MRO and so spans both halves
already; `StyleProperty.__set_name__` fires per class body and `_PROPERTIES` is a module-global registry, so a style
property declared in the generated half registers once; and `_is_a` matches a type selector by walking the MRO for a
class *name*, so the two same-named classes a merged component puts there match `Button { }` exactly once — which is
also why both halves keep the component's name rather than the generated one taking a private spelling. A sheet then
reads the same whether or not a component has handlers.

