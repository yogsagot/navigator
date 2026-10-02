### What the generator emits, and what writes it

**The file is written as lines, through `navml/coder.py`'s `Coder`, and not as a syntax tree that is unparsed once.**
A tree carries no comments, and comments are load-bearing in the output: every emitted statement ends in a trailing
`# button.nml:12`, which is the whole of the source map below, and a `#:` run above a declaration in the markup is
re-emitted above the declaration in the Python. `ast.unparse` is still what turns a document's *expressions* into
source, one fragment at a time through `navml/expression.py`; the frame around them is lines. `Coder` gives the
emitter logical indent levels (`add`), a trailing comment on the line just written (`comment(-1, ..., same_line=True)`),
multi-line constants (`add_formatted`) and sub-builders that compose (`block`), which is the whole of what the job
needs.

Three things follow, and they are the emitter's contract rather than its taste:

- **Every widget is constructed before any property is installed.** The stand-ins interleaved the two per child; the
  order matters because `Widget.add` lays out and mounts a child the moment it joins a tree that is already mounted, so
  a widget can be asked for a value before a sibling named further down the document exists. `__init__` is therefore
  one block of `self.<id> = Type(parent=self)` lines and then one block of installations, grouped per widget.
- **Formatting is fixed here rather than left to a formatter**, because `navml build --check` compares text: a rule
  nobody applies twice the same way would report drift on every run. One statement per line, `Coder`'s comment gutter,
  and a binding past 79 columns wrapped at its own `_bind(` bracket. The trailing source-map comment is allowed to
  overhang, since wrapping a line to make room for a comment about it would be the tail wagging the dog.
- **A markup-declared event class in a *merged* component is reachable only from `<stem>_nml`.** `GeneratedLoader`
  republishes `__all__` onto the public module name, so the markup-only shape is fine; `RebaseLoader` copies nothing,
  because the hand-written half owns that namespace. It is a corner rather than a problem: which half declares an event
  follows which half emits it, so a component with a `.py` that wanted to name the class would be declaring it there in
  the first place.

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

Three small things for `alias`, and **all three are now there**:

- ~~**`_Declaration` wants a public name.**~~ **Done.** `navkit.reactive.Declaration`, exported from `navkit`, with
  `_Declaration` kept as an alias because the prototype in the appendix below imports the private spelling. Its
  contract is that `cell()` may be overridden to answer for a cell the declaration does not own.
- ~~**`Binding` wants a method returning a copy with the owner fixed.**~~ **Done:** `Binding.owned_by(owner)`. The
  re-wrap under *A binding through an alias is re-owned* is navkit's shape to give rather than navml's to improvise,
  and it carries `equal` across, because the copy replaces the original at the cell.
- **`unbind()` and `is_bound()` refusing a `Computed`.** This one was a bug rather than a request, and navkit's
  rather than markup's: `is_bound()` answered `True` for a computed, and `unbind()` unlinked its cell and left it
  frozen at whatever it last returned, never to update again. Aliases only made it easy to reach, by giving `cell()`
  a second way in. **Now fixed**, and the guard rejects `Computed` rather than requiring `Reactive`, so an `_Alias`
  passes it — an alias whose *target* is a computed is navml's to reject, under *Checked when the document is
  compiled* above.

### What converting `Manager` needed, and what it turned up

**The conversion is done, and the frames match.** `navigator/widgets/manager/manager/manager.nml` is the desktop and
`navigator/widgets/manager/manager/manager.py` is the handlers. The proof is the one this section always asked for and is worth
keeping the shape of: run both trees — the commit before the conversion and the one after — on a pty at 80x24 against
the same two absolute paths, read the escape stream each writes up to its first complete frame, and compare. It is
3725 bytes either way and `cmp` reports no difference, so the desktop is not merely equivalent but identical down to
the cursor moves. What is left here is the record of what stood in the way, because three of the four blockers were
found by walking the real class and none of them was written down anywhere until it was.

One thing the conversion turned up that this list did not anticipate has a section of its own: *A property a widget
navigates cannot be bound* above. It is the only place where the finished document says *less* than the old
`_place()` did, and the only rule in the language that is about what the child does rather than what the parent
wants.

