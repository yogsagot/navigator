"""F2's user menu: DOS Navigator's ``dn.mnu`` (USERMENU.PAS), read for POSIX.

**The file.**  An item is a line ``>N Caption``, *N* its depth from 1; the
lines under it, up to the next ``>`` line, are what choosing it runs.  An item
with deeper ones under it is a submenu instead.  ``>N`` with no caption is a
separator.  A caption may mark its letter with ``~``, and one starting
``F1 `` .. ``F12 `` is chosen by that key from anywhere in the menu
(``CheckFKeys``).  In an item's lines, ``<Title`` titles the box asking for
parameters and ``<=text`` fills it in; either, or a ``%3`` .. ``%9``, has the
box asked.  ``>>N`` was DN's *run through COMMAND.COM's int 2Eh*, and is read
as ``>N``.

**Where it is** (``ExecUserMenu``): F2 looks for ``dn.mnu`` in the active
panel's directory and then in each one above it -- the *local* menu -- and
uses the *global* one, ``dn.mnu`` beside ``navigator.ini``, when there is
none.  F2 in the box changes between the two, F4 edits the one shown.

**The macros** (``MakeString``), in captions and in what runs: ``!`` the
active panel's file without its extension, ``.!`` its extension with the dot,
``!\\`` its directory ending in ``/``, ``!/`` the same without the ``/``,
``!:`` its drive -- nothing, on POSIX; ``$``, ``.$``, ``$\\``, ``$/`` and
``$:`` the passive panel's; ``!!`` and ``$$`` a ``!`` and a ``$``.  So
``!.!`` is the file's name, and ``!\\!.!`` its whole path.  What runs also
has DOS's batch parameters, which COMMAND.COM put in as text and Navigator
puts in the same way: ``%1`` a file listing the active panel's tagged names
(or the one at the cursor), ``%2`` the passive panel's, ``%3`` .. ``%9`` the
words typed as parameters, ``%0`` the script, ``%%`` a ``%``.

Departures, each for the shell rather than COMMAND.COM:

- **What runs is quoted for the shell**: a name with a blank in it is one
  word.  Quotes are added only where a name needs them (``shlex.quote``), so
  a macro needs none around it -- and one put inside the file's own quotes
  would show them.  Captions are shown as they are.
- **Names keep their case**; DN lowered them, as DOS's were all one case.
- **The lines run in the console's own shell**, sourced, as though typed:
  they are that shell's language, a ``cd`` among them stays, and ``$`` has
  to be written ``$$`` to reach the shell, as it had in DN.  A line starting
  ``;`` is a comment, and a blank one is dropped.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from navigator.settings import config_dir

#: The file's name, local and global alike, as DN's was.
MENU_NAME = "dn.mnu"

#: Every macro and batch parameter, longest first where two share a start.
_TOKEN = re.compile(r"\$\$|!!|\.!|\.\$|[!$][:\\/]|[!$]|%[0-9%]")

#: A caption's function key: ``F1 `` .. ``F12 `` at its start.
_FKEY = re.compile(r"^f(1[0-2]|[1-9]) ", re.IGNORECASE)


@dataclass(frozen=True)
class Side:
    """One panel, as the macros see it: the file at its cursor, and its list."""

    directory: str = ""
    name: str = ""
    extension: str = ""
    #: The file listing its tagged names, or ``-`` without one (DN's).
    list_file: str = "-"

    @classmethod
    def of(cls, directory: Path, file_name: str | None, list_file: str = "-") -> "Side":
        """*file_name* in *directory*, split as ``FSplit`` split it."""
        stem, extension = _split(file_name or "")
        return cls(str(directory), stem, extension, list_file)


def _split(name: str) -> tuple[str, str]:
    """``FSplit``'s name and extension; a dot-file's dot is its name's."""
    dot = name.rfind(".")
    if dot <= 0 or name == "..":
        return name, ""
    return name[:dot], name[dot:]


@dataclass
class Entry:
    """A ``>N`` line: its depth, its caption, and where it is in the file."""

    level: int
    caption: str
    line: int
    children: list["Entry"] = field(default_factory=list)

    @property
    def is_line(self) -> bool:
        return not self.caption and not self.children

    @property
    def fkey(self) -> str | None:
        """``f5`` for a caption starting ``F5 ``; None without one."""
        found = _FKEY.match(self.caption)
        return f"f{found.group(1)}" if found else None


