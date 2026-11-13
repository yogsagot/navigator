"""Painting: invalidating, lending the terminal to a program and taking it back, composing the
frame (modals, dimming, the cursor, a mirrored screen), and resizing.

A mixin of :class:`~navkit.application.Application` (:class:`navkit.widget.Mixin`):
methods only; its state, keys and ``checks`` are in ``navkit/application.py``.
"""

from __future__ import annotations

import asyncio
import dataclasses
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.capabilities import BIDI_WORDS
from navkit.screen import Clip, ScreenBuffer, Surface, for_words, render_diff
from navkit.style import Style
from navkit.terminal import HIDE_CURSOR, cursor_color, place_cursor
from navkit import i18n
from navkit.widget import Widget
from navkit.application import DIMMED_STYLES_LIMIT, _ARROW_MIRROR, _WAKE

# The surface is a stub with no module of its own, by design (navml.surface).
# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from navkit.application_surface import Application as _Base
else:
    from navkit.widget import Mixin as _Base


class Painting(_Base):
    """Painting: invalidating, lending the terminal to a program and taking it back, composing the"""

    # -- painting -----------------------------------------------------------

    def invalidate(self, widget: Widget | None = None) -> None:
        """Request a repaint.  Cheap and safe to call many times per frame.

        *widget* is what changed, when a widget is asking for itself
        (:meth:`Widget.invalidate`).  A change inside the top modal leaves
        what lies beneath it as it was, which lets :meth:`_render` reuse
        that; anything else -- no widget named included -- does not.
        """
        if not self._below_dirty and (
            widget is None or (modal := self.modal) is None or not modal._holds(widget)
        ):
            self._below_dirty = True
        if widget is not None and widget.paints_alone:
            if self._damage is not None:
                self._damage.add(widget)
        else:
            self._damage = None
        if not self._dirty:
            self._dirty = True
            self._wake()

    def _reactive_changed(self, name: str) -> None:
        """One of the application's own observables changed: repaint.

        The same hook ``Widget`` has, and needed for the same reason.  A
        write reaches ``_reactive_changed`` only on the object it was made
        to, and every widget derived from ``focused`` or ``stylesheet`` is
        merely marked stale -- so without this, moving the focus and nothing
        else (Tab between two panels) restyled both widgets and asked for no
        frame, and the change showed up with the next unrelated key.
        """
        self.invalidate()

    def _wake(self) -> None:
        """Nudge the loop when it is parked waiting for input."""
        if self._loop is not None and not self._events.full():
            self._events.put_nowait(_WAKE)

    # -- lending the terminal ---------------------------------------------------

    @property
    def released(self) -> bool:
        """Whether the terminal is lent out by :meth:`release_terminal`."""
        return self._released is not None

    def release_terminal(self, on_input: Callable[[bytes], bytes]) -> None:
        """Lend the real terminal out, as Midnight Commander's Ctrl+O does.

        The screen and its modes are given back (:meth:`Terminal.suspend`),
        nothing is painted, and every byte read goes raw to *on_input*, which
        returns whatever of it is still the application's -- the bytes after
        the key that ended the loan, once it has called
        :meth:`reclaim_terminal`.  The loop goes on running, so timers, pty
        output and resizes are still handled.
        """
        self._released = on_input
        for event in self._parser.flush():
            self.post_event(event)
        self.terminal.write(self._graphics.release(self.terminal.info.graphics))
        self.terminal.suspend()
        self._cursor_shown = None
        self._caret_color = None  # suspend() gave the terminal its own back
        self.terminal_focused = None

    def bell(self) -> None:
        """Ring the terminal's bell -- DOS Navigator's ``Beep`` -- now: a frame
        is written whole within one turn, so nothing of one is pending here."""
        bell = getattr(self.terminal, "bell", None)
        if bell is not None:
            bell()
            self.terminal.flush()

    def redraw(self) -> None:
        """Paint the next frame whole, every cell, whatever the terminal is
        thought to show already -- for a screen something else has written
        over.  Turbo Vision's ``Application^.Redraw``."""
        self._front = None
        self._cursor_shown = None
        self.invalidate()

    def use_terminal_info(self, info: Any) -> None:
        """Use *info* -- a :class:`~navkit.capabilities.TerminalInfo` -- from
        the next frame on, and paint that frame whole.  This is how a running
        application changes its colour depth or glyph tier."""
        if info.graphics != self.terminal.info.graphics:
            self.terminal.write(self._graphics.release(self.terminal.info.graphics))
        self.terminal.info = info
        self._parser.charset = info.charset
        self.info_revision += 1
        self.redraw()

    def reclaim_terminal(self) -> None:
        """End a :meth:`release_terminal` loan: the screen back, repainted whole."""
        if self._released is None:
            return
        self._released = None
        self.terminal.resume()
        # Whatever happened to the focus meanwhile went unreported.
        self.terminal_focused = None
        self._graphics.forget()  # left with the alternate screen
        self._front = None
        self._cursor_shown = None
        self._dirty = False
        self.invalidate()

    async def _render(self) -> None:
        """Compose a frame and flush the difference to the terminal."""
        if self._released is not None:
            # Lent out: the frame waits for reclaim_terminal, which repaints.
            return
        if self._min_frame_interval and self._loop is not None:
            overdue = self._min_frame_interval - (self._loop.time() - self._last_frame)
            if overdue > 0:
                await asyncio.sleep(overdue)

        rtl = self.rtl
        if rtl != self._rtl_painted:
            self._rtl_painted = rtl
            self._below_dirty = True
            self._underlay = None
        self._back.rtl = rtl
        modal = self.modal
        underlay = self._underlay
        if (
            underlay is not None
            and not self._below_dirty
            and underlay[0] is modal
            and modal is not None
            and modal.parent is not None
            and modal.visible
            and underlay[1].width == self._back.width
            and underlay[1].height == self._back.height
        ):
            # Only the modal changed: start from what lay beneath it last
            # time and paint the modal and whatever stands above it.  A
            # progress box ticking over a full desktop is otherwise the whole
            # tree, every tick, for a few changed cells.
            self._back.copy_from(underlay[1])
            self._reusing = True
            try:
                self._render_above(modal)
            finally:
                self._reusing = False
        elif not self._render_damage(modal, rtl):
            self._underlay = None
            self._back.clear(self.background)
            if self._root is not None:
                self._composing = True
                try:
                    self._root.render_tree(self._back)
                finally:
                    self._composing = False
        self._below_dirty = False
        self._damage = set()

        shown = self._back.mirrored() if rtl else self._back
        if self.terminal.info.bidi == BIDI_WORDS:
            shown = for_words(shown)
        # Before the diff: a sixel picture that goes has its cells written
        # again, so it is told before the diff is worked out.
        before, after = self._graphics.compose(
            self._back.placements, shown, self._front, self.terminal.info.graphics
        )
        output = before + render_diff(self._front, shown, self.terminal.info) + after
        cursor = self._cursor()
        if cursor is not None and cursor[3] != self._caret_color:
            # Before the cursor is shown, so it never appears in the old one.
            output += cursor_color(cursor[3])
            self._caret_color = cursor[3]
            self.terminal.cursor_colored = cursor[3] is not None
        if cursor != self._cursor_shown:
            # Emitted after the diff, always: painting moves the terminal's
            # own cursor as a side effect, so anything placed before it would
            # be left wherever the last cell was written.
            output += place_cursor(*cursor[:3]) if cursor is not None else HIDE_CURSOR
            self._cursor_shown = cursor
        elif output and cursor is not None:
            # Unchanged, but the paint just moved it.  The position alone --
            # it is already visible and already the right shape.
            output += f"\x1b[{cursor[1] + 1};{cursor[0] + 1}H"
        if output:
            self.terminal.write(output)
            self.terminal.flush()

        if self._front is None:
            self._front = ScreenBuffer(self._back.width, self._back.height)
        self._front.copy_from(shown)
        self._dirty = False
        self._last_frame = self._loop.time() if self._loop is not None else 0.0

    def _render_damage(self, modal: Widget | None, rtl: bool) -> bool:
        """Repaint only what the widgets that asked for this frame cover,
        over the last frame still in :attr:`_back`; False when the whole
        frame has to be painted instead.

        Every widget that asked ``paints_alone``, so what changed is inside
        their rectangles -- where they are now and where they were last
        painted.  The tree is painted as always, through a :class:`Clip` of
        the rectangles' bounds: a widget wholly outside is skipped with its
        children, and one inside, or partly, paints in its usual order, so
        what lies over the clock -- a tooltip, an open menu -- is painted over
        it again.  Not under a modal (whose dimming is applied to everything
        painted before it), on a mirrored screen, with a picture shown, or
        when clipping would have changed a cell (:attr:`Clip.spoiled`).
        """
        damage = self._damage
        root = self._root
        if (
            not damage or modal is not None or rtl or root is None
            or self._front is None or self._back.placements
            or (self._front.width, self._front.height) != (self._back.width, self._back.height)
        ):
            return False
        rects = []
        for widget in damage:
            painted = widget.__dict__.get("_painted_at")
            if painted is not None:
                rects.append(painted)
            place = self._place_of(widget)
            if place is not None:
                rects.append(place)
        if not rects:
            return False
        left = min(x for x, _, _, _ in rects)
        top = min(y for _, y, _, _ in rects)
        right = max(x + width for x, _, width, _ in rects)
        bottom = max(y + height for _, y, _, height in rects)
        clip = Clip(self._back, left, top, right - left, bottom - top)
        # What the clip lets through is painted from scratch, as the whole
        # frame would be: the background first.
        clip.fill(left, top, right - left, bottom - top, " ", self.background)
        self._composing = True
        try:
            root.render_tree(clip)
        finally:
            self._composing = False
        if clip.spoiled:
            return False
        return True

    def _place_of(self, widget: Widget) -> tuple[int, int, int, int] | None:
        """*widget*'s rectangle on the screen, or None when it is not shown --
        detached, or itself or an ancestor hidden."""
        x, y = 0, 0
        node: Widget | None = widget
        while node is not None:
            if not node.visible:
                return None
            x, y = x + node.x, y + node.y
            if node is self._root:
                return (x, y, widget.width, widget.height)
            node = node.parent
        return None

    def _painting_modal(self, widget: Widget) -> None:
        """*widget*, a modal, is about to paint: dim what is already painted.

        Called by :meth:`Widget.render_tree` just before a modal widget paints
        itself.  Everything in the frame so far is what the modal is blocking,
        and everything after it -- the modal, its children, and any overlay a
        control inside it opened, such as a history drop-down -- is painted
        over the dimmed cells at full strength.  Only the *top* modal dims, so
        a dialog opened from a dialog dims the first one once, not twice.

        Rewriting cells after they are painted needs no widget's cooperation,
        which is the reason it is done here rather than by a style state.  It
        only marks the cells ``dim``; what faint *looks* like is decided at the
        edge, in :meth:`TerminalInfo.adapt_style`, because SGR 2 alone is
        ignored for direct-RGB colours by VTE-based terminals.

        It is also where the frame so far is kept as the modal's underlay,
        which :meth:`_render` paints over instead of the whole tree while
        nothing beneath the modal changes.
        """
        if widget is not self.modal or self._reusing:
            return
        if self.dim_modal and widget.dims_behind:
            self._dim_behind()
        if self._composing:
            underlay = ScreenBuffer(self._back.width, self._back.height)
            underlay.copy_from(self._back)
            self._underlay = (widget, underlay)

    def _dim_behind(self) -> None:
        dimmed = self._dimmed

        def dim(style: Style) -> Style:
            twin = dimmed.get(style)
            if twin is None:
                if len(dimmed) >= DIMMED_STYLES_LIMIT:
                    dimmed.clear()
                twin = dimmed[style] = style.derive(dim=True)
            return twin

        self._back.restyle(dim)

    def _render_above(self, modal: Widget) -> None:
        """Paint *modal* and everything painted after it, over its underlay.

        The tail of a whole-tree paint, in the same order: the modal's own
        subtree, then -- walking up -- each ancestor's later children and its
        :meth:`~Widget.render_after`.  What came before is the underlay.
        """
        path = [modal]
        while path[-1].parent is not None:
            path.append(path[-1].parent)
        path.reverse()  # the root first
        surfaces: list[Surface] = []
        surface: Surface = self._back
        for widget in path[:-1]:
            surface = surface.view(widget.x, widget.y, widget.width, widget.height)
            surfaces.append(surface)
        modal.render_tree(surfaces[-1])
        for depth in range(len(path) - 2, -1, -1):
            parent, child, own = path[depth], path[depth + 1], surfaces[depth]
            for later in parent.children[parent.children.index(child) + 1:]:
                later.render_tree(own)
            parent._guarded(parent.render_after, own)

    def _cursor(self) -> tuple[int, int, str, tuple[int, int, int] | None] | None:
        """Screen position, shape and colour of the terminal cursor, or None.

        The colour is the caret widget's ``::caret`` (:meth:`Widget.caret_color`)
        as the ``(r, g, b)`` OSC 12 takes, or ``None`` for the terminal's own
        -- also where the terminal is not to be sent one, or the colour is a
        palette index only its own theme knows.

        **Shown exactly where the keys go.** The widgets asked are the ones
        on the focus path -- the same walk :meth:`Widget.dispatch_key` makes,
        so the same modal, the same visibility test and the same answer of
        "nobody" when nothing holds the keyboard. A caret on a widget that
        could not receive what is typed into it would be a lie told once per
        frame.

        **The nearest one with a caret wins**, head first, which is the order
        a key is offered in. A widget holding the keyboard with no caret of
        its own -- a list -- declines the printable keys, they walk up, and an
        ancestor that types them somewhere is where they are really going.
        """
        scope = self.modal or self._root
        if scope is None:
            return None
        path = scope._focus_path()
        for widget in path:
            position = widget.cursor_position()
            if position is not None:
                break
        else:
            return None
        x, y = position
        if not (0 <= x < widget.width and 0 <= y < widget.height):
            return None
        offset_x, offset_y = widget.offset()
        x, y = offset_x + widget.x + x, offset_y + widget.y + y
        if not (0 <= x < self._back.width and 0 <= y < self._back.height):
            return None
        if self._back.rtl:
            x = self._mirror_x(x, widget)
        info = self.terminal.info
        color = info.rgb(widget.caret_color()) if info.cursor_color else None
        return x, y, widget.style_property("caret", "default"), color

    @property
    def rtl(self) -> bool:
        """Whether the screen is mirrored, reading right to left (:attr:`direction`)."""
        if self.direction == "auto":
            return i18n.is_rtl()
        return self.direction == "rtl"

    def _mirror_x(self, x: int, widget: Widget | None) -> int:
        """Screen column *x* of the frame as painted, where a mirrored screen
        shows it -- or, since mirroring is its own inverse, the other way.

        Inside a widget that keeps left to right (:attr:`Widget.mirrors`) the
        column is reversed within that widget first, as its cells were.
        """
        keeper = widget.unmirrored() if widget is not None else None
        if keeper is not None:
            left = keeper.offset()[0] + keeper.x
            x = 2 * left + keeper.width - 1 - x
        return self._back.width - 1 - x

    def _unmirror(self, event: Event) -> Event:
        """*event*, a mouse report in screen columns, in the frame's own.

        Left and Right trade places too, for whatever holds the keyboard on a
        mirrored screen (:meth:`Widget.arrows_mirrored`): the next menu, the
        next column, the next cell is to the left there.

        Done as the event comes off the queue -- once, so the double-click
        and context menu derived from it are already in the frame's columns.
        """
        if isinstance(event, KeyEvent) and self._back.rtl and event.key in _ARROW_MIRROR:
            scope = self.modal or self._root
            path = scope._focus_path() if scope is not None else []
            head = path[0] if path else scope  # nothing focused: keys go to the root
            if head is not None and head.unmirrored() is None and head.arrows_mirrored():
                return dataclasses.replace(event, key=_ARROW_MIRROR[event.key])
            return event
        if not (isinstance(event, MouseClickEvent) and self._back.rtl):
            return event
        x = self._back.width - 1 - event.x
        scope = self.modal or self._root
        target = None
        if scope is not None:
            dx, dy = scope.offset() if scope is not self._root else (0, 0)
            target = scope.widget_at(x - dx, event.y - dy)
        keeper = target.unmirrored() if target is not None else None
        if keeper is not None:
            left = keeper.offset()[0] + keeper.x
            x = 2 * left + keeper.width - 1 - x
        return dataclasses.replace(event, x=x)

    def _resize(self, width: int, height: int) -> None:
        self._asked_size = (width, height)
        self._clicks.reset()  # the layout moved out from under the pointer
        self._below_dirty = True
        self._damage = None
        self._back.resize(width, height, self.background)
        self._front = None  # sizes differ -- force a full repaint
        if self._root is not None:
            self._root.layout(width, height)
        self._dirty = True
