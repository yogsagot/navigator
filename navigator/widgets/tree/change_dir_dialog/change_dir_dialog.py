"""The handlers behind ``change_dir_dialog.nml``: what the buttons do.

``ChangeDir`` returned the directory the tree was on when OK was pressed, and
the panel went there; :meth:`accept` is that answer.  Enter in the tree means
OK, as a double click did.  Cancel needs no handler: ``Dialog.on_click``
dismisses for any button nobody claimed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from navkit.events import Event
from navkit.i18n import tr

from navml.widgets.dialog.control import escape_caption
from navml.widgets.dialog.dialog import Dialog

from navigator.widgets.tree.directory_tree.directory_tree import directory_root, show_path


class ChangeDirDialog(Dialog):
    """*Choose Directory*: a tree of the filesystem, opened on *start*."""

    def __init__(self, start: Any = None, hidden: bool = True,
                 made: Callable[[Any, str], None] | None = None, search: str = "", **kwargs: Any) -> None:
        """*hidden* is the panel's ``show_hidden``: whether dot-directories are
        listed.  *start* on another drive (a ``Location``) shows that drive's
        tree, read on threads.  *made*, when given, is told of each directory
        *MkDir* makes -- the directory it was made in and the name typed -- so
        a panel showing that directory can put its cursor on it.  *search* is
        typed into the tree's quick search once the box is up, as DN replayed
        a panel search's letters after ``\\`` (``PutEvent``)."""
        super().__init__(**kwargs)
        self._search = search
        self._hidden = hidden
        self._made = made
        start = start if start is not None else Path.cwd()
        self.tree.root = directory_root(self._hidden, at=start)
        self._show(start)

    def mounted(self) -> None:
        super().mounted()
        if self._search:
            # After the box has given the tree the keyboard: a search ends
            # when its widget does not have it.
            self.spawn(self._replay_search())

    async def _replay_search(self) -> None:
        """The letters typed into the tree's search -- once the directory it
        opened on has its rows (``when_loaded``), read on a thread."""
        from navkit.events import KeyEvent

        def replay() -> None:
            self.tree.focus()
            self.tree.start_search()
            for char in self._search:
                self.tree._search_key(KeyEvent(char, char))

        node = self.tree.selected_node
        if node is None:
            replay()
        else:
            self.tree.when_loaded(node, replay)

    def _show(self, place: Any) -> None:
        # Every read on a thread, the disk's as well as another drive's: a
        # dead mount or a huge directory stops nothing but its own rows.
        self.tree.load_in_background = self.tree.probe_in_background = True
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
        # F7's own making, DN's ``MakeDirectory`` the tree's ``MkDirectory``
        # called: a ``;`` list, parents, *As root* on a refusal, an archive's
        # rewrite, Undo.
        from navigator.widgets.file_ops.make_directory import failure_text, make_directories

        results, failure = await make_directories(self.application, base, name)
        if failure is not None:
            path, error = failure
            await Dialog(
                title=tr("Error"),
                prompt=escape_caption(failure_text(path, error)),
                buttons="ok",
            ).execute(self.application)
        if not results:
            return  # failed, or *As root* declined
        first = results[0].place
        if self._made is not None:
            self._made(first.parent.local if first.is_local else first.parent, first.name)
        self.tree.root = directory_root(self._hidden, at=base)
        self._show(first.local if first.is_local else first)
        self.tree.focus()
