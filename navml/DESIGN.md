# navml design notes

The markup language, its parser, the code generator, and the widget library are all unwritten. This file records
decisions made ahead of them, so the work starts from a spec rather than rediscovering it. Anything not written down
here is still open.

## Where the inspiration is taken from

**QML for the architecture, Kivy for the syntax.** From QML come the shape of the language and its semantics: a
declarative tree of objects, `id`s naming them, properties that are expressions re-evaluated when what they read
changes, and a component that is a class. From Kivy comes the surface, because the file should read like Python:

- **blocks are made by indentation**, not by braces;
- **no semicolons**, and one property per line;
- a widget opens a block with a trailing colon — `Panel:` — and its properties and children are the lines indented under
  it;
- `id: left` is a directive rather than a property — see *Ids* below.

So a declaration reads:

```
Panel:
    id: left
    width: parent.width // 2
```

and never `Panel { id: left; width: parent.width // 2 }`.

## The two halves of a component

A component is written as markup, as Python, or as both, and **either half may be absent**. All three reach the same
public module name, so nothing importing a component can tell which it is looking at:

| shape       | files                                                   | what backs `navml.widgets.button`                    |
|-------------|---------------------------------------------------------|-------------------------------------------------------|
| Python only | `button.py`                                             | nothing of navml's — the stock `PathFinder`           |
| markup only | `button.nml` → `button_nml.py`, `button.pyi`            | the generated module, re-homed onto the public name   |
| both        | the above, plus `button.py`                             | `button.py`, with the generated class spliced beneath |

- **`button.nml`** — hand-written markup. It ships, and it is the one file in the set that nothing at run time reads;
  see *The markup ships* below.
- **`button_nml.py`** — generated, tracked, shipped. `class Button(Widget)`: the tree, the bindings, the `layout()`
  override.
- **`button.py`** — hand-written. `class Button(Widget)`: the handlers. **It never names the generated class**, which is
  the whole of *Why the hand-written half never names the base* below.
- **`button.pyi`** — generated, tracked, shipped. Emitted whenever `button_nml.py` is, because in the markup-only shape
  it is the only thing a type checker can see for that module name.

The original sketch spelled the generated file `button.nml.py`. A dot makes it unimportable by name — `import
navml.widgets.button.nml` splits on the dots — so no checker, no IDE and no `pkgutil` ever sees the class the
hand-written half inherits from, which forecloses the id-annotation question in *Still open*. setuptools' `build_py`
also globs `*.py` and ships it as a module literally named `button.nml`.

**A component is not a kind of object.** There is no navml base class, no decorator, no metaclass and no registration on
the class. The Python-only row touches none of this file's machinery at all: an ordinary `navkit.Widget` subclass
already *is* a component, and giving it a `.nml` later changes not one line of it.

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
  `inspect` needs the public module's `__file__` to name the file the class really lives in.
- **Keyed on `button_nml.py`, never on `button.nml`.** Both halves of a component are then ordinary `.py` files, which
  reach a wheel automatically inside a declared package, so the import path never depends on a file a `package-data`
  mistake can drop. Keying on the markup would invert that and repeat the failure `CLAUDE.md` records for
  `navigator/styles/*.nss`.
- **`navml.register(__name__)` in a component package's `__init__.py`** is the bootstrap. Importing anything inside a
  package is guaranteed to run that file first, so there is no ordering hole, and the finder — which sits on
  `sys.meta_path` and is therefore consulted for every import in the process — can bail on a set lookup that fails. A
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

It costs two `[tool.setuptools.package-data]` entries, and a new component directory needs its own or its markup and its
stubs work from a checkout and vanish on install. `packaging/linux/build.sh` therefore asserts all three extensions are
staged, with the severities kept apart: a missing `*_nml.py` or `*.pyi` is a broken install, a missing `*.nml` is
a stripped one.

### What this asks of navkit

Nothing. The merge is `__bases__` assignment, which is Python's; `declarations()` walks the MRO and so spans both halves
already; `StyleProperty.__set_name__` fires per class body and `_PROPERTIES` is a module-global registry, so a style
property declared in the generated half registers once; and `_is_a` matches a type selector by walking the MRO for a
class *name*, so the two same-named classes a merged component puts there match `Button { }` exactly once — which is
also why both halves keep the component's name rather than the generated one taking a private spelling. A sheet then
reads the same whether or not a component has handlers.

## Importing another component

A document names types it does not otherwise say where to find: `Button:` as a child block, `FramedButton(Button):` as
a root. It says where in **Python's own words**, at the top of the file:

```
from navml.widgets.label import Label

Button:
    property text: ""

    Label:
        id: caption
```

Components are the case this exists for, but the line is an ordinary Python import and anything importable may be
imported — see *Why any import* below, which is a stronger argument than it first looks.

### Where the lines go, and what they compile to

**At indent 0, before the root block**, blank lines allowed between them. A line after the root block is rejected with
its `.nml` line: blocks are made by indentation, and an import inside one would have no meaning to give it.

**They compile to themselves.** `ast.parse` then `ast.unparse` round-trips every form exactly — measured across `as`,
dotted paths, `from . import x`, `from ..widgets.label import Label` and multi-name lines — and the set of names a line
binds falls out of the tree as `alias.asname or alias.name.split(".")[0]`. So navml invents no grammar here at all. It
reuses Python's, which is the same move *Compiling a property expression* makes with `ast.parse(mode="eval")`, and it
means a sibling component can be named relatively without anything being built for it.

Two forms are refused, each with the `.nml` line:

- **`from x import *`.** It makes the set of names a document binds unknowable, so the generator could no longer check
  that a block head resolves — see below — and a name arriving that way is one no reader of the document can see.
- **`from __future__ import …`.** A `__future__` import has to be the first statement in a module and the generator
  emits its own; a second one is a `SyntaxError` in generated code, which is a poor way to learn this.

**A block head is a single identifier.** `import navml.widgets` binds `navml`, not `widgets`, so it is no use for a
head and a document wanting `Label:` writes `from … import Label`. Plain `import x` stays legal and is still worth
having inside an expression, where an attribute chain is ordinary Python.

### A bare head, and why nothing is reserved

**`Label:` is how a document says it extends `Widget`, and the only way it says so.** `Label(Widget):` is not the
clearer spelling of the same thing — the parenthesised form names a type, and a type a document names is a type it
imports. So `Label(Widget):` means *whatever the document imported as `Widget`*, and a document that imported nothing of
that name is told so when it is compiled.

That is worth more than the two characters it saves. The generated module needs names of its own, and a document's
imports land in the same namespace, so the two could collide — and the answer is now the whole answer:

```python
from __future__ import annotations                 # always first
from typing import Any as _Any                     # everything the generator
from navkit.reactive import bind as _bind          # needs for itself is
from navkit.reactive import is_bound as _is_bound  # underscored, so that a
from navkit.reactive import reactive as _reactive  # document's imports cannot
from navkit.widget import Widget as _Widget        # reach any of it

from navml.widgets.label import Label              # button.nml:1, verbatim
```

**The generator reserves no word.** A document may import any name at all, `Widget` included, and gets exactly what it
asked for; a bare head asks for navkit's and cannot be confused with it. Had `Widget` stayed implicit it would have had
to be reserved, and then reserved alongside whatever the generator needed next — a list that grows by taking names away
from documents that had them. Underscoring costs a little readability in a file nobody edits and settles the question
for good.

The *language* reserves one, and the distinction is the point of this section: `event` names every handler's argument —
*The handler's one argument is `event`* below — so an import of that name would be shadowed inside a handler body and
nowhere else. The parser rejects the import rather than letting the shadow happen quietly, which is the same list the
ids are checked against. It is one name, taken deliberately and once; `_bind` and its siblings are how the generator
avoids taking any.

Each emitted line carries its origin as a trailing `# button.nml:1` comment, the import block included — the same
convention *Source mapping* settles for everything else the generator writes.

### What the generator checks

**Every type a document names must resolve** against the names it binds — the root's base when it has one, and every
child block head. One that does not fails when the document is compiled, naming the `.nml` line. That is worth having rather than leaving to
Python: otherwise the failure is a `NameError` raised out of generated code at the first *read* of a lazy,
failure-caching binding, arbitrarily far from the line that caused it.

### Why any import, and not components only

Restricting a document to components would read as the tidier rule. It is the wrong one, because two navkit mechanisms
are **silently off** for a name the generated module cannot see, and an import is exactly what turns them on:

- **A declared type is only checked if it resolves.** `_resolve_annotation` in `navkit/reactive.py` evaluates the
  annotation in the globals of the module whose class carries it, and returns `UNKNOWN` — meaning *unchecked* — for
  anything it cannot see, then caches that answer for the life of the process. *Declared types* in `navkit/DESIGN.md`
  records this as the deliberate opt-out, and it is: but it means `property path: Path(".")` is checked against `Path`
  when the document imports `pathlib` and unchecked when it does not, with no signal either way.
- **A `style:` block can only be validated against a property whose widget has been imported.** `declared_property()`
  reads a module-global registry that `StyleProperty.__set_name__` fills when a class body runs. That is the import-order
  cost *Widget properties* already argues is worth paying, arriving at markup.

It also keeps the conversion target reachable: `Panel.path` is `reactive(Path("."))` today, and *Declaring a property*
uses `property path: Path(".")` as one of its own examples.

### The cold build

**The generator needs live class objects.** `compile_property(source, cls, ids)` walks `cls.__mro__`, so compiling
`button.nml` really does import `Label` — generation is not a static pass over text, and the import lines are what make
that legible rather than magic. Two things follow:

- **`navml build` orders documents by their import graph**, which is readable without executing anything: parse the
  import block, keep the edges that name another document in the build. A cycle between two documents is an error
  rather than something to resolve; Python's own answer to a circular import is not one worth inheriting here.
- **A component package's `__init__.py` must not re-export eagerly.** This was measured on this repository rather than
  reasoned about: importing `navml.widgets.label` used to load all four components, because the package imported each
  by name, so a cold build could import nothing until everything had already been generated. `navml/widgets/__init__.py`
  now re-exports through :pep:`562`'s module `__getattr__`, which keeps `from navml.widgets import Button` working,
  breaks the coupling, and takes the rest of the library out of the import path of anything that wanted one widget. A
  `TYPE_CHECKING` block beside it carries the real types, because a module `__getattr__` answers `Any` to a checker and
  would otherwise make every component untyped at every call site.

### What this asks of navkit

Nothing. The import block is copied into a Python module, and Python resolves it.

## Ids

