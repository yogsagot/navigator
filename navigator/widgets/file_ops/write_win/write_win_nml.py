# navml: generated
"""Generated from ``write_win.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # write_win.nml:1
from navml.widgets.dialog.static_text import StaticText    # write_win.nml:2
from navml.widgets.progress_bar import ProgressBar    # write_win.nml:3
from navml.widgets.spinner import Spinner    # write_win.nml:4

__navml_component__ = "WriteWin"

__all__ = ["WriteWin"]


class WriteWin(Dialog, _Component):
    """A file being read or written: DOS Navigator's ``WriteMsg``, the

    ``TWriteWin`` ``ReadBlock`` put up with *Reading file* and saving with
    *Writing file*.

    DN's was a plain box, its message centred and nothing else; Esc, read
    between blocks, was the only way out.  Three departures, all for files DN
    never met: a spinner beside the message, so a slow disk is not taken for a
    hung program; ``StrGrd``'s gauge and the percentage under it, whenever the
    size is known; and *Cancel*, which says what Esc does.
    """

    #: The document this class was generated from.
    __navml_source__ = "write_win.nml"

    notice: str = _reactive('')    # write_win.nml:22

    #: How far the work has got, and how far it goes; a total of 0 is not
    #: known, and shows neither gauge nor percentage.
    position: int = _reactive(0)    # write_win.nml:25
    total: int = _reactive(0)    # write_win.nml:26

    #: False for work that cannot stop half way -- a file written in place --
    #: which takes *Cancel* away and lets Esc and Enter do nothing.
    cancellable: bool = _reactive(True)    # write_win.nml:29

    #: Ids, annotated so the hand-written half completes them.
    spinner: Spinner    # write_win.nml:32
    notice_row: StaticText    # write_win.nml:39
    bar: ProgressBar    # write_win.nml:48
    percent_row: StaticText    # write_win.nml:58

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.spinner = Spinner(parent=self)    # write_win.nml:31
        self.notice_row = StaticText(parent=self)    # write_win.nml:38
        self.bar = ProgressBar(parent=self)    # write_win.nml:47
        self.percent_row = StaticText(parent=self)    # write_win.nml:57

        self.modal_width = 34    # write_win.nml:16
        self.modal_height = 9    # write_win.nml:17
        self.title = ''    # write_win.nml:18
        self.buttons = 'ok'    # write_win.nml:19
        self.closable = False    # write_win.nml:20

        self.spinner.x = _bind(    # write_win.nml:33
            lambda _o: max(1, (_o.parent.width - len(self.notice)) // 2 - 2)
        )
        self.spinner.y = 1    # write_win.nml:34
        self.spinner.width = 1    # write_win.nml:35
        self.spinner.height = 1    # write_win.nml:36

        self.notice_row.x = 2    # write_win.nml:40
        self.notice_row.y = 1    # write_win.nml:41
        self.notice_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # write_win.nml:42
        self.notice_row.height = 1    # write_win.nml:43
        self.notice_row.align = 'center'    # write_win.nml:44
        self.notice_row.text = _bind(lambda _o: self.notice)    # write_win.nml:45

        self.bar.x = 2    # write_win.nml:49
        self.bar.y = 3    # write_win.nml:50
        self.bar.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # write_win.nml:51
        self.bar.height = 1    # write_win.nml:52
        self.bar.visible = _bind(lambda _o: self.total > 0)    # write_win.nml:53
        self.bar.value = _bind(lambda _o: self.position)    # write_win.nml:54
        self.bar.total = _bind(lambda _o: self.total)    # write_win.nml:55

        self.percent_row.x = 2    # write_win.nml:59
        self.percent_row.y = 4    # write_win.nml:60
        self.percent_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # write_win.nml:61
        self.percent_row.height = 1    # write_win.nml:62
        self.percent_row.align = 'center'    # write_win.nml:63
        self.percent_row.visible = _bind(lambda _o: self.total > 0)    # write_win.nml:64
        self.percent_row.text = _bind(lambda _o: '%d%%' % self.bar.percent)    # write_win.nml:65
