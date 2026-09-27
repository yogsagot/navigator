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
from navml.widgets.dialog.history import History    # field.nml:1
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # field.nml:2
from navml.widgets.dialog.input_line import InputLine    # field.nml:3
from navml.widgets.dialog.label import Label    # field.nml:4

__navml_component__ = "Field"

__all__ = ["Field"]


class Field(HorizontalLayout, _Component):
    """A caption and the line it names, side by side.

    The library's one component written in markup alone: it paints nothing
    itself, so it needs no hand-written half, and ``navml.widgets.dialog.field`` is
    backed by the generated module directly.

    It is also where ``alias`` and ``link`` are each worth their existence.
    ``alias value: entry.value`` is how the text gets in and out without the
    caller reaching through ``field.entry``, and ``link: entry`` is what makes
    the caption's ``~N~`` put the keyboard in the line beside it -- which is
    the whole of what Turbo Vision's ``TLabel`` is *for*.

    And it is a row, so it *is* a ``HorizontalLayout``: the caption asks for
    ``label_width`` columns and no more, and the line takes the rest.
    """

    #: The document this class was generated from.
    __navml_source__ = "field.nml"

    #: The caption, with one ``~A~`` run.
    label_text: str = _reactive('')    # field.nml:22

    #: How many columns the caption takes before the line begins.
    label_width: int = _reactive(12)    # field.nml:25

    #: The history the line remembers into, or ``""`` for none.  Naming one
    #: puts the ``▐↓▌`` button after the line, which gives up three columns.
    history_id: str = _reactive('')    # field.nml:29

    #: The text in the line.  An alias, so a read and a write both reach the
    #: ``InputLine``'s own reactive one property deep, and a binding assigned
    #: through it is re-owned by whoever wrote it.
    value: str = _Alias("entry", "value")    # field.nml:34

    #: Ids, annotated so the hand-written half completes them.
    caption: Label    # field.nml:37
    entry: InputLine    # field.nml:44
    history: History    # field.nml:47

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)    # field.nml:36
        self.entry = InputLine(parent=self)    # field.nml:43
        self.history = History(parent=self)    # field.nml:46

        self.caption.inline_style = _bind(    # field.nml:38
            lambda _o: 'basis: %d; grow: 0' % _o.parent.label_width
        )
        self.caption.text = _bind(lambda _o: _o.parent.label_text)    # field.nml:39
        self.caption.link = _bind(lambda _o: self.entry)    # field.nml:40
        self.caption.align = 'left'    # field.nml:41

        self.history.link = _bind(lambda _o: self.entry)    # field.nml:48
        self.history.history_id = _bind(lambda _o: _o.parent.history_id)    # field.nml:49
        self.history.visible = _bind(lambda _o: _o.parent.history_id != '')    # field.nml:50
        self.history.inline_style = 'basis: 3; grow: 0'    # field.nml:51
