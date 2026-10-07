"""≡ > Trashcan on/off: DOS Navigator's ``TTrashCan`` (GAUGES.PAS).

Five columns by three rows -- ``╤╤╪╤╤``, ``Trash``, ``└┴┴┴┘`` -- in the
desktop's bottom right corner, a column and a row in from it, over every
window, and hidden until the menu shows it (``cmHideShowTools``).  The mouse
drags it anywhere on the desktop; it keeps its distance from the bottom right
corner when the screen is resized, as ``gfGrowAll`` kept it.  Files dragged
out of a panel and dropped on it are erased (``cmDropped`` ->
``cmEraseGroup``): see :mod:`navigator.widgets.manager.panel.drag`.

DN's double click on it ran the *Reanimator*, its undelete; there is nothing
on a POSIX file system for that to do, and a double click does nothing.
"""

from __future__ import annotations

from typing import Any

from navkit.events import MouseClickEvent
from navkit.reactive import bind, reactive
from navkit.screen import Surface
from navkit.widget import Widget

#: ``TTrashCan.Draw``'s three rows, CP437's 209, 216, 192, 193 and 217.
ROWS = ("╤╤╪╤╤", "Trash", "└┴┴┴┘")
WIDTH, HEIGHT = 5, 3


class TrashCan(Widget):
    """The trash can, bound to the corner of *desktop*."""

    #: Shown by ≡ > Trashcan on/off.
    shown: bool = reactive(False)
    #: Columns and rows between it and the desktop's bottom right corner.
    gap_x: int = reactive(1)
    gap_y: int = reactive(1)
    #: Being dragged: ``sfDragging``, drawn in the frame-icons colour.
    dragging: bool = reactive(False)

    def __init__(self, desktop: Any, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.desktop = desktop
        self.width = bind(lambda o: WIDTH)
        self.height = bind(lambda o: HEIGHT)
        self.x = bind(lambda o: o.desktop.x + max(0, o.desktop.width - WIDTH - o.gap_x))
        self.y = bind(lambda o: o.desktop.y + max(0, o.desktop.height - HEIGHT - o.gap_y))
        self.visible = bind(lambda o: o.shown and o.desktop.visible)
        self._grab: tuple[int, int] | None = None

    def place(self, x: int, y: int) -> None:
        """Its top left corner at *x*, *y* in the desktop, kept on it whole."""
        desktop = self.desktop
        x = max(0, min(x, desktop.width - WIDTH))
        y = max(0, min(y, desktop.height - HEIGHT))
        self.gap_x = max(0, desktop.width - WIDTH - x)
        self.gap_y = max(0, desktop.height - HEIGHT - y)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """``DragView(dmDragMove)``: pressed, it follows the pointer until released."""
        app = self.application
        if event.button == "left" and event.action == "press" and app is not None:
            self._grab = (event.x, event.y)
            self.dragging = True
            app.capture_mouse(self)
            return True
        if self._grab is not None and event.action in ("move", "release"):
            gx, gy = self._grab
            self.place(self.x - self.desktop.x + event.x - gx, self.y - self.desktop.y + event.y - gy)
            if event.action == "release":
                self._grab = None
                self.dragging = False
            return True
        return event.action == "press"

    def render(self, surface: Surface) -> None:
        for y, text in enumerate(ROWS):
            surface.draw_text(0, y, text, self.style, WIDTH)
