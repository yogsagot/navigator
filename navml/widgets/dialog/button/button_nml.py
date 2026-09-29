# navml: generated
"""Generated from ``button.nml``.

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
from navml.widgets.dialog.control import Control    # button.nml:1
from navml.widgets.dialog.static_text import StaticText    # button.nml:2

__navml_component__ = "Button"

__all__ = ["Button"]


class Button(Control, _Component):
    """A pressable box with a centred caption.

    DOS Navigator's ``[41-46] Button normal / default / selected / disabled /
    shortcut / shadow``, and Turbo Vision's ``TButton`` as DOS Navigator's
    ``DIALOGS.PAS`` draws it: a plain coloured face with no brackets, ``►``
    and ``◄`` inside it on the button Enter would press, and a half-block
    shadow.  Two rows and one column wider than its face: the shadow is inside
    the button's own rectangle rather than painted over its neighbour, which
    is what keeps it a widget that can be placed anywhere -- and pressed, the
    face moves one cell right into the shadow's column, still inside it.
    """

    #: The document this class was generated from.
    __navml_source__ = "button.nml"

    #: The caption, with one ``~A~`` run marking the letter that presses it.
    text: str = _reactive('')    # button.nml:16

    #: Whether Enter presses this button from anywhere in the dialog.  One
    #: per dialog, and the dialog is what enforces that rather than this.
    default: bool = _reactive(False)    # button.nml:20

    #: Whether the button is drawn pressed: held under the mouse, or under a
    #: Space that has not been let go.  The click comes when it is released.
    down: bool = _reactive(False)    # button.nml:24

    #: Ids, annotated so the hand-written half completes them.
    caption: StaticText    # button.nml:27

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = StaticText(parent=self)    # button.nml:26

        self.caption.x = _bind(lambda _o: 2 if _o.parent.down else 1)    # button.nml:30
        self.caption.y = 0    # button.nml:31
        self.caption.width = _bind(lambda _o: max(0, _o.parent.width - 3))    # button.nml:33
        self.caption.height = 1    # button.nml:34
        self.caption.text = _bind(lambda _o: _o.parent.text)    # button.nml:35
        self.caption.align = 'center'    # button.nml:36
