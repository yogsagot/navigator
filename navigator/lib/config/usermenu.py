"""F2's user menu: ``menu.ini``, what was DOS Navigator's ``dn.mnu`` (USERMENU.PAS).

**The file** is ``.ini``-shaped, as ``extensions.ini`` and its siblings are
(:mod:`navigator.lib.config.associations`), though read line by line here
since a menu keeps separators, repeated captions and its own order:

- ``Caption = command`` is an item; indented lines under it are more of its
  commands, up to a blank line or the next item.  ``Caption =`` runs nothing.
- ``[Archive]`` starts a submenu, ``[Archive/Compress]`` one inside it --
  ancestors not seen yet are made on the way.  Items before any header are the
  top menu, and ``[/]`` goes back to it.  A submenu sits in its parent where
  its header first appears; naming it again goes on adding to it.  A path's
  parts are compared as written, ``~`` and all; a submenu left empty is
  dropped.
- A line of only ``-`` is a separator.
- A line starting ``#`` or ``;`` is a comment.

A caption may mark its letter with ``~``, and one starting ``F1 `` .. ``F12 ``
is chosen by that key from anywhere in the menu (``CheckFKeys``).  In an
item's commands, ``<Title`` titles the box asking for parameters and
``<=text`` fills it in; either, or a ``%3`` .. ``%9``, has the box asked.
A line of only ``<|`` panelizes the item: what it prints becomes the active
panel's listing, a name a line, rather than being shown in the console (a
departure, :mod:`navigator.lib.file_ops.panelize`).
A ``<&`` line runs it in a window of its own rather than on the console (a
departure, ``TerminalWindow``), opened as System Setup's *Command windows*
say unless the words after it do: ``zoomed`` or ``normal``, ``modal`` or
``floating`` (``<& normal modal``).  With a word it does not know it is a
``<Title`` as before; ``<|`` wins over it.  A command line starting ``&``
does the same as a bare ``<&``, as ``&`` does on the command line
(``Run = &./!.!``), the ``&`` taken off.

**Where it is** (``ExecUserMenu``): F2 looks for ``.navigator-menu.ini`` in
the active panel's directory and then in each one above it -- the *local*
menu -- and uses the *global* one, ``menu.ini`` beside ``navigator.ini``,
when there is none.  F2 in the box changes between the two, F4 edits the one
shown.  The global one is written from ``navigator/assets/menu.ini`` the first
time Navigator starts without it.

**The macros** (``MakeString``), in captions and in what runs: ``!`` the
active panel's file without its extension, ``.!`` its extension with the dot,
``!\\`` its directory ending in ``/``, ``!/`` the same without the ``/``,
``!:`` nothing (DN's drive); ``$``, ``.$``, ``$\\``, ``$/`` and ``$:`` the
passive panel's; ``!!`` and ``$$`` a ``!`` and a ``$``.  So ``!.!`` is the
file's name, and ``!\\!.!`` its whole path.  What runs also has numbered
parameters: ``%1`` a file listing the active panel's tagged names (or the one
at the cursor), ``%2`` the passive panel's, ``%3`` .. ``%9`` the words typed
as parameters, ``%0`` the script, ``%%`` a ``%``.

Departures, each for the shell rather than COMMAND.COM:

- **What runs is quoted for the shell**: a name with a blank in it is one
  word.  Quotes are added only where a name needs them (``shlex.quote``), so
  a macro needs none around it -- and one put inside the file's own quotes
  would show them.  Captions are shown as they are.
- **Names keep their case**; DN lowered them, as DOS's were all one case.
- **The lines run in the console's own shell**, sourced, as though typed:
  they are that shell's language, a ``cd`` among them stays, and ``$`` has
  to be written ``$$`` to reach the shell, as it had in DN.  A command line
  starting ``;`` is dropped, as is a blank one.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from navigator.settings import config_dir

#: The global menu's name, beside ``navigator.ini``.
GLOBAL_NAME = "menu.ini"
#: A local menu's name, in a directory the panel shows or one above it.
LOCAL_NAME = ".navigator-menu.ini"

#: Every macro and batch parameter, longest first where two share a start.
_TOKEN = re.compile(r"\$\$|!!|\.!|\.\$|[!$][:\\/]|[!$]|%[0-9%]")

#: A caption's function key: ``F1 `` .. ``F12 `` at its start.
_FKEY = re.compile(r"^f(1[0-2]|[1-9]) ", re.IGNORECASE)

#: A separator: a line of dashes.
_LINE = re.compile(r"-+")


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


#: The words a ``<&`` line takes, and what each says of the window.
_WINDOW_WORDS = {
    "zoomed": ("zoomed", True), "normal": ("zoomed", False),
    "modal": ("modal", True), "floating": ("modal", False),
}


@dataclass(frozen=True)
class WindowMode:
    """How a ``<&`` item's window opens; None is System Setup's say."""

    zoomed: bool | None = None
    modal: bool | None = None


def window_mode(text: str) -> WindowMode | None:
    """``<&`` and its words as a :class:`WindowMode`; None if *text* is not one."""
    if not text.startswith("<&"):
        return None
    words = text[2:].lower().split()
    if any(word not in _WINDOW_WORDS for word in words):
        return None
    return WindowMode(**dict(_WINDOW_WORDS[word] for word in words))


@dataclass(frozen=True)
class Commands:
    """An item's lines, and whether and how to ask for parameters first."""

    lines: list[str]
    asks: bool = False
    title: str = ""
    default: str = ""
    #: A ``<|`` line: the output is the active panel's listing.
    panelize: bool = False
    #: A ``<&`` line: run in a window of its own, opened so.
    window: WindowMode | None = None


