"""Where a panel is: a directory on a drive, local or not.

DOS Navigator's panel held a ``Drive`` and a ``CurDir`` string on it
(``DRIVES.PAS``); a :class:`Location` is the two together -- the
:class:`Site` that says which drive, and the path on it.

**A Location is not a path.**  It has no ``__fspath__``, so a call into
:mod:`os` that was handed one instead of a :class:`~pathlib.Path` fails at
once rather than quietly running on the local disk with a remote file's
name.  :attr:`Location.local` is the way back to a ``Path``, and raises for
a remote one.

The text form of a local location is exactly ``str(Path)``, so everything
that stored a directory as text before -- histories, bookmarks, a saved
desktop -- reads and writes the same bytes.  A remote one is a URL,
``sftp://user@host:port/path``, the port and the user left out when there
are none; the path is percent-encoded, which ``/`` and the usual name
characters are not.
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import SplitResult, quote, unquote, urlsplit


class RemoteLocation(TypeError):
    """A local path was asked of a location that is not on the local disk."""


#: What starts a URL rather than a local path: a scheme and ``://``.
_URL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")

#: The characters a path keeps unencoded in a URL: what ``quote`` keeps by
#: default, plus the ones a file name has often and a URL does not mind.
_SAFE = "/~!$&'()*+,;=:@"


@dataclass(frozen=True, slots=True)
class Site:
    """Which drive: a scheme, and for a remote one who and where.

    ``Site()`` is the local disk.  Two locations on one site share one
    connection (:mod:`navigator.lib.drives.sessions`).
    """

    scheme: str = "file"
    user: str = ""
    host: str = ""
    port: int = 0

    @property
    def is_local(self) -> bool:
        return self.scheme == "file"

    def __str__(self) -> str:
        if self.is_local:
            return ""
        user = f"{quote(self.user, safe='')}@" if self.user else ""
        port = f":{self.port}" if self.port else ""
        host = f"[{self.host}]" if ":" in self.host else self.host
        return f"{self.scheme}://{user}{host}{port}"


#: The local disk's site.
LOCAL_SITE = Site()


def _is_archive_name(text: str) -> bool:
    """Whether the last name in *text* is one the *archive* file type takes."""
    from navigator.lib.appearance import filetypes

    name = text.rstrip("/").rpartition("/")[2]
    return bool(name) and filetypes.group_of(name) == "archive"


def _host(parts: SplitResult, scheme: str) -> str:
    """The host *parts* name: lower case, as DNS has it -- but as written
    for a GVfs or KIO scheme, whose "host" is a phone's or a camera's name
    (``mtp://Google_Pixel_7_2B14/``), which GVfs and KIO match exactly."""
    from navigator.lib.system.gio import GVFS_SCHEMES
    from navigator.lib.system.kio import KIO_SCHEMES

    if scheme not in GVFS_SCHEMES and scheme not in KIO_SCHEMES:
        return parts.hostname or ""
    host = parts.netloc.rpartition("@")[2]
    if host.startswith("["):
        return host[1:].partition("]")[0]
    return unquote(host.partition(":")[0])


@dataclass(frozen=True, slots=True)
class Location:
    """A directory or a file on a :class:`Site`.

    *path* is a :class:`~pathlib.Path` for the local disk -- the very one a
    panel was given, relative or not -- and a :class:`~pathlib.PurePosixPath`
    on any other site, where nothing may touch it but its drive.

    *outer* is the location of the file this one is inside, for a drive that
    is a file on another (an archive: DN's ``TArcDrive``, stacked on the
    drive it was opened from through ``Prev``).
    """

    site: Site
    path: PurePosixPath
    outer: Location | None = None

    @classmethod
    def of(cls, path: Path | str | Location) -> Location:
        """*path* on the local disk; a Location is answered as it is."""
        if isinstance(path, Location):
            return path
        return cls(LOCAL_SITE, Path(path))

    @classmethod
    def parse(cls, text: str) -> Location:
        """What :meth:`__str__` wrote: a URL, or a local path -- and either
        followed by ``#/inside`` for a place in an archive there, when what
        comes before the ``#`` is named as an archive is."""
        outer, mark, inner = text.partition("#/")
        if mark and _is_archive_name(outer):
            # ``a.zip#//`` is its root too: POSIX's ``//`` is a root of its own.
            return cls(Site("arc"), PurePosixPath("/" + unquote(inner).lstrip("/")), cls.parse(outer))
        if not _URL.match(text):
            return cls(LOCAL_SITE, Path(text))
        parts = urlsplit(text)
        scheme = parts.scheme.lower()
        path = unquote(parts.path) or "/"
        if scheme == "file":
            return cls(LOCAL_SITE, Path(path))
        site = Site(scheme, unquote(parts.username or ""), _host(parts, scheme), parts.port or 0)
        return cls(site, PurePosixPath(path))

    @property
    def is_local(self) -> bool:
        return self.site.is_local and self.outer is None

    @property
    def local(self) -> Path:
        """The local path; :class:`RemoteLocation` for a location elsewhere."""
        if not self.is_local:
            raise RemoteLocation(f"{self} is not on the local disk")
        return self.path  # type: ignore[return-value]

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def parent(self) -> Location:
        return Location(self.site, self.path.parent, self.outer)

    @property
    def is_root(self) -> bool:
        return self.path == self.path.parent

    def __truediv__(self, name: str) -> Location:
        return Location(self.site, self.path / name, self.outer)

    def normalized(self) -> Location:
        """``..`` and ``.`` taken out by the letters alone: never a question
        to the drive, which a remote one would make a round trip."""
        text = posixpath.normpath(str(self.path))
        if text.startswith("//"):
            text = "/" + text.lstrip("/")
        return Location(self.site, type(self.path)(text), self.outer)

    def __str__(self) -> str:
        if self.is_local:
            return str(self.path)
        inner = quote(str(self.path), safe=_SAFE)
        if self.outer is not None:
            return f"{self.outer}#{inner}"
        return f"{self.site}{inner}"


__all__ = ["LOCAL_SITE", "Location", "RemoteLocation", "Site"]
