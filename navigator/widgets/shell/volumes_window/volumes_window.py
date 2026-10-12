"""The handlers behind ``volumes_window.nml``.

The mounts are read on a thread (:func:`navigator.volumes.gather`) -- a
network mount whose server has gone can hold ``statvfs`` for as long as it
likes -- and what was read last stays listed meanwhile.  Everything is read,
real or not; *Show all mounts* only changes which are shown, so it needs no
read.  **Enter in the list is not handled here**: the list emits
``ChosenEvent`` and it walks up to the screen, the one thing that knows where
the file manager is.  *Go* is that, then closing.
"""

from __future__ import annotations

from typing import Any

from navkit.events import Event, KeyEvent
from navkit.reactive import effect, peek
from navml.background import Background, Outcome
from navml.widgets.dialog.commands import SelectNext, SelectPrevious
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.window import Window

from navigator import volumes
from navigator.widgets.manager.commands import Rescan, ToggleHidden

#: Where the window reads the mounts.
_READER = Background("nav-volumes", workers=1)


class VolumesWindow(Window):
    """The mounted volumes in a window of their own."""

    def __init__(self, show_all: bool = False, **kwargs: Any) -> None:
        """*show_all* ticks *Show all mounts*: the kernel's own file systems too."""
        super().__init__(**kwargs)
        self.show_all = show_all
        self._found: list[volumes.Volume] = []
        self._reads = 0

    @property
    def show_all(self) -> bool:
        """Whether *Show all mounts* is ticked."""
        return bool(self.everything.value & 1)

    @show_all.setter
    def show_all(self, value: bool) -> None:
        self.everything.value = 1 if value else 0

    def mounted(self) -> None:
        super().mounted()
        effect(self, VolumesWindow._follow_box)
        # Not from ``__init__``: until the window is on the desktop it has no
        # application, and ``Background`` would read on the loop instead.
        self.reload()

    def _follow_box(self) -> None:
        """The box ticked or cleared, by a key, a click or Ctrl+H: list again."""
        self.everything.value  # noqa: B018 -- what this effect follows
        self._show()

    def take_keyboard(self) -> None:
        # Not from ``mounted()``, for the reason ``TreeWindow`` gives.
        self.volumes.focus()

    def reload(self) -> None:
        """Read the mounts again, on a thread; only the newest read is listed."""
        self._reads += 1
        _READER.run(self, volumes.gather, done=lambda outcome, n=self._reads: self._read(n, outcome))

    def _read(self, read: int, outcome: Outcome) -> None:
        if read != self._reads:
            return
        try:
            self._found = outcome.result()
        except OSError:
            self._found = []
        self._show()

    def _show(self) -> None:
        """List what was read, keeping the cursor on the mount it was on.

        The list's items and cursor are peeked: ``_follow_box`` calls this,
        and an effect that read them would run again at every cursor move.
        """
        listing = self.volumes
        items = peek(listing, ListViewer.items)
        cursor = peek(listing, ListViewer.cursor)
        current = items[cursor] if 0 <= cursor < len(items) else None
        shown = [volume for volume in self._found if self.show_all or volume.real]
        listing.items = shown
        if current is not None:
            for index, volume in enumerate(shown):
                if volume.mount == current.mount:
                    listing.cursor = index
                    break

    async def go(self) -> None:
        """*Go*: the active panel to the volume under the cursor, and the window closed."""
        if await self.volumes.choose():
            self.request_close()

    # -- what the buttons and keys do ---------------------------------------------------

    async def on_rescan(self, event: Rescan) -> bool:
        self.reload()
        return True

    async def on_toggle_hidden(self, event: ToggleHidden) -> bool:
        self.show_all = not self.show_all
        return True

    async def on_go_button_click(self, event: Event) -> bool:
        await self.go()
        return True

    async def on_close_button_click(self, event: Event) -> bool:
        self.request_close()
        return True

    async def on_select_next(self, event: SelectNext) -> bool:
        self._step(1)
        return True

    async def on_select_previous(self, event: SelectPrevious) -> bool:
        self._step(-1)
        return True

    def _step(self, by: int) -> None:
        """Tab within this window, wrapping, as a dialog's Tab stays in it."""
        order = [widget for widget in self.focusable() if widget is not self]
        if not order:
            return
        app = self.application
        focused = app.focused if app is not None else None
        index = order.index(focused) if focused in order else (-1 if by > 0 else 0)
        order[(index + by) % len(order)].focus()

    async def on_key(self, event: KeyEvent) -> bool:
        """Alt and a marked letter: that control, as a dialog's ``Alt+letter`` walk."""
        if event.alt and not event.ctrl and len(event.key) == 1 and event.key.isalpha():
            for control in (self.everything, self.go_button, self.close_button):
                if control.shortcut_match(event.key):
                    return await control.activate(event.key)
        return await super().on_key(event)
