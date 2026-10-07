# navml: generated
"""Generated from ``group_box.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component

__navml_component__ = "GroupBox"

__all__ = ["GroupBox"]


class GroupBox(_Component):
    """A titled single frame round its children: what Turbo Vision drew for a

    view with ``ofFramed`` and a ``TLabel`` on the frame's top line, as DOS
    Navigator's System Information built its four boxes.  The children are
    placed inside it in its own coordinates, the frame taking the outer row
    and column on each side.
    """

    #: The document this class was generated from.
    __navml_source__ = "group_box.nml"

    #: The caption on the top edge, two cells in, with a blank either side;
    #: a ``~A~`` run is drawn in the shortcut colour.  Empty: no caption.
    title: str = _reactive('')    # group_box.nml:9

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
