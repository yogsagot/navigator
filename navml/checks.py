"""Everything a document can only get wrong against a live class.

The parser answers *what does this document say* and refuses everything a
document can fail on its own -- a malformed line, a reserved word, two ids of
one name.  What is left is every question that needs a class object or the
hand-written half beside the document, and it is all here, raised as a
:class:`~navml.errors.MarkupError` naming the ``.nml`` line.

The split is worth keeping in mind while reading: nothing in this module knows
how to *emit* anything, and nothing in the emitter refuses anything.  A document
that reaches :mod:`navml.generator` has already been checked.

Two of the checks are about the sibling ``.py``, and both are asked of a file
that was parsed rather than imported -- see :mod:`navml.sibling` for why that
matters more than it looks.
"""

from __future__ import annotations

import ast
import inspect
from typing import Iterable, Iterator

from navkit.commands import Command
from navkit.events import Event, emitted, handler_name
from navkit.reactive import Computed, Declaration
from navkit.stylesheet import (
    PropertySpec,
    StyleProperty,
    StylesheetError,
    check_declarations,
    declared_property,
)
from navkit.widget import Widget

from navml.errors import MarkupError
from navml.expression import compile_expression
from navml.parser import (
    AliasDecl,
    Block,
    ClassAttrDecl,
    Document,
    EventDecl,
    StylePropertyDecl,
)
from navml.resolve import Resolved, declared, style_property


def check(resolved: Resolved) -> None:
    """Refuse *resolved*'s document, or return having found nothing."""
    _check_declarations(resolved)
    _check_ids(resolved)
    _check_aliases(resolved)
    _check_children(resolved)
    _check_anchors(resolved)
    _check_properties(resolved)
    _check_styles(resolved)
    _check_keys(resolved)
    _check_commands(resolved)
    _check_handlers(resolved)
    _check_sibling(resolved)


# -- what the root block declares --------------------------------------------


def _check_declarations(resolved: Resolved) -> None:
    """No declaration may shadow something the base already has.

    A ``property`` or an ``alias`` is a data descriptor, so it wins over the
    instance ``__dict__`` and would swallow writes meant for the base's
    attribute; a ``style_property`` is one too.  The banned set is therefore
    everything the base declares *and* everything it ordinarily carries.

    One exception, and navkit's rather than navml's: a ``style_property`` may
    re-declare one the base already has, because two declarations of a key have
    to agree on the *vocabulary* and not on the default -- a dialog framed
    ``double`` beside a widget framed ``single`` is the case the registry exists
    to allow.  The vocabulary is then checked below.
    """
    banned = set(dir(resolved.base))
    for declaration in resolved.document.root.declarations:
        if isinstance(declaration, EventDecl):
            continue
        if isinstance(declaration, ClassAttrDecl):
            _check_class_attribute(resolved, declaration)
            continue
        redeclared = isinstance(declaration, StylePropertyDecl) and (
            style_property(resolved.base, declaration.name) is not None
        )
        if declaration.name in banned and not redeclared:
            _refuse(
                resolved,
                declaration.line,
                f"{declaration.name} is already an attribute of "
                f"{resolved.base.__name__}",
            )
        if isinstance(declaration, StylePropertyDecl):
            _check_style_property(resolved, declaration)


def _check_class_attribute(
    resolved: Resolved, declaration: ClassAttrDecl
) -> None:
    """A ``class`` line overrides a plain class attribute the base has.

    Only one the base already has, so a misspelt name is refused rather than
    left to be read by nothing; and only a plain one, because a reactive or a
    style property replaced by a bare value would stop being one for every
    instance -- ``is_bound(w, Widget.height)`` would refuse the class.  The
    value is a class-level expression, like a key table's.
    """
    base = resolved.base
    name = declaration.name
    try:
        existing = inspect.getattr_static(base, name)
    except AttributeError:
        _refuse(
            resolved,
            declaration.line,
            f"{base.__name__} has no class attribute {name}; a class line "
            f"overrides one the base already has",
        )
    if (
        isinstance(existing, (Declaration, StyleProperty, property))
        or inspect.isfunction(existing)
        or name.startswith("_")
    ):
        _refuse(
            resolved,
            declaration.line,
            f"{base.__name__}.{name} is not a plain class attribute, so a "
            f"class line cannot replace it",
        )
    _class_level(
        resolved,
        declaration.expression,
        declaration.line,
        f"the value of {name!r} failed to evaluate",
        "a class attribute",
    )


