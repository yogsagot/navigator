# navml: generated
"""Generated from ``static_text.nml``.

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

__navml_component__ = "StaticText"

__all__ = ["StaticText"]


class StaticText(_Component):
    """A block of text that wraps, and never takes the keyboard.

    DOS Navigator's ``[37] Static text``, and Turbo Vision's ``TStaticText``.
    The plain one: a caption a dialog puts on itself, and what a ``Button``
    composes to draw its own.  ``Label`` is the *other* one -- a caption that
    belongs to a control beside it and focuses it.
    """

    #: The document this class was generated from.
    __navml_source__ = "static_text.nml"

    #: The text, which may carry one ``~A~`` run and any number of newlines.
    text: str = _reactive('')    # static_text.nml:9

    #: ``left``, ``center`` or ``right``, applied to each line separately.
    align: str = _reactive('left')    # static_text.nml:12

    #: Whether a line longer than the widget is broken onto the next one.
    #: Off gives one line clipped at the edge, which is what a caption inside
    #: a button wants.
    wrap: bool = _reactive(False)    # static_text.nml:17

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
