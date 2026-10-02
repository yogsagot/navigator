"""Bookmarks: the directories Alt+F1, Alt+F2 and Alt+C offer.

**A departure.**  DOS Navigator's ``cmChangeLeft``/``cmChangeRight`` and the
panel's ``cmChangeDrive`` ran ``SelectDrive``: a box of drive letters over the
panel, the panel's own drive selected, and the letter chosen sent the panel to
that drive.  A POSIX file system has one root and no letters, so the same box
lists bookmarked directories instead, and its last entry adds the panel's
directory to them -- or, if it is one already, removes it.

**The first set is written once**, the first time Navigator opens a database
without it: the home directory, the desktop folders in it that exist
(``xdg-user-dirs``' names where ``user-dirs.dirs`` gives them, the English ones
otherwise), and every directory under ``/mnt`` and ``/media``.  A ``Marker``
row records that it was, so a user who removes every bookmark keeps an empty
list rather than getting the defaults back.

The rows are :class:`~navigator.models.bookmark.Bookmark`; a path is stored
absolute, case and all, as the file histories store theirs.
"""

from __future__ import annotations

import getpass
import os
import shlex
from pathlib import Path

from navkit.database import DATABASE

from navigator.models.bookmark import Bookmark
from navigator.models.marker import Marker

#: The ``Marker`` that says the first set has been written.
SEEDED = "bookmarks seeded"

#: The desktop folders, in the order they are offered: the ``XDG_*_DIR`` name
#: ``user-dirs.dirs`` gives each, and the folder to look for without one.
USER_DIRS = (
    ("XDG_DESKTOP_DIR", "Desktop"),
    ("XDG_DOCUMENTS_DIR", "Documents"),
    ("XDG_DOWNLOAD_DIR", "Downloads"),
    ("XDG_MUSIC_DIR", "Music"),
    ("XDG_PICTURES_DIR", "Pictures"),
    ("XDG_VIDEOS_DIR", "Videos"),
)


def key_of(path: Path | str) -> str:
    """The name a directory is bookmarked under: absolute, nothing else changed."""
    return str(Path(path).absolute())


def read_user_dirs(home: Path, config_home: Path) -> dict[str, Path]:
    """What ``user-dirs.dirs`` names, as ``xdg-user-dirs-update`` writes it.

    Lines are ``XDG_DESKTOP_DIR="$HOME/Desktop"``: a shell assignment whose
    value is either ``$HOME/`` and a relative path or an absolute one.  A file
    that is missing or unreadable names nothing.
    """
    try:
        text = (config_home / "user-dirs.dirs").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    found: dict[str, Path] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        try:
            words = shlex.split(value)
        except ValueError:
            continue
        if len(words) != 1:
            continue
        value = words[0]
        if value == "$HOME" or value.startswith("$HOME/"):
            path = home / value[len("$HOME/"):]
        elif value.startswith("/"):
            path = Path(value)
        else:
            continue
        found[name.strip()] = path
    return found


def _subdirectories(path: Path) -> list[Path]:
    try:
        return sorted(child for child in path.iterdir() if child.is_dir())
    except OSError:
        return []


def default_bookmarks(
    home: Path | None = None,
    config_home: Path | None = None,
    mnt: Path = Path("/mnt"),
    media: Path = Path("/media"),
    user: str | None = None,
) -> list[Path]:
    """The first set, in the order it is offered.

    ``/media/$USER`` is where udisks mounts a desktop's removable drives, so
    it is the drives under it that are offered, not the folder itself;
    anything else directly in ``/media`` -- Debian's ``/media/cdrom`` -- is
    offered as it is.  A desktop folder ``user-dirs.dirs`` points at the home
    directory itself is how it says "none", and is left out.
    """
    home = home if home is not None else Path.home()
    if config_home is None:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    if user is None:
        try:
            user = getpass.getuser()
        except (KeyError, OSError):
            user = home.name
    named = read_user_dirs(home, config_home)
    found: list[Path] = [home]
    for variable, folder in USER_DIRS:
        path = named.get(variable, home / folder)
        if path != home and path.is_dir():
            found.append(path)
    found.extend(_subdirectories(mnt))
    for child in _subdirectories(media):
        if child.name == user:
            found.extend(_subdirectories(child))
        else:
            found.append(child)
    unique: list[Path] = []
    for path in found:
        if path not in unique:
            unique.append(path)
    return unique


def seed_bookmarks(paths: list[Path] | None = None) -> bool:
    """Write the first set unless it has been written before; True if it was now."""
    with DATABASE.transaction():
        if Marker.where(name=SEEDED).exists():
            return False
        for path in default_bookmarks() if paths is None else paths:
            add_bookmark(path)
        Marker.create(name=SEEDED)
    return True


def bookmarks() -> list[Bookmark]:
    """Every bookmark, in the order the box lists them."""
    return Bookmark.where().order("seq").all()


def find_bookmark(path: Path | str) -> Bookmark | None:
    return Bookmark.get(path=key_of(path))


def add_bookmark(path: Path | str) -> Bookmark:
    """*path* bookmarked, after every other; one already bookmarked stays where it is."""
    key = key_of(path)
    existing = Bookmark.get(path=key)
    if existing is not None:
        return existing
    last = Bookmark.where().order("-seq").first()
    return Bookmark.create(path=key, seq=(last.seq + 1) if last is not None else 1)


def remove_bookmark(path: Path | str) -> bool:
    """*path* no longer bookmarked; False if it was not."""
    return Bookmark.where(path=key_of(path)).delete() > 0
