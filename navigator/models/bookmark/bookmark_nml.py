# navml: generated
"""Generated from ``bookmark.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # bookmark.nml:1

__navml_component__ = "Bookmark"

__all__ = ["Bookmark"]


class Bookmark(Model):    # bookmark.nml:7
    """A directory the panels can be sent to from Alt+F1, Alt+F2 or Alt+C.

    What stands where DOS Navigator's ``SelectDrive`` listed the drive
    letters; ``navigator/bookmarks.py`` has why, and the first set.
    """

    #: The document this class was generated from.
    __navml_source__ = "bookmark.nml"
    __table__ = "bookmarks"
    __fields__ = (
        _Field("path", str, ''),    # bookmark.nml:10
        _Field("seq", int, 0),    # bookmark.nml:12
    )
    __indexes__ = (
        _Index("by_path", ('path',), unique=True),    # bookmark.nml:13
        _Index("by_seq", ('seq',)),    # bookmark.nml:14
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "bookmarks" ("id" INTEGER PRIMARY KEY, "path" TEXT NOT NULL DEFAULT \'\', "seq" INTEGER NOT NULL DEFAULT 0)',
        'CREATE UNIQUE INDEX "bookmarks_by_path" ON "bookmarks" ("path")',
        'CREATE INDEX "bookmarks_by_seq" ON "bookmarks" ("seq")',
    )
    __schema__ = "dcbccf335734e163"

    id: int | None

    #: The absolute path, case and all.
    path: str    # bookmark.nml:10

    #: Smaller first; a bookmark added goes after every other.
    seq: int    # bookmark.nml:12
