# navml: generated
"""Generated from ``system_setup_dialog.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # system_setup_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # system_setup_dialog.nml:2
from navml.widgets.dialog.field import Field    # system_setup_dialog.nml:3
from navml.widgets.dialog.label import Label    # system_setup_dialog.nml:4
from navml.widgets.dialog.masked_field import MaskedField    # system_setup_dialog.nml:5
from navml.widgets.dialog.radio_buttons import RadioButtons    # system_setup_dialog.nml:6
from navml.widgets.dialog.static_text import StaticText    # system_setup_dialog.nml:7

__navml_component__ = "SystemSetupDialog"

__all__ = ["SystemSetupDialog"]


class SystemSetupDialog(Dialog, _Component):
    """Options > Configuration > System Setup: DOS Navigator's ``dlgSystemSetup``.

    The resource's *Options* and *Temporary directory*, less what only meant
    something on DOS -- *Disable XMS/EMS usage*, *OS-dependent Disk Access*,
    *Clear read-only from CD*, *"Fast" command execution* (DN's INT 2Fh reload
    trick), *Advanced copy* (XMS/EMS buffers), the two video modes and the
    per-drive list -- so it is nine rows shorter.  *Flush disk buffers* is
    kept as what it means on POSIX: syncing what a copy wrote.  Help is left out, having nothing to show yet.
    *Use internal terminal* is not DN's but a departure: whether Ctrl+O shows
    the console in Navigator, or hands the real terminal over as mc does.
    *Unexpected errors* is another: DN had Turbo Pascal's ``Runtime error``
    and no choice, where this picks a box with the traceback or quitting
    with it printed -- never nothing (``SystemData.on_error``).  *Report a
    stall after* is a third: how long Navigator may stop answering before
    ``errors.log`` records why (``SystemData.stall_report``).
    """

    #: The document this class was generated from.
    __navml_source__ = "system_setup_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    options_caption: Label    # system_setup_dialog.nml:30
    options: CheckBoxes    # system_setup_dialog.nml:39
    temp_caption: Label    # system_setup_dialog.nml:47
    temp_dir: Field    # system_setup_dialog.nml:56
    on_error_caption: Label    # system_setup_dialog.nml:65
    on_error: RadioButtons    # system_setup_dialog.nml:74
    stall_report: MaskedField    # system_setup_dialog.nml:82
    stall_unit: StaticText    # system_setup_dialog.nml:92

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options_caption = Label(parent=self)    # system_setup_dialog.nml:29
        self.options = CheckBoxes(parent=self)    # system_setup_dialog.nml:38
        self.temp_caption = Label(parent=self)    # system_setup_dialog.nml:46
        self.temp_dir = Field(parent=self)    # system_setup_dialog.nml:55
        self.on_error_caption = Label(parent=self)    # system_setup_dialog.nml:64
        self.on_error = RadioButtons(parent=self)    # system_setup_dialog.nml:73
        self.stall_report = MaskedField(parent=self)    # system_setup_dialog.nml:81
        self.stall_unit = StaticText(parent=self)    # system_setup_dialog.nml:91

        self.modal_width = 60    # system_setup_dialog.nml:25
        self.modal_height = 18    # system_setup_dialog.nml:26
        self.title = _bind(lambda _o: _tr('System Setup'), yielding=True)    # system_setup_dialog.nml:27

        self.options_caption.x = 3    # system_setup_dialog.nml:31
        self.options_caption.y = 1    # system_setup_dialog.nml:32
        self.options_caption.width = 12    # system_setup_dialog.nml:33
        self.options_caption.height = 1    # system_setup_dialog.nml:34
        self.options_caption.text = _bind(    # system_setup_dialog.nml:35
            lambda _o: _tr('~O~ptions'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # system_setup_dialog.nml:36

        self.options.x = 3    # system_setup_dialog.nml:40
        self.options.y = 2    # system_setup_dialog.nml:41
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_dialog.nml:42
        self.options.height = 3    # system_setup_dialog.nml:43
        self.options.items = _bind(    # system_setup_dialog.nml:44
            lambda _o: [_tr('Internal ~e~ditor'), _tr('Internal ~v~iewer'), _tr('~U~se system clipboard'), _tr('~S~how hidden files'), _tr('S~y~nc after copying'), _tr('Use internal te~r~minal')],
            yielding=True,
        )

        self.temp_caption.x = 3    # system_setup_dialog.nml:48
        self.temp_caption.y = 6    # system_setup_dialog.nml:49
        self.temp_caption.width = 24    # system_setup_dialog.nml:50
        self.temp_caption.height = 1    # system_setup_dialog.nml:51
        self.temp_caption.text = _bind(    # system_setup_dialog.nml:52
            lambda _o: _tr('~T~emporary directory'),
            yielding=True,
        )
        self.temp_caption.link = _bind(lambda _o: self.temp_dir.entry)    # system_setup_dialog.nml:53

        self.temp_dir.x = 3    # system_setup_dialog.nml:57
        self.temp_dir.y = 7    # system_setup_dialog.nml:58
        self.temp_dir.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_dialog.nml:59
        self.temp_dir.height = 1    # system_setup_dialog.nml:60
        self.temp_dir.label_text = ''    # system_setup_dialog.nml:61
        self.temp_dir.label_width = 0    # system_setup_dialog.nml:62

        self.on_error_caption.x = 3    # system_setup_dialog.nml:66
        self.on_error_caption.y = 9    # system_setup_dialog.nml:67
        self.on_error_caption.width = 24    # system_setup_dialog.nml:68
        self.on_error_caption.height = 1    # system_setup_dialog.nml:69
        self.on_error_caption.text = _bind(    # system_setup_dialog.nml:70
            lambda _o: _tr('Unexpected ~f~ailures'),
            yielding=True,
        )
        self.on_error_caption.link = _bind(lambda _o: self.on_error)    # system_setup_dialog.nml:71

        self.on_error.x = 3    # system_setup_dialog.nml:75
        self.on_error.y = 10    # system_setup_dialog.nml:76
        self.on_error.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_dialog.nml:77
        self.on_error.height = 1    # system_setup_dialog.nml:78
        self.on_error.items = _bind(    # system_setup_dialog.nml:79
            lambda _o: [_tr('Show a ~m~essage'), _tr('~Q~uit with a traceback')],
            yielding=True,
        )

        self.stall_report.x = 3    # system_setup_dialog.nml:83
        self.stall_report.y = 12    # system_setup_dialog.nml:84
        self.stall_report.width = 31    # system_setup_dialog.nml:85
        self.stall_report.height = 1    # system_setup_dialog.nml:86
        self.stall_report.label_text = _bind(    # system_setup_dialog.nml:87
            lambda _o: _tr('Report a ~s~tall after'),
            yielding=True,
        )
        self.stall_report.label_width = 26    # system_setup_dialog.nml:88
        self.stall_report.mask = '999'    # system_setup_dialog.nml:89

        self.stall_unit.x = 35    # system_setup_dialog.nml:93
        self.stall_unit.y = 12    # system_setup_dialog.nml:94
        self.stall_unit.width = _bind(lambda _o: max(0, _o.parent.width - 38))    # system_setup_dialog.nml:95
        self.stall_unit.height = 1    # system_setup_dialog.nml:96
        self.stall_unit.text = _bind(    # system_setup_dialog.nml:97
            lambda _o: _tr('seconds (0: never)'),
            yielding=True,
        )
