"""Alt+L's list file: DOS Navigator's ``MakeListFile`` (FILECOPY.PAS).

One line per file -- its name, or its whole path -- or, given an *action*,
one line per file for each of the action's ``;``-separated templates (``;;``
is a ``;``): a script built from the selection.  A template's macros are the
user menu's for one file: ``!`` its name without the extension, ``.!`` the
extension, ``!\\`` its directory ending in ``/``, ``!/`` the same without,
``!:`` its drive (nothing, on POSIX), ``!!`` a ``!``.  A template with none
of them is followed by the file, as ``cp`` becomes ``cp name``.

Path names go in with *Store path names*, or, with *Autodetermine*, for a
file whose directory is not the list's -- and then a template naming the
file without its directory gets ``!\\`` put in before the name, as DN did.

Departures, the user menu's (:mod:`navigator.usermenu`): in an action's
lines every value is quoted for the shell where it needs it, a plain list
keeps names as they are; ``.!`` of a name without an extension is nothing,
where DN's was ``.`` -- ``README.`` is not ``README`` here.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Iterable

#: What the *File name* line holds when its history is empty: DN's
#: ``DNLIST.BAT``, which a POSIX shell would not run as one.
DEFAULT_NAME = "dnlist.txt"

#: The two boxes, as DN's ``Options`` bits.
STORE_PATHS = 1
AUTO_PATHS = 2

_TOKEN = re.compile(r"!!|!\\|!/|!:|\.!|!")
_DIRECTORY = ("!\\", "!/", "!:")


def templates(action: str) -> list[str]:
    """*action* split at ``;``, ``;;`` kept as one; empty for no action."""
    action = action.rstrip()
    if not action:
        return []
    return [part.replace("\0", ";") for part in action.replace(";;", "\0").split(";")]


def _split(name: str) -> tuple[str, str]:
    dot = name.rfind(".")
    if dot <= 0:
        return name, ""
    return name[:dot], name[dot:]


def _force_directory(template: str) -> str:
    """``!\\`` put before the file's name in *template*, where DN found room."""
    masked = template.replace("!!", "\0\0")
    if any(macro in masked for macro in _DIRECTORY):
        return template
    at = masked.find(".!")
    if at >= 0:
        if at == 0 or masked[at - 1] != "!":
            return template  # nowhere to put it (``Fail``)
        at -= 1
    else:
        at = masked.find("!")
        if at < 0:
            return template
    return template[:at] + "!\\" + template[at:]


def line(template: str, path: Path, with_path: bool, forced: bool) -> str:
    """*template* for *path*: its macros in, or the file after it."""
    if forced:
        template = _force_directory(template)
    stem, extension = _split(path.name)
    directory = str(path.parent)
    used = False

    def value(match: re.Match[str]) -> str:
        nonlocal used
        token = match.group()
        if token == "!!":
            return "!"
        used = True
        if token == "!\\":
            found = directory if directory.endswith("/") else directory + "/"
        elif token == "!/":
            found = directory
        elif token == "!:":
            found = ""
        elif token == ".!":
            found = extension
        else:
            found = stem
        return shlex.quote(found) if found else found

    text = _TOKEN.sub(value, template)
    if used:
        return text
    target = str(path) if with_path else path.name
    return f"{template.rstrip()} {shlex.quote(target)}"


def make_lines(files: Iterable[Path], action: str, list_dir: Path, options: int) -> list[str]:
    """The list file's lines for *files*, written into *list_dir*."""
    found: list[str] = []
    parts = templates(action)
    for path in files:
        elsewhere = bool(options & AUTO_PATHS) and path.parent != list_dir
        with_path = bool(options & STORE_PATHS) or elsewhere
        if not parts:
            found.append(str(path) if with_path else path.name)
            continue
        found.extend(line(part, path, with_path, elsewhere) for part in parts)
    return found