An id is a **name, never a value**, and both ancestors agree on that much. QML's docs are blunt about it — "it is not
possible to access `myTextInput.id`" — and Kivy deprecated
`Widget.id` through the 1.x line and removed it in 2.0.0, leaving only the `ids` dict. navml follows: a widget has no
`id` attribute, and there is no reverse lookup either (QML keeps one for C++, `qmlContext(o)->nameForObject(o)`).
Nothing needs one. An id exists so that one expression can name another widget in the same document, and that job is
finished at generation time. If a test or a debugger ever wants to name a widget at run time, that is a separate
reactive attribute on `Widget` — QML's `objectName`, which is a different thing with different rules — not this.

**In particular, an id is not a stylesheet selector.** `README.md` promises navkit a CSS-like stylesheet, and the
obvious reading of that is `#left` matching `id: left`. It does not: the lookup engine is navkit, which cannot depend on
navml and has nothing to match anyway, and a navml id is unique per document where CSS `#` presumes it is unique across
everything being styled. `#` matches `Widget.name`, an ordinary run-time property written in markup as
`name: "left-panel"` like any other. This is the same split Qt draws between a QML `id` and
`QObject::objectName`; `navkit/DESIGN.md` records it in full.

Where the two ancestors *disagree* is what an id compiles to, and there navml takes QML's side. QML assigns each id a
slot index in the instance's `QQmlContextData` at compile time, so a reference costs an array read. Kivy stores a
`WeakProxy` in a `DictProperty` and re-resolves the name out of that dict on every re-evaluation, because its compiled
expression is `eval`'d with the id map as its globals.

### What an id becomes

A plain instance attribute of the component, assigned in the generated `__init__`:

```
Panel:
    id: left
```

```python
self.left = Panel(parent=self)
```

Not a dict. Three reasons, in order of weight: the expression rewriter already emits
`self.left.width`, so an attribute is the form the compiled output wants anyway; the paired handler module writes
`self.left` by hand and gets completion and a rename for it; and a mistyped id fails as an `AttributeError` naming the
component, rather than a `KeyError` on a dict that could be anybody's.

The attribute holds the widget itself, not a weak proxy. Kivy needs `WeakProxy` because its
`ids` dict outlives the widget it names; a navml component owns its tree the way a QML context owns its objects and is
collected with it, so there is no cycle to break by hand. That also avoids Kivy's sharpest corner, where the key
survives the widget and `root.ids.gone` is a live entry holding a dead proxy that raises `ReferenceError` on any access.

Two consequences worth stating outright:

- **The id attribute is never reassigned after the generated `__init__` has run**, and that is what makes an ordinary
  safe. A binding compiled from `left.width` reads `self.left` and then subscribes to `Panel.width`: it tracks the
  panel's width, but *not* a replacement of
  `self.left`. QML does track its id slot — `captureProperty(context->idValueBindings(idx))` — because incremental
  creation can refill one. navml has no such moment.
- **Removing a widget from `children` leaves `self.left` pointing at it.** Deliberate: an id names a widget the document
  declares, not a position in the tree.

### Naming rules

Checked by the parser, each failing with the `.nml` line:

| Rule                                                   | Rejects                  | Why                                                        |
|--------------------------------------------------------|--------------------------|------------------------------------------------------------|
| a Python identifier, and not a keyword                 | `id: 2left`, `id: class` | it is emitted into generated source as an attribute name   |
| not one of the reserved words `self`, `root`, `parent`, `event` | `id: parent`       | each already means something in the resolution table below |
| not an attribute of the component's own class          | `id: width`              | it would be stored as `self.width` — see *Name resolution* |
| unique within the document                             | two `id: left`           | the second assignment would silently win                   |
| not a property or alias the document declares          | `id: console_visible`    | both become `self.<name>`, and the descriptor wins the tie |

The reserved-word row is the one both ancestors got wrong, in the same direction. QML checks id names against the
JavaScript globals but not against `parent`, so `id: parent` compiles and shadows `Item.parent` for a whole component
scope. Kivy rejects exactly `self` and `root` and silently shadows the rest — and shadows them *in opposite directions*
depending on context:
inside a property expression the globals overwrite the ids, inside an `on_*` handler the ids overwrite the globals. One
explicit list, checked once, in the parser.

Not adopted: QML's rule that an id must start with a lowercase letter. It exists to keep ids distinguishable from type
names, and navml distinguishes them by position — a type opens a block, an `id:` is a directive line indented under it —
so the rule buys nothing.

### Scope, order, and anonymity

**An id is scoped to its document.** One `.nml` file declares one component, and its ids are visible from every
expression in that file and from nowhere else. This is Kivy's per-rule boundary rather than QML's component scopes,
which chain upward so that a delegate can read names from wherever it happened to be instantiated. The reason is
mechanical rather than aesthetic: the compiled form is a closure over *one* component instance, and there is no
enclosing instance in scope to chain to.

**Order does not matter.** An expression may name an id declared further down the document.
The generated `__init__` constructs every widget before it installs any binding, and a binding body is not run until
the value, so a forward reference costs nothing.

**A widget without an id is anonymous, by construction.** It gets a local in the generated `__init__`, which dies when
that returns — the parent's `children` list is then the only reference to it:

```python
    def __init__(self, **kwargs: Any) -> None:
      super().__init__(**kwargs)
      _w1 = MenuBar(parent=self)
      _w1.width = _bind(lambda _o: _o.parent.width)
  
      self.left = Panel(parent=self)  # id: left
      self.left.width = _bind(lambda _o: _o.parent.width // 2)
```

No rule is needed to keep an un-id'd widget out of expressions: an id reference always compiles to `self.<id>` and never
to a bare local, so the widget is unreachable from any expression whether or not the local is still alive.

**Ids are live before any hand-written code runs.** The generated `__init__` assigns every id attribute before it
installs the first binding, and runs to completion during the component's construction — so there is no window in which
`self.left` is
missing. Kivy has one, which is why its ids are unusable from `__init__` and why 1.11 had to add `on_kv_post` after
years of
`Clock.schedule_once` folklore. The contract this puts on the still-undecided merge with the hand-written half is a
single line: the generated `__init__` builds the tree, and a hand-written `__init__` must call `super().__init__()`
before it touches an id. See *Building the tree* above for why that construction is not a `_build()` method.

## Declaring a property

A document may add a reactive attribute to the component it declares:

```
Manager:
    property console_visible: False
```

`property` is a directive line like `id:`, told from an ordinary assignment by its two-token head. The `:` goes on
meaning what it means everywhere else in the file — name on the left, value on the right — which is why the
Python-flavoured `property console_visible: bool = False` loses: it would give one line's colon two jobs. QML's
`property bool consoleVisible: false` keeps the colon honest and is where the word comes from; navml drops the type
and the slot stays free if it is ever wanted.

navkit *does* check one now — a reactive attribute is checked against the annotation written beside it, see *Declared
types* in `navkit/DESIGN.md` — so what a typeless `property` generates is a declaration with no annotation, which that
layer leaves unchecked. That is the right default rather than a gap: an attribute the document declares is written and
read by that document and its paired handler module, where a wrong type is a local mistake, and the generator has no
type to emit until the language has a spelling for one. What changed is the cost of adding the spelling later: it is
now one annotation on the emitted line and the check follows, rather than a run-time mechanism that would have to be
built first.

The word is deliberately the one this file already uses for every `name: value` line. That overload is QML's too —
everything is a property, `property` declares a new one — and the alternative, `reactive`, would leak the name of the
machinery into a language that otherwise never mentions it. Python's `@property` is the *opposite* thing, a computed
rather than a source, which is the one real cost; navml is not Python and its `:` lines already are not, so it was
judged smaller than either alternative.

### Where the line lands

The class body always gets the declaration, because that is where a descriptor has to live:

```python
class Manager(_Widget):
    console_visible = _reactive(False)
```

Without it, `self.console_visible = _bind(...)` would store a `Binding` on an ordinary attribute and do nothing, there
being no descriptor to notice it — the failure whose only symptom is the `<unassigned binding ...>` repr.

What varies is whether a second line joins it in the generated `__init__`, and the test is **whether the expression reads anything
reactive** — precisely whether the rewriter of the next section rewrote any free name:

| The right-hand side  | rewritten? | compiles to                                                                  |
|----------------------|------------|------------------------------------------------------------------------------|
| `False`, `0`, `None` | no         | `console_visible = _reactive(False)`                                         |
| `[]`, `Path(".")`    | no         | `entries = _reactive(factory=lambda: [])`                                    |
| `self.width // 3`    | yes        | `w = _reactive()`, and `self.w = _bind(lambda _o: _o.width // 3)` in `__init__`|

So a declared property may be derived, and `property first_column_width: self.width // 3` is one line rather than two.
The test costs the generator nothing: the expression compiler already knows whether it touched a free name, so the
answer falls out of a pass it runs anyway. It is the same rule as *A literal is not a binding* below, asked at the
declaration site.

The second row over-applies `factory=` on purpose, and the one case in the repository shows it: `Panel.path` is a plain
`reactive(Path("."))` today, an immutable default instances can safely share, and markup generates a factory for it
instead. The two are indistinguishable through the equality guard, and erring this way costs one object per instance
where erring the other way costs a shared mutable.

**Not "a constant is a default, everything else is a binding".** That is the obvious rule, and it is wrong in a way
worth recording so it is not tried again. `property entries: []` is not a constant, and compiling it to a binding would
leave `entries` a live bound cell — over which navkit refuses a plain assignment, so `Panel`'s scan effect could never
write `self.entries = ...` again. A list display reads nothing, so it is an initial value; `factory=` is what stops the
instances sharing it, and it is inferred rather than spelled for exactly this pair of cases. `equal=` gets no spelling
at all: nothing in the repository needs one, and a property that does is declared in the paired hand-written module,
which is the escape hatch that makes an incomplete `property` acceptable.

**A bound property is read-only until something unbinds it.** The third row's consequence, stated here rather than
discovered later: the hand-written half cannot assign `first_column_width` without calling `unbind()` first. That is
the trade every bound attribute in the repository already makes, and the honest reading of having written a derived
expression. It is still the right form rather than a `computed`, which fixes one function on the class; a binding
belongs to one instance and can be replaced or taken back.

**A default *and* a binding still take two lines** — `property width_hint: 0`, then `width_hint: parent.width // 2`
lower down. Only the derived case stopped needing them. The two-line form remains for the case where the initial value
is genuinely observed before the binding is installed.

**A value is required.** `property console_visible` alone is rejected rather than quietly meaning `reactive(None)`.

### Where it may appear

