# navml: generated
"""Generated from ``button.nml``.

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

from navml.widgets.label import Label  # button.nml:1

__navml_component__ = "Button"

__all__ = ["Button"]


class Button(_Widget):
    """A pressable box with a centred caption."""

    text: str = _reactive("")                                    # button.nml:4

    #: Ids, annotated so the hand-written half completes them.
    caption: Label

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)                       # button.nml:6
        self.caption.x = 1                                      # button.nml:8
        self.caption.y = 0                                      # button.nml:9
        self.caption.width = _bind(                              # button.nml:10
            lambda _o: max(0, _o.parent.width - 2)
        )
        self.caption.height = 1                                 # button.nml:11
        self.caption.text = _bind(lambda _o: _o.parent.text)     # button.nml:12
        self.caption.align = "center"                           # button.nml:13

    def layout(self, width: int, height: int) -> None:
        """Size only this widget: its children are placed by the markup."""
        if not _is_bound(self, _Widget.width):
            self.width = width
        if not _is_bound(self, _Widget.height):
            self.height = height
