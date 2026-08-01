"""The widget base class.

A widget owns a rectangle of the screen and knows how to paint it.  It never
touches the terminal, and it never learns where on the screen it is:
:meth:`Widget.render` receives a :class:`~navkit.screen.Surface` covering the
widget's own area, so it paints from ``0, 0`` in its own ``width`` x
``height`` and anything it aims outside itself is clipped away.  Positions --
``x``, ``y`` and the coordinates a :class:`~navkit.events.MouseEvent` carries
-- are relative to the parent, not to the terminal.

Geometry, visibility, style and the link to the parent are observable: assign
one and everything derived from it goes out of date, and the screen is marked
for a repaint without anybody calling :meth:`invalidate` by hand.  A size may
also be *bound* to an expression -- ``bind(panel, "width", lambda w:
w.parent.width // 2)`` -- which is what markup compiles to and what makes a
container able to place its children without a :meth:`layout` method at all.
"""

from __future__ import annotations

from navkit.events import KeyEvent, MouseEvent
from navkit.reactive import is_bound, reactive
from navkit.screen import Surface
from navkit.style import DEFAULT_STYLE, Style


class Widget:
    """A rectangular, nestable piece of user interface."""

    x: int = reactive(0)
    y: int = reactive(0)
    width: int = reactive(0)
    height: int = reactive(0)
    style: Style = reactive(DEFAULT_STYLE)
    visible: bool = reactive(True)
    #: Observable too, so an expression written in terms of the parent is
    #: re-evaluated when the widget moves to a different one.
    parent: Widget | None = reactive(None)

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

    def _reactive_changed(self, name: str) -> None:
        """An observable attribute really changed, so the screen is stale.

        Only assignments to *sources* arrive here, which is enough: every
        derived value that moved is downstream of one of them, and the
        application tracks dirtiness with a single flag.  Per-widget damage
        tracking would have to look at the derived values as well.
        """
        self.invalidate()

    # -- geometry -----------------------------------------------------------

    def contains(self, x: int, y: int) -> bool:
        """True if *x*, *y* -- in the parent's coordinates -- is inside this."""
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def layout(self, width: int, height: int) -> None:
        """Fit this widget into *width* x *height*.

        Called on the root widget whenever the terminal is resized.  The
        default fills the area and hands its own size to every child;
        containers either override this or bind their children's geometry.

        A size that carries a binding is left alone.  The binding is the
        widget's own declaration of how big it wants to be, and assigning over
        it is an error rather than a silent override -- so the cascade has to
        step around it, or the first resize would take the whole tree down.
        """
        if not is_bound(self, "width"):
            self.width = width
        if not is_bound(self, "height"):
            self.height = height
        for child in self.children:
            child.layout(self.width, self.height)

    # -- painting -----------------------------------------------------------

    def render(self, surface: Surface) -> None:
        """Paint this widget -- but not its children -- into *surface*.

        *surface* covers exactly this widget, so paint from ``0, 0``; there is
        no need to add :attr:`x` and :attr:`y`, and no way to reach a sibling.
        """

    def render_tree(self, surface: Surface) -> None:
        """Paint this widget and then, on top of it, its children.

        *surface* covers the parent, so the first thing to do is narrow it to
        this widget.  Children are then painted through that, which is what
        keeps every widget's coordinates relative to the one above it.
        """
        if not self.visible:
            return
        own = surface.view(self.x, self.y, self.width, self.height)
        self.render(own)
        for child in self.children:
            child.render_tree(own)

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
        """Offer a mouse action to the child under the pointer, then to self.

        *event* arrives in the parent's coordinates -- the same ones :attr:`x`
        and :attr:`y` are in -- and is shifted into this widget's own before
        going any further, so :meth:`on_mouse` always sees a position relative
        to the widget handling it.
        """
        local = event.translated(-self.x, -self.y)
        for child in reversed(self.children):
            if child.visible and child.contains(local.x, local.y):
                if child.dispatch_mouse(local):
                    return True
        return self.on_mouse(local)