**Component parameters** — **settled**, under *How a value gets in* above, and the second shape won: every parameter
is an ordinary declared property, arriving as a keyword. What made it affordable was noticing that "after" need not
mean after the tree is built — `Component.__init__` applies the keywords before `Widget.__init__` joins the widget to
its parent, so a `mounted()` sees them. `Panel`'s scan against the default remains, and is recorded there as the price
of "construct, then bind" rather than as an open question. The half that was *not* in this paragraph turned out to
block harder: `Panel(parent=self)` was a `TypeError`, because a required positional argument keeps a widget out of a
document altogether.

**Child and base types have no import spelling** — **settled**, under *Importing another component* above. `Manager:`
names `MenuBar`, `Panel`, `Console` and `KeyBar`, and a root block may name a base as well, and a document now says
where each of them comes from in Python's own words. It was one question rather than two: a base and a child are both
just a type named in markup, and one `from … import …` line answers for either.

**`_stylesheet` has no markup spelling** — **settled**, under *The sheet a component brings* above, and it needed no
spelling of its own: the attribute was already reactive and only lacked a public name. It is `Widget.stylesheet` now
— the walk-up that had the name became `effective_stylesheet` — and a document assigns it like any other property. A `style:` block still compiles to `inline_style`, which remains the
different slot with the different semantics — one is a sheet governing a subtree, the other is a handful of
declarations for one widget.

Two smaller ones, recorded so they are not rediscovered, and **neither blocks this conversion**.

`effect()` registration order in `Panel.__init__` is load-bearing — the comment there says "declaration order is flush
order" — and markup has no spelling for an effect at all. The ordering itself is *guaranteed* rather than merely
observed, which is worth knowing before anything is built on it: `Effect.order` is stamped from a process-global
`itertools.count()` at the moment `effect()` is called, and `Scheduler.flush` sorts the pending list on it, so the
order holds across owners and across whatever queued them. What is missing is only a way to *say* it in markup, and
`Panel` stays a Python-only component until something needs one.

`MenuBar` and `KeyBar` paint loops over module-level constants, which is the repeater/model question that the *Parts*
argument in `navkit/DESIGN.md` deliberately does **not** answer, because it answers the row case instead. `Manager`
reaches neither of their internals — a zero-argument constructor and four geometry bindings each is the whole of their
markup surface — so they stay hand-written and a `manager.nml` needs nothing of them.

### What the generator settled by being written

Five things this file had left implicit, each found by writing the code and each now pinned by a test.

- **A `StyleProperty` joins the `own` set, though it is not a `Declaration`.** *Name resolution* says a bare name
  resolves against what the widget's class declares, and `declarations()` was the obvious reading of that — but a style
  property is authored in a sheet rather than assigned, so it is not in that mapping at all. A bare `icons` would have
  fallen to the last row, compiled to a module global and raised `NameError` at the first read. `navml.resolve`'s
  `attributes(cls)` is the union, and it is what the compiler is handed.
- **`_Component` is appended to every base except `Component` itself.** *The shared base* says the generator emits it
  unconditionally, which is right for every base a document can name but one: `class X(Component, _Component)` is
  `TypeError: duplicate base class`. A document naming it is refused and told to write a bare head, which is the
  spelling that asks for exactly that.
- **A property line carrying a binding must name a declaration on the target class.** *Where the line lands* records
  the failure from the other side — a `Binding` assigned to something that is not reactive is silently *stored*, and
  the only symptom is the `<unassigned binding ...>` repr. The generator has the class in hand, so it says so at
  compile time instead. A literal onto a plain attribute stays legal; it is the binding that cannot work.
- **A widget that paints cannot be markup-only, and `Label` was.** Its `render()` lived in the *generated* file, which
  was tenable only while that file was hand-written; regenerating it would have blanked every `Button` caption. `Label`
  now has a `label.py` holding the painting, and `navml/widgets/dialog/field/field.nml` is the markup-only example in its place: a
  caption and a value composed out of two `Label`s, which paints nothing itself and so needs no hand-written half. The
  general rule is worth stating, because it arrives for every future component: **markup declares and places, Python
  paints**, so a component with a `render()` has two halves by construction.
- **Resolution and checking are separate modules, and the split is not the obvious one.** `navml/resolve.py` refuses
  the two failures that stop a document being resolved at all — an import that does not import, and a type the document
  names that its imports do not bind — because it cannot produce anything without them. Everything else a live class
  can reveal is `navml/checks.py`'s. The reason to keep them apart is that resolution is the one pass that imports
  arbitrary user code, so a test can build a resolution by hand and exercise the emitter with no imports at all.

