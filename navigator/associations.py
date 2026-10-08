"""What runs for a file or a key: DOS Navigator's ``DN.EXT``, ``DN.VWR``,
``DN.EDT`` and ``DN.XRN``, as ``.ini`` files.

DN kept four text files of its own formats beside DN.EXE, each telling it
what to run: ``DN.EXT`` for Enter on a file by its extension (``ExecFile``),
``DN.VWR`` and ``DN.EDT`` for the viewer and editor a file's extension wants
(``ExecExtFile``), and ``DN.XRN`` for Ctrl+Shift+F1 .. F10's *Quick run*
(``QuickExecExternal``).  Here they are one format -- a departure, by
request: an ``.ini`` file each, beside ``navigator.ini``:

- :data:`EXTENSIONS` (``extensions.ini``), :data:`VIEWERS` (``viewers.ini``)
  and :data:`EDITORS` (``editors.ini``): a section is a mask, the panel's own
  ``;``-separated shell patterns (``[*.tar.gz;*.tgz]``), matched without
  regard to case as DN's extensions were.  The first section that matches
  wins.
- :data:`QUICK_RUN` (``quickrun.ini``): a section is a key, ``[F1]`` ..
  ``[F10]``.

In a section every key is a caption and its value what runs: one line or
several, indented under the first, in the user menu's language --
``!.!`` the file, ``!\\`` its directory, ``%1`` the tagged list, ``<Title``
and ``<=text`` and ``%3`` .. ``%9`` asking for parameters
(:mod:`navigator.usermenu`).  A section with one entry runs it; one with
several offers them in a menu, as DN's Alt+Enter offered ``DN.EXT``'s
``[ ]`` menu -- Navigator keeps Alt+Enter for *Insert name*, so the menu is
what several entries mean rather than a key of its own, and DN's
Shift+Enter variant (``( )``) has no key and so no place.

The files are only ever read whole, on a thread: :func:`read`.  Each is
written from its template the first time Navigator starts without it
(:func:`seed_all`), as DN's came filled in.
"""

from __future__ import annotations

import configparser
import fnmatch
from dataclasses import dataclass
from pathlib import Path

from navigator.filetypes import patterns
from navigator.settings import config_dir
from navigator.usermenu import Commands, commands_of

#: Enter on a file that is not to be run itself: DN's ``DN.EXT``.
EXTENSIONS = "extensions.ini"
#: The viewer a file wants: DN's ``DN.VWR``.
VIEWERS = "viewers.ini"
#: The editor a file wants: DN's ``DN.EDT``.
EDITORS = "editors.ini"
#: Ctrl+Shift+F1 .. F10: DN's ``DN.XRN``.
QUICK_RUN = "quickrun.ini"


@dataclass(frozen=True)
class Action:
    """One entry of a section: its caption, and what it runs."""

    caption: str
    commands: Commands


@dataclass(frozen=True)
class Group:
    """One section: its name -- a mask, or a key -- and its entries in order."""

    name: str
    actions: tuple[Action, ...]

    def matches(self, file_name: str) -> bool:
        """Whether *file_name* is one of this section's, case aside."""
        name = file_name.lower()
        return any(fnmatch.fnmatchcase(name, pattern.lower()) for pattern in patterns(self.name))


def path_of(file_name: str) -> Path:
    """Where *file_name* (one of the four) lives: beside ``navigator.ini``."""
    return config_dir() / file_name


def parse(text: str, source: str = "<string>") -> list[Group]:
    """*text* as sections, or ``ValueError`` saying where it is not an ``.ini``.

    Captions keep their case, ``=`` alone separates a caption from its
    commands (a ``:`` belongs to the shell), and nothing on a line is a
    comment -- ``;`` and ``#`` are the shell's there -- but a line that
    starts with either.
    """
    parser = configparser.ConfigParser(
        interpolation=None, delimiters=("=",), comment_prefixes=("#", ";"),
        inline_comment_prefixes=None, empty_lines_in_values=False, default_section="\0",
    )
    parser.optionxform = str  # type: ignore[assignment,method-assign]
    try:
        parser.read_string(text, source)
    except configparser.Error as error:
        raise ValueError(str(error)) from None
    return [
        Group(name, tuple(Action(caption, commands_of(value.splitlines()))
                          for caption, value in parser.items(name)))
        for name in parser.sections()
    ]


