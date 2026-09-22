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
        """The desktop's own keys: moving about the panels, and Alt+X.

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
        elif event.matches("up"):
            panel.move_cursor(-1)
        elif event.matches("down"):
            panel.move_cursor(1)
        elif event.matches("pageup"):
            panel.move_cursor(-max(1, panel.rows - 1))
        elif event.matches("pagedown"):
            panel.move_cursor(max(1, panel.rows - 1))
        elif event.matches("home"):
            panel.move_cursor(-len(panel.entries))
        elif event.matches("end"):
            panel.move_cursor(len(panel.entries))
        elif event.matches("enter"):
            panel.enter()
        elif event.matches("ctrl+r"):
            panel.reload()
        else:
            return False
        return True

    @computed
    def active_panel(self) -> Panel:
        """Whichever panel currently has the cursor."""
        return self.left if self.left.active else self.right

    def switch_panel(self) -> None:
        self.left.active, self.right.active = self.right.active, self.left.active

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
