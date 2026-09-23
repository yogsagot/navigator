"""The handlers behind ``framed_button.nml``.

The base repeats the markup's -- ``FramedButton(Button)``, not
``FramedButton(Widget)``.  Both splice to the same MRO, but naming the real one
is what lets this component drop its markup half without changing what it
extends, and it is what gives an editor ``Button``'s members on ``self`` while
these handlers are being written.
"""

from __future__ import annotations

from navkit.screen import Surface

from navml.widgets.button import Button


class FramedButton(Button):
    """A button that draws a frame around itself."""

    def render(self, surface: Surface) -> None:
        super().render(surface)
        if self.width >= 2 and self.height >= 2:
            surface.draw_box(
                0, 0, self.width, self.height, self.style,
                charset=self.box_charset(),
            )
