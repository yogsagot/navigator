"""Where Help's pages are, and reading one.

The pages are Markdown under ``docs/``, one directory a language, every one
with the tree ``docs/en/`` has (the ``navigator-help`` skill).  A page is
named by its path under the language's directory, as a link between pages
spells it -- ``clipboard.md``, ``editor/macros.md`` -- and a **topic id** is
that with an optional heading anchor, ``file-operations.md#copy``: what a
dialog names as its help, DN's help context.

Everything that reads here can wait on a disk, so it is called on a thread
(``navml.background.Background``), and takes the language as a plain string:
a thread never reads ``LOCALE``, which is reactive.

Installed, the pages are ``navigator/docs/`` (``setup.py`` puts ``docs/``
there); in a checkout they are ``docs/`` beside the package.  One of the two
exists, and :func:`root` finds it.
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

from navkit.screen import Cell

from . import ansi

#: The language every page exists in, and the one a missing page falls back to.
ENGLISH = "en"
#: The contents page: where F1 opens with no topic, and Shift+F1's *Index*.
CONTENTS = "README.md"
#: F1 inside Help: *Help on help*.
HELP_ON_HELP = "help.md"

_LANGUAGE = re.compile(r"[A-Za-z]{2,3}(_[A-Za-z]{2,4})?\Z")
_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")


class PageNotFound(LookupError):
    """No such page, in the language asked for or in English."""


@dataclass(frozen=True)
class Page:
    """A page as read: its Markdown, and which language's it turned out to be."""

    name: str
    data: bytes
    language: str


def root() -> Traversable:
    """The directory holding the language directories."""
    package = files("navigator")
    installed = package.joinpath("docs")
    if installed.is_dir():
        return installed
    # A checkout: ``docs/`` is beside the package, not in it.
    return Path(str(package)).parent / "docs"


def split(topic: str) -> tuple[str, str]:
    """A topic id as its page and its anchor (``""`` for the top)."""
    name, _, anchor = topic.partition("#")
    return name, anchor


def follow(page: str, href: str) -> str | None:
    """The topic id a link *href* on *page* leads to, or None when it leads
    out of Help: another site (``https:``, ``mailto:``), or above the
    language's directory.

    ``#anchor`` alone stays on *page*; anything else is relative to the
    directory *page* is in, as GitHub reads it.
    """
    if _SCHEME.match(href) or href.startswith("/"):
        return None
    target, _, anchor = href.partition("#")
    name = posixpath.normpath(posixpath.join(posixpath.dirname(page), target)) if target else page
    if name == ".." or name.startswith("../") or name == ".":
        return None
    return f"{name}#{anchor}" if anchor else name


def _languages(language: str) -> list[str]:
    """Where to look, in order: the language, its bare code (``pt_BR`` then
    ``pt``), English."""
    wanted = [language, language.split("_")[0]] if _LANGUAGE.match(language) else []
    return list(dict.fromkeys([*wanted, ENGLISH]))


def _find(name: str, language: str) -> tuple[Traversable, str] | None:
    """The file *name* names, in the first language that has it."""
    parts = posixpath.normpath(name).split("/")
    if not name or parts[0] in ("..", "", "."):
        return None
    base = root()
    for code in _languages(language):
        found = base.joinpath(code, *parts)
        if found.is_file():
            return found, code
    return None


def read(name: str, language: str) -> Page:
    """The page *name* in *language*, else in English.  Blocking.

    Raises :class:`PageNotFound` when neither has it.
    """
    found = _find(name, language)
    if found is None:
        raise PageNotFound(name)
    file, code = found
    return Page(posixpath.normpath(name), file.read_bytes(), code)


def exists(topic: str, language: str = ENGLISH) -> bool:
    """Whether *topic*'s page is there (its anchor is the layout's to find).  Blocking."""
    return _find(split(topic)[0], language) is not None


def shot(page: str, source: str, language: str) -> list[list[Cell]] | None:
    """The cells of the picture a page names as ``![alt](source)``.  Blocking.

    *source* is the SVG GitHub shows; what is read is the ``.ans`` beside it
    (``tools/screenshot.py`` writes both), in *language*'s ``shots/`` or else
    English's.  None when the picture is no screenshot of ours, has no
    ``.ans``, or the file is not one the tool wrote: the page then shows the
    alt text.
    """
    name = follow(page, source)
    if name is None or "#" in name or not name.endswith(".svg"):
        return None
    found = _find(name[: -len(".svg")] + ".ans", language)
    if found is None:
        return None
    try:
        return ansi.read(found[0].read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
