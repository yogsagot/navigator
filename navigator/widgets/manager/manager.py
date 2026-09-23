"""The handlers behind ``manager.nml``.

The desktop, and the first screen this repository converted to markup.  What
the document says is the tree and the geometry; what is left here is the logic
-- the keys, which panel is active, and the one default that depends on whether
the caller supplied a value.

This file never names the generated class.  ``class Manager(Widget)`` is what a
Python-only widget would say too, which is what lets a component gain or lose
its markup half without being edited, and it is the base the markup's bare
``Manager:`` head asks for.
"""

from __future__ import annotations

from pathlib import Path

from navkit.events import KeyEvent
from navkit.reactive import computed
from navkit.screen import Surface
from navkit.stylesheet import Stylesheet
from navkit.widget import Widget

from navigator.scheme import default_scheme
from navml.widgets.dialog import Dialog

from navigator.widgets.mkdir_dialog import MkdirDialog
from navigator.widgets.panel import Panel


class Manager(Widget):
    """The Navigator desktop: menu bar, two panels and the key bar."""

    def __init__(
        self,
        left: Path,
        right: Path,
        scheme: Stylesheet | None = None,
        **kwargs,
    ):
        """Build the desktop, then seed the three values markup cannot.

        ``super().__init__()`` is the generated half, so the whole tree exists
        from the next line on -- which is the contract the merge rests on.

        **Where the panels open is seeded rather than bound, and that is the
        rule the conversion turned up.**  A markup property line compiles to a
        binding, a bound attribute is read-only until something unbinds it, and
        :meth:`~navigator.widgets.panel.Panel.enter` assigns ``path`` every
        time the user descends a directory.  So a property a widget *navigates*
        can be given a starting value by its parent and cannot be bound to one;
        the document says so where it declares nothing about these three.

        ``stylesheet`` is a keyword rather than a markup line for a different
        reason: a default that depends on whether the caller supplied one is
        logic.  A root-block line would also be assigned *after*
        ``super().__init__()`` had applied the caller's keyword and would
        clobber it.  The desktop brings its own look either way, so the tree is
        styled with or without an application around it -- which is what lets a
        single panel be built and painted on its own.
        """
        super().__init__(stylesheet=scheme or default_scheme(), **kwargs)
        self.left.path = left
        self.right.path = right
        self.console.cwd = left

    def mounted(self) -> None:
        """Put the keyboard in the left panel.

        Required rather than tidy.  The panels' keys are ``ListViewer``'s now
        and reach it along the focus path, and ``Panel:focused`` is what
        paints the cursor row -- so a desktop that focused nothing would come
        up with two identical panels and arrow keys that did nothing.  It is
        also what ``_pop_modal`` hands the keyboard back *to* when a dialog
        closes, which is why the conversion had to land with the extraction
        rather than after it.
        """
        super().mounted()
        self.left.focus()

    def toggle_console(self) -> None:
        """Show or hide the console, starting its shell the first time.

        The focus moves with the flag, and **in the same call rather than from
        an effect**.  An effect runs at the next flush, which is after the
        whole batch of events has been dispatched -- so a Ctrl+O and the
        keystroke behind it, arriving together as a paste or fast typing do,
        would be routed by a focus that had not moved yet and the second key
        would go to the panels.  Late is invisible for the cursor and a lost
        keystroke for the keyboard.
        """
        showing = not self.console_visible
        if showing:
            self.console.start()
        self.console_visible = showing
        app = self.application
        if showing:
            self.console.focus()
        elif app is not None and app.focused is self.console:
            app.focused = None

    async def on_key(self, event: KeyEvent) -> bool:
        """The desktop's own keys: switching panels, rescanning, and Alt+X.

        The keys that move *within* a panel are no longer here: up, down, the
        pages, home, end and Enter belong to the list and are
        ``ListViewer``'s, reached along the focus path.  What is left is what
        genuinely needs the desktop -- which panel, and the ways out.

        Reached only when nothing nearer the keyboard claimed the key, which
        while the console is showing means never -- the console holds the
        focus and swallows what it does not use, so none of this needs to ask
        whether it is visible.  That question used to be an ``if`` at the top
        of ``Navigator.on_key``; the focus path answers it now.

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

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
