# navml: generated
"""Generated from ``drive_info_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # drive_info_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # drive_info_dialog.nml:2
from navml.widgets.dialog.label import Label    # drive_info_dialog.nml:3

__navml_component__ = "DriveInfoDialog"

__all__ = ["DriveInfoDialog"]


class DriveInfoDialog(Dialog, _Component):
    """Options > File Manager > Information panel: DOS Navigator's ``dlgDriveInfoSetup``.

    Its boxes in its order, less *EMS* and *XMS Information*, which only
    meant something on DOS; *Conventional Memory* is the machine's.  Help is
    left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "drive_info_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    items_caption: Label    # drive_info_dialog.nml:16
    options: CheckBoxes    # drive_info_dialog.nml:25

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.items_caption = Label(parent=self)    # drive_info_dialog.nml:15
        self.options = CheckBoxes(parent=self)    # drive_info_dialog.nml:24

        self.modal_width = 46    # drive_info_dialog.nml:11
        self.modal_height = 15    # drive_info_dialog.nml:12
        self.title = 'Information Panel Setup'    # drive_info_dialog.nml:13

        self.items_caption.x = 2    # drive_info_dialog.nml:17
        self.items_caption.y = 1    # drive_info_dialog.nml:18
        self.items_caption.width = 20    # drive_info_dialog.nml:19
        self.items_caption.height = 1    # drive_info_dialog.nml:20
        self.items_caption.text = 'Items to display'    # drive_info_dialog.nml:21
        self.items_caption.link = _bind(lambda _o: self.options)    # drive_info_dialog.nml:22

        self.options.x = 2    # drive_info_dialog.nml:26
        self.options.y = 2    # drive_info_dialog.nml:27
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # drive_info_dialog.nml:28
        self.options.height = 9    # drive_info_dialog.nml:29
        self.options.items = ['~D~irectory Title', '~T~otals', 'Volume ~S~ize', 'Volume ~F~ree space', 'Volume ~L~abel', 'Total ~m~emory', 'M~e~mory for user', 'Memory for ~N~avigator', '~I~nformation file']    # drive_info_dialog.nml:30
