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

from navkit.commands import Command
from navkit.events import Event
from navkit.reactive import effect, reactive, untracked
from navkit.widget import Widget

from navml.commands import (
    CloseWindow,
    NextWindow,
    PreviousWindow,
    SizeMoveWindow,
    ZoomWindow,
)
from navml.widgets.window import Window


class EmptiedEvent(Event):
    """The last window on a desktop was closed."""


class Desktop(Widget):
    """The layer windows live on."""

    emits = (EmptiedEvent,)

    #: The window keys, checked against DOS Navigator's own *Window* menu
    #: (``dlgMainMenu`` in ``DN.DNR``): Size/Move Ctrl-F5, Zoom Alt-Z, Close
    #: Ctrl-F4.  Its Next and Previous are Alt-Tab and Ctrl-Tab, which a
    #: terminal cannot deliver -- the window manager takes the one, and the
    #: other arrives as a plain Tab -- so those two keep Ctrl-F6 and
    #: Ctrl-Shift-F6.  Consulted after the active window's own children,
    #: because this desktop is further from the focus than they are.
    keys = {
        "ctrl+f5": SizeMoveWindow,
        "alt+z": ZoomWindow,
        "ctrl+f6": NextWindow,
        "ctrl+shift+f6": PreviousWindow,
        "ctrl+f4": CloseWindow,
    }

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

    # -- commands ------------------------------------------------------------

    def enables(self, command: Command) -> bool:
        """Every window command needs a window, and two need its consent."""
        window = self.active_window
        if window is None:
            return False
        if isinstance(command, ZoomWindow):
            return window.zoomable
        if isinstance(command, CloseWindow):
            return window.closable
        return True

    async def on_size_move_window(self, event: SizeMoveWindow) -> bool:
        self.active_window.begin_move()
        return True

    async def on_zoom_window(self, event: ZoomWindow) -> bool:
        self.active_window.toggle_zoom()
        return True

    async def on_next_window(self, event: NextWindow) -> bool:
        self.next_window()
        return True

    async def on_previous_window(self, event: PreviousWindow) -> bool:
        self.previous_window()
        return True

    async def on_close_window(self, event: CloseWindow) -> bool:
        self.active_window.close()
        return True
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
