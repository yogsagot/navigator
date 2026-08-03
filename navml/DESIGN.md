# navml design notes

The markup language, its parser, the code generator and the widget library are all
unwritten. This file records decisions made ahead of them, so the work starts from a spec
rather than rediscovering it. Anything not written down here is still open.

## Where the inspiration is taken from

**QML for the architecture, Kivy for the syntax.** From QML come the shape of the language
and its semantics: a declarative tree of objects, `id`s naming them, properties that are
expressions re-evaluated when what they read changes, and a component that is a class. From
Kivy comes the surface, because the file should read like Python:

- **blocks are made by indentation**, not by braces;
- **no semicolons**, and one property per line;
- a widget opens a block with a trailing colon — `Panel:` — and its properties and children
  are the lines indented under it;
- `id: left` is a directive rather than a property — see *Ids* below.

So a declaration reads:

```
Panel:
    id: left
    width: parent.width // 2
```

and never `Panel { id: left; width: parent.width // 2 }`.

## Ids

An id is a **name, never a value**, and both ancestors agree on that much. QML's docs are
blunt about it — "it is not possible to access `myTextInput.id`" — and Kivy deprecated
`Widget.id` through the 1.x line and removed it in 2.0.0, leaving only the `ids` dict. navml
follows: a widget has no `id` attribute, and there is no reverse lookup either (QML keeps one
for C++, `qmlContext(o)->nameForObject(o)`). Nothing needs one. An id exists so that one
expression can name another widget in the same document, and that job is finished at
generation time. If a test or a debugger ever wants to name a widget at run time, that is a
separate reactive attribute on `Widget` — QML's `objectName`, which is a different thing with
different rules — not this.

**In particular, an id is not a stylesheet selector.** `README.md` promises navkit a CSS-like
stylesheet, and the obvious reading of that is `#left` matching `id: left`. It does not: the
lookup engine is navkit, which cannot depend on navml and has nothing to match anyway, and a
navml id is unique per document where CSS `#` presumes it is unique across everything being
styled. `#` matches `Widget.name`, an ordinary run-time property written in markup as
`name: "left-panel"` like any other. This is the same split Qt draws between a QML `id` and
`QObject::objectName`; `navkit/DESIGN.md` records it in full.

Where the two ancestors *disagree* is what an id compiles to, and there navml takes QML's
side. QML assigns each id a slot index in the instance's `QQmlContextData` at compile time, so
a reference costs an array read. Kivy stores a `WeakProxy` in a `DictProperty` and re-resolves
the name out of that dict on every re-evaluation, because its compiled expression is `eval`'d
with the id map as its globals.

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
`self.left.width`, so an attribute is the form the compiled output wants anyway; the paired
handler module writes `self.left` by hand and gets completion and a rename for it; and a
mistyped id fails as an `AttributeError` naming the component, rather than a `KeyError` on a
dict that could be anybody's.

The attribute holds the widget itself, not a weak proxy. Kivy needs `WeakProxy` because its
`ids` dict outlives the widget it names; a navml component owns its tree the way a QML context
owns its objects and is collected with it, so there is no cycle to break by hand. That also
avoids Kivy's sharpest corner, where the key survives the widget and `root.ids.gone` is a live
entry holding a dead proxy that raises `ReferenceError` on any access.

Two consequences worth stating outright:

- **The id attribute is never reassigned after `_build()`**, and that is what makes an ordinary
  non-reactive attribute safe. A binding compiled from `left.width` reads `self.left` and then
  subscribes to `Panel.width`: it tracks the panel's width, but *not* a replacement of
  `self.left`. QML does track its id slot — `captureProperty(context->idValueBindings(idx))` —
  because incremental creation can refill one. navml has no such moment.
- **Removing a widget from `children` leaves `self.left` pointing at it.** Deliberate: an id
  names a widget the document declares, not a position in the tree.

### Naming rules

Checked by the parser, each failing with the `.nml` line:

