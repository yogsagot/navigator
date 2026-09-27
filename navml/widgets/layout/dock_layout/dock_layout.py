"""Children docked against the edges, and the rest of the area filled.

Each child says where with its ``dock`` hint and how thick with its
``basis``.  The edge children carve their strips off what is left, **in the
order they come**, so the first ``top`` is the topmost and a ``left`` after
it starts below it.  Every ``fill`` child then gets **the same** leftover
rectangle -- which layers them, the way Navigator's console and desktop share
the band between its bars -- and they are placed after every edge whatever
their position among the children, so the child order stays free to say
what paints over what.  ``none`` leaves a child's geometry entirely alone,
for something that floats over the rest, like the clock over the menu bar.
"""

from __future__ import annotations

from navkit.stylesheet import StyleProperty
from navkit.widget import Widget

from navml.widgets.layout.layout import Layout
from navml.widgets.layout.layout.layout import Rect

#: Where a child of a dock layout may say it goes.
DOCK = ("fill", "top", "bottom", "left", "right", "none")


class DockLayout(Layout):
    """Children against the edges, and the middle filled."""

    #: Which edge a child goes against.  Read off the *child*.
    dock = StyleProperty("fill", values=DOCK)

    def plan(self, children: list[Widget]) -> dict[Widget, Rect]:
        x, y, width, height = 0, 0, self.width, self.height
        plan: dict[Widget, Rect] = {}
        fills = []
        for child in children:
            where = child.style_property("dock", "fill")
            if where == "fill":
                fills.append(child)
                continue
            if where == "none":
                continue
            basis = max(0, child.style_property("basis", 0))
            if where in ("top", "bottom"):
                thickness = min(basis, height)
                top = y if where == "top" else y + height - thickness
                plan[child] = (x, top, width, thickness)
                height -= thickness
                if where == "top":
                    y += thickness
            else:
                thickness = min(basis, width)
                left = x if where == "left" else x + width - thickness
                plan[child] = (left, y, thickness, height)
                width -= thickness
                if where == "left":
                    x += thickness
        for child in fills:
            plan[child] = (x, y, width, height)
        return plan
