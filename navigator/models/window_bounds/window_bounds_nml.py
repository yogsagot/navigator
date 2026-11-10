# navml: generated
"""Generated from ``window_bounds.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # window_bounds.nml:1

__navml_component__ = "WindowBounds"

__all__ = ["WindowBounds"]


class WindowBounds(Model):    # window_bounds.nml:8
    """The last rectangle a kind of window had: DOS Navigator's ``TempBounds`` and

    ``LastEditDeskSize`` for the editor (``MICROED.PAS:483``), which it kept in
    its configuration and where *Store editor position* opened every new editor,
    scaled to the desktop (``navigator.lib.config.file_history.place_last_edit``).
    One row a kind -- ``editor``.
    """

    #: The document this class was generated from.
    __navml_source__ = "window_bounds.nml"
    __table__ = "window_bounds"
    __fields__ = (
        _Field("kind", str, ''),    # window_bounds.nml:10
        _Field("zoomed", bool, False),    # window_bounds.nml:11
        _Field("x", int, 0),    # window_bounds.nml:12
        _Field("y", int, 0),    # window_bounds.nml:13
        _Field("width", int, 0),    # window_bounds.nml:14
        _Field("height", int, 0),    # window_bounds.nml:15
        _Field("desk_width", int, 0),    # window_bounds.nml:16
        _Field("desk_height", int, 0),    # window_bounds.nml:17
    )
    __indexes__ = (
        _Index("by_kind", ('kind',), unique=True),    # window_bounds.nml:18
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "window_bounds" ("id" INTEGER PRIMARY KEY, "kind" TEXT NOT NULL DEFAULT \'\', "zoomed" INTEGER NOT NULL DEFAULT 0, "x" INTEGER NOT NULL DEFAULT 0, "y" INTEGER NOT NULL DEFAULT 0, "width" INTEGER NOT NULL DEFAULT 0, "height" INTEGER NOT NULL DEFAULT 0, "desk_width" INTEGER NOT NULL DEFAULT 0, "desk_height" INTEGER NOT NULL DEFAULT 0)',
        'CREATE UNIQUE INDEX "window_bounds_by_kind" ON "window_bounds" ("kind")',
    )
    __schema__ = "ae9e9a573d6f5b94"

    id: int | None
    kind: str    # window_bounds.nml:10
    zoomed: bool    # window_bounds.nml:11
    x: int# window_bounds.nml:12
    y: int# window_bounds.nml:13
    width: int    # window_bounds.nml:14
    height: int    # window_bounds.nml:15
    desk_width: int    # window_bounds.nml:16
    desk_height: int    # window_bounds.nml:17
