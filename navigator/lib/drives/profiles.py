"""Connection profiles: places on other drives kept by name
(:class:`~navigator.models.remote_profile.RemoteProfile`), for the *Link*
part of the Alt+F1/Alt+F2 box and Utilities > Navigator Link.

DN's ``SelectDrive`` listed the drives of the PC across the cable under
``LINK``; these are what stands there -- each a server, a user, a port and
the directory to open on.  No password is ever among them.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from navkit.database import DATABASE

from navigator.lib.drives.location import Location, Site
from navigator.models.remote_profile import RemoteProfile

#: The path a location has before its drive says where home is: the panel
#: opens on the server's home directory.
HOME = PurePosixPath(".")


def profiles() -> list[RemoteProfile]:
    """Every profile, in the user's order."""
    return sorted(RemoteProfile.all(), key=lambda row: (row.seq, row.name))


def find(name: str) -> RemoteProfile | None:
    return RemoteProfile.get(name=name)


def site_of(profile: RemoteProfile) -> Site:
    return Site(profile.scheme, profile.user, profile.host, profile.port)


def location_of(profile: RemoteProfile) -> Location:
    """Where *profile* opens: its directory, or the home directory there."""
    return Location(site_of(profile), PurePosixPath(profile.path) if profile.path else HOME)


def save(name: str, scheme: str, host: str, user: str = "", port: int = 0, path: str = "") -> RemoteProfile:
    """*name* kept as the profile for this place, replacing one of that name."""
    with DATABASE.transaction():
        row = find(name)
        if row is None:
            last = max((each.seq for each in RemoteProfile.all()), default=0)
            row = RemoteProfile.create(name=name, scheme=scheme, host=host, user=user, port=port,
                                       path=path, seq=last + 1)
        else:
            row.scheme, row.host, row.user, row.port, row.path = scheme, host, user, port, path
            row.save()
    return row


def remove(name: str) -> bool:
    row = find(name)
    if row is None:
        return False
    row.delete()
    return True


def replace(old: str, name: str, scheme: str, host: str, user: str = "", port: int = 0,
            path: str = "") -> RemoteProfile:
    """The profile *old*, edited -- renamed to *name* if that differs, in the
    place it had.  A name another profile has already is that one's, and it
    goes: the one being edited takes its name."""
    with DATABASE.transaction():
        row = find(old)
        if row is None:
            return save(name, scheme, host, user, port, path)
        if name != old:
            other = find(name)
            if other is not None:
                other.delete()
        row.name, row.scheme, row.host, row.user, row.port, row.path = name, scheme, host, user, port, path
        row.save()
    return row


def move(name: str, by: int) -> bool:
    """*name* one place up (*by* -1) or down (1) the list; False at its end."""
    with DATABASE.transaction():
        rows = profiles()
        index = next((i for i, row in enumerate(rows) if row.name == name), None)
        if index is None or not 0 <= index + by < len(rows):
            return False
        rows[index], rows[index + by] = rows[index + by], rows[index]
        for seq, row in enumerate(rows, 1):
            if row.seq != seq:
                row.seq = seq
                row.save()
    return True


__all__ = ["HOME", "find", "location_of", "move", "profiles", "remove", "replace", "save", "site_of"]