| Rule | Rejects | Why |
| --- | --- | --- |
| a Python identifier, and not a keyword | `id: 2left`, `id: class` | it is emitted into generated source as an attribute name |
| not one of the reserved words `self`, `root`, `parent` | `id: parent` | each already means something in the resolution table below |
| not an attribute of the component's own class | `id: width` | it would be stored as `self.width` — see *Name resolution* |
| unique within the document | two `id: left` | the second assignment would silently win |

The reserved-word row is the one both ancestors got wrong, in the same direction. QML checks
id names against the JavaScript globals but not against `parent`, so `id: parent` compiles and
shadows `Item.parent` for a whole component scope. Kivy rejects exactly `self` and `root` and
silently shadows the rest — and shadows them *in opposite directions* depending on context:
inside a property expression the globals overwrite the ids, inside an `on_*` handler the ids
overwrite the globals. One explicit list, checked once, in the parser.

Not adopted: QML's rule that an id must start with a lowercase letter. It exists to keep ids
distinguishable from type names, and navml distinguishes them by position — a type opens a
block, an `id:` is a directive line indented under it — so the rule buys nothing.

### Scope, order, and anonymity

**An id is scoped to its document.** One `.nml` file declares one component, and its ids are
visible from every expression in that file and from nowhere else. This is Kivy's per-rule
boundary rather than QML's component scopes, which chain upward so that a delegate can read
names from wherever it happened to be instantiated. The reason is mechanical rather than
aesthetic: the compiled form is a closure over *one* component instance, and there is no
enclosing instance in scope to chain to.

**Order does not matter.** An expression may name an id declared further down the document.
`_build()` constructs every widget before it installs any binding, and a binding body is not
run until something reads the value, so a forward reference costs nothing.

**A widget without an id is anonymous, by construction.** It gets a local in `_build()`, which
dies when `_build()` returns — the parent's `children` list is then the only reference to it:

```python
    def _build(self) -> None:
        _w1 = MenuBar(parent=self)
        _w1.width = bind(lambda _o: _o.parent.width)

        self.left = Panel(parent=self)          # id: left
        self.left.width = bind(lambda _o: _o.parent.width // 2)
```

No rule is needed to keep an un-id'd widget out of expressions: an id reference always
compiles to `self.<id>` and never to a bare local, so the widget is unreachable from any
expression whether or not the local is still alive.

**Ids are live before any hand-written code runs.** `_build()` assigns every id attribute
before it installs the first binding, and runs to completion during the component's
construction — so there is no window in which `self.left` is missing. Kivy has one, which is
why its ids are unusable from `__init__` and why 1.11 had to add `on_kv_post` after years of
`Clock.schedule_once` folklore. The contract this puts on the still-undecided merge with the
hand-written half is a single line: the generated `__init__` calls `_build()`, and a
hand-written `__init__` must call `super().__init__()` before it touches an id.

## Compiling a property expression

Everything to the right of a `property:` is stored as source text:

```
Panel:
    width: parent.width // 2
```

`navkit.reactive.bind()` takes a callable of exactly one argument, called with the object
that owns the attribute, so the generator has to produce:

```python
self.left.width = bind(lambda _o: _o.parent.width // 2)
```

The bare `parent` in the markup is not a free variable there — it names something about the
widget. Turning the text into a lambda is therefore a *rewrite*, not a wrapping: string
formatting would have to know which names in an arbitrary expression refer to the widget,
which refer to another object in the document, and which are ordinary globals like `max`.

The rewrite is done on the syntax tree — `ast.parse(source, mode="eval")`, transform the
free `Name` nodes, wrap the result in a one-argument `ast.Lambda`, `ast.unparse` it into the
generated class. A prototype of exactly this compiled all eleven of the current
`Manager`'s bindings correctly, including the scoping corner cases below.

### Name resolution

Checked in this order. **The widget's own property wins**: a bare name inside a widget means
that widget first, so adding an `id` elsewhere in a document can never silently change what
an existing expression refers to. An id that collides with a property name is simply
unreachable by a bare name from inside that widget.

