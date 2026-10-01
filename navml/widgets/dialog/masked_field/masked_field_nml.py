# navml: generated
"""Generated from ``masked_field.nml``.

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

from navml._alias import _Alias as _Alias
from navml.component import Component as _Component
from navml.widgets.dialog.masked_line import MaskedLine    # masked_field.nml:1
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # masked_field.nml:2
from navml.widgets.dialog.label import Label    # masked_field.nml:3

__navml_component__ = "MaskedField"

__all__ = ["MaskedField"]


class MaskedField(HorizontalLayout, _Component):
    """A caption and a :class:`MaskedLine`: digits in fixed places, and nothing

    else.  :class:`Field`'s shape without the history button, markup alone.
    """

    #: The document this class was generated from.
    __navml_source__ = "masked_field.nml"

    #: The caption, with one ``~A~`` run.
    label_text: str = _reactive('')    # masked_field.nml:9

    #: How many columns the caption takes before the line begins.
    label_width: int = _reactive(12)    # masked_field.nml:12

    #: The shape: ``9`` a digit's place, anything else a literal.
    mask: str = _reactive('')    # masked_field.nml:15

    #: Which digits a place takes, ``0`` to ``base - 1``.
    base: int = _reactive(10)    # masked_field.nml:18

    #: The text in the line.
    value: str = _Alias("entry", "value")    # masked_field.nml:21

    #: Ids, annotated so the hand-written half completes them.
    caption: Label    # masked_field.nml:24
    entry: MaskedLine    # masked_field.nml:31

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)    # masked_field.nml:23
        self.entry = MaskedLine(parent=self)    # masked_field.nml:30

        self.caption.inline_style = _bind(    # masked_field.nml:25
            lambda _o: 'basis: %d; grow: 0' % _o.parent.label_width
        )
        self.caption.text = _bind(lambda _o: _o.parent.label_text)    # masked_field.nml:26
        self.caption.link = _bind(lambda _o: self.entry)    # masked_field.nml:27
        self.caption.align = 'left'    # masked_field.nml:28

        self.entry.mask = _bind(lambda _o: _o.parent.mask)    # masked_field.nml:32
        self.entry.base = _bind(lambda _o: _o.parent.base)    # masked_field.nml:33
