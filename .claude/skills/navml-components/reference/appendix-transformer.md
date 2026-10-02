### Appendix: the transformer

The prototype, minus its `__main__` block, kept as the record of what was reasoned out before the code existed.
**`navml/expression.py` is the real one**, and differs in five places, each recorded above: `properties()` became
`navkit.reactive.declarations()` and then `navml.resolve.attributes()`; `owner` became an expression rather than a
name, deep-copied at each substitution site; `event` joins the bound names for a handler body; the scope stack starts
with one frame rather than none, so a top-level walrus records its target; and `compile_property` reports whether it
rewrote anything instead of special-casing a constant, the constant-size caveat in its docstring here having been
retired by the `layout()` override.

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