def read(file_name: str) -> list[Group]:
    """The sections of *file_name* (one of the four); none when it is missing.

    Touches the file system: run it on a thread.  ``OSError`` for a file that
    is there and will not read, ``ValueError`` for one that is not an ``.ini``.
    """
    path = path_of(file_name)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return []
    return parse(text, str(path))


def for_file(groups: list[Group], file_name: str) -> Group | None:
    """The first section whose mask takes *file_name*, or None."""
    return next((group for group in groups if group.actions and group.matches(file_name)), None)


def for_key(groups: list[Group], key: str) -> Group | None:
    """The section named *key* (``F1``, any case), or None."""
    return next((group for group in groups if group.actions and group.name.lower() == key.lower()), None)


#: What the four files hold when Options opens one that is not there yet:
#: the format, and an example to change -- DN shipped its files filled in.
TEMPLATES = {
    EXTENSIONS: """\
# Enter on a file that is not itself a program: what runs, by the file's name.
# Options > Extension file edit.  A section is a mask (`;'-separated patterns,
# case aside); the first that matches wins.  Each line below it is
# `Caption = commands': one entry runs at once, several are offered in a menu.
# Commands may go on over indented lines, in the user menu's language: !.! is
# the file, !\\ its directory, %1 a file listing the tagged names, and <Title,
# <=default or %3..%9 ask for parameters first.

[*.tar;*.tar.gz;*.tgz;*.tar.bz2;*.tar.xz]
List = tar tvf !.!
Extract here = tar xvf !.!

[*.py]
Run = python3 !.!
""",
    VIEWERS: """\
# The viewer a file wants: what F3 runs with System Setup's Internal viewer
# off, and Alt+F3 (Alternate view) with it on.  A file no section takes is
# viewed as before.  Options > Viewers.  The format is extensions.ini's: a
# mask, then `Caption = commands', several offered in a menu; !.! is the file.

[*.pdf]
PDF viewer = xdg-open !.!
""",
    EDITORS: """\
# The editor a file wants: what F4 runs with System Setup's Internal editor
# off, and Alt+F4 (Alternate edit) with it on.  A file no section takes is
# edited as before.  Options > Editors.  The format is extensions.ini's: a
# mask, then `Caption = commands', several offered in a menu; !.! is the file.

[*.odt;*.docx]
Word processor = libreoffice !.!
""",
    QUICK_RUN: """\
# Quick run: Ctrl+Shift+F1 .. F10 run their section, [F1] .. [F10], from the
# panels.  Options > Quick run file edit.  Each line is `Caption = commands':
# one runs at once, several are offered in a menu.  The user menu's macros
# work here: !.! is the file at the cursor, <Title asks for parameters.

[F1]
Disk usage = du -sh !\\*
""",
}


def seed(file_name: str) -> bool:
    """Write *file_name* (one of the four) from its template if it is not there.

    True when it was written, False when it was there already; ``OSError``
    when it could not be.  Never overwrites: the file is created exclusively.
    """
    path = path_of(file_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(TEMPLATES[file_name])
    except FileExistsError:
        return False
    return True


def seed_all() -> list[str]:
    """Each of the four that is missing written from its template, as
    ``navigator.ini`` is written with its defaults at the first start.

    A complaint for each that could not be, rather than an exception: a file
    that cannot be written only leaves its association empty.
    """
    problems = []
    for file_name in TEMPLATES:
        try:
            seed(file_name)
        except OSError as error:
            problems.append(f"{path_of(file_name)}: {error.strerror or error}")
    return problems
