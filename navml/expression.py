"""Turning the text right of a ``:`` into Python.

The parser keeps every expression as source text with the line it came from,
because compiling one needs the document's types to be live.  This is where it
is compiled -- and it is a *rewrite* rather than a wrapping::

    width: parent.width // 2        ->   _bind(lambda _o: _o.parent.width // 2)

The bare ``parent`` in the markup is not a free variable there; it names
something about the widget.  String formatting would have to know which names in
an arbitrary expression refer to the widget, which refer to another widget in the
document, and which are ordinary globals like ``max`` -- so the names are
rewritten on the syntax tree, where that question has an answer.

**Name resolution, in the order it is asked** (*Name resolution* in
``navml/DESIGN.md`` has the argument for each row):

=================================== =========================================
a free name in the expression       compiles to
=================================== =========================================
bound by the expression itself      left alone
``self``                            the owner expression
``root``                            the component -- ``self``
``parent``, or an attribute the     an attribute of the owner
widget's class declares
an ``id`` the document declares     an attribute of the component
anything else                       left alone, a global of the generated
                                    module
=================================== =========================================

The widget's own property wins over an id, so adding an ``id`` elsewhere in a
document can never silently change what an existing expression refers to.

**There is one transformer and two entry points.**  A handler body goes through
the same table with one substitution: the function's one argument is the
*event*, so the owner is no longer a lambda parameter but an expression naming
the widget in the enclosing ``__init__`` -- ``self.caption``, or the anonymous
local for a widget with no id -- and ``event`` joins the names the function
binds for itself.  Nothing else moves.  Keeping it one transformer is the whole
reason a handler body is one line: a block would need a second set of rules for
the names a body may *write*.
"""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
from typing import Iterable

from navml.errors import MarkupError

#: The generated module underscores everything it needs for itself, so that a
#: document may import any name at all and get exactly what it asked for.
BIND = "_bind"

#: The lambda parameter a compiled property expression takes.  Underscored for
#: the same reason, since the expression it wraps is the document's.
ARGUMENT = "_o"


@dataclass(frozen=True, slots=True)
class Compiled:
    """One expression, and the two things the emitter decides by.

    ``constant`` and ``rewritten`` are not the same question and are asked at
    different sites.  A *declaration* asks both -- a constant is a default, an
    expression that reads nothing reactive is a ``factory``, and one that reads
    something is a binding installed in ``__init__``.  A property *line* asks
    only ``rewritten``: an expression that touched nothing about the widget can
    never produce a different answer later, so evaluating it once at
    construction is all a binding would ever do.
    """

    #: The rewritten expression, unwrapped.
    expression: str
    #: Whether any free name was resolved to the widget or the component.
    rewritten: bool
    #: Whether the whole expression was a literal.
    constant: bool

    @property
    def binding(self) -> str:
        """The expression as :func:`~navkit.reactive.bind` takes it."""
        return f"{BIND}(lambda {ARGUMENT}: {self.expression})"

    @property
    def value(self) -> str:
        """What a property line assigns: a binding, or the value itself."""
        return self.binding if self.rewritten else self.expression


