"""KIO places as a drive: ``mtp://``, ``webdav://``, ``fish://``, ``gdrive://``...

Not DOS Navigator's, and the KDE counterpart of :mod:`navigator.lib.drives.gvfs`.
Where the desktop's plumbing is KDE's (:func:`navigator.lib.system.desktop.backend`),
KIO's workers speak the protocols Navigator does not
(:data:`navigator.lib.system.kio.KIO_SCHEMES`), and kio-fuse shows each URL
as a directory under ``$XDG_RUNTIME_DIR/kio-fuse-XXXXXX``.  This drive is
that directory under the URL's own name, as :class:`~navigator.lib.drives.gvfs.GvfsDrive`
is GVfs's -- whose every step it shares.

* **Connecting** is kio-fuse's D-Bus ``mountUrl`` (:func:`connect`).  It
  has no prompts to answer: KIO asks a password in its own window where
  there is a display, and a password from Navigator's box goes into the URL
  it is given.  A refusal that names authentication raises
  :class:`~navigator.lib.drives.sessions.NeedPassword`.
* **Where the mount starts**: kio-fuse puts a URL's path under the
  directory it answers one to one, so the drive's root is that directory
  less the asked path, and its *prefix* is ``/``.
* **Closing** unmounts nothing: kio-fuse has no call to let one URL go
  (it forgets them itself when idle), unlike ``gio mount -u``.
* **The host keeps its case**, as GVfs's do, and a scheme whose KIO URL has
  no host (``mtp:/Phone/Storage``) is written ``mtp://Phone/Storage`` in a
  panel, as GVfs writes it (:data:`navigator.lib.system.kio.HOSTLESS`).
"""

from __future__ import annotations

import errno
import re
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

from navigator.lib.drives.gvfs import GvfsDrive, uri_of
from navigator.lib.drives.location import Site
from navigator.lib.system import kio

#: Why KIO is not asked though ``kioclient`` is there.
NOT_IN_USE = "KIO is not in use: [system] desktop_vfs is not kio"

#: What a refusal says when it wants a password: KIO's ``ERR_CANNOT_AUTHENTICATE``
#: and its kin, as kio-fuse passes them on.
_AUTH = re.compile(r"(?i)authenticat|authoriz|password|access denied|\b401\b")


def available() -> str | None:
    """Why KIO cannot be reached here, or None if it can."""
    from navigator.lib.system import desktop

    if kio.program() is None:
        return kio.NO_KIO
    if desktop.backend() is not kio:
        return NOT_IN_USE
    return None


class KioDrive(GvfsDrive):
    """A KIO URL, read and written through kio-fuse's FUSE path."""

    def describe(self) -> list[tuple[str, str]]:
        return [("Server", uri_of(self.site, self.prefix)), ("Kind", "KIO")]

    def close(self) -> None:
        """Nothing: kio-fuse lets go of a URL on its own."""


def with_password(uri: str, site: Site, password: str | None) -> str:
    """*uri* with *password* after its user, for kio-fuse to log in with."""
    if not password:
        return uri
    scheme, sep, rest = uri.partition("://")
    host_part = rest.partition("@")[2] if "@" in rest.partition("/")[0] else rest
    return f"{scheme}{sep}{quote(site.user or '', safe='')}:{quote(password, safe='')}@{host_part}"


def root_of(local: Path, start: PurePosixPath) -> tuple[Path, PurePosixPath]:
    """The drive's root and prefix from *local*, where kio-fuse shows
    *start*: *local* less *start*'s names where it ends with them, else
    *local* itself standing for *start*."""
    names = start.parts[1:]
    if names and local.parts[-len(names):] == names:
        return Path(*local.parts[:-len(names)]), PurePosixPath("/")
    return local, start if names else PurePosixPath("/")


def connect(site: Site, answers: Any) -> KioDrive:
    """*site* reached through kio-fuse: blocks, and raises
    :class:`~navigator.lib.drives.sessions.NeedPassword` for the user to answer."""
    from navigator.lib.drives.sessions import NeedPassword

    start = PurePosixPath(answers.start or "/")
    uri = uri_of(site, start)
    try:
        local = kio.mount_url(with_password(uri, site, answers.password))
    except OSError as error:
        if error.errno != errno.ENOENT and _AUTH.search(error.strerror or ""):
            raise NeedPassword(site, site.user, site.host, wrong=answers.password is not None) from None
        raise
    root, prefix = root_of(local, start)
    return KioDrive(site, root, prefix, ours=False)


__all__ = ["KioDrive", "NOT_IN_USE", "available", "connect", "root_of", "with_password"]
