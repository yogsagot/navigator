# navml: generated
"""Generated from ``search_progress.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # search_progress.nml:1
from navml.widgets.dialog.static_text import StaticText    # search_progress.nml:2

__navml_component__ = "SearchProgress"

__all__ = ["SearchProgress"]


class SearchProgress(Dialog, _Component):
    """A search that is taking a while: DOS Navigator's ``TWhileView``, the box

    ``SearchFileStr`` put up once its timer ran out.

    ``TWhileView`` is a double frame with the title on the top edge, centred
    lines, and one *Stop* button (``dlStop``) that Esc and Enter press too.
    The first line is ``StrGrd``'s thirty-column gauge, ``█`` done and ``▒`` to
    go; the second is the percentage.  DN opened it 29 wide and let the gauge
    widen it to 34, which is where this one starts.
    """

    #: The document this class was generated from.
    __navml_source__ = "search_progress.nml"

    #: Where the search has got to, and how far it can go.  The position is
    #: the offset being read, backwards or forwards, as ``StrGrd(L, I)`` was.
    position: int = _reactive(0)    # search_progress.nml:22
    total: int = _reactive(0)    # search_progress.nml:23

    #: Ids, annotated so the hand-written half completes them.
    gauge_row: StaticText    # search_progress.nml:26
    percent_row: StaticText    # search_progress.nml:35

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.gauge_row = StaticText(parent=self)    # search_progress.nml:25
        self.percent_row = StaticText(parent=self)    # search_progress.nml:34

        self.modal_width = 34    # search_progress.nml:13
        self.modal_height = 8    # search_progress.nml:14
        self.title = 'Search Progress'    # search_progress.nml:15
        self.buttons = 'ok'    # search_progress.nml:16
        self.closable = False    # search_progress.nml:18

        self.gauge_row.x = 2    # search_progress.nml:27
        self.gauge_row.y = 1    # search_progress.nml:28
        self.gauge_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # search_progress.nml:29
        self.gauge_row.height = 1    # search_progress.nml:30
        self.gauge_row.align = 'center'    # search_progress.nml:31
        self.gauge_row.text = _bind(lambda _o: self.gauge_text())    # search_progress.nml:32

        self.percent_row.x = 2    # search_progress.nml:36
        self.percent_row.y = 2    # search_progress.nml:37
        self.percent_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # search_progress.nml:38
        self.percent_row.height = 1    # search_progress.nml:39
        self.percent_row.align = 'center'    # search_progress.nml:40
        self.percent_row.text = _bind(lambda _o: '%d%%' % self.percent())    # search_progress.nml:41
