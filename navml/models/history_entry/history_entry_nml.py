# navml: generated
"""Generated from ``history_entry.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # history_entry.nml:1

__navml_component__ = "HistoryEntry"

__all__ = ["HistoryEntry"]


class HistoryEntry(Model):    # history_entry.nml:7
    """One remembered input-line string: an entry of a ``HistList``.

    Every list -- ``"mkdir"``, ``"copy"``, ``"command"`` -- shares the one
    table, told apart by ``list_id``; ``seq`` orders a list newest first.
    """

    #: The document this class was generated from.
    __navml_source__ = "history_entry.nml"
    __table__ = "history"
    __fields__ = (
        _Field("list_id", str, ''),    # history_entry.nml:10
        _Field("text", str, ''),    # history_entry.nml:11
        _Field("pinned", bool, False),    # history_entry.nml:13
        _Field("seq", int, 0),    # history_entry.nml:15
    )
    __indexes__ = (
        _Index("entry", ('list_id', 'text'), unique=True),    # history_entry.nml:16
        _Index("by_list", ('list_id', 'seq')),    # history_entry.nml:17
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "history" ("id" INTEGER PRIMARY KEY, "list_id" TEXT NOT NULL DEFAULT \'\', "text" TEXT NOT NULL DEFAULT \'\', "pinned" INTEGER NOT NULL DEFAULT 0, "seq" INTEGER NOT NULL DEFAULT 0)',
        'CREATE UNIQUE INDEX "history_entry" ON "history" ("list_id", "text")',
        'CREATE INDEX "history_by_list" ON "history" ("list_id", "seq")',
    )
    __schema__ = "b1c0f09837ffbc20"

    id: int | None

    #: The history id the input lines sharing this list name.
    list_id: str    # history_entry.nml:10
    text: str    # history_entry.nml:11

    #: DOS Navigator's flag byte: a pinned entry is never evicted.
    pinned: bool    # history_entry.nml:13

    #: Larger is newer; only the order means anything.
    seq: int    # history_entry.nml:15
