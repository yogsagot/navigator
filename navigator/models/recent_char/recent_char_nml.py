# navml: generated
"""Generated from ``recent_char.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # recent_char.nml:1

__navml_component__ = "RecentChar"

__all__ = ["RecentChar"]


class RecentChar(Model):    # recent_char.nml:8
    """A character taken from the character table: its *Recent* category.

    One row a character, taken again moving it to the front; ``seq`` orders
    them newest first, and only the newest ``RECENT_LIMIT`` are kept
    (``navigator/lib/utilities/unicode_table.py``).
    """

    #: The document this class was generated from.
    __navml_source__ = "recent_char.nml"
    __table__ = "recent_chars"
    __fields__ = (
        _Field("code", int, 0),    # recent_char.nml:11
        _Field("seq", int, 0),    # recent_char.nml:13
    )
    __indexes__ = (
        _Index("by_code", ('code',), unique=True),    # recent_char.nml:14
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "recent_chars" ("id" INTEGER PRIMARY KEY, "code" INTEGER NOT NULL DEFAULT 0, "seq" INTEGER NOT NULL DEFAULT 0)',
        'CREATE UNIQUE INDEX "recent_chars_by_code" ON "recent_chars" ("code")',
    )
    __schema__ = "bebffb1b91ad6e1c"

    id: int | None

    #: The code point.
    code: int    # recent_char.nml:11

    #: Larger is newer; only the order means anything.
    seq: int    # recent_char.nml:13
