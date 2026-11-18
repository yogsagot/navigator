"""The help window's commands: ``StatusDef hcHelp``'s keys (``DN.DNR``).

DN's status line sent ``cmYes``/``cmSave``/``cmOk``/``cmNo``/``cmDefault``/
``cmCancel`` to ``THelpViewer.HandleEvent``, which turned them back into
keys; here each is a command of its own, named for what it does.

The scrolling keys were ``TScroller``'s, in no status line: they are commands
here so that they are in the window's key table, where they can be bound to
other keys.  They have no title -- the key bar has no room to name them.
"""

from __future__ import annotations

from navkit.commands import Command


class HelpOnHelp(Command):
    """F1 inside Help, *Help on help*: ``cmDefault``."""

    title = "Help on help"


class HelpIndex(Command):
    """Shift+F1, *Index*: ``cmCancel`` -- the contents page."""

    title = "Index"


class NextTopic(Command):
    """Tab, *Next topic*: ``cmYes`` -- the next link selected."""

    title = "Next topic"


class PreviousTopic(Command):
    """Shift+Tab, *Previous topic*: ``cmSave``."""

    title = "Previous topic"


class GoToReference(Command):
    """Enter, *Go to reference*: ``cmOk`` -- the selected link followed."""

    title = "Go to reference"


class GoBack(Command):
    """Alt+F1, *Go back*: ``cmNo``, ``PrevTopic``."""

    title = "Go back"


class ScrollLineUp(Command):
    """Up: the page a row up."""


class ScrollLineDown(Command):
    """Down: the page a row down."""


class ScrollPageUp(Command):
    """PgUp: a window less a row up."""


class ScrollPageDown(Command):
    """PgDn: a window less a row down."""


class ScrollToTop(Command):
    """Home: the top of the page."""


class ScrollToBottom(Command):
    """End: the end of the page."""


class ScrollLeft(Command):
    """Left: the page a column left, where a code block is wider than the window."""


class ScrollRight(Command):
    """Right: the page a column right."""
