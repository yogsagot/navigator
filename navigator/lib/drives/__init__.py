"""Drives: where a panel's files are -- the disk, a server, an archive.

DOS Navigator's ``TDrive`` family (``DRIVES.PAS``) recreated for a modern
system: :class:`~navigator.lib.drives.location.Location` is where, and
:class:`~navigator.lib.drives.base.Drive` is what reads and writes there.
:func:`drive_of` finds a location's drive: :data:`LOCAL` for the disk, and
for anything else the drive :func:`mount` registered for its site -- a
connection open to a server, say -- or :class:`DriveGone` when none is.

The ``navigator-drives`` skill has the rules.
"""

from __future__ import annotations

import threading

from navigator.lib.drives.base import Drive, DriveGone, FileStat
from navigator.lib.drives.local import LOCAL, LocalDrive
from navigator.lib.drives.location import LOCAL_SITE, Location, RemoteLocation, Site

_LOCK = threading.Lock()
#: The drives open now, other than the disk, by site.
_MOUNTED: dict[Site, Drive] = {}


def mount(drive: Drive) -> Drive:
    """Make *drive* the one its site's locations are read through."""
    with _LOCK:
        _MOUNTED[drive.site] = drive
    return drive


def unmount(site: Site) -> Drive | None:
    """Forget *site*'s drive; answer it, for whoever closes it."""
    with _LOCK:
        return _MOUNTED.pop(site, None)


def mounted() -> list[Drive]:
    """The drives open now, other than the disk."""
    with _LOCK:
        return list(_MOUNTED.values())


def drive_of(location: Location) -> Drive:
    """The drive *location* is on; :class:`DriveGone` if it is not open."""
    if location.is_local:
        return LOCAL
    if location.outer is not None:
        # Inside an archive (DN's ``TArcDrive``): the drive is the archive's.
        from navigator.lib.drives.archive import find

        drive = find(location.outer)
        if drive is None:
            raise DriveGone(location.outer.name)
        return drive
    site = location.site
    if site.scheme == "trash":
        # The Trash: no connection, nothing mounted (:mod:`navigator.lib.drives.trash`).
        from navigator.lib.drives.trash import TRASH

        return TRASH
    with _LOCK:
        drive = _MOUNTED.get(site)
    if drive is None:
        raise DriveGone(str(site) or site.scheme)
    return drive


__all__ = [
    "Drive", "DriveGone", "FileStat", "LOCAL", "LOCAL_SITE", "LocalDrive", "Location",
    "RemoteLocation", "Site", "drive_of", "mount", "mounted", "unmount",
]