| A free name in the expression | compiles to | example |
| --- | --- | --- |
| bound inside the expression itself — a comprehension target, a nested lambda's argument | left alone | `e` in `', '.join(e.name for e in entries)` |
| `self` | the lambda's argument | `self.width` → `_o.width` |
| `root` | the component instance | `root.left.width` → `self.left.width` |
| `parent`, or any reactive attribute the widget's class declares | an attribute of the lambda's argument | `parent.width` → `_o.parent.width` |
| an `id` declared elsewhere in the same document | a closure reference to the component instance | `left.width` → `self.left.width` |
| anything else | left alone, resolved as a global of the generated module | `max`, `min`, and whatever the paired handler module imports |

Only the leftmost name of an attribute chain is rewritten: `parent.width` becomes
`_o.parent.width`, never `_o.parent._o.width`.

`root` comes from Kivy and names the component the markup declares — the generated `self`,
which is *not* what `self` means in the markup. That is the one place where the QML/Kivy
vocabulary and the generated Python disagree, so the generator should never emit a bare
`self` for anything but the component.

Because the ids become attributes of the component, `root.<id>` also reaches an id that a
widget's own property shadows: inside a `Panel`, `cursor` is the panel's own property and
`root.cursor` is the widget declared with `id: cursor`.

**An id may not collide with an attribute of the component's own class**, and the generator
has to reject one that does. The component is a `Widget`, so `id: width` would be stored as
`self.width` — the component's own reactive width, silently broken rather than shadowed, and
`root.width` would read the geometry back instead of the widget. This is not a case the
expression compiler can rescue; it has to fail when the document is compiled, naming the
line. The banned set is exactly `declarations(component_class)` plus its ordinary attributes
(`children`, `parent`, …).

### Worked example

The markup for the desktop `nav.py` builds by hand today:

```
Manager:
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
    Panel:
        id: right
        y: 1
        x: parent.width // 2
        width: parent.width - left.width
        height: max(3, parent.height - 2)
```

and what the generator emits — verified output of the prototype, not an illustration. Run
against a real widget tree it reproduces the geometry `nav.py` produces by hand, at 80x24,
120x40 and 200x60:

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

Note `x: 0` compiling to a plain `0` while `height: 1` compiles to a binding — the reason is
the constant-size trap described below. `self.left.width` in the last-but-one line is the id
reference, resolved through the closure over the component; every other name went to `_o`.

The prototype was run against a widget tree that already existed, so what it emits is the
property half of `_build()` only. The real generator constructs the four widgets first — see
*Ids* — and construction being a separate earlier pass is also why `right` may name `left`
regardless of which of the two the document declares first.

Two expressions written only to exercise the scope tracking, from the same run:

```python
        self.left.footer_text = bind(lambda _o: ', '.join((e.name for e in _o.entries)))
        self.left.error = bind(lambda _o: (lambda entries: entries)(_o.cursor))
```

The first keeps `e` a comprehension target while `entries` beside it becomes `_o.entries`.
In the second the nested lambda's argument `entries` shadows the property of that name, and
the outer `cursor` still resolves to `_o.cursor`.

### Two things that fall out of the rule

- **A literal is not a binding — except for a size.** `height: 1` has nothing to depend on,
  so it is tempting to compile it to a plain assignment rather than a cell holding a constant
  expression. That is right for `x`, `y` and anything else, and *wrong* for `width` and
  `height`: `Widget.layout()` cascades the parent's size into every child whose size is not
  bound, so a constant size assigned plainly is silently overwritten on the first resize.
  This was measured, not guessed — compiling `height: 1` to an assignment gave the menu bar a
  height of 24 in an 80x24 terminal. `nav.py`'s `bind(lambda w: 1)` is therefore not
  redundancy; the binding is what protects the constant.

  The tidier fix belongs to navml rather than to the expression compiler: a component whose
  children are all placed by markup does not want the inherited cascade at all, so the
  generated class should override `layout()` to size only itself. With that in place a
  constant size is safe as a plain assignment. Until it is decided (see below), compile a
  literal `width` or `height` to a binding and everything else to a value.
