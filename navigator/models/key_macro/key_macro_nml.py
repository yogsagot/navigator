# navml: generated
"""Generated from ``key_macro.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # key_macro.nml:1

__navml_component__ = "KeyMacro"

__all__ = ["KeyMacro"]


class KeyMacro(Model):    # key_macro.nml:9
    """A key macro: DOS Navigator's ``TKeyMacros``, one of the ten

    ``KeyMacroses`` -- the keys recorded into a slot, kept between sessions
    (a departure: DN's lived as long as the desktop did).

    ``keys`` is the recording as JSON (``navigator/lib/config/macros.py``
    ``encode``): every key, and every paste, in the order typed.
    """

    #: The document this class was generated from.
    __navml_source__ = "key_macro.nml"
    __table__ = "key_macros"
    __fields__ = (
        _Field("slot", int, 0),    # key_macro.nml:12
        _Field("keys", str, '[]'),    # key_macro.nml:13
    )
    __indexes__ = (
        _Index("by_slot", ('slot',), unique=True),    # key_macro.nml:14
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "key_macros" ("id" INTEGER PRIMARY KEY, "slot" INTEGER NOT NULL DEFAULT 0, "keys" TEXT NOT NULL DEFAULT \'[]\')',
        'CREATE UNIQUE INDEX "key_macros_by_slot" ON "key_macros" ("slot")',
    )
    __schema__ = "2ff65ef9107875a6"

    id: int | None

    #: 1 to 9: the digit of ``Ctrl+J R N`` and ``Ctrl+J N``.
    slot: int    # key_macro.nml:12
    keys: str    # key_macro.nml:13
