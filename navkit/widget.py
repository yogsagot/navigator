"""The widget base class.

A widget owns a rectangle of the screen and knows how to paint it.  It never
touches the terminal, and it never learns where on the screen it is:
:meth:`Widget.render` receives a :class:`~navkit.screen.Surface` covering the
widget's own area, so it paints from ``0, 0`` in its own ``width`` x
``height`` and anything it aims outside itself is clipped away.  Positions --
``x``, ``y`` and the coordinates a :class:`~navkit.events.MouseClickEvent` carries
-- are relative to the parent, not to the terminal.

Geometry, visibility, style and the link to the parent are observable: assign
one and everything derived from it goes out of date, and the screen is marked
for a repaint without anybody calling :meth:`invalidate` by hand.  A size may
also be *bound* to an expression -- ``panel.width = bind(lambda w:
w.parent.width // 2)`` -- which is what markup compiles to and what makes a
container able to place its children without a :meth:`layout` method at all.
"""

from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING, Any, Iterable, Mapping

from navkit import glyphs as glyphs_module
from navkit import stylesheet
from navkit import terminal as terminal_module
from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
from navkit.reactive import computed, dispose_effects, is_bound, reactive
from navkit.screen import Surface
from navkit.style import DEFAULT_STYLE, Style
from navkit.stylesheet import Stylesheet

if TYPE_CHECKING:
    # Only for the annotations: importing it for real would be a cycle, since
    # the application owns the widget tree.
    from navkit.application import Application


def check_handlers(cls: type) -> None:
    """Refuse a class whose own ``on_*`` methods are not ``async def``.

    Run from ``__init_subclass__`` on both :class:`Widget` and
    :class:`~navkit.application.Application`, so the mistake is caught once,
    at import, naming the class and the method -- rather than at the first
    keystroke that happens to reach it.  Only the class's *own* body is
    checked; an inherited handler was checked where it was written.
    """
    for name, value in vars(cls).items():
        if not name.startswith("on_") or not callable(value):
            continue
        if not asyncio.iscoroutinefunction(value):
            raise TypeError(
                f"{cls.__name__}.{name} must be `async def`: every `on_*` "
                f"is awaited.  A hook that cannot be awaited where it is "
                f"called does not get an `on_*` name -- see Widget.mounted()."
            )


async def _call(target: object, event: Event, handler: Any) -> bool:
    """Await *handler*, refusing one that is not a coroutine function.

    Every handler is ``async def`` -- the rule, and this is where an instance
    attribute is held to it.  A class's own ``on_*`` methods are checked once
    when the class is created; a handler *assigned onto an instance*, which is
    what markup compiles to, can only be caught here.  Without the check the
    failure is ``TypeError: object bool can't be used in 'await' expression``,
    which names neither the widget nor the handler.
    """
    if not asyncio.iscoroutinefunction(handler):
        raise TypeError(
            f"{type(target).__name__}.{event.handler} must be `async def`; "
            f"every event handler is awaited"
        )
    return bool(await handler(event))


