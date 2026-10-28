"""Alt+F4's console editors: the ones on ``PATH``, each run in a window of its own.

Not DOS Navigator's, whose Alt+F4 (``cmIntFileEdit``) fell back to the internal
editor when ``DN.EDT`` had nothing for the file -- here, with *Internal
editor* on, the same as F4.  Instead it offers the terminal editors that are
installed, ``$VISUAL`` and ``$EDITOR`` first, each as an ``editors.ini`` entry
``&editor !.!`` would be: run in a ``TerminalWindow`` on the file at the
cursor (or on its fetched copy, for a file on another drive), the window
gone as soon as the editor quits.
"""

from __future__ import annotations

import os
import shlex
import shutil
from collections.abc import Callable, Mapping

from navigator.lib.config.associations import Action
from navigator.lib.config.usermenu import commands_of

#: The editors looked for, in the order offered: caption, and the command
#: the file's name is put after.
KNOWN: tuple[tuple[str, str], ...] = (
    ("~V~im", "vim"),
    ("~N~eovim", "nvim"),
    ("N~a~no", "nano"),
    ("~M~cedit", "mcedit"),
    ("Mi~c~ro", "micro"),
    ("~E~macs", "emacs -nw"),
    ("Ne (Nice edi~t~or)", "ne"),
    ("~J~oe", "joe"),
    ("Je~d~", "jed"),
    ("~H~elix", "hx"),
    ("~K~akoune", "kak"),
    ("M~g~", "mg"),
    ("Vi (~p~osix)", "vi"),
)


def installed(which: Callable[[str], str | None] | None = None,
              environ: Mapping[str, str] | None = None) -> list[tuple[str, str]]:
    """The editors there are, as ``(caption, command)``: ``$VISUAL`` and
    ``$EDITOR`` first, captioned with their own text, then :data:`KNOWN`'s.

    One that is another's link (``vi`` to vim, ``$EDITOR=vim``) is offered
    once, as the first.  ``shutil.which`` is looked up at the call, so the
    tests' replacement reaches it.  It looks on the disk: call it on a thread.
    """
    if which is None:
        which = shutil.which
    if environ is None:
        environ = os.environ
    offered: list[tuple[str, str]] = []
    seen: set[str] = set()

    def offer(caption: str, command: str) -> None:
        try:
            program = shlex.split(command)[0]
        except (ValueError, IndexError):
            return
        found = which(program)
        if not found:
            return
        real = os.path.realpath(found)
        if real in seen:
            return
        seen.add(real)
        offered.append((caption, command))

    for variable in ("VISUAL", "EDITOR"):
        command = environ.get(variable, "").strip()
        if command:
            offer(command.replace("~", "~~"), command)
    for caption, command in KNOWN:
        offer(caption, command)
    return offered


def actions(found: list[tuple[str, str]]) -> list[Action]:
    """*found* as ``editors.ini`` entries, each ``<& close`` and ``command !.!``: run in a window.

    The window goes as soon as the editor quits, where a command window
    otherwise stays with its output: an editor's last screen is nothing to
    read.  One that fails stays, to say how.  A ``$``, ``!`` or
    ``%`` in the command is the shell's, so written twice, as the user menu's
    language wants it."""
    return [Action(caption, commands_of(["<& close", f"{_literal(command)} !.!"])) for caption, command in found]


def _literal(command: str) -> str:
    """*command* with the user menu's macro characters doubled."""
    return command.replace("$", "$$").replace("!", "!!").replace("%", "%%")
