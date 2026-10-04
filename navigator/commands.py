"""The application's own commands: what ``Navigator`` (``__main__.py``) handles.

Help, the way out and Ctrl+O mean the same wherever the focus is, so they are
the application's, bound on its key table.  Every other command lives with the
widgets that handle it, one ``commands.py`` per group of
``navigator/widgets/`` -- ``shell``, ``manager``, ``viewer``, ``editor`` and
``file_ops`` -- and a command nobody handles yet lives where its key table
binds it.  A command is only a name; its code is the ``on_*`` handler.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.commands import Command


class Help(Command):
    title = "Help"


@dataclass(frozen=True, slots=True)
class Quit(Command):
    """Leave Navigator.

    *desktop* marks the Alt+X binding, which quits only while the desktop is
    what the user is looking at: with Ctrl+O's console over the windows, Meta+X
    belongs to the program in it.  One command with a field rather than two
    commands, because both mean *quit* and a key bar shows them as one.
    """

    title = "Exit"

    desktop: bool = False


class AsciiTable(Command):
    """``cmASCIITable``: *ASCII Chart*, and the character picked typed where the
    keyboard is -- Ctrl+B and Utilities > *Character table* for the command line,
    Ctrl+P (and the info line's code, ``cmSpecChar``) in the editor, which
    answers it nearer the keyboard."""

    title = "Character table"


class OpenSmartpad(Command):
    """``cmOpenSmartpad``: Alt+Q, ≡ > *SmartPad (TM)* -- the notepad, opened or brought up."""

    title = "SmartPad"


class PrintFile(Command):
    """``cmPrintFile``: one command, as in DN, answered by whichever window has it --
    the editor's F8 prints its text, the file manager's Ctrl+F9 the file under
    the cursor."""

    title = "Print"


class ToggleConsole(Command):
    """Ctrl+O: put the windows away to show the console, or bring them back."""


__all__ = [
    "AsciiTable",
    "Help",
    "OpenSmartpad",
    "PrintFile",
    "Quit",
    "ToggleConsole",
]
