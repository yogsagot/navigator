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
        _Field("used", float, 0.0),    # view_record.nml:18
        _Field("zoomed", bool, True),    # view_record.nml:20
        _Field("x", int, 0),    # view_record.nml:21
        _Field("y", int, 0),    # view_record.nml:22
        _Field("width", int, 0),    # view_record.nml:23
        _Field("height", int, 0),    # view_record.nml:24
        _Field("desk_width", int, 0),    # view_record.nml:25
        _Field("desk_height", int, 0),    # view_record.nml:26
        _Field("mode", str, 'text'),    # view_record.nml:28
        _Field("wrap", bool, False),    # view_record.nml:29
        _Field("filter", int, 0),    # view_record.nml:30
        _Field("highlight", bool, True),    # view_record.nml:32
        _Field("file_type", str, ''),    # view_record.nml:35
        _Field("rendered", str, ''),    # view_record.nml:38
        _Field("top", int, 0),    # view_record.nml:40
        _Field("x_delta", int, 0),    # view_record.nml:41
        _Field("cursor", int, 0),    # view_record.nml:42
    )
    __indexes__ = (
        _Index("by_path", ('path',), unique=True),    # view_record.nml:43
        _Index("by_seq", ('seq',)),    # view_record.nml:44
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "view_history" ("id" INTEGER PRIMARY KEY, "path" TEXT NOT NULL DEFAULT \'\', "pinned" INTEGER NOT NULL DEFAULT 0, "seq" INTEGER NOT NULL DEFAULT 0, "used" REAL NOT NULL DEFAULT 0.0, "zoomed" INTEGER NOT NULL DEFAULT 1, "x" INTEGER NOT NULL DEFAULT 0, "y" INTEGER NOT NULL DEFAULT 0, "width" INTEGER NOT NULL DEFAULT 0, "height" INTEGER NOT NULL DEFAULT 0, "desk_width" INTEGER NOT NULL DEFAULT 0, "desk_height" INTEGER NOT NULL DEFAULT 0, "mode" TEXT NOT NULL DEFAULT \'text\', "wrap" INTEGER NOT NULL DEFAULT 0, "filter" INTEGER NOT NULL DEFAULT 0, "highlight" INTEGER NOT NULL DEFAULT 1, "file_type" TEXT NOT NULL DEFAULT \'\', "rendered" TEXT NOT NULL DEFAULT \'\', "top" INTEGER NOT NULL DEFAULT 0, "x_delta" INTEGER NOT NULL DEFAULT 0, "cursor" INTEGER NOT NULL DEFAULT 0)',
        'CREATE UNIQUE INDEX "view_history_by_path" ON "view_history" ("path")',
        'CREATE INDEX "view_history_by_seq" ON "view_history" ("seq")',
    )
    __schema__ = "659134ca8c26bdc5"

    id: int | None

    #: The absolute path: the record's ``fName`` without its flag.
    path: str    # view_record.nml:12

    #: The flag: a pinned record is never evicted or deleted.
    pinned: bool    # view_record.nml:14
    seq: int    # view_record.nml:15

    #: When the file was last viewed or edited, by ``time.time()``; 0 for a
    #: record from before this was kept.  A departure: DN's record kept no time.
    used: float    # view_record.nml:18

    #: The window, ``fOrigin``/``fSize``, on a desktop ``fDeskSize`` big.
    zoomed: bool    # view_record.nml:20
    x: int# view_record.nml:21
    y: int# view_record.nml:22
    width: int    # view_record.nml:23
    height: int    # view_record.nml:24
    desk_width: int    # view_record.nml:25
    desk_height: int    # view_record.nml:26

    #: ``fViewMode``: text, hex or dump.
    mode: str    # view_record.nml:28
    wrap: bool    # view_record.nml:29
    filter: int    # view_record.nml:30

    #: View > *Syntax highlight*, which DN's viewer had not.
    highlight: bool    # view_record.nml:32

    #: View > *File type*: the lexer chosen, ``none``, or empty for
    #: ``highlight.ini``'s choice.
    file_type: str    # view_record.nml:35

    #: View > *Markup view*, which DN's viewer had not: ``on``, ``off``, or
    #: empty for the ``[viewer]`` masks' choice.
    rendered: str    # view_record.nml:38

    #: The byte offset on top.
    top: int    # view_record.nml:40
    x_delta: int    # view_record.nml:41
    cursor: int    # view_record.nml:42
