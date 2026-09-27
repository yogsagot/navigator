"""Every child over the whole area, as layers.

The order of the children is the whole of how they stack, as it is anywhere
in navkit: the first is painted first and hit-tested last.  Hints are
ignored -- a layer has no share to ask for.
"""

from __future__ import annotations

from navkit.widget import Widget

from navml.widgets.layout.layout import Layout
from navml.widgets.layout.layout.layout import Rect


class StackLayout(Layout):
    """Children one on top of another, each filling the layout."""

    def plan(self, children: list[Widget]) -> dict[Widget, Rect]:
        return {child: (0, 0, self.width, self.height) for child in children}
