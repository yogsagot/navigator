# navml: generated
"""Generated from ``view_record.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navigator.models.file_record import FileRecord    # view_record.nml:1

__navml_component__ = "ViewRecord"

__all__ = ["ViewRecord"]


class ViewRecord(FileRecord):    # view_record.nml:9
    """A file once viewed, and how its viewer was left: DN's ``TViewRecord``.

    ``StoreViewInfo`` (``HISTRIES.PAS``) wrote one when a viewer closed and
    ``ViewFile`` read it back when the file was viewed again.  Its ``fPos`` and
    ``fBufPos`` are ``top``, its ``XDelta`` ``x_delta`` and its ``HexPos``/``Cur``
    the hex ``cursor``; ``XlateTable`` has nothing to stand for yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "view_record.nml"
    __table__ = "view_history"
    __fields__ = (
        _Field("path", str, ''),    # view_record.nml:12
        _Field("pinned", bool, False),    # view_record.nml:14
        _Field("seq", int, 0),    # view_record.nml:15
        _Field("zoomed", bool, True),    # view_record.nml:17
        _Field("x", int, 0),    # view_record.nml:18
        _Field("y", int, 0),    # view_record.nml:19
        _Field("width", int, 0),    # view_record.nml:20
        _Field("height", int, 0),    # view_record.nml:21
        _Field("desk_width", int, 0),    # view_record.nml:22
        _Field("desk_height", int, 0),    # view_record.nml:23
        _Field("mode", str, 'text'),    # view_record.nml:25
        _Field("wrap", bool, False),    # view_record.nml:26
        _Field("filter", int, 0),    # view_record.nml:27
        _Field("highlight", bool, True),    # view_record.nml:29
        _Field("top", int, 0),    # view_record.nml:31
        _Field("x_delta", int, 0),    # view_record.nml:32
        _Field("cursor", int, 0),    # view_record.nml:33
    )
    __indexes__ = (
        _Index("by_path", ('path',), unique=True),    # view_record.nml:34
        _Index("by_seq", ('seq',)),    # view_record.nml:35
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "view_history" ("id" INTEGER PRIMARY KEY, "path" TEXT NOT NULL DEFAULT \'\', "pinned" INTEGER NOT NULL DEFAULT 0, "seq" INTEGER NOT NULL DEFAULT 0, "zoomed" INTEGER NOT NULL DEFAULT 1, "x" INTEGER NOT NULL DEFAULT 0, "y" INTEGER NOT NULL DEFAULT 0, "width" INTEGER NOT NULL DEFAULT 0, "height" INTEGER NOT NULL DEFAULT 0, "desk_width" INTEGER NOT NULL DEFAULT 0, "desk_height" INTEGER NOT NULL DEFAULT 0, "mode" TEXT NOT NULL DEFAULT \'text\', "wrap" INTEGER NOT NULL DEFAULT 0, "filter" INTEGER NOT NULL DEFAULT 0, "highlight" INTEGER NOT NULL DEFAULT 1, "top" INTEGER NOT NULL DEFAULT 0, "x_delta" INTEGER NOT NULL DEFAULT 0, "cursor" INTEGER NOT NULL DEFAULT 0)',
        'CREATE UNIQUE INDEX "view_history_by_path" ON "view_history" ("path")',
        'CREATE INDEX "view_history_by_seq" ON "view_history" ("seq")',
    )
    __schema__ = "aa65ade4024999aa"

    id: int | None

    #: The absolute path: the record's ``fName`` without its flag.
    path: str    # view_record.nml:12

    #: The flag: a pinned record is never evicted or deleted.
    pinned: bool    # view_record.nml:14
    seq: int    # view_record.nml:15

    #: The window, ``fOrigin``/``fSize``, on a desktop ``fDeskSize`` big.
    zoomed: bool    # view_record.nml:17
    x: int# view_record.nml:18
    y: int# view_record.nml:19
    width: int    # view_record.nml:20
    height: int    # view_record.nml:21
    desk_width: int    # view_record.nml:22
    desk_height: int    # view_record.nml:23

    #: ``fViewMode``: text, hex or dump.
    mode: str    # view_record.nml:25
    wrap: bool    # view_record.nml:26
    filter: int    # view_record.nml:27

    #: View > *Syntax highlight*, which DN's viewer had not.
    highlight: bool    # view_record.nml:29

    #: The byte offset on top.
    top: int    # view_record.nml:31
    x_delta: int    # view_record.nml:32
    cursor: int    # view_record.nml:33
