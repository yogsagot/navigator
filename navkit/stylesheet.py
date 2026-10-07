"""The stylesheet language and its lookup engine.

A ``.nss`` file is CSS in shape -- selectors, a brace-delimited block of
declarations, a cascade ordered by specificity -- resolving to the
:class:`~navkit.style.Style` values :mod:`navkit.style` defines.  What it is
*not* is CSS in scope: there is no layout here, so every declaration either
names a field of ``Style`` or names a property the widget itself interprets.

:mod:`navkit.DESIGN` records why each of those decisions went the way it did.
The parts worth knowing to read this module:

- **Declarations cascade per property, not per rule.**  Sorting the matching
  rules by ``(specificity, order)`` and updating a dict in that order is the
  whole of it, because a later update overwrites only the keys it carries.
- **Variables are substituted, not looked up.**  They merge across sheets in
  load order and are resolved into the rule values here, so nothing downstream
  ever sees a ``$name``.
- **A part is not a widget.**  ``Panel::row`` styles something a widget paints
  itself; the widget supplies the part's state when it asks, because it is the
  only thing that knows a row is selected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Mapping

from navkit.style import Style

if TYPE_CHECKING:
    from navkit.widget import Widget

#: Every declaration key that ends up inside a :class:`~navkit.style.Style`.
#: Anything else a sheet declares is a widget property -- see
#: :func:`register_property`.  ``link`` is a ``Style`` field and not a
#: declaration: where a cell points is content, which a widget knows and a
#: sheet does not, so it is set while painting and never cascades.
#: ``terminal_palette`` is the same: it says whose colours a child program's
#: cells are, which only the widget showing them knows.
STYLE_FIELDS = frozenset(Style.__dataclass_fields__) - {"link", "terminal_palette"}

#: The sixteen colours :mod:`navkit.style` names, as a sheet spells them.
#: Listed rather than introspected so that a future integer constant in that
#: module cannot quietly become a colour name.
COLOR_NAMES = {
    name.lower(): value
    for name, value in (
        ("BLACK", 0), ("RED", 1), ("GREEN", 2), ("BROWN", 3),
        ("BLUE", 4), ("MAGENTA", 5), ("CYAN", 6), ("LIGHT_GRAY", 7),
        ("DARK_GRAY", 8), ("LIGHT_RED", 9), ("LIGHT_GREEN", 10),
        ("YELLOW", 11), ("LIGHT_BLUE", 12), ("LIGHT_MAGENTA", 13),
        ("LIGHT_CYAN", 14), ("WHITE", 15),
    )
}


class StylesheetError(Exception):
    """A stylesheet could not be read.  Carries the source line."""

    def __init__(self, message: str, line: int, filename: str = "<stylesheet>"):
        super().__init__(f"{filename}:{line}: {message}")
        self.message = message
        self.line = line
        self.filename = filename


@dataclass(frozen=True, slots=True)
class PropertySpec:
    """What a sheet is allowed to *say* about one widget property.

    Not what it means, and not what it falls back to.  A default belongs to the
    widget class that declared it, and two classes may sensibly disagree about
    one -- a dialog framed ``double`` where a plain widget is framed ``single``
    -- while both accept exactly the same four words from a sheet.  This
    registry is global, so it holds only the half every declaration of a key
    has to agree on.

    The type is the default's own rather than a thing separately spelled --
    ``StyleProperty(0)`` takes a number and ``StyleProperty("auto")`` a keyword
    -- which is the inference navml's ``property`` directive already makes from
    its right-hand side.  ``kind`` of ``None`` means nothing was said about the
    type, which is what the bare :func:`register_property` leaves behind.
    """

    kind: type | None = None
    values: frozenset | None = None

    @classmethod
    def of(
        cls, default: Any = None, values: Iterable[Any] | None = None
    ) -> PropertySpec:
        allowed = None if values is None else frozenset(values)
        if allowed is not None and default is not None and default not in allowed:
            raise ValueError(
                f"default {default!r} is not one of the values declared with it"
            )
        return cls(None if default is None else type(default), allowed)

    def __str__(self) -> str:
        if self.values is not None:
            return " | ".join(sorted(str(v) for v in self.values))
        return _kind_named(self.kind) if self.kind is not None else "anything"


#: Declaration keys that are not ``Style`` fields but are still legal, because
#: some widget interprets them.  A widget class declares its own -- see
#: :class:`StyleProperty` -- and the parser checks against this, so a
#: misspelled property fails with a line number instead of being silently
#: dropped the way a CSS typo is.
_PROPERTIES: dict[str, PropertySpec] = {}


def register_property(
    *names: str, default: Any = None, values: Iterable[Any] | None = None
) -> None:
    """Declare *names* as stylable widget properties.

    The spec applies to each name given.  Registration is global because a
    stylesheet is parsed without knowing which widgets it will meet;
    :class:`StyleProperty` is the declared route to it and this is the bare
    one, kept for a property nothing holds an attribute for.

    Registering a name twice agreeably is a no-op, so a module imported twice
    is harmless and a subclass may re-declare a property with a different
    *default* -- which is not part of the spec, for the reason
    :class:`PropertySpec` gives.  Registering it twice with conflicting
    vocabularies raises, because the two would disagree about what a sheet may
    say and the loser would be whichever imported last.
    """
    spec = PropertySpec.of(default, values)
    for name in names:
        existing = _PROPERTIES.get(name)
        if existing is not None and existing != spec:
            raise ValueError(
                f"property {name!r} is already declared as {existing}; "
                f"a second declaration as {spec} would depend on import order"
            )
        _PROPERTIES[name] = spec


def parts_of(cls: type) -> frozenset[str]:
    """Every part *cls* and its bases declare they paint.

    The counterpart of :func:`navkit.events.emitted`, and it **unions over the
    MRO** for the same reason: a subclass that paints a new part is adding to
    what its base paints, never replacing it, so ``ListBox`` keeps its base's
    ``row`` without restating it.

    This is what makes a part name checkable at all.  A ``::part`` selector
    cannot be checked when a sheet is parsed -- selectors match by class
    *name* over the MRO, so the parser has no class to ask, and a sheet may
    legally name a type it could not import.  The check therefore lives where
    the class is in hand: :meth:`navkit.widget.Widget.part_style` refuses a
    part its widget never declared, which fires at the first paint, in the
    widget, naming both.
    """
    found: set[str] = set()
    for klass in cls.__mro__:
        found.update(vars(klass).get("parts", ()))
    return frozenset(found)


def declared_property(name: str) -> PropertySpec | None:
    """What a sheet may say about *name*, or ``None`` if it may not say it.

    The read side of the registry, for anything that has to check a
    declaration without parsing a sheet -- a code generator validating markup
    against the same union the parser uses.
    """
    return _PROPERTIES.get(name)


def check_value(
    key: str, value: Any, line: int = 0, filename: str = "<stylesheet>"
) -> Any:
    """Hold *value* against what the widget declaring *key* said it may be.

    Deliberately a second pass over :func:`parse_value`'s result rather than a
    branch inside it: that function answers ``true``, ``false`` and a digit
    string before it ever reaches the widget-property branch, so a check
    written there would pass ``icons: true`` through untouched.  Checking the
    value it produced covers every form it can produce.
    """
    spec = _PROPERTIES.get(key)
    if spec is None:
        return value
    # `type(...) is' rather than isinstance: bool is a subclass of int, so an
    # int-valued property would otherwise accept `true'.
    if spec.kind is not None and type(value) is not spec.kind:
        raise StylesheetError(
            f"{value!r} is not a valid {key}; expected {_kind_named(spec.kind)}",
            line,
            filename,
        )
    if spec.values is not None and value not in spec.values:
        raise StylesheetError(
            f"{value!r} is not a valid {key}; expected "
            + _listed(sorted(str(v) for v in spec.values)),
            line,
            filename,
        )
    return value


def _kind_named(kind: type) -> str:
    return {bool: "true or false", int: "a number", str: "a keyword"}.get(
        kind, kind.__name__
    )


def _listed(items: list[str]) -> str:
    """``a``, ``a or b``, ``a, b or c`` -- an error message reads better than a repr."""
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " or " + items[-1]


class StyleProperty:
    """A declaration about a widget that :class:`~navkit.style.Style` cannot hold.

    A border character set is the first of them: it produces no SGR sequence
    and is meaningless for the overwhelming majority of cells, so it is an
    input to a drawing operation rather than an appearance a cell can carry --
    see *Widget properties* in ``navkit/DESIGN.md``.  It is still stylable,
    and this is how a widget says so::

        class Panel(Widget):
            icons = StyleProperty("auto", values=("auto", "none"))

    Three facts that were in three places -- the name, in a module-level
    ``register_property`` call; the default, at the read site; the vocabulary,
    implied by whatever the read site compared against -- are one line beside
    the widget that reads them.  The name comes from the attribute, and
    ``__set_name__`` registers it, so a sheet may not name a property no
    widget declares and a widget cannot declare one the parser has not been
    told about.

    The type is the default's own: ``StyleProperty(0)`` takes a number,
    ``StyleProperty(True)`` a flag, ``StyleProperty("auto")`` a keyword, and
    ``values`` narrows that further to a fixed vocabulary.  Both halves are
    then checked where the declaration is read, with its ``.nss`` line.

    Reading is the cascade's answer, so it inherits nothing and changes with
    the sheet; writing raises, because a stylable property is authored in a
    sheet or in ``inline_style`` and nowhere else.
    """

    __slots__ = ("name", "default", "values")

    def __init__(self, default: Any, *, values: Iterable[Any] | None = None):
        self.name = ""
        self.default = default
        self.values = None if values is None else tuple(values)
        PropertySpec.of(default, self.values)  # raises now rather than at __set_name__

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        register_property(name, default=self.default, values=self.values)

    def __get__(self, obj: Any, owner: type | None = None) -> Any:
        if obj is None:
            return self
        return obj.style_property(self.name, self.default)

    def __set__(self, obj: Any, value: Any) -> None:
        raise AttributeError(
            f"{self.name!r} is resolved from the stylesheet and cannot be "
            f"assigned; author it in a sheet, or with "
            f'merge_style("{self.name}: {value}")'
        )


# -- selectors --------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Compound:
    """One compound selector -- ``Panel#left.wide:active::row:selected``.

    Everything before ``::`` constrains the widget, everything after it
    constrains the part, which is why the two sets of classes and states are
    kept apart rather than merged.
    """

    type_name: str | None = None
    name: str | None = None
    classes: frozenset[str] = frozenset()
    states: frozenset[str] = frozenset()
    part: str | None = None
    part_classes: frozenset[str] = frozenset()
    part_states: frozenset[str] = frozenset()
    #: One compound per ``:not(...)`` written before the ``::part``, each
    #: of which must fail to match the widget.
    negated: tuple[Compound, ...] = ()
    #: One per ``:not(...)`` written after it.  These hold classes and states
    #: alone, which are the only things a part carries.
    part_negated: tuple[Compound, ...] = ()

    @property
    def specificity(self) -> tuple[int, int, int]:
        """This compound's share of :attr:`Selector.specificity`.

        A ``:not(x)`` adds what ``x`` would, as CSS counts it: the negation
        itself is free, and ``:not(#left)`` still outranks any number of
        classes.
        """
        names = int(self.name is not None)
        classes = len(self.classes) + len(self.states)
        classes += len(self.part_classes) + len(self.part_states)
        # A part counts as a type, the way CSS counts a pseudo-element.
        types = int(self.type_name is not None) + int(self.part is not None)
        for negation in (*self.negated, *self.part_negated):
            n, c, t = negation.specificity
            names, classes, types = names + n, classes + c, types + t
        return names, classes, types

    @property
    def state_names(self) -> frozenset[str]:
        """The widget states this compound reads, negated ones included."""
        return self.states.union(*(n.states for n in self.negated))

    def matches(self, widget: Widget, request: PartRequest) -> bool:
        if self.part != request.part:
            return False
        if self.type_name is not None and not _is_a(widget, self.type_name):
            return False
        if self.name is not None and getattr(widget, "name", "") != self.name:
            return False
        if not self.classes <= getattr(widget, "classes", frozenset()):
            return False
        if not all(getattr(widget, state, False) for state in self.states):
            return False
        if not self.part_classes <= request.classes:
            return False
        if not self.part_states <= request.states:
            return False
        if any(n.matches(widget, _WIDGET) for n in self.negated):
            return False
        return not any(
            n.part_classes <= request.classes and n.part_states <= request.states
            for n in self.part_negated
        )


@dataclass(frozen=True, slots=True)
class Selector:
    """A compound, optionally qualified by ancestors.

    *ancestors* runs outermost-first and pairs each compound with the
    combinator joining it to what follows -- ``" "`` for a descendant, ``">"``
    for a child.
    """

    subject: Compound
    ancestors: tuple[tuple[Compound, str], ...] = ()

    @property
    def specificity(self) -> tuple[int, int, int]:
        """``(names, classes + states, types)``, compared left to right.

        The columns do not add: one ``#name`` beats any number of classes,
        which is what makes this a tuple rather than a weighted sum.
        """
        names = classes = types = 0
        for compound in (self.subject, *(a for a, _ in self.ancestors)):
            n, c, t = compound.specificity
            names, classes, types = names + n, classes + c, types + t
        return names, classes, types

    def matches(self, widget: Widget, request: PartRequest) -> bool:
        if not self.subject.matches(widget, request):
            return False
        # Ancestors are matched innermost-first against the parent chain; a
        # part constrains only the subject, so they are asked about the widget.
        current = widget.parent
        for compound, combinator in reversed(self.ancestors):
            if combinator == ">":
                if current is None or not compound.matches(current, _WIDGET):
                    return False
                current = current.parent
                continue
            while current is not None and not compound.matches(current, _WIDGET):
                current = current.parent
            if current is None:
                return False
            current = current.parent
        return True


@dataclass(frozen=True, slots=True)
class PartRequest:
    """What is being styled: the widget itself, or one part of it."""

    part: str | None = None
    classes: frozenset[str] = frozenset()
    states: frozenset[str] = frozenset()


#: The widget itself rather than any part of it.
_WIDGET = PartRequest()


def _is_a(widget: Widget, type_name: str) -> bool:
    """True if *widget* is of a class called *type_name*, subclasses included.

    Matched by name rather than by identity, as CSS, Qt and Textual all do.
    Two unrelated classes sharing a name therefore both match, which is the
    accepted cost of a stylesheet being able to name a type it cannot import.
    """
    return any(base.__name__ == type_name for base in type(widget).__mro__)


@dataclass(frozen=True, slots=True)
class Rule:
    """One selector and the declarations it carries, with its source position."""

    selector: Selector
    declarations: Mapping[str, Any]
    order: int
    line: int = 0

    @property
    def sort_key(self) -> tuple[tuple[int, int, int], int]:
        return self.selector.specificity, self.order


# -- the sheet --------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Stylesheet:
    """Parsed rules and the variable table they were resolved against."""

    rules: tuple[Rule, ...] = ()
    variables: Mapping[str, str] = field(default_factory=dict)

    @property
    def state_names(self) -> frozenset[str]:
        """Every widget state any selector in this sheet names.

        Small and bounded by the sheet, which is what lets a caller ask "which
        of these is true right now" cheaply -- see
        :meth:`~navkit.widget.Widget.part_style`, where the answer has to go
        into a cache key because a state appearing only in a part rule never
        changes the widget's own style and so invalidates nothing.
        """
        return frozenset(
            state
            for rule in self.rules
            for compound in (rule.selector.subject, *(a for a, _ in rule.selector.ancestors))
            for state in compound.state_names
        )

    def declarations_for(
        self, widget: Widget, request: PartRequest = _WIDGET
    ) -> dict[str, Any]:
        """Cascade every rule matching *widget* into one set of declarations.

        Per property rather than per rule: a lower-specificity rule still
        supplies whatever the winner did not mention, which falls out of
        updating a dict in ascending order.
        """
        matched = [r for r in self.rules if r.selector.matches(widget, request)]
        matched.sort(key=lambda rule: rule.sort_key)
        declarations: dict[str, Any] = {}
        for rule in matched:
            declarations.update(rule.declarations)
        return declarations


#: A sheet that says nothing, so a widget with no stylesheet still resolves.
EMPTY = Stylesheet()


def appearance(declarations: Mapping[str, Any]) -> dict[str, Any]:
    """The subset of *declarations* a :class:`~navkit.style.Style` can hold."""
    return {k: v for k, v in declarations.items() if k in STYLE_FIELDS}


def properties(declarations: Mapping[str, Any]) -> dict[str, Any]:
    """The subset of *declarations* the widget itself has to interpret."""
    return {k: v for k, v in declarations.items() if k not in STYLE_FIELDS}


# -- parsing ----------------------------------------------------------------

_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_VARIABLE = re.compile(r"\$([A-Za-z_][\w-]*)\s*:\s*([^;{}]*);")
#: A declaration block.  Deliberately *not* ``([^{}]*)\{([^{}]*)\}`` with the
#: selector in front: a pattern starting with an unanchored ``[^{}]*`` gives the
#: engine no literal to seek, so on a sheet that is mostly declarations it
#: retries at every character and scans to the end each time -- quadratic, and
#: about a second on a 17 kB palette sheet.  Seeking ``{`` first is a literal
#: search, and the selector is simply the text since the last block closed.
_BLOCK = re.compile(r"\{([^{}]*)\}")
_HEX = re.compile(r"#([0-9A-Fa-f]{6})\Z")
_KEYWORD = re.compile(r"[A-Za-z_][\w-]*\Z")

#: What ``inherit`` on a ``Style`` field parses to: the declaration is dropped,
#: so the field cascades as if the rule had never named it.  Written by hand
#: it is CSS's keyword; its use is a variable that may hold a value or not --
#: ``bold: $cursor-bold`` with ``$cursor-bold: inherit`` leaves the cursor row
#: bold over a directory, as a rule silent on ``bold`` would.
INHERIT = object()
_RGB = re.compile(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\Z")
_COMPOUND = re.compile(
    r"""
    (?P<type>\*|[A-Za-z_]\w*)?          # Panel, or * for anything
    (?P<rest>(?:\#[\w-]+|\.[\w-]+|::[\w-]+|:not\([^()]*\)|:[\w-]+)*)
    \Z
    """,
    re.X,
)
_PIECE = re.compile(r":not\(([^()]*)\)|(::|[#.:])([\w-]+)")
#: A ``:not(...)`` anywhere in a selector, found before the selector is split
#: into compounds so that what is inside the parentheses can be refused whole.
_NOT = re.compile(r":not\(([^()]*)\)")


def _blank_comments(text: str) -> str:
    """Replace comments with whitespace, keeping every newline in place.

    Line numbers in errors are worth more than the few bytes this wastes.
    """
    return _COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)


def _line_of(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def _parse_negation(text: str, line: int, filename: str) -> Compound:
    """The argument of one ``:not(...)``: a single compound, and a plain one.

    One compound because a combinator inside would have to be matched against
    a chain the negation cannot see, and CSS 3 drew the line in the same
    place.  Several things to exclude are written ``:not(.a):not(.b)``, and
    a nested ``:not`` cannot be read at all, the parentheses being unbalanced
    for :data:`_COMPOUND`.
    """
    if not text:
        raise StylesheetError("':not()' needs a selector", line, filename)
    compound = _parse_compound(text, line, filename)
    if compound.part is not None:
        raise StylesheetError(
            f"':not({text})' names a part; write the part outside it, "
            f"as '::part:not(:state)'",
            line,
            filename,
        )
    return compound


def _parse_compound(text: str, line: int, filename: str) -> Compound:
    match = _COMPOUND.match(text)
    if match is None or (not match.group("type") and not match.group("rest")):
        raise StylesheetError(f"cannot read selector {text!r}", line, filename)

    type_name = match.group("type")
    if type_name == "*":
        type_name = None
    name = part = None
    classes: set[str] = set()
    states: set[str] = set()
    part_classes: set[str] = set()
    part_states: set[str] = set()
    negated: list[Compound] = []
    part_negated: list[Compound] = []

    for argument, sigil, word in _PIECE.findall(match.group("rest")):
        if not sigil:
            inner = _parse_negation(argument, line, filename)
            if part is None:
                negated.append(inner)
                continue
            # After a ``::part`` the negation is about the part, which carries
            # classes and states and nothing else.
            if inner.type_name is not None or inner.name is not None:
                raise StylesheetError(
                    f"':not({argument})' after '::{part}' may only name "
                    f"classes and states",
                    line,
                    filename,
                )
            part_negated.append(
                Compound(part_classes=inner.classes, part_states=inner.states)
            )
        elif sigil == "::":
            if part is not None:
                raise StylesheetError(
                    f"{text!r} names more than one part", line, filename
                )
            part = word
        elif sigil == "#":
            name = word
        elif sigil == ".":
            (part_classes if part else classes).add(word)
        else:
            # After a ``::part`` a state belongs to the part, which is what
            # lets ``Panel:active::row:selected`` say two different things.
            (part_states if part else states).add(word)

    return Compound(
        type_name=type_name,
        name=name,
        classes=frozenset(classes),
        states=frozenset(states),
        part=part,
        part_classes=frozenset(part_classes),
        part_states=frozenset(part_states),
        negated=tuple(negated),
        part_negated=tuple(part_negated),
    )


def _parse_selector(text: str, line: int, filename: str) -> Selector:
    for argument in _NOT.findall(text):
        # Refused here, before the split below would turn ``:not(A > B)``
        # into three compounds and a confusing complaint about the first.
        if ">" in argument or argument != "".join(argument.split()):
            raise StylesheetError(
                f"':not({argument})' takes one compound, with no combinator; "
                f"write ':not(.a):not(.b)' to exclude several",
                line,
                filename,
            )
    tokens = text.replace(">", " > ").split()
    if not tokens:
        raise StylesheetError("empty selector", line, filename)

    compounds: list[Compound] = []
    #: ``joins[i]`` relates ``compounds[i]`` to ``compounds[i + 1]``.  Keeping
    #: it that way round is the whole subtlety: a combinator read from the
    #: source sits *before* the compound that follows it, but matching walks
    #: outwards from the subject and needs to know how each ancestor relates to
    #: what came after it.  Attaching it to the following compound instead
    #: silently turns every ``>`` into a descendant match.
    joins: list[str] = []
    pending: str | None = None
    for token in tokens:
        if token == ">":
            if pending is not None or not compounds:
                raise StylesheetError(
                    f"misplaced '>' in selector {text!r}", line, filename
                )
            pending = ">"
            continue
        if compounds:
            joins.append(pending or " ")
        compounds.append(_parse_compound(token, line, filename))
        pending = None
    if pending is not None:
        raise StylesheetError(f"selector {text!r} ends with '>'", line, filename)

    for compound in compounds[:-1]:
        if compound.part is not None:
            raise StylesheetError(
                "a part may only appear on the last compound of a selector",
                line,
                filename,
            )
    return Selector(
        subject=compounds[-1], ancestors=tuple(zip(compounds[:-1], joins))
    )


def _collect_variables(text: str) -> tuple[dict[str, str], dict[str, int]]:
    """Every ``$name: value;`` in *text*, with the line each was defined on."""
    source = _blank_comments(text)
    raw: dict[str, str] = {}
    lines: dict[str, int] = {}
    for match in _VARIABLE.finditer(source):
        raw[match.group(1)] = match.group(2).strip()
        lines[match.group(1)] = _line_of(source, match.start())
    return raw, lines


def variables_in(text: str) -> dict[str, str]:
    """Every ``$name: value`` *text* defines, as written: a reference to
    another variable is left a reference.  What a palette editor reads a
    sheet of definitions with, to write it back."""
    return _collect_variables(text)[0]


def _resolve_variables(
    raw: Mapping[str, str], filename: str, lines: Mapping[str, int]
) -> dict[str, str]:
    """Chase ``$a: $b`` chains, refusing cycles and undefined names."""
    resolved: dict[str, str] = {}
    for key in raw:
        value, seen = raw[key], {key}
        while value.startswith("$"):
            reference = value[1:]
            if reference in seen:
                raise StylesheetError(
                    f"variable ${key} is defined in terms of itself",
                    lines.get(key, 0),
                    filename,
                )
            if reference not in raw:
                raise StylesheetError(
                    f"undefined variable ${reference}", lines.get(key, 0), filename
                )
            seen.add(reference)
            value = raw[reference]
        resolved[key] = value
    return resolved


def parse_value(
    key: str, text: str, variables: Mapping[str, str], line: int = 0,
    filename: str = "<stylesheet>", *, defer: bool = False,
) -> Any:
    """One declaration value, as the literal it denotes.

    Substitution happens first, so a variable may hold any of the forms below
    -- and by the time this returns, nothing downstream ever sees a ``$name``.

    Unless *defer* is set, which is how something checking a declaration
    *before* any sheet exists asks for the grammar to be read and the variable
    left alone: the reference is returned as it was written, for whatever
    resolves it later.  :func:`check_declarations` is the caller that wants
    this, and it exists for markup -- see *The `style` block* in
    ``navml/DESIGN.md``.
    """
    text = text.strip()
    if text.startswith("$"):
        name = text[1:]
        if defer and name not in variables:
            return text
        if name not in variables:
            raise StylesheetError(f"undefined variable ${name}", line, filename)
        text = variables[name].strip()

    if text in ("true", "false"):
        return text == "true"
    if text.isdigit():
        number = int(text)
        if key in STYLE_FIELDS and number > 255:
            raise StylesheetError(
                f"palette index {number} is above 255", line, filename
            )
        return number

    if key not in STYLE_FIELDS:
        # A widget property.  A bare keyword is its own value here -- what
        # ``single`` *means* belongs to the widget that reads it -- but whether
        # this widget accepts that keyword at all is answered by
        # :func:`check_value` against what the widget declared.
        if _KEYWORD.match(text):
            return text
        raise StylesheetError(f"cannot read value {text!r} for {key}", line, filename)

    if text == "inherit":
        return INHERIT
    if text == "default":
        if key not in ("fg", "bg"):
            raise StylesheetError(
                f"'default' is only meaningful on fg and bg, not {key}; "
                f"a flag turns off with 'false'",
                line,
                filename,
            )
        return None
    if text in COLOR_NAMES:
        return COLOR_NAMES[text]
    if match := _HEX.match(text):
        digits = match.group(1)
        return tuple(int(digits[i : i + 2], 16) for i in (0, 2, 4))
    if match := _RGB.match(text):
        channels = tuple(int(g) for g in match.groups())
        if any(c > 255 for c in channels):
            raise StylesheetError(f"{text!r} has a channel above 255", line, filename)
        return channels
    raise StylesheetError(f"cannot read value {text!r} for {key}", line, filename)


def _parse_declarations(
    body: str, variables: Mapping[str, str], line: int, filename: str,
    *, defer: bool = False,
) -> dict[str, Any]:
    declarations: dict[str, Any] = {}
    for part in body.split(";"):
        if not part.strip():
            continue
        key, separator, value = part.partition(":")
        key = key.strip()
        if not separator:
            raise StylesheetError(
                f"{part.strip()!r} is not a declaration; expected 'property: value'",
                line,
                filename,
            )
        if key not in STYLE_FIELDS and key not in _PROPERTIES:
            raise StylesheetError(
                f"unknown property {key!r}", line, filename
            )
        parsed = parse_value(key, value, variables, line, filename, defer=defer)
        if parsed is INHERIT:
            continue
        if defer and isinstance(parsed, str) and parsed.startswith("$"):
            # An unresolved reference: what it will hold is not knowable yet,
            # so there is nothing to hold against the vocabulary.  The key was
            # checked above, which is the half that does not need a sheet.
            declarations[key] = parsed
            continue
        declarations[key] = check_value(key, parsed, line, filename)
    return declarations


def parse(text: str, *, filename: str = "<stylesheet>", order: int = 0) -> Stylesheet:
    """Read one sheet.

    *order* offsets the rule numbering so several sheets keep their load order
    when merged -- which is what makes a theme sheet loaded last win a tie
    without needing to out-specify anything.
    """
    raw, lines = _collect_variables(text)
    return _parse_with(text, filename, _resolve_variables(raw, filename, lines), order)


def load(sheets: Iterable[tuple[str, str]]) -> Stylesheet:
    """Merge several sheets, given as ``(filename, text)`` pairs, in load order.

    Variables merge with later definitions winning, and are then resolved for
    every sheet at once -- so a theme may redefine a name the default sheet's
    rules use.  Rule order continues across sheets, which is what the tie-break
    rests on.
    """
    texts = list(sheets)

    raw: dict[str, str] = {}
    lines: dict[str, int] = {}
    for _, text in texts:
        found, found_lines = _collect_variables(text)
        raw.update(found)               # later sheets win, which is the theme
        lines.update(found_lines)
    merged = _resolve_variables(raw, texts[-1][0] if texts else "<stylesheet>", lines)

    rules: list[Rule] = []
    for filename, text in texts:
        sheet = _parse_with(text, filename, merged, len(rules))
        rules.extend(sheet.rules)
    return Stylesheet(tuple(rules), merged)


def read(*sources: str | Path | tuple[str, str]) -> Stylesheet:
    """Load sheets from disk, in order, and merge them.

    A source is a path to a ``.nss`` file, or a ``(name, text)`` pair for one
    that is not on disk.  Order is load order, so the theming story is just
    ``read(default_path, user_theme_path)``: the later file redefines the
    variables the earlier one's rules use, and wins any tie without having to
    out-specify anything.
    """
    sheets: list[tuple[str, str]] = []
    for source in sources:
        if isinstance(source, tuple):
            sheets.append(source)
            continue
        path = Path(source)
        try:
            sheets.append((str(path), path.read_text(encoding="utf-8")))
        except OSError as exc:
            raise StylesheetError(
                f"cannot read {path}: {exc.strerror or exc}", 0, str(path)
            ) from exc
    return load(sheets)


def _split_group(selectors: str, line: int, filename: str) -> list[str]:
    """A selector list, split on the commas that are not inside ``:not(...)``.

    A comma inside is refused rather than supported: ``:not(.a, .b)`` is CSS 4,
    and ``:not(.a):not(.b)`` already says it.
    """
    pieces, depth, start = [], 0, 0
    for index, char in enumerate(selectors):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == ",":
            if depth:
                raise StylesheetError(
                    "':not()' takes one compound; write ':not(.a):not(.b)' "
                    "to exclude several",
                    line,
                    filename,
                )
            pieces.append(selectors[start:index])
            start = index + 1
    pieces.append(selectors[start:])
    return pieces


def _parse_with(
    text: str, filename: str, variables: Mapping[str, str], order: int
) -> Stylesheet:
    """:func:`parse`, but against an already-merged variable table."""
    source = _VARIABLE.sub(
        lambda m: re.sub(r"[^\n]", " ", m.group()), _blank_comments(text)
    )
    rules: list[Rule] = []
    consumed = 0
    for match in _BLOCK.finditer(source):
        # Everything since the previous block closed is this block's selector
        # list.  A stray brace therefore lands in the selector rather than in a
        # check of its own, and `_parse_selector' rejects it with the line.
        selectors = source[consumed : match.start()]
        consumed = match.end()
        line = _line_of(source, match.start(1))
        declarations = _parse_declarations(match.group(1), variables, line, filename)
        for piece in _split_group(selectors, line, filename):
            if not piece.strip():
                raise StylesheetError("empty selector in a group", line, filename)
            rules.append(
                Rule(
                    _parse_selector(piece.strip(), line, filename),
                    declarations,
                    order + len(rules),
                    line,
                )
            )
    if source[consumed:].strip():
        raise StylesheetError(
            f"stray text {source[consumed:].strip()!r} outside a rule",
            _line_of(source, consumed),
            filename,
        )
    return Stylesheet(tuple(rules), variables)


def parse_declarations(
    text: str | Mapping[str, Any] | None, variables: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """An inline declaration set -- ``"bg: red"`` -- as a mapping.

    Accepts a mapping unchanged, which is what :meth:`Widget.merge_style`
    stores: merging two strings by concatenating them would grow without bound.

    A whole :class:`~navkit.style.Style` is accepted too, and becomes the seven
    declarations it actually makes.  That it then overrides all seven is not a
    special case -- it is what stating all seven means.
    """
    if text is None:
        return {}
    if isinstance(text, Style):
        return {name: getattr(text, name) for name in STYLE_FIELDS}
    if isinstance(text, Mapping):
        return dict(text)
    return _parse_declarations(text, variables or {}, 0, "<inline style>")


def check_declarations(
    text: str, *, line: int = 0, filename: str = "<declarations>"
) -> None:
    """Read a declaration set for its grammar alone, resolving no variable.

    What a code generator asks before any sheet has been loaded: every
    property name is held against the same union :func:`parse` checks -- the
    ``Style`` fields and whatever widgets have declared -- and every literal
    value against the same grammar, while a ``$name`` is passed over because
    what it will hold is not knowable yet.  Raises
    :class:`StylesheetError` naming *filename* and *line*, which is the half
    :func:`parse_declarations` cannot do: it is for an inline string arriving
    at run time and has no position to give.

    Returns nothing.  The declarations it produces would be half-resolved, and
    a caller that wanted them would have to know which half.
    """
    _parse_declarations(text, {}, line, filename, defer=True)
