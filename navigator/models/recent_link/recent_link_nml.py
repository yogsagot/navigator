# navml: generated
"""Generated from ``recent_link.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # recent_link.nml:1

__navml_component__ = "RecentLink"

__all__ = ["RecentLink"]


class RecentLink(Model):    # recent_link.nml:10
    """A connection made from the SSH link box (Utilities > *SSH link (SFTP)*),

    everything it was made with kept together: what the Host line's ``▐↓▌``
    drops, and choosing one fills every line again.

    Its own table, not a ``HistoryEntry`` list: a history keeps one string
    per row, and a connection is five.  Never a password
    (``navigator/lib/drives/credentials.py``).
    """

    #: The document this class was generated from.
    __navml_source__ = "recent_link.nml"
    __table__ = "recent_links"
    __fields__ = (
        _Field("scheme", str, ''),    # recent_link.nml:13
        _Field("host", str, ''),    # recent_link.nml:14
        _Field("user", str, ''),    # recent_link.nml:16
        _Field("port", int, 0),    # recent_link.nml:18
        _Field("path", str, ''),    # recent_link.nml:20
        _Field("seq", int, 0),    # recent_link.nml:22
    )
    __indexes__ = (
        _Index("by_place", ('scheme', 'host', 'user', 'port'), unique=True),    # recent_link.nml:23
        _Index("by_seq", ('seq',)),    # recent_link.nml:24
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "recent_links" ("id" INTEGER PRIMARY KEY, "scheme" TEXT NOT NULL DEFAULT \'\', "host" TEXT NOT NULL DEFAULT \'\', "user" TEXT NOT NULL DEFAULT \'\', "port" INTEGER NOT NULL DEFAULT 0, "path" TEXT NOT NULL DEFAULT \'\', "seq" INTEGER NOT NULL DEFAULT 0)',
        'CREATE UNIQUE INDEX "recent_links_by_place" ON "recent_links" ("scheme", "host", "user", "port")',
        'CREATE INDEX "recent_links_by_seq" ON "recent_links" ("seq")',
    )
    __schema__ = "4b74377186a40db1"

    id: int | None

    #: The protocol: ``sftp``, and later ``ftp``, ``smb``.
    scheme: str    # recent_link.nml:13
    host: str    # recent_link.nml:14

    #: Empty for the system's (or ``~/.ssh/config``'s).
    user: str    # recent_link.nml:16

    #: 0 for the scheme's own (or ``~/.ssh/config``'s).
    port: int    # recent_link.nml:18

    #: The directory it opened on; empty for the home directory there.
    path: str    # recent_link.nml:20

    #: Larger is newer: the list comes newest first.
    seq: int    # recent_link.nml:22