@dataclass
class Entry:
    """An item, a submenu (with *children*) or a separator (*is_line*)."""

    caption: str = ""
    commands: Commands | None = None
    children: list["Entry"] = field(default_factory=list)
    is_line: bool = False

    @property
    def fkey(self) -> str | None:
        """``f5`` for a caption starting ``F5 ``; None without one."""
        found = _FKEY.match(self.caption)
        return f"f{found.group(1)}" if found else None


@dataclass
class Menu:
    """A read ``menu.ini``: its items as a tree."""

    path: Path
    is_global: bool
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

    def commands(self, entry: Entry) -> Commands:
        """What choosing *entry* runs."""
        return entry.commands or Commands([])


def commands_of(body: Iterable[str]) -> Commands:
    """An item's lines as what runs: ``<Title`` and ``<=text`` taken out for
    the parameters box, ``;`` lines and blank ones dropped, and whether a
    ``%3`` .. ``%9`` among them asks for parameters too; a ``<|`` line
    panelizes it, a ``<&`` line -- or one starting ``&`` -- runs it in a window."""
    lines: list[str] = []
    title = default = ""
    asks = panelize = False
    window: WindowMode | None = None
    for raw in body:
        text = raw.strip()
        if not text or text.startswith(";"):
            continue
        if text == "<|":
            panelize = True
            continue
        mode = window_mode(text)
        if mode is not None:
            window = mode
            continue
        if text.startswith("<"):
            asks = True
            rest = text[1:]
            if rest.startswith("="):
                default = rest[1:]
            else:
                title = rest.lstrip()
            continue
        if text.startswith("&"):
            # ``&command``, as on the command line: the item runs in a window,
            # opened as a bare ``<&`` would.  No shell line starts with ``&``.
            text = text[1:].lstrip()
            window = window or WindowMode()
            if not text:
                continue
        lines.append(text)
        asks = asks or bool(re.search(r"(?<!%)%[3-9]", text))
    return Commands(lines, asks, title, default, panelize, window)


def parse(text: str, path: Path = Path(GLOBAL_NAME), is_global: bool = False) -> Menu:
    """*text* as a menu, or ``ValueError`` naming the line that is neither an
    item, a header, a separator nor a comment."""
    root: list[Entry] = []
    #: Each submenu made so far, by its path from the top.
    menus: dict[tuple[str, ...], Entry] = {}
    into = root
    #: The item whose commands an indented line goes on, and its lines so far.
    item: Entry | None = None
    body: list[str] = []

    def close() -> None:
        nonlocal item
        if item is not None:
            item.commands = commands_of(body)
            item = None

    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            close()
            continue
        if raw[0].isspace() and item is not None:
            body.append(line)
            continue
        close()
        if line[0] in "#;":
            continue
        if line.startswith("["):
            if not line.endswith("]"):
                raise ValueError(f"line {number}: a header must end with ']'")
            parts = tuple(part.strip() for part in line[1:-1].split("/") if part.strip())
            into = root
            for depth in range(1, len(parts) + 1):
                submenu = menus.get(parts[:depth])
                if submenu is None:
                    submenu = menus[parts[:depth]] = Entry(parts[depth - 1])
                    into.append(submenu)
                into = submenu.children
            continue
        if _LINE.fullmatch(line):
            into.append(Entry(is_line=True))
            continue
        caption, equals, command = line.partition("=")
        if not equals:
            raise ValueError(f"line {number}: expected 'Caption = command'")
        item = Entry(caption.strip())
        body = [command]
        into.append(item)
    close()
    return Menu(path, is_global, _prune(root))


def _prune(entries: list[Entry]) -> list[Entry]:
    """*entries* without the submenus that came to hold no item."""
    kept = []
    for entry in entries:
        if entry.commands is None and not entry.is_line:
            entry.children = _prune(entry.children)
            if not any(not child.is_line for child in entry.children):
                continue
        kept.append(entry)
    return kept


def global_menu() -> Path:
    """The global ``menu.ini``: beside ``navigator.ini``."""
    return config_dir() / GLOBAL_NAME


def local_menu(start: Path) -> Path | None:
    """The nearest ``.navigator-menu.ini`` in *start* or a directory above it, or None."""
    for directory in (start, *start.parents):
        candidate = directory / LOCAL_NAME
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
