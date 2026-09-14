# navml: generated
"""Generated from ``label.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.

(Until the parser and the code generator exist this file is written by hand, as
a stand-in for what they will emit.  Its *shape* is the contract -- everything
:mod:`navml._merge` relies on is here.)
"""

from __future__ import annotations

from typing import Any

from navkit.reactive import is_bound, reactive
from navkit.screen import Surface
from navkit.widget import Widget

#: The class this document declares.  The loader looks this name up in the
#: hand-written half rather than guessing one from the file name.
__navml_component__ = "Label"

__all__ = ["Label"]


class Label(Widget):
    """A line of text."""

    text: str = reactive("")                                    # label.nml:2
    align: str = reactive("left")                               # label.nml:3

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # The tree goes here, inline.  See *Building the tree* in
        # navml/DESIGN.md for why it is not a `_build()' method: a derived
        # component's would override its base's, so the base's children would
        # never be built and the derived one's would be built twice.

    def layout(self, width: int, height: int) -> None:
        """Size only this widget: its children are placed by the markup."""
        if not is_bound(self, Widget.width):
            self.width = width
        if not is_bound(self, Widget.height):
            self.height = height

    def render(self, surface: Surface) -> None:
        text = self.text[: max(0, self.width)]
        if self.align == "right":
            x = max(0, self.width - len(text))
        elif self.align == "center":
            x = max(0, (self.width - len(text)) // 2)
        else:
            x = 0
        surface.draw_text(x, 0, text, self.style)
