# navml: generated
"""Generated from ``framed_button.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.

(Written by hand until the parser and the code generator exist, as a stand-in
for what they will emit.)
"""

from __future__ import annotations

from typing import Any

from navkit.reactive import bind, is_bound, reactive
from navkit.widget import Widget

from navml.widgets.button import Button
from navml.widgets.label import Label

__navml_component__ = "FramedButton"

__all__ = ["FramedButton"]


class FramedButton(Button):
    """A :class:`~navml.widgets.button.Button` that also shows a key hint.

    Its base is itself a component with two halves, so this class sits on top
    of a four-deep chain once both are merged.
    """

    hint_text: str = reactive("[enter]")                 # framed_button.nml:2

    hint: Label

    def __init__(self, **kwargs: Any) -> None:
        # Builds the base component's tree first -- which is exactly why the
        # children are constructed here rather than in an overridable
        # ``_build()``: a shared name would mean this ran instead of Button's,
        # not after it.
        super().__init__(**kwargs)
        self.hint = Label(parent=self)                   # framed_button.nml:4
        self.hint.x = 1                                  # framed_button.nml:6
        self.hint.y = 1                                  # framed_button.nml:7
        self.hint.width = bind(                          # framed_button.nml:8
            lambda _o: max(0, _o.parent.width - 2)
        )
        self.hint.height = 1                             # framed_button.nml:9
        self.hint.text = bind(                           # framed_button.nml:10
            lambda _o: _o.parent.hint_text
        )
        self.hint.align = "right"                        # framed_button.nml:11

    def layout(self, width: int, height: int) -> None:
        """Size only this widget: its children are placed by the markup."""
        if not is_bound(self, Widget.width):
            self.width = width
        if not is_bound(self, Widget.height):
            self.height = height
