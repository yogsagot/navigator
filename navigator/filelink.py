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
    """What the link at *dest* holds: *source*, absolute or relative to *dest*'s directory."""
    source = Path(os.path.abspath(source))
    if relative:
        return os.path.relpath(source, os.path.abspath(dest.parent))
    return str(source)


def make_link(source: Path, dest: Path, relative: bool) -> None:
    """Make *dest* a symbolic link to *source*.

    An existing *dest* is refused, a dangling link included -- ``os.symlink``
    would refuse it too, but only after the check this makes explicit.
    """
    if os.path.lexists(dest):
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(dest))
    os.symlink(link_path(source, dest, relative), dest)
