"""A passing word: a small framed box that goes by itself.

Not Turbo Vision's, which had only modal message boxes.  A toast says
something happened -- a copy in the background finished -- without taking
the keyboard or waiting for an answer: it is never focused, a click on it
takes it away, and so does :attr:`Toast.seconds` passing.  Whoever adds it
places it; :attr:`Toast.natural_width` is how wide it would like to be.
"""

from __future__ import annotations

from typing import Any, Callable

from navkit.bidi import display_width, fit_cells
from navkit.events import MouseClickEvent
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navkit.widget import Widget

#: How long a toast stays up, unless it is given another time.
TOAST_SECONDS = 5.0


class Toast(Widget):
    """*text* in a frame titled *title*, for :attr:`seconds`."""

    #: On the top edge, as a window's title is.
    title: str = reactive("")
    text: str = reactive("")
    seconds: float = reactive(TOAST_SECONDS)

    def __init__(self, text: str = "", *, title: str = "", seconds: float = TOAST_SECONDS, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.text, self.title, self.seconds = text, title, seconds
        self.height = 3
        self._timer: Any = None
        #: Called once it has gone, for whoever stacks toasts to close up.
        self.gone: Callable[[Toast], None] | None = None

    @computed
    def natural_width(self) -> int:
        """The text with a space and the frame either side, or the title's room."""
        title = display_width(self.title) + 4 if self.title else 0
        return max(display_width(self.text) + 4, title, 12)

    def mounted(self) -> None:
        super().mounted()
        app = self.application
        if app is not None and self.seconds > 0:
            self._timer = app.call_later(self.seconds, self._expire)

    def unmounting(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        super().unmounting()

    def dismiss(self) -> None:
        """Gone now, as when its time is up."""
        if self.parent is not None:
            self.parent.remove(self)
            if self.gone is not None:
                self.gone(self)

    async def _expire(self) -> None:
        self._timer = None
        self.dismiss()

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.button != "left" or event.action != "press":
            return False
        self.dismiss()
        return True

    def render(self, surface: Surface) -> None:
        style = self.style
        surface.draw_box(0, 0, self.width, self.height, style, charset=self.box_charset(), fill=" ")
        room = max(0, self.width - 4)
        if self.title and room:
            surface.draw_text(2, 0, fit_cells(f" {self.title} ", self.width - 2), style)
        surface.draw_text(2, 1, fit_cells(self.text, room), style)
