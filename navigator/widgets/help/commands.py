"""The help window's commands: ``StatusDef hcHelp``'s keys (``DN.DNR``).

DN's status line sent ``cmYes``/``cmSave``/``cmOk``/``cmNo``/``cmDefault``/
``cmCancel`` to ``THelpViewer.HandleEvent``, which turned them back into
keys; here each is a command of its own, named for what it does.
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