def _class_level(
    resolved: Resolved, source: str, line: int, failed: str, what: str
) -> object:
    """Evaluate *source* as the class body will: reading only the imports."""
    tree = ast.parse(source, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id not in resolved.namespace:
            _refuse(
                resolved,
                line,
                f"{node.id!r} is not imported; {what} belongs to the class and "
                f"is made before any instance, so it can name only what the "
                f"import block brings in",
            )
    try:
        return eval(  # noqa: S307 - the document's own expression
            compile(tree, resolved.filename, "eval"), dict(resolved.namespace)
        )
    except Exception as error:  # noqa: BLE001 - reported with its line
        _refuse(resolved, line, f"{failed}: {error}")


def _check_style_property(
    resolved: Resolved, declaration: StylePropertyDecl
) -> None:
    """Two declarations of one key must agree on the vocabulary.

    Not on the default: a dialog framed ``double`` beside a widget framed
    ``single`` is exactly what the registry leaves each class free to decide.
    Asked here so the disagreement names the ``.nml`` line rather than coming
    out of a class body at import.
    """
    existing = declared_property(declaration.name)
    if existing is None:
        return
    proposed = PropertySpec.of(declaration.default, declaration.values)
    if existing != proposed:
        _refuse(
            resolved,
            declaration.line,
            f"{declaration.name} is already declared, and differently: "
            f"{existing} against {proposed}",
        )


def _check_ids(resolved: Resolved) -> None:
    """An id becomes ``self.<id>``, so it may not be one of the base's."""
    banned = set(dir(resolved.base))
    for block in resolved.document.root.walk():
        if block.id is not None and block.id in banned:
            _refuse(
                resolved,
                block.id_line or block.line,
                f"{block.id} is already an attribute of "
                f"{resolved.base.__name__}",
            )


def _check_aliases(resolved: Resolved) -> None:
    """An alias forwards to a reactive attribute, and to nothing else."""
    for declaration in resolved.document.root.declarations:
        if not isinstance(declaration, AliasDecl):
            continue
        target = resolved.ids[declaration.target]
        found = declared(target, declaration.attribute)
        if found is None:
            _refuse(
                resolved,
                declaration.line,
                f"{declaration.attribute} is not a reactive attribute of "
                f"{target.__name__}; an alias forwards to a cell, and a "
                f"plain attribute has none",
            )
        if isinstance(found, Computed):
            _refuse(
                resolved,
                declaration.line,
                f"{target.__name__}.{declaration.attribute} is computed, so "
                f"an alias to it could never be written",
            )


# -- what a child block constructs -------------------------------------------


def _check_children(resolved: Resolved) -> None:
    """A child block compiles to ``Type(parent=self)`` and nothing else.

    Markup sets every property *after* construction, so a widget with a
    required constructor argument cannot appear in a document at all.
    """
    for block in _children(resolved.document):
        cls = resolved.class_of(block)
        required = _required(cls)
        if required:
            _refuse(
                resolved,
                block.line,
                f"{cls.__name__} requires {', '.join(required)} at "
                f"construction; markup constructs a child with parent alone",
            )


def _check_anchors(resolved: Resolved) -> None:
    """An ``anchors:`` block under a layout, which owns its children's places.

    Arranging steps around a bound side rather than fighting it, so anchors
    there would quietly half-work -- a bound ``x`` kept, the width the
    layout's -- instead of failing.
    """
    from navml.widgets.layout.dock_layout import DockLayout
    from navml.widgets.layout.layout import Layout

    for parent in resolved.document.root.walk():
        cls = resolved.class_of(parent)
        if not issubclass(cls, Layout):
            continue
        for block in parent.children:
            if block.anchors is None:
                continue
            # ``dock: none`` is the one child a layout leaves where it is.
            undocked = block.style is not None and any(
                d.name == "dock" and d.value == "none" for d in block.style.declarations
            )
            if not (issubclass(cls, DockLayout) and undocked):
                _refuse(
                    resolved,
                    block.anchors.line,
                    f"{block.type} sits in a {resolved.class_of(parent).__name__}, "
                    f"which places its children itself; anchors place a widget "
                    f"that nothing else does",
                )


def _required(cls: type) -> list[str]:
    try:
        signature = inspect.signature(cls.__init__)
    except (TypeError, ValueError):  # pragma: no cover - builtins only
        return []
    return [
        name
        for name, parameter in list(signature.parameters.items())[1:]
        if parameter.default is inspect.Parameter.empty
        and parameter.kind
        not in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD)
    ]


