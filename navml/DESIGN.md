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

A plain instance attribute of the component, assigned in `_build()`:

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

- **The id attribute is never reassigned after `_build()`**, and that is what makes an ordinary non-reactive attribute
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
| not one of the reserved words `self`, `root`, `parent` | `id: parent`             | each already means something in the resolution table below |
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
`_build()` constructs every widget before it installs any binding, and a binding body is not run until something reads
the value, so a forward reference costs nothing.

**A widget without an id is anonymous, by construction.** It gets a local in `_build()`, which dies when `_build()`
returns — the parent's `children` list is then the only reference to it:

```python
    def _build(self) -> None:
      _w1 = MenuBar(parent=self)
      _w1.width = bind(lambda _o: _o.parent.width)
  
      self.left = Panel(parent=self)  # id: left
      self.left.width = bind(lambda _o: _o.parent.width // 2)
```

No rule is needed to keep an un-id'd widget out of expressions: an id reference always compiles to `self.<id>` and never
to a bare local, so the widget is unreachable from any expression whether or not the local is still alive.

**Ids are live before any hand-written code runs.** `_build()` assigns every id attribute before it installs the first
binding, and runs to completion during the component's construction — so there is no window in which `self.left` is
missing. Kivy has one, which is why its ids are unusable from `__init__` and why 1.11 had to add `on_kv_post` after
years of
`Clock.schedule_once` folklore. The contract this puts on the still-undecided merge with the hand-written half is a
single line: the generated `__init__` calls `_build()`, and a hand-written `__init__` must call `super().__init__()`
before it touches an id.

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
class Manager(Widget):
    console_visible = reactive(False)
```

Without it, `self.console_visible = bind(...)` would store a `Binding` on an ordinary attribute and do nothing, there
being no descriptor to notice it — the failure whose only symptom is the `<unassigned binding ...>` repr.

What varies is whether a second line joins it in `_build()`, and the test is **whether the expression reads anything
reactive** — precisely whether the rewriter of the next section rewrote any free name:

| The right-hand side  | rewritten? | compiles to                                                                  |
|----------------------|------------|------------------------------------------------------------------------------|
| `False`, `0`, `None` | no         | `console_visible = reactive(False)`                                          |
| `[]`, `Path(".")`    | no         | `entries = reactive(factory=lambda: [])`                                     |
| `self.width // 3`    | yes        | `w = reactive()`, and `self.w = bind(lambda _o: _o.width // 3)` in `_build()` |

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
  `__set__`, so it is a data descriptor and beats the instance `__dict__`. `_build()`'s
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

One knock-on, flagged rather than solved: a binding installed in `_build()` lands *after* the children are constructed,
and `Panel.__init__` starts a directory scan from an effect at construction — so a `Panel` whose `path` came from a
component property would scan once against the default before the binding arrives. That is the *Component parameters*
question under *What converting `Manager` needs and does not have*, which this decision makes reachable without
answering.

This asks navkit for nothing: `reactive()` is callable in a class body, and that is the whole requirement.

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
class Panel(Widget):
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

**An alias to a widget is not offered.** QML has one — `property alias headerItem: header` — and it hands the widget
out whole, which recreates the reach-through with one extra step and no further declaration. It would also be a
declaration with no cell of its own, which `unbind()` and `is_bound()` could not answer for. The case that wants it is
naming an inner button in order to connect a handler to it, and signals are open on both sides of the layer boundary;
settle it with them rather than ahead of them.

### Where it may appear, and what it may be called

**In the root block only**, for the reason `property` is restricted there: it becomes a descriptor on a class, and the
root block is the only block in a document that becomes one.

An alias declares a name on the component, so it joins the `self.<name>` namespace the ids and the declared properties
share, and takes those rules entire — not colliding with an id, not colliding with a declared property, not shadowing
an attribute of the component's base class.

### Checked when the document is compiled

Each failing with the `.nml` line:

- The target's leading name is an **id declared in this document**, and not `self`, `root` or `parent`, which name
  things that have no stable meaning from the other side of the boundary.
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
  that does not exist until `_build()` has run. A component wanting one assigns it there, like anything else.
