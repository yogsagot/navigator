"""The menu bar, and the five pull-downs DOS Navigator put across the top.

The pull-downs themselves are not written yet: the bar paints their names and
their hotkeys, and opening one waits on the widget library.
"""

from __future__ import annotations

from navkit.screen import Surface
from navkit.widget import Widget


MENU_ITEMS = ["Left", "Files", "Commands", "Options", "Right"]


class MenuBar(Widget):
    """The pull-down menu bar across the top of the screen."""

    #: The highlighted letter in each name.
    parts = ("hotkey",)

    def render(self, surface: Surface) -> None:
        label, hotkey = self.style, self.part_style("hotkey")
        surface.fill(0, 0, self.width, 1, " ", label)
        column = 1
        for item in MENU_ITEMS:
            surface.draw_text(column, 0, item[0], hotkey)
            surface.draw_text(column + 1, 0, item[1:], label)
            column += len(item) + 2