# -- what a property line lands on -------------------------------------------


def _check_properties(resolved: Resolved) -> None:
    for block in resolved.document.root.walk():
        cls = resolved.class_of(block)
        for line in block.properties:
            _check_property(
                resolved, block, cls, line.name, line.expression, line.line,
                once=line.once,
            )


def _check_property(
    resolved: Resolved,
    block: Block,
    cls: type,
    name: str,
    expression: str,
    line: int,
    *,
    once: bool = False,
) -> None:
    root = block is resolved.document.root
    found = declared(cls, name) if not root else _root_declaration(resolved, name, cls)
    if isinstance(found, Computed):
        _refuse(
            resolved,
            line,
            f"{cls.__name__}.{name} is computed; assign what it derives from",
        )
    if style_property(cls, name) is not None and found is None:
        _refuse(
            resolved,
            line,
            f"{name} is a style property of {cls.__name__}; it is authored in "
            f"a sheet, in a style: block here, and never assigned",
        )
    if once:
        _check_once_names(resolved, block, expression, line)
    if found is None and not once and _is_binding(resolved, expression, block, line):
        _refuse(
            resolved,
            line,
            f"{cls.__name__} does not declare {name}, so the expression would "
            f"be stored rather than followed",
        )


def _check_once_names(
    resolved: Resolved, block: Block, expression: str, line: int
) -> None:
    """A ``name = ...`` line runs as the widget is built: every bare name in
    it must mean something then.  One the hand-written half declares is not
    seen from markup (``root.sort_mode`` reaches it), and would otherwise be
    a ``NameError`` the first time the component is made."""
    import builtins

    tree = ast.parse(expression, mode="eval")
    local: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            local.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            local.add(node.id)
    known = (
        set(resolved.own(block)) | set(resolved.ids) | set(resolved.namespace)
        | set(dir(builtins)) | {"self", "root", "parent"} | local
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in known:
            _refuse(
                resolved,
                line,
                f"{node.id!r} means nothing here: it is not an id, an import or "
                f"a property this document can see (one the .py half declares "
                f"is reached as root.{node.id})",
            )


def _root_declaration(resolved: Resolved, name: str, cls: type):
    """A root property line may name what the document itself declares."""
    if name in resolved.declared:
        declaration = resolved.declared[name]
        return None if isinstance(declaration, EventDecl) else declaration
    return declared(cls, name)


def _is_binding(
    resolved: Resolved, expression: str, block: Block, line: int
) -> bool:
    return compile_expression(
        expression,
        own=resolved.own(block),
        ids=resolved.ids,
        line=line,
        filename=resolved.filename,
    ).rewritten


# -- what a style block says -------------------------------------------------


def _check_styles(resolved: Resolved) -> None:
    """A ``style:`` block is a stylesheet fragment, checked as one.

    Names go against the same union a ``.nss`` sheet is checked against -- the
    :class:`~navkit.style.Style` fields and whatever widgets have declared --
    and values against the same grammar, while a ``$variable`` is passed over,
    because what it will hold is not knowable until a theme is loaded.
    """
    for block in resolved.document.root.walk():
        if block.style is None:
            continue
        for declaration in block.style.declarations:
            try:
                check_declarations(
                    f"{declaration.name}: {declaration.value}",
                    line=declaration.line,
                    filename=resolved.filename,
                )
            except StylesheetError as error:
                _refuse(resolved, declaration.line, error.message)


# -- what a keys block binds -------------------------------------------------


def _check_keys(resolved: Resolved) -> None:
    """Every binding names a command, and reads nothing but the imports.

    A key table is a class attribute, evaluated once when the generated class
    is made, so there is no instance for ``self``, ``root`` or an id to mean:
    a name the import block did not bind is refused by name here, rather than
    by a ``NameError`` at import.  What remains is evaluated, the way the
    class body will evaluate it, and has to be a command class or an instance
    of one -- the check navkit makes too, only earlier and with a line number.
    """
    table = resolved.document.root.keys
    if table is None:
        return
    for binding in table.bindings:
        value = _class_level(
            resolved,
            binding.command,
            binding.line,
            f"the command for {binding.key!r} failed to evaluate",
            "a key table",
        )
        is_class = isinstance(value, type) and issubclass(value, Command)
        if not is_class and not isinstance(value, Command):
            _refuse(
                resolved,
                binding.line,
                f"{binding.command} is not a Command class or instance, so "
                f"{binding.key!r} would ask for nothing",
            )


# -- what a commands block handles -------------------------------------------


def _check_commands(resolved: Resolved) -> None:
    """Each line names a command class, its handler is not the ``.py``'s too,
    and an ``enables``/``checks`` the ``.py`` overrides asks ``super()``.

    The ``.py`` half is the derived class, so a handler it also defines would
    win without a word, and its ``enables`` returning without ``super()``
    would leave every ``enabled:`` line unasked.
    """
    root = resolved.document.root
    table = root.commands
    if table is None:
        return
    sibling = resolved.sibling
    component = sibling.component(root.type) if sibling else None
    own_handlers = {h.name: h.line for h in root.handlers}
    for handler in table.handlers:
        value = _class_level(
            resolved,
            handler.command,
            handler.line,
            f"the command {handler.command} failed to evaluate",
            "a command",
        )
        if not (isinstance(value, type) and issubclass(value, Command)):
            _refuse(
                resolved,
                handler.line,
                f"{handler.command} is not a Command class: a commands block "
                f"handles a class, as its handler is named for one",
            )
        name = value.handler
        if name in own_handlers:
            _refuse(
                resolved,
                handler.line,
                f"{name} is already a handler line on line {own_handlers[name]}",
            )
        if component is not None and name in component.methods:
            _refuse(
                resolved,
                handler.line,
                f"{sibling.filename} defines {name} too, and the hand-written "
                f"half is the derived class: its method would win",
            )
        _check_handler_body(resolved, handler, True)
    for kind, method in (("enabled", "enables"), ("checked", "checks")):
        if component is None or method not in component.methods:
            continue
        if not any(getattr(h, kind) is not None for h in table.handlers):
            continue
        if not _calls_super(sibling.path, root.type, method):
            line = next(getattr(h, f"{kind}_line") for h in table.handlers
                        if getattr(h, kind) is not None)
            _refuse(
                resolved,
                line,
                f"{sibling.filename}'s {method} never calls super().{method}, "
                f"so this line would never be asked",
            )


def _calls_super(path, class_name: str, method: str) -> bool:
    """Whether *class_name*.*method* in *path* calls ``super().method``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method:
                    return any(
                        isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Attribute)
                        and call.func.attr == method
                        and isinstance(call.func.value, ast.Call)
                        and isinstance(call.func.value.func, ast.Name)
                        and call.func.value.func.id == "super"
                        for call in ast.walk(item)
                    )
    return True


# -- what a handler line lands on --------------------------------------------


def _check_handlers(resolved: Resolved) -> None:
    live = _live_handlers()
    for block in resolved.document.root.walk():
        cls = resolved.class_of(block)
        root = block is resolved.document.root
        for handler in block.handlers:
            _check_handler_name(resolved, block, cls, handler, live, root)
            _check_handler_body(resolved, handler, root)


def _check_handler_name(
    resolved: Resolved, block: Block, cls: type, handler, live, root: bool
) -> None:
    if not root and handler.name in _handlers_of(emitted(cls)):
        pass
    elif handler.name not in live:
        emits = ", ".join(sorted(_handlers_of(emitted(cls)))) or "nothing"
        _refuse(
            resolved,
            handler.line,
            f"nothing raises {handler.name}; {cls.__name__} emits {emits}",
        )
    owner = _implements(resolved, cls, handler.name, root)
    if owner is not None:
        _refuse(
            resolved,
            handler.line,
            f"{owner} already implements {handler.name}, and an assignment "
            f"beats a method; call it from this line instead of replacing it",
        )


def _implements(
    resolved: Resolved, cls: type, name: str, root: bool
) -> str | None:
    """Which class owns *name*, where owning it makes the line a mistake.

    A markup handler is *assigned onto the instance*, and an instance attribute
    is found before a class's method -- so a line landing on a class that
    implements the same hook silently takes it away.  On the root block the
    class in question is the hand-written half, which is parsed rather than
    imported; on a child it is the child's own class, which is live.
    ``Widget``'s own hooks are do-nothing stubs and do not count.
    """
    if root:
        sibling = resolved.sibling
        component = sibling.component(resolved.document.root.type) if sibling else None
        if component is not None and name in component.methods:
            return f"{sibling.filename}'s {component.name}"
        return None
    for klass in cls.__mro__:
        if name in vars(klass):
            return None if klass is Widget else klass.__name__
    return None


def _check_handler_body(resolved: Resolved, handler, root: bool) -> None:
    """A body awaits what the hand-written half spells ``async def``.

    Checked only where the ``def`` is visible in that file: an inherited method
    falls through to a ``TypeError`` at run time, which is the honest limit of
    reading one file without importing it.
    """
    sibling = resolved.sibling
    component = sibling.component(resolved.document.root.type) if sibling else None
    if component is None:
        return
    for name, awaited in _calls(handler.body, root):
        method = component.methods.get(name)
        if method is None:
            continue
        if awaited and not method.is_async:
            _refuse(
                resolved,
                handler.line,
                f"{sibling.filename}'s {name} is not async, so it cannot be "
                f"awaited",
            )
        if not awaited and method.is_async:
            _refuse(
                resolved,
                handler.line,
                f"{sibling.filename}'s {name} is async, so without await this "
                f"line builds a coroutine and drops it",
            )


def _calls(body: str, root: bool) -> Iterator[tuple[str, bool]]:
    """Every ``root.name(...)`` in *body*, and whether it was awaited.

    A call handed straight to ``spawn()`` counts as awaited: the coroutine is
    the task's, which is how a handler starts a dialog without waiting on it.
    """
    reaching = {"root"} | ({"self"} if root else set())
    tree = ast.parse("async def _h(event):\n    " + body)
    awaited = {
        id(node.value) for node in ast.walk(tree) if isinstance(node, ast.Await)
    }
    awaited |= {
        id(argument)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "spawn"
        for argument in node.args
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id in reaching
        ):
            yield function.attr, id(node) in awaited


# -- what the hand-written half says about the document ----------------------


def _check_sibling(resolved: Resolved) -> None:
    sibling = resolved.sibling
    if sibling is None:
        return
    component = sibling.component(resolved.document.root.type)
    _check_events(resolved, sibling)
    if component is None:
        return
    _check_orphans(resolved, sibling, component)
    _check_composed(resolved, component)
    _check_shadowed_reactives(resolved, sibling, component)


def _check_events(resolved: Resolved, sibling) -> None:
    """Which half declares an event follows which half emits it."""
    for declaration in resolved.document.root.declarations:
        if not isinstance(declaration, EventDecl):
            continue
        if declaration.name in sibling.classes:
            _refuse(
                resolved,
                declaration.line,
                f"{declaration.name} is declared in {sibling.filename} too; a "
                f"component declares an event in the half that emits it, and "
                f"never in both",
            )


def _check_orphans(resolved: Resolved, sibling, component) -> None:
    """A composed name in the ``.py`` must name an id the markup still has.

    Renaming an ``id`` would otherwise leave the method behind, wired to
    nothing, and the widget silently dead.
    """
    ids = set(resolved.ids)
    # The document's imports make its events live, but not the hand-written
    # half's: a command the ``.py`` imports to answer -- ``ClipboardCopy``,
    # whose handler ends in ``_copy`` -- is read here, not imported.
    live = _live_handlers() | {
        handler_name(name) for name in sibling.imports if name[:1].isupper()
    }
    for name, method in component.methods.items():
        if name in live or not name.startswith("on_"):
            continue
        for handler in live:
            stem = handler.removeprefix("on_")
            if not name.endswith(f"_{stem}"):
                continue
            target = name[3: -len(stem) - 1]
            if target and target not in ids:
                _refuse(
                    resolved,
                    resolved.document.root.line,
                    f"{sibling.filename}:{method.line} defines {name}, but "
                    f"{target} is not an id in this document",
                )


def _check_composed(resolved: Resolved, component) -> None:
    """A stub's name may not already mean something else."""
    live = _live_handlers()
    taken = set(resolved.ids) | set(resolved.declared)
    for block in _children(resolved.document):
        if block.id is None:
            continue
        cls = resolved.class_of(block)
        for handler in _handlers_of(emitted(cls)):
            composed = f"on_{block.id}_{handler.removeprefix('on_')}"
            if composed in live:
                _refuse(
                    resolved,
                    block.id_line or block.line,
                    f"the stub for this child would be called {composed}, "
                    f"which is already the handler of an event class",
                )
            if composed in taken:
                _refuse(
                    resolved,
                    block.id_line or block.line,
                    f"the stub for this child would be called {composed}, "
                    f"which this document already declares",
                )


def _check_shadowed_reactives(resolved: Resolved, sibling, component) -> None:
    """A ``reactive()`` in the ``.py`` the markup's expressions cannot see.

    The two halves are separate modules with separate globals, so a compiled
    expression resolves such a name as a module global and raises ``NameError``
    at the first read.  Declaring it in the markup is the fix.
    """
    for name, line in component.reactive.items():
        if name in resolved.declared or name in resolved.ids:
            _refuse(
                resolved,
                resolved.document.root.line,
                f"{sibling.filename}:{line} declares {name}, which this "
                f"document declares too",
            )


# -- shared --------------------------------------------------------------


def _children(document: Document) -> Iterator[Block]:
    root = document.root
    for block in root.walk():
        if block is not root:
            yield block


def _handlers_of(events: Iterable[type[Event]]) -> set[str]:
    return {event.handler for event in events}


def _live_handlers() -> set[str]:
    """Every handler name an :class:`~navkit.events.Event` subclass answers to.

    No registry: the classes the document's imports have made live are already
    there, and navkit's own events are in the set for free.  This is the looser
    of the two answers a handler line is checked against, and it has to be --
    an event raised three levels down legitimately reaches an ancestor.
    """
    found = {Event.handler}
    stack = list(Event.__subclasses__())
    while stack:
        event = stack.pop()
        found.add(event.handler)
        stack.extend(event.__subclasses__())
    return found


def _refuse(resolved: Resolved, line: int, message: str) -> None:
    raise MarkupError(message, line, resolved.filename)


__all__ = ["check"]