class _Scope(ast.NodeTransformer):
    """Rewrite the free names of an expression to where they actually live."""

    def __init__(
        self, owner: ast.expr, own: Iterable[str], ids: Iterable[str],
        bound: Iterable[str] = (),
    ):
        self.owner = owner
        self.own = frozenset(own)
        self.ids = frozenset(ids)
        #: A stack of the names each enclosing scope binds.  It starts with one
        #: frame rather than none -- the prototype in ``navml/DESIGN.md`` starts
        #: empty -- so that a walrus at the top level of an expression records
        #: its target: ``(width := 3) + width`` makes a local, and the second
        #: ``width`` must not become the widget's.
        self.bound: list[set[str]] = [set(bound)]
        self.rewrote = False

    def visit(self, node: ast.AST) -> ast.AST:
        """Hand *node* to whichever handler claims its type.

        :class:`ast.NodeTransformer` dispatches by building the method name
        ``visit_`` + the node class -- ``visit_NamedExpr`` -- which is the
        stdlib's spelling, not this project's.  A table costs one lookup and
        keeps the handlers named like everything else; anything absent from it
        falls through to the stdlib's own recursive walk.
        """
        handler = self._handlers.get(type(node))
        return handler(self, node) if handler else self.generic_visit(node)

    # -- scopes the expression opens itself ---------------------------------

    def _targets(self, node: ast.AST) -> set[str]:
        return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}

    def _lambda(self, node: ast.Lambda) -> ast.AST:
        args = node.args
        self.bound.append(
            {a.arg for a in args.posonlyargs + args.args + args.kwonlyargs}
            | {a.arg for a in (args.vararg, args.kwarg) if a}
        )
        try:
            return self.generic_visit(node)
        finally:
            self.bound.pop()

    def _comprehension(self, node: ast.AST) -> ast.AST:
        """A comprehension's iterable is outside the scope its target opens.

        Which is what keeps ``', '.join(e.name for e in entries)`` working:
        ``entries`` is read from the widget and ``e`` is the comprehension's
        own, one clause apart.
        """
        self.bound.append(set())
        try:
            for generator in node.generators:  # type: ignore[attr-defined]
                generator.iter = self.visit(generator.iter)
                self.bound[-1] |= self._targets(generator.target)
                generator.ifs = [self.visit(i) for i in generator.ifs]
            for field in ("elt", "key", "value"):
                if (part := getattr(node, field, None)) is not None:
                    setattr(node, field, self.visit(part))
            return node
        finally:
            self.bound.pop()

    def _named_expr(self, node: ast.NamedExpr) -> ast.AST:
        node.value = self.visit(node.value)
        self.bound[-1] |= self._targets(node.target)
        return node

    # -- the rewrite itself -------------------------------------------------

    def _name(self, node: ast.Name) -> ast.AST:
        name = node.id
        if not isinstance(node.ctx, ast.Load):
            return node
        if any(name in scope for scope in self.bound):
            return node
        if name == "self":
            return self._rewritten(copy.deepcopy(self.owner))
        if name == "root":
            # The markup's ``root`` is the generated ``self``; the markup's
            # ``self`` is the widget the property belongs to.
            return self._rewritten(ast.Name(id="self", ctx=ast.Load()))
        if name == "parent" or name in self.own:
            return self._rewritten(
                ast.Attribute(
                    value=copy.deepcopy(self.owner), attr=name, ctx=ast.Load()
                )
            )
        if name in self.ids:
            return self._rewritten(
                ast.Attribute(
                    value=ast.Name(id="self", ctx=ast.Load()),
                    attr=name,
                    ctx=ast.Load(),
                )
            )
        return node

    def _rewritten(self, node: ast.expr) -> ast.expr:
        self.rewrote = True
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


# -- the two entry points ----------------------------------------------------


def compile_expression(
    source: str,
    *,
    own: Iterable[str] = (),
    ids: Iterable[str] = (),
    owner: str = ARGUMENT,
    line: int = 0,
    filename: str = "<markup>",
) -> Compiled:
    """Compile one property expression.

    *own* is every attribute the widget's class declares and *ids* every id the
    document declares; *owner* is the expression naming the widget the property
    belongs to, which is the lambda's parameter unless a handler is being
    compiled through :func:`compile_handler`.
    """
    tree = _parse(source, line, filename, mode="eval")
    scope = _Scope(_owner(owner, line, filename), own, ids)
    body = scope.visit(tree.body)
    return Compiled(
        expression=ast.unparse(ast.fix_missing_locations(body)),
        rewritten=scope.rewrote,
        constant=isinstance(tree.body, ast.Constant),
    )


def compile_handler(
    body: str,
    *,
    own: Iterable[str] = (),
    ids: Iterable[str] = (),
    owner: str,
    line: int = 0,
    filename: str = "<markup>",
) -> str:
    """Compile one handler body, which is one statement.

    Returns the statement alone: the ``async def`` around it, its ``event``
    parameter and the ``return True`` beneath it are the emitter's, because a
    markup handler always consumes and the document never says so.
    """
    tree = _parse(body, line, filename, mode="exec")
    if len(tree.body) != 1:
        raise MarkupError("a handler is one statement", line, filename)
    scope = _Scope(_owner(owner, line, filename), own, ids, bound={"event"})
    statement = scope.visit(tree.body[0])
    return ast.unparse(ast.fix_missing_locations(statement))


def _parse(source: str, line: int, filename: str, *, mode: str) -> ast.AST:
    """*source* as a tree, or a :class:`MarkupError` naming the markup line.

    The parser has already vetted both shapes, so reaching the failure here
    means something upstream let a malformed line through; it is still reported
    against the document rather than as a traceback out of the generator.
    """
    try:
        # ``async`` is only legal inside a function, and a handler body is
        # allowed to await -- so one is wrapped around it to be parsed.
        if mode == "exec":
            wrapped = "async def _h(event):\n" + _indent(source)
            tree = ast.parse(wrapped)
            return tree.body[0]  # type: ignore[return-value]
        return ast.parse(source, mode=mode)
    except SyntaxError as error:
        raise MarkupError(str(error.msg), line, filename) from error


def _indent(source: str) -> str:
    return "\n".join("    " + part for part in source.splitlines())


def _owner(source: str, line: int, filename: str) -> ast.expr:
    """The owner as a tree, parsed once and copied at each substitution."""
    return _parse(source, line, filename, mode="eval").body  # type: ignore[attr-defined]
