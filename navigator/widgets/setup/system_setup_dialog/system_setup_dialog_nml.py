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
from navml.widgets.dialog.radio_buttons import RadioButtons    # system_setup_dialog.nml:5

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
    with it printed -- never nothing (``SystemData.on_error``).
    """

    #: The document this class was generated from.
    __navml_source__ = "system_setup_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    options_caption: Label    # system_setup_dialog.nml:26
    options: CheckBoxes    # system_setup_dialog.nml:35
    temp_caption: Label    # system_setup_dialog.nml:43
    temp_dir: Field    # system_setup_dialog.nml:52
    on_error_caption: Label    # system_setup_dialog.nml:61
    on_error: RadioButtons    # system_setup_dialog.nml:70

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.options_caption = Label(parent=self)    # system_setup_dialog.nml:25
        self.options = CheckBoxes(parent=self)    # system_setup_dialog.nml:34
        self.temp_caption = Label(parent=self)    # system_setup_dialog.nml:42
        self.temp_dir = Field(parent=self)    # system_setup_dialog.nml:51
        self.on_error_caption = Label(parent=self)    # system_setup_dialog.nml:60
        self.on_error = RadioButtons(parent=self)    # system_setup_dialog.nml:69

        self.modal_width = 60    # system_setup_dialog.nml:21
        self.modal_height = 16    # system_setup_dialog.nml:22
        self.title = _bind(lambda _o: _tr('System Setup'), yielding=True)    # system_setup_dialog.nml:23

        self.options_caption.x = 3    # system_setup_dialog.nml:27
        self.options_caption.y = 1    # system_setup_dialog.nml:28
        self.options_caption.width = 12    # system_setup_dialog.nml:29
        self.options_caption.height = 1    # system_setup_dialog.nml:30
        self.options_caption.text = _bind(    # system_setup_dialog.nml:31
            lambda _o: _tr('~O~ptions'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # system_setup_dialog.nml:32

        self.options.x = 3    # system_setup_dialog.nml:36
        self.options.y = 2    # system_setup_dialog.nml:37
        self.options.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_dialog.nml:38
        self.options.height = 3    # system_setup_dialog.nml:39
        self.options.items = _bind(    # system_setup_dialog.nml:40
            lambda _o: [_tr('Internal ~e~ditor'), _tr('Internal ~v~iewer'), _tr('~U~se system clipboard'), _tr('~S~how hidden files'), _tr('S~y~nc after copying'), _tr('Use internal te~r~minal')],
            yielding=True,
        )

        self.temp_caption.x = 3    # system_setup_dialog.nml:44
        self.temp_caption.y = 6    # system_setup_dialog.nml:45
        self.temp_caption.width = 24    # system_setup_dialog.nml:46
        self.temp_caption.height = 1    # system_setup_dialog.nml:47
        self.temp_caption.text = _bind(    # system_setup_dialog.nml:48
            lambda _o: _tr('~T~emporary directory'),
            yielding=True,
        )
        self.temp_caption.link = _bind(lambda _o: self.temp_dir.entry)    # system_setup_dialog.nml:49

        self.temp_dir.x = 3    # system_setup_dialog.nml:53
        self.temp_dir.y = 7    # system_setup_dialog.nml:54
        self.temp_dir.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_dialog.nml:55
        self.temp_dir.height = 1    # system_setup_dialog.nml:56
        self.temp_dir.label_text = ''    # system_setup_dialog.nml:57
        self.temp_dir.label_width = 0    # system_setup_dialog.nml:58

        self.on_error_caption.x = 3    # system_setup_dialog.nml:62
        self.on_error_caption.y = 9    # system_setup_dialog.nml:63
        self.on_error_caption.width = 24    # system_setup_dialog.nml:64
        self.on_error_caption.height = 1    # system_setup_dialog.nml:65
        self.on_error_caption.text = _bind(    # system_setup_dialog.nml:66
            lambda _o: _tr('Unexpected ~f~ailures'),
            yielding=True,
        )
        self.on_error_caption.link = _bind(lambda _o: self.on_error)    # system_setup_dialog.nml:67

        self.on_error.x = 3    # system_setup_dialog.nml:71
        self.on_error.y = 10    # system_setup_dialog.nml:72
        self.on_error.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # system_setup_dialog.nml:73
        self.on_error.height = 1    # system_setup_dialog.nml:74
        self.on_error.items = _bind(    # system_setup_dialog.nml:75
            lambda _o: [_tr('Show a ~m~essage'), _tr('~Q~uit with a traceback')],
            yielding=True,
        )
