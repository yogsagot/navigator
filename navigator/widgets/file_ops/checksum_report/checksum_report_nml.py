# navml: generated
"""Generated from ``checksum_report.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # checksum_report.nml:1
from navml.widgets.dialog.label import Label    # checksum_report.nml:2
from navml.widgets.dialog.list_viewer import ListViewer    # checksum_report.nml:3
from navml.widgets.dialog.static_text import StaticText    # checksum_report.nml:4

__navml_component__ = "ChecksumReport"

__all__ = ["ChecksumReport"]


class ChecksumReport(Dialog, _Component):
    """File > Checksums > Verify's answer.  Not DN's: a departure, asked for.

    The counts at the top and, when anything did not match, every such file
    in a list under them -- as many as there are, which a message box's few
    lines could not hold.
    """

    #: The document this class was generated from.
    __navml_source__ = "checksum_report.nml"

    #: Ids, annotated so the hand-written half completes them.
    summary: StaticText    # checksum_report.nml:18
    bad_caption: Label    # checksum_report.nml:26
    bad: ListViewer    # checksum_report.nml:36

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.summary = StaticText(parent=self)    # checksum_report.nml:17
        self.bad_caption = Label(parent=self)    # checksum_report.nml:25
        self.bad = ListViewer(parent=self)    # checksum_report.nml:35

        self.modal_width = _bind(    # checksum_report.nml:12
            lambda _o: min(70, _o.parent.width) if _o.parent is not None else 70
        )
        self.modal_height = _bind(    # checksum_report.nml:13
            lambda _o: min(20, _o.parent.height) if _o.parent is not None else 20
        )
        self.title = _bind(lambda _o: _tr('Verify Checksums'), yielding=True)    # checksum_report.nml:14
        self.buttons = 'ok'    # checksum_report.nml:15

        self.summary.x = 2    # checksum_report.nml:19
        self.summary.y = 1    # checksum_report.nml:20
        self.summary.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # checksum_report.nml:21
        self.summary.height = 4    # checksum_report.nml:22
        self.summary.wrap = False    # checksum_report.nml:23

        self.bad_caption.x = 2    # checksum_report.nml:27
        self.bad_caption.y = 6    # checksum_report.nml:28
        self.bad_caption.width = 12    # checksum_report.nml:29
        self.bad_caption.height = 1    # checksum_report.nml:30
        self.bad_caption.text = _bind(    # checksum_report.nml:31
            lambda _o: _tr('~P~roblems'),
            yielding=True,
        )
        self.bad_caption.link = _bind(lambda _o: self.bad)    # checksum_report.nml:32
        self.bad_caption.visible = _bind(lambda _o: len(self.bad.items) > 0)    # checksum_report.nml:33

        self.bad.x = 2    # checksum_report.nml:37
        self.bad.y = 7    # checksum_report.nml:38
        self.bad.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # checksum_report.nml:39
        self.bad.height = _bind(lambda _o: max(1, _o.parent.height - 12))    # checksum_report.nml:40
        self.bad.visible = _bind(lambda _o: len(_o.items) > 0)    # checksum_report.nml:41