- **An `equal=`.** It has no cell to put one on. The `equal=` question left open below would otherwise be asked at a
  third site, and this is why it is not: on an alias, never — the comparator belongs to the component that owns the
  target, which is the only side that knows what the value means.
- **A useful error location.** Every message navkit raises names `Header.text`, an attribute that does not appear in
  the document its reader is looking at. `_Alias` should catch and re-raise naming both ends, and carry a `__repr__`
  reading `<alias Panel.title -> header.text>`, so that the three functions which reject a non-declaration say
  something legible when they do.

## Compiling a property expression

Everything to the right of a property's `:` is stored as source text:

```
Panel:
    width: parent.width // 2
```

`navkit.reactive.bind()` takes a callable of exactly one argument, called with the object that owns the attribute, so
the generator has to produce:

```python
self.left.width = bind(lambda _o: _o.parent.width // 2)
```

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
| anything else                                                                           | left alone, resolved as a global of the generated module | `max`, `min`, and whatever the paired handler module imports |

For the component's own expressions the fourth row includes the properties the document itself declares, which are on
no class until the generator has emitted one — see *Declaring a property* above. It includes aliases as well, in both
directions: the component's own, and those of a component used as a child. `declarations()` returns them, because an
alias is one of navkit's declarations — see *Aliases* above — so the rewriter needs no second source that could fall out
of step with the first.

Only the leftmost name of an attribute chain is rewritten: `parent.width` becomes
`_o.parent.width`, never `_o.parent._o.width`.

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

The three `visible` lines are the whole of Ctrl+O, and they are ordinary boolean expressions over a reactive attribute —
nothing about them needs a new language feature. What they do need is the `property` line above, which *Declaring a
property* settles. `Console(left)`'s constructor argument is the one hole the example still has, and it is the first of
the two left in the section after next.

and what the generator emits — verified output of the prototype, not an illustration. Run against a real widget tree it
reproduces the geometry `navigator/__main__.py` produces by hand, at 80x24, 120x40, and 200x60. The prototype predates
the console, so the run covered the four widgets below and not the `Console` or the three `visible` lines; those compile
by the same rules —
`visible` is an ordinary reactive attribute and `not parent.console_visible` an ordinary expression — but they are
unverified, and the emitted block is left as it was actually produced rather than extended by hand:

```python
    def _build(self) -> None:
      self.menu.x = 0
      self.menu.y = 0
      self.menu.width = bind(lambda _o: _o.parent.width)
      self.menu.height = bind(lambda _o: 1)
      self.keybar.x = 0
      self.keybar.y = bind(lambda _o: max(1, _o.parent.height - 1))
      self.keybar.width = bind(lambda _o: _o.parent.width)
      self.keybar.height = bind(lambda _o: 1)
      self.left.x = 0
      self.left.y = 1
      self.left.width = bind(lambda _o: _o.parent.width // 2)
      self.left.height = bind(lambda _o: max(3, _o.parent.height - 2))
      self.right.y = 1
      self.right.x = bind(lambda _o: _o.parent.width // 2)
      self.right.width = bind(lambda _o: _o.parent.width - self.left.width)
      self.right.height = bind(lambda _o: max(3, _o.parent.height - 2))
```

Note `x: 0` compiling to a plain `0` while `height: 1` compiles to a binding — that was the constant-size trap described
below, and the decision recorded there since supersedes it: with the generated class overriding `layout()`, `height: 1`
compiles to a plain `1` too. `self.left.width` in the last-but-one line is the id reference, resolved through the
closure over the component; every other name went to `_o`.

The `property` line compiles to neither of these but to a line of the generated *class body*, and is unverified for the
same reason the `Console` is — the prototype predates it:

```python
class Manager(Widget):
    console_visible = reactive(False)
```

The prototype was run against a widget tree that already existed, so what it emits is the property half of `_build()`
only. The real generator constructs the four widgets first — see *Ids* — and construction being a separate earlier pass
is also why `right` may name `left`
regardless of which of the two the document declares first.

