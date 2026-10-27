# navml: generated
"""Generated from ``checksum_progress.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # checksum_progress.nml:1
from navml.widgets.dialog.static_text import StaticText    # checksum_progress.nml:2
from navml.widgets.progress_bar import ProgressBar    # checksum_progress.nml:3
from navml.widgets.spinner import Spinner    # checksum_progress.nml:4

__navml_component__ = "ChecksumProgress"

__all__ = ["ChecksumProgress"]


class ChecksumProgress(Dialog, _Component):
    """Files being hashed, by File > Checksums' Calculate and Verify.  Not DN's

    (a departure, as the feature is): the file being read, a gauge over the
    bytes of them all, how many are done, and *Cancel*, which says what Esc does.
    """

    #: The document this class was generated from.
    __navml_source__ = "checksum_progress.nml"

    current: str = _reactive('')    # checksum_progress.nml:16
    position: int = _reactive(0)    # checksum_progress.nml:17
    total: int = _reactive(0)    # checksum_progress.nml:18
    files_done: int = _reactive(0)    # checksum_progress.nml:19
    files_total: int = _reactive(0)    # checksum_progress.nml:20

    #: Ids, annotated so the hand-written half completes them.
    spinner: Spinner    # checksum_progress.nml:23
    current_row: StaticText    # checksum_progress.nml:30
    bar: ProgressBar    # checksum_progress.nml:39
    count_row: StaticText    # checksum_progress.nml:48

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.spinner = Spinner(parent=self)    # checksum_progress.nml:22
        self.current_row = StaticText(parent=self)    # checksum_progress.nml:29
        self.bar = ProgressBar(parent=self)    # checksum_progress.nml:38
        self.count_row = StaticText(parent=self)    # checksum_progress.nml:47

        self.modal_width = _bind(    # checksum_progress.nml:10
            lambda _o: min(64, _o.parent.width) if _o.parent is not None else 64
        )
        self.modal_height = 10    # checksum_progress.nml:11
        self.title = _bind(lambda _o: _tr('Checksums'), yielding=True)    # checksum_progress.nml:12
        self.buttons = 'ok'    # checksum_progress.nml:13
        self.closable = False    # checksum_progress.nml:14

        self.spinner.x = 2    # checksum_progress.nml:24
        self.spinner.y = 1    # checksum_progress.nml:25
        self.spinner.width = 1    # checksum_progress.nml:26
        self.spinner.height = 1    # checksum_progress.nml:27

        self.current_row.x = 4    # checksum_progress.nml:31
        self.current_row.y = 1    # checksum_progress.nml:32
        self.current_row.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # checksum_progress.nml:33
        self.current_row.height = 1    # checksum_progress.nml:34
        self.current_row.wrap = False    # checksum_progress.nml:35
        self.current_row.text = _bind(lambda _o: self.fit(self.current))    # checksum_progress.nml:36

        self.bar.x = 2    # checksum_progress.nml:40
        self.bar.y = 3    # checksum_progress.nml:41
        self.bar.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # checksum_progress.nml:42
        self.bar.height = 1    # checksum_progress.nml:43
        self.bar.value = _bind(lambda _o: self.position)    # checksum_progress.nml:44
        self.bar.total = _bind(lambda _o: self.total)    # checksum_progress.nml:45

        self.count_row.x = 2    # checksum_progress.nml:49
        self.count_row.y = 4    # checksum_progress.nml:50
        self.count_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # checksum_progress.nml:51
        self.count_row.height = 1    # checksum_progress.nml:52
        self.count_row.align = 'center'    # checksum_progress.nml:53
        self.count_row.text = _bind(    # checksum_progress.nml:54
            lambda _o: self.counted(self.files_done, self.files_total, self.bar.percent)
        )
