# navml: generated
"""Generated from ``field.nml``.

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
from navml.widgets.label import Label    # field.nml:1

__navml_component__ = "Field"

__all__ = ["Field"]


class Field(_Component):
    """A caption and a value side by side.

    The library's one component written in markup alone: it paints nothing
    itself, so it needs no hand-written half, and ``navml.widgets.field`` is
    backed by the generated module directly.
    """

    #: The document this class was generated from.
    __navml_source__ = "field.nml"

    label_text: str = _reactive('')    # field.nml:9
    value_text: str = _reactive('')    # field.nml:10
    label_width: int = _reactive(12)    # field.nml:11

    #: Ids, annotated so the hand-written half completes them.
    caption: Label    # field.nml:14
    value: Label    # field.nml:23

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)    # field.nml:13
        self.value = Label(parent=self)    # field.nml:22

        self.caption.x = 0    # field.nml:15
        self.caption.y = 0    # field.nml:16
        self.caption.width = _bind(lambda _o: _o.parent.label_width)    # field.nml:17
        self.caption.height = 1    # field.nml:18
        self.caption.text = _bind(lambda _o: _o.parent.label_text)    # field.nml:19
        self.caption.align = 'left'    # field.nml:20

        self.value.x = _bind(lambda _o: _o.parent.label_width)    # field.nml:24
        self.value.y = 0    # field.nml:25
        self.value.width = _bind(    # field.nml:26
            lambda _o: max(0, _o.parent.width - _o.parent.label_width)
        )
        self.value.height = 1    # field.nml:27
        self.value.text = _bind(lambda _o: _o.parent.value_text)    # field.nml:28
        self.value.align = 'left'    # field.nml:29
