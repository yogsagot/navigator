# navml: generated
"""Generated from ``interface_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # interface_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # interface_dialog.nml:2
from navml.widgets.dialog.masked_field import MaskedField    # interface_dialog.nml:3

__navml_component__ = "InterfaceDialog"

__all__ = ["InterfaceDialog"]


class InterfaceDialog(Dialog, _Component):
    """Options > Configuration > Interface: DOS Navigator's ``dlgInterfaceSetup``.

    The resource's twelve boxes in its two columns of six, at its width; Help
    is left out, having nothing to show yet.  *History size* below them is a
    departure: DN's lists were a fixed 20 long.
    """

    #: The document this class was generated from.
    __navml_source__ = "interface_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    options: CheckBoxes    # interface_dialog.nml:16
    history_size: MaskedField    # interface_dialog.nml:24

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options = CheckBoxes(parent=self)    # interface_dialog.nml:15
        self.history_size = MaskedField(parent=self)    # interface_dialog.nml:23

        self.modal_width = 60    # interface_dialog.nml:11
        self.modal_height = 14    # interface_dialog.nml:12
        self.title = 'Interface Setup'    # interface_dialog.nml:13

        self.options.x = 2    # interface_dialog.nml:17
        self.options.y = 1    # interface_dialog.nml:18
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # interface_dialog.nml:19
        self.options.height = 6    # interface_dialog.nml:20
        self.options.items = ['~C~lock', 'Hide ~m~enu bar', 'Hide ~s~tatus line', 'ESC for ~u~ser screen', 'Hide Command ~L~ine', '~A~uto hide Command Line', '~B~lock Insert Cursor', 'Store edi~t~or position', 'Store vie~w~er position', 'Track ~e~diting history', 'Track ~v~iewing history', 'Track ~d~irectories']    # interface_dialog.nml:21

        self.history_size.x = 2    # interface_dialog.nml:25
        self.history_size.y = 8    # interface_dialog.nml:26
        self.history_size.width = 20    # interface_dialog.nml:27
        self.history_size.height = 1    # interface_dialog.nml:28
        self.history_size.label_text = '~H~istory size'    # interface_dialog.nml:29
        self.history_size.label_width = 15    # interface_dialog.nml:30
        self.history_size.mask = '999'    # interface_dialog.nml:31
