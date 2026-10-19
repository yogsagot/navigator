# navml: generated
"""Generated from ``system_setup_page.nml``.

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
from navml.widgets.dialog.check_boxes import CheckBoxes    # system_setup_page.nml:1
from navml.widgets.dialog.field import Field    # system_setup_page.nml:2
from navml.widgets.dialog.label import Label    # system_setup_page.nml:3
from navml.widgets.dialog.masked_field import MaskedField    # system_setup_page.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # system_setup_page.nml:5
from navml.widgets.dialog.static_text import StaticText    # system_setup_page.nml:6

__navml_component__ = "SystemSetupPage"

__all__ = ["SystemSetupPage"]


class SystemSetupPage(_Component):
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
    __navml_source__ = "system_setup_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # system_setup_page.nml:25

    #: Ids, annotated so the hand-written half completes them.
    options_caption: Label    # system_setup_page.nml:28
    options: CheckBoxes    # system_setup_page.nml:37
    temp_caption: Label    # system_setup_page.nml:45
    temp_dir: Field    # system_setup_page.nml:54
    on_error_caption: Label    # system_setup_page.nml:63
    on_error: RadioButtons    # system_setup_page.nml:72
    stall_report: MaskedField    # system_setup_page.nml:80
    stall_unit: StaticText    # system_setup_page.nml:92

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options_caption = Label(parent=self)    # system_setup_page.nml:27
        self.options = CheckBoxes(parent=self)    # system_setup_page.nml:36
        self.temp_caption = Label(parent=self)    # system_setup_page.nml:44
        self.temp_dir = Field(parent=self)    # system_setup_page.nml:53
        self.on_error_caption = Label(parent=self)    # system_setup_page.nml:62
        self.on_error = RadioButtons(parent=self)    # system_setup_page.nml:71
        self.stall_report = MaskedField(parent=self)    # system_setup_page.nml:79
        self.stall_unit = StaticText(parent=self)    # system_setup_page.nml:91

        self.options_caption.x = 3    # system_setup_page.nml:29
        self.options_caption.y = 1    # system_setup_page.nml:30
        self.options_caption.width = 12    # system_setup_page.nml:31
        self.options_caption.height = 1    # system_setup_page.nml:32
        self.options_caption.text = _bind(    # system_setup_page.nml:33
            lambda _o: _tr('~O~ptions'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # system_setup_page.nml:34

        self.options.x = 3    # system_setup_page.nml:38
        self.options.y = 2    # system_setup_page.nml:39
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_page.nml:40
        self.options.height = 3    # system_setup_page.nml:41
        self.options.items = _bind(    # system_setup_page.nml:42
            lambda _o: [_tr('Internal ~e~ditor'), _tr('Internal ~v~iewer'), _tr('~U~se system clipboard'), _tr('~S~how hidden files'), _tr('S~y~nc after copying'), _tr('Use internal te~r~minal')],
            yielding=True,
        )

        self.temp_caption.x = 3    # system_setup_page.nml:46
        self.temp_caption.y = 6    # system_setup_page.nml:47
        self.temp_caption.width = 24    # system_setup_page.nml:48
        self.temp_caption.height = 1    # system_setup_page.nml:49
        self.temp_caption.text = _bind(    # system_setup_page.nml:50
            lambda _o: _tr('~T~emporary directory'),
            yielding=True,
        )
        self.temp_caption.link = _bind(lambda _o: self.temp_dir.entry)    # system_setup_page.nml:51

        self.temp_dir.x = 3    # system_setup_page.nml:55
        self.temp_dir.y = 7    # system_setup_page.nml:56
        self.temp_dir.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_page.nml:57
        self.temp_dir.height = 1    # system_setup_page.nml:58
        self.temp_dir.label_text = ''    # system_setup_page.nml:59
        self.temp_dir.label_width = 0    # system_setup_page.nml:60

        self.on_error_caption.x = 3    # system_setup_page.nml:64
        self.on_error_caption.y = 9    # system_setup_page.nml:65
        self.on_error_caption.width = 24    # system_setup_page.nml:66
        self.on_error_caption.height = 1    # system_setup_page.nml:67
        self.on_error_caption.text = _bind(    # system_setup_page.nml:68
            lambda _o: _tr('Unexpected ~f~ailures'),
            yielding=True,
        )
        self.on_error_caption.link = _bind(lambda _o: self.on_error)    # system_setup_page.nml:69

        self.on_error.x = 3    # system_setup_page.nml:73
        self.on_error.y = 10    # system_setup_page.nml:74
        self.on_error.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_page.nml:75
        self.on_error.height = 1    # system_setup_page.nml:76
        self.on_error.items = _bind(    # system_setup_page.nml:77
            lambda _o: [_tr('Show a ~m~essage'), _tr('~Q~uit with a traceback')],
            yielding=True,
        )

        self.stall_report.x = 3    # system_setup_page.nml:81
        self.stall_report.y = 12    # system_setup_page.nml:82
        self.stall_report.width = 31    # system_setup_page.nml:83
        self.stall_report.height = 1    # system_setup_page.nml:84
        self.stall_report.label_text = _bind(    # system_setup_page.nml:85
            lambda _o: _tr('Report a ~s~tall after'),
            yielding=True,
        )
        self.stall_report.label_width = 26    # system_setup_page.nml:86
        self.stall_report.mask = '999'    # system_setup_page.nml:87
        self.stall_report.page_keys = False    # system_setup_page.nml:89

        self.stall_unit.x = 35    # system_setup_page.nml:93
        self.stall_unit.y = 12    # system_setup_page.nml:94
        self.stall_unit.width = _bind(lambda _o: max(0, _o.parent.width - 38))    # system_setup_page.nml:95
        self.stall_unit.height = 1    # system_setup_page.nml:96
        self.stall_unit.text = _bind(    # system_setup_page.nml:97
            lambda _o: _tr('seconds (0: never)'),
            yielding=True,
        )