**In the root block only.** `Reactive` is a descriptor installed on a class, and the root block is the only block in a
document that becomes one — every other block is an *instance* of a class that already exists, so a `property` under
it would have to synthesise a per-document subclass. One under a child is rejected with its `.nml` line, pointing at
giving that child a document of its own or declaring the attribute in the `.py` half. Nothing is lost today: every
declaration `navigator/__main__.py` carries — `Manager.console_visible`, `Console.revision` and `Panel`'s seven — is
on a class that becomes some document's root.

The ancestors sit on either side of this. QML allows a `property` on any object, because there an object carrying one
becomes its own anonymous type. Kivy allows it nowhere: a `.kv` file declares nothing, the properties live in the
Python class and the markup only assigns them — which is the hole this section fills.

### Naming rules

Everything the id rules say, and one more, each checked by the parser with the `.nml` line:

- **A property may not collide with an id, nor with an alias.** Both become `self.<name>`, and `Reactive` defines
  `__get__` *and*
  `__set__`, so it is a data descriptor and beats the instance `__dict__`. The generated `__init__`'s
  `self.left = Panel(parent=self)` would therefore write the panel *into a reactive cell* rather than shadow the
  declaration — wrong, and silently so. An alias collides more simply, both being lines of the same class body: the
  second name would overwrite the first outright.
- **A property may not shadow an attribute of the component's base class**, reactive or not. `property width: 0` on a
  `Manager` re-declares `Widget.width` with a fresh cell, and `property title_text: ...` on a `Panel` collides with a
  `Computed` that *A `computed` target is a generation-time error* already rejects from the other side. The banned set
  is the one the id rules name: `declarations(base)` plus the ordinary attributes.

### What the generator has to do about it

Declared properties join the `own` set the expression rewriter checks. The table under *Name resolution* reads "any
reactive attribute the widget's class declares", and for the component's own expressions that class does not exist yet
— so the generator collects declarations in a first pass and compiles expressions in a second. Construction is already
a separate earlier pass, so this is one more table filled before an existing one rather than new structure. A
declaration's own right-hand side is compiled in that second pass like everything else, which is what makes
`property first_column_width: self.width // 3` safe: `self` resolves to the component, and the cell is lazy, so nothing
is read while the class is still being built.

One knock-on, flagged rather than solved: a binding installed in the generated `__init__` lands *after* the children are
constructed,
and `Panel.__init__` starts a directory scan from an effect at construction — so a `Panel` whose `path` came from a
component property would scan once against the default before the binding arrives. That is the *Component parameters*
question under *What converting `Manager` needs and does not have*, which this decision makes reachable without
answering.

This asks navkit for nothing: `reactive()` is callable in a class body, and that is the whole requirement.

## Declaring a style property

The other half of what a component declares about itself is what a *stylesheet* may say about it:

```
Panel:
    style_property icons: auto | none

    style:
        bg: $panel-bg
```

A stylable property is a declaration a sheet may make that `Style` has no field for — `border` being the first of them,
for the reason `navkit/DESIGN.md` argues at length — and navkit now takes it as a class attribute,
`icons = StyleProperty("auto", values=("auto", "none"))`. This directive is that line, and compiles to exactly it --
spelled `_StyleProperty`, like everything else the generator imports for itself.

`style_property` is a two-token head like `property` and `id`, so the directive rule stands unchanged; the underscored
spelling is what keeps it decidable against the `style:` block without lookahead, and it is the name it compiles to.

### The right-hand side is a `.nss` value, not a Python expression

This is the same boundary *The `style` block* draws below, and it is drawn for the same reason: what is being written is
what a sheet may say, in the grammar a sheet says it in. So a `$variable` is **not** meaningful here, which it is inside
that block — there is no sheet loaded when a class body runs, and a default that could not be resolved until one was
would be a different mechanism wearing the same syntax.

**The default's form is the type, and `|` narrows it further.** Nothing spells a type:

```
style_property icons: auto | none         # a keyword, one of two
style_property align: left                # a keyword, any
style_property margin: 0                  # a number
style_property scrollbar: true            # a flag
style_property indent: 2 | 4 | 8          # a number, one of three
```

The first alternative is the default and the rest complete the vocabulary. This is the inference `property` already
makes from *its* right-hand side rather than a second idea, it is what navkit's `StyleProperty` does with the default it
is handed, and it is what makes the directive useful beyond enumerations — a sheet saying `margin: wide` is refused
because the default is a number.

Deliberately not offered: a **range** (`0 .. 80`). A widget clamps a number it is given, the one property that might
want a range does not exist, and a spelling invented for a hypothetical case is one the `.py` half can carry instead.
**A value is required**, as for `property`, so there is no markup way to say "no default"; a property wanting one is
declared in the paired module — the escape hatch `equal=` already uses.

### Where it may appear, and what it may be called

**In the root block only**, and for exactly the reason `property` is: it emits a descriptor onto the class the root
block becomes, and every other block is an instance of a class that already exists.

The naming rules are `property`'s, with one addition. It may not collide with an `id` or an `alias` — `StyleProperty`
defines `__get__` *and* `__set__`, so it is a data descriptor and would beat the instance `__dict__` the same way
`Reactive` does. It may not shadow a base-class attribute, which now includes `Widget.border`; a component wanting a
different *default* frame is the one case where re-declaring is right rather than wrong, and navkit permits it
explicitly — two declarations of a name must agree on the vocabulary, not on the default.

One name is worth checking for in the paired module rather than in the markup: a component declaring `style_property
icons` and importing a module called `icons` has two of them a few lines apart. Python resolves it correctly — a class
body's names are not in scope inside its methods, so the global wins — which is what makes it a trap rather than an
error. `navigator/__main__.py` hit precisely this and renamed the import.

### What it asks of navkit

Nothing further. `StyleProperty` is there, it registers the name from `__set_name__`, and the parser checks both halves
of a declaration against what was registered. The one thing the generator inherits is **import order**: a sheet may only
be parsed once the widgets it styles have been declared, which is why `navigator/__main__.py` now parses its default
sheet on first use rather than at import. A generated module is imported before anything loads a sheet naming its
properties, so this costs markup nothing — but a sheet loaded by a plugin for a component nobody has imported yet will
fail with `unknown property`, and that is the honest failure rather than a silently dropped declaration.

## Aliases

Ids stop at the document, so markup that uses a `Panel` component cannot name anything declared inside `panel.nml`. A
component says for itself what crosses that boundary:

```
Panel:
    alias title: header.text

    Label:
        id: header
```

`alias` is a directive line with a two-token head, like `property`. QML spells it
`property alias title: header.text` and navml does not, because the second token slot is empty *on purpose*: the type
was dropped from `property bool consoleVisible: false` to keep one line's colon doing one job, and refilling that slot
with a word that is not a type would undo the reason it is free. `alias` standing alone reads as the third member of
the `id:` / `property` family, which is what it is.

Kivy has no answer at all, which is exactly why Kivy code reaches through `outer.ids.child.ids.grandchild` and the
boundary ends up meaning nothing. What separates the two is not how far a name can reach — chained aliases reach as far
as anything — but that every hop here was declared by the component it crosses.

### What an alias becomes

A line of the generated class body, as `property` is, but carrying a descriptor of navml's own:

```python
class Panel(_Widget):
    title: str = _Alias("header", "text")
```

`__get__` and `__set__` forward by `getattr` and `setattr` to `<id>.<attribute>`, and that is the whole mechanism.
Everything correct about it falls out of the *target's* descriptor doing the work rather than this one:

- **Reads are tracked.** navkit captures a dependency at the moment of the read, against whatever binding is on its
  stack, keyed by the cell — it never asks whether the read went through an attribute of the reading object, and it
  subscribes outside the memoisation, so even a cached value subscribes. A forwarded read is an ordinary read of
  `Header.text` that happens to sit a few plain Python calls deeper, so an expression mentioning `panel.title`
  invalidates when `header.text` changes.
- **Writes keep their semantics.** The value is type-checked against the *target's* annotation, refused if the target
  holds a live binding, and propagates to dependents normally.
- **A write from inside a `computed` is still refused**, because navkit asks that question of its stack rather than of
  ownership. The number of forwarding hops is irrelevant to it.

`_Alias` **subclasses navkit's declaration base** and overrides `cell()` to return the target's cell. That is not
decoration — forwarding alone would leave the alias a descriptor navkit knows nothing about — and it buys four
things:

- `unbind()`, `is_bound()` and `peek()` work through the alias. Each names an attribute by its class declaration —
  which is this descriptor — and navkit refuses anything that is not one of its own.
- `declarations(cls)` returns aliases, so the `own` set the expression rewriter checks is one function rather than two
  that have to stay in step.
- An alias that *shadows* an inherited reactive attribute is reported correctly. `declarations()` walks the MRO keeping
  what it sees first, but sees only its own declarations — so a plain descriptor shadowing a base class's `reactive`
  would be walked straight past and the shadowed one returned in its place. That answer is not incomplete, it is
  **wrong**, and a generator trusting it would emit code against a cell nothing ever reads.
- An annotated alias carries a declared type, which is what the still-open `.pyi` question will want. Annotate every
  one the generator emits: the type is resolved by walking the declaring class's MRO for the name, so an unannotated
  alias silently inherits the annotation of whatever it shadows — and since the alias verifies nothing itself, that
  type is advisory and can disagree with the target's without anything noticing.

Both routes end at the same cell, so forwarding by attribute access and `cell()` pointing at the target cannot
disagree about anything.

### A binding through an alias is re-owned

`bind()` calls its expression with the object that owns the attribute, and after forwarding that object is the
*target*. So this:

```
Panel:
    id: p
    title: self.width * 2
```

compiles by the ordinary rules to `_o.width * 2`, in which `self` meant the `Panel` — and the expression is handed the
`Label`. A `Label` has a `width` too, so nothing raises: it computes the wrong number and goes on computing it. That is
the worst shape a binding failure can take, and it is why this is a section rather than an implementation detail.

`_Alias.__set__` therefore re-wraps a `Binding` before forwarding it, so the expression keeps being called with the
object the markup was written against:

```python
if isinstance(value, Binding):
    expression = value.expression
    value = bind(lambda _t, _o=obj: expression(_o), equal=value.equal)
```

In the descriptor rather than in the generator, for two reasons. It then holds for hand-written Python too, where
`panel.title = bind(lambda p: p.width)` means the panel to whoever typed it. And it composes: the wrapper ignores its
own argument, so an alias into a component that aliases further in re-wraps an expression that is already owned, and
the outermost object wins rather than the innermost. The expression has to be lifted into a local first: closing
over `value` while rebinding it on the same line gives a wrapper that finds itself at call time and recurses.

