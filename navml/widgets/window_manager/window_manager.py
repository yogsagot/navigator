"""The handlers behind ``window_manager.nml``: what the buttons do.

``WindowManager`` in ``COLORS.PAS`` ran the dialog in a loop.  OK selected the
window under the cursor.  Close (``cmNo``) freed it, if it agreed to close,
listed the desktop again and **went round again**, with the cursor on the same
row or on the one above if that row had gone.  The last window closing ended
the dialog.  Here the loop is the dialog staying up: :meth:`close_selected`
lists the desktop again in place, and ``ListViewer``'s clamp puts the cursor
back on a row.

Cancel needs no handler: ``Dialog.on_click`` dismisses for any button nobody
claimed.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event
from navkit.reactive import effect

from navml.widgets.dialog.dialog import Dialog


class WindowManagerDialog(Dialog):
    """*Windows Manager*: the windows on *desktop*, top first."""

    def __init__(self, desktop: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Dialog's bottom row and message are not in this layout.
        self.row.visible = False
        self.message.visible = False
        #: The desktop whose windows are listed.
        self.desktop = desktop
        self.refresh()

    def mounted(self) -> None:
        super().mounted()
        effect(self, WindowManagerDialog._close_follows_window)

    def _close_follows_window(self) -> None:
        """Close is greyed while the window under the cursor will not close."""
        window = self.windows.selected
        self.shut.disabled = window is None or not window.closable

    def refresh(self) -> None:
        """List the desktop's visible windows again, top first."""
        windows = [] if self.desktop is None else self.desktop.windows()
        self.windows.show([w for w in reversed(windows) if w.visible])

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        """This dialog's own buttons, which the tab order puts after the list."""
        return (self.pick, self.shut, self.abandon, self.helper)

    def accept(self) -> Any:
        """The window under the cursor."""
        return self.windows.selected

    def close_selected(self) -> None:
        """Close the window under the cursor, and stay up while any are left."""
        window = self.accept()
        if window is None or not window.closable:
            return
        if window.must_ask():
            self.spawn(self._close_asking(window))
            return
        window.close()
        self._closed()

    async def _close_asking(self, window: Any) -> None:
        if await window.close_asking():
            self._closed()

    def _closed(self) -> None:
        self.refresh()
        if not self.windows.items:
            self.close(None)
            return
        self.windows.focus()

    # -- the buttons -----------------------------------------------------------

    async def on_pick_click(self, event: Event) -> bool:
        self.close(self.accept())
        return True

    async def on_windows_chosen(self, event: Any) -> bool:
        """Enter in the list is OK."""
        self.close(self.accept())
        return True

    async def on_shut_click(self, event: Event) -> bool:
        self.close_selected()
        return True
