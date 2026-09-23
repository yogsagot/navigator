# navml: generated
"""Generated from ``label.nml``.

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
from navml.widgets.control import Control    # label.nml:1

__navml_component__ = "Label"

__all__ = ["Label"]


class Label(Control, _Component):
    """A caption that belongs to the control beside it.

    DOS Navigator's ``[38-40] Label normal / selected / shortcut``, and Turbo
    Vision's ``TLabel``.  Not the plain one: this is the caption that carries a
    ``~N~`` and hands the keyboard to whatever its ``link`` names, which is
    what ``[39] Label selected`` is a colour *for* -- it lights up while its
    control has the focus.  Plain text is ``StaticText``.
    """

    #: The document this class was generated from.
    __navml_source__ = "label.nml"

    #: The caption, with one ``~A~`` run marking the letter that reaches it.
    text: str = _reactive('')    # label.nml:12

    #: ``left``, ``center`` or ``right``.
    align: str = _reactive('left')    # label.nml:15

    #: The control this caption belongs to -- in markup, an ``id`` from the
    #: same document.  A label with no link is a label that does nothing, and
    #: is a mistake rather than a shape worth having.
    link = _reactive(None)    # label.nml:20

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
