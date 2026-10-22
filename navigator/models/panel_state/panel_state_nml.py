# navml: generated
"""Generated from ``panel_state.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # panel_state.nml:1

__navml_component__ = "PanelState"

__all__ = ["PanelState"]


class PanelState(Model):    # panel_state.nml:8
    """What a side of the file manager was left showing: Ctrl+H's hidden files and

    Alt+I's footer, written at each switch and seeded into each new file
    manager's panel on that side (``navigator.lib.config.panel_state``).  One
    row a side, ``left`` or ``right``.  A departure: DN's ``ossShowHidden`` was
    a system option and it had no footer to hide.
    """

    #: The document this class was generated from.
    __navml_source__ = "panel_state.nml"
    __table__ = "panel_states"
    __fields__ = (
        _Field("side", str, ''),    # panel_state.nml:10
        _Field("show_hidden", bool, True),    # panel_state.nml:11
        _Field("show_info", bool, True),    # panel_state.nml:12
    )
    __indexes__ = (
        _Index("by_side", ('side',), unique=True),    # panel_state.nml:13
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "panel_states" ("id" INTEGER PRIMARY KEY, "side" TEXT NOT NULL DEFAULT \'\', "show_hidden" INTEGER NOT NULL DEFAULT 1, "show_info" INTEGER NOT NULL DEFAULT 1)',
        'CREATE UNIQUE INDEX "panel_states_by_side" ON "panel_states" ("side")',
    )
    __schema__ = "16b2112c95e85576"

    id: int | None
    side: str    # panel_state.nml:10
    show_hidden: bool    # panel_state.nml:11
    show_info: bool    # panel_state.nml:12
