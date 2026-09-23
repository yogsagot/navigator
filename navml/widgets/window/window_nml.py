# navml: generated
"""Generated from ``window.nml``.

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

__navml_component__ = "Window"

__all__ = ["Window"]


class Window(_Component):
    """A framed box with a title, and the thing a dialog is made of.

    DOS Navigator's ``[33] Frame/background`` and ``[34] Frame icons``, and
    Turbo Vision's ``TWindow``.  It paints the frame, centres the title on the
    top edge, and puts a close icon in the corner -- and it is what carries the
    ``Alt+letter`` walk, because a window is the smallest thing that holds a
    whole set of controls.
    """

    #: The document this class was generated from.
    __navml_source__ = "window.nml"

    #: Shown centred on the top edge, with a space either side of it.
    title: str = _reactive('')    # window.nml:10

    #: Whether the ``[■]`` icon is painted, and the corner answers a click.
    closable: bool = _reactive(True)    # window.nml:13

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
