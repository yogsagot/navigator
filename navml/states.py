"""``when COND:`` -- a widget's lines that differ while a condition holds.

QML's *States*, kept to what a document needs: a page that reflows when it is
narrow, a row that moves when a mode is on.  A ``when`` block holds property
lines and an ``anchors:`` block, and while its condition holds the widget is
as if those lines replaced its own::

    StaticText:
        x: 35
        y: 12
        when parent.width < 67:
            x: 30
            y: 13

    Button:
        width: 10
        anchors:
            right: 47
            bottom: 1
        when parent.width < 82:
            anchors:
                right: 25
                bottom: 3

A property line replaces the widget's line of that name.  An anchor line
replaces the widget's anchors **on the sides it names** -- ``left``/``after``
the horizontal start, ``right``/``before`` its end, ``top``/``below`` and
``bottom``/``above`` likewise, ``center`` both sides of its axis; ``fill``
stays the default for any side the block leaves alone, as it is for the
widget's own edges.

It is sugar, as anchors are, and done in the same pass before the generator
sees the document: the widget as written and each variant are expanded alike
(so every anchor rule holds for every variant), and a line whose expression
differs becomes ``(variant) if (COND) else (as written)`` -- the first block
whose condition holds winning, in document order.  A variant may not give a
property the widget otherwise has no line for: there would be nothing to fall
back on while the condition is false.
"""

from __future__ import annotations

from dataclasses import replace

from navml.anchors import _properties as _anchored
from navml.errors import MarkupError
from navml.parser import AnchorBlock, AnchorDeclaration, Block, Property, WhenBlock

#: The sides each anchor key places.
_SIDES = {
    "left": {"hs"}, "after": {"hs"},
    "right": {"he"}, "before": {"he"},
    "top": {"vs"}, "below": {"vs"},
    "bottom": {"ve"}, "above": {"ve"},
}
_AXIS = {"horizontal": {"hs", "he"}, "vertical": {"vs", "ve"}, "both": {"hs", "he", "vs", "ve"}}


def expand(root: Block, filename: str) -> Block:
    """*root* with every ``anchors:`` and ``when`` block in it turned into property lines."""
    return _expand(root, None, filename)


def _expand(block: Block, parent: Block | None, filename: str) -> Block:
    children = tuple(_expand(child, block, filename) for child in block.children)
    properties = block.properties
    if block.anchors is not None or block.whens:
        properties = _lines(block, parent, filename)
    if children == block.children and properties is block.properties:
        return block
    return replace(block, children=children, properties=properties)


def _lines(block: Block, parent: Block | None, filename: str) -> tuple[Property, ...]:
    """The widget's property lines with its anchors and ``when`` blocks folded in."""
    base = _expanded(block, parent, filename)
    if not block.whens:
        return tuple(base.values())
    variants = []
    for when in block.whens:
        variant = _variant(block, when)
        lines = _expanded(variant, parent, filename)
        for name, line in lines.items():
            if base.get(name) is not None and base[name].once and line is not base[name]:
                raise MarkupError(
                    f"{name} is set once ('{name} = ...'), so nothing would follow "
                    f"'{when.condition}': write the widget's line as '{name}: ...'",
                    _line_of(when, name, line),
                    filename,
                )
            if name not in base:
                raise MarkupError(
                    f"this when block gives {name} a value the widget has no line for "
                    f"otherwise: there would be nothing while '{when.condition}' is false",
                    _line_of(when, name, line),
                    filename,
                )
        variants.append((when, lines))
    out = []
    for name, line in base.items():
        expression = line.expression
        for when, lines in reversed(variants):
            if name not in lines:
                continue  # the variant writes nothing there: the widget's own line stands
            other = lines[name].expression
            if other != expression:
                expression = f"({other}) if ({when.condition}) else ({expression})"
        out.append(line if expression == line.expression else replace(line, expression=expression))
    return tuple(out)


def _expanded(block: Block, parent: Block | None, filename: str) -> dict[str, Property]:
    """The widget's own lines and what its anchors write, by property name."""
    lines = {p.name: p for p in block.properties}
    if block.anchors is not None:
        for line in _anchored(block, parent, filename):
            lines[line.name] = line
    return lines


def _variant(block: Block, when: WhenBlock) -> Block:
    """*block* with *when*'s lines put in place of its own."""
    properties = {p.name: p for p in block.properties}
    for line in when.properties:
        properties[line.name] = line
    return replace(
        block,
        properties=tuple(properties.values()),
        anchors=_merged(block.anchors, when.anchors),
        whens=(),
    )


def _merged(own: AnchorBlock | None, when: AnchorBlock | None) -> AnchorBlock | None:
    """*own* anchors with *when*'s in place of them on every side *when* names."""
    if when is None:
        return own
    if own is None:
        return when
    taken: set[str] = set()
    for declaration in when.declarations:
        taken |= _sides(declaration)
    kept: list[AnchorDeclaration] = []
    for declaration in own.declarations:
        if declaration.name == "fill":
            # The default for whatever side nothing names: still so, unless the
            # block brings a fill of its own.
            if not any(d.name == "fill" for d in when.declarations):
                kept.append(declaration)
            continue
        if declaration.name == "center":
            # Centring is the whole axis: an edge the block names on either
            # side of it takes the axis away.
            axes = [axis for axis in ("horizontal", "vertical")
                    if _AXIS[axis] <= _AXIS[declaration.value] and not _AXIS[axis] & taken]
            if len(axes) == 2:
                kept.append(declaration)
            elif axes:
                kept.append(replace(declaration, value=axes[0]))
            continue
        if not _sides(declaration) & taken:
            kept.append(declaration)
    return AnchorBlock(tuple(kept) + when.declarations, own.line)


def _sides(declaration: AnchorDeclaration) -> set[str]:
    if declaration.name == "center":
        return set(_AXIS[declaration.value])
    if declaration.name == "fill":
        return set()  # a default, never a replacement
    return set(_SIDES[declaration.name])


def _line_of(when: WhenBlock, name: str, line: Property) -> int:
    for own in when.properties:
        if own.name == name:
            return own.line
    return line.line if line.line >= when.line else when.line


__all__ = ["expand"]
