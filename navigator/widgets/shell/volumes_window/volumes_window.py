"""The handlers behind ``volumes_window.nml``.

The mounts are read on a thread (:func:`navigator.lib.system.volumes.gather`) -- a
network mount whose server has gone can hold ``statvfs`` for as long as it
likes -- and what was read last stays listed meanwhile.  Everything is read,
real or not; *Show all mounts* only changes which are shown, so it needs no
read.  **Enter in the list is not handled here**: the list emits
``ChosenEvent`` and it walks up to the screen, the one thing that knows where
the file manager is.  *Go* is that, then closing.

**Mount, Unmount and Eject** are the desktop's -- ``gio``'s or Solid's,
else udisks2's own (:func:`navigator.lib.system.desktop.volume_backend`) --
each run on a thread, its failure said in a box, the mounts read again after.
Enter or *Go* on a volume not mounted mounts it, reads again, and only then
chooses it -- with its mount point now -- for the screen.

**Mount image** and **Unmount image** are the Disk menu's (``MountImage``,
``UnmountImage``), answered here while the window is active: the first asks
for an image file (DN's ``TFileDialog``) and mounts it, the cursor going to
its row; the second unmounts the image of the row under the cursor, whole
(:mod:`navigator.widgets.drives.disk_image`).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from navkit.events import ContextMenuEvent, KeyEvent
from navkit.i18n import tr
from navkit.reactive import effect, peek
from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.dialog.tree_view import ChosenEvent
from navml.background import Background, Outcome
from navml.commands import CloseWindow
from navml.widgets.menu.commands import ShowContextMenu
from navml.widgets.menu.context_menu import ContextMenu
from navml.widgets.menu.context_menu.context_menu import open_on_click, open_on_key
from navml.widgets.dialog.commands import SelectNext, SelectPrevious
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.window import Window

from navigator.lib.system import desktop, volumes
from navigator.widgets.manager.commands import MountImage, Rescan, ToggleHidden, UnmountImage
from navigator.widgets.shell.commands import EjectVolume, MountVolume, UnmountVolume

#: Where the window reads the mounts.
_READER = Background("nav-volumes", workers=1)


class VolumesWindow(Window):
    """The mounted volumes in a window of their own."""

    def __init__(self, show_all: bool = False, show_free: bool = False, **kwargs: Any) -> None:
        """*show_all* ticks *Show all mounts*: the kernel's own file systems too;
        *show_free* ticks *Show free %*: the free share instead of the used one."""
        super().__init__(**kwargs)
        self.show_all = show_all
        self.show_free = show_free
        self._found: list[volumes.Volume] = []
        self._reads = 0
        #: Where the cursor goes at the next listing: a mount point just mounted.
        self._select_mount = ""

    @property
    def show_all(self) -> bool:
        """Whether *Show all mounts* is ticked."""
        return bool(self.everything.value & 1)

    @show_all.setter
    def show_all(self, value: bool) -> None:
        self.everything.value = 1 if value else 0

    @property
    def show_free(self) -> bool:
        """Whether *Show free %* is ticked."""
        return bool(self.free_box.value & 1)

    @show_free.setter
    def show_free(self, value: bool) -> None:
        self.free_box.value = 1 if value else 0

    def mounted(self) -> None:
        super().mounted()
        effect(self, VolumesWindow._follow_box)
        effect(self, VolumesWindow._follow_free_box)
        # Not from ``__init__``: until the window is on the desktop it has no
        # application, and ``Background`` would read on the loop instead.
        self.reload()

    def _follow_box(self) -> None:
        """The box ticked or cleared, by a key, a click or Ctrl+H: list again."""
        self.everything.value  # noqa: B018 -- what this effect follows
        self._show()

    def _follow_free_box(self) -> None:
        """*Show free %* ticked or cleared: the share column follows."""
        self.volumes.show_free = self.show_free

    def reload(self) -> None:
        """Read the mounts again, on a thread; only the newest read is listed."""
        self._reads += 1
        _READER.run(self, volumes.gather_all, done=lambda outcome, n=self._reads: self._read(n, outcome))

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
        wanted, self._select_mount = self._select_mount, ""
        if wanted:
            for index, volume in enumerate(shown):
                if volume.mount == wanted:
                    listing.cursor = index
                    return
        if current is not None:
            for index, volume in enumerate(shown):
                if volume.mount == current.mount:
                    listing.cursor = index
                    break

    async def go(self) -> None:
        """*Go*: the active panel to the volume under the cursor, and the window closed."""
        volume = self.volumes.selected
        if volume is not None and not volume.mounted:
            self.spawn(self._mount_and_choose(volume, close=True))
            return
        if await self.volumes.choose():
            self.request_close()

    async def on_hbar_scroll(self, event: Any) -> bool:
        """The bottom bar was worked: its value counts from the mount points'
        starts, ``back`` from their ends."""
        volumes = self.volumes
        volumes.back = max(0, volumes.mount_reach - event.value)
        return True

    async def on_chosen(self, event: ChosenEvent) -> bool:
        """Enter on a volume not mounted: mounted first, then chosen; any other walks on up."""
        volume = event.node
        if isinstance(volume, volumes.Volume) and not volume.mounted:
            self.spawn(self._mount_and_choose(volume, close=False))
            return True
        return False

    # -- Mount, Unmount, Eject ------------------------------------------------------------

    async def _desktop(self, step: Any, *args: Any) -> bool:
        """``step(*args)`` on a thread, its failure in a box, the mounts read
        again either way; True when it worked."""
        try:
            await asyncio.to_thread(step, *args)
        except OSError as error:
            await Dialog(title=tr("Volumes"), buttons="ok",
                         prompt=escape_caption(error.strerror or str(error))).execute(self.application)
            self.reload()
            return False
        self.reload()
        return True

    async def _mount_and_choose(self, volume: volumes.Volume, *, close: bool) -> None:
        """*volume* mounted, the mounts read again, and the volume -- at its
        mount point now -- chosen, as Enter on a mounted one is."""
        if volume.native is None or not await self._desktop(desktop.mount_device, volume.native):
            return
        found = await asyncio.to_thread(volumes.gather_all)
        self._found = found
        self._show()
        now = next((each for each in found if each.mounted and each.native is not None
                    and (each.native.ident or each.native.name) == (volume.native.ident or volume.native.name)), None)
        if now is None:
            return
        await self.volumes.emit(ChosenEvent(now))
        if close:
            self.request_close()

    async def on_mount_volume(self, command: MountVolume) -> bool:
        volume = self.volumes.selected
        if volume is not None and volume.native is not None:
            self.spawn(self._desktop(desktop.mount_device, volume.native))
        return True

    async def on_unmount_volume(self, command: UnmountVolume) -> bool:
        volume = self.volumes.selected
        if volume is not None and volume.mounted:
            self.spawn(self._desktop(desktop.unmount, volume.target))
        return True

    async def on_eject_volume(self, command: EjectVolume) -> bool:
        volume = self.volumes.selected
        if volume is not None and volume.mounted:
            self.spawn(self._desktop(desktop.eject, volume.target))
        return True

    # -- Mount image, Unmount image -----------------------------------------------------

    async def on_mount_image(self, command: MountImage) -> bool:
        self.spawn(self._mount_image())
        return True

    async def _mount_image(self) -> None:
        """A disk image file asked for -- listed from the active panel's
        directory, its cursor's image named -- mounted, read again, and the
        cursor on its first file system."""
        from navml.widgets.dialog.file_dialog import FileDialog
        from navigator.widgets.drives.disk_image import mount_image

        app = self.application
        directory, name = self._image_start()
        dialog = FileDialog(title=tr("Mount image"), label=tr("~I~mage file"), history_id="mount_image",
                            directory=directory, ok_text=tr("~M~ount"))
        if name:
            dialog.target.value = name
        chosen = await dialog.execute(app)
        if not chosen:
            return
        mounted = await mount_image(app, Path(chosen))
        if mounted:
            self._select_mount = mounted[0].local
        self.reload()

    def _image_start(self) -> tuple[Path, str]:
        """Where *Mount image*'s box starts: the active panel's directory on
        the disk, with the image at its cursor named -- else the home
        directory.  Nothing here waits on a disk: the panel's own fields."""
        manager = getattr(getattr(self.application, "root", None), "active_manager", None)
        panel = getattr(manager, "active_panel", None)
        if panel is not None and panel.location.is_local and panel.found is None:
            image = panel.image_file()
            return panel.path, (str(image) if image is not None else "")
        return Path.home(), ""

    def _image_mounts(self) -> list[Any]:
        """The mounts of the disk image the row under the cursor is of, or ``[]``."""
        from navigator.lib.system import udisks

        volume = self.volumes.selected
        if volume is None or not volume.mounted or udisks.program() is None:
            return []
        return udisks.image_at(volume.mount)

    async def on_unmount_image(self, command: UnmountImage) -> bool:
        mounts = self._image_mounts()
        if mounts:
            self.spawn(self._unmount_image(mounts))
        return True

    async def _unmount_image(self, mounts: list[Any]) -> None:
        from navigator.widgets.drives.disk_image import unmount_image

        await unmount_image(self.application, mounts)
        self.reload()

    def allows(self, action: str) -> bool:
        """Whether ``"mount"``, ``"unmount"`` or ``"eject"`` can be done to the
        volume under the cursor: ``gio``, Solid or udisks is there and says it can.  What the
        buttons' ``disabled`` follows -- the list's cursor and items are read,
        so they follow it as it moves -- and what :meth:`enables` answers."""
        volume = self.volumes.selected
        if volume is None or desktop.volume_program() is None:
            return False
        if action == "mount":
            return volume.can_mount
        if action == "unmount":
            return volume.mounted and volume.can_unmount
        return volume.mounted and volume.can_eject

    def refusal(self, command: Any) -> str:
        """Mount, Unmount and Eject where :meth:`allows` them."""
        for kind, action in ((MountVolume, "mount"), (UnmountVolume, "unmount"), (EjectVolume, "eject")):
            if isinstance(command, kind):
                if self.allows(action):
                    return ""
                if self.volumes.selected is None:
                    return tr("The cursor is on no volume")
                if desktop.volume_program() is None:
                    return tr("Neither GIO, Solid nor udisks is installed")
                return tr("Not for this volume")
        if isinstance(command, MountImage):
            from navigator.lib.system import udisks

            return "" if udisks.program() is not None else tr("udisksctl (udisks2) is not installed")
        if isinstance(command, UnmountImage):
            if self._image_mounts():
                return ""
            return tr("The cursor is on no disk image")
        return super().refusal(command)

    # -- what the buttons and keys do ---------------------------------------------------

    async def on_rescan(self, event: Rescan) -> bool:
        self.reload()
        return True

    async def on_toggle_hidden(self, event: ToggleHidden) -> bool:
        self.show_all = not self.show_all
        return True

    def checks(self, command: Any) -> bool | None:
        """The *Volumes* menu ticks *Show all mounts* while it is on."""
        if isinstance(command, ToggleHidden):
            return self.show_all
        return super().checks(command)

    # -- the right-click menu: ``ContextMenuHost``'s hooks, written out, as
    # ``InputLine``'s are -- this half has one base, its markup's.

    def prepare_context(self, x: int, y: int) -> None:
        """A right click on a row puts the list's cursor there."""
        index = self.volumes.row_at(y - self.volumes.y)
        if index is not None and self.volumes.x <= x < self.volumes.x + self.volumes.width:
            self.volumes.cursor = index

    def context_menu(self) -> ContextMenu:
        """The *Volumes* menu's entries, built each time so its captions follow the language."""
        menu = ContextMenu()
        menu.add_item(tr("~R~e-read"), Rescan)
        menu.add_item(tr("~S~how all mounts"), ToggleHidden)
        menu.add_line()
        menu.add_item(tr("~M~ount"), MountVolume)
        menu.add_item(tr("~U~nmount"), UnmountVolume)
        menu.add_item(tr("~E~ject"), EjectVolume)
        menu.add_line()
        menu.add_item(tr("Mount ~i~mage..."), MountImage)
        menu.add_item(tr("Unmount ima~g~e"), UnmountImage)
        menu.add_line()
        menu.add_item(tr("~C~lose"), CloseWindow)
        return menu

    def context_point(self) -> tuple[int, int]:
        """Under the list's cursor row."""
        view = self.volumes
        return view.x + 2, view.y + view.inset + view.header + max(0, view.cursor - view.scroll) + 1

    async def on_context_menu(self, event: ContextMenuEvent) -> bool:
        return open_on_click(self, event)

    async def on_show_context_menu(self, command: ShowContextMenu) -> bool:
        return open_on_key(self)

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
            for control in (self.everything, self.free_box, self.mount_button, self.unmount_button,
                            self.eject_button, self.go_button, self.close_button):
                if control.shortcut_match(event.key):
                    return await control.activate(event.key)
        return await super().on_key(event)
