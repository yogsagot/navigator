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
- `id: left` is a directive rather than a property. The widget has no `id` attribute; the
  name is a document-scoped label the generator turns into an attribute of the component.

So a declaration reads:

```
Panel:
    id: left
    width: parent.width // 2
```

and never `Panel { id: left; width: parent.width // 2 }`.

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
