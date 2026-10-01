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

from navkit.reactive import reactive

from navml.widgets.dialog.cluster import Cluster
from navml.widgets.dialog.control import parse_shortcut


class CheckBoxes(Cluster):
    """A column of independent on/off boxes.

    ``value`` is a bit per item -- Turbo Vision keeps a Word in
    ``TCheckBoxes`` and this is the same thing, which is what makes a value
    saved by the original readable here.
    """

    #: The bits shown ``[?]``: neither on nor off, *leave it as it is*.
    #: Turbo Vision's ``TMultiCheckBoxes`` idea, for one dialog over several
    #: things that disagree -- File Attributes over files whose modes differ.
    #: A bit in here is off in :attr:`value` as well, so a caller that knows
    #: nothing of the third state reads it as off and is no worse for it.
    mixed: int = reactive(0)

    #: The bits that may come back to ``[?]`` once moved off it.  A press
    #: cycles such a bit ``?`` -> ``X`` -> blank -> ``?``; every other bit
    #: stays two-state, which is what a box with no ``mixed`` start wants.
    tristate: int = reactive(0)

    #: The third mark.  ASCII, as the brackets are, so every glyph tier has it.
    mixed_mark = "?"

    def chosen(self, index: int) -> bool:
        return bool(self.value & (1 << index))

    def is_mixed(self, index: int) -> bool:
        """Whether item *index* shows ``[?]``."""
        return bool(self.mixed & (1 << index))

    def toggle(self, index: int) -> None:
        bit = 1 << index
        if self.mixed & bit:
            self.mixed = self.mixed & ~bit
            self.value = self.value | bit
        elif self.value & bit:
            self.value = self.value & ~bit
        elif self.tristate & bit:
            self.mixed = self.mixed | bit
        else:
            self.value = self.value | bit

    def mark_char(self, index: int, off: str, on: str) -> str:
        if self.is_mixed(index):
            return self.mixed_mark
        return super().mark_char(index, off, on)

    def mark_states(self, index: int) -> dict[str, bool]:
        return {**super().mark_states(index), "mixed": self.is_mixed(index)}

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
