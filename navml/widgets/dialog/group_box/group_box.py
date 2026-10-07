"""The painting behind ``group_box.nml``: the frame, then the caption over it."""

from __future__ import annotations

from navkit import glyphs as glyphs_module
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget

from navml.widgets.dialog.static_text import draw_caption


class GroupBox(Widget):
    """A frame with a title, never taking the keyboard."""

    #: Single, as an ``ofFramed`` view's frame was.
    border = StyleProperty("single", values=tuple(glyphs_module.BOX_CHARSETS))

    #: The caption, and its marked letter.
    parts = ("title", "shortcut")

    def render(self, surface: Surface) -> None:
        if self.width < 2 or self.height < 2:
            return
        surface.draw_box(0, 0, self.width, self.height, self.style,
                         charset=self.box_charset(), fill=" ")
        if self.title and self.width > 6:
            draw_caption(surface, 2, 0, f" {self.title} ", self.part_style("title"),
                         self.part_style("shortcut"), max_width=self.width - 4)
