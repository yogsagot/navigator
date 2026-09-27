"""What every layout container has in common: it places its children.

Every container in the tree used to place its children by arithmetic in the
markup -- ``width: parent.width // 2`` beside ``x: parent.width // 2``, a
``button_row`` property centring buttons eleven columns at a time.  A layout
says *how* the children are arranged instead, and works the numbers out itself.

**A child says how much room it wants with a style hint**, read off the child
by the layout it sits in -- CSS's ``flex-grow`` and ``flex-basis``, not a
list of track sizes on the container::

    HorizontalLayout:
        Label:
            style:
                basis: 12
                grow: 0
        InputLine:

``basis`` is the cells a child asks for along the layout's axis, ``grow`` its
weight in whatever is left over, and ``grow`` defaults to 1, so a child that
says nothing shares the space equally with its siblings.  The two are
:class:`~navkit.stylesheet.StyleProperty` declarations, and that bends the
rule a sheet otherwise keeps -- a declaration names a property *the widget
it lands on* interprets -- because here the child carries it and the parent
reads it.  It was taken over an attached-property mechanism navkit does not
have, and over tracks on the container, because it is the one spelling in
which a sheet rule (``Dialog Button { basis: 11; grow: 0 }``) can say it for a
whole class of children at once.

**Arranging is an effect, not the ``layout()`` cascade.**  A markup parent
does not cascade :meth:`~navkit.widget.Widget.layout`, so a resize reaches a
layout as a changed ``width`` and never as a call -- the reason
:class:`~navml.widgets.desktop.Desktop` re-fits its windows from an effect.
The effect reads the layout's size, its own knobs, and every child's
``visible`` and hints, so restyling a child or hiding one re-arranges the
rest with nobody asking.  The children list is not reactive, so :meth:`add`
and :meth:`remove` ask by hand.

**The geometry a layout assigns is navigated, in the sense `navml/DESIGN.md`
gives the word**: the layout writes it on every pass, so a child's markup must
not bind it.  A side that carries a binding anyway is stepped around, the way
``Widget.layout()`` steps around one, which is also what lets a child keep a
bound size across the layout's cross axis.  **A hidden child gets no slot**,
and no spacing either, and its geometry is left as it was.

Read *Layouts* in ``navml/DESIGN.md`` for the rest.
"""

from __future__ import annotations

from typing import Any, Iterable

from navkit.reactive import effect, is_bound, reactive, untracked
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget

from navml.component import take_declared

#: One child's rectangle, in the layout's coordinates.
Rect = tuple[int, int, int, int]

#: Where a linear layout puts its children when none of them grows.
JUSTIFY = ("start", "center", "end")


def distribute(
    total: int, bases: Iterable[int], grows: Iterable[int], spacing: int = 0
) -> list[int]:
    """Share *total* cells between children asking for *bases* and *grows*.

    The bases are granted first, in order, and a child that no longer fits is
    clamped -- later children shrink to nothing rather than earlier ones being
    squeezed.  What is left is split by ``grow`` weight in floor shares, and
    the cells the floors lose go one each to the **trailing** growing
    children, which is exactly ``W // 2`` and ``W - W // 2`` for two equal
    ones: the arithmetic the file manager's panels were written in.
    """
    bases, grows = list(bases), list(grows)
    remaining = max(0, total - max(0, spacing) * max(0, len(bases) - 1))
    sizes = []
    for base in bases:
        size = min(max(0, base), remaining)
        sizes.append(size)
        remaining -= size
    weight = sum(max(0, grow) for grow in grows)
    if weight and remaining:
        shares = [remaining * max(0, grow) // weight for grow in grows]
        left = remaining - sum(shares)
        for index in reversed(range(len(grows))):
            if not left:
                break
            if grows[index] > 0:
                shares[index] += 1
                left -= 1
        sizes = [size + share for size, share in zip(sizes, shares)]
    return sizes


class Layout(Widget):
    """A container that places its children, and paints nothing itself."""

    #: The cells a child asks for along its layout's axis -- and a docked
    #: child's thickness.  Read off the *child*.
    basis = StyleProperty(0)

    #: A child's weight in the space its layout has left once every basis is
    #: granted.  Read off the *child*; 0 keeps it at its basis.
    grow = StyleProperty(1)

    def __init__(self, **kwargs: Any) -> None:
        # ``HorizontalLayout(spacing=2)`` as ``Button(text="OK")`` -- the
        # constructor a markup-built neighbour has.
        take_declared(self, kwargs)
        super().__init__(**kwargs)

    def mounted(self) -> None:
        super().mounted()
        effect(self, Layout.arrange)

    def layout(self, width: int, height: int) -> None:
        """Size this widget as any widget is sized, then place the children.

        Called only by a parent that cascades, and by ``Widget.add``; under a
        markup parent the effect in :meth:`mounted` is what keeps up.
        """
        if not is_bound(self, Widget.width):
            self.width = width
        if not is_bound(self, Widget.height):
            self.height = height
        self.arrange()

    def add(self, child: Widget) -> Widget:
        super().add(child)
        if self.is_mounted:
            self.arrange()
        return child

    def remove(self, child: Widget) -> None:
        super().remove(child)
        if self.is_mounted:
            self.arrange()

    def arrange(self) -> None:
        """Work out every visible child's rectangle, then assign them.

        The plan is made with tracking on -- that is what the effect depends
        on -- and applied without it, so that the layout does not come to
        depend on the children's geometry it is writing.
        """
        plan = self.plan([child for child in self.children if child.visible])
        with untracked():
            for child, (x, y, width, height) in plan.items():
                if not is_bound(child, Widget.x):
                    child.x = x
                if not is_bound(child, Widget.y):
                    child.y = y
                child.layout(max(0, width), max(0, height))

    def plan(self, children: list[Widget]) -> dict[Widget, Rect]:
        """The rectangle each of *children* gets; the one thing a layout says.

        *children* are the visible ones, in order.  A child left out of the
        answer is left alone.
        """
        return {}

    def render(self, surface: Surface) -> None:
        """Nothing: whatever is behind a layout shows between its children."""


class LinearLayout(Layout):
    """Children one after another along an axis, filling the other one.

    The base :class:`~navml.widgets.layout.horizontal_layout.HorizontalLayout` and
    :class:`~navml.widgets.layout.vertical_layout.VerticalLayout` share; they differ
    only in :attr:`horizontal`.
    """

    #: Which axis the children follow.  A class constant, not a knob.
    horizontal = True

    #: Empty cells between two visible children.
    spacing: int = reactive(0)

    #: ``start``, ``center`` or ``end``: where the children sit when they do
    #: not fill the axis, which is only ever when none of them grows.
    justify: str = reactive("start")

    def plan(self, children: list[Widget]) -> dict[Widget, Rect]:
        if self.justify not in JUSTIFY:
            raise ValueError(
                f"justify is {self.justify!r}; it takes {', '.join(JUSTIFY)}"
            )
        along = self.width if self.horizontal else self.height
        across = self.height if self.horizontal else self.width
        spacing = max(0, self.spacing)
        sizes = distribute(
            along,
            (child.style_property("basis", 0) for child in children),
            (child.style_property("grow", 1) for child in children),
            spacing,
        )
        used = sum(sizes) + spacing * max(0, len(sizes) - 1)
        free = max(0, along - used)
        position = {"start": 0, "center": free // 2, "end": free}[self.justify]
        plan = {}
        for child, size in zip(children, sizes):
            if self.horizontal:
                plan[child] = (position, 0, size, across)
            else:
                plan[child] = (0, position, across, size)
            position += size + spacing
        return plan
