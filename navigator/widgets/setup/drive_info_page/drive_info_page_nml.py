# navml: generated
"""Generated from ``drive_info_page.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # drive_info_page.nml:1
from navml.widgets.dialog.label import Label    # drive_info_page.nml:2

__navml_component__ = "DriveInfoPage"

__all__ = ["DriveInfoPage"]


class DriveInfoPage(_Component):
    """Options > File Manager > Information panel: DOS Navigator's ``dlgDriveInfoSetup``.

    Its boxes in its order, less *EMS* and *XMS Information*, which only
    meant something on DOS; *Conventional Memory* is the machine's.  *File
    under the cursor* is Navigator's own.  Help is
    left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "drive_info_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # drive_info_page.nml:12

    #: Ids, annotated so the hand-written half completes them.
    items_caption: Label    # drive_info_page.nml:15
    options: CheckBoxes    # drive_info_page.nml:24

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.items_caption = Label(parent=self)    # drive_info_page.nml:14
        self.options = CheckBoxes(parent=self)    # drive_info_page.nml:23

        self.items_caption.x = 2    # drive_info_page.nml:16
        self.items_caption.y = 1    # drive_info_page.nml:17
        self.items_caption.width = 20    # drive_info_page.nml:18
        self.items_caption.height = 1    # drive_info_page.nml:19
        self.items_caption.text = _bind(    # drive_info_page.nml:20
            lambda _o: _tr('Items to display'),
            yielding=True,
        )
        self.items_caption.link = _bind(lambda _o: self.options)    # drive_info_page.nml:21

        self.options.x = 2    # drive_info_page.nml:25
        self.options.y = 2    # drive_info_page.nml:26
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # drive_info_page.nml:27
        self.options.height = 10    # drive_info_page.nml:28
        self.options.items = _bind(    # drive_info_page.nml:29
            lambda _o: [_tr('~D~irectory Title'), _tr('~T~otals'), _tr('File under the ~c~ursor'), _tr('Volume ~S~ize'), _tr('Volume ~F~ree space'), _tr('Volume ~L~abel'), _tr('Total ~m~emory'), _tr('M~e~mory for user'), _tr('Memory for ~N~avigator'), _tr('~I~nformation file')],
            yielding=True,
        )
