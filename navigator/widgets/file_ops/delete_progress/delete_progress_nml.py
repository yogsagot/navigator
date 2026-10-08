# navml: generated
"""Generated from ``delete_progress.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # delete_progress.nml:1
from navml.widgets.dialog.static_text import StaticText    # delete_progress.nml:2
from navml.widgets.progress_bar import ProgressBar    # delete_progress.nml:3

__navml_component__ = "DeleteProgress"

__all__ = ["DeleteProgress"]


class DeleteProgress(Dialog, _Component):
    """A delete under way: the ``TWhileView`` ``ERASER.PAS`` opened, titled *Erase*.

    DN's two lines -- ``Erasing the file`` or ``Erasing the directory``, and
    the name -- and then what DN did not have, a gauge over the entries
    counted before the first went, with its count.  One *Cancel* where DN's
    said *Stop*, which asks before it stops, as ``dlQueryAbort`` did.
    """

    #: The document this class was generated from.
    __navml_source__ = "delete_progress.nml"

    action: str = _reactive('')    # delete_progress.nml:18
    path: str = _reactive('')    # delete_progress.nml:19
    done: int = _reactive(0)    # delete_progress.nml:20
    total: int = _reactive(0)    # delete_progress.nml:21

    #: Ids, annotated so the hand-written half completes them.
    action_row: StaticText    # delete_progress.nml:24
    path_row: StaticText    # delete_progress.nml:33
    bar: ProgressBar    # delete_progress.nml:42
    count_row: StaticText    # delete_progress.nml:52

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.action_row = StaticText(parent=self)    # delete_progress.nml:23
        self.path_row = StaticText(parent=self)    # delete_progress.nml:32
        self.bar = ProgressBar(parent=self)    # delete_progress.nml:41
        self.count_row = StaticText(parent=self)    # delete_progress.nml:51

        self.modal_width = 50    # delete_progress.nml:12
        self.modal_height = 10    # delete_progress.nml:13
        self.title = _bind(lambda _o: _tr('Erase'), yielding=True)    # delete_progress.nml:14
        self.buttons = 'ok'    # delete_progress.nml:15
        self.closable = False    # delete_progress.nml:16

        self.action_row.x = 2    # delete_progress.nml:25
        self.action_row.y = 1    # delete_progress.nml:26
        self.action_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # delete_progress.nml:27
        self.action_row.height = 1    # delete_progress.nml:28
        self.action_row.align = 'center'    # delete_progress.nml:29
        self.action_row.text = _bind(lambda _o: self.action)    # delete_progress.nml:30

        self.path_row.x = 2    # delete_progress.nml:34
        self.path_row.y = 2    # delete_progress.nml:35
        self.path_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # delete_progress.nml:36
        self.path_row.height = 1    # delete_progress.nml:37
        self.path_row.align = 'center'    # delete_progress.nml:38
        self.path_row.text = _bind(lambda _o: self.fit(self.path))    # delete_progress.nml:39

        self.bar.x = 4    # delete_progress.nml:43
        self.bar.y = 4    # delete_progress.nml:44
        self.bar.width = _bind(lambda _o: max(0, _o.parent.width - 8))    # delete_progress.nml:45
        self.bar.height = 1    # delete_progress.nml:46
        self.bar.value = _bind(lambda _o: self.done)    # delete_progress.nml:47
        self.bar.total = _bind(lambda _o: max(1, self.total))    # delete_progress.nml:49

        self.count_row.x = 2    # delete_progress.nml:53
        self.count_row.y = 5    # delete_progress.nml:54
        self.count_row.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # delete_progress.nml:55
        self.count_row.height = 1    # delete_progress.nml:56
        self.count_row.align = 'center'    # delete_progress.nml:57
        self.count_row.text = _bind(    # delete_progress.nml:58
            lambda _o: self.count(self.done, self.total, self.bar.percent)
        )
