"""``anchors:`` -- where a widget sits, said as edges rather than arithmetic.

A block's ``anchors:`` lines are turned into the ``x``/``y``/``width``/
``height`` property lines that would otherwise be written by hand, before the
generator sees the document.  It is sugar and nothing more: the generated code
is the same bindings as ``x: max(0, parent.width - 12)``, so nothing at run
time knows anchors exist, and every rule a property line keeps -- the names an
expression may read, translation, stubs -- holds for these too::

    Button:
        width: 11
        anchors:
            right: 2        # x: max(0, parent.width - 2 - self.width)
            bottom: 3       # y: max(0, parent.height - 3 - self.height)

Per axis (horizontal; vertical is the same with ``top``/``bottom``/
``below``/``above`` and ``y``/``height``):

* a **start** edge, ``left: L`` (inset from the parent's left) or
  ``after: id + gap`` (that many cells past a sibling's right edge), sets
  ``x``;
* an **end** edge, ``right: R`` (inset from the parent's right) or
  ``before: id + gap``, alone pins the widget's own width against it;
* both stretch it between them: ``x`` from the start, ``width`` the rest;
* ``center: horizontal`` (``vertical``, ``both``) centres it, clamped at 0,
  with the very text :class:`~navml.widgets.dialog.modal.Modal` binds.

**A sibling form may name several ids, and take a parent edge as fallback.**
``before: macro_mark, clock + 1`` sits against the first of them that is
*shown* -- visible, and not empty along the axis -- and ``right: 0`` beside it
says where to sit when none is.  Without a fallback the last id is sat against
whatever it shows; a single id with no fallback is the plain, unconditional
form.

``fill: N`` is all four insets at once; a named edge wins over it.  Every
position and size is clamped at 0, which is the ``max(0, ...)`` the
hand-written lines carry.  Read *Anchors* in ``navml/DESIGN.md`` for why the
design is this and not QML's.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from navml.errors import MarkupError
from navml.parser import AnchorBlock, AnchorDeclaration, Block, Property

#: The two axes: the start edges, the end edges, the sibling forms of each,
#: the position and size properties, and the parent's extent.
_AXES = (
    ("horizontal", "left", "right", "after", "before", "x", "width"),
    ("vertical", "top", "bottom", "below", "above", "y", "height"),
)


@dataclass(frozen=True, slots=True)
class _Side:
    """One side of one axis: a sibling form, a parent edge, or both."""

    sibling: AnchorDeclaration | None
    parent: AnchorDeclaration | None

    @property
    def line(self) -> int:
        return (self.sibling or self.parent).line  # type: ignore[union-attr]

    @property
    def name(self) -> str:
        return (self.sibling or self.parent).name  # type: ignore[union-attr]

    @property
    def literal(self) -> str | None:
        """The parent inset, when this side is nothing but an integer one."""
        if self.sibling is None and self.parent is not None and _is_int(self.parent.value):
            return self.parent.value.strip()
        return None


def expand(root: Block, filename: str) -> Block:
    """*root* with every ``anchors:`` block in it turned into property lines."""
    return _expand(root, None, filename)


def _expand(block: Block, parent: Block | None, filename: str) -> Block:
    children = tuple(_expand(child, block, filename) for child in block.children)
    properties = block.properties
    if block.anchors is not None:
        properties = properties + _properties(block, parent, filename)
    if children == block.children and properties is block.properties:
        return block
    return replace(block, children=children, properties=properties)


def _properties(block: Block, parent: Block | None, filename: str
                ) -> tuple[Property, ...]:
    anchors: AnchorBlock = block.anchors  # type: ignore[assignment]
    named = {d.name: d for d in anchors.declarations}
    written = {p.name: p for p in block.properties}
    siblings = {
        child.id for child in (parent.children if parent is not None else ())
        if child.id is not None and child is not block
    }
    for declaration in anchors.declarations:
        for target in declaration.targets:
            if target in siblings:
                continue
            where = (
                "the root block has no siblings" if parent is None
                else f"{target!r} is not an id beside this widget under the "
                     f"same parent"
            )
            raise MarkupError(
                f"{declaration.name} anchors to a sibling, and {where}: its "
                f"coordinates would be another widget's",
                declaration.line,
                filename,
            )
    centre = named.get("center")
    fill = named.get("fill")
    out: list[Property] = []
    for axis, start, end, after, before, position, size in _AXES:
        centred = centre is not None and centre.value in (axis, "both")
        first = _side(named.get(after), named.get(start))
        last = _side(named.get(before), named.get(end))
        if fill is not None:
            if centred:
                raise MarkupError(
                    f"center {centre.value} and fill both place the widget "  # type: ignore[union-attr]
                    f"{axis}ly; say one",
                    fill.line,
                    filename,
                )
            first = first or _Side(None, AnchorDeclaration(start, fill.value, fill.line))
            last = last or _Side(None, AnchorDeclaration(end, fill.value, fill.line))
        if centred and (first or last):
            side = first or last
            raise MarkupError(
                f"center {centre.value} and {side.name} both place "  # type: ignore[union-attr]
                f"the widget {axis}ly; say one",
                side.line,  # type: ignore[union-attr]
                filename,
            )
        if not (centred or first or last):
            continue
        line = centre.line if centred else (first or last).line  # type: ignore[union-attr]
        if (position in written and not centred and first is None
                and last is not None and size not in written):
            # A start no edge can say (``x: menu.item_span(...)[0] + 1``),
            # written, stretched to an anchored end.
            end_at = _end(last, position, size)
            out.append(Property(
                size, f"max(0, {_minus(_wrap(end_at), f'self.{position}')})", last.line
            ))
            continue
        if position in written:
            raise MarkupError(
                f"{position} is written on line {written[position].line} and "
                f"anchored here; say one",
                line,
                filename,
            )
        if first and last and size in written:
            raise MarkupError(
                f"{first.name} and {last.name} stretch the widget, and "
                f"{size} is written on line {written[size].line}; say one",
                last.line,
                filename,
            )
        if centred:
            out.append(Property(
                position,
                f"max(0, (parent.{size} - self.{size}) // 2)",
                line,
            ))
            continue
        if first is not None:
            out.append(Property(position, _start(first, position, size), first.line))
        if last is None:
            continue
        end_at = _end(last, position, size)
        if first is None:
            out.append(Property(
                position, f"max(0, {_minus(_wrap(end_at), f'self.{size}')})", last.line
            ))
        elif first.literal is not None:
            if last.literal is not None:
                # ``left: 2`` and ``right: 2`` read as the line they replace,
                # ``max(0, parent.width - 4)``.
                inset = str(int(first.literal) + int(last.literal))
                end_at = _minus(f"parent.{size}", inset)
            else:
                end_at = _minus(_wrap(end_at), first.literal)
            out.append(Property(size, f"max(0, {end_at})", last.line))
        else:
            out.append(Property(
                size, f"max(0, {_minus(_wrap(end_at), f'self.{position}')})", last.line
            ))
    return tuple(out)


def _side(sibling: AnchorDeclaration | None, parent: AnchorDeclaration | None
          ) -> _Side | None:
    if sibling is None and parent is None:
        return None
    return _Side(sibling, parent)


def _start(side: _Side, position: str, size: str) -> str:
    """Where the start edge sits, in the parent's coordinates."""
    fallback = side.parent.value if side.parent is not None else None
    if side.sibling is None:
        return fallback  # type: ignore[return-value]

    def edge(target: str) -> str:
        at = f"{target}.{position} + {target}.{size}"
        gap = side.sibling.value  # type: ignore[union-attr]
        return at if _is_zero(gap) else f"{at} + {_operand(gap)}"

    return _chain(side.sibling.targets, edge, size, fallback)


