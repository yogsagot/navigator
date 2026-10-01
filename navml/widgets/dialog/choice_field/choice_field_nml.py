# navml: generated
"""Generated from ``choice_field.nml``.

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
from navml.widgets.dialog.choice_line import ChoiceLine    # choice_field.nml:1
from navml.widgets.dialog.history import History    # choice_field.nml:2
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # choice_field.nml:3
from navml.widgets.dialog.label import Label    # choice_field.nml:4

__navml_component__ = "ChoiceField"

__all__ = ["ChoiceField"]


class ChoiceField(HorizontalLayout, _Component):
    """A caption, a line chosen into, and the ``▐↓▌`` that drops the choices.

    :class:`Field`'s shape with a :class:`ChoiceLine` where the input line
    was: markup alone, because it paints nothing itself.  The button is always
    shown -- it is the one way in that a mouse has -- and ``choices`` is what
    it drops; there is no history.
    """

    #: The document this class was generated from.
    __navml_source__ = "choice_field.nml"

    #: The caption, with one ``~A~`` run.
    label_text: str = _reactive('')    # choice_field.nml:14

    #: How many columns the caption takes before the line begins.
    label_width: int = _reactive(12)    # choice_field.nml:17

    #: The text in the line: one of ``choices``, or what it was seeded with.
    value: str = _Alias("entry", "value")    # choice_field.nml:20

    #: What the button drops.
    choices: _Any = _Alias("history", "choices")    # choice_field.nml:23

    #: Ids, annotated so the hand-written half completes them.
    caption: Label    # choice_field.nml:26
    entry: ChoiceLine    # choice_field.nml:33
    history: History    # choice_field.nml:36

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)    # choice_field.nml:25
        self.entry = ChoiceLine(parent=self)    # choice_field.nml:32
        self.history = History(parent=self)    # choice_field.nml:35

        self.caption.inline_style = _bind(    # choice_field.nml:27
            lambda _o: 'basis: %d; grow: 0' % _o.parent.label_width
        )
        self.caption.text = _bind(lambda _o: _o.parent.label_text)    # choice_field.nml:28
        self.caption.link = _bind(lambda _o: self.entry)    # choice_field.nml:29
        self.caption.align = 'left'    # choice_field.nml:30

        self.history.link = _bind(lambda _o: self.entry)    # choice_field.nml:37
        self.history.inline_style = 'basis: 3; grow: 0'    # choice_field.nml:38
