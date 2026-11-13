"""The event loop -- dispatch a batch, run its effects, paint -- and delivering the mouse: hover,
tooltips, VTE's middle click.

A mixin of :class:`~navkit.application.Application` (:class:`navkit.widget.Mixin`):
methods only; its state, keys and ``checks`` are in ``navkit/application.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import dataclasses
import time

from navkit.events import (
    ClickOutsideEvent,
    ContextMenuEvent,
    DoubleClickEvent,
    Event,
    KeyEvent,
    KeyReleaseEvent,
    FocusEvent,
    ModifiersEvent,
    MouseClickEvent,
    PasteEvent,
    ResizeEvent,
    WakeEvent,
)
from navkit.reactive import flush_effects
from navkit.tooltip import ShowTooltip, Tooltip
from navkit import commands
from navkit.widget import Widget, _call
from navkit.application import (
    MIDDLE_PASTE_WINDOW,
    Repeat,
    TOOLTIP_FOLLOW_ON,
    TOOLTIP_FOLLOW_ON_DELAY,
    _Tick,
    _is_plain_motion,
    describe_event,
)

# The surface is a stub with no module of its own, by design (navml.surface).
# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from navkit.application_surface import Application as _Base
else:
    from navkit.widget import Mixin as _Base


class Dispatch(_Base):
    """The event loop -- dispatch a batch, run its effects, paint -- and delivering the mouse: hover,"""

    # -- event loop ---------------------------------------------------------

    async def _main_loop(self) -> None:
        self._flush_effects()
        await self._paint()
        while self._running:
            event = await self._events.get()
            batch = [id(event)]
            event = self._unmirror(event)
            self.handling_since, self.handling = time.monotonic(), describe_event(event)
            await self._handle(event)
            # Drain whatever else arrived in the meantime: a paste or a mouse
            # drag should cost one frame, not one frame per event.  A handler
            # that awaits lets the loop's other work run -- reading input,
            # pty output, timers -- but cannot produce a frame, because
            # ``_render`` is only ever awaited from here.
            while self._running and not self._events.empty():
                event = self._events.get_nowait()
                batch.append(id(event))
                await self._handle(self._unmirror(event))
            if self._running:
                self._flush_effects()
            if self._running and self._dirty:
                await self._paint()
            self._posted.difference_update(batch)
            self.handling_since = None

    async def _paint(self) -> None:
        """:meth:`_render`, where a failure always stops the application.

        A widget's own ``render`` failing is caught in
        :meth:`Widget.render_tree` and reported without stopping anything; what
        reaches here is the frame machinery itself, and a box could not be
        painted over it.
        """
        try:
            await self._render()
        except Exception as error:
            self.fail(error, fatal=True)
            raise

    def _flush_effects(self) -> None:
        """Run the reactions this batch of events queued, before painting.

        Effects assign reactive attributes, so they belong here rather than
        inside :meth:`_render`: whatever they change is part of the frame that
        is about to be composed.  A failing reaction goes to :meth:`fail`
        the same way a failing event handler does.
        """
        # Again after a failure that was reported: the effects queued behind
        # the one that failed are owed this frame too.  Each pass consumes the
        # failing one, and the storm guard ends a run of them.
        while True:
            try:
                flush_effects()
                return
            except Exception as error:
                if not self.fail(error):
                    raise

    async def _handle(self, event: Event) -> None:
        if isinstance(event, WakeEvent):
            return
        if not isinstance(event, _Tick):
            # Input, or anything posted, may change what lies beneath the
            # modal without a widget there asking: the focus path's key bar,
            # a command enabled by a field.  Only a timer's tick is trusted to
            # say through invalidate() what it changed.
            self._below_dirty = True
            self._damage = None
        if not isinstance(event, _Tick | ModifiersEvent) and not (
            isinstance(event, MouseClickEvent) and _is_plain_motion(event)
        ):
            self.recent_events.append((time.time(), describe_event(event)))
        if isinstance(event, _Tick):
            await self._tick(event.repeat)
            return
        if isinstance(event, ResizeEvent):
            self._resize(event.width, event.height)
        if isinstance(event, FocusEvent):
            # A fact about the terminal's window, kept the same way.
            self.terminal_focused = event.focused
            return
        if isinstance(event, ModifiersEvent):
            # A fact about the keyboard rather than something to act on, kept
            # the way the pointer's position is: nothing is offered it.
            self.modifiers = event.modifiers
            return
        if isinstance(event, PasteEvent) and self._hold_paste(event):
            return
        if (isinstance(event, MouseClickEvent) and event.button == "middle"
                and not isinstance(event, (DoubleClickEvent, ContextMenuEvent))):
            if event.action == "press":
                self._middle_down = True
            elif event.action == "release":
                if not self._middle_down:
                    await self._lone_middle_release(event)
                self._middle_down = False
        # Any input takes a tooltip away, shown or waiting; only the pointer
        # coming to rest (below) asks for one again.  The pointer moving off
        # one shown keeps the next quick; anything else makes it wait again.
        motion = isinstance(event, MouseClickEvent) and _is_plain_motion(event)
        if motion and self._tooltip is not None:
            self._tooltip_warm_until = time.monotonic() + TOOLTIP_FOLLOW_ON
        elif not motion:
            self._tooltip_warm_until = 0.0
        self._drop_tooltip()
        if isinstance(event, KeyEvent) and not self.chord and self._is_show_tooltip(event):
            # Read off the application's own table even past a modal, which
            # that table otherwise stands aside for: a dialog is where it is
            # most wanted.
            self.show_focus_tooltip()
            return
        # Saved and restored rather than set and cleared: `_handle' returns
        # early for a claimed event and re-enters itself for a double click,
        # so a plain reset would report "not dispatching" while the outer call
        # still is.
        if isinstance(event, MouseClickEvent):
            self.pointer = (event.x, event.y)
        if isinstance(event, MouseClickEvent) and _is_plain_motion(event):
            # The pointer moving with no button held.  A fact the application
            # keeps rather than an event anybody is offered: mode 1003 reports
            # one per cell crossed, every existing ``on_mouse_click`` was
            # written for presses, releases and drags, and all a motion can
            # mean on its own is "the pointer is here now".
            self._hover(event)
            if self.tooltip_delay > 0:
                delay = self.tooltip_delay / 1000
                if time.monotonic() < self._tooltip_warm_until:
                    delay = min(delay, TOOLTIP_FOLLOW_ON_DELAY)
                self._tooltip_timer = self.call_later(delay, self._show_tooltip)
            return
        dispatching, self._dispatching = self._dispatching, True
        try:
            tap = self.input_tap
            if tap is not None and isinstance(event, (KeyEvent, PasteEvent)):
                tap(event)
            if await self.on_event(event):
                return
            if isinstance(event, KeyEvent):
                # A Hebrew or Arabic letter under a modifier is offered as
                # typed first, everywhere -- a translated menu's Alt+ק -- and
                # only if nothing took it as the Latin key in its place, so
                # Alt+ס still quits (KeyEvent.base).
                if not await self._deliver_key(event) and event.base is not None:
                    await self._deliver_key(event.as_base())
            elif isinstance(event, MouseClickEvent):
                # Counted from the press itself, before it is delivered and
                # whatever claims it: whether a widget consumed a press says
                # nothing about whether the user clicked twice.  A
                # DoubleClickEvent is a conclusion *about* presses and is
                # never counted as one, which bounds the recursion below at
                # one level.
                derived = isinstance(event, (DoubleClickEvent, ContextMenuEvent))
                clicks = 0 if derived else self._clicks.press(event, self._now())
                # Taken before delivery: a press that grabs the mouse (a
                # drag starting) is not asking for a menu.
                captured_before = self._capture is not None
                # A press says where the pointer is as well, which keeps the
                # hover right on a terminal that never reports plain motion.
                if event.action == "press":
                    self._hover(event)
                await self._deliver_mouse(event)
                if clicks == 2:
                    # Inline rather than posted, so cause and effect stay
                    # adjacent: the press's own release is usually already in
                    # the queue from the same read, and queueing would deliver
                    # it in between.  Through `_handle' so `on_event' sees it,
                    # as it sees the escape key navkit manufactures.
                    await self._handle(DoubleClickEvent.of(event))
                if (
                    not derived
                    and event.button == "right"
                    and event.action == "press"
                    and not captured_before
                    and self._capture is None
                ):
                    # After the press and inline, as the double-click is:
                    # whoever gives the right button a meaning of its own has
                    # had it, and a press that took the capture declines.
                    await self._handle(ContextMenuEvent.of(event))
            elif isinstance(event, KeyReleaseEvent):
                # The focused widget alone, and no key table or walk up: a
                # release means something only to whoever took the press.
                # Inside the modal, as a key would be, so a dialog that opened
                # between press and release does not hand it to what is under.
                focused = self.focused
                if focused is not None and (self.modal is None or self.modal._holds(focused)):
                    handler = getattr(focused, event.handler, None)
                    if handler is not None:
                        await _call(focused, event, handler)
            elif isinstance(event, ResizeEvent):
                await self.on_resize(event)
            elif isinstance(event, PasteEvent):
                if event.origin == "answer":
                    if not self._clipboard_asked:
                        return  # too late: the private copy went instead
                    self._clipboard_asked = False
                # The application first, as with a key, and then where the
                # keyboard is -- the modal's focused line, under a dialog.
                if not await self.on_paste(event):
                    target = self.modal or self._root
                    if target is not None:
                        await target.dispatch_paste(event)
                if event.origin == "private" and not self._clipboard_hinted:
                    self._clipboard_hinted = True
                    self.clipboard_unavailable()
            else:
                # Anything posted that the four branches above do not know.
                # It has no sender in the widget tree -- nobody emitted it --
                # so it stops here, at the hook its own class names.  A widget's
                # event goes the other way, through ``Widget.emit``.
                handler = getattr(self, event.handler, None)
                # A bare ``Event`` derives ``on_event``, which every event has
                # already been offered to above; the hooks are only distinct
                # when the names are.
                if handler is not None and handler != self.on_event:
                    await _call(self, event, handler)
        except Exception as error:
            if not self.fail(error):
                raise
        finally:
            self._dispatching = dispatching

    async def _tick(self, repeat: Repeat) -> None:
        """Run one tick of *repeat*, as a handler: failure stops the app.

        A cancelled one is skipped here as well as at the timer, because its
        tick may already have been queued when its owner let go of it.
        """
        if repeat.cancelled:
            return
        if repeat.once:
            repeat.cancel()
        dispatching, self._dispatching = self._dispatching, True
        try:
            await repeat.callback()
        except Exception as error:
            if not self.fail(error):
                raise
        finally:
            self._dispatching = dispatching

    def _now(self) -> float:
        """The loop's clock, or a real one when there is no loop yet.

        Not ``_render``'s fallback of ``0.0``: a frame stamped "long ago" is
        the right default there, but two presses both stamped ``0.0`` are a
        double-click by the rule, so a test calling :meth:`_handle` directly
        would manufacture one out of nothing.  ``monotonic()`` is the clock
        asyncio's own is built on, and is always there.
        """
        return self._loop.time() if self._loop is not None else time.monotonic()

    async def _deliver_mouse(self, event: MouseClickEvent) -> None:
        """Offer *event* to this application's own hook, then to the tree.

        Looked up under ``event.handler`` for the reason
        :meth:`Widget.dispatch_mouse` does it: ``on_mouse_click`` is what a plain
        ``MouseClickEvent`` derives, so this is the call that was always made, and
        a refinement reaches its own hook or goes straight past the
        application to the widgets.
        """
        hook = getattr(self, event.handler, None)
        if hook is None or not await _call(self, event, hook):
            await self._dispatch_mouse(event)

    # -- tooltips ---------------------------------------------------------------

    def tooltip_here(self) -> str:
        """The tooltip for where the pointer is, or ``""``.

        Asked of the widget under the pointer (:attr:`hovered`) and then its
        ancestors, nearest first, each in its own coordinates
        (:meth:`Widget.tooltip_at`): a widget without one shows what it sits
        in says -- unless it is one that stops the walk
        (:attr:`Widget.tooltip_passes`).
        """
        if self.pointer is None:
            return ""
        return self.tooltip_from(self.hovered, *self.pointer)

    @staticmethod
    def tooltip_from(widget: Widget | None, x: int, y: int) -> str:
        """The tooltip at screen cell *x*, *y*, asked of *widget* -- what is
        painted there -- and then its ancestors, nearest first, each in its
        own coordinates, until one answers or stops the walk
        (:attr:`Widget.tooltip_passes`)."""
        while widget is not None:
            ox, oy = widget.offset()
            text = widget.tooltip_at(x - ox - widget.x, y - oy - widget.y)
            if text or not widget.tooltip_passes:
                return text
            widget = widget.parent
        return ""

    async def _show_tooltip(self) -> None:
        """The pointer rested: put up what it rests on says, if anything.

        As the root's last child, over everything -- a modal too, since what
        stands after a modal is painted after it.
        """
        self._tooltip_timer = None
        text = self.tooltip_here()
        if not text or self._root is None or self.pointer is None:
            return
        self._tooltip = self.overlay(Tooltip(text, self.pointer))

    def _is_show_tooltip(self, event: KeyEvent) -> bool:
        binding = commands.key_table(type(self)).get(event.name)
        return binding is not None and isinstance(commands.command_of(binding), ShowTooltip)

    async def on_show_tooltip(self, event: ShowTooltip) -> bool:
        self.show_focus_tooltip()
        return True

    def show_focus_tooltip(self) -> bool:
        """Put up the tooltip of where the keyboard is, beside it -- the
        nearest widget on the focus path's :meth:`Widget.tooltip_anchor`,
        asked of whatever is painted there and its ancestors as the pointer
        would be.  False, showing nothing, where there is none."""
        self._drop_tooltip()
        scope = self.modal or self._root
        if scope is None or self._root is None:
            return False
        path = scope._focus_path() or [scope]
        widget = path[0]
        ax, ay = widget.tooltip_anchor()
        ox, oy = widget.offset()
        x, y = ox + widget.x + ax, oy + widget.y + ay
        # What is painted there: a descendant of the focused widget, if one
        # is (an open menu's box), else the widget itself.
        found = widget.widget_at(widget.x + ax, widget.y + ay) or widget
        text = self.tooltip_from(found, x, y)
        if not text:
            return False
        self._tooltip = self.overlay(Tooltip(text, (x, y)))
        return True

    def _drop_tooltip(self) -> None:
        """Forget the tooltip waiting to show and take down the one shown."""
        if self._tooltip_timer is not None:
            self._tooltip_timer.cancel()
            self._tooltip_timer = None
        tooltip, self._tooltip = self._tooltip, None
        if tooltip is not None and tooltip.parent is not None:
            tooltip.parent.remove(tooltip)

    # -- VTE's middle click -------------------------------------------------------
    #
    # VTE (xfce4-terminal) does not report a middle *press* under mouse
    # tracking: it pastes the primary selection itself and reports only the
    # release.  A widget that wants the middle button (a file panel tagging)
    # says so through :meth:`Widget.claims_middle_click`; a terminal paste
    # while the pointer rests on such a spot is held for a moment, and a lone
    # middle release there turns into the press it lost, the paste dropped.

    def _middle_claimer(self, x: int, y: int) -> bool:
        """Whether the widget at screen *x*, *y* (or one above it) claims the middle button."""
        if self._capture is not None:
            return False
        modal = self.modal
        if modal is not None:
            dx, dy = modal.offset()
            widget = modal.widget_at(x - dx, y - dy)
        else:
            widget = self._root.widget_at(x, y) if self._root is not None else None
        while widget is not None:
            dx, dy = widget.offset()
            if widget.claims_middle_click(x - dx - widget.x, y - dy - widget.y):
                return True
            if widget is modal:
                break
            widget = widget.parent
        return False

    def _hold_paste(self, event: PasteEvent) -> bool:
        """Hold a terminal's *event* while the pointer rests where the middle button is claimed."""
        if event is self._paste_let_go:
            self._paste_let_go = None
            return False
        if (event.origin != "terminal" or self._middle_down or self.pointer is None
                or self._held_paste is not None or not self._middle_claimer(*self.pointer)):
            return False

        async def let_go() -> None:
            self._release_held_paste()

        self._held_paste = (event, self.call_later(MIDDLE_PASTE_WINDOW, let_go))
        return True

    def _release_held_paste(self) -> None:
        """The held paste was a paste after all: deliver it."""
        held, self._held_paste = self._held_paste, None
        if held is not None:
            held[1].cancel()
            self._paste_let_go = held[0]
            self.post_event(held[0])

    async def _lone_middle_release(self, event: MouseClickEvent) -> None:
        """A middle release with no press: VTE pasted instead of reporting it."""
        if self._middle_claimer(event.x, event.y):
            if self._held_paste is not None:
                self._held_paste[1].cancel()
                self._held_paste = None
            await self._handle(dataclasses.replace(event, action="press"))
        else:
            self._release_held_paste()

    def _hover(self, event: MouseClickEvent) -> None:
        """Move :attr:`hovered` to whatever is under *event*'s position.

        Confined to the modal the way delivery is: outside it nothing is
        hovered, because nothing out there is reachable.
        """
        if self._capture is not None:
            return
        modal = self.modal
        if modal is not None:
            dx, dy = modal.offset()
            self.hovered = modal.widget_at(event.x - dx, event.y - dy)
        elif self._root is not None:
            self.hovered = self._root.widget_at(event.x, event.y)

    async def _dispatch_mouse(self, event: MouseClickEvent) -> None:
        """Route a mouse action into the tree, or into the modal alone.

        The mouse is where modality costs something, because it routes by
        position rather than by focus: every widget under the pointer is on
        the path, whether or not it is supposed to be reachable. So the event
        is moved into the modal's parent's frame and offered there, and one
        that lands outside the modal reaches nothing at all -- not the widgets
        underneath, and not the modal either, whose coordinates it is not in.

        Dismissing on an outside click is a *policy*, and belongs to whatever
        widget wants it: a press that misses the modal is offered to the modal
        itself as a :class:`ClickOutsideEvent`, and what it does then is its
        own business.
        """
        capture = self._capture
        if capture is not None:
            dx, dy = capture.offset()
            local = event.translated(-dx - capture.x, -dy - capture.y)
            hold = self._hold
            try:
                if (
                    hold is not None
                    and hold.widget is capture
                    and event.action in ("move", "release")
                    and not isinstance(event, (DoubleClickEvent, ContextMenuEvent))
                ):
                    if event.action == "move":
                        await hold._moved(local.x, local.y)
                else:
                    handler = getattr(capture, event.handler, None)
                    if handler is not None:
                        await _call(capture, local, handler)
            finally:
                if event.action == "release" and self._capture is capture:
                    self._set_capture(None)
            return
        modal = self.modal
        if modal is None:
            if self._root is not None:
                await self._root.dispatch_mouse(event)
            return
        dx, dy = modal.offset()
        local = event.translated(-dx, -dy)
        if modal.contains(local.x, local.y):
            await modal.dispatch_mouse(local)
        elif (
            event.action == "press"
            and not event.is_wheel
            and not isinstance(event, (DoubleClickEvent, ContextMenuEvent))
        ):
            outside = ClickOutsideEvent.of(local).translated(-modal.x, -modal.y)
            handler = getattr(modal, outside.handler, None)
            if handler is not None:
                await _call(modal, outside, handler)
