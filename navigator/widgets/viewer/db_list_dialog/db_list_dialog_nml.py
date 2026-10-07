# navml: generated
"""Generated from ``db_list_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # db_list_dialog.nml:1
from navml.widgets.dialog.list_viewer import ListViewer    # db_list_dialog.nml:2
from navml.widgets.dialog.static_text import StaticText    # db_list_dialog.nml:3

__navml_component__ = "DBListDialog"

__all__ = ["DBListDialog"]


class DBListDialog(Dialog, _Component):
    """The dBase viewer's two boxes of lines: F2's *Structure of* (``GetInfo``:

    ``dlDBViewInfoString`` over ``TFieldListBox``) and F3's *Memo view*
    (``ViewMemo``'s text) -- a heading, the lines under it, and OK.
    """

    #: The document this class was generated from.
    __navml_source__ = "db_list_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    heading: StaticText    # db_list_dialog.nml:14
    lines: ListViewer    # db_list_dialog.nml:21

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.heading = StaticText(parent=self)    # db_list_dialog.nml:13
        self.lines = ListViewer(parent=self)    # db_list_dialog.nml:20

        self.modal_width = 50    # db_list_dialog.nml:9
        self.modal_height = 18    # db_list_dialog.nml:10
        self.buttons = 'ok'    # db_list_dialog.nml:11

        self.heading.x = 2    # db_list_dialog.nml:15
        self.heading.y = 1    # db_list_dialog.nml:16
        self.heading.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # db_list_dialog.nml:17
        self.heading.height = 1    # db_list_dialog.nml:18

        self.lines.framed = False    # db_list_dialog.nml:22
        self.lines.x = 2    # db_list_dialog.nml:23
        self.lines.y = 2    # db_list_dialog.nml:24
        self.lines.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # db_list_dialog.nml:25
        self.lines.height = _bind(lambda _o: max(0, _o.parent.height - 7))    # db_list_dialog.nml:26
