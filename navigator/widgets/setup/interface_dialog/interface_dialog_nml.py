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

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # interface_dialog.nml:1
from navml.widgets.dialog.choice_field import ChoiceField    # interface_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # interface_dialog.nml:3
from navml.widgets.dialog.masked_field import MaskedField    # interface_dialog.nml:4

__navml_component__ = "InterfaceDialog"

__all__ = ["InterfaceDialog"]


class InterfaceDialog(Dialog, _Component):
    """Options > Configuration > Interface: DOS Navigator's ``dlgInterfaceSetup``.

    The resource's twelve boxes in its two columns of six, at its width; Help
    is left out, having nothing to show yet.  *History size* below them is a
    departure: DN's lists were a fixed 20 long; so is *Language*, DN's being
    the resource set it was installed with.
    """

    #: The document this class was generated from.
    __navml_source__ = "interface_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    options: CheckBoxes    # interface_dialog.nml:18
    history_size: MaskedField    # interface_dialog.nml:26
    language: ChoiceField    # interface_dialog.nml:37

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options = CheckBoxes(parent=self)    # interface_dialog.nml:17
        self.history_size = MaskedField(parent=self)    # interface_dialog.nml:25
        self.language = ChoiceField(parent=self)    # interface_dialog.nml:36

        self.modal_width = 60    # interface_dialog.nml:13
        self.modal_height = 16    # interface_dialog.nml:14
        self.title = _bind(lambda _o: _tr('Interface Setup'), yielding=True)    # interface_dialog.nml:15

        self.options.x = 2    # interface_dialog.nml:19
        self.options.y = 1    # interface_dialog.nml:20
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # interface_dialog.nml:21
        self.options.height = 6    # interface_dialog.nml:22
        self.options.items = _bind(    # interface_dialog.nml:23
            lambda _o: [_tr('~C~lock'), _tr('Hide ~m~enu bar'), _tr('Hide ~s~tatus line'), _tr('ESC for ~u~ser screen'), _tr('Hide Command ~L~ine'), _tr('~A~uto hide Command Line'), _tr('~B~lock Insert Cursor'), _tr('Store edi~t~or position'), _tr('Store vie~w~er position'), _tr('Track ~e~diting history'), _tr('Track ~v~iewing history'), _tr('Track ~d~irectories')],
            yielding=True,
        )

        self.history_size.x = 2    # interface_dialog.nml:27
        self.history_size.y = 8    # interface_dialog.nml:28
        self.history_size.width = 20    # interface_dialog.nml:29
        self.history_size.height = 1    # interface_dialog.nml:30
        self.history_size.label_text = _bind(    # interface_dialog.nml:31
            lambda _o: _tr('~H~istory size'),
            yielding=True,
        )
        self.history_size.label_width = 15    # interface_dialog.nml:32
        self.history_size.mask = '999'    # interface_dialog.nml:33

        self.language.x = 2    # interface_dialog.nml:38
        self.language.y = 10    # interface_dialog.nml:39
        self.language.width = 40    # interface_dialog.nml:40
        self.language.height = 1    # interface_dialog.nml:41
        self.language.label_text = _bind(    # interface_dialog.nml:42
            lambda _o: _tr('~L~anguage'),
            yielding=True,
        )
        self.language.label_width = 15    # interface_dialog.nml:43
