"""The handlers behind ``manager.nml``.

The file manager window.  What the document says is the two panels, their
geometry and the keys; what is left here is the logic -- what the commands
do, which panel is active, and where the panels open.

This file never names the generated class.  ``class Manager(Window)`` is the
base the markup's ``Manager(Window):`` head asks for.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from navkit.reactive import computed, effect, reactive, untracked

from navml.widgets.dialog.dialog import Dialog
from navml.widgets.window import Window

from navigator.commands import MakeDirectory, Rescan, SwitchPanel, ToggleTree
from navigator.widgets.mkdir_dialog import MkdirDialog
from navigator.widgets.panel import Panel


class Manager(Window):
    """The file manager: two panels, in a window on the desktop."""

    #: The panels' frames are this window's frame.
    framed = False

    #: How long the tree's cursor has to rest before the panel follows it:
    #: DOS Navigator's thirty ticks of the 18.2 Hz timer (``NeedLocated``).
    LOCATE_DELAY = 30 / 18.2

    #: The panel the directory tree stands in for, or None while there is no
    #: tree.  Reactive, so ``active_panel`` and the follow effects move with it.
    tree_replaces: Any = reactive(None)

    def __init__(self, left: Path, right: Path, **kwargs):
        """Build the window, then seed where the panels open.

        ``super().__init__()`` is the generated half, so the whole tree exists
        from the next line on -- which is the contract the merge rests on.

        **Where the panels open is seeded rather than bound.**  A markup
        property line compiles to a binding, a bound attribute is read-only
        until something unbinds it, and
        :meth:`~navigator.widgets.panel.Panel.enter` assigns ``path`` every
        time the user descends a directory.  So a property a widget
        *navigates* can be given a starting value by its parent and cannot be
        bound to one.
        """
        super().__init__(**kwargs)
        self.left.path = left
        self.right.path = right
        self.tree.visible = False
        #: The pending "panel, follow the tree" -- cancelled by every move.
        self._follow: asyncio.Task[Any] | None = None

    def mounted(self) -> None:
        super().mounted()
        effect(self, Manager._tree_follows_panel)
        effect(self, Manager._panel_follows_tree)

    # -- commands ------------------------------------------------------------
    #
    # The keys are the markup's ``keys:`` block.  Alt+X is not among them: a
    # way out of Navigator cannot live on a window the user can close, so it
    # is the application's.

    async def on_switch_panel(self, event: SwitchPanel) -> bool:
        self.switch_panel()
        return True

    async def on_rescan(self, event: Rescan) -> bool:
        if self.tree.focused:
            self.tree.reload()
        else:
            self.active_panel.reload()
        return True

    async def on_toggle_tree(self, event: ToggleTree) -> bool:
        self.toggle_tree()
        return True

    async def on_tree_chosen(self, event: Any) -> bool:
        """Enter in the tree: the panel goes there now, not after the pause."""
        self.active_panel.path = event.node.data
        return True

    async def on_make_directory(self, event: MakeDirectory) -> bool:
        # **Started, not awaited.**  A handler that waits for a dialog holds
        # the event queue's only consumer, so the dialog is never painted and
        # the key that would dismiss it is never dispatched.  `spawn' lets
        # this handler return, the batch finish and the frame appear -- see
        # `Dialog.execute', which refuses the mistake.
        self.spawn(self.make_directory())
        return True

    async def make_directory(self) -> None:
        """F7: ask for a name, and make it in the active panel.

        The shape every file operation will take: start a dialog, wait for
        its answer in a task, act, and tell the panel to look again.  The
        rescan is a token rather than a call because the panel's listing
        follows its path and its token -- which is what makes "the directory
        changed" and "the user pressed Ctrl+R" the same code path.
        """
        panel = self.active_panel
        name = await MkdirDialog().execute(self.application)
        if not name:
            return
        try:
            (panel.path / name).mkdir()
        except OSError as error:
            await Dialog(
                title="Cannot make directory",
                prompt=error.strerror or str(error),
                buttons="ok",
            ).execute(self.application)
        panel.reload()

    @computed
    def active_panel(self) -> Panel:
        """Whichever panel currently has the keyboard.

        The right one only when it actually holds the focus, so that a
        desktop with the focus somewhere else entirely -- in the console, in
        a dialog -- still answers "the left one" rather than guessing.  While
        the tree stands in for one panel, the other is the active one whether
        or not it holds the keyboard: it is the one the tree steers.
        """
        replaced = self.tree_replaces
        if replaced is not None:
            return self.right if replaced is self.left else self.left
        return self.right if self.right.focused else self.left

    def switch_panel(self) -> None:
        """Move the keyboard to the other panel, or between panel and tree."""
        if self.tree_replaces is not None:
            (self.active_panel if self.tree.focused else self.tree).focus()
            return
        other = self.right if self.active_panel is self.left else self.left
        other.focus()

    # -- the directory tree ----------------------------------------------------

    def toggle_tree(self) -> None:
        """Ctrl+T: ``SwitchView(dtTree)``.

        The **passive** panel gives way to the tree, in its place, and the
        keyboard stays with the active one.  The second Ctrl+T puts the panel
        back -- and gives it the keyboard if the tree had it, as the original
        re-selected the panel it restored.
        """
        tree, replaced = self.tree, self.tree_replaces
        if replaced is None:
            active = self.active_panel
            passive = self.right if active is self.left else self.left
            row = self.panels.children
            row.remove(tree)
            row.insert(row.index(passive), tree)
            tree.show(active.path)
            passive.visible = False
            tree.visible = True
            self.tree_replaces = passive
        else:
            had_keys = tree.focused
            tree.visible = False
            replaced.visible = True
            self.tree_replaces = None
            if had_keys:
                replaced.focus()
        self.panels.invalidate()

    def _tree_follows_panel(self) -> None:
        """The tree's cursor goes wherever the active panel goes: ``cmChangeTree``."""
        if self.tree_replaces is None:
            return
        path = self.active_panel.path
        with untracked():
            if self.tree.selected_path != Path(path).resolve():
                self.tree.show(path)

    def _panel_follows_tree(self) -> None:
        """A cursor at rest in a focused tree takes the panel with it.

        DOS Navigator's ``NeedLocated``: every move restarts the wait, and the
        panel moves only once the cursor has stayed put for ``LOCATE_DELAY``.
        """
        path, focused = self.tree.selected_path, self.tree.focused
        with untracked():
            if self._follow is not None:
                self._follow.cancel()
                self._follow = None
            app = self.application
            if (
                self.tree_replaces is None or not focused or path is None
                or app is None or not app.is_running
            ):
                return
            self._follow = self.spawn(self._follow_later(path))

    async def _follow_later(self, path: Path) -> None:
        await asyncio.sleep(self.LOCATE_DELAY)
        if self.tree.focused and self.tree.selected_path == path:
            self.active_panel.path = path
