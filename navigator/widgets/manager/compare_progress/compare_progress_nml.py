# navml: generated
"""Generated from ``compare_progress.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # compare_progress.nml:1
from navml.widgets.dialog.static_text import StaticText    # compare_progress.nml:2

__navml_component__ = "CompareProgress"

__all__ = ["CompareProgress"]


class CompareProgress(Dialog, _Component):
    """*Compare directories*' *Window, recursive* under way: the directory being

    compared, and how many differences so far.  Shaped as the search's box
    (``FindProgress``), whose *Cancel* it shares; DN had no such box, its
    compare reading one directory and saying only *Comparing files*.
    """

    #: The document this class was generated from.
    __navml_source__ = "compare_progress.nml"

    directory: str = _reactive('')    # compare_progress.nml:15
    count: int = _reactive(0)    # compare_progress.nml:16

    #: Ids, annotated so the hand-written half completes them.
    directory_row: StaticText    # compare_progress.nml:19
    count_row: StaticText    # compare_progress.nml:28

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.directory_row = StaticText(parent=self)    # compare_progress.nml:18
        self.count_row = StaticText(parent=self)    # compare_progress.nml:27

        self.modal_width = 56    # compare_progress.nml:9
        self.modal_height = 8    # compare_progress.nml:10
        self.title = _bind(    # compare_progress.nml:11
            lambda _o: _tr('Compare directories'),
            yielding=True,
        )
        self.buttons = 'ok'    # compare_progress.nml:12
        self.closable = False    # compare_progress.nml:13

        self.directory_row.x = 2    # compare_progress.nml:20
        self.directory_row.y = 1    # compare_progress.nml:21
        self.directory_row.width = _bind(    # compare_progress.nml:22
            lambda _o: max(0, _o.parent.width - 4)
        )
        self.directory_row.height = 1    # compare_progress.nml:23
        self.directory_row.align = 'center'    # compare_progress.nml:24
        self.directory_row.text = _bind(lambda _o: self.fit(self.directory))    # compare_progress.nml:25

        self.count_row.x = 2    # compare_progress.nml:29
        self.count_row.y = 2    # compare_progress.nml:30
        self.count_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # compare_progress.nml:31
        self.count_row.height = 1    # compare_progress.nml:32
        self.count_row.align = 'center'    # compare_progress.nml:33
        self.count_row.text = _bind(lambda _o: self.count_text(self.count))    # compare_progress.nml:34
