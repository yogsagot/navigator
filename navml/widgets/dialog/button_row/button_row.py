"""A dialog's row of buttons: one width each, two cells apart, centred.

Turbo Vision placed every button by hand, and the dialogs here did the same
-- ``y: parent.height - 4`` and an x worked out per button, or a ``slot()``
method doing the sum.  A row says it once::

    ButtonRow:
        anchors:
            left: 0
            right: 0
            bottom: 2
        Button:
            text: "O~K~"
        Button:
            text: "~C~ancel"

**Every child takes** :attr:`button_width` **unless it says otherwise**: a
child's own ``basis`` (and ``grow``) in its ``style:`` wins, and
``button_width: 0`` gives each button its caption's width instead.  A hidden
button gives up its slot, so the rest stay centred.  Nothing grows, which is
what lets ``justify`` centre them.
"""

from __future__ import annotations

from typing import Any

from navkit.bidi import display_width
from navkit.reactive import reactive
from navkit.widget import Widget

from navml.widgets.dialog.button import Button
from navml.widgets.dialog.control import parse_shortcut
from navml.widgets.layout.horizontal_layout import HorizontalLayout

#: What a button needs beyond its caption when it is sized by it: the two
#: markers, one blank either side of the caption, and the shadow's column.
BUTTON_CHROME = 5


class ButtonRow(HorizontalLayout):
    """Buttons side by side, all one width, centred in the row."""

    #: The cells each button gets, 11 being DOS Navigator's usual: nine of
    #: face and markers, one of shadow, one of air.  0 sizes each by its
    #: caption.
    button_width: int = reactive(11)

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("spacing", 2)
        kwargs.setdefault("justify", "center")
        super().__init__(**kwargs)
        if "height" not in kwargs:
            self.height = 2

    def hints(self, child: Widget) -> tuple[int, int]:
        basis = child.style_property("basis", None)
        grow = child.style_property("grow", 0)
        if basis is not None:
            return basis, grow
        if self.button_width > 0:
            return self.button_width, grow
        if isinstance(child, Button):
            caption = parse_shortcut(child.text)[0]
            return display_width(caption) + BUTTON_CHROME, grow
        return child.width, grow


__all__ = ["BUTTON_CHROME", "ButtonRow"]