This was measured rather than argued — argument identity, recompute on a property of the aliasing widget, the value
landing on the target with no stray cell left on the component, `unbind()` through the `cell()` override, and `equal=`
surviving the re-wrap.

**It makes `bind()` mean something different at an alias**, and deliberately: one cell hands its expression a different
object depending on which name the binding was installed through. An alias exists to make the target's location
unobservable, and the argument is part of that location. It is stated beside the one-argument convention as well as
here, because a hand-written caller meets it without having read this section.

The strong reference the re-wrap adds — the target's cell holds the expression, which holds the aliasing widget — is
the same cycle `Widget.parent` and `Widget.children` already form for every attached widget pair, between two objects
that live and die together, and the collector breaks it exactly as it breaks those. What the weakrefs inside navkit's
cells protect is the other direction, a long-lived widget not retaining a dead one through its subscriber set, and
nothing here touches it.

### Depth, and what is deliberately not offered

**Exactly one property deep.** `alias title: header.text`, never `header.child.text`. Chaining is how reach goes
further, and the rule is what makes the difference from `outer.ids.child.ids.grandchild` real: each hop is an export
that the component in the middle declared, rather than a reach-through it never agreed to.

**An alias to a widget is not offered**, and the deferral this paragraph used to end on is now discharged. QML has
one — `property alias headerItem: header` — and it hands the widget out whole, which recreates the reach-through with
one extra step and no further declaration. It would also be a declaration with no cell of its own, which `unbind()`
and `is_bound()` could not answer for. The case that wanted it was naming an inner button in order to connect a
handler to it, and **that case has evaporated**: an emitted event walks up, so an outer document handles a click from
a button it cannot name. See *This settles the widget-alias question, and settles it as no* below.

### Where it may appear, and what it may be called

**In the root block only**, for the reason `property` is restricted there: it becomes a descriptor on a class, and the
root block is the only block in a document that becomes one.

An alias declares a name on the component, so it joins the `self.<name>` namespace the ids and the declared properties
share, and takes those rules entire — not colliding with an id, not colliding with a declared property, not shadowing
an attribute of the component's base class.

### Checked when the document is compiled

Each failing with the `.nml` line:

- The target's leading name is an **id declared in this document**, and not `self`, `root`, `parent` or `event`,
  which name things that have no stable meaning from the other side of the boundary.
- The attribute **resolves to a reactive declaration** on that id's class. A plain attribute is rejected rather than
  allowed through: a `bind()` forwarded onto one is silently stored, there being no descriptor to notice it, and the
  author reading the outer document cannot see the target's declaration to work out why nothing happened.
- A target that is a **`computed` makes the alias read-only**, classified here rather than left to fail when the widget
  is first painted. navkit's own refusal is intelligible but names the target, and its advice — declare it reactive —
  is addressed to somebody who can edit the target's class, which the outer author usually cannot.
- A **self-referential alias is rejected**. It yields a `RecursionError` rather than navkit's `CycleError`: the cycle
  detector sees cells, and an alias has none of its own to be seen.

### Three things an alias cannot carry

Each reads as an oversight until it is written down.

- **An initial value.** There is no slot for one and there could not be: the cell it would fill belongs to a widget
  that does not exist until the generated `__init__` has run. A component wanting one assigns it there, like anything
  else.
- **An `equal=`.** It has no cell to put one on. The `equal=` question left open below would otherwise be asked at a
  third site, and this is why it is not: on an alias, never — the comparator belongs to the component that owns the
  target, which is the only side that knows what the value means.
- **A useful error location.** Every message navkit raises names `Header.text`, an attribute that does not appear in
  the document its reader is looking at. `_Alias` should catch and re-raise naming both ends, and carry a `__repr__`
  reading `<alias Panel.title -> header.text>`, so that the three functions which reject a non-declaration say
  something legible when they do.

## Declaring an event

A component says what it emits, and the widget library is where every event that is not terminal input comes from.
`navkit/DESIGN.md`'s *What belongs in `navkit/events.py`* draws the other side of that line: navkit carries the events
it raises itself and nothing a widget *means*.

The worked example is the one the library will be full of — a `Button` clicked by a mouse press **or** by Space:

```python
@dataclass(frozen=True, slots=True)
class ClickEvent(Event):
    """The button was pressed, by whichever route."""


class Button(Widget):
    emits = (ClickEvent,)

    async def press(self) -> bool:
        return await self.emit(ClickEvent())

    async def on_key(self, event): ...    # Space, Enter  -> press()
    async def on_mouse_click(self, event): ...  # a left press  -> press()
```

**Two input routes, one thing they mean.** That is the whole reason a component declares an event rather than letting
documents bind to `on_key` and `on_mouse_click` themselves: a listener that had to know which route fired would break
the moment a third arrived.

### Where the class lives, and why it follows who emits it

**Beside the component, in its hand-written half** — `ClickEvent` in `button.py`, next to `Button`. Nothing is
registered anywhere: navkit derives `on_click` from the class name at class creation, so a document that uses a Button
writes `on_click:` without importing the class at all.

Markup can declare one too, and **which half owns it is decided by which half emits it**. That is not a preference; it
falls out of a rule already in this file. A markup `event` line puts the class in `button_nml.py`, and *Why the
hand-written half never names the base* forbids that half from naming the generated module — so a `.py` that emitted
it could not import it. Hence:

| the event is emitted from | declared in | reached as |
|---------------------------|-------------|------------|
| the hand-written half     | `button.py`, beside the class | an ordinary global of that module |
| a one-line markup handler | `button.nml`, with `event`    | a global of the generated module |

**A component may not do both**, and the generator rejects it with the `ast.parse` of the sibling `.py` *without
importing it* that *Name resolution* already specifies for reactive declarations the Python half alone declares.

### `event ClickEvent`

A directive line with a two-token head, like `property`, `alias` and `style_property`:

```
Button:
    event ClickEvent
    on_key: await self.emit(ClickEvent())
```

It emits both halves of the declaration into the generated class — the `Event` subclass, and the `emits` entry naming
it — so a markup-only component is a first-class shape for events too, which *The two halves of a component* insists
on everywhere else.

**The document names the class, not the event.** `event click` would be shorter and would read like the handler it
leads to, and it is refused for the reason *A bare head, and why nothing is reserved* gives: the generator would then
be putting a non-underscored `ClickEvent` into a namespace the document shares with its own imports, which is a name
taken from the author. Naming it is what keeps the generator reserving nothing. The handler name still derives from it
— navkit's rule, unchanged — so `event SelectionChanged` is handled by `on_selection_changed`.

**In the root block only**, for the reason `property` is: it emits onto the class the root block becomes, and every
other block is an instance of a class that already exists.

**A markup-declared event carries no fields**, there being no syntax for one, and none is invented here. An event that
carries data is declared in the `.py` — the same escape hatch `equal=` uses, and the same boundary: markup says what a
component emits, Python says what it emits *about*.

### What the generator checks, and why it needs two answers

An `on_*` line is legal in two different places, because emitting walks up:

- **On the block that emits it** — checked against that widget's `emitted()` set, failing with the `.nml` line and a
  list of what the widget does emit. This is the case that catches a typo where it hurts, on the component the author
  is looking at.
- **On an ancestor** — checked against the handler names of every `Event` subclass the document's imports have made
  live, walked with `Event.__subclasses__()`. No registry: the classes are already there, and navkit's own handler
  names are in the set for free, being `Event` subclasses like everything else.

The second is the looser check and has to be, because a `Dialog` may legitimately handle a click from a button three
levels down without knowing which component emitted it.

### This settles the widget-alias question, and settles it as no

*Depth, and what is deliberately not offered* refuses an alias that names a widget, and defers the refusal to this
section: "the case that wants it is naming an inner button in order to connect a handler to it, and signals are open
on both sides of the layer boundary". They are closed now, and the case has evaporated — **bubbling reaches what a
widget alias was wanted for**. An outer document writes `on_click:` on the `Dialog:` block and catches clicks from any
button inside it, without the dialog handing out a widget.

Where a component must distinguish *which* inner widget, it translates in its own markup, one line per button:

```
Dialog:
    event Accepted
    Button:
        id: ok
        on_click: await root.emit(Accepted())
```

`self` is the Button and `root` is the Dialog — the *Name resolution* table already says so — so the translation costs
one line and the outer document never learns the dialog has buttons in it at all. That is the boundary *Aliases* exists
to defend, arrived at without a new kind of declaration.

That is the answer for telling somebody *outside*. For the component's own hand-written half the next section is
the answer, and it does not cost even the one line.

### Which child it was is a question the generator answers

Bubbling gets a child's event to the component; it cannot say **which** child. `Widget.emit()` walks from the emitter
upward and hands each handler the event alone, `Event` declares no fields, and `ClickEvent` deliberately adds none —
*Declaring an event* above is what makes that a feature, since two input routes have to arrive as one thing. So a
`Dialog` with an OK and a Cancel button in it hears both clicks through one `on_click` and has nothing to switch on.

**The component never asks. The generator answers, by wiring each id'd child to a handler named after it.** For every
id'd child and every event that child's class declares in `emits`, the generated class declares a handler and assigns
it:

```
Dialog:
    Button:
        id: cancel
        text: "Cancel"
```

```python
class Dialog(_Widget):

    cancel: Button

    async def on_cancel_click(self, event: _Event) -> bool:     # dialog.nml:25
        """``cancel`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.cancel = Button(parent=self)                       # dialog.nml:24
        self.cancel.text = "Cancel"                             # dialog.nml:30
        self.cancel.on_click = self.on_cancel_click             # dialog.nml:25
```

```python
class Dialog(Widget):
    async def on_cancel_click(self, event: Event) -> bool:
        self.result = False
        return True