class Widget:
    """A rectangular, nestable piece of user interface."""

    #: The event classes this widget emits, as its own declaration -- read
    #: through :func:`navkit.events.emitted`, which unions the tuples down the
    #: MRO, so a subclass names only what it adds.  It is the component's
    #: public surface: what a reader, a checker and navml's code generator ask
    #: instead of hunting for :meth:`emit` calls.  Widgets that emit nothing
    #: of their own say nothing.
    emits: tuple[type[Event], ...] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        check_handlers(cls)

    x: int = reactive(0)
    y: int = reactive(0)
    width: int = reactive(0)
    height: int = reactive(0)
    visible: bool = reactive(True)
    #: Whether this widget takes the keyboard when focus is moved onto it.
    #: False on the base class, so a container, a label and a frame stay out of
    #: the tab order by saying nothing; a widget that wants keys opts in.
    #: Reactive rather than a plain class attribute so a widget can withdraw
    #: from the order while disabled, and so a binding can decide it.
    can_focus: bool = reactive(False)
    #: Whether this widget takes *all* input while it is mounted: keys go to
    #: it or to what it contains, focus cannot leave it, and a click outside
    #: it reaches nothing.  Read when the widget is mounted, because that is
    #: when the application is told -- a dialog declares it in its class body
    #: and is opened, which is the shape it is for.
    modal: bool = reactive(False)
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
    #: Which box-drawing characters this widget frames itself with.  A widget
    #: property rather than a ``Style`` field because a character set produces
    #: no SGR sequence and is an input to a drawing operation rather than an
    #: appearance a cell can carry -- navkit/DESIGN.md argues it at length.
    #: Declared here rather than by the application because :meth:`box_charset`
    #: reads it and :mod:`navkit.glyphs` owns its vocabulary.
    border = stylesheet.StyleProperty(
        glyphs_module.DEFAULT_BOX, values=tuple(glyphs_module.BOX_CHARSETS)
    )
    #: What the terminal's own cursor looks like while it sits on this widget.
    #: ``default`` leaves the shape the user configured alone, which is what
    #: anything that is not a text field should want.  A widget property for
    #: the same reason ``border`` is one: a shape is an input to an escape
    #: sequence rather than an appearance a cell can carry.
    caret = stylesheet.StyleProperty("default", values=tuple(terminal_module.CURSOR_SHAPES))
    #: A sheet governing this widget and everything under it, overriding the
    #: application's.  Normally ``None``; set it on the root of a screen that
    #: brings its own look.
    #:
    #: Public, and named to match :attr:`Application.stylesheet`, which is the
    #: same thing one layer up: the sheet an object *brings*.  What a widget
    #: *resolves against* is :attr:`effective_stylesheet`, which is derived and
    #: cannot be assigned.  Markup assigns this one like any other reactive,
    #: rather than through a spelling of its own.
    stylesheet: Stylesheet | None = reactive(None)
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
        """Add *child* to this widget and return it.

        A child added to a *mounted* widget is laid out and mounted at once.
        Without the layout it stays 0x0 until the next terminal resize, so a
        dialog opened at run time paints nothing at all, silently, unless
        every one of its sizes carries a binding.

        A tree still being assembled is left alone, because it has no size to
        cascade yet and :attr:`Application.root` lays the whole of it out when
        it is attached.  That also keeps the cascade where it was: ``layout``
        hands the parent's size to every child that is not bound, so laying
        out earlier than this would overwrite a width a caller had just
        passed to the constructor.
        """
        if child.parent is not None:
            child.parent.remove(child)
        child.parent = self
        self.children.append(child)
        if self.is_mounted:
            child.layout(self.width, self.height)
            child._mount()
        self.invalidate()
        return child

    def remove(self, child: Widget) -> None:
        """Detach *child*, unmounting it and everything under it first."""
        if child in self.children:
            # Both of these happen before the unlink, and have to.  The focused
            # widget can still be walked back to *child* -- a focus left
            # pointing into a detached subtree would send every key to a widget
            # that is no longer on screen.  And an ``on_unmount`` handler is
            # owed the place it is being removed from.
            app = self.application
            if app is not None and child._holds(app.focused):
                app.focused = None
            if child.is_mounted:
                child._unmount()
            self.children.remove(child)
            child.parent = None
            self.invalidate()

    def _holds(self, other: Widget | None) -> bool:
        """True if *other* is this widget or somewhere beneath it."""
        while other is not None:
            if other is self:
                return True
            other = other.parent
        return False

    def offset(self) -> tuple[int, int]:
        """Where this widget's parent's coordinates start, in screen ones.

        The sum of every ancestor's position, the root sitting at the origin.
        What :meth:`dispatch_mouse` needs to be handed an event for a widget
        that is not the root: it takes one in its *parent's* frame.
        """
        x = y = 0
        node = self.parent
        while node is not None:
            x += node.x
            y += node.y
            node = node.parent
        return x, y

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
    def effective_stylesheet(self) -> Stylesheet:
        """The sheet governing this widget, or an empty one.

        The nearest one wins: a widget carrying its own governs the subtree
        beneath it, and otherwise the search ends at the application's.  That
        is what lets a self-contained screen -- or a test holding one widget --
        be styled without an application around it.

        Named apart from :attr:`stylesheet` because they are different
        questions: that one is the sheet this widget *brings*, and is assigned;
        this one is the sheet it *resolves against*, and is derived from every
        sheet above it.  Most widgets bring none and resolve against one.

        Both the walk and :attr:`application` are derived, so replacing either
        sheet restyles everything below it without anything walking the tree.
        """
        widget: Widget | None = self
        while widget is not None:
            if widget.stylesheet is not None:
                return widget.stylesheet
            widget = widget.parent
        app = self.application
        return getattr(app, "stylesheet", None) or stylesheet.EMPTY

    @computed
    def style_declarations(self) -> Mapping[str, Any]:
        """Everything the cascade says about this widget, before it is split.

        Rules first, in ``(specificity, order)``, then the inline declarations
        on top -- the one authoring channel that outranks every selector.

        Named for the half of the cascade it carries rather than just
        ``declarations``, which collides with
        :func:`navkit.reactive.declarations` -- the reactive attributes a
        *class* declares, which is a different thing at a different level.
        """
        resolved = dict(self.effective_stylesheet.declarations_for(self))
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
        return base.derive(**stylesheet.appearance(self.style_declarations))

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
        sheet, base = self.effective_stylesheet, self.style
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

        The name is checked against :attr:`parts`, which is the only place it
        *can* be checked: a ``.nss`` selector matches by class name and may
        legally name a type the parser cannot import, so the sheet half of the
        question has no class to ask.  Here there is one, and a typo fails at
        the first paint naming the widget and what it really paints.
        """
        if part not in stylesheet.parts_of(type(self)):
            known = ", ".join(sorted(stylesheet.parts_of(type(self)))) or "none"
            raise LookupError(
                f"{type(self).__name__} paints no part {part!r}; it declares "
                f"{known}.  A part is named in `parts' on the class that "
                f"paints it."
            )
        sheet = self.effective_stylesheet
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
        return stylesheet.properties(self.style_declarations).get(name, default)

    @property
    def glyphs(self) -> int:
        """Which characters this widget may draw with -- a ``GLYPHS_*`` tier.

        A stylesheet says which character set is *wanted* and this says which
        can be *shown*; a widget that draws anything above ASCII owes both a
        look, the way :class:`~navkit.terminal.Terminal` takes the caller's
        wish for a mouse and the terminal's ability to report one and lets
        either veto.

        Deliberately a plain property rather than a ``computed``: the tier is
        settled once, when the terminal is detected, and never changes
        afterwards, so there is nothing for a dependency to invalidate.  A
        detached widget assumes Unicode, which is what the kit assumes whenever
        it has no terminal to ask.
        """
        app = self.application
        terminal = getattr(app, "terminal", None)
        return GLYPHS_UNICODE if terminal is None else terminal.info.glyphs

    def box_charset(self) -> str:
        """The six characters this widget's ``border`` asks for and can have.

        A widget wanting a different default frame declares :attr:`border`
        again with one; the vocabulary a sheet may use is the same either way.
        """
        return glyphs_module.charset(self.border, self.glyphs)

    def box_joins(self) -> str:
        """The five tee characters that match this widget's frame.

        Read off the same ``border`` property rather than one of its own, so a
        divider inside a double frame cannot end up drawn with single tees.
        See :func:`navkit.glyphs.joins`.
        """
        return glyphs_module.joins(self.border, self.glyphs)

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

    def spawn(self, work: Any) -> Any:
        """Run *work* beside the event loop -- see :meth:`Application.spawn`.

        The shorthand a handler reaches for, because the thing most likely to
        need it is a widget opening a dialog: a handler that *awaits* one
        holds the event queue's only consumer, so the dialog is never painted
        and the key that would dismiss it is never dispatched.  Starting the
        work instead lets the handler return and the frame appear.
        """
        app = self.application
        if app is None:
            raise RuntimeError(
                f"{type(self).__name__} is not in a running application, so "
                f"there is no event loop to start work beside"
            )
        return app.spawn(work)

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

    def cursor_position(self) -> tuple[int, int] | None:
        """Where the terminal's cursor belongs, in this widget's coordinates.

        None -- the default -- means this widget does not want one, which is
        every widget that is not editable. A text field returns the column and
        row of its insertion point and gets a real caret: the terminal's own,
        blinking the way the user configured it, in the shape :attr:`caret`
        asks for.

        Only the widget the keys are going to is asked, so a widget need not
        check whether it is focused. **Not spelled ``cursor``**, which
        `navigator`'s ``Panel`` already uses for the row its selection bar is
        on -- an int, and a reactive one. A base-class ``cursor`` would have
        been shadowed by it silently and the application would have been
        handed a row number where it expected a position.
        """
        return None

    async def on_key(self, event: KeyEvent) -> bool:
        """Handle a key press.  Return True to stop it propagating."""
        return False

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """Handle a mouse action.  Return True to stop it propagating."""
        return False

    # -- mounting -----------------------------------------------------------

    #: Whether this widget is part of a tree that belongs to an application.
    #: Spelled ``is_mounted`` so that :meth:`mounted` can be the callback.
    #: A plain attribute rather than a reactive one: it changes exactly when
    #: the mount walk sets it, and that walk already calls the hook, so an
    #: observable copy would be a second notification channel for one fact.
    is_mounted: bool = False

    #: The names this widget paints as ``::part``\ s, its public styling
    #: surface beside the properties it declares.  Unioned down the MRO by
    #: :func:`navkit.stylesheet.parts_of`, the way ``emits`` is and for the
    #: same reason: a subclass that paints a new part adds to what its base
    #: paints.
    parts: tuple[str, ...] = ()

    def mounted(self) -> None:
        """Called once this widget is part of a live tree.

        The place for anything that needs an application, a stylesheet or a
        size: the geometry is settled and :attr:`application` answers.  It is
        also **where effects belong** for a widget that can be removed and put
        back, because :meth:`remove` disposes them on the way out -- see
        :func:`navkit.reactive.dispose_effects`.  A widget that is built once
        and never detached may keep declaring them in ``__init__``.

        **Not an ``on_*`` handler, and synchronous**, which is forced rather
        than chosen: every handler is ``async def``, and this runs from
        :meth:`add`, which runs from ``__init__`` when a widget is constructed
        with a parent -- and a constructor cannot await.  It takes no event
        for the same reason it is not called ``on_mount``: nothing is being
        dispatched, the tree is telling a widget where it now is.
        """

    def unmounting(self) -> None:
        """Called before this widget leaves a live tree.

        Still parented, still sized, still reachable when this runs.  Anything
        outside the reactive graph -- a subprocess, an open file, a timer --
        is released here; the effects are navkit's to dispose.  Synchronous
        and eventless, for the reasons :meth:`mounted` gives.
        """

    def _mount(self) -> None:
        """Mount this subtree, then let the application settle the focus.

        Two steps rather than one because a modal only knows what it can focus
        once its children are mounted, and because a mount handler that
        focuses something itself should not then be overruled by a default.
        """
        if self.is_mounted:
            return
        self._mount_tree()
        app = self.application
        if app is not None:
            app._claim_focus()

    def _mount_tree(self) -> None:
        """Mount this widget and then everything under it.

        Parents first, so a child's handler finds every ancestor already
        mounted, and depth-first in child order so the tree is visited in
        the order it is written.  A modal is registered with the application
        *before* its own handler runs, so the handler already sees itself
        holding the input.
        """
        if self.is_mounted:
            return
        self.is_mounted = True
        app = self.application
        if self.modal and app is not None:
            app._push_modal(self)
        self.mounted()
        for child in list(self.children):
            child._mount_tree()

    def _unmount(self) -> None:
        """Unmount everything under this widget and then the widget itself.

        The mirror of :meth:`_mount`: children first, so a child is taken
        apart while its parent is still whole, and the widget's own handler
        runs before its effects are disposed rather than after.
        """
        if not self.is_mounted:
            return
        for child in reversed(list(self.children)):
            child._unmount()
        self.unmounting()
        dispose_effects(self)
        self.is_mounted = False
        # Last, and while the widget is still attached: releasing the input is
        # the final thing a modal does, and the application has to be able to
        # reach it to hand the focus back.
        app = self.application
        if self.modal and app is not None:
            app._pop_modal(self)

    # -- focus --------------------------------------------------------------

    @computed
    def focused(self) -> bool:
        """Whether this widget is the one the application sends keys to.

        A ``computed``, so it is also a stylesheet state: ``Panel:focused``
        matches through the same ``getattr`` every ``:state`` selector uses,
        and moving focus restyles both widgets without anybody asking for a
        repaint.
        """
        app = self.application
        return app is not None and app.focused is self

    def focus(self) -> bool:
        """Take the keyboard.  False if this widget cannot have it.

        A widget must be :attr:`can_focus`, visible, attached to an
        application, and inside the active modal if there is one.  Whether it
        is *reachable* -- inside a container that is itself visible -- is not
        asked here but at delivery, in :meth:`dispatch_key`, so that hiding a
        container does not have to chase the focus that happens to be inside
        it.
        """
        app = self.application
        if app is None or not self.can_focus or not self.visible:
            return False
        modal = app.modal
        if modal is not None and not modal._holds(self):
            return False
        app.focused = self
        return True

    def focusable(self) -> list[Widget]:
        """The tab order of this subtree: visible, focusable, in tree order.

        Pre-order, so a container that can take focus itself comes before the
        children it contains.  Scoped to a subtree rather than global because
        that is what a modal dialog will need -- it runs the same walk over
        itself and nothing outside it is reachable.
        """
        if not self.visible:
            return []
        order = [self] if self.can_focus else []
        for child in self.children:
            order.extend(child.focusable())
        return order

    def _focus_path(self) -> list[Widget]:
        """The focused widget and its ancestors up to this one, innermost first.

        Empty if the focus is outside this subtree or behind something
        invisible, which is the eligibility test :meth:`dispatch_key` makes at
        delivery time rather than when focus was set.
        """
        app = self.application
        widget = app.focused if app is not None else None
        path: list[Widget] = []
        while widget is not None:
            if not widget.visible:
                return []
            path.append(widget)
            if widget is self:
                return path
            widget = widget.parent
        return []

    async def emit(self, event: Event) -> bool:
        """Offer *event* to this widget, its ancestors, then the application.

        The other direction from :meth:`dispatch_key`: input arrives from
        outside and travels *down* to where the user pointed, while a widget's
        own event travels *up*, because it knows its sender and not its
        audience.  The walk stops at the first handler returning True, so the
        innermost claim on an event wins -- the widget that raised it gets
        first refusal.

        A handler is anything awaitable found under ``event.handler``: the
        ``async def on_*`` a widget class defines, or an attribute of that name
        assigned onto the instance, which is what markup compiles to.  A
        widget that declares neither is skipped, so a new event type needs no
        stub anywhere.
        """
        widget: Widget | None = self
        while widget is not None:
            handler = getattr(widget, event.handler, None)
            if handler is not None and await _call(widget, event, handler):
                return True
            widget = widget.parent
        # The application sees input before the tree and emitted events
        # after it.  Its ``on_event`` hook is deliberately not offered one: it
        # exists to intercept an event *before* the widgets, and this one has
        # already passed every widget that could have claimed it.
        app = self.application
        if app is not None:
            handler = getattr(app, event.handler, None)
            if handler is not None and await _call(app, event, handler):
                return True
        return False

    async def dispatch_key(self, event: KeyEvent) -> bool:
        """Offer a key to the focused widget in this subtree, then up to here.

        The same walk :meth:`emit` makes, starting where the keyboard is
        rather than where the event was raised -- so an unhandled key reaches
        the container that holds the focused widget, and a container can carry
        the bindings its children share.

        With nothing focused, or with the focus outside this subtree or behind
        something invisible, this widget alone is offered the key. That is
        deliberately *not* the old behaviour of touring every descendant until
        one claimed it: a key belongs to whatever holds the keyboard, and when
        nothing does, to nothing.
        """
        for widget in self._focus_path() or (self,):
            if await widget.on_key(event):
                return True
        return False

    async def dispatch_mouse(self, event: MouseClickEvent) -> bool:
        """Offer a mouse action to the child under the pointer, then to self.

        *event* arrives in the parent's coordinates -- the same ones :attr:`x`
        and :attr:`y` are in -- and is shifted into this widget's own before
        going any further, so :meth:`on_mouse_click` always sees a position relative
        to the widget handling it.

        **Delivered under ``event.handler``, not to ``on_mouse_click`` by name**,
        which is the same lookup :meth:`emit` makes and the whole of what lets
        a refinement of a mouse action -- a ``DoubleClickEvent`` -- reach
        ``on_double_click`` and nothing else.  A plain ``MouseClickEvent`` derives
        ``on_mouse_click``, which every widget has, so that call is the one this
        always made.  A widget defining no handler for the refinement is
        skipped, and skipped is what "did not claim it" already means here, so
        the event falls outward to an ancestor exactly as an unhandled press
        does and no widget needs a stub.
        """
        local = event.translated(-self.x, -self.y)
        for child in reversed(self.children):
            if child.visible and child.contains(local.x, local.y):
                if await child.dispatch_mouse(local):
                    return True
        handler = getattr(self, event.handler, None)
        return handler is not None and await _call(self, local, handler)