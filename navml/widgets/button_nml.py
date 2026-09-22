# navml: generated
"""Generated from ``button.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.label import Label    # button.nml:1

__navml_component__ = "Button"

__all__ = ["Button"]


class Button(_Component):
    """A pressable box with a centred caption."""

    #: The document this class was generated from.
    __navml_source__ = "button.nml"

    text: str = _reactive('')    # button.nml:5

    #: Ids, annotated so the hand-written half completes them.
    caption: Label    # button.nml:8

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)    # button.nml:7

        self.caption.x = 1    # button.nml:9
        self.caption.y = 0    # button.nml:10
        self.caption.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # button.nml:11
        self.caption.height = 1    # button.nml:12
        self.caption.text = _bind(lambda _o: _o.parent.text)    # button.nml:13
        self.caption.align = 'center'    # button.nml:14
