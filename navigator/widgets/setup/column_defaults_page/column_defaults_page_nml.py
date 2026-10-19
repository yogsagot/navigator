# navml: generated
"""Generated from ``column_defaults_page.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # column_defaults_page.nml:1
from navml.widgets.dialog.label import Label    # column_defaults_page.nml:2

__navml_component__ = "ColumnDefaultsPage"

__all__ = ["ColumnDefaultsPage"]


class ColumnDefaultsPage(_Component):
    """Options > File Manager > Column defaults: DOS Navigator's ``dlgColumnsDefaults``.

    Its *Disk Drive* and *File find* groups, side by side as DN had them, the
    boxes *Columns Setup*'s (Alt+K) -- POSIX's size, attributes, owner and
    date where DN's were size, date, time and descriptions.  *TEMP:* and *TDR
    View* are left out, having only meant something on DOS, and *Archives*
    until there are archive handlers.  Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "column_defaults_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # column_defaults_page.nml:13

    #: Ids, annotated so the hand-written half completes them.
    disk_caption: Label    # column_defaults_page.nml:16
    disk: CheckBoxes    # column_defaults_page.nml:25
    find_caption: Label    # column_defaults_page.nml:33
    find: CheckBoxes    # column_defaults_page.nml:42

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.disk_caption = Label(parent=self)    # column_defaults_page.nml:15
        self.disk = CheckBoxes(parent=self)    # column_defaults_page.nml:24
        self.find_caption = Label(parent=self)    # column_defaults_page.nml:32
        self.find = CheckBoxes(parent=self)    # column_defaults_page.nml:41

        self.disk_caption.x = 3    # column_defaults_page.nml:17
        self.disk_caption.y = 1    # column_defaults_page.nml:18
        self.disk_caption.width = 12    # column_defaults_page.nml:19
        self.disk_caption.height = 1    # column_defaults_page.nml:20
        self.disk_caption.text = _bind(    # column_defaults_page.nml:21
            lambda _o: _tr('~D~isk Drive'),
            yielding=True,
        )
        self.disk_caption.link = _bind(lambda _o: self.disk)    # column_defaults_page.nml:22

        self.disk.x = 3    # column_defaults_page.nml:26
        self.disk.y = 2    # column_defaults_page.nml:27
        self.disk.width = 17    # column_defaults_page.nml:28
        self.disk.height = 4    # column_defaults_page.nml:29
        self.disk.items = _bind(    # column_defaults_page.nml:30
            lambda _o: [_tr('Size'), _tr('Attributes'), _tr('Owner'), _tr('Date')],
            yielding=True,
        )

        self.find_caption.x = 21    # column_defaults_page.nml:34
        self.find_caption.y = 1    # column_defaults_page.nml:35
        self.find_caption.width = 10    # column_defaults_page.nml:36
        self.find_caption.height = 1    # column_defaults_page.nml:37
        self.find_caption.text = _bind(    # column_defaults_page.nml:38
            lambda _o: _tr('~F~ile find'),
            yielding=True,
        )
        self.find_caption.link = _bind(lambda _o: self.find)    # column_defaults_page.nml:39

        self.find.x = 21    # column_defaults_page.nml:43
        self.find.y = 2    # column_defaults_page.nml:44
        self.find.width = 17    # column_defaults_page.nml:45
        self.find.height = 5    # column_defaults_page.nml:46
        self.find.items = _bind(    # column_defaults_page.nml:47
            lambda _o: [_tr('Size'), _tr('Attributes'), _tr('Owner'), _tr('Date'), _tr('Path')],
            yielding=True,
        )
