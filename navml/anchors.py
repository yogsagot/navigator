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

``fill: N`` is all four insets at once; a named edge wins over it.  Every
position and size is clamped at 0, which is the ``max(0, ...)`` the
hand-written lines carry.  Read *Anchors* in ``navml/DESIGN.md`` for why the
design is this and not QML's.
"""

from __future__ import annotations

from dataclasses import replace

from navml.errors import MarkupError
from navml.parser import AnchorBlock, AnchorDeclaration, Block, Property

#: The two axes: the start edges, the end edges, the sibling forms of each,
#: the position and size properties, and the parent's extent.
_AXES = (
    ("horizontal", "left", "right", "after", "before", "x", "width"),
    ("vertical", "top", "bottom", "below", "above", "y", "height"),
)


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
        if declaration.target is not None and declaration.target not in siblings:
            where = (
                "the root block has no siblings" if parent is None
                else f"{declaration.target!r} is not an id beside this widget "
                     f"under the same parent"
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
        starts = [named[k] for k in (start, after) if k in named]
        ends = [named[k] for k in (end, before) if k in named]
        for pair in (starts, ends):
            if len(pair) == 2:
                raise MarkupError(
                    f"{pair[0].name} and {pair[1].name} are both one edge; "
                    f"a widget's edge sits one place",
                    pair[1].line,
                    filename,
                )
        first = starts[0] if starts else None
        last = ends[0] if ends else None
        if fill is not None:
            if centred:
                raise MarkupError(
                    f"center {centre.value} and fill both place the widget "  # type: ignore[union-attr]
                    f"{axis}ly; say one",
                    fill.line,
                    filename,
                )
            first = first or AnchorDeclaration(start, fill.value, fill.line)
            last = last or AnchorDeclaration(end, fill.value, fill.line)
        if centred and (first or last):
            raise MarkupError(
                f"center {centre.value} and {(first or last).name} both place "  # type: ignore[union-attr]
                f"the widget {axis}ly; say one",
                (first or last).line,  # type: ignore[union-attr]
                filename,
            )
        if not (centred or first or last):
            continue
        anchor = centre if centred else (first or last)
        if position in written:
            raise MarkupError(
                f"{position} is written on line {written[position].line} and "
                f"anchored here; say one",
                anchor.line,  # type: ignore[union-attr]
                filename,
            )
        if first and last and size in written:
            raise MarkupError(
                f"{first.name} and {last.name} stretch the widget, and "
                f"{size} is written on line {written[size].line}; say one",
                last.line,
                filename,
            )
        line = anchor.line  # type: ignore[union-attr]
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
                position, f"max(0, {end_at} - self.{size})", last.line
            ))
        elif first.target is None:
            if last.target is None and _is_int(first.value) and _is_int(last.value):
                # ``left: 2`` and ``right: 2`` read as the line they replace,
                # ``max(0, parent.width - 4)``.
                inset = str(int(first.value) + int(last.value))
                end_at = _minus(f"parent.{size}", inset)
            else:
                end_at = _minus(end_at, first.value)
            out.append(Property(size, f"max(0, {end_at})", last.line))
        else:
            out.append(Property(
                size, f"max(0, {end_at} - self.{position})", last.line
            ))
    return tuple(out)


def _start(anchor: AnchorDeclaration, position: str, size: str) -> str:
    """Where the start edge sits, in the parent's coordinates."""
    if anchor.target is None:
        return anchor.value
    edge = f"{anchor.target}.{position} + {anchor.target}.{size}"
    return edge if _is_zero(anchor.value) else f"{edge} + {_operand(anchor.value)}"


def _end(anchor: AnchorDeclaration, position: str, size: str) -> str:
    """Where the end edge sits: the first cell past the widget."""
    if anchor.target is not None:
        return _minus(f"{anchor.target}.{position}", anchor.value)
    return _minus(f"parent.{size}", anchor.value)


def _minus(base: str, value: str) -> str:
    """``base - (value)``, or *base* alone when the value is a literal 0."""
    return base if _is_zero(value) else f"{base} - {_operand(value)}"


def _is_zero(value: str) -> bool:
    return value.strip() == "0"


def _is_int(value: str) -> bool:
    return value.strip().isdigit()


def _operand(value: str) -> str:
    """*value* as the right of a ``-``: bracketed unless it is one token."""
    value = value.strip()
    return value if _is_int(value) or value.isidentifier() else f"({value})"


__all__ = ["expand"]
