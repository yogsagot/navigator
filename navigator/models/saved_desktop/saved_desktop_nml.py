# navml: generated
"""Generated from ``saved_desktop.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # saved_desktop.nml:1

__navml_component__ = "SavedDesktop"

__all__ = ["SavedDesktop"]


class SavedDesktop(Model):    # saved_desktop.nml:7
    """A desktop saved: what DOS Navigator wrote to ``DN.DSK`` (``SaveDesktop``),

    the windows and their state, as JSON (``navigator.desktop_state``).  One
    row a name; Navigator writes ``default``, as DN wrote ``DN`` and
    ``$DNDSK``.
    """

    #: The document this class was generated from.
    __navml_source__ = "saved_desktop.nml"
    __table__ = "desktops"
    __fields__ = (
        _Field("name", str, ''),    # saved_desktop.nml:9
        _Field("data", str, ''),    # saved_desktop.nml:11
    )
    __indexes__ = (
        _Index("by_name", ('name',), unique=True),    # saved_desktop.nml:12
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "desktops" ("id" INTEGER PRIMARY KEY, "name" TEXT NOT NULL DEFAULT \'\', "data" TEXT NOT NULL DEFAULT \'\')',
        'CREATE UNIQUE INDEX "desktops_by_name" ON "desktops" ("name")',
    )
    __schema__ = "d9124dfceb780eb5"

    id: int | None
    name: str    # saved_desktop.nml:9

    #: ``navigator.desktop_state.snapshot``'s dict, as JSON.
    data: str    # saved_desktop.nml:11