Two expressions written only to exercise the scope tracking, from the same run:

```python
  self.left.footer_text = bind(lambda _o: ', '.join((e.name for e in _o.entries)))
  self.left.error = bind(lambda _o: (lambda entries: entries)(_o.cursor))
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
- **The generator validates the block, and should.** Property names check against `Style`'s fields and values against
  the literal grammar, both at generation time with the `.nml` line — leaving only variable *resolution* to run time,
  because the sheets do not exist yet. That makes the markup channel strictly better than the code channel, where a
  malformed string cannot surface until the widget is first painted and the failure is then cached.

The variable reference surviving to run time is what makes a theme swap reach markup-authored styles: the string is
parsed inside the `style` computed, which reads the reactive variable table, so replacing the sheet restyles these
widgets along with everything else.

### Source mapping

This matters more here than in most code generators. A binding is lazy and its failure is *cached* — `_Cell._recompute`
in `navkit/reactive.py` stores the exception and re-raises it at every read — so a bad expression surfaces when
something first reads the value, arbitrarily far from where it was written.

Carry the `.nml` line and column onto the rewritten nodes (`ast.increment_lineno`, then
`ast.fix_missing_locations`), compile with the `.nml` path as the filename, and register the generated source with
`linecache` so the traceback points at the markup.

### What this asks of navkit

Already true, and worth stating so it does not get broken by accident:

- `bind()` takes an expression of **exactly one argument**, called with the object that owns the attribute. That
  convention is what makes a mechanical rewrite possible at all. An alias is the one place the second half of it is
  deliberately set aside, and it is navml that sets it aside rather than navkit — see *A binding through an alias is
  re-owned* above.
- Ids resolve through a closure over the component instance, so generated bindings must be installed inside a method
  where that instance is in scope — `_build(self)` — not in a class body.
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
example turns up three things markup cannot say, none of them recorded anywhere until now. Each blocks that conversion,
so each needs an answer before the generator is finished. One of the three, declaring a reactive property, is settled
above under *Declaring a property*; the two that remain are not answered here, because each is a language decision
rather than an oversight.

**Component parameters.** `Panel(left)`, `Panel(right)` and `Console(left)` take a positional constructor argument, and
`Manager(left, right, scheme)` takes three. Markup has properties, which are set *after* construction, and no way to
name a value arriving from outside the document at all. The two obvious shapes pull in opposite directions: a declared
parameter list on the component (`Manager` takes `left`, `right`) keeps the Python call site unchanged and makes the
document a function of its arguments; or every parameter becomes an ordinary reactive property assigned after
`_build()`, which is uniform but changes when a `Panel` first knows its path — and `Panel` starts a directory scan from
an effect the moment it is constructed, so "after" is not free. QML's answer is that a component has no constructor and
everything is a property; Kivy's is that `__init__` keeps taking Python arguments.

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
  continuing on lines indented under the `property:` — which is how Kivy writes a handler — compiling to a nested `def`
  rather than a lambda, still taking one argument. What is undecided is whether a body may contain statements at all, or
  only an expression spread over several lines.
- Whether `equal=` is expressible in markup, on a `bind()` expression or on a `property` declaration. It is one
  question asked at two sites, and until it is answered a property needing one is declared in the hand-written half.
  There is no third site: on an `alias` the answer is settled and it is no, for the reason under *Three things an alias
  cannot carry*.
- Comment syntax. Kivy's `.kv` takes `#` and nothing here has said whether `.nml` does. Every declaration this file
  moves into markup carries a `#:` doc comment in `navigator/__main__.py` — `Panel`'s seven, `Console.revision`,
  `Manager.console_visible` — so without one the reason a property exists is lost in translation.
- Signal and handler syntax, and how it meets the hand-written half of the class — and with them whether an alias
  may name a widget rather than a property, which *Aliases* defers to this question rather than settling alone.
- Whether the generator emits type information for the id attributes, so that the paired handler module completes
  `self.left` as a `Panel`. Class-level annotations or a generated
  `.pyi`; it interacts with the import hook.

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
