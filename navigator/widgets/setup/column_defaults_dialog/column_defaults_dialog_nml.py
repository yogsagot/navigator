# navml: generated
"""Generated from ``column_defaults_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # column_defaults_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # column_defaults_dialog.nml:2
from navml.widgets.dialog.label import Label    # column_defaults_dialog.nml:3

__navml_component__ = "ColumnDefaultsDialog"

__all__ = ["ColumnDefaultsDialog"]


class ColumnDefaultsDialog(Dialog, _Component):
    """Options > File Manager > Column defaults: DOS Navigator's ``dlgColumnsDefaults``.

    Its *Disk Drive* and *File find* groups, side by side as DN had them, the
    boxes *Columns Setup*'s (Alt+K) -- POSIX's size, attributes, owner and
    date where DN's were size, date, time and descriptions.  *TEMP:* and *TDR
    View* are left out, having only meant something on DOS, and *Archives*
    until there are archive handlers.  Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "column_defaults_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    disk_caption: Label    # column_defaults_dialog.nml:18
    disk: CheckBoxes    # column_defaults_dialog.nml:27
    find_caption: Label    # column_defaults_dialog.nml:35
    find: CheckBoxes    # column_defaults_dialog.nml:44

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.disk_caption = Label(parent=self)    # column_defaults_dialog.nml:17
        self.disk = CheckBoxes(parent=self)    # column_defaults_dialog.nml:26
        self.find_caption = Label(parent=self)    # column_defaults_dialog.nml:34
        self.find = CheckBoxes(parent=self)    # column_defaults_dialog.nml:43

        self.modal_width = 42    # column_defaults_dialog.nml:13
        self.modal_height = 12    # column_defaults_dialog.nml:14
        self.title = 'Column Defaults'    # column_defaults_dialog.nml:15

        self.disk_caption.x = 3    # column_defaults_dialog.nml:19
        self.disk_caption.y = 1    # column_defaults_dialog.nml:20
        self.disk_caption.width = 12    # column_defaults_dialog.nml:21
        self.disk_caption.height = 1    # column_defaults_dialog.nml:22
        self.disk_caption.text = '~D~isk Drive'    # column_defaults_dialog.nml:23
        self.disk_caption.link = _bind(lambda _o: self.disk)    # column_defaults_dialog.nml:24

        self.disk.x = 3    # column_defaults_dialog.nml:28
        self.disk.y = 2    # column_defaults_dialog.nml:29
        self.disk.width = 17    # column_defaults_dialog.nml:30
        self.disk.height = 4    # column_defaults_dialog.nml:31
        self.disk.items = ['Size', 'Attributes', 'Owner', 'Date']    # column_defaults_dialog.nml:32

        self.find_caption.x = 21    # column_defaults_dialog.nml:36
        self.find_caption.y = 1    # column_defaults_dialog.nml:37
        self.find_caption.width = 10    # column_defaults_dialog.nml:38
        self.find_caption.height = 1    # column_defaults_dialog.nml:39
        self.find_caption.text = '~F~ile find'    # column_defaults_dialog.nml:40
        self.find_caption.link = _bind(lambda _o: self.find)    # column_defaults_dialog.nml:41

        self.find.x = 21    # column_defaults_dialog.nml:45
        self.find.y = 2    # column_defaults_dialog.nml:46
        self.find.width = 17    # column_defaults_dialog.nml:47
        self.find.height = 5    # column_defaults_dialog.nml:48
        self.find.items = ['Size', 'Attributes', 'Owner', 'Date', 'Path']    # column_defaults_dialog.nml:49
