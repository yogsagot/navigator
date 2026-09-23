"""A column of choices, of which exactly one is taken.

Python alone for the reason ``check_boxes.py`` gives at length: it declares
nothing and places nothing.  The same ``[47-49]`` palette as ``CheckBoxes``,
because DOS Navigator gives the two one set of colours between them -- Turbo
Vision gives them one ``TCluster`` between them, and so does this.

What differs is the mark, the arithmetic, and one behaviour.

Moving the cursor *chooses* here, which it does not in a check box column:
Turbo Vision's ``TRadioButtons`` moves the value with ``Sel``, because a set
of radio buttons always has exactly one answer and an arrow key that changed
nothing would be a key that did nothing.
"""

from __future__ import annotations

from navkit.events import KeyEvent

from navml.widgets.cluster import Cluster
from navml.widgets.control import parse_shortcut


class RadioButtons(Cluster):
    """A column of choices, of which exactly one is taken.

    ``value`` is an index rather than a bit set.
    """

    #: Radio marks are the second pair in the glyph table.
    mark_offset = 2
    brackets = "()"

    def chosen(self, index: int) -> bool:
        return index == self.value

    def toggle(self, index: int) -> None:
        self.value = index

    @property
    def choice(self) -> str:
        """The caption that is taken, without its ``~A~`` mark, or ``""``."""
        if 0 <= self.value < len(self.items):
            return parse_shortcut(self.items[self.value])[0]
        return ""

    async def on_key(self, event: KeyEvent) -> bool:
        taken = await super().on_key(event)
        if taken and event.key in ("up", "down"):
            self.value = self.sel
        return taken
