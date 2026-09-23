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

from navml._alias import _Alias as _Alias
from navml.component import Component as _Component
from navml.widgets.input_line import InputLine    # field.nml:1
from navml.widgets.label import Label    # field.nml:2

__navml_component__ = "Field"

__all__ = ["Field"]


class Field(_Component):
    """A caption and the line it names, side by side.

    The library's one component written in markup alone: it paints nothing
    itself, so it needs no hand-written half, and ``navml.widgets.field`` is
    backed by the generated module directly.

    It is also where ``alias`` and ``link`` are each worth their existence.
    ``alias value: entry.value`` is how the text gets in and out without the
    caller reaching through ``field.entry``, and ``link: entry`` is what makes
    the caption's ``~N~`` put the keyboard in the line beside it -- which is
    the whole of what Turbo Vision's ``TLabel`` is *for*.
    """

    #: The document this class was generated from.
    __navml_source__ = "field.nml"

    #: The caption, with one ``~A~`` run.
    label_text: str = _reactive('')    # field.nml:17

    #: How many columns the caption takes before the line begins.
    label_width: int = _reactive(12)    # field.nml:20

    #: The text in the line.  An alias, so a read and a write both reach the
    #: ``InputLine``'s own reactive one property deep, and a binding assigned
    #: through it is re-owned by whoever wrote it.
    value: str = _Alias("entry", "value")    # field.nml:25

    #: Ids, annotated so the hand-written half completes them.
    caption: Label    # field.nml:28
    entry: InputLine    # field.nml:38

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)    # field.nml:27
        self.entry = InputLine(parent=self)    # field.nml:37

        self.caption.x = 0    # field.nml:29
        self.caption.y = 0    # field.nml:30
        self.caption.width = _bind(lambda _o: _o.parent.label_width)    # field.nml:31
        self.caption.height = 1    # field.nml:32
        self.caption.text = _bind(lambda _o: _o.parent.label_text)    # field.nml:33
        self.caption.link = _bind(lambda _o: self.entry)    # field.nml:34
        self.caption.align = 'left'    # field.nml:35

        self.entry.x = _bind(lambda _o: _o.parent.label_width)    # field.nml:39
        self.entry.y = 0    # field.nml:40
        self.entry.width = _bind(    # field.nml:41
            lambda _o: max(0, _o.parent.width - _o.parent.label_width)
        )
        self.entry.height = 1    # field.nml:42
