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
also be *bound* to an expression -- ``panel.width = bind(lambda w:
w.parent.width // 2)`` -- which is what markup compiles to and what makes a
container able to place its children without a :meth:`layout` method at all.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Mapping

from navkit import stylesheet
from navkit.events import KeyEvent, MouseEvent
from navkit.reactive import computed, is_bound, reactive
from navkit.screen import Surface
from navkit.style import DEFAULT_STYLE, Style
from navkit.stylesheet import Stylesheet

if TYPE_CHECKING:
    # Only for the annotations: importing it for real would be a cycle, since
    # the application owns the widget tree.
    from navkit.application import Application


class Widget:
    """A rectangular, nestable piece of user interface."""

    x: int = reactive(0)
    y: int = reactive(0)
    width: int = reactive(0)
    height: int = reactive(0)
    visible: bool = reactive(True)
    #: What ``#name`` matches.  Deliberately not a ``navml`` ``id``, which is a
    #: compile-time label with no run-time existence -- see navml/DESIGN.md.
    name: str = reactive("")
    #: What ``.tag`` matches.  Frozen because the reactive layer counts a change
    #: only when a collection is *replaced*: a mutable set would be mutated in
    #: place and notify nothing.  Use :meth:`add_class` / :meth:`remove_class`.
    classes: frozenset[str] = reactive(frozenset())
    #: Declarations authored for this widget alone, as ``"bg: red"`` or the
    #: mapping :meth:`merge_style` stores.  Partial: it overlays the cascade
    #: property by property rather than replacing it, so it does not stop the
    #: properties it leaves alone from being inherited.
    inline_style: Any = reactive(None)
    #: Observable too, so an expression written in terms of the parent is
    #: re-evaluated when the widget moves to a different one.
    parent: Widget | None = reactive(None)
    #: Set by :attr:`Application.root` on the root widget alone, and observable
    #: for the same reason ``parent`` is: an expression written in terms of the
    #: application -- which is how a widget will reach the stylesheet -- has to
    #: be re-evaluated when the tree it belongs to is attached to one.  Without
    #: this a value derived before the attachment memoises the answer it got
    #: when there was no application, and only an unrelated write dislodges it.
    _application: Application | None = reactive(None)

    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        height: int = 0,
        name: str = "",
        classes: Iterable[str] = (),
        inline_style: Any = None,
        parent: Widget | None = None,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.name = name
        self.classes = frozenset(classes)
        self.inline_style = inline_style
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

    @computed
    def application(self) -> Application | None:
        """The :class:`~navkit.application.Application` this widget belongs to.

        Derived rather than walked afresh each time.  Both things the walk
        reads are observable, so the answer is memoised until the widget is
        reparented or a tree is attached to an application -- which is what
        makes it correct, and incidentally makes it cheap:
        :meth:`invalidate` asks for this on every reactive change, and a
        memoised read costs a fraction of the walk it replaces.
        """
        widget: Widget | None = self
        while widget is not None:
            app = widget._application
            if app is not None:
                return app
            widget = widget.parent
        return None

    # -- style ---------------------------------------------------------------

    @computed
    def stylesheet(self) -> Stylesheet:
        """The sheet governing this widget, or an empty one.

        Read through :attr:`application`, which is itself derived, so replacing
        the application's sheet -- loading a theme -- restyles the whole tree
        without anything having to walk it.
        """
        app = self.application
        return getattr(app, "stylesheet", None) or stylesheet.EMPTY

    @computed
    def declarations(self) -> Mapping[str, Any]:
        """Everything the cascade says about this widget, before it is split.

        Rules first, in ``(specificity, order)``, then the inline declarations
        on top -- the one authoring channel that outranks every selector.
        """
        resolved = dict(self.stylesheet.declarations_for(self))
        resolved.update(stylesheet.parse_declarations(self.inline_style))
        return resolved

    @computed
    def style(self) -> Style:
        """How this widget's own cells look, cascade and inheritance resolved.

        Inherits from the parent by starting there rather than at nothing, so
        a widget the sheet says nothing about looks like its container.  Only
        the properties something actually declared stop descending.
        """
        base = self.parent.style if self.parent is not None else DEFAULT_STYLE
        return base.derive(**stylesheet.appearance(self.declarations))

    @computed
    def _part_styles(self):
        """A resolver for this widget's parts, rebuilt when the sheet or style moves.

        A part lookup takes arguments, so it cannot be a computed itself; this
        is the way round that.  The resolver memoises for as long as it lives,
        which is until the sheet or this widget's own style changes.

        That is not quite enough on its own, which is the subtle part.  A state
        naming only a part -- ``Panel:active::row`` with no widget-level
        ``Panel:active`` rule -- never alters the widget's own style, so
        nothing here would be marked stale when it flips.  The widget's live
        states therefore go into the cache *key* rather than being relied on as
        a dependency, so a stale entry cannot be returned in the first place.
        """
        sheet, base = self.stylesheet, self.style
        cache: dict[tuple[Any, ...], Style] = {}

        def resolve(
            part: str,
            classes: frozenset[str],
            states: frozenset[str],
            own: frozenset[str],
        ) -> Style:
            key = (part, classes, states, own)
            if key not in cache:
                request = stylesheet.PartRequest(part, classes, states)
                found = sheet.declarations_for(self, request)
                cache[key] = base.derive(**stylesheet.appearance(found))
            return cache[key]

        return resolve

    def part_style(self, part: str, *, classes: Iterable[str] = (), **states: Any) -> Style:
        """How a *part* this widget paints itself should look.

        The widget supplies the state because it is the only thing that knows
        it -- ``self.part_style("row", selected=index == self.cursor)``.  Only
        truthy states count, so a flag can be passed straight through.
        """
        sheet = self.stylesheet
        own = frozenset(
            name for name in sheet.state_names if getattr(self, name, False)
        )
        active = frozenset(name for name, on in states.items() if on)
        return self._part_styles(part, frozenset(classes), active, own)

    def style_property(self, name: str, default: Any = None) -> Any:
        """A declaration that is not a ``Style`` field -- ``border``, say.

        Unlike appearance these do **not** inherit: a border that descended
        would hand a frame to every child of a framed widget.
        """
        return stylesheet.properties(self.declarations).get(name, default)

    def add_class(self, *names: str) -> None:
        """Tag this widget, so ``.name`` selectors match it."""
        self.classes = self.classes | frozenset(names)

    def remove_class(self, *names: str) -> None:
        self.classes = self.classes - frozenset(names)

    def merge_style(self, declarations: Any) -> None:
        """Overlay *declarations* onto whatever is already authored here.

        Merging rather than replacing is what makes this behave like the DOM's
        ``el.style``: setting a background leaves an already-authored
        foreground alone.  The result is stored as a mapping, because merging
        strings by concatenation would grow without bound.
        """
        merged = stylesheet.parse_declarations(self.inline_style)
        merged.update(stylesheet.parse_declarations(declarations))
        self.inline_style = merged

    # -- painting ------------------------------------------------------------

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
        if not is_bound(self, Widget.width):
            self.width = width
        if not is_bound(self, Widget.height):
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