"""Children stacked top to bottom, each as wide as the layout.

A child's height is its ``basis`` plus its share of what is left by ``grow``;
see :mod:`navml.widgets.layout.layout` for the hints and the rules they follow.
"""

from __future__ import annotations

from navml.widgets.layout.layout import LinearLayout


class VerticalLayout(LinearLayout):
    """Children in a column."""

    horizontal = False
