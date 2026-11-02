# navml: generated
"""Generated from ``query_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # query_dialog.nml:1
from navml.widgets.dialog.field import Field    # query_dialog.nml:2

__navml_component__ = "QueryDialog"

__all__ = ["QueryDialog"]


class QueryDialog(Dialog, _Component):
    """F6 in the database window on a SQLite file: a query, typed on one line

    with its history -- not DN's, whose dBase viewer had no SQL to type.  It
    runs reading only (``navigator.lib.viewer.sqlite``).
    """

    #: The document this class was generated from.
    __navml_source__ = "query_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    sql: Field    # query_dialog.nml:13

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.sql = Field(parent=self)    # query_dialog.nml:12

        self.modal_width = 70    # query_dialog.nml:8
        self.modal_height = 8    # query_dialog.nml:9
        self.title = _bind(lambda _o: _tr('Query'), yielding=True)    # query_dialog.nml:10

        self.sql.x = 2    # query_dialog.nml:14
        self.sql.y = 2    # query_dialog.nml:15
        self.sql.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # query_dialog.nml:16
        self.sql.height = 1    # query_dialog.nml:17
        self.sql.label_text = _bind(lambda _o: _tr('~S~ELECT'), yielding=True)    # query_dialog.nml:18
        self.sql.label_width = 8    # query_dialog.nml:19
        self.sql.history_id = 'sql_query'    # query_dialog.nml:20
