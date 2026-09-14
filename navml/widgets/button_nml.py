# navml: generated
"""Generated from ``button.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.

(Written by hand until the parser and the code generator exist, as a stand-in
for what they will emit.)
"""

from __future__ import annotations

from typing import Any

from navkit.reactive import bind, is_bound, reactive
from navkit.widget import Widget

from navml.widgets.label import Label

__navml_component__ = "Button"

__all__ = ["Button"]


class Button(Widget):
    """A pressable box with a centred caption."""

    text: str = reactive("")                                    # button.nml:2

    #: Ids, annotated so the hand-written half completes them.
    caption: Label

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)                       # button.nml:4
        self.caption.x = 1                                      # button.nml:6
        self.caption.y = 0                                      # button.nml:7
        self.caption.width = bind(                              # button.nml:8
            lambda _o: max(0, _o.parent.width - 2)
        )
        self.caption.height = 1                                 # button.nml:9
        self.caption.text = bind(lambda _o: _o.parent.text)     # button.nml:10
        self.caption.align = "center"                           # button.nml:11

    def layout(self, width: int, height: int) -> None:
        """Size only this widget: its children are placed by the markup."""
        if not is_bound(self, Widget.width):
            self.width = width
        if not is_bound(self, Widget.height):
            self.height = height