```

The name is `on_` + the id + the stem of the event's own handler: `cancel` and `ClickEvent`, whose handler navkit
derives as `on_click`, compose to `on_cancel_click`. **There is no second naming rule** — the stem is read off
`Event.handler`, the same value `emit()` looks the handler up under, so an event class that renames its handler renames
this too and nothing has to be told twice.

#### The stub is the whole mechanism

`on_cancel_click` on the generated class is a no-op returning False, and the hand-written half overrides it. Every
property worth having falls out of that one shape, and it works only because the generated class is the **base** and
the hand-written one the derived — the same fact *The two halves of a component* forced for its own reasons, here
paying for itself a second time.

- **The generated file stays a pure function of the `.nml`.** It never reads `dialog.py` to decide what to emit. This
  is the objection that would otherwise have sunk the whole convention: the alternative is emitting the wiring only
  when an `ast.parse` of the sibling finds a matching method, which makes a generated file's *contents* depend on a
  file it is forbidden to know, so deleting a method rewrites `dialog_nml.py` and `navml build --check` reports drift
  for an edit made somewhere else.
- **A component that does not care pays nothing.** No `AttributeError` at construction for the stub nobody wanted, and
  no `getattr(self, f"on_{id}_{stem}", None)` in the generated `__init__` — which would be lookup by computed name,
  the registry *The handler name is read off the event class, not invented* refuses.
- **The specific hook does not take the general one away.** The stub returns False, so a click the hand-written half
  did not name carries on up to the component's own `on_click`, exactly as it would have if the stub were not there.
  A component may write both, and reading them together reads in the order `emit()` walks: the named child first, then
  everything else. `navml/widgets/dialog.py` is that example — `ok` overrides its stub, `cancel` does not, and the
  dialog's `on_click` is what dismisses it.
- **`check_handlers` enforces `async def` on both halves, for free.** It scans `vars(cls)` for `on_*` at class
  creation, so a synchronous stub or a synchronous override fails where it is written rather than at the first click.
  This is what the `on_*` spelling buys, and it is why the *routed* method below is deliberately spelled otherwise.
- **The author owns the return value.** This is not a markup handler, so *A markup handler always consumes* does not
  reach it: watching without consuming is `return False`, and needs no escape hatch.

#### What an explicit markup line is still for

The convention cannot name two children routed to one method, cannot reach a widget with no id, and has nothing to say
when the method wants to be named for what the component *does* rather than for what happened to it. Those keep the
form *A handler body is one line* below already implies, which at a child block reaches the component through `root`:

```
Button:
    id: info
    on_click: await root.show_info(event)
```

**The routed method is not an `on_*`** — `show_info`, never `on_info`. The prefix means one thing in this codebase,
*navkit found me under `event.handler`*, and a method reached from one markup line was found by nobody. Two costs
beyond the misreading. Its return value would mean two things at once, since the generated function discards what it
returns while the bubbling walk would read it. And wired by hand it is called twice: `self.info.on_click =
self.on_click` is found by the walk on the button, called, and — if it declines — found again on the component one step
up, under the same name, and called again with the same event. What the `on_*` name would have bought is the
`check_handlers` coverage above, and the last check below buys it back while naming the `.nml` line as well.

**An explicit handler line suppresses the convention for that child and that event.** Both would assign to
`self.info.on_click` and one would win silently, so the generator emits only the markup's and declares no stub.

#### What the generator checks about a handler line

Four, of which the first two are the convention's own and the third replaces a check this file previously specified
wrongly. All are generation-time and all name the `.nml` line.

- **A composed name the sibling `.py` defines must name an id the document declares.** `ast.parse` the sibling `.py`
  **without importing it** — the pass *Name resolution* above already describes — and refuse an `async def on_X_Y`
  whose `on_Y` is the handler name of a live `Event` subclass and whose `X` is no id. This is the price of composing a
  name out of an id, and paying it is what makes the composition safe: without it, renaming `id: cancel` leaves
  `on_cancel_click` sitting in the other file with nothing calling it and the button silently dead, which is the worst
  shape any failure in this document takes. With it, the rename fails the build naming both files.
- **A composed name may not collide with a handler navkit would derive anyway.** `on_cancel_click` is `cancel` +
  `on_click`, and it is also what a `CancelClickEvent` would be delivered to. Refuse the document naming both
  readings. The set to test against is the one *What the generator checks, and why it needs two answers* above already
  walks with `Event.__subclasses__()`. Composed names are checked against the component's own properties and ids too,
  as ids already are against its class.
- **A markup `on_X:` line may not land on an object whose class already implements `on_X`.** This replaces the
  by-name check under *The handler's one argument is `event`*, which was wrong in both directions: read by name alone
  it refuses a document whose line lands on a *child* and shadows nothing, and it never sees `on_key:` on a `Button:`
  block quietly beating `Button.on_key`, because the `.py` it parses is the document's and not the child's. Phrased
  about the object it is one rule asked two ways, the difference being which half exists yet — on the root block the
  class is the hand-written half, which cannot be imported and so is parsed; on a child block it is the child's class,
  which *The cold build* already requires to be live. `Widget.on_key` and `Widget.on_mouse_click` are do-nothing
  stubs, so ask which class in the MRO owns the name. A document meaning to replace a child's own handling gives the
  child a subclass; a document wanting the keys the child left alone puts the line on an ancestor block, where the
  walk reaches it anyway.
- **A handler body must `await` a method the sibling `.py` defines with `async def`, and must not await a plain one.**
  Both failures are close to silent — an un-awaited coroutine is a `RuntimeWarning` at the next collection and a button
  that does nothing. Checked only where the `def` is visible in that file; an inherited method falls through to the
  run-time `TypeError`, which is what any hand-written call already gets.

Not checked, deliberately: that the routed method exists. Being right about an inherited one means following the
import graph into a base component's `.py`, and what it buys is an `AttributeError` naming the component and the
method, raised at the click. Nothing here fails late or lies.

#### Not adopted

- **A `sender` field on `Event`.** It adds no information — the wiring already knows which child it was — and
  relocates it into the one place it is least useful, inviting `if event.sender is self.cancel:` in a component's
  `on_click`: dispatch by identity, in Python, over widgets the document declared, re-broken by every rename. The
  convention is that `if` chain compiled away. It would also have to be written by `emit()` into a frozen dataclass
  every widget shares, for the benefit of the callers that do not want it.
- **Bubbling alone, with no convention at all.** It cannot tell a component's children from its children's children:
  a `Dialog` containing a `FramedButton` catches that button's click identically. Kept for what it is actually good
  at, which is the two cases the convention does not serve — treating every click alike, and watching one without
  claiming it.
- **Wiring by hand in the hand-written `__init__`.** `self.cancel.on_click = self._cancelled` works, ids being live on
  the line after `super().__init__()`. It is refused as the ordinary form because it moves *what is connected to what*
  out of the document, which is the split the file layout rests on; because it is invisible from the `.nml`, where the
  reader sees `id: cancel` and no handler; because it forfeits every check above; and because it runs *after* the
  generated `__init__`, so it silently overwrites a markup line for the same child and event and leaves a document
  that lies about itself. It remains the only spelling for a widget the markup never declared — one built in a method,
  one handed to `Application.overlay()` — and for the Python-only shape, where there is no markup line to write.

## Compiling a property expression

Everything to the right of a property's `:` is stored as source text:

```
Panel:
    width: parent.width // 2
