"""The widget base class.

A widget owns a rectangle of the screen and knows how to paint it.  It never
touches the terminal: :meth:`Widget.render` receives the
:class:`~navkit.screen.ScreenBuffer` the frame is being composed in.

Observable attributes -- where assigning one recomputes every attribute that
references it -- will be layered onto this class; until then, widgets mark
themselves dirty explicitly via :meth:`invalidate`.
"""

from __future__ import annotations

from navkit.events import KeyEvent, MouseEvent
from navkit.screen import ScreenBuffer
from navkit.style import DEFAULT_STYLE, Style


class Widget:
    """A rectangular, nestable piece of user interface."""

    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        height: int = 0,
        style: Style = DEFAULT_STYLE,
        parent: Widget | None = None,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.style = style
        self.visible = True
        self.parent: Widget | None = None
        self.children: list[Widget] = []
        if parent is not None:
            parent.add(self)

    # -- tree ---------------------------------------------------------------

    def add(self, child: Widget) -> Widget:
        """Add *child* to this widget and return it."""
        if child.parent is not None:
            child.parent.remove(child)
        child.parent = self
        self.children.append(child)
        self.invalidate()
        return child

    def remove(self, child: Widget) -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            self.invalidate()

    @property
    def application(self):
        """The :class:`~navkit.application.Application` this widget belongs to."""
        widget: Widget | None = self
        while widget is not None:
            app = getattr(widget, "_application", None)
            if app is not None:
                return app
            widget = widget.parent
        return None

    def invalidate(self) -> None:
        """Ask for a repaint on the next turn of the event loop."""
        app = self.application
        if app is not None:
            app.invalidate()

    # -- geometry -----------------------------------------------------------

    def contains(self, x: int, y: int) -> bool:
        """True if screen position *x*, *y* falls inside this widget."""
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def layout(self, width: int, height: int) -> None:
        """Fit this widget into *width* x *height*.

        Called on the root widget whenever the terminal is resized.  The
        default fills the area and hands the same size to every child;
        containers override this to place their children.
        """
        self.width = width
        self.height = height
        for child in self.children:
            child.layout(width, height)

    # -- painting -----------------------------------------------------------

    def render(self, buffer: ScreenBuffer) -> None:
        """Paint this widget -- but not its children -- into *buffer*."""

    def render_tree(self, buffer: ScreenBuffer) -> None:
        """Paint this widget and then, on top of it, its children."""
        if not self.visible:
            return
        self.render(buffer)
        for child in self.children:
            child.render_tree(buffer)

    # -- events -------------------------------------------------------------

    def on_key(self, event: KeyEvent) -> bool:
        """Handle a key press.  Return True to stop it propagating."""
        return False

    def on_mouse(self, event: MouseEvent) -> bool:
        """Handle a mouse action.  Return True to stop it propagating."""
        return False

    def dispatch_key(self, event: KeyEvent) -> bool:
        """Offer a key to the children (topmost first), then to this widget."""
        for child in reversed(self.children):
            if child.visible and child.dispatch_key(event):
                return True
        return self.on_key(event)

    def dispatch_mouse(self, event: MouseEvent) -> bool:
        """Offer a mouse action to the child under the pointer, then to self."""
        for child in reversed(self.children):
            if child.visible and child.contains(event.x, event.y):
                if child.dispatch_mouse(event):
                    return True
        return self.on_mouse(event)