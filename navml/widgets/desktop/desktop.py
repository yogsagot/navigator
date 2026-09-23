"""The layer windows live on: their z-order, and which one is active.

Turbo Vision's ``TDeskTop``, less the background: **a desktop paints
nothing**, so whatever is behind it -- in Navigator, the console -- shows
between the windows, and a click on bare background falls through to it,
because nothing here claims one.

**The z-order is the order of the children**, which navkit already paints
forwards and hit-tests backwards; bringing a window forward is
:meth:`~navkit.widget.Widget.raise_child`, a reorder and never a re-add, so
the window stays mounted and keeps its keyboard.  :attr:`active_window`
exists because the children list is not reactive -- it is the top window,
and the one thing every window's ``:active`` state reads.

**The focus travels with the activation, in the same call.**  Each window
remembers what had the keyboard when it went to the back and gets it again
when it comes forward.  Done here rather than from an effect for the reason
``toggle_console`` gives: an effect runs after the whole batch, and a key
arriving in the same batch as the click would be routed by a focus that had
not moved yet.

A desktop never holds a modal.  A modal is overlaid on the application's
root, which is a level above this, so no window can be raised past one.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event, KeyEvent
from navkit.reactive import effect, reactive, untracked
from navkit.widget import Widget

from navml.widgets.window import Window


class EmptiedEvent(Event):
    """The last window on a desktop was closed."""


#: The window keys, and what each one does to the active window.  One table so
#: that the bindings can be checked against DOS Navigator's own menus in one
#: place; Turbo Vision's F5 and F6 are Copy and Move in the panels, so the
#: zoom and next-window keys take a modifier.
WINDOW_KEYS = {
    "ctrl+f5": "move",
    "shift+f5": "zoom",
    "ctrl+f6": "next",
    "ctrl+shift+f6": "previous",
    "alt+f3": "close",
}


class Desktop(Widget):
    """The layer windows live on."""

    emits = (EmptiedEvent,)

    #: The top window, which has the keyboard.  None on an empty desktop.
    active_window: Any = reactive(None)

    def mounted(self) -> None:
        super().mounted()
        # A desktop's size is bound by whoever placed it, so a resize reaches
        # it as a changed value rather than as a ``layout()`` call -- a markup
        # parent does not cascade.  Every window is re-fitted from here: the
        # zoomed ones fill the new size, the others are pulled back onto it.
        effect(self, Desktop._fit_windows)
        if self.active_window is not None:
            self.activate(self.active_window)

    def _fit_windows(self) -> None:
        width, height = self.width, self.height
        with untracked():
            for window in self.windows():
                window.layout(width, height)

    def windows(self) -> list[Window]:
        """The windows on this desktop, bottom to top."""
        return [child for child in self.children if isinstance(child, Window)]

    # -- opening, raising, closing -------------------------------------------

    def open(self, window: Window) -> Window:
        """Put *window* on top of the others and give it the keyboard."""
        self.add(window)
        if self.is_mounted:
            window.layout(self.width, self.height)
        self.activate(window)
        return window

    def activate(self, window: Window) -> None:
        """Bring *window* forward and hand it back the keyboard it had."""
        app = self.application
        previous = self.active_window
        if (
            previous is not None
            and previous is not window
            and app is not None
            and previous._holds(app.focused)
        ):
            previous._saved_focus = app.focused
        self.raise_child(window)
        self.active_window = window
        if app is None or not self.is_mounted:
            return
        if app.modal is not None and not app.modal._holds(window):
            # A modal is up: the window comes forward, the keyboard stays.
            return
        saved = window._saved_focus
        if saved is not None and saved.is_mounted and window._holds(saved) and saved.focus():
            return
        if window._holds(app.focused):
            return
        order = window.focusable()
        if order:
            order[0].focus()
        else:
            app.focused = None

    def close_window(self, window: Window) -> None:
        """Take *window* off, and give the keyboard to the one under it."""
        if window not in self.children:
            return
        was_active = window is self.active_window
        self.remove(window)
        if not was_active:
            return
        self.active_window = None
        remaining = self.windows()
        if remaining:
            self.activate(remaining[-1])
            return
        app = self.application
        if app is not None and app.is_running:
            self.spawn(self.emit(EmptiedEvent()))

    def next_window(self) -> None:
        """Bring the bottom window to the top: repeated, it visits them all."""
        windows = self.windows()
        if len(windows) > 1:
            self.activate(windows[0])

    def previous_window(self) -> None:
        """Send the top window to the bottom, and activate the one under it."""
        windows = self.windows()
        if len(windows) > 1:
            self.lower_child(windows[-1])
            self.activate(self.windows()[-1])

    # -- keys ----------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        """The window keys, reached after the active window's own children."""
        window = self.active_window
        if window is None:
            return False
        for spec, action in WINDOW_KEYS.items():
            if not event.matches(spec):
                continue
            if action == "move":
                window.begin_move()
            elif action == "zoom":
                if not window.zoomable:
                    return False
                window.toggle_zoom()
            elif action == "next":
                self.next_window()
            elif action == "previous":
                self.previous_window()
            elif action == "close":
                if not window.closable:
                    return False
                window.close()
            return True
        return False
