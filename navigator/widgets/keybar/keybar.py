"""The function key bar, and the ten labels DOS Navigator gave F1 to F10.

The labels are a module constant rather than a property because nothing yet
changes them; the original swapped the whole row while a modifier was held, and
that is what would make them one.
"""

from __future__ import annotations

from navkit.screen import Surface
from navkit.widget import Widget


FUNCTION_KEYS = [
    "Help",
    "Menu",
    "View",
    "Edit",
    "Copy",
    "RenMov",
    "Mkdir",
    "Delete",
    "PullDn",
    "Quit",
]


class KeyBar(Widget):
    """The F1..F10 hint bar across the bottom of the screen."""

    #: The digit in front of each label.
    parts = ("number",)

    def render(self, surface: Surface) -> None:
        label_style, number_style = self.style, self.part_style("number")
        surface.fill(0, 0, self.width, 1, " ", label_style)
        slot = max(3, self.width // len(FUNCTION_KEYS))
        for index, label in enumerate(FUNCTION_KEYS):
            column = index * slot
            if column >= self.width:
                break
            number = str(index + 1)
            surface.draw_text(column, 0, number, number_style)
            surface.draw_text(
                column + len(number),
                0,
                label.ljust(slot - len(number)),
                label_style,
                slot - len(number),
            )
