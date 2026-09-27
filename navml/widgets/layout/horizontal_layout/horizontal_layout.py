"""Children side by side, left to right, each as tall as the layout.

A child's width is its ``basis`` plus its share of what is left by ``grow``;
see :mod:`navml.widgets.layout.layout` for the hints and the rules they follow.
"""

from __future__ import annotations

from navml.widgets.layout.layout import LinearLayout


class HorizontalLayout(LinearLayout):
    """Children in a row."""

    horizontal = True
