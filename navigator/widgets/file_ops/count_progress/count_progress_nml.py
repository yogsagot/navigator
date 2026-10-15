# navml: generated
"""Generated from ``count_progress.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # count_progress.nml:1
from navml.widgets.dialog.static_text import StaticText    # count_progress.nml:2
from navml.widgets.spinner import Spinner    # count_progress.nml:3

__navml_component__ = "CountProgress"

__all__ = ["CountProgress"]


class CountProgress(Dialog, _Component):
    """Directories being counted: Alt+G's ``CountLen``, which DN did behind a

    plain wait box.  A departure: what has been met so far -- bytes, files and
    directories -- so a long count is seen to be getting somewhere; when there
    are several, the one being counted now, with what is in it beside the total.
    *Cancel* says what Esc does.
    """

    #: The document this class was generated from.
    __navml_source__ = "count_progress.nml"

    #: The directory being counted; shown only when there are *several*.
    directory: str = _reactive('')    # count_progress.nml:20
    several: bool = _reactive(False)    # count_progress.nml:21

    #: What has been met in the directory being counted now.
    here_size: int = _reactive(0)    # count_progress.nml:23
    here_files: int = _reactive(0)    # count_progress.nml:24
    here_directories: int = _reactive(0)    # count_progress.nml:25

    #: What has been met across every directory counted so far.
    size: int = _reactive(0)    # count_progress.nml:27
    files: int = _reactive(0)    # count_progress.nml:28
    directories: int = _reactive(0)    # count_progress.nml:29

    #: Ids, annotated so the hand-written half completes them.
    spinner: Spinner    # count_progress.nml:33
    directory_row: StaticText    # count_progress.nml:40
    table: StaticText    # count_progress.nml:53

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.spinner = Spinner(parent=self)    # count_progress.nml:32
        self.directory_row = StaticText(parent=self)    # count_progress.nml:39
        self.table = StaticText(parent=self)    # count_progress.nml:52

        self.modal_width = _bind(    # count_progress.nml:13
            lambda _o: self.box_width(_o.parent.width if _o.parent is not None else 0, self.several, self.here_size, self.size, self.here_files, self.files, self.here_directories, self.directories)
        )
        self.modal_height = _bind(lambda _o: 12 if self.several else 11)    # count_progress.nml:14
        self.title = _bind(    # count_progress.nml:15
            lambda _o: _tr('Counting directory length'),
            yielding=True,
        )
        self.buttons = 'ok'    # count_progress.nml:16
        self.closable = False    # count_progress.nml:17

        self.spinner.x = 4    # count_progress.nml:34
        self.spinner.y = 1    # count_progress.nml:35
        self.spinner.width = 1    # count_progress.nml:36
        self.spinner.height = 1    # count_progress.nml:37

        self.directory_row.x = 6    # count_progress.nml:41
        self.directory_row.y = 1    # count_progress.nml:42
        self.directory_row.width = _bind(    # count_progress.nml:43
            lambda _o: max(0, _o.parent.width - 8)
        )
        self.directory_row.height = 1    # count_progress.nml:44
        self.directory_row.visible = _bind(lambda _o: self.several)    # count_progress.nml:45
        self.directory_row.text = _bind(lambda _o: self.fit(self.directory))    # count_progress.nml:46

        self.table.x = 4    # count_progress.nml:54
        self.table.y = 3    # count_progress.nml:55
        self.table.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # count_progress.nml:56
        self.table.height = 4    # count_progress.nml:57
        self.table.wrap = False    # count_progress.nml:58
        self.table.text = _bind(    # count_progress.nml:59
            lambda _o: self.counts(_o.width, self.several, self.here_size, self.size, self.here_files, self.files, self.here_directories, self.directories)
        )
