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
from navigator.widgets.setup.settings_page import SettingsPage    # system_setup_page.nml:7

__navml_component__ = "SystemSetupPage"

__all__ = ["SystemSetupPage"]


class SystemSetupPage(SettingsPage, _Component):
    """Options > Configuration > System Setup: DOS Navigator's ``dlgSystemSetup``.

    The resource's *Options* and *Temporary directory*, less what only meant
    something on DOS -- *Disable XMS/EMS usage*, *OS-dependent Disk Access*,
    *Clear read-only from CD*, *"Fast" command execution* (DN's INT 2Fh reload
    trick), *Advanced copy* (XMS/EMS buffers), the two video modes and the
    per-drive list -- so it is nine rows shorter.  *Flush disk buffers* is
    kept as what it means on POSIX: syncing what a copy wrote, file by file
    as it is written, where DN flushed once at the end -- a departure.  Help is left out, having nothing to show yet.
    *Use internal terminal* is not DN's but a departure: whether Ctrl+O shows
    the console in Navigator, or hands the real terminal over as mc does.
    *Unexpected errors* is another: DN had Turbo Pascal's ``Runtime error``
    and no choice, where this picks a box with the traceback or quitting
    with it printed -- never nothing (``SystemData.on_error``).  *Report a
    stall after* is a third: how long Navigator may stop answering before
    ``errors.log`` records why (``SystemData.stall_report``).  *Root access*
    and *Keep root open while idle* are a fourth: what *As root* asks for root
    with, after a step was refused permission, and for how long it stays open
    (``SystemData.elevate``, ``root_timeout``; ``navigator.lib.system.elevate``).
    *Command windows zoomed* and *modal* are a fifth: how a command run in a
    window of its own opens (``TerminalWindow``), filling the row that was
    spare under *Options*.
    """

    #: The document this class was generated from.
    __navml_source__ = "system_setup_page.nml"

    section_name = 'system'    # system_setup_page.nml:32

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # system_setup_page.nml:35

    #: Ids, annotated so the hand-written half completes them.
    options_caption: Label    # system_setup_page.nml:38
    options: CheckBoxes    # system_setup_page.nml:46
    temp_caption: Label    # system_setup_page.nml:56
    temp_dir: Field    # system_setup_page.nml:64
    on_error_caption: Label    # system_setup_page.nml:74
    on_error: RadioButtons    # system_setup_page.nml:82
    stall_report: MaskedField    # system_setup_page.nml:92
    stall_unit: StaticText    # system_setup_page.nml:106
    elevate_caption: Label    # system_setup_page.nml:117
    elevate: RadioButtons    # system_setup_page.nml:128
    root_timeout: MaskedField    # system_setup_page.nml:141
    root_timeout_unit: StaticText    # system_setup_page.nml:154

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options_caption = Label(parent=self)    # system_setup_page.nml:37
        self.options = CheckBoxes(parent=self)    # system_setup_page.nml:45
        self.temp_caption = Label(parent=self)    # system_setup_page.nml:55
        self.temp_dir = Field(parent=self)    # system_setup_page.nml:63
        self.on_error_caption = Label(parent=self)    # system_setup_page.nml:73
        self.on_error = RadioButtons(parent=self)    # system_setup_page.nml:81
        self.stall_report = MaskedField(parent=self)    # system_setup_page.nml:91
        self.stall_unit = StaticText(parent=self)    # system_setup_page.nml:105
        self.elevate_caption = Label(parent=self)    # system_setup_page.nml:116
        self.elevate = RadioButtons(parent=self)    # system_setup_page.nml:127
        self.root_timeout = MaskedField(parent=self)    # system_setup_page.nml:140
        self.root_timeout_unit = StaticText(parent=self)    # system_setup_page.nml:153

        self.options_caption.x = 3    # system_setup_page.nml:39
        self.options_caption.y = 1    # system_setup_page.nml:40
        self.options_caption.width = 12    # system_setup_page.nml:41
        self.options_caption.text = _bind(    # system_setup_page.nml:42
            lambda _o: _tr('~O~ptions'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # system_setup_page.nml:43

        self.options.key = 'OPTIONS'    # system_setup_page.nml:47
        self.options.y = 2    # system_setup_page.nml:48
        self.options.height = 4    # system_setup_page.nml:49
        self.options.items = _bind(    # system_setup_page.nml:53
            lambda _o: [_tr('Internal ~e~ditor'), _tr('Internal ~v~iewer'), _tr('~U~se system clipboard'), _tr('~S~how hidden files'), _tr('S~y~nc after copying'), _tr('Use internal te~r~minal'), _tr('Command windows ~z~oomed'), _tr('Command windows moda~l~')],
            yielding=True,
        )
        self.options.x = 3    # system_setup_page.nml:51
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_page.nml:52

        self.temp_caption.x = 3    # system_setup_page.nml:57
        self.temp_caption.y = 6    # system_setup_page.nml:58
        self.temp_caption.width = 24    # system_setup_page.nml:59
        self.temp_caption.text = _bind(    # system_setup_page.nml:60
            lambda _o: _tr('~T~emporary directory'),
            yielding=True,
        )
        self.temp_caption.link = _bind(lambda _o: self.temp_dir.entry)    # system_setup_page.nml:61

        self.temp_dir.key = 'temp_dir'    # system_setup_page.nml:65
        self.temp_dir.y = 7    # system_setup_page.nml:66
        self.temp_dir.label_text = ''    # system_setup_page.nml:70
        self.temp_dir.label_width = 0    # system_setup_page.nml:71
        self.temp_dir.x = 3    # system_setup_page.nml:68
        self.temp_dir.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_page.nml:69

        self.on_error_caption.x = 3    # system_setup_page.nml:75
        self.on_error_caption.y = 9    # system_setup_page.nml:76
        self.on_error_caption.width = 24    # system_setup_page.nml:77
        self.on_error_caption.text = _bind(    # system_setup_page.nml:78
            lambda _o: _tr('Unexpected ~f~ailures'),
            yielding=True,
        )
        self.on_error_caption.link = _bind(lambda _o: self.on_error)    # system_setup_page.nml:79

        self.on_error.key = 'on_error'    # system_setup_page.nml:83
        self.on_error.y = 10    # system_setup_page.nml:84
        self.on_error.height = 1    # system_setup_page.nml:85
        self.on_error.items = _bind(    # system_setup_page.nml:89
            lambda _o: [_tr('Show a ~m~essage'), _tr('~Q~uit with a traceback')],
            yielding=True,
        )
        self.on_error.x = 3    # system_setup_page.nml:87
        self.on_error.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_page.nml:88

        self.stall_report.key = 'stall_report'    # system_setup_page.nml:93
        self.stall_report.x = 3    # system_setup_page.nml:94
        self.stall_report.y = 12    # system_setup_page.nml:95
        self.stall_report.width = 31    # system_setup_page.nml:96
        self.stall_report.label_text = _bind(    # system_setup_page.nml:97
            lambda _o: _tr('Re~p~ort a stall after'),
            yielding=True,
        )
        self.stall_report.label_width = 26    # system_setup_page.nml:98
        self.stall_report.mask = '999'    # system_setup_page.nml:99
        self.stall_report.page_keys = False    # system_setup_page.nml:101

        self.stall_unit.x = _bind(    # system_setup_page.nml:107
            lambda _o: 30 if _o.parent.width < 67 else 35
        )
        self.stall_unit.y = _bind(    # system_setup_page.nml:108
            lambda _o: 13 if _o.parent.width < 67 else 12
        )
        self.stall_unit.width = _bind(    # system_setup_page.nml:109
            lambda _o: max(0, _o.parent.width - 32) if _o.parent.width < 67 else max(0, _o.parent.width - 38)
        )
        self.stall_unit.text = _bind(    # system_setup_page.nml:114
            lambda _o: _tr('seconds (0: never)'),
            yielding=True,
        )

        self.elevate_caption.x = 3    # system_setup_page.nml:118
        self.elevate_caption.y = _bind(    # system_setup_page.nml:119
            lambda _o: 15 if _o.parent.width < 67 else 14
        )
        self.elevate_caption.width = 14    # system_setup_page.nml:120
        self.elevate_caption.text = _bind(    # system_setup_page.nml:123
            lambda _o: _tr('Root a~c~cess'),
            yielding=True,
        )
        self.elevate_caption.link = _bind(lambda _o: self.elevate)    # system_setup_page.nml:124

        self.elevate.key = 'elevate'    # system_setup_page.nml:129
        self.elevate.x = _bind(lambda _o: 3 if _o.parent.width < 67 else 17)    # system_setup_page.nml:130
        self.elevate.y = _bind(lambda _o: 16 if _o.parent.width < 67 else 14)    # system_setup_page.nml:131
        self.elevate.width = _bind(    # system_setup_page.nml:132
            lambda _o: max(0, _o.parent.width - 6) if _o.parent.width < 67 else max(0, _o.parent.width - 20)
        )
        self.elevate.height = 1    # system_setup_page.nml:133
        self.elevate.items = _bind(    # system_setup_page.nml:138
            lambda _o: [_tr('~A~uto'), _tr('su~d~o'), _tr('pke~x~ec'), _tr('~N~ever offer')],
            yielding=True,
        )

        self.root_timeout.key = 'root_timeout'    # system_setup_page.nml:142
        self.root_timeout.x = 3    # system_setup_page.nml:143
        self.root_timeout.y = _bind(    # system_setup_page.nml:144
            lambda _o: 17 if _o.parent.width < 67 else 16
        )
        self.root_timeout.width = 31    # system_setup_page.nml:145
        self.root_timeout.label_text = _bind(    # system_setup_page.nml:148
            lambda _o: _tr('Keep root open ~w~hile idle'),
            yielding=True,
        )
        self.root_timeout.label_width = 26    # system_setup_page.nml:149
        self.root_timeout.mask = '999'    # system_setup_page.nml:150
        self.root_timeout.page_keys = False    # system_setup_page.nml:151

        self.root_timeout_unit.x = _bind(    # system_setup_page.nml:155
            lambda _o: 30 if _o.parent.width < 67 else 35
        )
        self.root_timeout_unit.y = _bind(    # system_setup_page.nml:156
            lambda _o: 18 if _o.parent.width < 67 else 16
        )
        self.root_timeout_unit.width = _bind(    # system_setup_page.nml:157
            lambda _o: max(0, _o.parent.width - 32) if _o.parent.width < 67 else max(0, _o.parent.width - 38)
        )
        self.root_timeout_unit.text = _bind(    # system_setup_page.nml:162
            lambda _o: _tr('minutes (0: each time)'),
            yielding=True,
        )

        self._navml_built(__class__)
