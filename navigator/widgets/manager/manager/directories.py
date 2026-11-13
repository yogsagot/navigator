"""Making directories (F7), in a panel or in the directory tree.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from navkit.i18n import tr

from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.manager.commands import MakeDirectory
from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog
from navigator.widgets.tree.directory_tree.directory_tree import reread_trees
from navigator.lib.drives import Location

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Directories(_Base):
    """Making directories (F7), in a panel or in the directory tree."""

    async def on_make_directory(self, event: MakeDirectory) -> bool:
        # **Started, not awaited.**  A handler that waits for a dialog holds
        # the event queue's only consumer, so the dialog is never painted and
        # the key that would dismiss it is never dispatched.  `spawn' lets
        # this handler return, the batch finish and the frame appear -- see
        # `Dialog.execute', which refuses the mistake.
        self.spawn(self.tree_make_directory() if self.tree.focused else self.make_directory())
        return True

    async def tree_make_directory(self) -> None:
        """F7 in the Ctrl+T tree: ``MkDirectory``, DN's ``MakeDirectory`` (a
        ``;`` list, parents made) under the one at the tree's cursor, which
        the tree then shows and goes to -- the first part."""
        base = self.tree.selected_path
        if base is None:
            return
        name = await MkdirDialog().execute(self.application)
        if not name:
            return
        results = await self._make_directories(base, name)
        reread_trees(self.application)
        if results:
            place = results[0].place
            self.tree.show(place.local if place.is_local else place)
        for panel in self.all_panels:
            panel.reload()
        self.reread_info()

    async def _make_directories(self, base: Any, text: str) -> list[Any]:
        """``make_directories`` in *base*, its failure said in DN's
        ``dlFCNoCreateDir`` box; what was made."""
        from navml.widgets.dialog.control import escape_caption

        from navigator.widgets.file_ops.make_directory import failure_text, make_directories

        results, failure = await make_directories(self.application, base, text)
        if failure is not None:
            path, error = failure
            await Dialog(title=tr("Error"), prompt=escape_caption(failure_text(path, error)),
                         buttons="ok").execute(self.application)
        return results

    async def make_directory(self) -> None:
        """F7: ask for a name, and make it in the active panel.

        The shape every file operation will take: start a dialog, wait for
        its answer in a task, act, and tell the panel to look again.  The
        rescan is a token rather than a call because the panel's listing
        follows its path and its token -- which is what makes "the directory
        changed" and "the user pressed Ctrl+R" the same code path.

        A local directory refused permission offers *As root* (a departure;
        :mod:`navigator.lib.system.elevate`).
        """
        panel = self.active_panel
        name = await MkdirDialog().execute(self.application)
        if not name:
            return
        here = Location.of(panel.location)
        results = await self._make_directories(here, name)
        # ``RereadDirectory(Dr)`` for each part: every panel showing where
        # its first new directory went.
        changed = {made.top.parent for made in results if made.top is not None}
        for other in self.all_panels:
            if other is not panel and other.application is not None and Location.of(other.location) in changed:
                other.reload()
        # ``CM_MakeDir``: the cursor on the first part only when it is made
        # right here (DN's ``if Dr <> P^.DirectoryName then Exit``) -- one
        # there already included, ``a/b`` leaving the cursor be.
        first = results[0].place if results else None
        panel.reload(key=first.name if first is not None and first.parent == here else None)
        if results:
            reread_trees(self.application)  # DN's ``cmRereadTree``
            self.reread_info()
