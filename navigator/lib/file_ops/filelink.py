"""Symbolic links: Shift+F5's model, beside ``filecopy.py``'s F5 and F6.

A departure -- DOS Navigator had no links to make -- so there is no
original to follow, and the command borrows everything it can from Copy: the
target line is read by :func:`filecopy.resolve_target`, so an existing
directory, a name ending in ``/``, a ``MkName`` mask and a single new name all
mean what they mean to F5.  A link is made in one system call, so there is no
worker thread, no job and no progress box; :func:`make_link` raises and the
file manager asks.
"""

from __future__ import annotations

import errno
import os
from dataclasses import dataclass
from pathlib import Path


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
        import posixpath

        source_path, dest_dir = str(source.path), str(dest.parent.path)
        return posixpath.relpath(source_path, dest_dir) if relative else source_path
    source = Path(os.path.abspath(source))
    if relative:
        return os.path.relpath(source, os.path.abspath(dest.parent))
    return str(source)


def make_link(source: Path, dest: Path, relative: bool) -> None:
    """Make *dest* a symbolic link to *source*.

    An existing *dest* is refused, a dangling link included -- ``os.symlink``
    would refuse it too, but only after the check this makes explicit.
    """
    from navigator.lib.drives import Location, drive_of

    source_place, dest_place = Location.of(source), Location.of(dest)
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
