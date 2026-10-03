# navml: generated
"""Generated from ``edit_record.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navigator.models.file_record import FileRecord    # edit_record.nml:1

__navml_component__ = "EditRecord"

__all__ = ["EditRecord"]


class EditRecord(FileRecord):    # edit_record.nml:10
    """A file once edited, and how its editor was left: DN's ``TEditRecord``.

    ``StoreEditInfo`` (``HISTRIES.PAS``) wrote one when an editor closed and
    ``EditFile`` read it back.  ``fPos`` is the cursor (``line``, ``col``),
    ``fDelta`` the scroll (``top``, ``left``), ``InsMode`` the opposite of
    ``overwrite``, ``VertBlock`` ``vertical_blocks`` and ``fMarks`` ``marks``.
    The block, highlighting, auto-indent and the margins have no column yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "edit_record.nml"
    __table__ = "edit_history"
    __fields__ = (
        _Field("path", str, ''),    # edit_record.nml:13
        _Field("pinned", bool, False),    # edit_record.nml:15
        _Field("seq", int, 0),    # edit_record.nml:16
        _Field("zoomed", bool, True),    # edit_record.nml:18
        _Field("x", int, 0),    # edit_record.nml:19
        _Field("y", int, 0),    # edit_record.nml:20
        _Field("width", int, 0),    # edit_record.nml:21
        _Field("height", int, 0),    # edit_record.nml:22
        _Field("desk_width", int, 0),    # edit_record.nml:23
        _Field("desk_height", int, 0),    # edit_record.nml:24
        _Field("line", int, 0),    # edit_record.nml:25
        _Field("col", int, 0),    # edit_record.nml:26
        _Field("top", int, 0),    # edit_record.nml:27
        _Field("left", int, 0),    # edit_record.nml:28
        _Field("overwrite", bool, False),    # edit_record.nml:29
        _Field("vertical_blocks", bool, False),    # edit_record.nml:30
        _Field("marks", str, ''),    # edit_record.nml:32
    )
    __indexes__ = (
        _Index("by_path", ('path',), unique=True),    # edit_record.nml:33
        _Index("by_seq", ('seq',)),    # edit_record.nml:34
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "edit_history" ("id" INTEGER PRIMARY KEY, "path" TEXT NOT NULL DEFAULT \'\', "pinned" INTEGER NOT NULL DEFAULT 0, "seq" INTEGER NOT NULL DEFAULT 0, "zoomed" INTEGER NOT NULL DEFAULT 1, "x" INTEGER NOT NULL DEFAULT 0, "y" INTEGER NOT NULL DEFAULT 0, "width" INTEGER NOT NULL DEFAULT 0, "height" INTEGER NOT NULL DEFAULT 0, "desk_width" INTEGER NOT NULL DEFAULT 0, "desk_height" INTEGER NOT NULL DEFAULT 0, "line" INTEGER NOT NULL DEFAULT 0, "col" INTEGER NOT NULL DEFAULT 0, "top" INTEGER NOT NULL DEFAULT 0, "left" INTEGER NOT NULL DEFAULT 0, "overwrite" INTEGER NOT NULL DEFAULT 0, "vertical_blocks" INTEGER NOT NULL DEFAULT 0, "marks" TEXT NOT NULL DEFAULT \'\')',
        'CREATE UNIQUE INDEX "edit_history_by_path" ON "edit_history" ("path")',
        'CREATE INDEX "edit_history_by_seq" ON "edit_history" ("seq")',
    )
    __schema__ = "fd52ace76e808035"

    id: int | None

    #: The absolute path: the record's ``fName`` without its flag.
    path: str    # edit_record.nml:13

    #: The flag: a pinned record is never evicted or deleted.
    pinned: bool    # edit_record.nml:15
    seq: int    # edit_record.nml:16

    #: The window, ``fOrigin``/``fSize``, on a desktop ``fDeskSize`` big.
    zoomed: bool    # edit_record.nml:18
    x: int# edit_record.nml:19
    y: int# edit_record.nml:20
    width: int    # edit_record.nml:21
    height: int    # edit_record.nml:22
    desk_width: int    # edit_record.nml:23
    desk_height: int    # edit_record.nml:24
    line: int    # edit_record.nml:25
    col: int    # edit_record.nml:26
    top: int    # edit_record.nml:27
    left: int    # edit_record.nml:28
    overwrite: bool    # edit_record.nml:29
    vertical_blocks: bool    # edit_record.nml:30

    #: ``fMarks``: markers 1 to 9 as ``line:col``, comma-separated, empty where unset.
    marks: str    # edit_record.nml:32
