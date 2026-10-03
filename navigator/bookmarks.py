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

**The mounts are read again every time the box opens** (:func:`mounted_places`):
whatever is mounted under ``/mnt``, ``/media`` or ``/run/media/$USER`` now and
is not bookmarked is offered below the bookmarks, unstored, as DN's box
offered the drives there were at the time it opened.

The rows are :class:`~navigator.models.bookmark.Bookmark`; a path is stored
absolute, case and all, as the file histories store theirs.
"""

from __future__ import annotations

import getpass
import os
import re
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


def _user(home: Path) -> str:
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return home.name


def _mount_directories(mnt: Path, media: Path, run_media: Path, user: str) -> list[Path]:
    """The directories where drives are mounted, mounted or not.

    ``/media/$USER`` is where udisks mounts a desktop's removable drives
    (``/run/media/$USER`` on Fedora and Arch), so it is the drives under it
    that are offered, not the folder itself; anything else directly in
    ``/media`` -- Debian's ``/media/cdrom`` -- is offered as it is.
    """
    found = list(_subdirectories(mnt))
    for child in _subdirectories(media):
        if child.name == user:
            found.extend(_subdirectories(child))
        else:
            found.append(child)
    found.extend(_subdirectories(run_media / user))
    return found


def _unescape_mount(field: str) -> str:
    r"""A ``/proc/self/mounts`` path with its octal escapes (``\040`` for a space) undone."""
    return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), field)


def mounted_places(
    mounts: Path = Path("/proc/self/mounts"),
    mnt: Path = Path("/mnt"),
    media: Path = Path("/media"),
    run_media: Path = Path("/run/media"),
    user: str | None = None,
) -> list[Path]:
    """What is mounted under ``/mnt``, ``/media`` and ``/run/media/$USER`` now.

    Read from *mounts*, so an empty mount point is not offered; a system
    without ``/proc`` gets every directory where a drive would be instead,
    as the first set does.  Only direct children count: a drive is mounted
    at ``/mnt/usb``, and what is mounted inside it is the drive's business.
    """
    user = user if user is not None else _user(Path.home())
    try:
        text = mounts.read_text(encoding="utf-8", errors="surrogateescape")
    except OSError:
        return _mount_directories(mnt, media, run_media, user)
    parents = {mnt, media, media / user, run_media / user}
    found: set[Path] = set()
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 2:
            continue
        point = Path(_unescape_mount(fields[1]))
        if point.parent in parents and point != media / user:
            found.add(point)
    return sorted(found)


def default_bookmarks(
    home: Path | None = None,
    config_home: Path | None = None,
    mnt: Path = Path("/mnt"),
    media: Path = Path("/media"),
    user: str | None = None,
    run_media: Path = Path("/run/media"),
) -> list[Path]:
    """The first set, in the order it is offered.

    A desktop folder ``user-dirs.dirs`` points at the home directory itself
    is how it says "none", and is left out; the drives are
    :func:`_mount_directories`'.
    """
    home = home if home is not None else Path.home()
    if config_home is None:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    if user is None:
        user = _user(home)
    named = read_user_dirs(home, config_home)
    found: list[Path] = [home]
    for variable, folder in USER_DIRS:
        path = named.get(variable, home / folder)
        if path != home and path.is_dir():
            found.append(path)
    found.extend(_mount_directories(mnt, media, run_media, user))
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
    _forget()
    return True


def bookmarks() -> list[Bookmark]:
    """Every bookmark, in the order the box lists them.

    Reading them all refreshes :func:`bookmarked_paths` too, so a bookmark
    another Navigator added shows in the panels once this one's box opens.
    """
    rows = Bookmark.where().order("seq").all()
    global _known
    _known = (DATABASE.connection, frozenset(row.path for row in rows))
    return rows


#: The connection :func:`bookmarked_paths` was read from, and what it said.
#: Held with the connection, not beside it, so a database opened since -- a
#: test's fresh one, ``--database`` -- is never answered from another's.
_known: tuple[object, frozenset[str]] | None = None


def bookmarked_paths() -> frozenset[str]:
    """Every bookmarked path, as :func:`key_of` spells it.

    What a panel asks of every directory row it paints, so it is read once
    and kept until this process changes the bookmarks: a query per frame
    would be cheap, a query per row would not.
    """
    connection = DATABASE.connection
    if _known is None or _known[0] is not connection:
        bookmarks()
    assert _known is not None
    return _known[1]


def _forget() -> None:
    global _known
    _known = None


def find_bookmark(path: Path | str) -> Bookmark | None:
    return Bookmark.get(path=key_of(path))


def add_bookmark(path: Path | str) -> Bookmark:
    """*path* bookmarked, after every other; one already bookmarked stays where it is."""
    key = key_of(path)
    existing = Bookmark.get(path=key)
    if existing is not None:
        return existing
    last = Bookmark.where().order("-seq").first()
    created = Bookmark.create(path=key, seq=(last.seq + 1) if last is not None else 1)
    _forget()
    return created


def remove_bookmark(path: Path | str) -> bool:
    """*path* no longer bookmarked; False if it was not."""
    removed = Bookmark.where(path=key_of(path)).delete() > 0
    _forget()
    return removed


def label_bookmark(path: Path | str, label: str) -> bool:
    """Show *path* as *label* in the box, or as itself for ``""``; False if not bookmarked."""
    return Bookmark.where(path=key_of(path)).update(label=label.strip()) > 0


def move_bookmark(path: Path | str, by: int) -> bool:
    """*path* one place earlier (*by* -1) or later (+1); False if it cannot go.

    It changes places with its neighbour, the two ``seq`` values swapped, so
    the gaps removing leaves behind never matter.
    """
    rows = bookmarks()
    key = key_of(path)
    index = next((i for i, row in enumerate(rows) if row.path == key), None)
    if index is None or by not in (-1, 1) or not 0 <= index + by < len(rows):
        return False
    one, other = rows[index], rows[index + by]
    with DATABASE.transaction():
        # ``seq`` is not unique, so the swap needs no placeholder.
        one.seq, other.seq = other.seq, one.seq
        one.save()
        other.save()
    return True
