"""Modal and overlay, mouse capture, focus, and posting events from anywhere.

A mixin of :class:`~navkit.application.Application` (:class:`navkit.widget.Mixin`):
methods only; its state, keys and ``checks`` are in ``navkit/application.py``.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from navkit.events import Event, WakeEvent
from navkit.widget import Widget
from navkit.application import MouseHold, _Tick

# The surface is a stub with no module of its own, by design (navml.surface).
# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from navkit.application_surface import Application as _Base
else:
    from navkit.widget import Mixin as _Base


class Focus(_Base):
    """Modal and overlay, mouse capture, focus, and posting events from anywhere."""

    # -- modal and overlay ---------------------------------------------------

    @property
    def modal(self) -> Widget | None:
        """The widget holding all input, or None.  The innermost, if nested.

        Maintained by the mount walks rather than by a caller: a widget whose
        :attr:`Widget.modal` is set claims the input when it is mounted and
        releases it when it is unmounted, so every route out of the tree --
        ``remove()``, a replaced root, an ancestor going with it -- gives the
        input back without anybody remembering to.  A plain property over a
        plain list: nothing derives from it reactively yet, and a widget that
        wants to *look* different while it is blocked can be given a computed
        when something actually asks for one.
        """
        return self._modals[-1][0] if self._modals else None

    def overlay(self, widget: Widget) -> Widget:
        """Put *widget* on top of everything, and return it.

        The last child of the root: rendering walks children forwards and
        hit-testing backwards, so last is on top and asked first.  A widget
        deep in the tree opens one with ``self.application.overlay(dialog)``,
        which is the point -- where a dialog is *created* has nothing to do
        with where it belongs on the screen.

        Closing it is ``app.root.remove(dialog)``, which already unmounts the
        subtree, disposes its effects, releases the input if it was modal and
        hands the focus back to whatever had it.
        """
        if self._root is None:
            raise RuntimeError("no root widget to put an overlay on")
        return self._root.add(widget)

    # -- mouse capture -------------------------------------------------------

    @property
    def mouse_capture(self) -> Widget | None:
        """The widget holding the mouse, or None."""
        return self._capture

    def capture_mouse(self, widget: Widget) -> None:
        """Send every mouse action to *widget* until the button is released.

        What a drag needs.  Routing is by position, and a pointer dragging a
        window's edge is routinely *outside* the window by the time the
        terminal reports it -- a fast hand, or a resize the window refuses
        past its minimum -- so without this the drag stops the moment the
        pointer outruns what it is dragging.  While held, an action is
        delivered straight to *widget*'s handler in its own coordinates, with
        no hit test; the application's own hook still sees it first.

        Released by itself after a ``release`` is delivered, when *widget* is
        unmounted, and when a modal opens that does not hold it.
        """
        self._set_capture(widget)

    @property
    def mouse_hold(self) -> MouseHold | None:
        """The held button repeating, or None."""
        return self._hold

    def release_mouse(self) -> None:
        """Let the mouse route by position again."""
        self._set_capture(None)

    def _set_capture(self, widget: Widget | None) -> None:
        """The one place the capture changes, so a hold never outlives it."""
        hold = self._hold
        self._capture = widget
        if hold is not None and (widget is None or hold.widget is not widget):
            self._hold = None
            hold.cancel()

    def _push_modal(self, widget: Widget) -> None:
        """Called by the mount walk.  Remembers what had the focus."""
        self._below_dirty = True
        self._damage = None
        # Something else is under the pointer now, so a press before this and
        # one after it are not two clicks on one thing.
        self._clicks.reset()
        if self._capture is not None and not widget._holds(self._capture):
            self._set_capture(None)
        self._modals.append((widget, self.focused))

    def _pop_modal(self, widget: Widget) -> None:
        """Called by the unmount walk.  Hands the focus back if it was on top.

        A modal that is not the top one -- removed out of order, or carried
        off with an ancestor -- simply leaves the stack: the focus belongs to
        whatever is still holding the input, not to the thing behind it.
        """
        self._clicks.reset()  # as `_push_modal': the cell changed meaning
        self._below_dirty = True
        self._damage = None
        for index, (held, restore) in enumerate(self._modals):
            if held is not widget:
                continue
            del self._modals[index]
            if index == len(self._modals):
                self.focused = None
                if restore is not None and restore.is_mounted:
                    restore.focus()
            return

    def _claim_focus(self) -> None:
        """Put the focus inside the active modal, if it is not there already.

        Run once a subtree has finished mounting, so a modal is choosing from
        children that exist. A modal with nothing focusable in it takes the
        focus away rather than leaving it outside, where it would keep a
        widget the user can no longer reach looking like the live one.
        """
        modal = self.modal
        if modal is None or (self.focused is not None and modal._holds(self.focused)):
            return
        order = modal.focusable()
        # A modal may name where the keyboard goes first (navml's
        # ``first_focus``); one it cannot reach falls back to the tab order.
        wanted = getattr(modal, "first_focus", None)
        self.focused = wanted if wanted in order else order[0] if order else None

    def focus_next(self, reverse: bool = False) -> Widget | None:
        """Move focus along the tab order, wrapping.  The new holder, or None.

        The order is ``root.focusable()`` -- visible, focusable widgets in tree
        order -- or the active modal's, which is the whole of what makes a
        dialog's Tab stay inside the dialog.  Taken fresh each time rather than kept, because the tree is
        reactive and a cached order would be wrong the moment a widget is
        added, hidden or disabled; the walk is over the tree an event loop
        already repaints in full.

        A focus that is no longer in the order -- the widget was hidden, or
        removed -- does not stop the move: the search starts from the end it
        came from, so Tab out of a vanished widget lands on the first one.
        """
        scope = self.modal or self._root
        order = scope.focusable() if scope is not None else []
        if not order:
            return None
        if self.focused in order:
            index = order.index(self.focused) + (-1 if reverse else 1)
        else:
            index = -1 if reverse else 0
        self.focused = order[index % len(order)]
        return self.focused

    def post_event(self, event: Event) -> None:
        """Queue *event* as if it had arrived from the terminal.

        The event joins the current batch, so it is dispatched before the next
        frame rather than after it.
        """
        if not isinstance(event, _Tick | WakeEvent):
            self._posted.add(id(event))
        self._events.put_nowait(event)

    def call_from_thread(self, callback: Callable[..., Any], *args: Any) -> None:
        """Run *callback* on the loop, from any thread, then let it paint.

        The one way for a thread that is not the loop's -- a file-system
        watcher, say -- to reach the widgets: it queues the call and returns
        at once.  Dropped while no loop is running, or once it has closed, so
        a thread outliving the application has nothing to fail over.
        """
        loop = self._loop
        if loop is None or not self._running:
            return

        def run() -> None:
            callback(*args)
            self.post_event(WakeEvent())

        with contextlib.suppress(RuntimeError):  # the loop has closed
            loop.call_soon_threadsafe(run)
