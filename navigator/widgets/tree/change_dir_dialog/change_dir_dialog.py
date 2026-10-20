"""The handlers behind ``change_dir_dialog.nml``: what the buttons do.

``ChangeDir`` returned the directory the tree was on when OK was pressed, and
the panel went there; :meth:`accept` is that answer.  Enter in the tree means
OK, as a double click did.  Cancel needs no handler: ``Dialog.on_click``
dismisses for any button nobody claimed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.events import Event
from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.tree.directory_tree.directory_tree import directory_root, show_path


class ChangeDirDialog(Dialog):
    """*Choose Directory*: a tree of the filesystem, opened on *start*."""

    def __init__(self, start: Any = None, hidden: bool = True, **kwargs: Any) -> None:
        """*hidden* is the panel's ``show_hidden``: whether dot-directories are
        listed.  *start* on another drive (a ``Location``) shows that drive's
        tree, read on threads."""
        super().__init__(**kwargs)
        self._hidden = hidden
        # Dialog's bottom row and message are not in this layout.
        self.row.visible = False
        self.message.visible = False
        start = start if start is not None else Path.cwd()
        self.tree.root = directory_root(self._hidden, at=start)
        self._show(start)

    def _show(self, place: Any) -> None:
        from navigator.lib.drives import Location

        # Another drive's every read is a round trip: on threads.
        elsewhere = isinstance(place, Location) and not place.is_local
        self.tree.load_in_background = self.tree.probe_in_background = elsewhere
        show_path(self.tree, place)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        """This dialog's own buttons, which the tab order puts after the tree."""
        return (self.pick, self.drive, self.reread, self.mkdir, self.abandon)

    def accept(self) -> Path | None:
        """The directory under the cursor."""
        node = self.tree.selected_node
        return node.data if node is not None else None

    # -- the buttons -----------------------------------------------------------

    async def on_pick_click(self, event: Event) -> bool:
        self.close(self.accept())
        return True

    async def on_tree_chosen(self, event: Any) -> bool:
        """Enter in the tree is OK."""
        self.close(self.accept())
        return True

    async def on_reread_click(self, event: Event) -> bool:
        """Read the tree again, keeping the cursor where it was: ``Reread``."""
        here = self.accept()
        self.tree.root = directory_root(self._hidden, at=here)
        if here is not None:
            self._show(here)
        self.tree.focus()
        return True

    async def on_mkdir_click(self, event: Event) -> bool:
        self.spawn(self.make_directory())
        return True

    async def make_directory(self) -> None:
        """Make a directory in the one under the cursor, and put the cursor on it.

        As the tree's own ``MkDirectory`` did: the new directory is made where
        the tree points, not where any panel is.
        """
        from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

        base = self.accept()
        if base is None:
            return
        name = await MkdirDialog().execute(self.application)
        if not name:
            return
        try:
            from navigator.lib.drives import Location, drive_of

            if isinstance(base, Location) and not base.is_local:
                import asyncio

                place = base / name

                def make() -> None:
                    drive = drive_of(place)
                    drive.mkdir(place)
                    drive.finish()

                await asyncio.to_thread(make)
            else:
                (Path(base.local if isinstance(base, Location) else base) / name).mkdir()
        except OSError as error:
            await Dialog(
                title=tr("Cannot make directory"),
                prompt=error.strerror or str(error),
                buttons="ok",
            ).execute(self.application)
            return
        self.tree.root = directory_root(self._hidden, at=base)
        self._show(base / name)
        self.tree.focus()