- **A `computed` target is a generation-time error.** `Panel.title_text` is a `@computed`,
  and `Computed.__set__` refuses a binding. The generator knows the widget's class, so
  `title_text: …` in markup should be rejected with a line number instead of failing when the
  widget is first painted.

### The `style` block

One property is not compiled as a Python expression at all:

```
Panel:
    style:
        bg: $surface
        fg: white
```

The block is a **stylesheet fragment**, in the `.nss` value grammar rather than Python, and it
compiles to a declarations string assigned to `inline_style` — the same attribute a runtime
`widget.inline_style = "bg: red"` writes, since `navkit/DESIGN.md` makes that one slot rather
than two. Read that file's *Where a widget's style comes from* before implementing this.

Two things follow, and both are worth having:

- **`$name` is meaningful here and nowhere else in a `.nml` file.** A variable is a stylesheet
  concept; inside an ordinary property expression the free names resolve by the table under
  *Name resolution* above, where `$` is not even valid Python. The block is the boundary, and it
  is a sharp one because the two sides are different languages.
- **The generator validates the block, and should.** Property names check against `Style`'s
  fields and values against the literal grammar, both at generation time with the `.nml` line —
  leaving only variable *resolution* to run time, because the sheets do not exist yet. That
  makes the markup channel strictly better than the code channel, where a malformed string
  cannot surface until the widget is first painted and the failure is then cached.

The variable reference surviving to run time is what makes a theme swap reach markup-authored
styles: the string is parsed inside the `style` computed, which reads the reactive variable
table, so replacing the sheet restyles these widgets along with everything else.

### Source mapping

This matters more here than in most code generators. A binding is lazy and its failure is
*cached* — `_Cell._recompute` in `navkit/reactive.py` stores the exception and re-raises it
at every read — so a bad expression surfaces when something first reads the value,
arbitrarily far from where it was written.

Carry the `.nml` line and column onto the rewritten nodes (`ast.increment_lineno`, then
`ast.fix_missing_locations`), compile with the `.nml` path as the filename, and register the
generated source with `linecache` so the traceback points at the markup.

### What this asks of navkit

Already true, and worth stating so it does not get broken by accident:

- `bind()` takes an expression of **exactly one argument**, called with the object that owns
  the attribute. That convention is what makes a mechanical rewrite possible at all.
- Ids resolve through a closure over the component instance, so generated bindings must be
  installed inside a method where that instance is in scope — `_build(self)` — not in a class
  body.
- The generator needs the set of reactive attributes a class declares, inherited ones
  included. `navkit.reactive` exposes no such helper; the prototype reached for the private
  `_Declaration` and walked `cls.__mro__`. A public `declarations(cls)` belongs in
  `navkit/reactive.py` when the generator is written, not before.

### Still open

- Whether a generated class overrides `layout()` to size only itself, leaving its children
  entirely to the markup. It would remove the constant-size trap above, and make
  `Widget.layout()`'s `is_bound` guard a concern of hand-written widgets only.
- Multi-line property bodies. With indentation carrying the block structure, the natural
  form is the expression continuing on lines indented under the `property:` — which is how
  Kivy writes a handler — compiling to a nested `def` rather than a lambda, still taking one
  argument. What is undecided is whether a body may contain statements at all, or only an
  expression spread over several lines.
- Whether `bind()`'s `equal=` is expressible in markup.
- Signal and handler syntax, and how it meets the hand-written half of the class.
- How a component exports a widget inside it. Ids stop at the document, so markup that uses a
  `Panel` component cannot name anything declared inside `panel.nml`. QML's answer is
  `property alias buttonText: textItem.text` — a compile-time redirect resolved against the
  declaring component's own ids, at most one property deep, forwarding writes rather than
  binding to them. Kivy has no answer at all, which is exactly why Kivy code reaches through
  `outer.ids.child.ids.grandchild` and the boundary ends up meaning nothing. Deferred until
  components in separate documents exist — but shipping the boundary without the hatch is a
  known failure mode, not an open question.
- Whether the generator emits type information for the id attributes, so that the paired
  handler module completes `self.left` as a `Panel`. Class-level annotations or a generated
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