@dataclass
class Menu:
    """A read ``dn.mnu``: its lines, and its items as a tree."""

    path: Path
    is_global: bool
    lines: list[str]
    items: list[Entry]

    def walk(self) -> list[Entry]:
        """Every item, depth first, in the file's order."""
        found: list[Entry] = []

        def visit(entries: list[Entry]) -> None:
            for entry in entries:
                found.append(entry)
                visit(entry.children)

        visit(self.items)
        return found

    def commands(self, entry: Entry) -> "Commands":
        """What choosing *entry* runs: its lines, up to the next ``>`` line."""
        body: list[str] = []
        for raw in self.lines[entry.line + 1:]:
            if raw.strip().startswith(">"):
                break
            body.append(raw)
        return commands_of(body)


@dataclass(frozen=True)
class Commands:
    """An item's lines, and whether and how to ask for parameters first."""

    lines: list[str]
    asks: bool = False
    title: str = ""
    default: str = ""


def commands_of(body: Iterable[str]) -> Commands:
    """An item's lines as what runs: ``<Title`` and ``<=text`` taken out for
    the parameters box, ``;`` lines and blank ones dropped, and whether a
    ``%3`` .. ``%9`` among them asks for parameters too."""
    lines: list[str] = []
    title = default = ""
    asks = False
    for raw in body:
        text = raw.strip()
        if not text or text.startswith(";"):
            continue
        if text.startswith("<"):
            asks = True
            rest = text[1:]
            if rest.startswith("="):
                default = rest[1:]
            else:
                title = rest.lstrip()
            continue
        lines.append(text)
        asks = asks or bool(re.search(r"(?<!%)%[3-9]", text))
    return Commands(lines, asks, title, default)


def parse(text: str, path: Path = Path(MENU_NAME), is_global: bool = False) -> Menu:
    """*text* as a menu: every ``>N`` line, nested by *N*."""
    lines = text.splitlines()
    root: list[Entry] = []
    stack: list[Entry] = []
    for index, raw in enumerate(lines):
        text_line = raw.strip()
        if not text_line.startswith(">"):
            continue
        rest = text_line[1:]
        if rest.startswith(">"):
            rest = rest[1:]
        number, _, caption = rest.partition(" ")
        try:
            level = int(number)
        except ValueError:
            continue
        if level <= 0:
            continue
        entry = Entry(level, caption, index)
        while stack and stack[-1].level >= level:
            stack.pop()
        (stack[-1].children if stack else root).append(entry)
        stack.append(entry)
    return Menu(path, is_global, lines, root)


def global_menu() -> Path:
    """The global ``dn.mnu``: beside ``navigator.ini``, where DN's was beside DN."""
    return config_dir() / MENU_NAME


def local_menu(start: Path) -> Path | None:
    """The nearest ``dn.mnu`` in *start* or a directory above it, or None."""
    for directory in (start, *start.parents):
        candidate = directory / MENU_NAME
        if candidate.is_file():
            return candidate
    return None


def find_menu(start: Path, want_global: bool = False) -> tuple[Path, bool] | None:
    """Which menu F2 shows from *start*: the local one, else the global one.

    ``(path, is_global)``, or None when neither exists (``dlMNUNotFound``).
    Touches the file system: run it on a thread.
    """
    if not want_global:
        local = local_menu(start)
        if local is not None:
            return local, False
    path = global_menu()
    return (path, True) if path.is_file() else None


def expand(text: str, active: Side, passive: Side, *, script: str = "",
           params: str = "", quote: bool = True) -> str:
    """*text* with its macros put in: quoted for the shell unless *quote* is off.

    One pass, so what a macro puts in -- a name with a ``%`` or a ``!`` in it
    -- is never read as another.
    """
    words = params.split()

    def value(token: str) -> str:
        if token == "$$":
            return "$"
        if token == "!!":
            return "!"
        if token == "%%":
            return "%"
        if token.startswith("%"):
            number = int(token[1])
            if number == 0:
                found = script
            elif number == 1:
                found = active.list_file
            elif number == 2:
                found = passive.list_file
            else:
                return words[number - 3] if number - 3 < len(words) else ""
        else:
            side = active if "!" in token else passive
            kind = token.replace("$", "!")
            directory = side.directory
            if kind == ".!":
                found = side.extension
            elif kind == "!:":
                found = ""
            elif kind == "!\\":
                found = directory if directory.endswith("/") else directory + "/"
            elif kind == "!/":
                found = directory if directory == "/" else directory.rstrip("/")
            else:
                found = side.name
        return shlex.quote(found) if quote and found else found

    return _TOKEN.sub(lambda match: value(match.group()), text)


def caption(entry: Entry, active: Side, passive: Side) -> str:
    """What the box shows for *entry*: its macros in, nothing quoted."""
    return expand(entry.caption, active, passive, quote=False)


def script_text(commands: Commands, active: Side, passive: Side, script: str,
                params: str = "") -> str:
    """The script an item runs: its lines with every macro and parameter in."""
    return "".join(
        expand(line, active, passive, script=script, params=params) + "\n"
        for line in commands.lines
    )
