"""The handlers behind ``manager.nml``.

The file manager window.  What the document says is the two panels and their
geometry; what is left here is the logic -- the keys, which panel is active,
and where the panels open.

This file never names the generated class.  ``class Manager(Window)`` is the
base the markup's ``Manager(Window):`` head asks for.
"""

from __future__ import annotations

from pathlib import Path

from navkit.events import KeyEvent
from navkit.reactive import computed

from navml.widgets.dialog import Dialog
from navml.widgets.window import Window

from navigator.widgets.mkdir_dialog import MkdirDialog
from navigator.widgets.panel import Panel


class Manager(Window):
    """The file manager: two panels, in a window on the desktop."""

    #: The panels' frames are this window's frame.
    framed = False

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

    async def on_key(self, event: KeyEvent) -> bool:
        """The desktop's own keys: switching panels, rescanning, and Alt+X.

        The keys that move *within* a panel are no longer here: up, down, the
        pages, home, end and Enter belong to the list and are
        ``ListViewer``'s, reached along the focus path.  What is left is what
        genuinely needs the desktop -- which panel, and the ways out.

        Reached only when nothing nearer the keyboard claimed the key, which
        while the console is showing means never -- the console holds the
        focus and the desktop this window is on is hidden, so none of this
        needs to ask whether it is visible.

        Alt+X is here rather than with the other two ways out because it has
        always been a desktop key: with the console up it is a keystroke for
        the child, and the child gets it by this method never running.
        """
        panel = self.active_panel
        if event.matches("alt+x"):
            if (app := self.application) is not None:
                app.exit()
        elif event.matches("tab"):
            self.switch_panel()
        elif event.matches("f7"):
            # **Started, not awaited.**  A handler that waits for a dialog
            # holds the event queue's only consumer, so the dialog is never
            # painted and the key that would dismiss it is never dispatched.
            # `spawn' lets this handler return, the batch finish and the frame
            # appear -- see `Dialog.execute', which refuses the mistake.
            self.spawn(self.make_directory())
        elif event.matches("ctrl+r"):
            panel.reload()
        else:
            return False
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
        a dialog -- still answers "the left one" rather than guessing.
        """
        return self.right if self.right.focused else self.left

    def switch_panel(self) -> None:
        """Move the keyboard to the other panel."""
        other = self.right if self.active_panel is self.left else self.left
        other.focus()
