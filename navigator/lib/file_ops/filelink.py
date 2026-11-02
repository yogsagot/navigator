"""Symbolic links: Shift+F5's model, beside ``filecopy.py``'s F5 and F6.

A departure -- DOS Navigator had no links to make -- so there is no
original to follow, and the command borrows everything it can from Copy: the
target line is read by :func:`filecopy.resolve_target`, so an existing
directory, a name ending in ``/``, a ``MkName`` mask and a single new name all
mean what they mean to F5.  A link is made in one system call, so there is no
worker thread, no job and no progress box; :func:`make_link` raises and the
file manager asks.

The rest of File > Symlink changes links already there -- what one holds
edited, a replacement in several (:func:`replaced`), absolute turned
relative and back (:func:`switched`) -- each through :func:`retarget`.
"""

from __future__ import annotations

import errno
import os
import posixpath
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


@dataclass
class LinkRequest:
    """What the Create symlink dialog answered."""

    sources: list[Path]
    target: str
    #: Point each link at its source relative to the link's own directory,
    #: so a tree moved whole keeps working; absolute otherwise.
    relative: bool = False


def link_path(source: Path, dest: Path, relative: bool) -> str:
    """What the link at *dest* holds: *source*, absolute or relative to *dest*'s directory.

    Either may be a :class:`~navigator.lib.drives.Location` on another drive,
    both on the same one: the paths are that drive's, worked out by name."""
    if not isinstance(source, (str, os.PathLike)) or not isinstance(dest, (str, os.PathLike)):
        source_path, dest_dir = str(source.path), str(dest.parent.path)
        return posixpath.relpath(source_path, dest_dir) if relative else source_path
    source = Path(os.path.abspath(source))
    if relative:
        return os.path.relpath(source, os.path.abspath(dest.parent))
    return str(source)


def make_link(source: Path, dest: Path, relative: bool, as_root: bool = False) -> None:
    """Make *dest* a symbolic link to *source*.

    An existing *dest* is refused, a dangling link included -- ``os.symlink``
    would refuse it too, but only after the check this makes explicit.
    *as_root* makes it through the root helper (blocking: on a thread).
    """
    from navigator.lib.drives import Location, drive_of

    source_place, dest_place = Location.of(source), Location.of(dest)
    if as_root and dest_place.is_local and source_place.is_local:
        from navigator.lib.drives.root import ROOT_DRIVE

        if ROOT_DRIVE.lexists(dest_place):
            raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(dest))
        ROOT_DRIVE.symlink(link_path(source, dest, relative), dest_place)
        return
    if not dest_place.is_local or not source_place.is_local:
        # On another drive: there, by its drive, and only to its own files --
        # a link holds a path, which means nothing on any other.
        if (source_place.site, source_place.outer) != (dest_place.site, dest_place.outer):
            raise OSError(errno.EXDEV, "A link cannot point to another drive", str(dest))
        drive = drive_of(dest_place)
        if drive.lexists(dest_place):
            raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(dest))
        drive.symlink(link_path(source_place, dest_place, relative), dest_place)
        drive.finish()
        return
    if os.path.lexists(dest):
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(dest))
    os.symlink(link_path(source, dest, relative), dest)


# -- changing a link that is there -------------------------------------------------
#
# File > Symlink's other entries, a departure as Shift+F5 is: what a link
# holds edited (one link), rewritten by a replacement (several), or turned
# from absolute to relative and back.  A link is never changed in place --
# no system call can -- so a new one is made beside it under a temporary
# name and renamed over it (:func:`retarget`): at no moment is the name
# missing, and a failure leaves the old link as it was.

#: The temporary's prefix, a dot-file so a panel hiding those never shows it.
TEMPORARY = ".navlink-"


def link_base(drive: Any, link: Any) -> str:
    """The directory a relative target in *link* is read from: its parent
    with every link followed, as the kernel follows them.

    A panel standing in ``~/www`` that is a link to ``/srv/www`` sees a
    link's ``../x`` as ``~/x``; the kernel reads it as ``/srv/x``, and this
    says so."""
    from navigator.lib.drives import Location

    return str(drive.realpath(Location.of(link).parent).path)


def absolute_target(base: str, target: str) -> str:
    """*target* as an absolute path, a relative one read from *base*.

    By the letters (``posixpath.normpath``), so a ``..`` after a link in the
    target is taken out as if the link were a directory; :func:`switched`
    checks the answer against the file system before using it."""
    if posixpath.isabs(target):
        return target
    return posixpath.normpath(posixpath.join(base, target))


def relative_target(base: str, target: str) -> str:
    """*target* as a path relative to *base*, an absolute one rewritten."""
    if not posixpath.isabs(target):
        return target
    return posixpath.relpath(posixpath.normpath(target), base)


class NotTheSame(ValueError):
    """The rewritten target would reach another file than the link does."""


def switched(drive: Any, link: Any, relative: bool) -> str | None:
    """What *link* should hold to be relative (or absolute), None when it
    already is.  Raises :class:`NotTheSame` when the new target reaches
    another file than the old -- a ``..`` after a link in it -- and the
    drive's ``OSError`` when the link cannot be read.

    A link pointing nowhere is rewritten by its letters alone: there is no
    file to check the answer against.  Touches the drive: on a thread."""
    from navigator.lib.drives import Location

    link = Location.of(link)
    old = drive.readlink(link)
    if posixpath.isabs(old) != relative:
        return None
    base = link_base(drive, link)
    new = relative_target(base, old) if relative else absolute_target(base, old)
    if new == old:
        return None
    if drive.exists(link):
        # Read as the kernel reads the new target: from the real parent, the
        # ``..`` left in, so a link in the path is followed before it.
        reached = Location(link.site, type(link.path)(new if posixpath.isabs(new) else posixpath.join(base, new)),
                           link.outer)
        if not drive.same_file(link, reached):
            raise NotTheSame(new)
    return new


def retarget(drive: Any, link: Any, target: str) -> None:
    """*link* made to hold *target*: a new link beside it, renamed over it.

    Refused (``EINVAL``) when *link* is not a symbolic link -- a file is
    never replaced by one.  Touches the drive: on a thread."""
    from navigator.lib.drives import Location

    link = Location.of(link)
    if not drive.is_link(link):
        raise OSError(errno.EINVAL, "Not a symbolic link", str(link))
    number = 0
    while drive.lexists(temporary := link.parent / f"{TEMPORARY}{number}"):
        number += 1
    drive.symlink(target, temporary)
    try:
        drive.replace(temporary, link)
    except BaseException:
        try:
            drive.unlink(temporary)
        except OSError:
            pass
        raise
    drive.finish()


#: What :func:`replaced` may find wrong with a row (the dialog puts each in words).
PROBLEMS = ("unchanged", "empty", "nul")


@dataclass
class Retarget:
    """One row of the *Change link targets* box: a link, what it holds and
    what it would hold, and what is wrong with that, if anything."""

    link: Any
    old: str
    new: str
    problem: str = ""


def replaced(links: Sequence[tuple[Any, str]], find: str, replace: str) -> list[Retarget]:
    """Every ``(link, target)`` with *find* replaced by *replace* in its target.

    Pure: the targets are the ones read with the directory.  A row whose
    target does not change is *unchanged*; one left empty or holding a NUL
    (which no path can) has a problem."""
    rows = []
    for link, old in links:
        new = old.replace(find, replace) if find else old
        problem = ""
        if new == old:
            problem = "unchanged"
        elif not new:
            problem = "empty"
        elif "\0" in new:
            problem = "nul"
        rows.append(Retarget(link, old, new, problem))
    return rows
