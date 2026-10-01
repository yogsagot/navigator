# navml: generated
"""Generated from ``date_field.nml``.

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
from navml.widgets.dialog.date_button import DateButton    # date_field.nml:1
from navml.widgets.dialog.masked_line import MaskedLine, mask_for    # date_field.nml:2
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # date_field.nml:3
from navml.widgets.dialog.label import Label    # date_field.nml:4

__navml_component__ = "DateField"

__all__ = ["DateField"]


class DateField(HorizontalLayout, _Component):
    """A caption, a line holding a date, and the ``▐↓▌`` that drops a

    calendar to pick one from.

    :class:`Field`'s shape with a :class:`DateButton` where the history was:
    markup alone.  The line is a :class:`MaskedLine`, digits in the places
    ``date_format`` gives them; the button reads it and writes it in the same
    format, and Alt+Down in the line drops it; Up and Down step a digit.
    """

    #: The document this class was generated from.
    __navml_source__ = "date_field.nml"

    #: The caption, with one ``~A~`` run.
    label_text: str = _reactive('')    # date_field.nml:15

    #: How many columns the caption takes before the line begins.
    label_width: int = _reactive(12)    # date_field.nml:18

    #: How the line spells a date, in ``strftime``'s directives.
    date_format: str = _reactive('%d-%m-%Y')    # date_field.nml:21

    #: The text in the line.
    value: str = _Alias("entry", "value")    # date_field.nml:24

    #: Ids, annotated so the hand-written half completes them.
    caption: Label    # date_field.nml:27
    entry: MaskedLine    # date_field.nml:35
    picker: DateButton    # date_field.nml:39

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)    # date_field.nml:26
        self.entry = MaskedLine(parent=self)    # date_field.nml:34
        self.picker = DateButton(parent=self)    # date_field.nml:38

        self.caption.inline_style = _bind(    # date_field.nml:28
            lambda _o: 'basis: %d; grow: 0' % _o.parent.label_width
        )
        self.caption.text = _bind(lambda _o: _o.parent.label_text)    # date_field.nml:29
        self.caption.link = _bind(lambda _o: self.entry)    # date_field.nml:30
        self.caption.align = 'left'    # date_field.nml:31

        self.entry.mask = _bind(lambda _o: mask_for(_o.parent.date_format))    # date_field.nml:36

        self.picker.link = _bind(lambda _o: self.entry)    # date_field.nml:40
        self.picker.date_format = _bind(lambda _o: _o.parent.date_format)    # date_field.nml:41
        self.picker.inline_style = 'basis: 3; grow: 0'    # date_field.nml:42
