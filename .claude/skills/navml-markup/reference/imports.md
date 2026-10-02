## Importing another component

A document names types it does not otherwise say where to find: `Button:` as a child block, `FramedButton(Button):` as
a root. It says where in **Python's own words**, at the top of the file:

```
from navml.widgets.dialog.label import Label

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

from navml.widgets.dialog.label import Label              # button.nml:1, verbatim
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
  reasoned about: importing `navml.widgets.dialog.label` used to load all four components, because the package imported each
  by name, so a cold build could import nothing until everything had already been generated. `navml/widgets/__init__.py`
  now re-exports through :pep:`562`'s module `__getattr__`, which keeps `from navml.widgets import Button` working,
  breaks the coupling, and takes the rest of the library out of the import path of anything that wanted one widget. A
  `TYPE_CHECKING` block beside it carries the real types, because a module `__getattr__` answers `Any` to a checker and
  would otherwise make every component untyped at every call site.

### What this asks of navkit

Nothing. The import block is copied into a Python module, and Python resolves it.

