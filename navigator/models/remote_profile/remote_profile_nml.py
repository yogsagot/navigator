# navml: generated
"""Generated from ``remote_profile.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # remote_profile.nml:1

__navml_component__ = "RemoteProfile"

__all__ = ["RemoteProfile"]


class RemoteProfile(Model):    # remote_profile.nml:9
    """A place on another drive the user connects to by name: Utilities >

    *Navigator Link* and the *Link* part of the Alt+F1/Alt+F2 box, where DOS
    Navigator's ``SelectDrive`` listed the drives of the PC across the cable.

    Never a password: those are asked for, or kept in the desktop's keyring
    (``navigator/lib/drives/credentials.py``), never in the database.
    """

    #: The document this class was generated from.
    __navml_source__ = "remote_profile.nml"
    __table__ = "remote_profiles"
    __fields__ = (
        _Field("name", str, ''),    # remote_profile.nml:12
        _Field("scheme", str, ''),    # remote_profile.nml:14
        _Field("host", str, ''),    # remote_profile.nml:15
        _Field("port", int, 0),    # remote_profile.nml:17
        _Field("user", str, ''),    # remote_profile.nml:19
        _Field("path", str, ''),    # remote_profile.nml:21
        _Field("seq", int, 0),    # remote_profile.nml:23
    )
    __indexes__ = (
        _Index("by_name", ('name',), unique=True),    # remote_profile.nml:24
        _Index("by_seq", ('seq',)),    # remote_profile.nml:25
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "remote_profiles" ("id" INTEGER PRIMARY KEY, "name" TEXT NOT NULL DEFAULT \'\', "scheme" TEXT NOT NULL DEFAULT \'\', "host" TEXT NOT NULL DEFAULT \'\', "port" INTEGER NOT NULL DEFAULT 0, "user" TEXT NOT NULL DEFAULT \'\', "path" TEXT NOT NULL DEFAULT \'\', "seq" INTEGER NOT NULL DEFAULT 0)',
        'CREATE UNIQUE INDEX "remote_profiles_by_name" ON "remote_profiles" ("name")',
        'CREATE INDEX "remote_profiles_by_seq" ON "remote_profiles" ("seq")',
    )
    __schema__ = "58721791b81e8a59"

    id: int | None

    #: What the user calls it; the profile's key.
    name: str    # remote_profile.nml:12

    #: The drive: ``sftp``, ``ftp``/``ftps``, ``smb``, ``s3``/``s3+http``.
    scheme: str    # remote_profile.nml:14
    host: str    # remote_profile.nml:15

    #: 0 for the scheme's own (or ``~/.ssh/config``'s).
    port: int    # remote_profile.nml:17

    #: Empty for the system's (or ``~/.ssh/config``'s).
    user: str    # remote_profile.nml:19

    #: Where the panel opens; empty for the home directory there.
    path: str    # remote_profile.nml:21

    #: Smaller first; a profile added goes after every other.
    seq: int    # remote_profile.nml:23
