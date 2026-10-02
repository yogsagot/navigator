# navml: generated
"""Generated from ``marker.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # marker.nml:1

__navml_component__ = "Marker"

__all__ = ["Marker"]


class Marker(Model):    # marker.nml:8
    """Something Navigator has done once in this database and must not do again.

    A row's presence is the whole of what it says.  ``"bookmarks seeded"`` is
    why an empty bookmark list stays empty: the first set is written once, not
    whenever the user has removed every bookmark.
    """

    #: The document this class was generated from.
    __navml_source__ = "marker.nml"
    __table__ = "markers"
    __fields__ = (
        _Field("name", str, ''),    # marker.nml:10
    )
    __indexes__ = (
        _Index("by_name", ('name',), unique=True),    # marker.nml:11
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "markers" ("id" INTEGER PRIMARY KEY, "name" TEXT NOT NULL DEFAULT \'\')',
        'CREATE UNIQUE INDEX "markers_by_name" ON "markers" ("name")',
    )
    __schema__ = "80a994a8a4fe7520"

    id: int | None
    name: str    # marker.nml:10
