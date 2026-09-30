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
from navml.widgets.progress_bar import ProgressBar    # search_progress.nml:3

__navml_component__ = "SearchProgress"

__all__ = ["SearchProgress"]


class SearchProgress(Dialog, _Component):
    """A search that is taking a while: DOS Navigator's ``TWhileView``, the box

    ``SearchFileStr`` put up once its timer ran out.

    ``TWhileView`` is a double frame with the title on the top edge, centred
    lines, and one *Stop* button (``dlStop``) that Esc and Enter press too.
    The first line is ``StrGrd``'s gauge, a ``ProgressBar``, ``█`` done and
    ``▒`` to go; the second is the percentage.  DN opened it 29 wide and let the gauge
    widen it to 34, which is where this one starts.
    """

    #: The document this class was generated from.
    __navml_source__ = "search_progress.nml"

    #: Where the search has got to, and how far it can go.  The position is
    #: the offset being read, backwards or forwards, as ``StrGrd(L, I)`` was.
    position: int = _reactive(0)    # search_progress.nml:23
    total: int = _reactive(0)    # search_progress.nml:24

    #: Ids, annotated so the hand-written half completes them.
    bar: ProgressBar    # search_progress.nml:29
    percent_row: StaticText    # search_progress.nml:38

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.bar = ProgressBar(parent=self)    # search_progress.nml:28
        self.percent_row = StaticText(parent=self)    # search_progress.nml:37

        self.modal_width = 34    # search_progress.nml:14
        self.modal_height = 8    # search_progress.nml:15
        self.title = 'Search Progress'    # search_progress.nml:16
        self.buttons = 'ok'    # search_progress.nml:17
        self.closable = False    # search_progress.nml:19

        self.bar.x = 2    # search_progress.nml:30
        self.bar.y = 1    # search_progress.nml:31
        self.bar.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # search_progress.nml:32
        self.bar.height = 1    # search_progress.nml:33
        self.bar.value = _bind(lambda _o: self.position)    # search_progress.nml:34
        self.bar.total = _bind(lambda _o: self.total)    # search_progress.nml:35

        self.percent_row.x = 2    # search_progress.nml:39
        self.percent_row.y = 2    # search_progress.nml:40
        self.percent_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # search_progress.nml:41
        self.percent_row.height = 1    # search_progress.nml:42
        self.percent_row.align = 'center'    # search_progress.nml:43
        self.percent_row.text = _bind(lambda _o: '%d%%' % self.bar.percent)    # search_progress.nml:44
