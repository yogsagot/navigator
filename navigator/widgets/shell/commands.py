"""The shell's commands: what ``Shell`` handles.

The command line's own -- run, complete, Home and End, the name typed onto it
-- and the screen-wide ones: About, a new file manager, the tree window, and
Space's tag, which is the command line's rule.  See ``navigator/commands.py``
for where the rest live.
"""

from __future__ import annotations

from navkit.commands import Command


class About(Command):
    """≡ > About: DOS Navigator's ``cmAbout``, the name, version and author."""

    title = "About"


class ExecuteCommandLine(Command):
    """Enter with something on the command line: run it.

    DOS Navigator's ``cmExecCommandLine``, which the panel's own Enter sent
    first and fell back from when the line was blank (``FLPANELX.PAS``).
    Here that is a key table's rule rather than the panel's: bound on the
    application, so it is asked before the panel sees Enter, and disabled
    while the line is empty, so the key falls through to the panel.
    """


class CompleteCommandLine(Command):
    """Tab with something on the command line: complete the word at the caret.

    Not DOS Navigator's -- ``TCommandLine`` completed nothing, and Tab only
    ever switched panels.  Bound the way Enter is, so the rule is Enter's:
    with the line empty the command is disabled and Tab falls through to the
    panels, and with text on it the shell is asked what the word could be.
    """


class InsertName(Command):
    """Ctrl+Enter: the name under the panel's cursor, typed onto the command line.

    DOS Navigator's ``_CtrlEnter`` (``FLPANELX.PAS``) sending ``cmInsertName``.
    On ``..`` it is the panel's own directory, whole.  Alt+Enter is bound to
    it as well, Midnight Commander's key for the same thing, because a
    terminal that does not speak the kitty keyboard protocol sends Ctrl+Enter
    as a plain Enter.
    """


class InsertPath(Command):
    """Ctrl+Shift+Enter: as :class:`InsertName`, but the whole path.

    ``_CtrlEnter`` with Shift held, which prefixed the panel's directory.
    """


class CommandLineHome(Command):
    """Home with something on the command line: to its start, not the list's top."""


class CommandLineEnd(Command):
    """End with something on the command line: to its end, not the list's bottom."""


class NewManager(Command):
    """Ctrl+F3: another file manager window, the size of the desktop.

    DOS Navigator's ``cmCreatePanel``, Manager > New.
    """

    title = "New Manager"


class OpenTreeWindow(Command):
    """Disk > Directory tree: a *Directory Tree* window on the desktop.

    DOS Navigator's ``cmCreateTree`` -- here opening the ``TTreeWindow`` that
    1.51 defined and never used.
    """

    title = "Tree"


class ToggleMarkBySpace(Command):
    """Space with the command line empty: :class:`ToggleMark`.

    DN's ``fmoSpaceToggle``, on by default: ``kbSpace`` shared ``kbIns``'s
    branch but gave up whenever ``CmdLine.Str`` was not empty, so that a blank
    typed into a command still reached it.  A command of its own because that
    condition is the command line's, and ``Shell`` -- which owns the line --
    is what handles it.
    """


__all__ = [
    "About",
    "ExecuteCommandLine",
    "CompleteCommandLine",
    "InsertName",
    "InsertPath",
    "CommandLineHome",
    "CommandLineEnd",
    "NewManager",
    "OpenTreeWindow",
    "ToggleMarkBySpace",
]