def _end(side: _Side, position: str, size: str) -> str:
    """Where the end edge sits: the first cell past the widget."""
    fallback = (
        _minus(f"parent.{size}", side.parent.value) if side.parent is not None else None
    )
    if side.sibling is None:
        return fallback  # type: ignore[return-value]
    gap = side.sibling.value
    return _chain(
        side.sibling.targets, lambda t: _minus(f"{t}.{position}", gap), size, fallback
    )


def _chain(targets: tuple[str, ...], edge, size: str, fallback: str | None) -> str:
    """The first shown target's edge, else the next's, else *fallback*.

    With no fallback the last target is sat against unconditionally, which
    keeps a lone ``after: label`` the plain ``label.x + label.width``.
    """
    if fallback is None:
        targets, result = targets[:-1], edge(targets[-1])
    else:
        result = fallback
    for target in reversed(targets):
        result = f"{edge(target)} if {target}.visible and {target}.{size} else {result}"
    return result


def _wrap(expression: str) -> str:
    """*expression* bracketed when it is a conditional, so it can be an operand."""
    return f"({expression})" if " if " in expression else expression


def _minus(base: str, value: str) -> str:
    """``base - value``, or *base* alone when the value is a literal 0."""
    return base if _is_zero(value) else f"{base} - {_operand(value)}"


def _is_zero(value: str) -> bool:
    return value.strip() == "0"


def _is_int(value: str) -> bool:
    return value.strip().isdigit()


def _operand(value: str) -> str:
    """*value* as the right of a ``-``: bracketed unless it is one token."""
    value = value.strip()
    return value if _is_int(value) or value.isidentifier() or _dotted(value) else f"({value})"


def _dotted(value: str) -> bool:
    return all(part.isidentifier() for part in value.split("."))


__all__ = ["expand"]
