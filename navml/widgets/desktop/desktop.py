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

**Tile and Cascade are DOS Navigator's own arithmetic**, ported from
``TDesktop.Tile`` and ``TDesktop.Cascade`` in ``DNAPP.PAS`` rather than
invented: they arrange every ``tileable`` window (all of them unless one
opts out -- a deliberate departure from ``ofTileable``'s opt-in), count
the bottom one first, and leave the z-order alone.

A desktop never holds a modal.  A modal is overlaid on the application's
root, which is a level above this, so no window can be raised past one.
"""

from __future__ import annotations

import math
from typing import Any

from navkit.commands import Command
from navkit.events import Event
from navkit.reactive import effect, reactive, untracked
from navkit.widget import Widget

from navml.commands import (
    CascadeWindows,
    CloseAllWindows,
    CloseWindow,
    NextWindow,
    PreviousWindow,
    SizeMoveWindow,
    TileWindows,
    WindowManager,
    ZoomWindow,
)
from navml.widgets.window import Window


class OpenedEvent(Event):
    """A window was opened on a desktop.

    Whoever can hide the desktop listens for it, so that a window opened while
    the desktop is out of sight is brought into view by being opened -- not by
    every command that opens one remembering to.
    """


class EmptiedEvent(Event):
    """The last window on a desktop was closed."""


def _most_equal_divisors(n: int, favor_y: bool) -> tuple[int, int]:
    """Columns and rows for *n* tiles: ``MostEqualDivisors``, favouring rows."""
    i = math.isqrt(n)
    if n % i and n % (i + 1) == 0:
        i += 1
    i = max(i, n // i)
    return (n // i, i) if favor_y else (i, n // i)


def _divider(lo: int, hi: int, num: int, pos: int) -> int:
    """Where the *pos*-th of *num* equal parts of *lo*..*hi* starts: ``DividerLoc``."""
    return (hi - lo) * pos // num + lo


class Desktop(Widget):
    """The layer windows live on."""

    emits = (OpenedEvent, EmptiedEvent)

    #: The window keys, checked against DOS Navigator's own *Window* menu
    #: (``dlgMainMenu`` in ``DN.DNR``): Size/Move Ctrl-F5, Zoom Alt-Z, Close
    #: Ctrl-F4.  Its menu gives Next and Previous as Alt-Tab and Ctrl-Tab,
    #: which a terminal cannot deliver -- the window manager takes the one, and
    #: the other arrives as a plain Tab -- so they take the keys its status
    #: lines bind ``cmNext`` and ``cmPrev`` to everywhere, F9 and Shift-F9.
    #: That leaves Ctrl-F6 for DOS Navigator's Calculator.  Alt-0 is the same
    #: menu's *List*, ``cmWindowManager``.  Tile, Cascade and Close all have no
    #: key, because the original gave them none.  Consulted after the
    #: active window's own children, because this desktop is further from the
    #: focus than they are.
    keys = {
        "ctrl+f5": SizeMoveWindow,
        "alt+z": ZoomWindow,
        "f9": NextWindow,
        "shift+f9": PreviousWindow,
        "ctrl+f4": CloseWindow,
        "alt+0": WindowManager,
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
        """Put *window* on top of the others and give it the keyboard.

        Raises :class:`OpenedEvent` once the application is running -- a
        window opened while the tree is being built has nothing to announce.
        """
        self.add(window)
        if self.is_mounted:
            window.layout(self.width, self.height)
        self.activate(window)
        app = self.application
        if app is not None and app.is_running:
            self.spawn(self.emit(OpenedEvent()))
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
        if saved is window and window._holds_keyboard:
            # Held only for want of anything else: ask again, in case there is.
            saved = None
        if saved is not None and saved.is_mounted and window._holds(saved) and saved.focus():
            return
        if window._holds(app.focused):
            return
        window.take_keyboard()

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

    def tileable_windows(self) -> list[Window]:
        """The windows Tile and Cascade arrange, bottom to top."""
        return [w for w in self.windows() if w.tileable and w.visible]

    def tile(self) -> None:
        """Window > Tile: share the desktop out between the tileable windows.

        More rows than columns, as DOS Navigator's ``TileColumnsFirst`` was
        never set -- two windows lie one above the other -- and the columns a
        grid cannot fill evenly, the rightmost ones, take a row more.  The
        bottom window gets the top-left tile.  A desktop too small for the
        grid is left as it was, which is all ``TileError`` ever did.
        """
        windows = self.tileable_windows()
        count = len(windows)
        if not count:
            return
        width, height = self.width, self.height
        cols, rows = _most_equal_divisors(count, favor_y=True)
        if width // cols == 0 or height // rows == 0:
            return
        left_over = count % cols
        even = (cols - left_over) * rows
        for pos, window in enumerate(windows):
            if pos < even:
                col, row, col_rows = pos // rows, pos % rows, rows
            else:
                col = (pos - even) // (rows + 1) + cols - left_over
                row, col_rows = (pos - even) % (rows + 1), rows + 1
            x = _divider(0, width, cols, col)
            y = _divider(0, height, col_rows, row)
            window.locate(
                x, y,
                _divider(0, width, cols, col + 1) - x,
                _divider(0, height, col_rows, row + 1) - y,
            )

    def cascade(self) -> None:
        """Window > Cascade: every tileable window a cell down and right of
        the one under it, **all the same size**.

        A departure from ``TDesktop.Cascade``, which kept every window's
        bottom-right corner on the desktop's, so each one lower in the stack
        was larger and, raised, covered every window above it.  Here the size
        is the desktop's less the steps the stack takes, so only the top
        window reaches the corner, and a window brought forward still leaves
        the edges of the ones above it showing.  Left alone when that size
        is below some window's minimum -- ``TileError`` was empty.
        """
        windows = self.tileable_windows()
        if not windows:
            return
        steps = len(windows) - 1
        width, height = self.width - steps, self.height - steps
        if any(w.min_width > width or w.min_height > height for w in windows):
            return
        for offset, window in enumerate(windows):
            window.locate(offset, offset, width, height)

    def close_all(self) -> None:
        """Window > Close all: close every window that has a close icon.

        ``cmClearDesktop`` broadcast ``cmClose``, which a window without one
        ignores.  Closed front to back, and the last to go raises
        :class:`EmptiedEvent` as a single close would.
        """
        for window in reversed(self.windows()):
            if window.closable:
                window.close()

    # -- commands ------------------------------------------------------------

    def enables(self, command: Command) -> bool:
        """Every window command needs a window, and two need its consent.

        Tile and Cascade need a window that is tileable, and Close all one that
        is closable, wherever it is in the stack.
        """
        if isinstance(command, (TileWindows, CascadeWindows)):
            return bool(self.tileable_windows())
        if isinstance(command, CloseAllWindows):
            return any(window.closable for window in self.windows())
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

    async def on_tile_windows(self, event: TileWindows) -> bool:
        self.tile()
        return True

    async def on_cascade_windows(self, event: CascadeWindows) -> bool:
        self.cascade()
        return True

    async def on_close_all_windows(self, event: CloseAllWindows) -> bool:
        self.close_all()
        return True

    async def on_window_manager(self, event: WindowManager) -> bool:
        # Started, not awaited: a handler that waits for a dialog holds the
        # loop that would paint it.
        self.spawn(self.window_manager())
        return True

    async def window_manager(self) -> None:
        """Alt+0: *Windows Manager*, and the window chosen in it comes forward.

        Activated only once the dialog is down, so the keyboard goes to the
        window rather than staying with the modal.  With no window worth
        listing nothing opens, as in ``COLORS.PAS``.
        """
        from navml.widgets.window_manager import WindowManagerDialog

        dialog = WindowManagerDialog(desktop=self)
        if not dialog.windows.items:
            return
        chosen = await dialog.execute(self.application)
        if chosen is not None and chosen in self.windows():
            self.activate(chosen)

    async def on_close_window(self, event: CloseWindow) -> bool:
        self.active_window.close()
        return True
