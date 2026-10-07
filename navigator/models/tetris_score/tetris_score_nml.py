# navml: generated
"""Generated from ``tetris_score.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # tetris_score.nml:1

__navml_component__ = "TetrisScore"

__all__ = ["TetrisScore"]


class TetrisScore(Model):    # tetris_score.nml:7
    """One line of a Top Ten: DN's ``HiScores`` record, kept in ``dn.tet``.

    Ten for Tetris and ten for Pentix, as DN's twenty were, told apart by
    ``style``.  Better first; one as good as another goes after it.
    """

    #: The document this class was generated from.
    __navml_source__ = "tetris_score.nml"
    __table__ = "tetris_scores"
    __fields__ = (
        _Field("style", str, ''),    # tetris_score.nml:10
        _Field("name", str, ''),    # tetris_score.nml:11
        _Field("start", int, 0),    # tetris_score.nml:13
        _Field("end", int, 0),    # tetris_score.nml:14
        _Field("score", int, 0),    # tetris_score.nml:15
        _Field("seq", int, 0),    # tetris_score.nml:17
    )
    __indexes__ = (
        _Index("by_style", ('style', 'score')),    # tetris_score.nml:18
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "tetris_scores" ("id" INTEGER PRIMARY KEY, "style" TEXT NOT NULL DEFAULT \'\', "name" TEXT NOT NULL DEFAULT \'\', "start" INTEGER NOT NULL DEFAULT 0, "end" INTEGER NOT NULL DEFAULT 0, "score" INTEGER NOT NULL DEFAULT 0, "seq" INTEGER NOT NULL DEFAULT 0)',
        'CREATE INDEX "tetris_scores_by_style" ON "tetris_scores" ("style", "score")',
    )
    __schema__ = "89e2390dab78a02b"

    id: int | None

    #: ``tetris`` or ``pentix``.
    style: str    # tetris_score.nml:10
    name: str    # tetris_score.nml:11

    #: The level the game began at and the one it ended at.
    start: int    # tetris_score.nml:13
    end: int    # tetris_score.nml:14
    score: int    # tetris_score.nml:15

    #: Larger is newer: the tie-break, older first.
    seq: int    # tetris_score.nml:17
