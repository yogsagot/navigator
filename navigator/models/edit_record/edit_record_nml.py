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


class EditRecord(FileRecord):    # edit_record.nml:18
    """A file once edited, and how its editor was left: DN's ``TEditRecord``.

    ``StoreEditInfo`` (``HISTRIES.PAS``) wrote one when an editor closed and
    ``EditFile`` (``DNUTIL.PAS``) read it back.  ``fPos`` is the cursor
    (``line``, ``col``), ``fDelta`` the scroll (``top``, ``left``), ``InsMode``
    the opposite of ``overwrite``, ``VertBlock`` ``vertical_blocks``, ``fMarks``
    ``marks``, ``HiLite`` ``highlight``, ``fBlockStart``/``fBlockEnd`` ``block``
    and ``fBlockVisible`` the opposite of ``block_hidden``; ``fHiliteLine``,
    ``fHiliteColumn``, ``fAutoIndent``, ``fAutoJustify``, ``fAutoBrackets``,
    ``fLeftSide``, ``fRightSide`` and ``fInSide`` are the fields of their names.
    Those last eight are None in a record written before they were kept, which
    reads as *not recorded*: the editor keeps what the Editor setup gave it.
    Auto wrap, Backspace unindents, Optimal fill, Hidden characters and the
    draw mode were not in DN's record and are not here: each editor is seeded
    with them from the setup.
    """

    #: The document this class was generated from.
    __navml_source__ = "edit_record.nml"
    __table__ = "edit_history"
    __fields__ = (
        _Field("path", str, ''),    # edit_record.nml:21
        _Field("pinned", bool, False),    # edit_record.nml:23
        _Field("seq", int, 0),    # edit_record.nml:24
        _Field("used", float, 0.0),    # edit_record.nml:27
        _Field("zoomed", bool, True),    # edit_record.nml:29
        _Field("x", int, 0),    # edit_record.nml:30
        _Field("y", int, 0),    # edit_record.nml:31
        _Field("width", int, 0),    # edit_record.nml:32
        _Field("height", int, 0),    # edit_record.nml:33
        _Field("desk_width", int, 0),    # edit_record.nml:34
        _Field("desk_height", int, 0),    # edit_record.nml:35
        _Field("line", int, 0),    # edit_record.nml:36
        _Field("col", int, 0),    # edit_record.nml:37
        _Field("top", int, 0),    # edit_record.nml:38
        _Field("left", int, 0),    # edit_record.nml:39
        _Field("overwrite", bool, False),    # edit_record.nml:40
        _Field("vertical_blocks", bool, False),    # edit_record.nml:41
        _Field("highlight", bool, True),    # edit_record.nml:43
        _Field("file_type", str, ''),    # edit_record.nml:46
        _Field("marks", str, ''),    # edit_record.nml:48
        _Field("block", str, ''),    # edit_record.nml:52
        _Field("block_hidden", bool, False),    # edit_record.nml:53
        _Field("highlight_line", bool, None, null=True),    # edit_record.nml:54
        _Field("highlight_column", bool, None, null=True),    # edit_record.nml:55
        _Field("auto_indent", bool, None, null=True),    # edit_record.nml:56
        _Field("justify_on_wrap", bool, None, null=True),    # edit_record.nml:57
        _Field("auto_brackets", bool, None, null=True),    # edit_record.nml:58
        _Field("left_margin", int, None, null=True),    # edit_record.nml:59
        _Field("right_margin", int, None, null=True),    # edit_record.nml:60
        _Field("paragraph", int, None, null=True),    # edit_record.nml:61
        _Field("insert_tabs", bool, None, null=True),    # edit_record.nml:64
        _Field("line_numbers", bool, None, null=True),    # edit_record.nml:66
        _Field("soft_wrap", bool, None, null=True),    # edit_record.nml:68
    )
    __indexes__ = (
        _Index("by_path", ('path',), unique=True),    # edit_record.nml:69
        _Index("by_seq", ('seq',)),    # edit_record.nml:70
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "edit_history" ("id" INTEGER PRIMARY KEY, "path" TEXT NOT NULL DEFAULT \'\', "pinned" INTEGER NOT NULL DEFAULT 0, "seq" INTEGER NOT NULL DEFAULT 0, "used" REAL NOT NULL DEFAULT 0.0, "zoomed" INTEGER NOT NULL DEFAULT 1, "x" INTEGER NOT NULL DEFAULT 0, "y" INTEGER NOT NULL DEFAULT 0, "width" INTEGER NOT NULL DEFAULT 0, "height" INTEGER NOT NULL DEFAULT 0, "desk_width" INTEGER NOT NULL DEFAULT 0, "desk_height" INTEGER NOT NULL DEFAULT 0, "line" INTEGER NOT NULL DEFAULT 0, "col" INTEGER NOT NULL DEFAULT 0, "top" INTEGER NOT NULL DEFAULT 0, "left" INTEGER NOT NULL DEFAULT 0, "overwrite" INTEGER NOT NULL DEFAULT 0, "vertical_blocks" INTEGER NOT NULL DEFAULT 0, "highlight" INTEGER NOT NULL DEFAULT 1, "file_type" TEXT NOT NULL DEFAULT \'\', "marks" TEXT NOT NULL DEFAULT \'\', "block" TEXT NOT NULL DEFAULT \'\', "block_hidden" INTEGER NOT NULL DEFAULT 0, "highlight_line" INTEGER, "highlight_column" INTEGER, "auto_indent" INTEGER, "justify_on_wrap" INTEGER, "auto_brackets" INTEGER, "left_margin" INTEGER, "right_margin" INTEGER, "paragraph" INTEGER, "insert_tabs" INTEGER, "line_numbers" INTEGER, "soft_wrap" INTEGER)',
        'CREATE UNIQUE INDEX "edit_history_by_path" ON "edit_history" ("path")',
        'CREATE INDEX "edit_history_by_seq" ON "edit_history" ("seq")',
    )
    __schema__ = "84f901c48e0f18c5"

    id: int | None

    #: The absolute path: the record's ``fName`` without its flag.
    path: str    # edit_record.nml:21

    #: The flag: a pinned record is never evicted or deleted.
    pinned: bool    # edit_record.nml:23
    seq: int    # edit_record.nml:24

    #: When the file was last viewed or edited, by ``time.time()``; 0 for a
    #: record from before this was kept.  A departure: DN's record kept no time.
    used: float    # edit_record.nml:27

    #: The window, ``fOrigin``/``fSize``, on a desktop ``fDeskSize`` big.
    zoomed: bool    # edit_record.nml:29
    x: int# edit_record.nml:30
    y: int# edit_record.nml:31
    width: int    # edit_record.nml:32
    height: int    # edit_record.nml:33
    desk_width: int    # edit_record.nml:34
    desk_height: int    # edit_record.nml:35
    line: int    # edit_record.nml:36
    col: int    # edit_record.nml:37
    top: int    # edit_record.nml:38
    left: int    # edit_record.nml:39
    overwrite: bool    # edit_record.nml:40
    vertical_blocks: bool    # edit_record.nml:41

    #: ``HiLite``: Editor > Options > *Syntax highlight*.
    highlight: bool    # edit_record.nml:43

    #: *File type*: the lexer chosen for the text, ``none``, or empty for
    #: ``highlight.ini``'s choice.  DN chose by ``DN.HGL``'s masks alone.
    file_type: str    # edit_record.nml:46

    #: ``fMarks``: markers 1 to 9 as ``line:col``, comma-separated, empty where unset.
    marks: str    # edit_record.nml:48

    #: ``fBlockStart``/``fBlockEnd``: the stream block as ``line:col-line:col``,
    #: a column block's two corners (screen cells) as ``|line:col-line:col``,
    #: empty for none.
    block: str    # edit_record.nml:52
    block_hidden: bool    # edit_record.nml:53
    highlight_line: bool | None    # edit_record.nml:54
    highlight_column: bool | None    # edit_record.nml:55
    auto_indent: bool | None    # edit_record.nml:56
    justify_on_wrap: bool | None    # edit_record.nml:57
    auto_brackets: bool | None    # edit_record.nml:58
    left_margin: int | None    # edit_record.nml:59
    right_margin: int | None    # edit_record.nml:60
    paragraph: int | None    # edit_record.nml:61

    #: *Tab characters* (not DN's, nor in its record): None in a record from
    #: before it was kept, which leaves the setup's or the mask's value.
    insert_tabs: bool | None    # edit_record.nml:64

    #: *Line numbers* (not DN's): None in a record from before it was kept.
    line_numbers: bool | None    # edit_record.nml:66

    #: *Soft wrap* (not DN's): None in a record from before it was kept.
    soft_wrap: bool | None    # edit_record.nml:68
