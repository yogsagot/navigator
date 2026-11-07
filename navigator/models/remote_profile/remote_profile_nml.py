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
        _Field("options", str, ''),    # remote_profile.nml:25
        _Field("forwards", str, ''),    # remote_profile.nml:30
        _Field("seq", int, 0),    # remote_profile.nml:32
    )
    __indexes__ = (
        _Index("by_name", ('name',), unique=True),    # remote_profile.nml:33
        _Index("by_seq", ('seq',)),    # remote_profile.nml:34
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "remote_profiles" ("id" INTEGER PRIMARY KEY, "name" TEXT NOT NULL DEFAULT \'\', "scheme" TEXT NOT NULL DEFAULT \'\', "host" TEXT NOT NULL DEFAULT \'\', "port" INTEGER NOT NULL DEFAULT 0, "user" TEXT NOT NULL DEFAULT \'\', "path" TEXT NOT NULL DEFAULT \'\', "options" TEXT NOT NULL DEFAULT \'\', "forwards" TEXT NOT NULL DEFAULT \'\', "seq" INTEGER NOT NULL DEFAULT 0)',
        'CREATE UNIQUE INDEX "remote_profiles_by_name" ON "remote_profiles" ("name")',
        'CREATE INDEX "remote_profiles_by_seq" ON "remote_profiles" ("seq")',
    )
    __schema__ = "c4be37229d001dbc"

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

    #: SSH's alone: words added to Remote shell's ``ssh`` command, after
    #: ``[remote] ssh_options`` -- ``-A -J jump``.  SSH link's panel goes
    #: through paramiko, which reads ``~/.ssh/config`` and no flags.
    options: str    # remote_profile.nml:25

    #: SSH's alone: the port forwards kept with the connection, one a line in
    #: ``ssh``'s own words -- ``L 8080:db:5432``, ``R 9000:localhost:9000``,
    #: ``D 1080`` (``navigator/lib/drives/forwards.py``).  Opened while a
    #: panel's connection is up, and passed to Remote shell's ``ssh``.
    forwards: str    # remote_profile.nml:30

    #: Smaller first; a profile added goes after every other.
    seq: int    # remote_profile.nml:32
