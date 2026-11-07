# navml: generated
"""Generated from ``directory_cursor.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # directory_cursor.nml:1

__navml_component__ = "DirectoryCursor"

__all__ = ["DirectoryCursor"]


class DirectoryCursor(Model):    # directory_cursor.nml:9
    """The entry the cursor was on when a panel last left a directory, for

    coming back to it there: File Manager Setup's *Return to last cursor
    position*, and every remembered directory
    (``navigator/lib/config/directory_settings.py``).  A departure: DN's
    cursor went to the top of every directory but the one just climbed out of.
    The newest ``CURSORS`` rows are kept.
    """

    #: The document this class was generated from.
    __navml_source__ = "directory_cursor.nml"
    __table__ = "directory_cursors"
    __fields__ = (
        _Field("path", str, ''),    # directory_cursor.nml:12
        _Field("name", str, ''),    # directory_cursor.nml:14
        _Field("used", float, 0.0),    # directory_cursor.nml:16
    )
    __indexes__ = (
        _Index("by_path", ('path',), unique=True),    # directory_cursor.nml:17
        _Index("by_used", ('used',)),    # directory_cursor.nml:18
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "directory_cursors" ("id" INTEGER PRIMARY KEY, "path" TEXT NOT NULL DEFAULT \'\', "name" TEXT NOT NULL DEFAULT \'\', "used" REAL NOT NULL DEFAULT 0.0)',
        'CREATE UNIQUE INDEX "directory_cursors_by_path" ON "directory_cursors" ("path")',
        'CREATE INDEX "directory_cursors_by_used" ON "directory_cursors" ("used")',
    )
    __schema__ = "9d30399f05a87694"

    id: int | None

    #: The directory, as a bookmark names it (``bookmarks.key_of``).
    path: str    # directory_cursor.nml:12

    #: The entry's name.
    name: str    # directory_cursor.nml:14

    #: When, by ``time.time()``: the oldest go first.
    used: float    # directory_cursor.nml:16
