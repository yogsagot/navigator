# navml: generated
"""Generated from ``copy_progress.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # copy_progress.nml:1
from navml.widgets.dialog.static_text import StaticText    # copy_progress.nml:2
from navml.widgets.progress_bar import ProgressBar    # copy_progress.nml:3

__navml_component__ = "CopyProgress"

__all__ = ["CopyProgress"]


class CopyProgress(Dialog, _Component):
    """A copy under way: the ``TWhileView`` ``FILECOPY.PAS`` opened 40 by 13.

    DN's rows were the file being read and its gauge, then the file being
    written and its; a copy here reads and writes in one pass, so the rows are
    the file and where it goes, the file's gauge, and the whole copy's gauge
    with its count -- DN's ``Total N bytes``, which it wrote on the frame.
    One *Stop*, which asks before it stops, as ``dlQueryAbort`` did.
    """

    #: The document this class was generated from.
    __navml_source__ = "copy_progress.nml"

    move: bool = _reactive(False)    # copy_progress.nml:19
    source: str = _reactive('')    # copy_progress.nml:20
    dest: str = _reactive('')    # copy_progress.nml:21
    file_done: int = _reactive(0)    # copy_progress.nml:22
    file_bytes: int = _reactive(0)    # copy_progress.nml:23
    done: int = _reactive(0)    # copy_progress.nml:24
    total: int = _reactive(0)    # copy_progress.nml:25

    #: Ids, annotated so the hand-written half completes them.
    source_row: StaticText    # copy_progress.nml:28
    dest_row: StaticText    # copy_progress.nml:36
    file_bar: ProgressBar    # copy_progress.nml:45
    file_count: StaticText    # copy_progress.nml:54
    total_bar: ProgressBar    # copy_progress.nml:63
    total_count: StaticText    # copy_progress.nml:72

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.source_row = StaticText(parent=self)    # copy_progress.nml:27
        self.dest_row = StaticText(parent=self)    # copy_progress.nml:35
        self.file_bar = ProgressBar(parent=self)    # copy_progress.nml:44
        self.file_count = StaticText(parent=self)    # copy_progress.nml:53
        self.total_bar = ProgressBar(parent=self)    # copy_progress.nml:62
        self.total_count = StaticText(parent=self)    # copy_progress.nml:71

        self.modal_width = 60    # copy_progress.nml:13
        self.modal_height = 13    # copy_progress.nml:14
        self.title = _bind(lambda _o: 'Rename/move' if self.move else 'Copy')    # copy_progress.nml:15
        self.buttons = 'ok'    # copy_progress.nml:16
        self.closable = False    # copy_progress.nml:17

        self.source_row.x = 2    # copy_progress.nml:29
        self.source_row.y = 1    # copy_progress.nml:30
        self.source_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # copy_progress.nml:31
        self.source_row.height = 1    # copy_progress.nml:32
        self.source_row.text = _bind(    # copy_progress.nml:33
            lambda _o: self.fit(' Moving ' if self.move else ' Copying ', self.source)
        )

        self.dest_row.x = 2    # copy_progress.nml:37
        self.dest_row.y = 2    # copy_progress.nml:38
        self.dest_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # copy_progress.nml:39
        self.dest_row.height = 1    # copy_progress.nml:40
        self.dest_row.text = _bind(lambda _o: self.fit(' to ', self.dest))    # copy_progress.nml:41

        self.file_bar.x = 4    # copy_progress.nml:46
        self.file_bar.y = 4    # copy_progress.nml:47
        self.file_bar.width = _bind(lambda _o: max(0, _o.parent.width - 8))    # copy_progress.nml:48
        self.file_bar.height = 1    # copy_progress.nml:49
        self.file_bar.value = _bind(lambda _o: self.file_done)    # copy_progress.nml:50
        self.file_bar.total = _bind(lambda _o: self.file_bytes)    # copy_progress.nml:51

        self.file_count.x = 2    # copy_progress.nml:55
        self.file_count.y = 5    # copy_progress.nml:56
        self.file_count.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # copy_progress.nml:57
        self.file_count.height = 1    # copy_progress.nml:58
        self.file_count.align = 'center'    # copy_progress.nml:59
        self.file_count.text = _bind(    # copy_progress.nml:60
            lambda _o: self.count(self.file_done, self.file_bar.percent)
        )

        self.total_bar.x = 4    # copy_progress.nml:64
        self.total_bar.y = 6    # copy_progress.nml:65
        self.total_bar.width = _bind(lambda _o: max(0, _o.parent.width - 8))    # copy_progress.nml:66
        self.total_bar.height = 1    # copy_progress.nml:67
        self.total_bar.value = _bind(lambda _o: self.done)    # copy_progress.nml:68
        self.total_bar.total = _bind(lambda _o: self.total)    # copy_progress.nml:69

        self.total_count.x = 2    # copy_progress.nml:73
        self.total_count.y = 7    # copy_progress.nml:74
        self.total_count.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # copy_progress.nml:75
        self.total_count.height = 1    # copy_progress.nml:76
        self.total_count.align = 'center'    # copy_progress.nml:77
        self.total_count.text = _bind(    # copy_progress.nml:78
            lambda _o: 'Total ' + self.count(self.done, self.total_bar.percent)
        )
