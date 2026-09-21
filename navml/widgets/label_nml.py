# navml: generated
"""Generated from ``label.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.

(Until the parser and the code generator exist this file is written by hand, as
a stand-in for what they will emit.  Its *shape* is the contract -- everything
:mod:`navml._merge` relies on is here.)
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import reactive as _reactive
from navkit.screen import Surface as _Surface

from navml.component import Component as _Component

#: The class this document declares.  The loader looks this name up in the
#: hand-written half rather than guessing one from the file name.
__navml_component__ = "Label"

__all__ = ["Label"]


class Label(_Component):
    """A line of text."""

    #: The document this class was generated from.
    __navml_source__ = "label.nml"

    text: str = _reactive("")                                    # label.nml:2
    align: str = _reactive("left")                               # label.nml:3

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        # The tree goes here, inline.  See *Building the tree* in
        # navml/DESIGN.md for why it is not a `_build()' method: a derived
        # component's would override its base's, so the base's children would
        # never be built and the derived one's would be built twice.

    def render(self, surface: _Surface) -> None:
        text = self.text[: max(0, self.width)]
        if self.align == "right":
            x = max(0, self.width - len(text))
        elif self.align == "center":
            x = max(0, (self.width - len(text)) // 2)
        else:
            x = 0
        surface.draw_text(x, 0, text, self.style)
