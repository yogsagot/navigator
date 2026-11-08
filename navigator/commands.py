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
class RecordMacro(Command):
    """Ctrl+J R 1 .. 9: DOS Navigator's Alt+Shift+N (``KeyMacroses``) --
    every key typed from here on recorded into slot *slot*; pressed again,
    with any digit, the recording ends, as any Alt+Shift+digit ended DN's.
    On a chord of DN's Ctrl+J, a departure: Alt+digits are the file
    manager's quick directories, and terminals take them."""

    title = "Record"

    slot: int = 1


@dataclass(frozen=True, slots=True)
class PlayMacro(Command):
    """Ctrl+J 1 .. 9: DOS Navigator's Alt+N -- slot *slot*'s keys typed
    again (``MacroPlaying``).  DN's Ctrl+J N played the editor's macros;
    those are Ctrl+J 0's now."""

    title = "Play"

    slot: int = 1


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


class Refresh(Command):
    """≡ > Refresh display: the whole screen painted again.

    DOS Navigator's ``cmRefresh`` (``Redraw``), for a screen another program
    has written over.
    """


class ShowUserScreen(Command):
    """Alt+F5, ≡ > User screen: the console shown until a key is pressed.

    DOS Navigator's ``cmShowUserScreen``: a look behind the windows, where
    Ctrl+O (``cmShowOutput``) is the console to type into.
    """


class ScreenGrab(Command):
    """Shift+Alt+Ins, ≡ > Screen grabber: a rectangle of the screen to the clipboard.

    DOS Navigator's ``cmExecGrabber`` (``ScreenGrabber``).
    """


class AsciiTable(Command):
    """``cmASCIITable``: *ASCII Chart* in the ASCII glyph tier, the Unicode
    *Character Table* in any other, and the character picked typed where the
    keyboard is -- Ctrl+B and Utilities > *Character table* for the command line,
    Ctrl+P (and the info line's code, ``cmSpecChar``) in the editor, which
    answers it nearer the keyboard."""

    title = "Character table"


class OpenSmartpad(Command):
    """``cmOpenSmartpad``: Alt+Q, ≡ > *SmartPad (TM)* -- the notepad, opened or brought up."""

    title = "SmartPad"


class NewView(Command):
    """Window > *New view* (not DN's): another window on the active editor's
    text -- one undo history, one save, a cursor, scroll and block of its own.
    Here, with the names other screens share, so the main menu that offers it
    does not import the editor; the editor's window answers it."""

    title = "New view"


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
    "PlayMacro",
    "RecordMacro",
    "NewView",
    "OpenSmartpad",
    "PrintFile",
    "Quit",
    "Refresh",
    "ScreenGrab",
    "ShowUserScreen",
    "ToggleConsole",
]
