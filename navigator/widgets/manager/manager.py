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

from navigator.commands import (
    ChangeDirectory,
    Edit,
    MakeDirectory,
    QuickView,
    Rescan,
    SwitchPanel,
    ToggleTree,
    View,
    ViewAsHex,
    ViewAsText,
)
from navigator.widgets.mkdir_dialog import MkdirDialog
from navigator.widgets.panel import Panel


class Manager(Window):
    """The file manager: two panels, in a window on the desktop."""

    #: The panels' frames are this window's frame.
    framed = False

    #: How long the tree's cursor has to rest before the panel follows it:
    #: DOS Navigator's thirty ticks of the 18.2 Hz timer (``NeedLocated``).
    LOCATE_DELAY = 30 / 18.2

    #: The panel something else stands in for -- the directory tree (Ctrl+T)
    #: or the quick view (Ctrl+Q) -- and that something, or None for both
    #: while the two panels are showing.  DOS Navigator's ``LType``/``RType``:
    #: one side at a time is ever not a panel.  Reactive, so ``active_panel``
    #: and the follow effects move with them.
    replaced: Any = reactive(None)
    replacement: Any = reactive(None)

    #: The panel that last held the keyboard.  What ``active_panel`` answers
    #: while neither does -- Ctrl+O has given the keyboard to the console, or
    #: a dialog has it -- since the panel the user left active is still the
    #: one a command means.
    _last_panel: Any = reactive(None)

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
        self.quick.visible = False
        #: The pending "panel, follow the tree" -- cancelled by every move.
        self._follow: asyncio.Task[Any] | None = None

    def mounted(self) -> None:
        super().mounted()
        effect(self, Manager._remember_panel)
        effect(self, Manager._tree_follows_panel)
        effect(self, Manager._panel_follows_tree)
        effect(self, Manager._quick_view_follows_panel)

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

    async def on_change_directory(self, event: ChangeDirectory) -> bool:
        # Started, not awaited, for the reason ``on_make_directory`` gives.
        self.spawn(self.change_directory())
        return True

    async def change_directory(self) -> None:
        """Alt+T: *Choose Directory*, and the active panel goes where it says.

        The panel that asked, remembered before the dialog takes the keyboard:
        while it is up the focus is in the dialog, and which panel was active
        is no longer something the focus can say.
        """
        from navigator.widgets.change_dir_dialog import ChangeDirDialog

        panel = self.active_panel
        chosen = await ChangeDirDialog(start=panel.path).execute(self.application)
        if chosen is not None:
            panel.path = Path(chosen)
            panel.focus()

    async def on_toggle_tree(self, event: ToggleTree) -> bool:
        self.toggle_tree()
        return True

    async def on_quick_view(self, event: QuickView) -> bool:
        self.toggle_quick_view()
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

    async def on_view(self, event: View) -> bool:
        """F3: ``cmFileView``, the selected file in a viewer window."""
        self.spawn(self.view("text"))
        return True

    async def on_view_as_text(self, event: ViewAsText) -> bool:
        self.spawn(self.view("text"))
        return True

    async def on_view_as_hex(self, event: ViewAsHex) -> bool:
        self.spawn(self.view("hex"))
        return True

    async def view(self, mode: str) -> None:
        """Open the selected file in a viewer on this window's desktop.

        A directory is passed over: DN counted its size (``CountLen``), which
        is not written yet, and ``..`` has nothing to show.  A file that will
        not open is said so, as a directory that will not be made is.
        """
        from navigator.widgets.file_window import FileWindow

        panel = self.active_panel
        entry = panel.selected
        desktop = self.desktop
        if entry is None or entry.is_dir or desktop is None:
            return
        path = panel.path / entry.name
        try:
            window = FileWindow(path, mode=mode)
        except OSError as error:
            await Dialog(
                title="Cannot view file",
                prompt=f"{entry.name}: {error.strerror or error}",
                buttons="ok",
            ).execute(self.application)
            return
        desktop.open(window)

    async def on_edit(self, event: Edit) -> bool:
        """F4: ``cmEditFile``, the selected file in an editor window."""
        self.spawn(self.edit())
        return True

    async def edit(self) -> None:
        """Open the selected file in an editor on this window's desktop.

        A directory and ``..`` are passed over, as DN's ``cmEditFile`` passed
        them; a file that will not open is said so.
        """
        from navigator.widgets.edit_window import EditWindow

        panel = self.active_panel
        entry = panel.selected
        desktop = self.desktop
        if entry is None or entry.is_dir or desktop is None:
            return
        path = panel.path / entry.name
        try:
            window = EditWindow(path)
        except OSError as error:
            await Dialog(
                title="Cannot edit file",
                prompt=f"{entry.name}: {error.strerror or error}",
                buttons="ok",
            ).execute(self.application)
            return
        desktop.open(window)

    def _remember_panel(self) -> None:
        if self.right.focused:
            self._last_panel = self.right
        elif self.left.focused:
            self._last_panel = self.left

    @computed
    def active_panel(self) -> Panel:
        """Whichever panel has the keyboard, or had it last.

        **Last, not "the left one"**, while the focus is somewhere else --
        the console after Ctrl+O, a dialog.  DOS Navigator's active panel
        stayed active while its user screen was up, and a command typed then
        ran in *its* directory; answering "left" whenever neither panel held
        the keyboard sent the shell back to the left panel's directory the
        moment the console was shown.  While the tree stands in for one
        panel, the other is the active one whether or not it holds the
        keyboard: it is the one the tree steers.
        """
        replaced = self.replaced
        if replaced is not None:
            return self.right if replaced is self.left else self.left
        if self.right.focused:
            return self.right
        if self.left.focused:
            return self.left
        return self._last_panel or self.left

    def list_name(self) -> str:
        """The active panel's directory: what the window list shows for this window.

        DOS Navigator's double window passed ``cmGetName`` on to its panel.
        A window in the background has lost the keyboard, so which panel was
        active is read off what it will get back, not off the focus.
        """
        app = self.application
        saved = self._saved_focus
        if (
            self.replaced is None
            and not (app is not None and self._holds(app.focused))
            and saved in (self.left, self.right)
        ):
            return str(saved.path)
        return str(self.active_panel.path)

    def switch_panel(self) -> None:
        """Move the keyboard to the other panel, or between panel and tree."""
        replacement = self.replacement
        if replacement is not None:
            if replacement.focus_within:
                self.active_panel.focus()
            else:
                self._focus_replacement()
            return
        other = self.right if self.active_panel is self.left else self.left
        other.focus()

    # -- the directory tree ----------------------------------------------------

    @computed
    def tree_replaces(self) -> Any:
        """The panel the directory tree stands in for, or None while there is none."""
        return self.replaced if self.replacement is self.tree else None

    def toggle_tree(self) -> None:
        """Ctrl+T: ``SwitchView(dtTree)``."""
        self.switch_view(self.tree)

    def toggle_quick_view(self) -> None:
        """Ctrl+Q: ``SwitchView(dtView)``, and the view loads the file under the cursor."""
        self.switch_view(self.quick)

    def switch_view(self, view: Any) -> None:
        """DOS Navigator's ``SwitchView``: *view* in the passive panel's place, or out of it.

        The **passive** panel gives way to *view*, in its place, and the
        keyboard stays with the active one.  Asking again for the view that is
        showing puts the panel back -- and gives it the keyboard if the view
        had it, as the original re-selected the panel it restored.  Asking for
        the *other* view swaps it in where the first one stood, and the
        keyboard goes back to the active panel, as ``SwitchView`` selected it.
        """
        current, replaced = self.replacement, self.replaced
        if current is view:
            had_keys = view.focus_within
            view.visible = False
            replaced.visible = True
            self.replacement = self.replaced = None
            if had_keys:
                replaced.focus()
            self.panels.invalidate()
            return
        active = self.active_panel
        had_keys = False
        if current is not None:
            had_keys = current.focus_within
            current.visible = False
            passive = replaced
        else:
            passive = self.right if active is self.left else self.left
        row = self.panels.children
        row.remove(view)
        row.insert(row.index(passive), view)
        if view is self.tree:
            view.show(active.path)
        passive.visible = False
        view.visible = True
        self.replaced, self.replacement = passive, view
        if had_keys:
            active.focus()
        if view is self.quick:
            self._quick_view_follows_panel()
        self.panels.invalidate()

    def _focus_replacement(self) -> None:
        (self.quick.viewer if self.replacement is self.quick else self.tree).focus()

    def _quick_view_follows_panel(self) -> None:
        """The quick view shows whatever the active panel's cursor is on: ``SendLocated``."""
        if self.replacement is not self.quick:
            return
        panel = self.active_panel
        entry, directory = panel.selected, panel.path
        path = None if entry is None or entry.is_dir else directory / entry.name
        with untracked():
            self.quick.show(path)

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
