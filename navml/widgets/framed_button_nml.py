# navml: generated
"""Generated from ``framed_button.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.

(Written by hand until the parser and the code generator exist, as a stand-in
for what they will emit.)
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Widget``; markup never
#: names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind
from navkit.reactive import is_bound as _is_bound
from navkit.reactive import reactive as _reactive
from navkit.widget import Widget as _Widget

from navml.widgets.button import Button  # framed_button.nml:1
from navml.widgets.label import Label  # framed_button.nml:2

__navml_component__ = "FramedButton"

__all__ = ["FramedButton"]


class FramedButton(Button):
    """A :class:`~navml.widgets.button.Button` that also shows a key hint.

    Its base is itself a component with two halves, so this class sits on top
    of a four-deep chain once both are merged.
    """

    hint_text: str = _reactive("[enter]")                 # framed_button.nml:5

    hint: Label

    def __init__(self, **kwargs: _Any) -> None:
        # Builds the base component's tree first -- which is exactly why the
        # children are constructed here rather than in an overridable
        # ``_build()``: a shared name would mean this ran instead of Button's,
        # not after it.
        super().__init__(**kwargs)
        self.hint = Label(parent=self)                   # framed_button.nml:7
        self.hint.x = 1                                  # framed_button.nml:9
        self.hint.y = 1                                  # framed_button.nml:10
        self.hint.width = _bind(                          # framed_button.nml:11
            lambda _o: max(0, _o.parent.width - 2)
        )
        self.hint.height = 1                             # framed_button.nml:12
        self.hint.text = _bind(                           # framed_button.nml:13
            lambda _o: _o.parent.hint_text
        )
        self.hint.align = "right"                        # framed_button.nml:14

    def layout(self, width: int, height: int) -> None:
        """Size only this widget: its children are placed by the markup."""
        if not _is_bound(self, _Widget.width):
            self.width = width
        if not _is_bound(self, _Widget.height):
            self.height = height
