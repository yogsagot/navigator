"""A column of independent on/off boxes.

Python alone, and that is the rule rather than a preference: **markup declares
and places**, and this component does neither.  Every property it has --
``items``, ``value``, ``sel`` -- is ``Cluster``'s, every item it shows is
painted rather than placed, and a document holding nothing but a head would be
a file that says only what its class statement already says.  ``CheckBoxes``
and ``RadioButtons`` are therefore the two components that *lost* their markup
half by being finished.
"""

from __future__ import annotations

from navml.widgets.cluster import Cluster
from navml.widgets.control import parse_shortcut


class CheckBoxes(Cluster):
    """A column of independent on/off boxes.

    ``value`` is a bit per item -- Turbo Vision keeps a Word in
    ``TCheckBoxes`` and this is the same thing, which is what makes a value
    saved by the original readable here.
    """

    def chosen(self, index: int) -> bool:
        return bool(self.value & (1 << index))

    def toggle(self, index: int) -> None:
        self.value = self.value ^ (1 << index)

    @property
    def checked(self) -> tuple[str, ...]:
        """The captions that are ticked, without their ``~A~`` marks.

        A caller asking which boxes are on wants the words, not the markup:
        the tilde is a rendering instruction and stops being one the moment it
        leaves the widget.
        """
        return tuple(
            parse_shortcut(item)[0]
            for index, item in enumerate(self.items)
            if self.chosen(index)
        )
