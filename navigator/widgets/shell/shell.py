"""The handlers behind ``shell.nml``.

What the document says is the two bars and the two layers between them; what
is left here is opening the file manager on the desktop, and Ctrl+O.

This file never names the generated class.  ``class Shell(DockLayout)`` is
what a Python-only widget would say too, and it is the base the markup's
``Shell(DockLayout):`` head names.
"""

from __future__ import annotations

from pathlib import Path

from navkit.events import Event, KeyEvent
from navkit.screen import Surface
from navkit.stylesheet import Stylesheet
from navml.commands import OpenMenu
from navml.widgets.layout.dock_layout import DockLayout

from navigator.scheme import default_scheme
from navigator.widgets.manager import Manager


class Shell(DockLayout):
    """The Navigator screen: menu bar, console, desktop and key bar."""

    def __init__(
        self,
        left: Path,
        right: Path,
        scheme: Stylesheet | None = None,
        **kwargs,
    ):
        """Build the screen, and open the file manager on its desktop.

        ``stylesheet`` is a keyword rather than a markup line because a
        default that depends on whether the caller supplied one is logic.  The
        screen brings its own look either way, so the tree is styled with or
        without an application around it.

        **The console's working directory is seeded, not bound**, for the
        reason ``Panel.path`` is: the shell inside it navigates it.
        """
        super().__init__(stylesheet=scheme or default_scheme(), **kwargs)
        self.console.cwd = left
        #: The file manager window.  Kept after it is closed, for whoever asks
        #: what it was; whether it is still on the desktop is
        #: ``manager.parent is not None``.
        self.manager = self.desktop.open(Manager(left, right))

    def toggle_console(self) -> None:
        """Put the windows away to show the console, or bring them back.

        The console starts its shell the first time it is shown.  The focus
        moves with the flag, and **in the same call rather than from an
        effect**.  An effect runs at the next flush, which is after the whole
        batch of events has been dispatched -- so a Ctrl+O and the keystroke
        behind it, arriving together as a paste or fast typing do, would be
        routed by a focus that had not moved yet and the second key would go
        to the wrong place.

        Bringing the windows back hands the keyboard to exactly the widget
        that had it, because that is what activating a window does.  With no
        window left there is nothing to go back to, and the console stays.
        """
        desktop = self.desktop
        showing = not self.console_visible
        if not showing and desktop.active_window is None:
            return
        if showing:
            self.console.start()
            window = desktop.active_window
            app = self.application
            if window is not None and app is not None and window._holds(app.focused):
                window._saved_focus = app.focused
        self.console_visible = showing
        if showing:
            self.console.focus()
        else:
            desktop.activate(desktop.active_window)

    def show_console(self) -> None:
        """Show the console if it is not showing already."""
        if not self.console_visible:
            self.console.start()
            self.console_visible = True
        self.console.focus()

    # -- the menu ---------------------------------------------------------------

    async def on_open_menu(self, event: OpenMenu) -> bool:
        """F10: the menu bar is this screen's, so the command stops here.

        The bar is nowhere near the focus -- it is a sibling of the desktop --
        so the command, which starts from the focus and walks up, reaches it
        only through the screen that holds both.
        """
        self.menu.open(0)
        return True

    async def on_key(self, event: KeyEvent) -> bool:
        """Alt+letter drops the menu whose caption carries that letter.

        Reached only by a key that everything nearer the keyboard declined,
        so a dialog's Alt+letter walk and the console's child both come
        first: the console sends Meta+F to its program, as DOS Navigator's
        user screen would have.
        """
        return await self.menu.open_hotkey(event)

    async def on_desktop_emptied(self, event: Event) -> bool:
        """The last window on ``desktop`` closed: the console is all there is.

        Named by the generator's ``on_<id>_<event>`` convention, so the stub it
        writes is what this overrides.
        """
        self.show_console()
        return True

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