```

`navkit.reactive.bind()` takes a callable of exactly one argument, called with the object that owns the attribute, so
the generator has to produce:

```python
self.left.width = _bind(lambda _o: _o.parent.width // 2)
```

`_bind` rather than `bind` because that is the name the generated preamble imports it under — every generated-code
example in this file spells the generator's own machinery with a leading underscore, and hand-written Python still
calls `bind`. *Importing another component* says why.

The bare `parent` in the markup is not a free variable there — it names something about the widget. Turning the text
into a lambda is therefore a *rewrite*, not a wrapping: string formatting would have to know which names in an arbitrary
expression refer to the widget, which refer to another object in the document, and which are ordinary globals like
`max`.

The rewrite is done on the syntax tree — `ast.parse(source, mode="eval")`, transform the free `Name` nodes, wrap the
result in a one-argument `ast.Lambda`, `ast.unparse` it into the generated class. A prototype of exactly this compiled
all eleven of the current
`Manager`'s bindings correctly, including the scoping corner cases below.

### Name resolution

Checked in this order. **The widget's own property wins**: a bare name inside a widget means that widget first, so
adding an `id` elsewhere in a document can never silently change what an existing expression refers to. An id that
collides with a property name is simply unreachable by a bare name from inside that widget.

| A free name in the expression                                                           | compiles to                                              | example                                                      |
|-----------------------------------------------------------------------------------------|----------------------------------------------------------|--------------------------------------------------------------|
| bound inside the expression itself — a comprehension target, a nested lambda's argument | left alone                                               | `e` in `', '.join(e.name for e in entries)`                  |
| `self`                                                                                  | the lambda's argument                                    | `self.width` → `_o.width`                                    |
| `root`                                                                                  | the component instance                                   | `root.left.width` → `self.left.width`                        |
| `parent`, or any reactive attribute the widget's class declares                         | an attribute of the lambda's argument                    | `parent.width` → `_o.parent.width`                           |
| an `id` declared elsewhere in the same document                                         | a closure reference to the component instance            | `left.width` → `self.left.width`                             |
| anything else                                                                           | left alone, resolved as a global of the generated module | `max`, `min`, and whatever the document imports              |

For the component's own expressions the fourth row includes the properties the document itself declares, which are on
no class until the generator has emitted one — see *Declaring a property* above. It includes aliases as well, in both
directions: the component's own, and those of a component used as a child. `declarations()` returns them, because an
alias is one of navkit's declarations — see *Aliases* above — so the rewriter needs no second source that could fall out
of step with the first.

That last row read "and whatever the paired handler module imports" until *The two halves of a component* was settled,
and the `__bases__` splice made it false: the two halves are separate modules with separate globals, so a compiled
expression cannot see what `button.py` imports and never could. *Importing another component* is what gives the document
back the capability the row promises, and the row now says so.

**Inside a handler body the same table applies, with one substitution.** The function's one argument is the event
rather than the owner — *The handler's one argument is `event`* below — so every row reading "the lambda's argument"
means instead the expression naming the owner in the enclosing `__init__`, `event` joins the first row as a name the
function itself binds, and nothing else moves.

Only the leftmost name of an attribute chain is rewritten: `parent.width` becomes
`_o.parent.width`, never `_o.parent._o.width`.

**An attribute the markup's expressions name has to be declared in the markup.** The `own` set is `declarations(base)`
plus what the document itself declares, and the hand-written half is not in it — that module does not exist when the
base is generated, and importing it would be a cycle. So a `reactive()` declared only in `button.py` falls through to
the last row of the table, compiles to a global of the generated module, and raises a `NameError` that lazy-and-cached
bindings surface at first read, arbitrarily far from the line that caused it. The rule is the cheap half of the fix and
costs nothing: a property markup reads is a `property` line. The other half the generator can afford whenever it is
wanted — `ast.parse` the sibling `.py` *without importing it*, collect the class-body `name: T = reactive(...)`
assignments, and report the collision at generation time with the `.nml` line. The hand-written half may still declare
whatever the markup never names.

`root` comes from Kivy and names the component the markup declares — the generated `self`, which is *not* what `self`
means in the markup. That is the one place where the QML/Kivy vocabulary and the generated Python disagree, so the
generator should never emit a bare
`self` for anything but the component.

Because the ids become attributes of the component, `root.<id>` also reaches an id that a widget's own property shadows:
inside a `Panel`, `cursor` is the panel's own property and
`root.cursor` is the widget declared with `id: cursor`.

**An id may not collide with an attribute of the component's own class**, and the generator has to reject one that does.
The component is a `Widget`, so `id: width` would be stored as
`self.width` — the component's own reactive width, silently broken rather than shadowed, and
`root.width` would read the geometry back instead of the widget. This is not a case the expression compiler can rescue;
it has to fail when the document is compiled, naming the line. The banned set is exactly `declarations(component_class)`
plus its ordinary attributes (`children`, `parent`, …).

### Worked example

The markup for the desktop `navigator/__main__.py` builds by hand today, matching
`Manager._place()` as it now stands:

```
from navigator.widgets.console import Console
from navigator.widgets.keybar import KeyBar
from navigator.widgets.menubar import MenuBar
from navigator.widgets.panel import Panel

Manager:
    property console_visible: False

    MenuBar:
        id: menu
        x: 0
        y: 0
        width: parent.width
        height: 1
    KeyBar:
        id: keybar
        x: 0
        y: max(1, parent.height - 1)
        width: parent.width
        height: 1
    Panel:
        id: left
        x: 0
        y: 1
        width: parent.width // 2
        height: max(3, parent.height - 2)
        visible: not parent.console_visible
    Panel:
        id: right
        y: 1
        x: parent.width // 2
        width: parent.width - left.width
        height: max(3, parent.height - 2)
        visible: not parent.console_visible
    Console:
        id: console
        x: 0
        y: 1
        width: parent.width
        height: max(1, parent.height - 2)
        visible: parent.console_visible
```

The four import lines name a package the conversion has to create. `MenuBar`, `Panel`, `Console` and `KeyBar` all live
in `navigator/__main__.py` today, and while `from navigator.__main__ import Panel` would resolve, it would resolve to a
*second* copy of the module `python -m navigator` is already running as `__main__` — so the widgets have to move out of
the entry point before any of this compiles. That is a consequence of the import spelling rather than a cost of it: the
document says where its children come from, and saying it makes the problem visible at the top of the file instead of
at run time.

The three `visible` lines are the whole of Ctrl+O, and they are ordinary boolean expressions over a reactive attribute —
nothing about them needs a new language feature. What they do need is the `property` line above, which *Declaring a
property* settles. `Console(left)`'s constructor argument is the one hole the example still has, and it is the first of
the two left in the section after next.

and what the generator emits — verified output of the prototype, not an illustration, re-spelled only where *Importing
another component* later underscored the generator's own names (`bind` to `_bind`), which is a rename and changes
nothing the run established. Run against a real widget tree it
reproduces the geometry `navigator/__main__.py` produces by hand, at 80x24, 120x40, and 200x60. The prototype predates
the console, so the run covered the four widgets below and not the `Console` or the three `visible` lines; those compile
by the same rules —
`visible` is an ordinary reactive attribute and `not parent.console_visible` an ordinary expression — but they are
unverified, and the emitted block is left as it was actually produced rather than extended by hand:

```python
    def __init__(self, **kwargs: _Any) -> None:
      super().__init__(**kwargs)
      self.menu.x = 0
      self.menu.y = 0
      self.menu.width = _bind(lambda _o: _o.parent.width)
      self.menu.height = _bind(lambda _o: 1)
      self.keybar.x = 0
      self.keybar.y = _bind(lambda _o: max(1, _o.parent.height - 1))
      self.keybar.width = _bind(lambda _o: _o.parent.width)
      self.keybar.height = _bind(lambda _o: 1)
      self.left.x = 0
      self.left.y = 1
      self.left.width = _bind(lambda _o: _o.parent.width // 2)
      self.left.height = _bind(lambda _o: max(3, _o.parent.height - 2))
      self.right.y = 1
      self.right.x = _bind(lambda _o: _o.parent.width // 2)
      self.right.width = _bind(lambda _o: _o.parent.width - self.left.width)
      self.right.height = _bind(lambda _o: max(3, _o.parent.height - 2))
```

Note `x: 0` compiling to a plain `0` while `height: 1` compiles to a binding — that was the constant-size trap described
below, and the decision recorded there since supersedes it: with the generated class overriding `layout()`, `height: 1`
compiles to a plain `1` too. `self.left.width` in the last-but-one line is the id reference, resolved through the
closure over the component; every other name went to `_o`.

The `property` line compiles to neither of these but to a line of the generated *class body*, and is unverified for the
same reason the `Console` is — the prototype predates it:

```python
class Manager(_Widget):
    console_visible = _reactive(False)
```

The prototype was run against a widget tree that already existed, so what it emits is the property half of the generated
`__init__` only. The real generator constructs the four widgets first — see *Ids* — and construction being a separate earlier pass
is also why `right` may name `left`
regardless of which of the two the document declares first.

Two expressions written only to exercise the scope tracking, from the same run:

```python
  self.left.footer_text = _bind(lambda _o: ', '.join((e.name for e in _o.entries)))
  self.left.error = _bind(lambda _o: (lambda entries: entries)(_o.cursor))
```

The first keeps `e` a comprehension target while `entries` beside it becomes `_o.entries`. In the second the nested
lambda's argument `entries` shadows the property of that name, and the outer `cursor` still resolves to `_o.cursor`.

### Two things that fall out of the rule

- **A literal is not a binding — except for a size.** `height: 1` has nothing to depend on, so it is tempting to compile
  it to a plain assignment rather than a cell holding a constant expression. That is right for `x`, `y` and anything
  else, and *wrong* for `width` and
  `height`: `Widget.layout()` cascades the parent's size into every child whose size is not bound, so a constant size
  assigned plainly is silently overwritten on the first resize. This was measured, not guessed — compiling `height: 1`
  to an assignment gave the menu bar a height of 24 in an 80x24 terminal. `navigator/__main__.py`'s `bind(lambda w: 1)`
  is therefore not redundancy; the binding is what protects the constant.

  The tidier fix belongs to navml rather than to the expression compiler, and it is now **decided**: a generated class
  overrides `layout()` to size only itself and does not cascade into its children, because a component whose children
  are all placed by markup does not want the inherited cascade at all. So a literal `width` or `height` compiles to a
  plain value like everything else, and the trap does not exist for generated code.

  Three things follow. `Widget.layout()`'s `is_bound` guard becomes a concern of hand-written widgets only — it stays,
  because they still need it, but nothing the generator emits relies on it. A markup child that says nothing about its
  size therefore *stays zero* rather than silently filling its parent, which is the honest failure: the size is missing
  from the document and the screen says so. And `Manager` already works this way, having no `layout()`
  at all, so the emitted shape matches the worked example below rather than departing from it.
- **A `computed` target is a generation-time error.** `Panel.title_text` is a `@computed`, and `Computed.__set__`
  refuses a binding. The generator knows the widget's class, so
  `title_text: …` in markup should be rejected with a line number instead of failing when the widget is first painted.

### The `style` block

One property is not compiled as a Python expression at all:

```
Panel:
    style:
        bg: $surface
        fg: white
```

The block is a **stylesheet fragment**, in the `.nss` value grammar rather than Python, and it compiles to a
declarations string assigned to `inline_style` — the same attribute a runtime
`widget.inline_style = "bg: red"` writes, since `navkit/DESIGN.md` makes that one slot rather than two. Read that file's
*Where a widget's style comes from* before implementing this.

Two things follow, and both are worth having:

- **`$name` is meaningful here and nowhere else in a `.nml` file.** A variable is a stylesheet concept; inside an
  ordinary property expression the free names resolve by the table under *Name resolution* above, where `$` is not even
  valid Python. The block is the boundary, and it is a sharp one because the two sides are different languages.
- **The generator validates the block, and should.** A property name checks against `Style`'s fields **or** the widget
  properties something has declared — `navkit.stylesheet.declared_property()` is the read side of that registry, and
  the union is the one the `.nss` parser itself checks, so `border: double` is as legal here as it is in a sheet.
  Values check against the literal grammar and, where the property declared a vocabulary, against that too. All of it
  at generation time with the `.nml` line, leaving only variable *resolution* to run time, because the sheets do not
  exist yet. That makes the markup channel strictly better than the code channel, where a malformed string cannot
  surface until the widget is first painted and the failure is then cached.

The variable reference surviving to run time is what makes a theme swap reach markup-authored styles: the string is
parsed inside the `style` computed, which reads the reactive variable table, so replacing the sheet restyles these
widgets along with everything else.

### A handler body is one line

**A handler written in markup is one line, and it compiles to a function holding that one statement.** Anything
longer — a branch, a loop, a `try`, two statements in sequence — is a method in the hand-written half, and the markup
line calls it:

```
Button:
    text: "Quit"
    on_click: await self.confirm_quit()
```

`confirm_quit()` lives in `button.py` and may be as long as it needs to be. **The `await` is not decoration**: the
method is `async def` like everything else a handler reaches, and without it the line builds a coroutine, drops it,
returns `True`, and the button does nothing — a `RuntimeWarning` at the next collection and no traceback. *What the
generator checks about a handler line* above is what catches the omission.

The spelling of the handler line and what the function is handed besides the component were both deferred to *Still
open* from here, and both are answered now — *The handler's one argument is `event`* below, and *Which child it was is
a question the generator answers* above for the line that routes to a method. Neither touches this rule, which governs
the body rather than the line introducing it.

Four reasons, in the order they carry weight:

- **There is one expression compiler, and this is what keeps it one.** A handler body goes through the transformer in
  the appendix exactly as a property expression does, and its free names resolve by the table under *Name resolution*
  above — `self`, the ids and the reactive attributes mean there what they mean everywhere else in the document. A
*block* needs a second set of rules stacked on that one, for the names a body may *write* rather than read:
  `count = 0` in a handler is a dead local, `self.count = 0` is an attribute of the owner, and the two look alike. One
  statement asks that question once and leaves it answerable by the parser, the statement being the whole body; a block
  interleaves reads and writes until the rewriter has to carry a scope of its own. *Naming rules* above records that
  Kivy resolves names one way inside a property expression and the opposite way inside an `on_*` handler; a second set
  of rules is how a language arrives there, and one table used in both places is the whole of the alternative.
- **The failure stays findable.** A binding's failure is already cached and surfaces arbitrarily far from where it was
  written — *Source mapping* above — and the answer there was that generated code is a real file every tool can
  read. A one-line body is one emitted statement carrying one `# button.nml:12` comment, so the frame a traceback
  names and the markup line its reader wants are the same line. A block is one frame standing in for many markup lines,
  and the line wanted is the one the block opened on, which nothing in the traceback names.
- **It is the split the file layout already makes.** *The two halves of a component* gives `button_nml.py` the tree and
  `button.py` the handlers. This rule reads that same sentence one level down: markup says *what* is connected to what,
  Python says *how*. A document grown a body of logic has stopped describing a tree.
- **It costs the markup-only shape nothing.** A component with no `.py` half that needs a real handler gains one, and
  *The two halves of a component* is explicit that gaining it changes no import line anywhere and no line of the markup
  either. The escape hatch is one new file and no edit.

The parser check is mechanical: a line indented under a handler line is an error, and the message names the component's
`.py` file. Lines indented under a *property* line are a different question, still open below.

Not adopted: allowing the long form and leaving its length to convention, which is what both ancestors do. Kivy takes an
indented block of statements under `on_press:` and compiles it out of the file's text at load time, so nothing but Kivy
reads it — no completion, no checker. QML takes a JavaScript function body inline, which its engine does report
properly; the cost there is not tooling but the document, which stops being a tree and becomes a program with a tree in
it. The advice that follows in both is to keep such bodies short, and enforcing that is cheaper than repeating it.

### The handler's one argument is `event`

**Every handler takes exactly one argument, the event object, and in markup it is always called `event`.**

```
Label:
    id: b
    on_key: self.text = event.key
```

A hand-written handler may call it whatever it likes — the call is positional — but there is nothing to gain by it:
navkit's own hooks already say `event` throughout, `Widget.on_key(self, event)` and `Application.on_mouse_click(self,
event)` included, so markup is adopting the house spelling rather than inventing one.

A `Label:` and not a `Button:`, deliberately, and the difference is the subject of *What the generator checks about a
handler line* above: the line assigns onto the instance, and an instance attribute beats a class method, so on a
`Button` it would land in front of `Button.on_key` and take Space and Enter away from the button without saying so. A
`Label` implements neither handler, so this is what the rule permits.

Two halves to the rule, and the second is the one that needs defending:

- **Fixed at one argument**, because markup has no parameter list and should not grow one. A property line and a handler
  line are the same shape — `name:` and one line of Python — and a parameter list is precisely what would make them two
  shapes. So the arity cannot vary with the event. One serves an event that carries something and an event that carries
  nothing alike, provided the object always exists, which is navkit's side of it: an argumentless event is already
  idiomatic there — `Event` declares no fields and `WakeEvent` adds none.

  This once carried a second clause, that a future `on_mount` would announce itself with an empty event rather than an
  empty argument list. **That is void.** navkit's lifecycle hooks are not handlers and not called `on_*`, because the
  mount walk runs from a constructor and a constructor cannot await — `navkit/DESIGN.md`, *Why the hook is not an
  event, and not called `on_*`*. The rule above is unaffected; only the example it reached for is.
- **Fixed at the name `event`**, because with no parameter list there is nobody to ask. The author cannot name it, so
  the language names it, once, for every handler in every document.

**`event` therefore joins `self`, `root` and `parent` in the reserved list** that *Naming rules* above checks, and for
that section's own reason: a document allowed to declare `id: event` or `property event:` would have the name mean
`self.event` in a property expression and the handler's argument inside a handler body. That is the divergence
*Naming rules* convicts Kivy of, arrived at from a different direction. One list, checked once, in the parser.

**What it does to the compiled form** — three things, the second of which amends the section above:

- **A handler does not take the owner, so it closes over it.** `bind()`'s convention is that an expression's one
  argument is the object that owns the attribute — *What this asks of navkit* below — and a handler's one argument is
  now spoken for. So markup's `self` compiles not to the function's parameter but to the expression that names the
  owner in the enclosing `__init__`: `self.b` for a widget with an id, the anonymous local otherwise. **This is one
  change to the transformer in the appendix**, whose `owner` becomes an expression rather than a name; every other row
  of *Name resolution* reads unchanged, `root` still being the component's bare `self` and an id still `self.<id>`.
- **The emitted form is a one-statement `def` inside `__init__`** — not a lambda, and not a method on the generated
  class:

  ```python
  def __init__(self, **kwargs: Any) -> None:
      super().__init__(**kwargs)
      self.b = Label(parent=self)  # id: b

      async def _on_key(event):  # button.nml:4
          self.b.text = event.key
          return True
      self.b.on_key = _on_key
  ```

  **`async def`, not `def`.** Every handler is awaited — `navkit/DESIGN.md`, *Every handler is `async def`* — and
  `_call` holds an instance-assigned one to it at the call, which is precisely the case markup compiles to. A
  synchronous one raises `TypeError` at the first key rather than at generation, and a body that awaits anything, which
  the canonical routed body below does, could not be compiled at all.

  **Not a lambda**, because the commonest handler body there is — the one in the example above — is an assignment, and a
  lambda cannot hold one. The way to keep the literal lambda is to rewrite `self.title = event.key` into a `setattr`
  call, which makes the transformer rewrite *statements* as well as names and drags in augmented assignment, subscript
  targets and chained targets behind it. That is the seam *A handler body is one line* exists to avoid, so the emitted
  shape gives way rather than the rule. **Not a method**, because *Building the tree* above already establishes the
  hazard: a derived component's generated class would name its handlers by the same rule as its base's and shadow them,
  which is the argument that keeps the tree out of a `_build()` method.

  The body is copied through with its free names rewritten and nothing else done to it, so the one statement under
  the comment is exactly the one markup line it names. The `return True` beneath it is the generator's own, for the
  reason in the next bullet.
- **An assignment beats a method, which is backwards here, so the generator rejects the pair.**
  `self.b.on_click = _on_click` lands on the instance and wins over a `def on_click` defined on the class — and for a
  component written as both halves that inverts the usual precedence, the hand-written class being the derived one that
  wins everywhere else. `navkit/DESIGN.md` states the rule and leaves the catch here, under *One handler per widget per
  event*, because the assignment is legal and navkit cannot tell a shadow from an intention. **The rule is about the
  object the line lands on, not about a name**, and *What the generator checks about a handler line* above states it
  and says why a check phrased by name alone was wrong in both directions. A component that wants the Python one
  deletes the markup line; a component that wants both writes the markup line to call the method.
- **A markup handler always consumes.** navkit reads a handler's return value as *stop propagating* — `dispatch_key`
  offers a key to the children topmost-first and stops at the first `True` — and a body that is an assignment returns
  `None`, so without this the commonest handler there is would read its event and let it through. The third possible
  answer goes out first: passing the body's value through makes `on_key: self.close()` consume or not according to what
  `close()` happens to return, which is the value-dependent divergence this file refuses everywhere else. The two that
  remain are both fixed and so both uniform, and the choice between them is not about the body at all but about which
  of the two cases stays reachable from the other side. Under *never consumes*, a markup-only component could not bind
  a key at all without growing a Python half, which would make the first-class markup-only shape degenerate after all.
  Under *always consumes*, a component that merely watches an event writes that one handler in its `.py`, where a
  handler returns what it likes. The rarer case is the one that pays, and the failure it can cause is legible: an outer
  handler that stops running, with the document that claimed the event one level in.

  Two edges. Where the protocol ignores the value — `Application.on_resize` is annotated `-> None` — the `return True`
  costs nothing, and where it reads it the answer is the same every time, which is the property being bought. And the
  emit mechanism has since been designed around this same protocol rather than around a broadcast —
  `navkit/DESIGN.md`, *Emitting: a widget event walks up* — so consuming means something for a widget's own events
  too: the ancestors do
  not see what the document that named the widget has claimed. The two notes agree on which claim is the specific one.
- **It works for input as well as for signals.** `Widget.emit()` now exists — `navkit/DESIGN.md`, *Emitting: a
  widget event walks up* — and it looks a handler up under `event.handler`, which finds an instance attribute exactly
  as `dispatch_key` finds `self.on_key`. So one emitted assignment serves both directions: a key arriving from the
  terminal and a `ClickEvent` a sibling raised reach the same generated function, with the same one argument, under the
  same name. What the widget library adds is more events to handle, not a different shape of handler.

### Source mapping

This matters more here than in most code generators. A binding is lazy and its failure is *cached* — `_Cell._recompute`
in `navkit/reactive.py` stores the exception and re-raises it at every read — so a bad expression surfaces when
something first reads the value, arbitrarily far from where it was written.

That argued for carrying the `.nml` line and column onto the rewritten nodes (`ast.increment_lineno`, then
`ast.fix_missing_locations`), compiling with the `.nml` path as the filename, and registering the generated source with
`linecache` so the traceback points at the markup. **That was the right answer for generating in memory, and the file
layout has since overtaken it.** `button_nml.py` is a real, tracked file, so a frame names it for free and `inspect`,
`pydoc`, `pdb`, coverage and every checker follow without being told anything — none of which a `linecache` entry under
a `.nml` filename gets, and coverage actively breaks on, since it parses `co_filename` as Python.

So the generated code keeps its own filename and the markup location rides along as a trailing `# button.nml:12`
comment on each emitted line, which costs nothing because `ast.unparse` is already called per statement. A reader who
reaches a generated frame is one grep from the markup that produced it, and every tool that reads a traceback keeps
working. If the balance ever tips back — if `.nml` frames matter more than tooling does — the earlier scheme is intact
above and the cost of returning to it is `[tool.setuptools.package-data]` gaining nothing, since *The markup ships*
already puts the `.nml` in the wheel.

### What this asks of navkit

Already true, and worth stating so it does not get broken by accident:

- `bind()` takes an expression of **exactly one argument**, called with the object that owns the attribute. That
  convention is what makes a mechanical rewrite possible at all. An alias is the one place the second half of it is
  deliberately set aside, and it is navml that sets it aside rather than navkit — see *A binding through an alias is
  re-owned* above.
- Ids resolve through a closure over the component instance, so generated bindings must be installed inside a method
  where that instance is in scope — the generated `__init__` — not in a class body.
- The generator needs the set of reactive attributes a class declares, inherited ones included. **Now there**:
  `navkit.reactive.declarations(cls)`, exported from `navkit`, replacing the prototype's `properties()` in the appendix
  below. It maps each name to its declaration rather than returning bare names, because the generator needs to tell the
  two kinds apart in opposite directions — a `Reactive` is a rewrite target and a binding target, a `Computed` is a
  generation-time error (see *A `computed` target is a generation-time error* above). An override shadows what it
  inherits, as attribute lookup does.

  The name is unambiguous: the widget-level property that used to share it is now
  `Widget.style_declarations`, renamed when this function landed, because one meant the reactive surface a *class*
  declares and the other the stylesheet declarations that cascaded onto one *instance*.
- Nothing at all for `property`. `reactive()` is callable in a generated class body, and that is the entire
  requirement — see *Declaring a property* above.

Three small things for `alias`. The third turned out to be a bug and is already fixed; the other two are not
needed before the generator is written:

- **`_Declaration` wants a public name.** navml subclasses it — see *Aliases* — and the prototype in the appendix
  below already imports the private one. Renaming it `Declaration`, keeping the private spelling, turns an
  implementation detail into the extension point it has become; its contract is that `cell()` may be overridden to
  answer for a cell the declaration does not own.
- **`Binding` wants a method returning a copy with the owner fixed.** Without one navml reads `Binding.expression`
  directly, which is mild — it is `__slots__`-declared, unprefixed, and exactly what navkit's own binding installation
  reads — but the re-wrap under *A binding through an alias is re-owned* is navkit's shape to give rather than
  navml's to improvise.
- **`unbind()` and `is_bound()` refusing a `Computed`.** This one was a bug rather than a request, and navkit's
  rather than markup's: `is_bound()` answered `True` for a computed, and `unbind()` unlinked its cell and left it
  frozen at whatever it last returned, never to update again. Aliases only made it easy to reach, by giving `cell()`
  a second way in. **Now fixed**, and the guard rejects `Computed` rather than requiring `Reactive`, so an `_Alias`
  passes it — an alias whose *target* is a computed is navml's to reject, under *Checked when the document is
  compiled* above.

### What converting `Manager` needs and does not have

The worked example above is the plan for proving the markup machinery: compile
`navigator/__main__.py`'s desktop from a `.nml` and check the frames still match. Walking the real class rather than the
example turns up four things markup cannot say, none of them recorded anywhere until now. Each blocks that conversion,
so each needs an answer before the generator is finished. Two of the four are settled above — declaring a reactive
property under *Declaring a property*, and naming another component under *Importing another component*; the two that
remain are not answered here, because each is a language decision rather than an oversight.

**Component parameters.** `Panel(left)`, `Panel(right)` and `Console(left)` take a positional constructor argument, and
`Manager(left, right, scheme)` takes three. Markup has properties, which are set *after* construction, and no way to
name a value arriving from outside the document at all. The two obvious shapes pull in opposite directions: a declared
parameter list on the component (`Manager` takes `left`, `right`) keeps the Python call site unchanged and makes the
document a function of its arguments; or every parameter becomes an ordinary reactive property assigned after
the generated `__init__`, which is uniform but changes when a `Panel` first knows its path — and `Panel` starts a scan from
an effect the moment it is constructed, so "after" is not free. QML's answer is that a component has no constructor and
everything is a property; Kivy's is that `__init__` keeps taking Python arguments.

**Child and base types have no import spelling** — **settled**, under *Importing another component* above. `Manager:`
names `MenuBar`, `Panel`, `Console` and `KeyBar`, and a root block may name a base as well, and a document now says
where each of them comes from in Python's own words. It was one question rather than two: a base and a child are both
just a type named in markup, and one `from … import …` line answers for either.

**`_stylesheet` has no markup spelling.** `Manager.__init__` assigns it so the desktop is styled with or without an
application around it, and a `style:` block compiles to
`inline_style`, which is a different slot with different semantics — one is a sheet governing a subtree, the other is a
handful of declarations for one widget. A component that brings its own look needs the first and can only say the
second.

Two smaller ones, recorded so they are not rediscovered: `effect()` registration order in
`Panel.__init__` is load-bearing — the comment there says "declaration order is flush order" — and has no markup
spelling either; and `MenuBar` and `KeyBar` paint loops over module-level constants, which is the repeater/model
question that the *Parts* argument in
`navkit/DESIGN.md` deliberately does **not** answer, because it answers the row case instead.

### Still open

- Multi-line property bodies. With indentation carrying the block structure, the natural form is the expression
  continuing on lines indented under the `property:` — which is how Kivy writes a handler. **Half of this is now
  answered.** *A handler body is one line* above refuses statements, and refuses them for reasons that do not care
  whether the line is a handler or a property: one expression compiler, one resolution table, and a hand-written half
  that is already where length belongs. What is left is the lexical question of whether a single expression may be
  *spread* over several indented lines, which changes nothing about what is emitted — still a one-argument lambda —
  and so can be settled by the parser alone.
- Whether `equal=` is expressible in markup, on a `bind()` expression or on a `property` declaration. It is one
  question asked at two sites, and until it is answered a property needing one is declared in the hand-written half.
  There is no third site: on an `alias` the answer is settled and it is no, for the reason under *Three things an alias
  cannot carry*.
- Comment syntax. Kivy's `.kv` takes `#` and nothing here has said whether `.nml` does. Every declaration this file
  moves into markup carries a `#:` doc comment in `navigator/__main__.py` — `Panel`'s seven, `Console.revision`,
  `Manager.console_visible` — so without one the reason a property exists is lost in translation.
- ~~Signal and handler syntax.~~ **Answered, and the last piece was the one this bullet said had to wait.** The body,
  its argument and what it returns are settled under *A handler body is one line* and *The handler's one argument is
  `event`*; navkit's half is *Emitting: a widget event walks up*; and *Declaring an event* above settles where an
  event class lives, that a widget declares what it emits, how the generator checks an `on_click:` line in both of the
  places bubbling makes it legal, and the `event ClickEvent` directive. The alias question *Aliases* deferred here is
  answered with it, and answered as no. What this bullet was waiting for — "the widget library declares some events to
  point at" — is `navml/widgets/button.py`, which emits a `ClickEvent` from two input routes.
- **How the hand-written half gets type-checked.** The id-annotation question is answered — the generated class carries
  `left: Panel` and the generated `.pyi` carries the merged surface — but the answer brought its own problem with it,
  measured rather than predicted: a stub replaces its module for a checker, so an error planted in `button.py` is not
  reported even when mypy is pointed at the file. Options are a second pass with the stubs held aside, moving the stubs
  somewhere only an IDE reads, or accepting that handler bodies are covered by tests rather than by a checker. Nothing
  forces a choice yet, because `CLAUDE.md` records that no lint tooling is configured; the day it is, this is waiting.

### Appendix: the transformer

The prototype, minus its `__main__` block. `properties()` is the part that should become
`navkit.reactive.declarations()`.

```python
import ast

from navkit.reactive import _Declaration


def properties(cls: type) -> set[str]:
    """Every reactive attribute *cls* declares, inherited ones included."""
    return {
        name
        for klass in cls.__mro__
        for name, value in vars(klass).items()
        if isinstance(value, _Declaration)
    }


class _Scope(ast.NodeTransformer):
    """Rewrite the free names of an expression to where they actually live."""

    def __init__(self, owner: str, own: set[str], ids: set[str]):
        self.owner = owner
        self.own = own
        self.ids = ids
        self.bound: list[set[str]] = []

    def visit(self, node: ast.AST) -> ast.AST:
        """Hand *node* to whichever handler claims its type.

        ``ast.NodeTransformer`` dispatches by building the method name
        ``visit_`` + the node class -- ``visit_NamedExpr`` -- which is the
        stdlib's spelling, not this project's.  A table costs one lookup and
        keeps the handlers named like everything else; anything absent from
        it falls through to the stdlib's own recursive walk.
        """
        handler = self._handlers.get(type(node))
        return handler(self, node) if handler else self.generic_visit(node)

    # -- scopes the expression opens itself ---------------------------------

    def _targets(self, node) -> set[str]:
        return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}

    def _lambda(self, node):
        args = node.args
        self.bound.append(
            {a.arg for a in args.posonlyargs + args.args + args.kwonlyargs}
            | {a.arg for a in (args.vararg, args.kwarg) if a}
        )
        try:
            return self.generic_visit(node)
        finally:
            self.bound.pop()

    def _comprehension(self, node):
        self.bound.append(set())
        try:
            for generator in node.generators:
                generator.iter = self.visit(generator.iter)
                self.bound[-1] |= self._targets(generator.target)
                generator.ifs = [self.visit(i) for i in generator.ifs]
            for field in ("elt", "key", "value"):
                if (part := getattr(node, field, None)) is not None:
                    setattr(node, field, self.visit(part))
            return node
        finally:
            self.bound.pop()

    def _named_expr(self, node):
        node.value = self.visit(node.value)
        if self.bound:
            self.bound[-1] |= self._targets(node.target)
        return node

    # -- the rewrite itself --------------------------------------------------

    def _name(self, node):
        name = node.id
        if not isinstance(node.ctx, ast.Load):
            return node
        if any(name in scope for scope in self.bound):
            return node
        if name == "self":
            return ast.Name(id=self.owner, ctx=ast.Load())
        if name == "root":
            # The markup's root is the generated ``self``; the markup's
            # ``self`` is the widget the property belongs to.
            return ast.Name(id="self", ctx=ast.Load())
        if name == "parent" or name in self.own:
            return ast.Attribute(
                value=ast.Name(id=self.owner, ctx=ast.Load()),
                attr=name,
                ctx=ast.Load(),
            )
        if name in self.ids:
            return ast.Attribute(
                value=ast.Name(id="self", ctx=ast.Load()),
                attr=name,
                ctx=ast.Load(),
            )
        return node

    #: Filled in last, so the handlers above are already in the class body.
    _handlers = {
        ast.Name: _name,
        ast.Lambda: _lambda,
        ast.NamedExpr: _named_expr,
        ast.ListComp: _comprehension,
        ast.SetComp: _comprehension,
        ast.GeneratorExp: _comprehension,
        ast.DictComp: _comprehension,
    }


def compile_property(
        source: str, cls: type, ids: set[str], owner: str = "_o"
) -> str:
    """The right-hand side of the assignment the generator should emit."""
    tree = ast.parse(source, mode="eval")
    if isinstance(tree.body, ast.Constant):
        # Nothing to depend on -- but see the constant-size trap above: a
        # literal width or height still has to be compiled to a binding, so
        # the real generator needs the property name here as well.
        return ast.unparse(tree)
    body = _Scope(owner, properties(cls), ids).visit(tree.body)
    lam = ast.Lambda(
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg=owner)],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        ),
        body=body,
    )
    return f"bind({ast.unparse(ast.fix_missing_locations(lam))})"
```
